"""Tests for Telegram inbound bridge — routing, openclaw client, formatting."""
import json
import socket
import threading
from unittest.mock import patch, MagicMock
import pytest

from aho.telegram.inbound import (
    _route_message,
    _handle_iteration_info,
    _handle_status_info,
    _format_openclaw_response,
    _load_offset,
    _save_offset,
    COMMANDS,
)
from aho.telegram.openclaw_client import send_chat, get_status


class TestCommandRouting:
    """Test that commands route to the correct handler."""

    def test_start_command_exists(self):
        assert "/start" in COMMANDS

    def test_help_command_exists(self):
        assert "/help" in COMMANDS

    def test_status_command_exists(self):
        assert "/status" in COMMANDS

    def test_iteration_command_exists(self):
        assert "/iteration" in COMMANDS

    def test_last_command_exists(self):
        assert "/last" in COMMANDS

    def test_start_returns_greeting(self):
        result = COMMANDS["/start"]()
        assert "aho harness bot" in result
        assert "/status" in result

    def test_help_returns_help_text(self):
        result = COMMANDS["/help"]()
        assert "openclaw" in result.lower()

    def test_command_count(self):
        assert len(COMMANDS) == 5


class TestOpenClawResponseFormatting:
    """Test response formatting for Telegram display."""

    def test_ok_response(self):
        result = _format_openclaw_response({"ok": True, "response": "hello world"})
        assert result == "hello world"

    def test_empty_response(self):
        result = _format_openclaw_response({"ok": True, "response": ""})
        assert "empty" in result.lower()

    def test_error_response(self):
        result = _format_openclaw_response({"ok": False, "error": "connection refused"})
        assert "connection refused" in result

    def test_timeout_response(self):
        result = _format_openclaw_response({"ok": False, "error": "timeout", "timed_out": True})
        assert "dispatched" in result.lower()

    def test_truncation_at_4000(self):
        """Response formatter truncates at 4000 chars but formatting is done in _send_reply."""
        long_response = "x" * 5000
        result = _format_openclaw_response({"ok": True, "response": long_response})
        # The raw response is returned; truncation happens in _send_reply
        assert len(result) == 5000


class TestOpenClawClient:
    """Test openclaw socket client."""

    def test_missing_socket(self, tmp_path):
        with patch("aho.telegram.openclaw_client.OPENCLAW_SOCK", tmp_path / "nonexistent.sock"):
            result = send_chat("hello")
            assert not result["ok"]
            assert "not found" in result["error"]

    def test_status_missing_socket(self, tmp_path):
        with patch("aho.telegram.openclaw_client.OPENCLAW_SOCK", tmp_path / "nonexistent.sock"):
            result = get_status()
            assert not result["ok"]


class TestOffsetPersistence:
    """Test update_id offset load/save."""

    def test_save_and_load(self, tmp_path):
        offset_path = tmp_path / "telegram_offset"
        with patch("aho.telegram.inbound.OFFSET_PATH", offset_path):
            _save_offset(12345)
            assert _load_offset() == 12345

    def test_load_missing_file(self, tmp_path):
        with patch("aho.telegram.inbound.OFFSET_PATH", tmp_path / "missing"):
            assert _load_offset() == 0

    def test_load_corrupt_file(self, tmp_path):
        offset_path = tmp_path / "telegram_offset"
        offset_path.write_text("not_a_number")
        with patch("aho.telegram.inbound.OFFSET_PATH", offset_path):
            assert _load_offset() == 0


class TestIterationInfo:
    """Test /iteration command handler."""

    def test_returns_iteration_data(self):
        result = _handle_iteration_info()
        # Should contain iteration info from .aho.json
        assert "0.2.8" in result or "Iteration" in result

    def test_contains_status(self):
        result = _handle_iteration_info()
        assert "Status" in result or "status" in result.lower()


class TestRouteMessage:
    """Test message routing with mocked Telegram API."""

    @patch("aho.telegram.inbound._send_reply")
    def test_routes_start_command(self, mock_reply):
        _route_message("fake_token", 123, "/start")
        mock_reply.assert_called_once()
        args = mock_reply.call_args[0]
        assert "aho harness bot" in args[2]

    @patch("aho.telegram.inbound._send_reply")
    def test_routes_help_command(self, mock_reply):
        _route_message("fake_token", 123, "/help")
        mock_reply.assert_called_once()

    @patch("aho.telegram.inbound._send_reply")
    @patch("aho.telegram.inbound.send_chat")
    def test_routes_freetext_to_openclaw(self, mock_chat, mock_reply):
        mock_chat.return_value = {"ok": True, "response": "openclaw says hi", "timed_out": False}
        _route_message("fake_token", 123, "what is the meaning of life?")
        mock_chat.assert_called_once()
        mock_reply.assert_called_once()
        assert "openclaw says hi" in mock_reply.call_args[0][2]

    @patch("aho.telegram.inbound._send_reply")
    @patch("aho.telegram.inbound.send_chat")
    def test_timeout_sends_async_ack(self, mock_chat, mock_reply):
        mock_chat.return_value = {"ok": False, "error": "timeout", "timed_out": True}
        _route_message("fake_token", 123, "slow question")
        # Should get at least the ack reply
        assert mock_reply.call_count >= 1
        first_reply = mock_reply.call_args_list[0][0][2]
        assert "dispatched" in first_reply.lower() or "processing" in first_reply.lower()
