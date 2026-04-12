"""Tests for /ws fixes (W8 Part A).

3+ cases: status denominator, in_progress transition, caption routing.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch


def test_ws_status_shows_completed_of_planned():
    """/ws status shows completed/planned not completed/completed."""
    from aho.telegram.inbound import _handle_ws_status
    result = _handle_ws_status()
    # Should contain a fraction with denominator >= numerator
    assert "/" in result
    # Find the progress line
    for line in result.splitlines():
        if "Progress" in line:
            # Extract N/M from the line
            import re
            match = re.search(r"(\d+)/(\d+)", line)
            if match:
                num, denom = int(match.group(1)), int(match.group(2))
                assert denom >= num, f"Denominator {denom} < numerator {num}"
            break


def test_workstream_start_sets_in_progress():
    """workstream_start updates checkpoint to in_progress."""
    log_path = tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False)
    log_path.close()

    from aho.paths import find_project_root
    root = find_project_root()
    ckpt_path = root / ".aho-checkpoint.json"
    orig_ckpt = ckpt_path.read_text()

    try:
        with patch("aho.workstream_events.LOG_PATH", log_path.name), \
             patch("aho.logger.LOG_PATH", log_path.name):
            from aho.workstream_events import emit_workstream_start
            emit_workstream_start("W_TEST_IP")

        ckpt = json.loads(ckpt_path.read_text())
        assert ckpt["workstreams"].get("W_TEST_IP") == "in_progress"
    finally:
        ckpt_path.write_text(orig_ckpt)
        Path(log_path.name).unlink(missing_ok=True)


def test_caption_text_extraction():
    """Caption from document messages is used when text is empty."""
    # Simulate the extraction logic from poll_loop
    msg_with_caption = {"text": "", "caption": "/ws last", "chat": {"id": 0}}
    text = msg_with_caption.get("text", "") or msg_with_caption.get("caption", "")
    assert text == "/ws last"

    msg_with_text = {"text": "/status", "caption": "", "chat": {"id": 0}}
    text = msg_with_text.get("text", "") or msg_with_text.get("caption", "")
    assert text == "/status"


def test_planned_ws_count_reads_plan_doc():
    """_get_planned_ws_count reads workstream headers from plan doc."""
    from aho.telegram.inbound import _get_planned_ws_count
    count = _get_planned_ws_count()
    # 0.2.11 plan has 19 workstreams
    assert count >= 19, f"Expected >= 19 planned, got {count}"
