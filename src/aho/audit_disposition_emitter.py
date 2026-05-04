"""audit_disposition_emitter — write council audit dispositions to disk.

Produces a single .json file with two logical parts:

1. Machine-parseable header — top-level fields covering disposition,
   confidence, target sha, timestamps, finding counts. Schema-validatable.
2. Human-readable body — `body_md` field with per-finding markdown
   sections written for drafter (Claude web) consumption on next planning
   turn. No raw JSON dumps embedded in prose.

Output paths follow the iteration layout:
- Top-level workstream audits: artifacts/iterations/{iter}/audit/{ws}.json
- Replay audits (D9, D10):     artifacts/iterations/{iter}/audit/replay/{source}-llama.json

Pillar 11: this primitive only writes to artifacts/. It never invokes git.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.audit_disposition_emitter")
except ImportError:  # pragma: no cover
    _otel_trace = None
    _tracer = None

SCHEMA_VERSION = "audit-v2-llama-seat"


class AuditEmitterError(RuntimeError):
    pass


class AuditEmitterInputError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

REQUIRED_HEADER_FIELDS = (
    "disposition",
    "confidence",
    "auditor_model_id",
    "audit_started_utc",
    "audit_completed_utc",
    "target_artifact_sha256",
    "findings_count",
    "evidence_trace_count",
    "audit_kind",
    "iteration",
    "workstream",
    "schema_version",
)


def validate_header(header: Dict[str, Any]) -> None:
    missing = [f for f in REQUIRED_HEADER_FIELDS if f not in header]
    if missing:
        raise AuditEmitterError(
            f"audit header missing required fields: {missing}"
        )
    if header["disposition"] not in ("clean", "halt", "surface_to_drafter"):
        raise AuditEmitterError(
            f"audit header disposition {header['disposition']!r} invalid"
        )
    if not (0.0 <= float(header["confidence"]) <= 1.0):
        raise AuditEmitterError(
            f"audit header confidence {header['confidence']} outside [0,1]"
        )
    if header["audit_kind"] not in ("top_level", "replay", "self"):
        raise AuditEmitterError(
            f"audit header audit_kind {header['audit_kind']!r} invalid"
        )


# ---------------------------------------------------------------------------
# Body rendering
# ---------------------------------------------------------------------------

def _render_finding_section(idx: int, finding: Dict[str, Any]) -> str:
    fid = finding.get("id", f"AF-{idx}")
    severity = finding.get("severity", "info")
    description = (finding.get("description") or "").strip()
    return (
        f"### Finding {fid} ({severity})\n\n"
        f"{description}\n"
    )


def _render_evidence_section(traces: List[str]) -> str:
    if not traces:
        return "_No evidence traces returned by auditor._\n"
    lines = ["The auditor cited the following evidence:\n"]
    for t in traces:
        cleaned = (t or "").strip()
        if not cleaned:
            continue
        # Single-line bulleted quote — quote-safe even if the trace itself
        # contains JSON, since the body never embeds raw JSON dumps.
        cleaned = cleaned.replace("\n", " ")
        if len(cleaned) > 400:
            cleaned = cleaned[:400] + "…"
        lines.append(f"- “{cleaned}”\n")
    return "".join(lines)


def render_body_md(
    *,
    audit: Dict[str, Any],
    target_path: Optional[str],
    iteration: str,
    workstream: str,
    audit_kind: str,
) -> str:
    findings: List[Dict[str, Any]] = audit.get("findings") or []
    traces: List[str] = audit.get("evidence_traces") or []
    pre_checks: Dict[str, Any] = audit.get("structural_pre_checks") or {}
    parts: List[str] = []
    title_kind = {
        "top_level": "Workstream Audit",
        "replay": "Audit Replay",
        "self": "Self-Audit",
    }.get(audit_kind, audit_kind)
    parts.append(f"# {title_kind} — {iteration} {workstream}\n")
    parts.append(f"**Disposition:** {audit['disposition']}\n")
    parts.append(f"**Confidence:** {audit['confidence']}\n")
    parts.append(f"**Auditor:** {audit['auditor_model_id']}\n")
    if target_path:
        parts.append(f"**Target:** `{target_path}`\n")
    if audit.get("confidence_floor_locked"):
        parts.append(
            f"\n> Confidence floor lock activated "
            f"(floor={audit.get('confidence_floor', 0.85)}, "
            f"original_disposition={audit.get('original_disposition', 'clean')}). "
            f"Disposition forcibly surfaced to drafter.\n"
        )
    if audit.get("structural_override_to_surface"):
        parts.append(
            "\n> Structural pre-check override fired (G081 banned phrase or "
            "Pillar 11 git-op reference present). Disposition forcibly "
            "surfaced to drafter regardless of model verdict.\n"
        )
    if pre_checks:
        parts.append("\n## Structural pre-checks\n\n")
        for k in (
            "g081_banned_phrases",
            "git_ops_referenced",
            "three_octet_versioning_present",
        ):
            if k in pre_checks:
                parts.append(f"- {k}: **{pre_checks[k]}**\n")
        hits = pre_checks.get("g081_banned_phrases_hits") or []
        if hits:
            parts.append(f"- g081 hits: {', '.join(repr(h) for h in hits)}\n")
        git_hits = pre_checks.get("git_ops_hits") or []
        if git_hits:
            parts.append(
                f"- git-op references: {', '.join(repr(h) for h in git_hits)}\n"
            )
    if findings:
        parts.append("\n## Findings\n\n")
        for idx, f in enumerate(findings, start=1):
            parts.append(_render_finding_section(idx, f))
            parts.append("\n")
    else:
        parts.append("\n## Findings\n\n_No findings._\n")
    parts.append("\n## Evidence traces\n\n")
    parts.append(_render_evidence_section(traces))
    return "".join(parts)


# ---------------------------------------------------------------------------
# SHA + path resolution
# ---------------------------------------------------------------------------

def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def output_path_for(
    *,
    iteration_root: Path,
    iteration: str,
    workstream: str,
    audit_kind: str,
    replay_source: Optional[str] = None,
) -> Path:
    iter_dir = iteration_root / iteration
    if audit_kind == "replay":
        if not replay_source:
            raise AuditEmitterInputError("audit_kind=replay requires replay_source")
        return iter_dir / "audit" / "replay" / f"{replay_source}-llama.json"
    return iter_dir / "audit" / f"{workstream}.json"


# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------

def _emit_span(
    *,
    output_path: Path,
    audit_kind: str,
    disposition: str,
    findings_count: int,
) -> None:
    if _tracer is None:
        return
    with _tracer.start_as_current_span("aho.audit_disposition_emitter") as span:
        try:
            span.set_attribute("aho.audit.output_path", str(output_path))
            span.set_attribute("aho.audit.kind", audit_kind)
            span.set_attribute("aho.audit.disposition", disposition)
            span.set_attribute("aho.audit.findings_count", findings_count)
            # Materiality bucket — emitter is the count-emission point for
            # llama-caught mismatches so D12 doesn't double-count.
            span.set_attribute(
                "aho.materiality.bucket",
                "claim_vs_artifact_mismatch_caught_by_llama"
                if findings_count > 0
                else "claim_vs_artifact_mismatch_no_finding",
            )
        except Exception:
            pass


def emit_disposition(
    *,
    audit: Dict[str, Any],
    iteration: str,
    workstream: str,
    audit_kind: str = "top_level",
    target_artifact_path: Optional[str | Path] = None,
    target_artifact_text: Optional[str] = None,
    iteration_root: Optional[Path] = None,
    replay_source: Optional[str] = None,
) -> Dict[str, Any]:
    """Write the audit disposition to disk in the canonical two-part shape.

    Either `target_artifact_path` (file) or `target_artifact_text` (raw text
    of an in-memory artifact like a self-audit target) must be provided so
    the emitter can compute target_artifact_sha256.

    Returns dict with `output_path`, `header`, and `sha256` of the emitted file.
    """
    if not isinstance(audit, dict):
        raise AuditEmitterInputError(
            f"audit must be dict, got {type(audit).__name__}"
        )
    for k in ("disposition", "confidence", "findings", "evidence_traces", "auditor_model_id"):
        if k not in audit:
            raise AuditEmitterInputError(
                f"audit missing required field: {k!r}"
            )
    if audit_kind not in ("top_level", "replay", "self"):
        raise AuditEmitterInputError(
            f"audit_kind must be top_level|replay|self, got {audit_kind!r}"
        )
    if not iteration or not workstream:
        raise AuditEmitterInputError("iteration and workstream both required")

    if target_artifact_text is None and target_artifact_path is None:
        raise AuditEmitterInputError(
            "either target_artifact_text or target_artifact_path must be provided"
        )
    target_path_str: Optional[str] = None
    if target_artifact_path is not None:
        tap = Path(target_artifact_path)
        if not tap.exists():
            raise AuditEmitterInputError(f"target_artifact_path does not exist: {tap}")
        target_sha = sha256_of_path(tap)
        target_path_str = str(tap)
    else:
        target_sha = sha256_of_text(target_artifact_text or "")

    if iteration_root is None:
        from aho.paths import get_iterations_dir
        iteration_root = get_iterations_dir()

    out_path = output_path_for(
        iteration_root=iteration_root,
        iteration=iteration,
        workstream=workstream,
        audit_kind=audit_kind,
        replay_source=replay_source,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    findings: List[Dict[str, Any]] = audit.get("findings") or []
    evidence: List[str] = audit.get("evidence_traces") or []

    header: Dict[str, Any] = {
        "disposition": audit["disposition"],
        "confidence": float(audit["confidence"]),
        "auditor_model_id": audit["auditor_model_id"],
        "audit_started_utc": audit.get("audit_started_utc")
            or datetime.now(timezone.utc).isoformat(),
        "audit_completed_utc": audit.get("audit_completed_utc")
            or datetime.now(timezone.utc).isoformat(),
        "target_artifact_sha256": target_sha,
        "findings_count": len(findings),
        "evidence_trace_count": len(evidence),
        "audit_kind": audit_kind,
        "iteration": iteration,
        "workstream": workstream,
        "schema_version": SCHEMA_VERSION,
    }
    validate_header(header)

    body_md = render_body_md(
        audit=audit,
        target_path=target_path_str,
        iteration=iteration,
        workstream=workstream,
        audit_kind=audit_kind,
    )

    document = {
        **header,
        "findings": findings,
        "evidence_traces": evidence,
        "structural_pre_checks": audit.get("structural_pre_checks"),
        "confidence_floor": audit.get("confidence_floor"),
        "confidence_floor_locked": audit.get("confidence_floor_locked", False),
        "structural_override_to_surface": audit.get(
            "structural_override_to_surface", False
        ),
        "latency_ms": audit.get("latency_ms"),
        "body_md": body_md,
    }
    # W3: when the audit ran with RAG enrichment, surface the enrichment
    # summary alongside the disposition so downstream consumers can tell
    # RAG-enriched runs apart from non-RAG (W2-shape) runs.
    if audit.get("rag_enrichment") is not None:
        document["rag_enrichment"] = audit["rag_enrichment"]
    # W4 D1: surface the deterministic post-hoc filter outcome alongside
    # the disposition. `suppressed_findings` is auditable / falsifiable —
    # drafter or downstream review can inspect what was suppressed and why.
    if audit.get("suppressed_findings") is not None:
        document["suppressed_findings"] = audit["suppressed_findings"]
    if audit.get("finding_filter") is not None:
        document["finding_filter"] = audit["finding_filter"]

    serialized = json.dumps(document, indent=2)
    out_path.write_text(serialized + "\n", encoding="utf-8")
    output_sha = sha256_of_text(serialized + "\n")

    _emit_span(
        output_path=out_path,
        audit_kind=audit_kind,
        disposition=audit["disposition"],
        findings_count=len(findings),
    )
    return {
        "output_path": str(out_path),
        "header": header,
        "sha256": output_sha,
    }
