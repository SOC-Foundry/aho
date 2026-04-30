"""Cascade orchestrator — 5-stage pipeline execution (0.2.14 W1).

Executes: indexer_in → producer → auditor → indexer_out → assessor
Each stage dispatches to the model assigned in the RoleAssignment.
Each handoff emits a trace event via the aho event log.
"""
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from aho.pipeline.schemas import (
    RoleAssignment, PipelineTrace, HandoffEvent,
    DeltaProposal, DeltaValidation, DeltaItem,
)
from aho.pipeline.dispatcher import dispatch, EmptyContentError
from aho.logger import log_event


STAGE_ORDER = ["indexer_in", "producer", "auditor", "indexer_out", "assessor"]

STAGE_SYSTEM_PROMPTS = {
    "indexer_in": (
        "You are an Indexer (pre-producer). Scan the input document against known registries, "
        "gotchas, ADRs, and patterns. Flag anything relevant. Propose deltas if the input reveals "
        "gaps in the harness. Output a JSON object with keys: summary (string), "
        "proposed_deltas (array of {category, confidence, evidence_citation, proposed_text, canonical_target_path})."
    ),
    "producer": (
        "You are a Producer. Analyze the input document and produce a structured analytical report. "
        "Focus on: key concepts, architecture patterns, data flow, potential issues, and actionable insights. "
        "Output a JSON object with keys: title (string), sections (array of {heading, content}), "
        "key_findings (array of strings)."
    ),
    "auditor": (
        "You are an Auditor. You receive the Producer's analysis AND the Indexer-in's proposed deltas. "
        "Validate both: is the analysis accurate? Are the proposed deltas warranted? "
        "Accept or reject each delta with reasoning. "
        "Output a JSON object with keys: analysis_review (string), "
        "delta_validations (array of {accepted: bool, reasoning: string}), "
        "additional_findings (array of strings)."
    ),
    "indexer_out": (
        "You are an Indexer (post-auditor). Scan the Auditor's findings for new insights. "
        "Propose additional deltas based on what the audit surfaced. "
        "Output a JSON object with keys: summary (string), "
        "proposed_deltas (array of {category, confidence, evidence_citation, proposed_text, canonical_target_path})."
    ),
    "assessor": (
        "You are an Assessor. You receive ALL prior work products plus the Indexer-out's proposed deltas. "
        "Produce a meta-assessment: what is the overall quality of the analysis pipeline's output? "
        "Validate the Indexer-out's deltas. Produce a final work product summarizing the document. "
        "Output a JSON object with keys: overall_assessment (string), quality_score (0-100), "
        "delta_validations (array of {accepted: bool, reasoning: string}), "
        "final_summary (string), recommendations (array of strings)."
    ),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_stage_prompt(stage: str, document: str,
                        prior_outputs: dict[str, str]) -> str:
    """Build the prompt for a given stage, including prior stage outputs."""
    parts = []

    if stage == "indexer_in":
        parts.append(f"## Input Document\n\n{document}")

    elif stage == "producer":
        parts.append(f"## Input Document\n\n{document}")
        if "indexer_in" in prior_outputs:
            parts.append(f"\n## Indexer-in Analysis\n\n{prior_outputs['indexer_in']}")

    elif stage == "auditor":
        parts.append(f"## Producer Analysis\n\n{prior_outputs.get('producer', '(none)')}")
        parts.append(f"\n## Indexer-in Proposed Deltas\n\n{prior_outputs.get('indexer_in', '(none)')}")

    elif stage == "indexer_out":
        parts.append(f"## Auditor Findings\n\n{prior_outputs.get('auditor', '(none)')}")

    elif stage == "assessor":
        for prior_stage in ["indexer_in", "producer", "auditor", "indexer_out"]:
            if prior_stage in prior_outputs:
                label = prior_stage.replace("_", " ").title()
                parts.append(f"## {label} Output\n\n{prior_outputs[prior_stage]}")

    return "\n\n".join(parts)


def run_cascade(document_path: str, role_assignment: RoleAssignment,
                output_dir: Optional[str] = None,
                stage_timeout: int = 3600,
                document_text: Optional[str] = None,
                workstream_id: str = "W0") -> PipelineTrace:
    """Execute the 5-stage cascade pipeline.

    Args:
        document_path: Path to input document (used as document_id in trace).
        role_assignment: Model binding for each role.
        output_dir: Directory for per-stage output artifacts. Created if needed.
        stage_timeout: Max seconds per stage (default 3600 = 60 min).
        document_text: Pre-loaded document text. If None, reads from document_path.
        workstream_id: Workstream label for emitted handoff events.

    Returns:
        PipelineTrace with full execution record.

    Raises:
        EmptyContentError: a stage returned error=None with 0-char content
            (halt-on-empty semantics; the cascade does not propagate a silent
            empty-string to downstream stages).
    """
    run_id = uuid.uuid4().hex[:12]
    trace = PipelineTrace(
        pipeline_run_id=run_id,
        document_id=str(document_path),
        role_assignment=role_assignment,
        dispatch_layer="ollama-direct",
        started_at=_now_iso(),
    )

    if document_text is None:
        document_text = Path(document_path).read_text()

    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        out_path = None

    prior_outputs: dict[str, str] = {}
    pipeline_start = time.monotonic()

    for stage in STAGE_ORDER:
        model_id = getattr(role_assignment, stage)
        system_prompt = STAGE_SYSTEM_PROMPTS[stage]
        user_prompt = _build_stage_prompt(stage, document_text, prior_outputs)

        # Truncate document for non-first stages to manage context
        # First stage gets full doc; others get prior outputs only
        stage_start = _now_iso()
        stage_clock_start = time.monotonic()

        log_event(
            event_type="pipeline_handoff",
            source_agent="cascade-orchestrator",
            target=stage,
            action="dispatch",
            input_summary=f"run={run_id} stage={stage} model={model_id} input_chars={len(user_prompt)}",
            workstream_id=workstream_id,
        )

        result = dispatch(model_id, user_prompt, system=system_prompt,
                          timeout=stage_timeout)

        stage_elapsed = time.monotonic() - stage_clock_start
        stage_end = _now_iso()

        response_text = result["response"]
        error = result["error"]
        partial = error is not None and len(response_text) > 0

        handoff = HandoffEvent(
            stage=stage,
            started_at=stage_start,
            completed_at=stage_end,
            wall_clock_seconds=round(stage_elapsed, 2),
            partial_completion=partial or (error is not None),
            error=error,
            output_size_chars=len(response_text),
        )
        trace.handoffs.append(handoff)

        if error and not response_text:
            trace.exceptions.append(f"{stage}: {error}")
            prior_outputs[stage] = f"[stage failed: {error}]"
        else:
            prior_outputs[stage] = response_text

        # Write per-stage output artifact
        if out_path:
            stage_file = out_path / f"{stage}.json"
            stage_data = {
                "stage": stage,
                "model": model_id,
                "wall_clock_seconds": round(stage_elapsed, 2),
                "output_chars": len(response_text),
                "error": error,
                "partial": partial,
                "response": response_text[:50000],  # cap artifact size
            }
            stage_file.write_text(json.dumps(stage_data, indent=2) + "\n")

        log_event(
            event_type="pipeline_handoff",
            source_agent="cascade-orchestrator",
            target=stage,
            action="complete",
            output_summary=f"run={run_id} stage={stage} chars={len(response_text)} elapsed={stage_elapsed:.1f}s error={error}",
            workstream_id=workstream_id,
        )

        # Halt-on-empty: stage returned cleanly with 0-char content.
        # Stage artifact and completion event already written above so the
        # forensic trail is preserved; raise to the caller before continuing.
        if error is None and not response_text:
            raise EmptyContentError(
                f"Stage {stage!r} (model={model_id}) emitted 0-char content "
                f"with no error (run_id={run_id}). Halting cascade; downstream "
                f"stages will not be dispatched."
            )

    pipeline_elapsed = time.monotonic() - pipeline_start
    trace.total_wall_clock_seconds = round(pipeline_elapsed, 2)
    trace.completed_at = _now_iso()

    # Write trace to output dir
    if out_path:
        trace_file = out_path / "trace.json"
        trace_file.write_text(trace.model_dump_json(indent=2) + "\n")

    return trace
