"""Tests for orchestrator workstream_id parameterization (0.2.16 W0, F006).

0.2.15 W4 observed run_cascade emitting pipeline_handoff events with
workstream_id hardcoded to "W1" at the dispatch and complete call sites.
Every later workstream that runs a cascade attributes events to W1 wrongly.
Fix: workstream_id is a parameter with a "W0" default; both log_event call
sites inside the stage loop receive the value.
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from aho.pipeline.schemas import RoleAssignment
from aho.pipeline.orchestrator import run_cascade


def _role_assignment(model: str = "qwen3.5:9b") -> RoleAssignment:
    return RoleAssignment(
        indexer_in=model, producer=model, auditor=model,
        indexer_out=model, assessor=model,
    )


def _dispatch_result(response: str = "stage output") -> dict:
    return {
        "response": response,
        "total_duration_ms": 100,
        "model": "qwen3.5:9b",
        "error": None,
        "wall_clock_seconds": 0.1,
        "family": "qwen",
        "retries_used": 0,
    }


def test_default_workstream_id_is_w0(tmp_path):
    """Default parameter is 'W0' — no more hardcoded 'W1'."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: _dispatch_result()), \
         patch("aho.pipeline.orchestrator.log_event") as mock_log:
        run_cascade(
            document_path=str(doc),
            role_assignment=_role_assignment(),
            output_dir=str(tmp_path / "out"),
        )

    # 10 calls = 5 stages × (dispatch + complete). All must carry W0.
    assert mock_log.call_count == 10
    for call_obj in mock_log.call_args_list:
        assert call_obj.kwargs["workstream_id"] == "W0", (
            f"Expected W0, got {call_obj.kwargs.get('workstream_id')}"
        )


def test_explicit_workstream_id_propagates(tmp_path):
    """Passing workstream_id='W4' → all 10 events carry W4."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: _dispatch_result()), \
         patch("aho.pipeline.orchestrator.log_event") as mock_log:
        run_cascade(
            document_path=str(doc),
            role_assignment=_role_assignment(),
            output_dir=str(tmp_path / "out"),
            workstream_id="W4",
        )

    assert mock_log.call_count == 10
    for call_obj in mock_log.call_args_list:
        assert call_obj.kwargs["workstream_id"] == "W4"


def test_dispatch_and_complete_events_agree(tmp_path):
    """Both dispatch and complete events for the same stage carry the same id."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: _dispatch_result()), \
         patch("aho.pipeline.orchestrator.log_event") as mock_log:
        run_cascade(
            document_path=str(doc),
            role_assignment=_role_assignment(),
            output_dir=str(tmp_path / "out"),
            workstream_id="W2",
        )

    # Alternating dispatch/complete per stage; verify pairs agree.
    for i in range(0, 10, 2):
        dispatch_call = mock_log.call_args_list[i]
        complete_call = mock_log.call_args_list[i + 1]
        assert dispatch_call.kwargs["action"] == "dispatch"
        assert complete_call.kwargs["action"] == "complete"
        assert dispatch_call.kwargs["workstream_id"] == "W2"
        assert complete_call.kwargs["workstream_id"] == "W2"
