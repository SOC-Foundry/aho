"""council.audit - real implementation (W2).

Calls llama3.2:3b via host Ollama for structural spot-check audits.
Combines deterministic pre-checks (G081 banned-phrase scan, three-octet
versioning detection, git-op-reference scan) with a model-driven spot
check, then enforces a confidence floor of 0.85 - disposition `clean` is
structurally unreachable below the floor (overrides to `surface_to_drafter`).

This is the primitive Adversarial Authorship at base tier sits on. It must
fail loud - never silently rubber-stamp.

Wire-up env:
- OLLAMA_BASE_URL - default http://localhost:11434
- AHO_COUNCIL_AUDIT_MODEL - default llama3.2:3b
- AHO_COUNCIL_AUDIT_TIMEOUT_S - default 180
- AHO_COUNCIL_AUDIT_CONFIDENCE_FLOOR - default 0.85
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.council.audit")
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
from .audit_finding_filter import filter_findings
from .audit_ref_extract import RefExtractError, detect_references
from .audit_ref_lookup import RefLookupError, lookup_references

DEFAULT_MODEL = "llama3.2:3b"
DEFAULT_TIMEOUT_S = 180.0
DEFAULT_CONFIDENCE_FLOOR = 0.85
# Cap registered-references entries surfaced to the auditor. Each entry is
# ID + kind + top-1 snippet ≈ 250 chars; 30 entries fits comfortably under
# the 5K-token RAG section budget called out in the W3 plan doc.
DEFAULT_MAX_ENRICHMENT_REFS = 30
# Hard ceiling on the constructed prompt - system + enrichment + user
# blocks. Plan budget is 28K tokens (4K headroom in 32K ctx); chars-per-
# token for dense JSON-heavy archives runs ~3, so 84K chars is the
# conservative ceiling guard.
PROMPT_CHAR_CEILING = 84_000

DISPOSITIONS = ("clean", "halt", "surface_to_drafter")

# Canonical severity values + an explicit synonym table. The synonym map
# is NOT a categories[-1] fallback - it's a documented, exhaustive
# normalisation. Unknown severity strings still raise
# CouncilAuditMalformedError. The map exists because llama3.2:3b
# frequently mirrors source-artifact vocabulary (e.g. "moderate" from
# carry-forward entries) rather than picking from the prompt's enum.
SEVERITIES = ("info", "important", "critical")
SEVERITY_SYNONYMS = {
    "low": "info",
    "minor": "info",
    "cosmetic": "info",
    "trivial": "info",
    "negligible": "info",
    "medium": "important",
    "moderate": "important",
    "notable": "important",
    "significant": "important",
    "warning": "important",
    "high": "critical",
    "severe": "critical",
    "blocker": "critical",
    "blocking": "critical",
    "fatal": "critical",
}


def normalise_severity(sev: str) -> str:
    """Map sev to canonical {info, important, critical}. Raises
    CouncilAuditMalformedError on unknown values - synonym table is
    exhaustive and explicit, not an open-ended fallback (G083).
    """
    if not isinstance(sev, str):
        raise CouncilAuditMalformedError(
            f"severity must be str, got {type(sev).__name__}"
        )
    cleaned = sev.strip().lower()
    if cleaned in SEVERITIES:
        return cleaned
    if cleaned in SEVERITY_SYNONYMS:
        return SEVERITY_SYNONYMS[cleaned]
    raise CouncilAuditMalformedError(
        f"severity {sev!r} not in {SEVERITIES} and not in known synonym table"
    )

# G081 - banned celebratory framing. Patterns are case-insensitive,
# anchored on whitespace/punctuation to avoid sub-string false positives
# (e.g. "shipping" should not match "shipped"). Documented in CLAUDE.md.
_BANNED_PHRASE_PATTERNS = [
    re.compile(r"\bclean[\s-]+close\b", re.IGNORECASE),
    re.compile(r"\blanded[\s-]+beautifully\b", re.IGNORECASE),
    re.compile(r"\ball[\s-]+green\b", re.IGNORECASE),
    re.compile(r"(?<![a-z])shipped(?![a-z])", re.IGNORECASE),
]

# Patterns suggesting agent-side git operations (Pillar 11 violation).
# Conservative - flagged for human review, not auto-fail.
_GIT_OP_PATTERNS = [
    re.compile(r"\bgit[\s-]+(commit|push|merge|add|reset|rebase|cherry[\s-]?pick)\b", re.IGNORECASE),
    re.compile(r"\bgh[\s]+pr[\s]+(create|merge|close)\b", re.IGNORECASE),
]

# Sentinels marking a git-op mention as Pillar 11 *enforcement narration*
# rather than agent execution. Within ±_GIT_OP_SENTINEL_WINDOW chars of a
# git-op regex hit, any sentinel match suppresses that hit. Closes the
# 0.2.18 W0 false-positive shape: an acceptance archive narrating the
# Pillar 11 invariant ("No `git commit`, `git push`, ... from this
# session") tripped the pre-check on its own enforcement language. The
# pre-check is a fast-path heuristic - model + post-hoc filter remain the
# substantive defenses against actual violations.
_GIT_OP_ENFORCEMENT_SENTINELS = re.compile(
    r"(?:"
    r"\boperator[\s-]?only\b"
    r"|\boperator[\s-]?side\b"
    r"|\boperator[\s-]?execute(?:d|s)?\b"
    r"|\boperator[\s_-]?action\b"
    r"|\bagent[\s-]?surface(?:s|d)?\b"
    r"|\bnever[\s-]?execute(?:s|d)?\b"
    r"|\bno[\s-]?agent[\s-]?write\w*\b"
    r"|\bOPR-"
    r"|\bno[\s`]+git\b"
    r")",
    re.IGNORECASE,
)
_GIT_OP_SENTINEL_WINDOW = 150

# Three-octet versioning - phase.iteration.run.
_THREE_OCTET_PATTERN = re.compile(r"\b\d+\.\d+\.\d+\b")


class CouncilAuditInputError(ValueError):
    """Caller passed an unusable artifact."""


class CouncilAuditMalformedError(RuntimeError):
    """Model output didn't parse as the expected disposition shape."""


def _model() -> str:
    return os.environ.get("AHO_COUNCIL_AUDIT_MODEL", DEFAULT_MODEL)


def _timeout_s() -> float:
    raw = os.environ.get("AHO_COUNCIL_AUDIT_TIMEOUT_S")
    if raw is None:
        return DEFAULT_TIMEOUT_S
    try:
        return float(raw)
    except ValueError as exc:
        raise CouncilAuditInputError(
            f"AHO_COUNCIL_AUDIT_TIMEOUT_S={raw!r} not parseable as float"
        ) from exc


def _confidence_floor() -> float:
    raw = os.environ.get("AHO_COUNCIL_AUDIT_CONFIDENCE_FLOOR")
    if raw is None:
        return DEFAULT_CONFIDENCE_FLOOR
    try:
        v = float(raw)
    except ValueError as exc:
        raise CouncilAuditInputError(
            f"AHO_COUNCIL_AUDIT_CONFIDENCE_FLOOR={raw!r} not parseable"
        ) from exc
    if not (0.0 <= v <= 1.0):
        raise CouncilAuditInputError(
            f"AHO_COUNCIL_AUDIT_CONFIDENCE_FLOOR={v} outside [0,1]"
        )
    return v


def _tier() -> str:
    return os.environ.get("AHO_TIER", "base")


# ---------------------------------------------------------------------------
# Deterministic pre-checks
# ---------------------------------------------------------------------------

def _scan_banned_phrases(text: str) -> List[str]:
    hits: List[str] = []
    for pattern in _BANNED_PHRASE_PATTERNS:
        for m in pattern.finditer(text):
            hits.append(m.group(0))
    return hits


def _scan_git_ops(text: str) -> List[str]:
    """Return git-op regex hits, suppressing those wrapped in Pillar 11
    enforcement narration. A hit is suppressed if any
    `_GIT_OP_ENFORCEMENT_SENTINELS` token matches within ±
    `_GIT_OP_SENTINEL_WINDOW` chars of the hit span. Suppression is fast-
    path only - model spot-check still sees the artifact and can flag
    semantic violations that slip the regex.
    """
    hits: List[str] = []
    for pattern in _GIT_OP_PATTERNS:
        for m in pattern.finditer(text):
            window_start = max(0, m.start() - _GIT_OP_SENTINEL_WINDOW)
            window_end = min(len(text), m.end() + _GIT_OP_SENTINEL_WINDOW)
            if _GIT_OP_ENFORCEMENT_SENTINELS.search(text[window_start:window_end]):
                continue
            hits.append(m.group(0))
    return hits


def _scan_three_octet(text: str) -> List[str]:
    return _THREE_OCTET_PATTERN.findall(text)


def _structural_pre_checks(artifact: str) -> Dict[str, Any]:
    """Deterministic checks - no model involvement. Findings here are
    high-confidence (regex-grounded) and feed into the final disposition.
    """
    banned = _scan_banned_phrases(artifact)
    git_ops = _scan_git_ops(artifact)
    versions = _scan_three_octet(artifact)
    return {
        "g081_banned_phrases": "fail" if banned else "pass",
        "g081_banned_phrases_hits": banned,
        "git_ops_referenced": "fail" if git_ops else "pass",
        "git_ops_hits": git_ops,
        "three_octet_versioning_present": "pass" if versions else "n/a",
        "three_octet_versioning_examples": versions[:5],
    }


# ---------------------------------------------------------------------------
# Model-driven spot check
# ---------------------------------------------------------------------------

_AUDIT_SYSTEM = """You are aho's council auditor (base tier, llama3.2 seat).

You perform STRUCTURAL spot-checks against an audit target. Your job is NOT
to write the artifact, NOT to summarize it, and NOT to celebrate it. Your
job is to identify mismatches between what the artifact claims and what it
demonstrates.

Spot-check for:
- Did the executor say it did X? Does the artifact corroborate X?
- Did the executor reference a gotcha / ADR / carry-forward by ID? Does
  the ID look real (matches naming conventions)?
- Did the workstream contract require deliverables A, B, C? Is each present?
- Did the executor close a checkpoint cleanly?
- Are there celebratory or rubber-stamp phrases? (G081)
- Is there any reference to agent-side git ops? (Pillar 11)

ALLOWED DISPOSITION VALUES (pick exactly one): clean, halt, surface_to_drafter
ALLOWED SEVERITY VALUES (per finding): info, important, critical

Severity mapping if you would normally say: low / minor / cosmetic → info;
medium / moderate / notable → important; high / severe / blocker → critical.
Do NOT invent any other severity string. The harness will REJECT any value
outside info / important / critical.

Respond with a JSON object containing exactly these keys:
- disposition (string): one of clean / halt / surface_to_drafter
- confidence (float): 0.0 to 1.0, your actual certainty
- findings (array of objects): each finding is {id, severity, description}
  where id is the deliverable / section / claim ID you are flagging
  (e.g. "D7", "F-0.2.17-W1-003", "B2.5"), severity is info / important /
  critical, and description is a SPECIFIC sentence about THIS artifact
  (NOT placeholder text - name the actual claim or section).
- evidence_traces (array of strings): each is a verbatim short phrase
  COPIED from the audit target itself (NOT from this prompt). If you
  cannot cite a phrase from the target, the spot-check failed and you
  should set disposition=surface_to_drafter.

Rules:
- Pick ONE disposition string from the allowed list. Never write
  "clean | halt | surface_to_drafter" - that is the menu, not the answer.
- NEVER use "AF-1", "concise sentence", or "short phrase quoted from the
  artifact" - those are illustrative tokens. Use IDs and quotes from the
  ACTUAL artifact you are auditing.
- Confidence MUST reflect your actual certainty. If you would not stake
  your audit chair on the disposition, set confidence below 0.85 - the
  harness will then route to surface_to_drafter automatically.
- If the findings list is empty, evidence_traces must still cite at least
  one phrase from the artifact you spot-checked.
- If the prompt contains a "## Registered references retrieved from project
  context" section, treat it as authoritative ground truth on which IDs are
  real. Before flagging any reference ID as 'not real,' 'placeholder,' 'not
  corroborated,' or 'fake,' check that section. If the ID is listed with
  status `registered`, do NOT flag it - its definition exists in another
  archive (the snippet shows where). If the ID is listed with status
  `unverified`, flag for verification rather than as fake - the ID may be
  newly introduced in this archive itself, which is normal.
- Return JSON only. No markdown, no narrative outside the JSON object.
"""


def _validate_disposition_payload(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise CouncilAuditMalformedError(
            f"audit payload not a JSON object: {type(payload).__name__}"
        )
    missing = {"disposition", "confidence", "findings", "evidence_traces"} - set(payload.keys())
    if missing:
        raise CouncilAuditMalformedError(
            f"audit payload missing required keys: {sorted(missing)}"
        )
    disposition = payload["disposition"]
    if disposition not in DISPOSITIONS:
        raise CouncilAuditMalformedError(
            f"audit disposition {disposition!r} not in {DISPOSITIONS}"
        )
    confidence = payload["confidence"]
    if not isinstance(confidence, (int, float)) or not (0.0 <= float(confidence) <= 1.0):
        raise CouncilAuditMalformedError(
            f"audit confidence {confidence!r} not a float in [0,1]"
        )
    findings = payload["findings"]
    if not isinstance(findings, list):
        raise CouncilAuditMalformedError(
            f"audit findings must be list, got {type(findings).__name__}"
        )
    cleaned_findings: List[Dict[str, Any]] = []
    for idx, f in enumerate(findings):
        if not isinstance(f, dict):
            raise CouncilAuditMalformedError(
                f"finding[{idx}] not a JSON object: {type(f).__name__}"
            )
        missing_f = {"id", "severity", "description"} - set(f.keys())
        if missing_f:
            raise CouncilAuditMalformedError(
                f"finding[{idx}] missing keys: {sorted(missing_f)}"
            )
        sev = normalise_severity(f["severity"])
        cleaned_findings.append({
            "id": str(f["id"]),
            "severity": sev,
            "description": str(f["description"]).strip(),
        })
    evidence = payload["evidence_traces"]
    if not isinstance(evidence, list):
        raise CouncilAuditMalformedError(
            f"audit evidence_traces must be list, got {type(evidence).__name__}"
        )
    cleaned_evidence = [str(e).strip() for e in evidence if str(e).strip()]
    return {
        "disposition": disposition,
        "confidence": float(confidence),
        "findings": cleaned_findings,
        "evidence_traces": cleaned_evidence,
    }


# ---------------------------------------------------------------------------
# RAG enrichment - registered-references context section (W3)
# ---------------------------------------------------------------------------

ENRICHMENT_SECTION_HEADER = "## Registered references retrieved from project context"


def _max_retrieval_score(result: Dict[str, Any]) -> float:
    retrievals = result.get("retrievals") or []
    if not retrievals:
        return 0.0
    return max(float(r.get("score", 0.0)) for r in retrievals)


def _format_enrichment_section(
    results: List[Dict[str, Any]],
) -> str:
    """Render lookup results as the Registered references prompt section.
    Empty results produce empty string (caller should omit the section).
    """
    if not results:
        return ""
    lines: List[str] = [
        ENRICHMENT_SECTION_HEADER,
        "",
        (
            "Each entry below is a reference-shaped token detected in the "
            "audit target, with status `registered` if its definition was "
            "found elsewhere in the project iteration-context, or "
            "`unverified` if not. Use this as ground truth before flagging "
            "any ID as 'not real' or 'placeholder.'"
        ),
        "",
    ]
    for result in results:
        ident = result.get("id")
        kind = result.get("kind")
        status = result.get("status")
        retrievals = result.get("retrievals") or []
        lines.append(f"- **{ident}** ({kind}) - status: `{status}`")
        if retrievals:
            top = retrievals[0]
            path = top.get("source_artifact_path") or "<unknown>"
            iteration = top.get("source_iteration") or "?"
            workstream = top.get("source_workstream") or "?"
            snippet = top.get("snippet") or ""
            lines.append(
                f"  - source: `{path}` ({iteration} / {workstream})"
            )
            lines.append(f"  - snippet: {snippet}")
        else:
            lines.append("  - source: not found in iteration-context")
    lines.append("")
    return "\n".join(lines)


def _build_enrichment(
    artifact: str,
    *,
    max_refs: int = DEFAULT_MAX_ENRICHMENT_REFS,
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """Run D1 + D2 against `artifact`. Returns enrichment metadata:

    {
        "section_text": str,  # empty if no refs detected
        "detected_count": int,
        "registered_count": int,
        "unverified_count": int,
        "truncated": bool,
        "results": [RefLookupResult, ...],  # truncated to max_refs
    }
    """
    refs = detect_references(artifact)
    if not refs:
        return {
            "section_text": "",
            "detected_count": 0,
            "registered_count": 0,
            "unverified_count": 0,
            "truncated": False,
            "results": [],
        }
    results = lookup_references(refs, project=project)
    truncated = False
    if len(results) > max_refs:
        results = sorted(results, key=_max_retrieval_score, reverse=True)
        results = results[:max_refs]
        truncated = True
    section_text = _format_enrichment_section(results)
    return {
        "section_text": section_text,
        "detected_count": len(refs),
        "registered_count": sum(1 for r in results if r.get("status") == "registered"),
        "unverified_count": sum(1 for r in results if r.get("status") == "unverified"),
        "truncated": truncated,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Confidence floor - STRUCTURALLY ENFORCED
# ---------------------------------------------------------------------------

def enforce_confidence_floor(
    disposition: str,
    confidence: float,
    *,
    floor: Optional[float] = None,
) -> Dict[str, Any]:
    """If confidence < floor and disposition == 'clean', lock disposition to
    'surface_to_drafter'. The clean disposition is unreachable below the
    floor by construction. Returns dict with new (or unchanged) disposition
    plus a `confidence_floor_locked` flag.

    This function is the load-bearing piece of the anti-rubber-stamp
    contract for the auditor. D8 mutation-tests it.
    """
    f = floor if floor is not None else _confidence_floor()
    if disposition == "clean" and float(confidence) < f:
        return {
            "disposition": "surface_to_drafter",
            "confidence_floor_locked": True,
            "confidence_floor": f,
            "original_disposition": "clean",
        }
    return {
        "disposition": disposition,
        "confidence_floor_locked": False,
        "confidence_floor": f,
    }


def _emit_span(
    *,
    disposition: str,
    confidence: float,
    findings_count: int,
    latency_ms: int,
    floor_locked: bool,
    error: Optional[str] = None,
    suppressed_count: int = 0,
    filter_eligible: bool = False,
) -> None:
    if _tracer is None:
        return
    with _tracer.start_as_current_span("aho.council.audit") as span:
        try:
            span.set_attribute("aho.council.role", "audit")
            span.set_attribute("aho.council.work_shape", "structural_audit")
            span.set_attribute("aho.tier", _tier())
            span.set_attribute("aho.model", _model())
            span.set_attribute("aho.council.disposition", disposition)
            span.set_attribute("aho.council.confidence", confidence)
            span.set_attribute("aho.council.findings_count", findings_count)
            span.set_attribute("aho.council.latency_ms", latency_ms)
            span.set_attribute("aho.council.confidence_floor_locked", floor_locked)
            span.set_attribute(
                "aho.council.audit.finding_filter.suppressed_count",
                suppressed_count,
            )
            span.set_attribute(
                "aho.council.audit.finding_filter.eligible",
                filter_eligible,
            )
            # Materiality - count audits that surface findings vs not.
            span.set_attribute(
                "aho.materiality.bucket",
                "claim_vs_artifact_mismatch_caught_by_llama"
                if findings_count > 0
                else "claim_vs_artifact_mismatch_no_finding",
            )
            if error is not None:
                span.set_attribute("aho.council.error", error)
        except Exception:
            pass


def audit(
    artifact: Any,
    *,
    contract: Optional[str] = None,
    floor: Optional[float] = None,
    num_ctx: int = 32768,
    rag_enrichment: bool = True,
    rag_project: Optional[str] = None,
    max_enrichment_refs: int = DEFAULT_MAX_ENRICHMENT_REFS,
) -> Dict[str, Any]:
    """Audit `artifact` (text). Optional `contract` provides the spec the
    artifact is being checked against. Returns the disposition dict.

    `num_ctx` is the Ollama context window size; default 32K suits
    workstream-scale acceptance archives. Drop to 8K-16K for unit-test
    fixtures. Llama3.2 native ctx is 128K so larger values are safe but
    waste VRAM; 32K is the iteration-context sweet spot.

    `rag_enrichment` (W3): when True, scan the artifact for reference-
    shaped tokens (carry-forward IDs, ADR refs, etc.), retrieve their
    definitions from the project iteration-context collection, and inject
    them as a "## Registered references retrieved from project context"
    section in the prompt between system and audit-target blocks.
    Disable to reproduce the W2 (non-RAG) auditor for cross-comparison.

    Confidence floor is structurally enforced - if model returns
    `clean` at low confidence, the disposition is locked to
    `surface_to_drafter` post-validation.
    """
    if not isinstance(artifact, str):
        raise CouncilAuditInputError(
            f"artifact must be str, got {type(artifact).__name__}"
        )
    if not artifact.strip():
        raise CouncilAuditInputError("artifact must be non-empty")

    started_utc = datetime.now(timezone.utc).isoformat()
    pre_checks = _structural_pre_checks(artifact)
    start = time.monotonic()

    enrichment_meta: Dict[str, Any] = {
        "enabled": bool(rag_enrichment),
        "detected_count": 0,
        "registered_count": 0,
        "unverified_count": 0,
        "truncated": False,
        "section_chars": 0,
        "results": [],
    }
    enrichment_section = ""
    if rag_enrichment:
        try:
            built = _build_enrichment(
                artifact,
                max_refs=max_enrichment_refs,
                project=rag_project,
            )
        except RefExtractError as exc:
            # Detection should never fail on a non-empty string artifact, but
            # surface clearly if it does - silent fall-through would weaken
            # the load-bearing fix from F-0.2.17-W2-006.
            raise CouncilAuditInputError(
                f"reference detection failed: {exc}"
            ) from exc
        enrichment_section = built["section_text"]
        enrichment_meta.update({
            "detected_count": built["detected_count"],
            "registered_count": built["registered_count"],
            "unverified_count": built["unverified_count"],
            "truncated": built["truncated"],
            "section_chars": len(enrichment_section),
            "results": built["results"],
        })

    user_blocks: List[str] = []
    if enrichment_section:
        user_blocks.append(enrichment_section)
    user_blocks.append(f"AUDIT TARGET:\n{artifact}")
    if contract:
        user_blocks.append(f"CONTRACT (what the artifact claims to satisfy):\n{contract}")

    user_content = "\n\n".join(user_blocks)
    total_chars = len(_AUDIT_SYSTEM) + len(user_content)
    if total_chars > PROMPT_CHAR_CEILING:
        raise CouncilAuditInputError(
            f"constructed prompt exceeds char ceiling "
            f"({total_chars} > {PROMPT_CHAR_CEILING}); shrink artifact, "
            f"reduce max_enrichment_refs, or split the audit target"
        )

    try:
        response = chat(
            _model(),
            [
                {"role": "system", "content": _AUDIT_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            options={"temperature": 0.0, "num_ctx": num_ctx},
            format_json=True,
            timeout_s=_timeout_s(),
        )
    except CouncilTransportError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(
            disposition="halt",
            confidence=0.0,
            findings_count=0,
            latency_ms=latency_ms,
            floor_locked=False,
            error=type(exc).__name__,
        )
        raise

    try:
        raw = extract_message_content(response)
        parsed = parse_json_strict(raw)
        validated = _validate_disposition_payload(parsed)
    except CouncilModelOutputMalformedError as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(
            disposition="halt",
            confidence=0.0,
            findings_count=0,
            latency_ms=latency_ms,
            floor_locked=False,
            error=type(exc).__name__,
        )
        raise CouncilAuditMalformedError(str(exc)) from exc

    floor_decision = enforce_confidence_floor(
        validated["disposition"], validated["confidence"], floor=floor
    )

    # Build the rag_summary up front so the W4 D1 deterministic post-hoc
    # filter can operate against the same registered-references view that
    # the audit return surfaces. Filter-eligibility requires at least one
    # registered ID; with enrichment disabled or empty, the filter is a
    # no-op and every model finding flows through unchanged.
    rag_summary: Dict[str, Any] = {
        "enabled": enrichment_meta["enabled"],
        "detected_count": enrichment_meta["detected_count"],
        "registered_count": enrichment_meta["registered_count"],
        "unverified_count": enrichment_meta["unverified_count"],
        "truncated": enrichment_meta["truncated"],
        "section_chars": enrichment_meta["section_chars"],
        "references": [
            {
                "id": r.get("id"),
                "kind": r.get("kind"),
                "status": r.get("status"),
                "top_source_artifact_path": (
                    (r.get("retrievals") or [{}])[0].get("source_artifact_path")
                    if r.get("retrievals") else None
                ),
            }
            for r in enrichment_meta["results"]
        ],
    }

    # W4 D1 - deterministic post-hoc filter on RAG-aware findings. Drops
    # only findings where BOTH a registered anchor appears in the
    # description AND a fake-ID phrase matches. Structurally narrow.
    filter_outcome = filter_findings(validated["findings"], rag_summary)
    model_findings_active: List[Dict[str, Any]] = filter_outcome["active_findings"]
    suppressed_findings: List[Dict[str, Any]] = filter_outcome["suppressed_findings"]

    # Merge structural pre-check findings into the disposition. Pre-check
    # findings are regex-grounded and high-confidence - they are NOT
    # subject to the post-hoc filter (the filter is scoped to the small-
    # model false-positive shape, not regex-driven structural defects).
    extra_findings: List[Dict[str, Any]] = []
    if pre_checks["g081_banned_phrases"] == "fail":
        extra_findings.append({
            "id": "AUDIT-G081",
            "severity": "important",
            "description": (
                "G081 banned phrase(s) detected: "
                + ", ".join(repr(p) for p in pre_checks["g081_banned_phrases_hits"])
            ),
        })
    if pre_checks["git_ops_referenced"] == "fail":
        extra_findings.append({
            "id": "AUDIT-PILLAR11",
            "severity": "critical",
            "description": (
                "Possible Pillar 11 reference (agent-side git op): "
                + ", ".join(repr(p) for p in pre_checks["git_ops_hits"])
            ),
        })

    final_findings = model_findings_active + extra_findings

    # If structural checks surfaced critical/important issues, the model's
    # `clean` disposition is overridden - structural pre-checks are
    # higher-confidence than model semantic analysis.
    final_disposition = floor_decision["disposition"]
    structural_override = False
    unsupported_halt_downgrade = False
    if extra_findings and final_disposition == "clean":
        final_disposition = "surface_to_drafter"
        structural_override = True

    # 0.2.18 W0 / F-0.2.18-W0-007 - unsupported-halt downgrade. If the
    # model returned `halt` but the post-hoc filter suppressed every
    # active model finding AND no deterministic pre-check fired, the halt
    # is materially unsupported. Downgrade to `surface_to_drafter` (NEVER
    # `clean`) - the model still emitted a halt signal, so drafter/operator
    # arbitration is the right backstop. This is structurally narrow:
    # any active finding (model or pre-check) keeps the halt.
    if (
        final_disposition == "halt"
        and len(model_findings_active) == 0
        and len(extra_findings) == 0
    ):
        final_disposition = "surface_to_drafter"
        unsupported_halt_downgrade = True

    latency_ms = int((time.monotonic() - start) * 1000)
    completed_utc = datetime.now(timezone.utc).isoformat()
    _emit_span(
        disposition=final_disposition,
        confidence=validated["confidence"],
        findings_count=len(final_findings),
        latency_ms=latency_ms,
        floor_locked=floor_decision["confidence_floor_locked"],
        suppressed_count=len(suppressed_findings),
        filter_eligible=filter_outcome["filter_eligible"],
    )
    # Materiality counter - one increment per finding so severity rollups
    # are honest (heavy audits don't disappear into a single bump).
    if final_findings:
        try:
            from .. import materiality as _materiality
            for finding in final_findings:
                _materiality.record_caught_by_llama(
                    severity=str(finding.get("severity", "info"))
                )
        except Exception:
            # Materiality is observability - never block the audit return.
            pass
    return {
        "disposition": final_disposition,
        "confidence": validated["confidence"],
        "findings": final_findings,
        "suppressed_findings": suppressed_findings,
        "finding_filter": {
            "filter_enabled": filter_outcome["filter_enabled"],
            "filter_eligible": filter_outcome["filter_eligible"],
            "registered_id_count": filter_outcome["registered_id_count"],
            "model_findings_count": len(validated["findings"]),
            "active_findings_count": len(model_findings_active),
            "suppressed_count": len(suppressed_findings),
        },
        "evidence_traces": validated["evidence_traces"],
        "structural_pre_checks": pre_checks,
        "confidence_floor": floor_decision["confidence_floor"],
        "confidence_floor_locked": floor_decision["confidence_floor_locked"],
        "structural_override_to_surface": structural_override,
        "unsupported_halt_downgrade": unsupported_halt_downgrade,
        "auditor_model_id": _model(),
        "rag_enrichment": rag_summary,
        "audit_started_utc": started_utc,
        "audit_completed_utc": completed_utc,
        "latency_ms": latency_ms,
    }
