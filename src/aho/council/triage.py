"""council.triage — real implementation (W2).

Calls nemotron-mini:4b via host Ollama for two modes:

1. classify(): assign an artifact to one of a fixed rubric. Out-of-rubric
   model output raises CouncilTriageMalformedError. NO categories[-1]
   fallback (G083 — silent rubber-stamp gotcha this primitive refuses).

2. draft_registry_delta(): given an executor-output blob and the current
   registry state (gotcha registry + ADR index), draft proposed new
   entries. Drafts are *proposals* — the dispatcher writes them later.

Wire-up env:
- OLLAMA_BASE_URL — default http://localhost:11434
- AHO_COUNCIL_TRIAGE_MODEL — default nemotron-mini:4b
- AHO_COUNCIL_TRIAGE_TIMEOUT_S — default 120
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.council.triage")
except ImportError:  # pragma: no cover
    _otel_trace = None
    _tracer = None

from ._client import (
    CouncilModelOutputMalformedError,
    CouncilTransportError,
    chat,
    extract_message_content,
    parse_json_strict,
)

DEFAULT_MODEL = "nemotron-mini:4b"
DEFAULT_TIMEOUT_S = 120.0

# Rubric — fixed at module level. Adding a category is a deliberate change,
# not a model-output-tolerated drift.
CLASSIFY_CATEGORIES = (
    "gotcha-candidate",
    "ADR-relevance",
    "gate-state",
    "work-shape-tier-decision",
)


class CouncilTriageInputError(ValueError):
    """Caller passed a None / wrong-typed artifact."""


class CouncilTriageMalformedError(RuntimeError):
    """Model output not parseable as the expected JSON shape, OR returned a
    category outside the rubric, OR confidence outside [0,1]. Raise — never
    fall back to categories[-1] or synthesise a 'best-guess' shape.
    """


def _model() -> str:
    return os.environ.get("AHO_COUNCIL_TRIAGE_MODEL", DEFAULT_MODEL)


def _timeout_s() -> float:
    raw = os.environ.get("AHO_COUNCIL_TRIAGE_TIMEOUT_S")
    if raw is None:
        return DEFAULT_TIMEOUT_S
    try:
        return float(raw)
    except ValueError as exc:
        raise CouncilTriageInputError(
            f"AHO_COUNCIL_TRIAGE_TIMEOUT_S={raw!r} not parseable as float"
        ) from exc


def _tier() -> str:
    return os.environ.get("AHO_TIER", "base")


def _emit_span(
    *,
    mode: str,
    latency_ms: int,
    confidence: Optional[float] = None,
    category: Optional[str] = None,
    proposals_count: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    if _tracer is None:
        return
    with _tracer.start_as_current_span("aho.council.triage") as span:
        try:
            span.set_attribute("aho.council.role", "triage")
            span.set_attribute("aho.council.work_shape", mode)
            span.set_attribute("aho.tier", _tier())
            span.set_attribute("aho.model", _model())
            span.set_attribute("aho.council.latency_ms", latency_ms)
            if confidence is not None:
                span.set_attribute("aho.council.confidence", confidence)
            if category is not None:
                span.set_attribute("aho.council.category", category)
            if proposals_count is not None:
                span.set_attribute("aho.council.proposals_count", proposals_count)
            if error is not None:
                span.set_attribute("aho.council.error", error)
            # Materiality bucket: triage decisions feed downstream triage rate.
            span.set_attribute("aho.materiality.bucket", "triage_decision")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Mode 1: classify
# ---------------------------------------------------------------------------

_CLASSIFY_SYSTEM = """You are aho's council triage classifier (base tier).

Given an artifact text blob, classify it into EXACTLY ONE of these categories:
- gotcha-candidate: artifact describes a failure mode, footgun, or surprising
  behavior that should land in the gotcha registry.
- ADR-relevance: artifact contains a decision worth promoting to an ADR.
- gate-state: artifact describes the state of an iteration / workstream gate
  (open, closed, deferred, blocked).
- work-shape-tier-decision: artifact describes a routing / tier-assignment
  decision (which model, which container, which environment).

You MUST respond with JSON in EXACTLY this shape, no other keys:
{"category": "<one of the four exact strings>", "confidence": <float 0.0 to 1.0>, "rationale_summary": "<one short sentence>"}

If the artifact does not clearly fit any category, return category "unknown"
with confidence 0.0 and a one-sentence rationale. NEVER invent a fifth
category. NEVER return narrative outside the JSON object.
"""


def _validate_classify_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise CouncilTriageMalformedError(
            f"classify payload not a JSON object: {type(payload).__name__}"
        )
    missing = {"category", "confidence", "rationale_summary"} - set(payload.keys())
    if missing:
        raise CouncilTriageMalformedError(
            f"classify payload missing required keys: {sorted(missing)}"
        )
    category = payload["category"]
    if not isinstance(category, str):
        raise CouncilTriageMalformedError(
            f"classify category not a string: {type(category).__name__}"
        )
    if category not in CLASSIFY_CATEGORIES and category != "unknown":
        raise CouncilTriageMalformedError(
            f"classify category {category!r} not in rubric "
            f"{CLASSIFY_CATEGORIES + ('unknown',)} — refusing categories[-1] fallback"
        )
    confidence = payload["confidence"]
    if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0):
        raise CouncilTriageMalformedError(
            f"classify confidence {confidence!r} not a float in [0,1]"
        )
    rationale = payload["rationale_summary"]
    if not isinstance(rationale, str) or not rationale.strip():
        raise CouncilTriageMalformedError(
            f"classify rationale_summary not a non-empty string: {rationale!r}"
        )
    return {
        "category": category,
        "confidence": float(confidence),
        "rationale_summary": rationale.strip(),
    }


def classify(artifact: Any) -> Dict[str, Any]:
    """Classify an artifact into the fixed rubric. Returns dict with
    category, confidence, rationale_summary, mode, model, latency_ms.
    Raises CouncilTriageInputError or CouncilTriageMalformedError.
    """
    if artifact is None:
        raise CouncilTriageInputError("artifact must not be None")
    if not isinstance(artifact, str):
        raise CouncilTriageInputError(
            f"artifact must be str, got {type(artifact).__name__}"
        )
    if not artifact.strip():
        raise CouncilTriageInputError("artifact must not be empty")

    start = time.monotonic()
    try:
        response = chat(
            _model(),
            [
                {"role": "system", "content": _CLASSIFY_SYSTEM},
                {"role": "user", "content": f"Artifact:\n{artifact}"},
            ],
            options={"temperature": 0.0},
            format_json=True,
            timeout_s=_timeout_s(),
        )
    except CouncilTransportError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(mode="classify", latency_ms=latency_ms, error=type(exc).__name__)
        raise

    try:
        raw = extract_message_content(response)
        parsed = parse_json_strict(raw)
        validated = _validate_classify_payload(parsed)
    except CouncilModelOutputMalformedError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(mode="classify", latency_ms=latency_ms, error=type(exc).__name__)
        raise CouncilTriageMalformedError(str(exc)) from exc

    latency_ms = int((time.monotonic() - start) * 1000)
    _emit_span(
        mode="classify",
        latency_ms=latency_ms,
        confidence=validated["confidence"],
        category=validated["category"],
    )
    return {
        **validated,
        "mode": "classify",
        "model": _model(),
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Mode 2: draft_registry_delta
# ---------------------------------------------------------------------------

DELTA_KINDS = ("gotcha", "ADR-candidate")

_DELTA_SYSTEM = """You are aho's council registry-delta drafter (base tier).

You receive an executor-output blob and a JSON snapshot of the current
registry state (existing gotcha IDs and ADR titles). Your job is to draft
PROPOSALS for new registry entries that the executor's output suggests
should land in the registry. You DO NOT write to the registry — you only
draft proposals. Dispatcher routes proposals through approval flow later.

You MUST respond with JSON in EXACTLY this shape, no other keys:
{
  "proposals": [
    {"kind": "<gotcha|ADR-candidate>", "proposed_text": "<one short sentence>", "confidence": <0.0 to 1.0>, "rationale": "<one short sentence>"}
  ]
}

If nothing in the executor output suggests a new registry entry, return
{"proposals": []}. NEVER invent kinds outside of {gotcha, ADR-candidate}.
NEVER return narrative outside the JSON object.
"""


def _validate_delta_payload(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        raise CouncilTriageMalformedError(
            f"delta payload not a JSON object: {type(payload).__name__}"
        )
    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        raise CouncilTriageMalformedError(
            f"delta payload 'proposals' must be list, got {type(proposals).__name__}"
        )
    out: List[Dict[str, Any]] = []
    for idx, p in enumerate(proposals):
        if not isinstance(p, dict):
            raise CouncilTriageMalformedError(
                f"proposal[{idx}] not a JSON object: {type(p).__name__}"
            )
        missing = {"kind", "proposed_text", "confidence", "rationale"} - set(p.keys())
        if missing:
            raise CouncilTriageMalformedError(
                f"proposal[{idx}] missing keys: {sorted(missing)}"
            )
        kind = p["kind"]
        if kind not in DELTA_KINDS:
            raise CouncilTriageMalformedError(
                f"proposal[{idx}].kind {kind!r} not in {DELTA_KINDS}"
            )
        proposed = p["proposed_text"]
        if not isinstance(proposed, str) or not proposed.strip():
            raise CouncilTriageMalformedError(
                f"proposal[{idx}].proposed_text not a non-empty string"
            )
        confidence = p["confidence"]
        if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0):
            raise CouncilTriageMalformedError(
                f"proposal[{idx}].confidence {confidence!r} not a float in [0,1]"
            )
        rationale = p["rationale"]
        if not isinstance(rationale, str) or not rationale.strip():
            raise CouncilTriageMalformedError(
                f"proposal[{idx}].rationale not a non-empty string"
            )
        out.append({
            "kind": kind,
            "proposed_text": proposed.strip(),
            "confidence": float(confidence),
            "rationale": rationale.strip(),
        })
    return out


def draft_registry_delta(
    executor_output: Any, registry_snapshot: Any
) -> Dict[str, Any]:
    """Draft proposed registry entries. Returns dict with 'proposals'
    (list), 'mode', 'model', 'latency_ms'.
    """
    if not isinstance(executor_output, str) or not executor_output.strip():
        raise CouncilTriageInputError("executor_output must be non-empty str")
    if not isinstance(registry_snapshot, (dict, str)):
        raise CouncilTriageInputError(
            f"registry_snapshot must be dict or str, got {type(registry_snapshot).__name__}"
        )

    start = time.monotonic()
    snapshot_text = (
        registry_snapshot
        if isinstance(registry_snapshot, str)
        else __import__("json").dumps(registry_snapshot, indent=2)
    )
    try:
        response = chat(
            _model(),
            [
                {"role": "system", "content": _DELTA_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Executor output:\n{executor_output}\n\n"
                        f"Current registry snapshot:\n{snapshot_text}"
                    ),
                },
            ],
            options={"temperature": 0.0},
            format_json=True,
            timeout_s=_timeout_s(),
        )
    except CouncilTransportError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(
            mode="registry_delta_draft",
            latency_ms=latency_ms,
            error=type(exc).__name__,
        )
        raise

    try:
        raw = extract_message_content(response)
        parsed = parse_json_strict(raw)
        proposals = _validate_delta_payload(parsed)
    except CouncilModelOutputMalformedError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(
            mode="registry_delta_draft",
            latency_ms=latency_ms,
            error=type(exc).__name__,
        )
        raise CouncilTriageMalformedError(str(exc)) from exc

    latency_ms = int((time.monotonic() - start) * 1000)
    _emit_span(
        mode="registry_delta_draft",
        latency_ms=latency_ms,
        proposals_count=len(proposals),
    )
    return {
        "proposals": proposals,
        "mode": "registry_delta_draft",
        "model": _model(),
        "latency_ms": latency_ms,
    }
