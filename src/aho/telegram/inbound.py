"""Telegram inbound bridge — long-polls getUpdates, routes commands and free-text.

Architecture:
- Runs as a thread inside the existing aho-telegram.service daemon
- Dedupes via update_id offset persisted to disk
- Filters by chat_id allow-list (Kyle only, single-user)
- Routes commands to handlers, free-text to openclaw
- Sync wait on openclaw with configurable timeout, async ack fallback

Per 0.2.8 Decision 6: fold into existing daemon, no new systemd unit.
Per 0.2.8 Decision 7: sync 30s timeout, async ack fallback.
"""
import json
import threading
import time
from pathlib import Path

import requests

from aho.secrets.store import get_secret
from aho.telegram.openclaw_client import send_chat, get_status
from aho.paths import find_project_root

PROJECT = "ahomw"
OFFSET_PATH = Path.home() / ".local/state/aho/telegram_offset"
BASE_URL = "https://api.telegram.org/bot{token}"

# Default timeout for openclaw sync wait (overridable via orchestrator.json)
_DEFAULT_OPENCLAW_TIMEOUT = 30


def _get_config() -> dict:
    """Read telegram config from orchestrator.json if available."""
    config_path = Path.home() / ".config/aho/orchestrator.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            return data.get("telegram", {})
        except Exception:
            pass
    return {}


def _get_openclaw_timeout() -> float:
    config = _get_config()
    return float(config.get("openclaw_sync_timeout_seconds", _DEFAULT_OPENCLAW_TIMEOUT))


def _load_offset() -> int:
    """Load last processed update_id from disk."""
    if OFFSET_PATH.exists():
        try:
            return int(OFFSET_PATH.read_text().strip())
        except (ValueError, OSError):
            pass
    return 0


def _save_offset(offset: int):
    """Persist update_id offset to disk."""
    OFFSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_PATH.write_text(str(offset))


def _send_reply(token: str, chat_id: int, text: str):
    """Send a reply via Telegram sendMessage. Truncates at 4000 chars."""
    if len(text) > 4000:
        text = text[:3990] + "\n…(truncated)"
    url = f"{BASE_URL.format(token=token)}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 429:
                retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after)
                continue
            return resp.ok
        except Exception:
            return False
    return False


def _format_openclaw_response(result: dict) -> str:
    """Format openclaw response for Telegram display."""
    if not result.get("ok"):
        error = result.get("error", "unknown error")
        if result.get("timed_out"):
            return f"⏳ dispatched to openclaw, will reply when done.\n_{error}_"
        return f"❌ openclaw error: {error}"

    response = result.get("response", "")
    if not response:
        return "_(empty response from openclaw)_"
    return response


def _handle_iteration_info() -> str:
    """Read .aho.json and checkpoint for /iteration and /last commands."""
    from aho.paths import find_project_root
    root = find_project_root()

    parts = []
    aho_json = root / ".aho.json"
    if aho_json.exists():
        data = json.loads(aho_json.read_text())
        parts.append(f"*Iteration:* {data.get('current_iteration', '?')}")
        parts.append(f"*Phase:* {data.get('phase', '?')}")
        parts.append(f"*Last completed:* {data.get('last_completed_iteration', '?')}")

    ckpt = root / ".aho-checkpoint.json"
    if ckpt.exists():
        data = json.loads(ckpt.read_text())
        parts.append(f"*Status:* {data.get('status', '?')}")
        parts.append(f"*Workstream:* {data.get('current_workstream', '?')}")
        ws = data.get("workstreams", {})
        passed = sum(1 for v in ws.values() if v == "pass")
        parts.append(f"*Progress:* {passed}/{len(ws)} workstreams pass")

    return "\n".join(parts) if parts else "_(no iteration data)_"


def _handle_status_info() -> str:
    """Run doctor preflight summary for /status command."""
    try:
        from aho.doctor import run_all
        results = run_all(level="quick")
        lines = ["*aho status*"]
        ok_count = sum(1 for s, _ in results.values() if s == "ok")
        total = len(results)
        lines.append(f"✅ {ok_count}/{total} checks pass\n")
        for name, (status, msg) in sorted(results.items()):
            icon = "✅" if status == "ok" else "⚠️" if status == "warn" else "❌"
            lines.append(f"{icon} {name}: {msg[:60]}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ doctor failed: {e}"


def _handle_ws_status() -> str:
    """Read .aho.json + .aho-checkpoint.json, format current WS + proceed_awaited state."""
    root = find_project_root()
    parts = []

    aho_json = root / ".aho.json"
    if aho_json.exists():
        data = json.loads(aho_json.read_text())
        parts.append(f"*Iteration:* {data.get('current_iteration', '?')}")

    ckpt = root / ".aho-checkpoint.json"
    if ckpt.exists():
        data = json.loads(ckpt.read_text())
        parts.append(f"*Status:* {data.get('status', '?')}")
        parts.append(f"*Current WS:* {data.get('current_workstream', '?')}")
        ws = data.get("workstreams", {})
        passed = sum(1 for v in ws.values() if v == "pass")
        parts.append(f"*Progress:* {passed}/{len(ws)} pass")
        parts.append(f"*Executor:* {data.get('executor', '?')}")
        paused = data.get("proceed_awaited", False)
        parts.append(f"*Paused:* {'yes' if paused else 'no'}")
    else:
        parts.append("_(no checkpoint)_")

    return "\n".join(parts)


def _handle_ws_pause() -> str:
    """Write proceed_awaited=true to checkpoint."""
    root = find_project_root()
    ckpt_path = root / ".aho-checkpoint.json"
    if not ckpt_path.exists():
        return "_(no checkpoint to pause)_"
    data = json.loads(ckpt_path.read_text())
    data["proceed_awaited"] = True
    ckpt_path.write_text(json.dumps(data, indent=2) + "\n")
    return f"Paused at next WS boundary. Current: {data.get('current_workstream', '?')}"


def _handle_ws_proceed() -> str:
    """Write proceed_awaited=false to checkpoint."""
    root = find_project_root()
    ckpt_path = root / ".aho-checkpoint.json"
    if not ckpt_path.exists():
        return "_(no checkpoint)_"
    data = json.loads(ckpt_path.read_text())
    data["proceed_awaited"] = False
    ckpt_path.write_text(json.dumps(data, indent=2) + "\n")
    return "Proceeding. proceed\\_awaited cleared."


def _handle_ws_last() -> str:
    """Read last workstream_complete event from event log."""
    from aho.paths import get_data_dir
    log_path = get_data_dir() / "aho_event_log.jsonl"
    if not log_path.exists():
        return "_(no event log)_"

    last_complete = None
    for line in log_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("event_type") == "workstream_complete":
                last_complete = ev
        except json.JSONDecodeError:
            continue

    if not last_complete:
        return "_(no workstream\\_complete events found)_"

    ws_id = last_complete.get("workstream_id", "?")
    status = last_complete.get("status", "?")
    iteration = last_complete.get("iteration", "?")
    summary = last_complete.get("output_summary", "")
    ts = last_complete.get("timestamp", "?")
    return f"*Last WS:* {ws_id} ({iteration})\n*Status:* {status}\n*Summary:* {summary}\n*Time:* {ts}"


# Command dispatch table
_HELP_TEXT = (
    "aho harness bot. Commands:\n"
    "/status — system health\n"
    "/iteration — current iteration\n"
    "/last — same as /iteration\n"
    "/ws status — workstream state\n"
    "/ws pause — pause at next WS boundary\n"
    "/ws proceed — resume execution\n"
    "/ws last — last completed workstream\n"
    "/help — this message\n\n"
    "Free text → dispatched to openclaw."
)

COMMANDS = {
    "/start": lambda: _HELP_TEXT,
    "/help": lambda: _HELP_TEXT,
    "/status": _handle_status_info,
    "/iteration": _handle_iteration_info,
    "/last": _handle_iteration_info,
}

# /ws subcommand dispatch
WS_COMMANDS = {
    "status": _handle_ws_status,
    "pause": _handle_ws_pause,
    "proceed": _handle_ws_proceed,
    "last": _handle_ws_last,
}


def _route_message(token: str, chat_id: int, text: str):
    """Route an incoming message to the appropriate handler."""
    text_stripped = text.strip()
    parts = text_stripped.split()
    cmd = parts[0].lower() if parts else ""

    # /ws subcommand routing
    if cmd == "/ws":
        subcmd = parts[1].lower() if len(parts) > 1 else ""
        if subcmd in WS_COMMANDS:
            reply = WS_COMMANDS[subcmd]()
        else:
            reply = "Usage: /ws {status|pause|proceed|last}"
        _send_reply(token, chat_id, reply)
        return

    if cmd in COMMANDS:
        reply = COMMANDS[cmd]()
        _send_reply(token, chat_id, reply)
        return

    # Free-text → openclaw
    timeout = _get_openclaw_timeout()
    result = send_chat(text_stripped, timeout=timeout)

    if result.get("timed_out"):
        # Async ack: tell user we're working on it
        _send_reply(token, chat_id, "⏳ dispatched to openclaw, processing…")
        # Fire async retry with longer timeout
        def _async_retry():
            retry_result = send_chat(text_stripped, timeout=300.0)
            reply = _format_openclaw_response(retry_result)
            _send_reply(token, chat_id, reply)
        t = threading.Thread(target=_async_retry, daemon=True)
        t.start()
    else:
        reply = _format_openclaw_response(result)
        _send_reply(token, chat_id, reply)


def poll_loop(stop_event: threading.Event = None):
    """Long-poll getUpdates in a loop. Runs until stop_event is set."""
    token = get_secret(PROJECT, "telegram_bot_token")
    chat_id_str = get_secret(PROJECT, "telegram_chat_id")

    if not token or not chat_id_str:
        print("[telegram-inbound] missing credentials, cannot start", flush=True)
        return

    allowed_chat_ids = {int(chat_id_str)}
    offset = _load_offset()
    url = f"{BASE_URL.format(token=token)}/getUpdates"

    print(f"[telegram-inbound] polling started, allowed chats: {allowed_chat_ids}", flush=True)

    while not (stop_event and stop_event.is_set()):
        try:
            params = {
                "offset": offset + 1 if offset else None,
                "timeout": 30,
                "allowed_updates": json.dumps(["message"]),
            }
            # Remove None params
            params = {k: v for k, v in params.items() if v is not None}

            resp = requests.get(url, params=params, timeout=35)
            if not resp.ok:
                time.sleep(5)
                continue

            data = resp.json()
            updates = data.get("result", [])

            for update in updates:
                update_id = update.get("update_id", 0)
                if update_id > offset:
                    offset = update_id
                    _save_offset(offset)

                msg = update.get("message", {})
                msg_chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")

                if not text or msg_chat_id not in allowed_chat_ids:
                    continue

                try:
                    _route_message(token, msg_chat_id, text)
                except Exception as e:
                    print(f"[telegram-inbound] route error: {e}", flush=True)

        except requests.exceptions.Timeout:
            continue  # Normal for long polling
        except Exception as e:
            print(f"[telegram-inbound] poll error: {e}", flush=True)
            time.sleep(5)


def _auto_push_loop(token: str, chat_id: int, stop_event: threading.Event):
    """Watch aho_event_log.jsonl for new workstream_complete events, push to Telegram.

    Tails the file by tracking position. Checks every 5 seconds.
    Only fires once per event (position advances past it).
    """
    from aho.paths import get_data_dir
    log_path = get_data_dir() / "aho_event_log.jsonl"

    # Start at end of file to avoid replaying history
    pos = log_path.stat().st_size if log_path.exists() else 0

    while not (stop_event and stop_event.is_set()):
        time.sleep(5)
        if not log_path.exists():
            continue
        try:
            current_size = log_path.stat().st_size
            if current_size <= pos:
                continue
            with open(log_path, "r") as f:
                f.seek(pos)
                new_lines = f.read()
                pos = f.tell()
            for line in new_lines.splitlines():
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("event_type") == "workstream_complete":
                        ws_id = ev.get("workstream_id", "?")
                        iteration = ev.get("iteration", "?")
                        status = ev.get("status", "?")
                        summary = ev.get("output_summary", "")
                        msg = f"[WS] {ws_id} ({iteration}) → {status}\n{summary}"
                        _send_reply(token, chat_id, msg)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"[telegram-auto-push] error: {e}", flush=True)


def start_inbound_thread() -> threading.Event:
    """Start the inbound poll loop in a daemon thread. Returns stop event."""
    stop = threading.Event()
    t = threading.Thread(target=poll_loop, args=(stop,), daemon=True, name="telegram-inbound")
    t.start()
    print("[telegram-inbound] thread started", flush=True)

    # Start auto-push subscriber thread
    try:
        token = get_secret(PROJECT, "telegram_bot_token")
        chat_id_str = get_secret(PROJECT, "telegram_chat_id")
        if token and chat_id_str:
            ap = threading.Thread(
                target=_auto_push_loop,
                args=(token, int(chat_id_str), stop),
                daemon=True,
                name="telegram-auto-push",
            )
            ap.start()
            print("[telegram-auto-push] subscriber started", flush=True)
    except Exception as e:
        print(f"[telegram-auto-push] failed to start: {e}", flush=True)

    return stop
