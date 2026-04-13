"""Test that emit_workstream_complete only modifies the named workstream's checkpoint state.

0.2.14 W0 fix for 0.2.13 side-effect bug: emitting workstream_complete for one
workstream was corrupting sibling workstream states (reverting workstream_complete
to in_progress, flipping skipped_per_rescope to in_progress).
"""
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def isolated_env(tmp_path):
    """Set up isolated event log, checkpoint, and project root."""
    log_file = tmp_path / "aho_event_log.jsonl"
    log_file.touch()

    ckpt_path = tmp_path / ".aho-checkpoint.json"
    ckpt_path.write_text(json.dumps({
        "iteration": "0.2.14",
        "phase": 0,
        "run_type": "pattern-c-modified",
        "current_workstream": "W2",
        "workstreams": {
            "W0": "workstream_complete",
            "W1": "workstream_complete",
            "W2": "in_progress",
            "W3": "skipped_per_rescope",
            "W4": "skipped_per_rescope",
        },
        "last_event": "W2_workstream_start",
        "status": "active",
    }, indent=2) + "\n")

    with patch("aho.workstream_events.LOG_PATH", str(log_file)), \
         patch("aho.workstream_events._ITERATION", "0.2.14"), \
         patch("aho.logger.LOG_PATH", str(log_file)), \
         patch("aho.logger._ITERATION", "0.2.14"), \
         patch("aho.paths.find_project_root", return_value=tmp_path):
        yield tmp_path, log_file, ckpt_path


def test_complete_preserves_sibling_states(isolated_env):
    """emit_workstream_complete for W2 must not alter W0, W1, W3, W4 states."""
    tmp_path, log_file, ckpt_path = isolated_env

    from aho.workstream_events import emit_workstream_complete
    result = emit_workstream_complete("W2", status="pass", summary="done")
    assert result is not None

    ckpt = json.loads(ckpt_path.read_text())
    ws = ckpt["workstreams"]

    # Named workstream updated
    assert ws["W2"] == "workstream_complete"

    # Siblings preserved exactly
    assert ws["W0"] == "workstream_complete", "W0 should remain workstream_complete"
    assert ws["W1"] == "workstream_complete", "W1 should remain workstream_complete"
    assert ws["W3"] == "skipped_per_rescope", "W3 should remain skipped_per_rescope"
    assert ws["W4"] == "skipped_per_rescope", "W4 should remain skipped_per_rescope"

    # last_event updated
    assert ckpt["last_event"] == "W2_workstream_complete"


def test_start_preserves_sibling_states(isolated_env):
    """emit_workstream_start for a new workstream must not alter existing states."""
    tmp_path, log_file, ckpt_path = isolated_env

    from aho.workstream_events import emit_workstream_start
    result = emit_workstream_start("W5", summary="new workstream")
    assert result is not None

    ckpt = json.loads(ckpt_path.read_text())
    ws = ckpt["workstreams"]

    # New workstream added
    assert ws["W5"] == "in_progress"

    # All existing siblings preserved
    assert ws["W0"] == "workstream_complete"
    assert ws["W1"] == "workstream_complete"
    assert ws["W2"] == "in_progress"
    assert ws["W3"] == "skipped_per_rescope"
    assert ws["W4"] == "skipped_per_rescope"
