"""Tests for workstream_gate.py (0.2.9 W5)."""
import json
import threading
import time
from unittest.mock import patch
import pytest

from aho.workstream_gate import wait_if_paused, _read_proceed_awaited


class TestReadProceedAwaited:
    """Test reading proceed_awaited from checkpoint."""

    def test_false_when_not_set(self, tmp_path):
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"status": "active"}))
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path):
            assert _read_proceed_awaited() is False

    def test_true_when_set(self, tmp_path):
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"proceed_awaited": True}))
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path):
            assert _read_proceed_awaited() is True

    def test_false_when_no_checkpoint(self, tmp_path):
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path):
            assert _read_proceed_awaited() is False

    def test_false_when_explicitly_false(self, tmp_path):
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"proceed_awaited": False}))
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path):
            assert _read_proceed_awaited() is False


class TestWaitIfPaused:
    """Test the blocking wait behavior."""

    def test_proceeds_immediately_when_not_paused(self, tmp_path):
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"proceed_awaited": False}))
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path):
            result = wait_if_paused(timeout_seconds=1.0)
        assert result is True

    def test_proceeds_immediately_when_no_checkpoint(self, tmp_path):
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path):
            result = wait_if_paused(timeout_seconds=1.0)
        assert result is True

    def test_timeout_returns_false(self, tmp_path):
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"proceed_awaited": True}))
        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path), \
             patch("aho.workstream_gate.time.sleep"):
            result = wait_if_paused(timeout_seconds=0.01, poll_interval=0.01)
        assert result is False

    def test_resumes_when_proceed_cleared(self, tmp_path):
        """Simulates /ws proceed clearing the flag mid-wait."""
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"proceed_awaited": True}))

        call_count = 0
        def mock_sleep(seconds):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                # Simulate /ws proceed clearing the flag
                ckpt.write_text(json.dumps({"proceed_awaited": False}))

        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path), \
             patch("aho.workstream_gate.time.sleep", side_effect=mock_sleep):
            result = wait_if_paused(timeout_seconds=None)
        assert result is True
        assert call_count >= 2

    def test_poll_interval_honored(self, tmp_path):
        """Verify sleep is called with the configured interval."""
        ckpt = tmp_path / ".aho-checkpoint.json"
        ckpt.write_text(json.dumps({"proceed_awaited": True}))

        sleep_calls = []
        def mock_sleep(seconds):
            sleep_calls.append(seconds)
            # Clear after first poll so we don't loop forever
            ckpt.write_text(json.dumps({"proceed_awaited": False}))

        with patch("aho.workstream_gate.find_project_root", return_value=tmp_path), \
             patch("aho.workstream_gate.time.sleep", side_effect=mock_sleep):
            wait_if_paused(timeout_seconds=None, poll_interval=3.0)
        assert sleep_calls[0] == 3.0
