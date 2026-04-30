"""Tests for cascade orchestrator empty-content halt semantics (0.2.16 W0).

When a stage returns `response == ""` with `error is None`, the cascade must
raise `EmptyContentError` rather than silently propagating an empty string to
the next stage as `[stage X failed: None]`. 0.2.15 W4 produced the measurement
that motivated this: Qwen Producer thinking-mode exhausted num_predict=2000
and emitted 0-char content with no dispatcher error.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from aho.pipeline.schemas import RoleAssignment
from aho.pipeline.orchestrator import run_cascade
from aho.pipeline.dispatcher import EmptyContentError


def _role_assignment(model: str = "qwen3.5:9b") -> RoleAssignment:
    return RoleAssignment(
        indexer_in=model, producer=model, auditor=model,
        indexer_out=model, assessor=model,
    )


def _dispatch_result(response: str, error: str | None = None) -> dict:
    return {
        "response": response,
        "total_duration_ms": 100,
        "model": "qwen3.5:9b",
        "error": error,
        "wall_clock_seconds": 0.1,
        "family": "qwen",
        "retries_used": 0,
    }


def test_empty_content_no_error_raises_halt(tmp_path):
    """Stage emits 0-char content with error=None → EmptyContentError."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")

    # indexer_in returns fine; producer returns empty, no error.
    call_sequence = [
        _dispatch_result("indexer output"),
        _dispatch_result(""),  # producer: empty content, no error → halt
    ]
    call_iter = iter(call_sequence)

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: next(call_iter)), \
         patch("aho.pipeline.orchestrator.log_event"):
        with pytest.raises(EmptyContentError) as exc_info:
            run_cascade(
                document_path=str(doc),
                role_assignment=_role_assignment(),
                output_dir=str(tmp_path / "out"),
            )

    assert "producer" in str(exc_info.value)
    assert "0-char content" in str(exc_info.value)


def test_empty_content_with_error_does_not_raise(tmp_path):
    """response='' with error set uses existing error-propagation path."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")

    call_sequence = [
        _dispatch_result("", error="timeout after 3600s"),
    ] + [_dispatch_result("recovered output")] * 4
    call_iter = iter(call_sequence)

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: next(call_iter)), \
         patch("aho.pipeline.orchestrator.log_event"):
        trace = run_cascade(
            document_path=str(doc),
            role_assignment=_role_assignment(),
            output_dir=str(tmp_path / "out"),
        )
    # Cascade completed — existing error path preserved.
    assert len(trace.handoffs) == 5
    assert trace.handoffs[0].error == "timeout after 3600s"


def test_non_empty_content_does_not_raise(tmp_path):
    """Normal completion (all stages return content) does not raise."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: _dispatch_result("stage output")), \
         patch("aho.pipeline.orchestrator.log_event"):
        trace = run_cascade(
            document_path=str(doc),
            role_assignment=_role_assignment(),
            output_dir=str(tmp_path / "out"),
        )
    assert len(trace.handoffs) == 5


def test_stage_artifact_written_before_halt(tmp_path):
    """Forensic trail: stage artifact is written before the halt exception."""
    doc = tmp_path / "doc.txt"
    doc.write_text("dummy")
    out_dir = tmp_path / "out"

    call_sequence = [
        _dispatch_result("indexer output"),
        _dispatch_result(""),
    ]
    call_iter = iter(call_sequence)

    with patch("aho.pipeline.orchestrator.dispatch",
               side_effect=lambda *a, **k: next(call_iter)), \
         patch("aho.pipeline.orchestrator.log_event"):
        with pytest.raises(EmptyContentError):
            run_cascade(
                document_path=str(doc),
                role_assignment=_role_assignment(),
                output_dir=str(out_dir),
            )

    # Both the successful indexer_in and the empty-content producer artifacts
    # should exist — forensic trail preserved.
    assert (out_dir / "indexer_in.json").exists()
    assert (out_dir / "producer.json").exists()
    prod_data = json.loads((out_dir / "producer.json").read_text())
    assert prod_data["output_chars"] == 0
    assert prod_data["error"] is None
    # Downstream stages (auditor, indexer_out, assessor) must NOT have been
    # dispatched — the halt stops propagation.
    assert not (out_dir / "auditor.json").exists()
    assert not (out_dir / "indexer_out.json").exists()
    assert not (out_dir / "assessor.json").exists()
