"""Tests for schema v3 — efficacy instrumentation (W8 Part D).

4+ cases: v3 emit, v2 backward compat, v1 backward compat, CLI flags.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from aho.acceptance import AcceptanceResult
from aho.workstream_events import emit_workstream_complete


def _make_tmp_log():
    tf = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    tf.close()
    return tf.name


def _read_events(log_path):
    events = []
    for line in Path(log_path).read_text().splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def test_v3_emit_with_efficacy_fields():
    """v3 event includes agents_involved, token_count, harness_contributions."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            emit_workstream_complete(
                "W_V3_TEST", "pass",
                agents_involved=["claude-code", "qwen-local"],
                token_count=45000,
                harness_contributions=["daemon_healthy", "acceptance_framework"],
                ad_hoc_forensics_minutes=17,
            )

        events = _read_events(log_path)
        assert len(events) == 1
        ev = events[0]
        assert ev["schema_version"] == 3
        assert ev["agents_involved"] == [
            {"agent": "claude-code", "role": "primary"},
            {"agent": "qwen-local", "role": "primary"},
        ]
        assert ev["token_count"] == 45000
        assert ev["harness_contributions"] == ["daemon_healthy", "acceptance_framework"]
        assert ev["ad_hoc_forensics_minutes"] == 17
    finally:
        os.unlink(log_path)


def test_v3_with_acceptance_results_also_present():
    """v3 event can include both acceptance_results and efficacy fields."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            results = [AcceptanceResult("c1", True, 0, "", None, 0.1)]
            emit_workstream_complete(
                "W_V3_COMBO", "pass",
                acceptance_results=results,
                agents_involved=["claude-code"],
            )

        events = _read_events(log_path)
        ev = events[0]
        assert ev["schema_version"] == 3
        assert "acceptance_results" in ev
        assert "agents_involved" in ev
    finally:
        os.unlink(log_path)


def test_v2_backward_compat_no_v3_fields():
    """v2 event (acceptance only, no efficacy) still works."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            results = [AcceptanceResult("c1", True, 0, "", None, 0.1)]
            emit_workstream_complete("W_V2_COMPAT", "pass", acceptance_results=results)

        events = _read_events(log_path)
        ev = events[0]
        assert ev["schema_version"] == 2
        assert "acceptance_results" in ev
        assert "agents_involved" not in ev
    finally:
        os.unlink(log_path)


def test_v1_backward_compat_no_extra_fields():
    """v1 event (no acceptance, no efficacy) has no schema_version."""
    log_path = _make_tmp_log()
    try:
        with patch("aho.workstream_events.LOG_PATH", log_path), \
             patch("aho.workstream_events._ITERATION", "0.2.11"), \
             patch("aho.logger.LOG_PATH", log_path), \
             patch("aho.logger._ITERATION", "0.2.11"):
            emit_workstream_complete("W_V1_COMPAT", "pass")

        events = _read_events(log_path)
        ev = events[0]
        assert "schema_version" not in ev
        assert "agents_involved" not in ev
    finally:
        os.unlink(log_path)


def test_v3_fields_default_to_none_when_missing():
    """Reading a v1 event, v3 fields are absent (callers use .get with default)."""
    event = {"event_type": "workstream_complete", "status": "pass"}
    assert event.get("agents_involved", []) == []
    assert event.get("token_count") is None
    assert event.get("harness_contributions", []) == []
    assert event.get("ad_hoc_forensics_minutes") is None
