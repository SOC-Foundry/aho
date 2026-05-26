"""aho-alerts-bridge - Alertmanager-webhook → dedicated Telegram channel.

Posts each alert from an Alertmanager-shaped webhook payload to the dedicated
alerts chat (distinct from the routine-notification chat used by
``aho.telegram.notifications``) and appends a one-line audit entry to
``~/.local/share/aho/events/aho_event_log.jsonl`` via ``aho.logger.log_event``
with ``event_type`` of ``pillar_11_violation`` or ``anomaly``.

0.2.16 W3 status: bridge code + mocked unit tests. Live engine wire-up is
DEFERRED - no alert engine is yet present on the host. The dedicated secrets
``ahomw:telegram_alerts_bot_token`` / ``ahomw:telegram_alerts_chat_id`` are
also pending Kyle creation per Pillar 11. Both deferrals are tracked as
W3 carry-forwards in ``artifacts/iterations/0.2.16/pillar-11-monitoring-notes.md``
§"Deferred verification".

Failure model (G083 - no ``except Exception``):
- Missing secret → ``AlertSecretMissingError`` → HTTP 503 to engine
- Telegram timeout / connection error / non-2xx → ``TelegramAPIError`` → HTTP 502
- Malformed webhook payload → ``WebhookPayloadError`` → HTTP 400
- Event-log append IO failure → ``OSError`` propagates → HTTP 500

Silent swallowing is forbidden. Alert delivery without an audit-log entry is
invisible to Pillar 11 enforcement, so the bridge fails loud and lets the
engine retry per its own policy.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import requests

from aho.logger import log_event
from aho.secrets.store import get_secret


PROJECT = "ahomw"
TOKEN_KEY = "telegram_alerts_bot_token"
CHAT_KEY = "telegram_alerts_chat_id"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
SOURCE_AGENT = "aho-alerts-bridge"

# W2 D3: bidirectional alert bridge to a central aggregator (Beacon).
# Both directions are env-driven and additive. If BEACON_WEBHOOK_URL is unset
# the outbound mirror is a no-op and the Telegram-only path is unchanged.
import os  # noqa: E402 - local to the bridge-config block


def _beacon_webhook_url() -> str | None:
    url = os.environ.get("BEACON_WEBHOOK_URL", "").strip()
    return url or None


def _beacon_webhook_token() -> str | None:
    tok = os.environ.get("BEACON_WEBHOOK_TOKEN", "").strip()
    return tok or None

PILLAR_11_ALERTNAMES = frozenset({
    "Pillar11CommitViolation",
    "Pillar11PullRequestViolation",
})


class AlertSecretMissingError(RuntimeError):
    """Alerts-channel secret is absent or empty in the store.

    Distinct from the secret-store's ``RuntimeError("Session locked")``: this
    class indicates Kyle has not yet provisioned the secret pair.
    """


class TelegramAPIError(RuntimeError):
    """Telegram Bot API returned non-2xx, timed out, or had a non-JSON body."""

    def __init__(self, status_code: int, body: str):
        super().__init__(f"telegram api status={status_code}")
        self.status_code = status_code
        self.body = body


class WebhookPayloadError(ValueError):
    """Webhook payload is missing required Alertmanager fields."""


def classify_event_type(alertname: str) -> str:
    """Pillar-11 alertnames map to ``pillar_11_violation``; everything else to ``anomaly``."""
    return "pillar_11_violation" if alertname in PILLAR_11_ALERTNAMES else "anomaly"


def _get_alert_creds() -> tuple[str, str]:
    token = get_secret(PROJECT, TOKEN_KEY)
    chat_id = get_secret(PROJECT, CHAT_KEY)
    if not token:
        raise AlertSecretMissingError(f"missing secret {PROJECT}:{TOKEN_KEY}")
    if not chat_id:
        raise AlertSecretMissingError(f"missing secret {PROJECT}:{CHAT_KEY}")
    return token, chat_id


def format_alert_message(alert: dict) -> str:
    """Render one alert's labels+annotations as Markdown text for Telegram."""
    labels = alert.get("labels") or {}
    annotations = alert.get("annotations") or {}
    name = labels.get("alertname") or "(unknown)"
    severity = labels.get("severity") or "info"
    status = alert.get("status") or "firing"
    summary = annotations.get("summary") or ""
    description = annotations.get("description") or ""

    lines = [
        f"*[{severity.upper()}]* {name}",
        f"status: {status}",
    ]
    if summary:
        lines.append(f"summary: {summary}")
    if description:
        lines.append(f"description: {description}")
    return "\n".join(lines)


def telegram_post(message: str, *, timeout: float = 10.0) -> dict:
    """POST one message to the dedicated alerts chat. Raises on any failure."""
    token, chat_id = _get_alert_creds()
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json=payload,
            timeout=timeout,
        )
    except requests.Timeout as e:
        raise TelegramAPIError(0, f"timeout: {e}") from e
    except requests.ConnectionError as e:
        raise TelegramAPIError(0, f"connection error: {e}") from e

    if not resp.ok:
        raise TelegramAPIError(resp.status_code, (resp.text or "")[:500])

    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise TelegramAPIError(resp.status_code, f"non-json body: {e}") from e


def event_log_append(alert: dict, event_type: str) -> None:
    """Append a one-line audit entry. Propagates ``OSError`` on IO failure."""
    labels = alert.get("labels") or {}
    annotations = alert.get("annotations") or {}
    name = labels.get("alertname") or "(unknown)"
    summary = (annotations.get("summary") or "")[:200]
    log_event(
        event_type=event_type,
        source_agent=SOURCE_AGENT,
        target="telegram-alerts-channel",
        action="alert_delivery",
        input_summary=name,
        output_summary=summary,
        status="success",
    )


def beacon_post(alert: dict, *, timeout: float = 10.0) -> bool:
    """Mirror one alert outbound to the central aggregator (Beacon) webhook.

    No-op (returns False) when BEACON_WEBHOOK_URL is unset - the Telegram path
    is the always-on default and Beacon mirroring is additive. Returns True on
    a 2xx from Beacon. Network/HTTP failures are swallowed with an event-log
    note: a Beacon-side outage must never block Telegram delivery (which has
    already succeeded by the time this is called).
    """
    url = _beacon_webhook_url()
    if not url:
        return False
    headers = {"Content-Type": "application/json"}
    token = _beacon_webhook_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    labels = alert.get("labels") or {}
    annotations = alert.get("annotations") or {}
    body = {
        "source": "aho",
        "alertname": labels.get("alertname") or "(unknown)",
        "severity": labels.get("severity") or "info",
        "status": alert.get("status") or "firing",
        "summary": annotations.get("summary") or "",
        "description": annotations.get("description") or "",
        "labels": labels,
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout)
        if 200 <= resp.status_code < 300:
            return True
        log_event(
            event_type="anomaly", source_agent=SOURCE_AGENT, target="beacon-webhook",
            action="beacon_mirror", input_summary=body["alertname"],
            output_summary=f"beacon non-2xx status={resp.status_code}", status="error",
        )
        return False
    except (requests.Timeout, requests.ConnectionError, requests.RequestException) as e:
        log_event(
            event_type="anomaly", source_agent=SOURCE_AGENT, target="beacon-webhook",
            action="beacon_mirror", input_summary=body["alertname"],
            output_summary=f"beacon unreachable: {type(e).__name__}", status="error",
        )
        return False


def webhook_handler(payload: dict) -> dict:
    """Process one Alertmanager webhook POST body.

    Returns a counts dict ``{"ok": True, "delivered": N, "events_logged": N,
    "beacon_mirrored": N}``. Order per alert: Telegram post first (always-on),
    then event-log append, then best-effort Beacon mirror. If Telegram fails,
    the event-log entry is not written and the engine retries per its own
    policy. If event-log append fails AFTER Telegram succeeded, the OSError
    propagates. Beacon mirror failure never propagates (Telegram already
    delivered) - it is logged and counted but does not fail the request.
    """
    if not isinstance(payload, dict):
        raise WebhookPayloadError("payload root must be a JSON object")
    alerts = payload.get("alerts")
    if not isinstance(alerts, list):
        raise WebhookPayloadError("payload.alerts must be a list")

    delivered = 0
    logged = 0
    mirrored = 0
    for alert in alerts:
        if not isinstance(alert, dict):
            raise WebhookPayloadError("each alert entry must be an object")
        labels = alert.get("labels") or {}
        alertname = labels.get("alertname") or "(unknown)"
        event_type = classify_event_type(alertname)
        message = format_alert_message(alert)

        telegram_post(message)
        delivered += 1
        event_log_append(alert, event_type)
        logged += 1
        if beacon_post(alert):
            mirrored += 1

    return {"ok": True, "delivered": delivered, "events_logged": logged,
            "beacon_mirrored": mirrored}


def beacon_inbound_handler(payload: dict) -> dict:
    """Process one Beacon-shaped inbound webhook (Beacon -> aho -> Telegram).

    Beacon escalations (host-down, GPU-stuck, etc.) reach the same Telegram
    channel the operator already watches. Tolerant of shape variation: extracts
    title/summary/message + severity from common key names. The exact Beacon
    webhook schema is a Track B input (Beacon dev surfaces it); this handler
    accepts the documented-generic shape and degrades gracefully on unknown
    keys.

    Returns ``{"ok": True, "delivered": N}``.
    """
    if not isinstance(payload, dict):
        raise WebhookPayloadError("payload root must be a JSON object")

    # A Beacon payload may be a single alert object or carry an "alerts" list.
    items = payload.get("alerts")
    if not isinstance(items, list):
        items = [payload]

    delivered = 0
    for item in items:
        if not isinstance(item, dict):
            raise WebhookPayloadError("each beacon alert entry must be an object")
        title = item.get("title") or item.get("alertname") or item.get("summary") or "(beacon alert)"
        severity = item.get("severity") or "info"
        message = item.get("message") or item.get("description") or item.get("summary") or ""
        text = f"*[beacon:{severity}]* {title}"
        if message:
            text += f"\n{message}"
        telegram_post(text)
        delivered += 1
        log_event(
            event_type="anomaly", source_agent=SOURCE_AGENT,
            target="telegram-alerts-channel", action="beacon_inbound_relay",
            input_summary=str(title)[:200], output_summary=str(message)[:200],
            status="success",
        )

    return {"ok": True, "delivered": delivered}


# --- HTTP server entry point ---
# DEFERRED: not wired in 0.2.16. Once an alert engine is selected, register
# this listener as the engine's webhook receiver and stand up a systemd user
# unit running ``python -m aho.alerts.telegram_alerts --serve``.

class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP receiver for engine-emitted webhooks."""

    def do_POST(self) -> None:  # noqa: N802 - stdlib API
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError:
            self._reply(400, {"ok": False, "error": "invalid content-length"})
            return
        body = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._reply(400, {"ok": False, "error": f"json decode: {e}"})
            return

        # Path routing: /beacon = Beacon-shaped inbound relay to Telegram;
        # anything else = Alertmanager-shaped (the existing default path).
        route_path = self.path.split("?")[0].rstrip("/")
        handler = beacon_inbound_handler if route_path == "/beacon" else webhook_handler

        try:
            result = handler(payload)
        except WebhookPayloadError as e:
            self._reply(400, {"ok": False, "error": str(e)})
            return
        except AlertSecretMissingError as e:
            self._reply(503, {"ok": False, "error": str(e)})
            return
        except TelegramAPIError as e:
            self._reply(502, {"ok": False, "error": str(e), "status_code": e.status_code})
            return
        except OSError as e:
            self._reply(500, {"ok": False, "error": f"event-log io: {e}"})
            return

        self._reply(200, result)

    def _reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: Any) -> None:
        return  # silence default stderr access log


def serve(host: str = "127.0.0.1", port: int = 9095) -> None:
    server = HTTPServer((host, port), BridgeHandler)
    print(f"[aho-alerts-bridge] listening on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    else:
        print("Usage: python -m aho.alerts.telegram_alerts --serve")
        print("DEFERRED: live wire-up requires alert engine selection.")
        print("See artifacts/iterations/0.2.16/pillar-11-monitoring-notes.md")
        sys.exit(1)
