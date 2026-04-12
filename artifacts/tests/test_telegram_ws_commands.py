"""Tests for /ws command family in Telegram inbound (0.2.9 W4)."""
import json
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from aho.telegram.inbound import (
    _route_message,
    _handle_ws_status,
    _handle_ws_pause,
    _handle_ws_proceed,
    _handle_ws_last,
    WS_COMMANDS,
)


class TestWsCommandDispatch:
    """Test that /ws subcommands route correctly."""

    def test_ws_status_in_dispatch(self):
        assert "status" in WS_COMMANDS

    def test_ws_pause_in_dispatch(self):
        assert "pause" in WS_COMMANDS

    def test_ws_proceed_in_dispatch(self):
        assert "proceed" in WS_COMMANDS

    def test_ws_last_in_dispatch(self):
        assert "last" in WS_COMMANDS

    def test_ws_count(self):
        assert len(WS_COMMANDS) == 4

    @patch("aho.telegram.inbound._send_reply")
    def test_ws_routes_status(self, mock_reply):
        with patch("aho.telegram.inbound._handle_ws_status", return_value="mocked status"):
            _route_message("tok", 123, "/ws status")
        mock_reply.assert_called_once()

    @patch("aho.telegram.inbound._send_reply")
    def test_ws_routes_pause(self, mock_reply):
        with patch("aho.telegram.inbound._handle_ws_pause", return_value="paused"):
            _route_message("tok", 123, "/ws pause")
        mock_reply.assert_called_once()

    @patch("aho.telegram.inbound._send_reply")
    def test_ws_routes_proceed(self, mock_reply):
        with patch("aho.telegram.inbound._handle_ws_proceed", return_value="proceeding"):
            _route_message("tok", 123, "/ws proceed")
        mock_reply.assert_called_once()

    @patch("aho.telegram.inbound._send_reply")
    def test_ws_unknown_shows_usage(self, mock_reply):
        _route_message("tok", 123, "/ws banana")
        mock_reply.assert_called_once()
        assert "Usage" in mock_reply.call_args[0][2]

    @patch("aho.telegram.inbound._send_reply")
    def test_ws_no_subcmd_shows_usage(self, mock_reply):
        _route_message("tok", 123, "/ws")
        mock_reply.assert_called_once()
        assert "Usage" in mock_reply.call_args[0][2]


class TestWsStatus:
    """Test /ws status handler."""

    def test_reads_checkpoint(self, tmp_path):
        aho_json = tmp_path / ".aho.json"
        aho_json.write_text(json.dumps({"current_iteration": "0.2.9"}))
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({
            "status": "active",
            "current_workstream": "W3",
            "workstreams": {"W0": "pass", "W1": "pass", "W2": "pass"},
            "executor": "claude-code",
            "proceed_awaited": False,
        }))
        with patch("aho.telegram.inbound.find_project_root", return_value=tmp_path):
            result = _handle_ws_status()
        assert "0.2.9" in result
        assert "W3" in result
        assert "3" in result  # 3 pass
        assert "no" in result.lower()  # not paused

    def test_shows_paused_state(self, tmp_path):
        aho_json = tmp_path / ".aho.json"
        aho_json.write_text(json.dumps({"current_iteration": "0.2.9"}))
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({
            "status": "active",
            "current_workstream": "W4",
            "workstreams": {},
            "executor": "claude-code",
            "proceed_awaited": True,
        }))
        with patch("aho.telegram.inbound.find_project_root", return_value=tmp_path):
            result = _handle_ws_status()
        assert "yes" in result.lower()  # paused


class TestWsPause:
    """Test /ws pause handler."""

    def test_sets_proceed_awaited(self, tmp_path):
        ckpt_path = tmp_path / ".aho-checkpoint.json"
        ckpt_path.write_text(json.dumps({"current_workstream": "W3", "proceed_awaited": False}))
        with patch("aho.telegram.inbound.find_project_root", return_value=tmp_path):
            result = _handle_ws_pause()
        assert "Paused" in result
        data = json.loads(ckpt_path.read_text())
        assert data["proceed_awaited"] is True

    def test_no_checkpoint(self, tmp_path):
        with patch("aho.telegram.inbound.find_project_root", return_value=tmp_path):
            result = _handle_ws_pause()
        assert "no checkpoint" in result.lower()


class TestWsProceed:
    """Test /ws proceed handler."""

    def test_clears_proceed_awaited(self, tmp_path):
        ckpt_path = tmp_path / ".aho-checkpoint.json"
        ckpt_path.write_text(json.dumps({"current_workstream": "W3", "proceed_awaited": True}))
        with patch("aho.telegram.inbound.find_project_root", return_value=tmp_path):
            result = _handle_ws_proceed()
        assert "Proceeding" in result
        data = json.loads(ckpt_path.read_text())
        assert data["proceed_awaited"] is False


class TestWsLast:
    """Test /ws last handler."""

    def test_reads_last_complete_event(self, tmp_path):
        log = tmp_path / "aho_event_log.jsonl"
        events = [
            {"event_type": "workstream_start", "workstream_id": "W0", "iteration": "0.2.9"},
            {"event_type": "workstream_complete", "workstream_id": "W0", "iteration": "0.2.9", "status": "success", "output_summary": "bumps done", "timestamp": "2026-04-12T05:00:00Z"},
            {"event_type": "workstream_complete", "workstream_id": "W1", "iteration": "0.2.9", "status": "success", "output_summary": "template done", "timestamp": "2026-04-12T05:10:00Z"},
        ]
        log.write_text("\n".join(json.dumps(e) for e in events))
        with patch("aho.paths.get_data_dir", return_value=tmp_path):
            result = _handle_ws_last()
        assert "W1" in result  # last complete is W1
        assert "template done" in result

    def test_no_events(self, tmp_path):
        log = tmp_path / "aho_event_log.jsonl"
        log.write_text("")
        with patch("aho.paths.get_data_dir", return_value=tmp_path):
            result = _handle_ws_last()
        assert "no workstream" in result.lower()

    def test_no_log_file(self, tmp_path):
        with patch("aho.paths.get_data_dir", return_value=tmp_path):
            result = _handle_ws_last()
        assert "no event log" in result.lower()


class TestAutoPush:
    """Test auto-push subscriber fires on workstream_complete events."""

    def test_auto_push_detects_new_complete(self, tmp_path):
        """Auto-push loop should detect a new workstream_complete event."""
        from aho.telegram.inbound import _auto_push_loop

        log = tmp_path / "aho_event_log.jsonl"
        log.write_text("")  # start empty so pos=0

        replies = []

        def mock_send_reply(token, chat_id, text):
            replies.append(text)

        call_count = 0
        def mock_sleep(seconds):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # After pos is set to 0, write the event so it appears as "new"
                event = {"event_type": "workstream_complete", "workstream_id": "W0", "iteration": "0.2.9", "status": "success", "output_summary": "done"}
                log.write_text(json.dumps(event) + "\n")
                return
            raise StopIteration

        stop = threading.Event()

        with patch("aho.paths.get_data_dir", return_value=tmp_path), \
             patch("aho.telegram.inbound._send_reply", side_effect=mock_send_reply), \
             patch("aho.telegram.inbound.time.sleep", side_effect=mock_sleep):
            try:
                _auto_push_loop("tok", 123, stop)
            except StopIteration:
                pass

        assert len(replies) == 1
        assert "W0" in replies[0]

    def test_auto_push_ignores_non_complete(self, tmp_path):
        """Auto-push should not fire for workstream_start events."""
        from aho.telegram.inbound import _auto_push_loop
        import threading

        log = tmp_path / "aho_event_log.jsonl"
        log.write_text("")

        replies = []

        def mock_send_reply(token, chat_id, text):
            replies.append(text)

        stop = threading.Event()

        with patch("aho.paths.get_data_dir", return_value=tmp_path), \
             patch("aho.telegram.inbound._send_reply", side_effect=mock_send_reply), \
             patch("aho.telegram.inbound.time.sleep", side_effect=[None, StopIteration]):
            event = {"event_type": "workstream_start", "workstream_id": "W0", "iteration": "0.2.9"}
            log.write_text(json.dumps(event) + "\n")

            try:
                _auto_push_loop("tok", 123, stop)
            except StopIteration:
                pass

        assert len(replies) == 0
