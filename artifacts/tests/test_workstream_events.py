"""Tests for workstream_events.py (0.2.9 W3)."""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def event_log(tmp_path):
    """Set up a temporary event log and patch LOG_PATH + _ITERATION."""
    log_file = tmp_path / "aho_event_log.jsonl"
    log_file.touch()
    with patch("aho.workstream_events.LOG_PATH", str(log_file)), \
         patch("aho.workstream_events._ITERATION", "0.2.9"), \
         patch("aho.logger.LOG_PATH", str(log_file)), \
         patch("aho.logger._ITERATION", "0.2.9"):
        yield log_file


def _read_events(log_file):
    events = []
    for line in log_file.read_text().splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def test_emit_start(event_log):
    from aho.workstream_events import emit_workstream_start
    result = emit_workstream_start("W0", summary="bump workstream")
    assert result is not None
    assert result["event_type"] == "workstream_start"
    assert result["workstream_id"] == "W0"

    events = _read_events(event_log)
    assert len(events) == 1
    assert events[0]["event_type"] == "workstream_start"
    assert events[0]["workstream_id"] == "W0"


def test_emit_complete(event_log):
    from aho.workstream_events import emit_workstream_complete
    result = emit_workstream_complete("W0", status="pass", summary="done")
    assert result is not None
    assert result["event_type"] == "workstream_complete"
    assert result["status"] == "pass"


def test_start_idempotent(event_log):
    from aho.workstream_events import emit_workstream_start
    r1 = emit_workstream_start("W1", summary="first")
    r2 = emit_workstream_start("W1", summary="duplicate")
    assert r1 is not None
    assert r2 is None  # idempotent skip

    events = _read_events(event_log)
    start_events = [e for e in events if e["event_type"] == "workstream_start" and e["workstream_id"] == "W1"]
    assert len(start_events) == 1


def test_complete_idempotent(event_log):
    from aho.workstream_events import emit_workstream_complete
    r1 = emit_workstream_complete("W2", status="pass", summary="first")
    r2 = emit_workstream_complete("W2", status="pass", summary="duplicate")
    assert r1 is not None
    assert r2 is None

    events = _read_events(event_log)
    complete_events = [e for e in events if e["event_type"] == "workstream_complete" and e["workstream_id"] == "W2"]
    assert len(complete_events) == 1


def test_different_workstreams_independent(event_log):
    from aho.workstream_events import emit_workstream_start, emit_workstream_complete
    emit_workstream_start("W0")
    emit_workstream_start("W1")
    emit_workstream_complete("W0", status="pass")
    emit_workstream_complete("W1", status="pass")

    events = _read_events(event_log)
    assert len(events) == 4


def test_event_shape(event_log):
    from aho.workstream_events import emit_workstream_start
    result = emit_workstream_start("W3", summary="test shape")
    required_keys = {"timestamp", "iteration", "workstream_id", "event_type", "source_agent", "target", "action", "status"}
    assert required_keys.issubset(set(result.keys()))
    assert result["iteration"] == "0.2.9"
    assert result["target"] == "W3"


def test_jsonl_append_only(event_log):
    from aho.workstream_events import emit_workstream_start, emit_workstream_complete
    emit_workstream_start("W4")
    size_after_start = event_log.stat().st_size
    emit_workstream_complete("W4", status="pass")
    size_after_complete = event_log.stat().st_size
    assert size_after_complete > size_after_start


def test_source_agent_default(event_log):
    from aho.workstream_events import emit_workstream_start
    with patch.dict(os.environ, {"AHO_EXECUTOR": "gemini-cli"}):
        result = emit_workstream_start("W5")
    assert result["source_agent"] == "gemini-cli"


def test_source_agent_override(event_log):
    from aho.workstream_events import emit_workstream_start
    result = emit_workstream_start("W6", source_agent="custom-agent")
    assert result["source_agent"] == "custom-agent"
