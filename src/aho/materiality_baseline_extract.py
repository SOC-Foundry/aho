"""W4 D5 — pre-base-container materiality baseline extractor.

Reads sealed 0.2.16 audit archives (`artifacts/iterations/0.2.16/audit/W*.json`)
and reconstructs a normalized materiality state in the four-bucket protocol
shape so it can be compared side-by-side with the 0.2.17 (base-container)
post-state.

The 0.2.16 audit archives use a different schema than the 0.2.17 archives:
findings are a dict keyed by finding ID with values {severity, description},
not a list-of-dicts. This module flattens both shapes to the canonical
``materiality_state`` dict used by ``aho.claw3d.lego.materiality_surfaces``.

Buckets we can populate from 0.2.16 archives:

  - **caught_by_auditor** (mapped to the dashboard's ``caught_by_llama``
    bucket label as the protocol-canonical "auditor caught it" count) —
    sum of all findings across audited workstreams, grouped by severity.
  - **carry_forward_resolution** — best-effort count from the iteration's
    `carry-forwards-*.md` file when present. Counted as the number of
    entries marked "closed" or "resolved" in the file body. Falls
    through to 0 when the file is unparseable, which is honest data
    rather than a fabricated number.

Buckets we cannot populate from 0.2.16:

  - **caught_by_drafter** — 0.2.16 archives don't separately record
    drafter-vs-auditor catch attribution. Stays 0; comparison surface
    notes the limitation.
  - **escaped** — 0.2.16 didn't have the escaped counter wired. Stays 0.

Honesty rule: if a counter cannot be reconstructed, it stays 0 and the
comparison surface explicitly annotates which fields are reconstructed
vs unknown. Halt-and-surface fires (D5 acceptance gate) when extraction
produces obviously-wrong numbers — the test suite verifies the math
against the actual archive contents.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SEVERITIES = ("info", "important", "critical")


SEVERITY_SYNONYMS = {
    "low": "info",
    "minor": "info",
    "medium": "important",
    "moderate": "important",
    "high": "critical",
    "severe": "critical",
    "blocker": "critical",
}


class BaselineExtractError(RuntimeError):
    """Reconstruction failed in a way that should halt-and-surface."""


def _normalize_severity(raw: Any) -> str:
    if not isinstance(raw, str):
        return "info"
    cleaned = raw.strip().lower()
    if cleaned in SEVERITIES:
        return cleaned
    return SEVERITY_SYNONYMS.get(cleaned, "info")


def _flatten_findings(findings_obj: Any) -> List[Dict[str, str]]:
    """Coerce either the 0.2.16 dict-keyed shape or the 0.2.17 list-of-dicts
    shape into a list of {id, severity, description}."""
    out: List[Dict[str, str]] = []
    if isinstance(findings_obj, dict):
        for fid, body in findings_obj.items():
            if not isinstance(body, dict):
                continue
            out.append({
                "id": str(fid),
                "severity": _normalize_severity(body.get("severity")),
                "description": str(body.get("description") or "").strip(),
            })
    elif isinstance(findings_obj, list):
        for entry in findings_obj:
            if not isinstance(entry, dict):
                continue
            out.append({
                "id": str(entry.get("id") or ""),
                "severity": _normalize_severity(entry.get("severity")),
                "description": str(entry.get("description") or "").strip(),
            })
    return out


def _empty_bucket() -> Dict[str, Any]:
    return {
        "count": 0,
        "by_severity": {sev: 0 for sev in SEVERITIES},
        "last_seen_utc": None,
    }


def extract_caught_by_auditor(
    audit_dir: Path,
) -> Tuple[Dict[str, Any], List[str]]:
    """Walk audit/W*.json under ``audit_dir`` and sum findings into the
    caught_by_auditor bucket. Returns (bucket_dict, sources_list).

    The sources list is the ordered set of audit archives consumed —
    surfaced in the comparison surface for falsifiability.
    """
    bucket = _empty_bucket()
    sources: List[str] = []
    if not audit_dir.is_dir():
        return bucket, sources
    for path in sorted(audit_dir.glob("W*.json")):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            raise BaselineExtractError(
                f"failed to parse audit archive {path}: {exc}"
            ) from exc
        findings = _flatten_findings(payload.get("findings"))
        if not findings:
            sources.append(str(path))
            continue
        for f in findings:
            bucket["count"] += 1
            bucket["by_severity"][f["severity"]] += 1
        sources.append(str(path))
    return bucket, sources


_CLOSED_PATTERN = re.compile(
    r"^\s*-\s+\*\*?(?:F-[\w\d.\-]+|AF\d+|AF-\d+\.\d+\.\d+-W\d+-\d+)\b[^\n]*\b(closed|resolved)\b",
    re.IGNORECASE | re.MULTILINE,
)


def extract_carry_forward_resolution_count(
    carry_forwards_path: Optional[Path],
) -> int:
    """Best-effort count of "closed" / "resolved" carry-forward entries
    in the iteration's carry-forwards markdown file. Returns 0 when the
    file is missing — caller surfaces that explicitly in the comparison.
    """
    if carry_forwards_path is None or not carry_forwards_path.exists():
        return 0
    try:
        text = carry_forwards_path.read_text()
    except OSError:
        return 0
    return len(_CLOSED_PATTERN.findall(text))


def reconstruct_baseline(
    iteration_root: Path,
    *,
    iteration_label: str,
) -> Dict[str, Any]:
    """Reconstruct a four-bucket materiality state from the sealed
    archives under ``iteration_root``.

    Returns a dict matching the ``normalize_materiality_state`` contract,
    plus a top-level ``baseline_provenance`` dict listing the audit files
    consumed and which buckets are reconstructed vs unknown.
    """
    if not iteration_root.is_dir():
        raise BaselineExtractError(
            f"iteration root not found: {iteration_root}"
        )

    audit_dir = iteration_root / "audit"
    caught_bucket, audit_sources = extract_caught_by_auditor(audit_dir)

    carry_forwards_path: Optional[Path] = None
    for candidate in (
        iteration_root / f"carry-forwards-{iteration_label}.md",
        iteration_root / "carry-forwards.md",
    ):
        if candidate.exists():
            carry_forwards_path = candidate
            break
    cf_count = extract_carry_forward_resolution_count(carry_forwards_path)

    cf_bucket = _empty_bucket()
    cf_bucket["count"] = cf_count
    # carry-forward resolution is severity-agnostic by design; lump under
    # "info" so the by_severity dict stays a complete contract.
    cf_bucket["by_severity"]["info"] = cf_count

    baseline = {
        "iteration": iteration_label,
        "workstream": "(rolled-up across all workstreams)",
        "buckets": {
            "caught_by_llama": caught_bucket,  # caught_by_auditor mapped here
            "caught_by_drafter": _empty_bucket(),
            "escaped": _empty_bucket(),
            "carry_forward_resolution": cf_bucket,
        },
        "baseline_provenance": {
            "iteration_root": str(iteration_root),
            "audit_sources": audit_sources,
            "carry_forwards_source": (
                str(carry_forwards_path) if carry_forwards_path else None
            ),
            "buckets_reconstructed": ["caught_by_llama", "carry_forward_resolution"],
            "buckets_unknown": ["caught_by_drafter", "escaped"],
            "notes": [
                "0.2.16 audit archives don't separately record drafter-vs-"
                "auditor catch attribution; caught_by_drafter stays 0.",
                "0.2.16 didn't wire the escaped counter; escaped stays 0.",
                "caught_by_llama label maps the protocol bucket; in 0.2.16"
                " the auditor was Gemini, not llama. Compare-with-care.",
            ],
        },
    }
    return baseline


def reconstruct_0_2_16_baseline(repo_root: Path) -> Dict[str, Any]:
    """Convenience wrapper for the 0.2.16 baseline (the comparison
    surface's primary input)."""
    iteration_root = repo_root / "artifacts" / "iterations" / "0.2.16"
    return reconstruct_baseline(iteration_root, iteration_label="0.2.16")


__all__ = [
    "BaselineExtractError",
    "extract_caught_by_auditor",
    "extract_carry_forward_resolution_count",
    "reconstruct_0_2_16_baseline",
    "reconstruct_baseline",
]
