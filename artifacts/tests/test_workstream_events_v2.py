"""Tests for workstream_events v2 schema — acceptance_results in events.

Minimum 6 cases per W2 plan:
1. v2 emit with acceptance_results serializes correctly
2. v1 emit (no acceptance_results) still works, schema_version omitted
3. v2 event readable, acceptance_results parse back
4. v1 event readable, acceptance_results defaults to empty
5. --acceptance-file loads JSON and emits correctly
6. --acceptance-file with invalid JSON exits 1
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from aho.acceptance import AcceptanceResult
from aho.workstream_events import (
    emit_workstream_complete,
    load_acceptance_file,
)


def _make_tmp_log():
    """Create a temp log file and patch LOG_PATH."""
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    tf.close()
    return tf.name


def _read_events(log_path):
    """Read all events from a JSONL log."""
    events = []
    for line in Path(log_path).read_text().splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def test_v2_emit_with_acceptance_results():
    """v2 emit serializes acceptance_results and sets schema_version=2."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            results = [
                AcceptanceResult(
                    check_name="test_check",
                    passed=True,
                    actual_exit=0,
                    actual_output="ok",
                    matched=None,
                    duration_seconds=0.1,
                ),
            ]
            emit_workstream_complete("W_V2_TEST", "pass", acceptance_results=results)

        events = _read_events(log_path)
        assert len(events) == 1
        ev = events[0]
        assert ev["schema_version"] == 2
        assert len(ev["acceptance_results"]) == 1
        assert ev["acceptance_results"][0]["check_name"] == "test_check"
        assert ev["acceptance_results"][0]["passed"] is True
    finally:
        os.unlink(log_path)


def test_v1_emit_no_acceptance_results():
    """v1 emit (no acceptance_results) has no schema_version field."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            emit_workstream_complete("W_V1_TEST", "pass")

        events = _read_events(log_path)
        assert len(events) == 1
        ev = events[0]
        assert "schema_version" not in ev
        assert "acceptance_results" not in ev
    finally:
        os.unlink(log_path)


def test_v2_event_acceptance_results_parseable():
    """v2 event acceptance_results parse back into expected structure."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            results = [
                AcceptanceResult("c1", True, 0, "out1", None, 0.05),
                AcceptanceResult("c2", False, 1, "out2", False, 0.1, error="mismatch"),
            ]
            emit_workstream_complete("W_PARSE_TEST", "pass", acceptance_results=results)

        events = _read_events(log_path)
        ar = events[0]["acceptance_results"]
        assert len(ar) == 2
        assert ar[0]["check_name"] == "c1"
        assert ar[0]["passed"] is True
        assert ar[1]["check_name"] == "c2"
        assert ar[1]["passed"] is False
        assert ar[1]["error"] == "mismatch"
    finally:
        os.unlink(log_path)


def test_v1_event_missing_acceptance_defaults_empty():
    """v1 event (no acceptance_results key) defaults to empty list on read."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            emit_workstream_complete("W_V1_DEFAULT", "pass")

        events = _read_events(log_path)
        ev = events[0]
        ar = ev.get("acceptance_results", [])
        assert ar == []
    finally:
        os.unlink(log_path)


def test_acceptance_file_loads_json():
    """load_acceptance_file parses valid JSON array."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        json.dump([
            {"check_name": "t1", "passed": True, "actual_exit": 0,
             "actual_output": "", "matched": None, "duration_seconds": 0.1},
        ], tf)
        tf.flush()
        path = tf.name

    try:
        results = load_acceptance_file(path)
        assert len(results) == 1
        assert results[0]["check_name"] == "t1"
    finally:
        os.unlink(path)


def test_acceptance_file_invalid_json_raises():
    """load_acceptance_file raises on invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        tf.write("not json {{{")
        tf.flush()
        path = tf.name

    try:
        raised = False
        try:
            load_acceptance_file(path)
        except (json.JSONDecodeError, ValueError):
            raised = True
        assert raised
    finally:
        os.unlink(path)


def test_cli_acceptance_file_invalid_json_exits_1():
    """CLI --acceptance-file with invalid JSON exits 1, no emit."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        tf.write("NOT VALID JSON")
        tf.flush()
        path = tf.name

    try:
        result = subprocess.run(
            ["python", "-m", "aho.cli", "iteration", "workstream", "complete",
             "W_BADJSON", "--status", "pass", "--acceptance-file", path],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "ERROR" in result.stdout or "ERROR" in result.stderr
    finally:
        os.unlink(path)


def test_report_builder_acceptance_column():
    """Report builder renders Acceptance column in workstream detail."""
    from aho.feedback.report_builder import _section_workstream_detail, _acceptance_summary_for_ws

    events = [
        {
            "workstream_id": "W1",
            "event_type": "workstream_complete",
            "schema_version": 2,
            "acceptance_results": [
                {"check_name": "c1", "passed": True},
                {"check_name": "c2", "passed": True},
                {"check_name": "c3", "passed": True},
            ],
        },
        {
            "workstream_id": "W0",
            "event_type": "workstream_complete",
        },
    ]

    assert _acceptance_summary_for_ws(events, "W1") == "3/3 checks"
    assert _acceptance_summary_for_ws(events, "W0") == "prose (bootstrap)"

    checkpoint = {"workstreams": {"W0": "pass", "W1": "pass"}, "executor": "claude-code"}
    detail = _section_workstream_detail(checkpoint, events)
    assert "Acceptance" in detail
    assert "3/3 checks" in detail
    assert "prose (bootstrap)" in detail
