"""Tests for Telegram bridge real implementation — send, capability_gap, close_complete."""
import json
from unittest.mock import MagicMock, patch

import pytest


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_success(mock_get_secret, mock_post):
    """send() posts to Telegram API and returns True on success."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "test-token-123",
        "telegram_chat_id": "7308867003",
    }[name]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from aho.telegram.notifications import send
    result = send("test message", priority="normal")
    assert result is True
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1] if len(call_args[0]) > 1 else None
    # Verify the payload structure
    assert payload is not None or "json" in call_args[1]


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_payload_shape(mock_get_secret, mock_post):
    """Verify payload contains chat_id, text, parse_mode."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "tok",
        "telegram_chat_id": "123",
    }[name]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from aho.telegram.notifications import send
    send("hello world")
    payload = mock_post.call_args[1]["json"]
    assert payload["chat_id"] == "123"
    assert "hello world" in payload["text"]
    assert payload["parse_mode"] == "Markdown"


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_high_priority_prefix(mock_get_secret, mock_post):
    """High priority messages get [!] prefix."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "tok",
        "telegram_chat_id": "123",
    }[name]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from aho.telegram.notifications import send
    send("alert!", priority="high")
    payload = mock_post.call_args[1]["json"]
    assert "[!]" in payload["text"]


@patch("aho.telegram.notifications.get_secret")
def test_send_missing_token(mock_get_secret):
    """send() returns False when token is missing."""
    mock_get_secret.return_value = None

    from aho.telegram.notifications import send
    result = send("test")
    assert result is False


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_capability_gap(mock_get_secret, mock_post):
    """send_capability_gap formats message with CAPABILITY GAP prefix."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "tok",
        "telegram_chat_id": "123",
    }[name]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from aho.telegram.notifications import send_capability_gap
    result = send_capability_gap("secrets session locked")
    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert "CAPABILITY GAP" in payload["text"]


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_close_complete(mock_get_secret, mock_post):
    """send_close_complete sends iteration close notification."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "tok",
        "telegram_chat_id": "123",
    }[name]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from aho.telegram.notifications import send_close_complete
    result = send_close_complete("0.2.2", "closed")
    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert "0.2.2" in payload["text"]
    assert "closed" in payload["text"]


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_rate_limit_retry(mock_get_secret, mock_post):
    """send() retries on 429 rate limit."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "tok",
        "telegram_chat_id": "123",
    }[name]
    rate_resp = MagicMock()
    rate_resp.status_code = 429
    rate_resp.ok = False
    rate_resp.json.return_value = {"parameters": {"retry_after": 0}}

    ok_resp = MagicMock()
    ok_resp.status_code = 200
    ok_resp.ok = True

    mock_post.side_effect = [rate_resp, ok_resp]

    from aho.telegram.notifications import send
    result = send("retry test")
    assert result is True
    assert mock_post.call_count == 2


@patch("aho.telegram.notifications.requests.post")
@patch("aho.telegram.notifications.get_secret")
def test_send_network_error(mock_get_secret, mock_post):
    """send() returns False on network error."""
    mock_get_secret.side_effect = lambda proj, name: {
        "telegram_bot_token": "tok",
        "telegram_chat_id": "123",
    }[name]
    mock_post.side_effect = Exception("connection refused")

    from aho.telegram.notifications import send
    result = send("test")
    assert result is False
