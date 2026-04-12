"""Telegram notification bridge for aho.

0.2.2 W3: real send-only implementation with project-scoped secrets.
Receive-side deferred to 0.2.3+.
"""
import json
import socketserver
import sys
import time
from pathlib import Path

import requests
from opentelemetry import trace

from aho.secrets.store import get_secret
from aho.logger import log_event

_tracer = trace.get_tracer("aho.telegram")

PROJECT = "ahomw"
BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _get_creds():
    """Retrieve Telegram credentials from aho secrets store."""
    token = get_secret(PROJECT, "telegram_bot_token")
    chat_id = get_secret(PROJECT, "telegram_chat_id")
    return token, chat_id


def send(message: str, priority: str = "normal", chat_id: str = None) -> bool:
    """Send a message via Telegram bot API.

    Handles 429 rate limiting with backoff. Returns True on success.
    """
    with _tracer.start_as_current_span("telegram.send") as span:
        span.set_attribute("message_length", len(message))
        span.set_attribute("priority", priority)
        try:
            token, default_chat_id = _get_creds()
            cid = chat_id or default_chat_id
            if not token or not cid:
                span.set_attribute("status", "no_creds")
                log_event("llm_call", "telegram", "api.telegram.org", "send",
                          status="error", error="missing credentials")
                return False

            prefix = {"high": "[!]", "normal": "[i]", "low": "[.]"}.get(priority, "")
            text = f"{prefix} {message}" if prefix else message
            payload = {"chat_id": cid, "text": text, "parse_mode": "Markdown"}

            for attempt in range(3):
                resp = requests.post(
                    BASE_URL.format(token=token),
                    json=payload,
                    timeout=10,
                )
                if resp.status_code == 429:
                    retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                    time.sleep(retry_after)
                    continue
                break

            span.set_attribute("status_code", resp.status_code)
            log_event("llm_call", "telegram", "api.telegram.org", "send",
                      input_summary=message[:80],
                      output_summary=f"status={resp.status_code}",
                      status="success" if resp.ok else "error")
            span.set_attribute("status", "ok" if resp.ok else "error")
            return resp.ok
        except Exception as e:
            span.set_attribute("status", "error")
            span.record_exception(e)
            log_event("llm_call", "telegram", "api.telegram.org", "send",
                      status="error", error=str(e))
            return False


def send_capability_gap(gap: str) -> bool:
    """Send a formatted capability gap alert."""
    return send(f"*[CAPABILITY GAP]* {gap}", priority="high")


def send_close_complete(iteration: str, status: str) -> bool:
    """Send iteration close notification."""
    icon = "OK" if status == "closed" else "WARN"
    return send(f"[{icon}] aho {iteration} {status}", priority="normal")


def send_message(project_code: str, text: str) -> bool:
    """Legacy API: send a plain text message (backwards-compatible)."""
    return send(text)


def send_iteration_complete(project_code: str, iteration: str, bundle_path: str, run_path: str) -> bool:
    """Send a structured iteration-complete notification."""
    text = (
        f"[OK] Iteration {iteration} COMPLETE\n"
        f"Project: {project_code}\n\n"
        f"Bundle: {bundle_path}\n"
        f"Report: {run_path}\n\n"
        f"Status: Review Pending"
    )
    return send(text)


# --- Daemon mode (Unix socket for inbound send requests) ---

SOCK_PATH = Path.home() / ".local/share/aho/telegram.sock"


class TelegramHandler(socketserver.StreamRequestHandler):
    """Handle send requests over Unix socket."""

    def handle(self):
        try:
            raw = self.rfile.readline().decode("utf-8").strip()
            if not raw:
                return
            req = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._reply({"error": "invalid JSON"})
            return

        cmd = req.get("cmd", "")
        if cmd == "send":
            ok = send(
                req.get("message", ""),
                priority=req.get("priority", "normal"),
                chat_id=req.get("chat_id"),
            )
            self._reply({"ok": ok})
        elif cmd == "status":
            token, chat_id = _get_creds()
            self._reply({
                "ok": True,
                "has_token": bool(token),
                "chat_id": str(chat_id) if chat_id else None,
            })
        else:
            self._reply({"error": f"unknown command: {cmd}"})

    def _reply(self, data: dict):
        self.wfile.write((json.dumps(data) + "\n").encode("utf-8"))


BOT_STATE_PATH = Path.home() / ".local/state/aho/telegram_bot.json"


def _write_bot_state():
    """Query getMe and cache bot info for doctor to read."""
    try:
        token, _ = _get_creds()
        if not token:
            return
        resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if resp.ok:
            bot = resp.json().get("result", {})
            BOT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            BOT_STATE_PATH.write_text(json.dumps({
                "username": bot.get("username"),
                "first_name": bot.get("first_name"),
                "id": bot.get("id"),
            }))
            print(f"[telegram] bot: @{bot.get('username')}", flush=True)
    except Exception:
        pass


def serve():
    """Start the Telegram bridge daemon (outbound socket + inbound polling)."""
    from aho.logger import emit_heartbeat
    from aho.telegram.inbound import start_inbound_thread

    SOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SOCK_PATH.exists():
        SOCK_PATH.unlink()
    _write_bot_state()
    emit_heartbeat("telegram")

    # Start inbound getUpdates polling thread
    inbound_stop = start_inbound_thread()

    print(f"[telegram] listening on {SOCK_PATH}", flush=True)
    server = socketserver.UnixStreamServer(str(SOCK_PATH), TelegramHandler)
    try:
        server.serve_forever()
    finally:
        inbound_stop.set()
        if SOCK_PATH.exists():
            SOCK_PATH.unlink()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    else:
        print("Usage: python -m aho.telegram.notifications --serve")
        sys.exit(1)
