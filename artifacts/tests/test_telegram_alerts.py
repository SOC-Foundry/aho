"""Unit tests for aho.alerts.telegram_alerts (0.2.16 W3).

All tests use mocked Telegram API responses and patched secrets — no live
network calls and no real Telegram credentials. Live engine wire-up is
deferred (see pillar-11-monitoring-notes.md §"Deferred verification"); the
end-to-end synthetic delivery test (W3 bucket 5) is also deferred until the
alert engine is selected.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from aho.alerts import telegram_alerts as ta


# ---------- classify_event_type ----------

@pytest.mark.parametrize("alertname,expected", [
    ("Pillar11CommitViolation", "pillar_11_violation"),
    ("Pillar11PullRequestViolation", "pillar_11_violation"),
    ("ClaudeAPIErrorSpike", "anomaly"),
    ("ClaudeCostAnomaly", "anomaly"),
    ("ToolDurationOutlier", "anomaly"),
    ("UnknownFutureRule", "anomaly"),
    ("(unknown)", "anomaly"),
])
def test_classify_event_type(alertname, expected):
    assert ta.classify_event_type(alertname) == expected


# ---------- format_alert_message ----------

def _alert(name="Pillar11CommitViolation", severity="critical",
           status="firing", summary="s", description="d"):
    return {
        "status": status,
        "labels": {"alertname": name, "severity": severity},
        "annotations": {"summary": summary, "description": description},
    }


def test_format_alert_message_full():
    msg = ta.format_alert_message(_alert())
    assert "*[CRITICAL]*" in msg
    assert "Pillar11CommitViolation" in msg
    assert "status: firing" in msg
    assert "summary: s" in msg
    assert "description: d" in msg


def test_format_alert_message_missing_annotations():
    alert = {"status": "firing", "labels": {"alertname": "X", "severity": "info"}}
    msg = ta.format_alert_message(alert)
    assert "*[INFO]*" in msg
    assert "X" in msg
    assert "summary:" not in msg
    assert "description:" not in msg


def test_format_alert_message_missing_alertname():
    alert = {"labels": {"severity": "info"}, "annotations": {}}
    msg = ta.format_alert_message(alert)
    assert "(unknown)" in msg


# ---------- _get_alert_creds + AlertSecretMissingError ----------

def test_get_alert_creds_happy(monkeypatch):
    monkeypatch.setattr(ta, "get_secret",
                        lambda p, k: {"telegram_alerts_bot_token": "tok",
                                      "telegram_alerts_chat_id": "123"}[k])
    assert ta._get_alert_creds() == ("tok", "123")


def test_get_alert_creds_missing_token(monkeypatch):
    monkeypatch.setattr(ta, "get_secret",
                        lambda p, k: None if k == "telegram_alerts_bot_token" else "123")
    with pytest.raises(ta.AlertSecretMissingError) as excinfo:
        ta._get_alert_creds()
    assert "telegram_alerts_bot_token" in str(excinfo.value)


def test_get_alert_creds_missing_chat(monkeypatch):
    monkeypatch.setattr(ta, "get_secret",
                        lambda p, k: "tok" if k == "telegram_alerts_bot_token" else None)
    with pytest.raises(ta.AlertSecretMissingError) as excinfo:
        ta._get_alert_creds()
    assert "telegram_alerts_chat_id" in str(excinfo.value)


def test_get_alert_creds_empty_string_treated_missing(monkeypatch):
    monkeypatch.setattr(ta, "get_secret", lambda p, k: "")
    with pytest.raises(ta.AlertSecretMissingError):
        ta._get_alert_creds()


# ---------- telegram_post ----------

def _stub_creds(monkeypatch):
    monkeypatch.setattr(ta, "get_secret",
                        lambda p, k: "tok" if k == ta.TOKEN_KEY else "123")


def test_telegram_post_success(monkeypatch):
    _stub_creds(monkeypatch)
    resp = MagicMock(ok=True, status_code=200)
    resp.json.return_value = {"ok": True, "result": {"message_id": 42}}
    posted = {}

    def fake_post(url, json=None, timeout=None):
        posted["url"] = url
        posted["json"] = json
        posted["timeout"] = timeout
        return resp

    monkeypatch.setattr(ta.requests, "post", fake_post)
    out = ta.telegram_post("hello")
    assert out["result"]["message_id"] == 42
    assert posted["url"] == "https://api.telegram.org/bottok/sendMessage"
    assert posted["json"]["chat_id"] == "123"
    assert posted["json"]["text"] == "hello"
    assert posted["json"]["parse_mode"] == "Markdown"
    assert posted["timeout"] == 10.0


def test_telegram_post_non_2xx_raises(monkeypatch):
    _stub_creds(monkeypatch)
    resp = MagicMock(ok=False, status_code=429, text="rate limited")
    monkeypatch.setattr(ta.requests, "post", lambda *a, **k: resp)
    with pytest.raises(ta.TelegramAPIError) as excinfo:
        ta.telegram_post("x")
    assert excinfo.value.status_code == 429
    assert "rate limited" in excinfo.value.body


def test_telegram_post_timeout_raises(monkeypatch):
    _stub_creds(monkeypatch)

    def boom(*a, **k):
        raise requests.Timeout("upstream timeout")

    monkeypatch.setattr(ta.requests, "post", boom)
    with pytest.raises(ta.TelegramAPIError) as excinfo:
        ta.telegram_post("x")
    assert excinfo.value.status_code == 0
    assert "timeout" in excinfo.value.body.lower()


def test_telegram_post_connection_error_raises(monkeypatch):
    _stub_creds(monkeypatch)

    def boom(*a, **k):
        raise requests.ConnectionError("dns fail")

    monkeypatch.setattr(ta.requests, "post", boom)
    with pytest.raises(ta.TelegramAPIError) as excinfo:
        ta.telegram_post("x")
    assert excinfo.value.status_code == 0


def test_telegram_post_non_json_body_raises(monkeypatch):
    _stub_creds(monkeypatch)
    resp = MagicMock(ok=True, status_code=200, text="<html>not json</html>")
    resp.json.side_effect = json.JSONDecodeError("expecting value", "<html>", 0)
    monkeypatch.setattr(ta.requests, "post", lambda *a, **k: resp)
    with pytest.raises(ta.TelegramAPIError):
        ta.telegram_post("x")


def test_telegram_post_secret_missing_propagates(monkeypatch):
    monkeypatch.setattr(ta, "get_secret", lambda p, k: None)
    with pytest.raises(ta.AlertSecretMissingError):
        ta.telegram_post("x")


# ---------- event_log_append ----------

def test_event_log_append_writes_jsonl(monkeypatch, tmp_path):
    log_file = tmp_path / "aho_event_log.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))

    alert = _alert(name="Pillar11CommitViolation", summary="commit observed")
    ta.event_log_append(alert, "pillar_11_violation")

    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event_type"] == "pillar_11_violation"
    assert record["source_agent"] == ta.SOURCE_AGENT
    assert record["target"] == "telegram-alerts-channel"
    assert record["action"] == "alert_delivery"
    assert record["input_summary"] == "Pillar11CommitViolation"
    assert "commit observed" in record["output_summary"]
    assert record["status"] == "success"


def test_event_log_append_missing_dir_raises(monkeypatch, tmp_path):
    # Point LOG_PATH at a path whose parent is a regular file, not a dir.
    blocker = tmp_path / "blocker"
    blocker.write_text("")
    bad_path = blocker / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(bad_path))

    with pytest.raises((OSError, NotADirectoryError, FileExistsError)):
        ta.event_log_append(_alert(), "anomaly")


# ---------- webhook_handler ----------

def _alertmanager_payload(*alerts):
    return {
        "version": "4",
        "groupKey": "{}:{alertname=\"x\"}",
        "status": "firing",
        "receiver": "aho-alerts-bridge",
        "groupLabels": {},
        "commonLabels": {},
        "commonAnnotations": {},
        "externalURL": "http://localhost:9093",
        "alerts": list(alerts),
    }


def _stub_telegram(monkeypatch, sent):
    _stub_creds(monkeypatch)
    resp = MagicMock(ok=True, status_code=200)
    resp.json.return_value = {"ok": True}

    def post(url, json=None, timeout=None):
        sent.append(json)
        return resp

    monkeypatch.setattr(ta.requests, "post", post)


def test_webhook_handler_pillar_11(monkeypatch, tmp_path):
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))
    sent = []
    _stub_telegram(monkeypatch, sent)

    payload = _alertmanager_payload(_alert(name="Pillar11CommitViolation"))
    out = ta.webhook_handler(payload)

    assert out == {"ok": True, "delivered": 1, "events_logged": 1}
    assert len(sent) == 1
    assert "Pillar11CommitViolation" in sent[0]["text"]
    record = json.loads(log_file.read_text().splitlines()[0])
    assert record["event_type"] == "pillar_11_violation"


def test_webhook_handler_anomaly(monkeypatch, tmp_path):
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))
    sent = []
    _stub_telegram(monkeypatch, sent)

    payload = _alertmanager_payload(_alert(name="ClaudeCostAnomaly", severity="important"))
    out = ta.webhook_handler(payload)

    assert out["delivered"] == 1
    record = json.loads(log_file.read_text().splitlines()[0])
    assert record["event_type"] == "anomaly"


def test_webhook_handler_multiple_alerts(monkeypatch, tmp_path):
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))
    sent = []
    _stub_telegram(monkeypatch, sent)

    payload = _alertmanager_payload(
        _alert(name="Pillar11CommitViolation"),
        _alert(name="ClaudeAPIErrorSpike", severity="important"),
        _alert(name="ToolDurationOutlier", severity="info"),
    )
    out = ta.webhook_handler(payload)

    assert out == {"ok": True, "delivered": 3, "events_logged": 3}
    assert len(sent) == 3
    types = [json.loads(line)["event_type"] for line in log_file.read_text().splitlines()]
    assert types == ["pillar_11_violation", "anomaly", "anomaly"]


def test_webhook_handler_empty_alerts_list(monkeypatch, tmp_path):
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))
    sent = []
    _stub_telegram(monkeypatch, sent)

    out = ta.webhook_handler(_alertmanager_payload())
    assert out == {"ok": True, "delivered": 0, "events_logged": 0}
    assert sent == []
    assert not log_file.exists() or log_file.read_text() == ""


def test_webhook_handler_non_dict_payload_raises():
    with pytest.raises(ta.WebhookPayloadError):
        ta.webhook_handler("not a dict")  # type: ignore[arg-type]


def test_webhook_handler_alerts_not_list_raises():
    with pytest.raises(ta.WebhookPayloadError):
        ta.webhook_handler({"alerts": "not a list"})


def test_webhook_handler_alert_not_object_raises():
    with pytest.raises(ta.WebhookPayloadError):
        ta.webhook_handler({"alerts": ["not an object"]})


def test_webhook_handler_telegram_failure_aborts_before_log(monkeypatch, tmp_path):
    """If Telegram POST fails, event log MUST NOT be written for that alert.

    Order is: telegram_post → event_log_append. A Telegram failure must
    propagate before the log is appended, so the engine retry produces a
    single audit entry on eventual success rather than two.
    """
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))
    _stub_creds(monkeypatch)
    resp = MagicMock(ok=False, status_code=500, text="boom")
    monkeypatch.setattr(ta.requests, "post", lambda *a, **k: resp)

    with pytest.raises(ta.TelegramAPIError):
        ta.webhook_handler(_alertmanager_payload(_alert()))

    # Log must be empty — Telegram failed, so we must not have appended.
    assert not log_file.exists() or log_file.read_text() == ""


def test_webhook_handler_secret_missing_propagates(monkeypatch, tmp_path):
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))
    monkeypatch.setattr(ta, "get_secret", lambda p, k: None)

    with pytest.raises(ta.AlertSecretMissingError):
        ta.webhook_handler(_alertmanager_payload(_alert()))

    assert not log_file.exists() or log_file.read_text() == ""


def test_webhook_handler_session_locked_propagates(monkeypatch, tmp_path):
    """If the secret store session is locked, get_secret raises RuntimeError.

    The bridge must NOT swallow it (G083 — no except Exception). The
    RuntimeError propagates and the engine sees an HTTP 500.
    """
    log_file = tmp_path / "events.jsonl"
    monkeypatch.setattr("aho.logger.LOG_PATH", str(log_file))

    def locked(*a, **k):
        raise RuntimeError("Session locked. Run 'aho secret unlock' first.")

    monkeypatch.setattr(ta, "get_secret", locked)
    with pytest.raises(RuntimeError, match="Session locked"):
        ta.webhook_handler(_alertmanager_payload(_alert()))


# ---------- BridgeHandler HTTP envelope behavior (no live socket) ----------
# These test the do_POST exception → status code mapping by invoking the
# handler in isolation with a stub rfile/wfile pair, which avoids binding
# a real port.

class _StubRequest:
    def __init__(self, body: bytes):
        self._body = body
        self.sent = bytearray()

    def makefile(self, mode, *args):
        import io
        if mode == "rb":
            return io.BytesIO(self._body)
        return _StubWriter(self.sent)


class _StubWriter:
    def __init__(self, buf):
        self._buf = buf

    def write(self, b):
        self._buf.extend(b)

    def flush(self):
        pass


def _invoke_handler(body_bytes: bytes, content_length: int | None = None):
    req = _StubRequest(b"")
    handler = ta.BridgeHandler.__new__(ta.BridgeHandler)
    handler.rfile = type("R", (), {"read": lambda self, n: body_bytes[:n]})()
    handler.wfile = type("W", (), {"write": lambda self, b: req.sent.extend(b),
                                    "flush": lambda self: None})()
    cl = str(content_length if content_length is not None else len(body_bytes))
    handler.headers = {"Content-Length": cl}

    captured = {}

    def fake_send_response(code):
        captured["code"] = code

    def fake_send_header(k, v):
        captured.setdefault("headers", []).append((k, v))

    def fake_end_headers():
        pass

    handler.send_response = fake_send_response
    handler.send_header = fake_send_header
    handler.end_headers = fake_end_headers
    handler.do_POST()
    return captured, bytes(req.sent)


def test_bridge_handler_invalid_content_length():
    captured, body = _invoke_handler(b"")
    # Default headers dict has CL=0 here; this exercises the empty-body path.
    # Force-invalid CL via a separate call:
    req = _StubRequest(b"")
    handler = ta.BridgeHandler.__new__(ta.BridgeHandler)
    handler.rfile = type("R", (), {"read": lambda self, n: b""})()
    handler.wfile = type("W", (), {"write": lambda self, b: req.sent.extend(b),
                                    "flush": lambda self: None})()
    handler.headers = {"Content-Length": "abc"}
    captured = {}
    handler.send_response = lambda c: captured.setdefault("code", c)
    handler.send_header = lambda *a: None
    handler.end_headers = lambda: None
    handler.do_POST()
    assert captured["code"] == 400


def test_bridge_handler_malformed_json():
    captured, _ = _invoke_handler(b"{not-json")
    assert captured["code"] == 400


def test_bridge_handler_payload_error_returns_400(monkeypatch):
    captured, _ = _invoke_handler(b'{"alerts": "not a list"}')
    assert captured["code"] == 400


def test_bridge_handler_secret_missing_returns_503(monkeypatch, tmp_path):
    monkeypatch.setattr("aho.logger.LOG_PATH", str(tmp_path / "events.jsonl"))
    monkeypatch.setattr(ta, "get_secret", lambda p, k: None)
    payload = json.dumps(_alertmanager_payload(_alert())).encode()
    captured, _ = _invoke_handler(payload)
    assert captured["code"] == 503


def test_bridge_handler_telegram_error_returns_502(monkeypatch, tmp_path):
    monkeypatch.setattr("aho.logger.LOG_PATH", str(tmp_path / "events.jsonl"))
    _stub_creds(monkeypatch)
    resp = MagicMock(ok=False, status_code=429, text="rate limited")
    monkeypatch.setattr(ta.requests, "post", lambda *a, **k: resp)
    payload = json.dumps(_alertmanager_payload(_alert())).encode()
    captured, _ = _invoke_handler(payload)
    assert captured["code"] == 502


def test_bridge_handler_success_returns_200(monkeypatch, tmp_path):
    monkeypatch.setattr("aho.logger.LOG_PATH", str(tmp_path / "events.jsonl"))
    sent = []
    _stub_telegram(monkeypatch, sent)
    payload = json.dumps(_alertmanager_payload(_alert())).encode()
    captured, _ = _invoke_handler(payload)
    assert captured["code"] == 200
    assert sent  # message was sent
