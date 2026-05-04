"""W3 D4 — replay W0 / W1 / W2 audits with RAG-enriched auditor.

Re-runs the audit primitive against the same sealed acceptance archives
W2 D9/D10/D11 audited, but with `rag_enrichment=True`. Output paths use
the `-rag` suffix so the W2 sealed replay artifacts remain untouched:

- audit/replay/W0-llama-rag.json
- audit/replay/W1-llama-rag.json
- audit/replay/W2-self-audit-rag.json
- audit/replay/comparison-rag-vs-non-rag.json

The comparison artifact is a single document keyed by source workstream.
For each, it records:
- RAG vs non-RAG disposition (match / mismatch).
- Finding count delta.
- Novel findings (RAG-only or non-RAG-only descriptions).
- False-positive resolution: did the RAG version stop flagging the
  reference IDs that the non-RAG version flagged as 'not real',
  'placeholder', etc.?

Halt-and-surface conditions:
- A reproducible RAG retrieval failure (RefLookupError) raises and aborts
  the run before writing partial artifacts.
- A substantive cross-audit disagreement (RAG says clean while non-RAG
  found a Pillar 11 / secrets / git-op finding) is recorded and surfaced
  via exit code 2.

CLI:
    python W3_audit_replay_rag.py            # run all three
    python W3_audit_replay_rag.py --only W0  # run a single replay
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from aho.audit_disposition_emitter import (  # noqa: E402
    SCHEMA_VERSION,
    render_body_md,
    sha256_of_text,
    validate_header,
)
from aho.council.audit import (  # noqa: E402
    CouncilAuditMalformedError,
    audit as council_audit,
)

ITER_ROOT = ROOT / "artifacts" / "iterations"
TARGET_ITERATION = "0.2.17"
REPLAY_DIR = ITER_ROOT / TARGET_ITERATION / "audit" / "replay"

# Output basename per source workstream (audit_kind, basename).
# W2 is `self`-kind audit, so the W2 archive is the W2 self-audit input.
RAG_TARGETS: Dict[str, Dict[str, Any]] = {
    "W0": {"audit_kind": "replay",  "basename": "W0-llama-rag.json"},
    "W1": {"audit_kind": "replay",  "basename": "W1-llama-rag.json"},
    "W2": {"audit_kind": "self",    "basename": "W2-self-audit-rag.json"},
}

NON_RAG_PATHS: Dict[str, Path] = {
    "W0": REPLAY_DIR / "W0-llama.json",
    "W1": REPLAY_DIR / "W1-llama.json",
    "W2": ITER_ROOT / TARGET_ITERATION / "audit" / "W2.json",
}

# Phrases that signal the auditor flagged an ID as fake — the precise
# false-positive shape F-0.2.17-W2-006 names. If a non-RAG finding's
# description matches and the corresponding RAG run did NOT produce the
# same shape, that is a closed false positive.
FAKE_ID_PHRASES = (
    "does not look real",
    "does not corroborate",
    "not corroborated",
    "looks placeholder",
    "looks like placeholder",
    "looks fake",
    "appears placeholder",
    "is placeholder",
    "is not real",
    "id is fake",
    "id does not look real",
)

SUBSTANTIVE_KEYWORDS = (
    "pillar 11",
    "pillar11",
    "git commit",
    "git push",
    "secrets",
    "credential",
    "rubber-stamp",
    "rubber stamp",
    "bypass",
)

ANCHOR_RE = re.compile(
    r"\b(?:AF\d+|AF-[0-9.]+|F-[0-9.\-A-Za-z]+|B[0-9.]+|D\d+|W\d+|G\d+)\b"
)


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------

def gather_target(workstream: str) -> Tuple[str, List[Path]]:
    iter_dir = ITER_ROOT / TARGET_ITERATION
    paths: List[Path] = [iter_dir / "acceptance" / f"{workstream}.json"]
    if workstream == "W0":
        paths.append(iter_dir / "acceptance" / "W0-amendment-b2-3.json")
    parts: List[str] = []
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"replay target missing: {p}")
        parts.append(f"=== {p.name} ===\n{p.read_text(encoding='utf-8')}\n")
    return "\n".join(parts), paths


def _emit_rag_disposition(
    *,
    audit_dict: Dict[str, Any],
    workstream: str,
    audit_kind: str,
    basename: str,
    target_text: str,
) -> Path:
    """Write the RAG-enriched audit disposition to its `-rag.json` path,
    mirroring the emitter's two-part document shape but extending the
    header with `rag_enrichment` so consumers can tell the runs apart.
    """
    out_path = REPLAY_DIR / basename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    findings: List[Dict[str, Any]] = audit_dict.get("findings") or []
    evidence: List[str] = audit_dict.get("evidence_traces") or []
    target_sha = sha256_of_text(target_text)
    header: Dict[str, Any] = {
        "disposition": audit_dict["disposition"],
        "confidence": float(audit_dict["confidence"]),
        "auditor_model_id": audit_dict["auditor_model_id"],
        "audit_started_utc": audit_dict["audit_started_utc"],
        "audit_completed_utc": audit_dict["audit_completed_utc"],
        "target_artifact_sha256": target_sha,
        "findings_count": len(findings),
        "evidence_trace_count": len(evidence),
        "audit_kind": audit_kind,
        "iteration": TARGET_ITERATION,
        "workstream": workstream,
        "schema_version": SCHEMA_VERSION,
    }
    validate_header(header)
    body_md = render_body_md(
        audit=audit_dict,
        target_path=None,
        iteration=TARGET_ITERATION,
        workstream=workstream,
        audit_kind=audit_kind,
    )
    document = {
        **header,
        "findings": findings,
        "evidence_traces": evidence,
        "structural_pre_checks": audit_dict.get("structural_pre_checks"),
        "confidence_floor": audit_dict.get("confidence_floor"),
        "confidence_floor_locked": audit_dict.get("confidence_floor_locked", False),
        "structural_override_to_surface": audit_dict.get(
            "structural_override_to_surface", False
        ),
        "latency_ms": audit_dict.get("latency_ms"),
        "rag_enrichment": audit_dict.get("rag_enrichment"),
        "body_md": body_md,
    }
    out_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return out_path


def run_rag_audit(workstream: str) -> Dict[str, Any]:
    config = RAG_TARGETS[workstream]
    artifact, source_paths = gather_target(workstream)
    print(
        f"[{workstream}] running RAG-enriched audit "
        f"(artifact size: {len(artifact)} chars)…",
        flush=True,
    )
    last_exc = None
    audit_dict: Optional[Dict[str, Any]] = None
    for attempt in range(1, 4):
        try:
            audit_dict = council_audit(artifact, rag_enrichment=True)
            break
        except CouncilAuditMalformedError as exc:
            last_exc = exc
            print(
                f"[{workstream}] attempt {attempt}: malformed llama output "
                f"({exc}); retrying",
                flush=True,
            )
    if audit_dict is None:
        raise RuntimeError(
            f"llama RAG audit malformed after 3 attempts: {last_exc}"
        )
    print(
        f"[{workstream}] disposition: {audit_dict['disposition']} "
        f"confidence={audit_dict['confidence']:.2f} "
        f"findings={len(audit_dict['findings'])} "
        f"refs={audit_dict['rag_enrichment']['detected_count']} "
        f"registered={audit_dict['rag_enrichment']['registered_count']} "
        f"unverified={audit_dict['rag_enrichment']['unverified_count']} "
        f"latency={audit_dict['latency_ms']}ms",
        flush=True,
    )
    out_path = _emit_rag_disposition(
        audit_dict=audit_dict,
        workstream=workstream,
        audit_kind=config["audit_kind"],
        basename=config["basename"],
        target_text=artifact,
    )
    print(f"[{workstream}] written → {out_path}", flush=True)
    return {
        "audit": audit_dict,
        "rag_audit_path": str(out_path),
        "source_artifact_paths": [str(p) for p in source_paths],
    }


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower())


def _findings_list(audit_or_replay: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = audit_or_replay.get("findings") or []
    return [
        {
            "id": str(f.get("id", f"AF-{i}")),
            "severity": str(f.get("severity") or "info").lower(),
            "description": str(f.get("description") or "").strip(),
        }
        for i, f in enumerate(findings)
    ]


def _is_fake_id_finding(description: str) -> bool:
    norm = _normalise(description)
    return any(p in norm for p in FAKE_ID_PHRASES)


def _topical_match(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    """Two findings overlap if they share an anchor ID, OR they share
    >=2 distinctive non-stopword tokens.
    """
    a_anchors = set(ANCHOR_RE.findall(a["description"]))
    b_anchors = set(ANCHOR_RE.findall(b["description"]))
    if a_anchors & b_anchors:
        return True
    stopwords = {
        "that", "this", "with", "from", "have", "been", "into", "more",
        "than", "such", "they", "will", "there", "these", "their",
        "what", "when", "would", "could", "should", "must", "artifact",
        "executor", "auditor", "finding", "claim", "section",
    }
    a_toks = {t for t in _normalise(a["description"]).split() if len(t) >= 4} - stopwords
    b_toks = {t for t in _normalise(b["description"]).split() if len(t) >= 4} - stopwords
    return len(a_toks & b_toks) >= 2


def compare_rag_vs_non_rag(
    workstream: str,
    rag_audit: Dict[str, Any],
    non_rag_path: Path,
) -> Dict[str, Any]:
    if not non_rag_path.exists():
        raise FileNotFoundError(f"non-RAG audit missing: {non_rag_path}")
    non_rag_doc = json.loads(non_rag_path.read_text(encoding="utf-8"))

    rag_disp = rag_audit["disposition"]
    non_rag_disp = non_rag_doc.get("disposition")
    rag_findings = _findings_list(rag_audit)
    non_rag_findings = _findings_list(non_rag_doc)

    # False-positive resolution. For each non-RAG finding that matches the
    # fake-id phrase template, check whether any RAG finding produces the
    # same shape (same anchor ID + fake-id phrase). If not, the RAG run
    # closed that false positive.
    closed_false_positives: List[Dict[str, Any]] = []
    open_false_positives: List[Dict[str, Any]] = []
    for nf in non_rag_findings:
        if not _is_fake_id_finding(nf["description"]):
            continue
        anchor_ids = set(ANCHOR_RE.findall(nf["description"]))
        still_flagged = any(
            _is_fake_id_finding(rf["description"])
            and (set(ANCHOR_RE.findall(rf["description"])) & anchor_ids)
            for rf in rag_findings
        )
        record = {
            "non_rag_finding_id": nf["id"],
            "anchor_ids": sorted(anchor_ids),
            "non_rag_description": nf["description"][:300],
        }
        if still_flagged:
            open_false_positives.append(record)
        else:
            closed_false_positives.append(record)

    # Novel findings (RAG-only or non-RAG-only).
    rag_only = [
        rf for rf in rag_findings
        if not any(_topical_match(rf, nf) for nf in non_rag_findings)
    ]
    non_rag_only = [
        nf for nf in non_rag_findings
        if not any(_topical_match(nf, rf) for rf in rag_findings)
    ]

    # Substantive disagreement detection — the explicit halt condition.
    # The shape we care about: RAG version says 'clean' but non-RAG
    # version surfaced a Pillar 11 / secrets / git-op finding. We also
    # treat the inverse (RAG surfaces a substantive finding non-RAG
    # missed) as substantive — either direction warrants drafter review.
    def _has_substantive(findings: List[Dict[str, Any]]) -> bool:
        return any(
            any(kw in _normalise(f["description"]) for kw in SUBSTANTIVE_KEYWORDS)
            for f in findings
        )

    rag_clean_non_rag_substantive = (
        rag_disp == "clean" and _has_substantive(non_rag_findings)
    )
    rag_substantive_only_finding = bool(
        [f for f in rag_only
         if any(kw in _normalise(f["description"]) for kw in SUBSTANTIVE_KEYWORDS)]
    )
    non_rag_substantive_only_finding = bool(
        [f for f in non_rag_only
         if any(kw in _normalise(f["description"]) for kw in SUBSTANTIVE_KEYWORDS)]
    )
    substantively_important = (
        rag_clean_non_rag_substantive
        or rag_substantive_only_finding
        or non_rag_substantive_only_finding
    )

    return {
        "source_workstream": workstream,
        "non_rag_audit_path": str(non_rag_path),
        "disposition": {
            "rag": rag_disp,
            "non_rag": non_rag_disp,
            "match": rag_disp == non_rag_disp,
        },
        "finding_counts": {
            "rag": len(rag_findings),
            "non_rag": len(non_rag_findings),
            "delta_rag_minus_non_rag": len(rag_findings) - len(non_rag_findings),
        },
        "false_positive_resolution": {
            "non_rag_fake_id_findings": (
                len(closed_false_positives) + len(open_false_positives)
            ),
            "closed_by_rag": closed_false_positives,
            "still_present_in_rag": open_false_positives,
        },
        "novel_findings": {
            "rag_only": [
                {"id": f["id"], "severity": f["severity"], "description": f["description"][:300]}
                for f in rag_only
            ],
            "non_rag_only": [
                {"id": f["id"], "severity": f["severity"], "description": f["description"][:300]}
                for f in non_rag_only
            ],
        },
        "substantive_keyword_split": {
            "rag_clean_while_non_rag_substantive": rag_clean_non_rag_substantive,
            "rag_only_substantive_findings": rag_substantive_only_finding,
            "non_rag_only_substantive_findings": non_rag_substantive_only_finding,
        },
        "substantively_important_disagreement": substantively_important,
    }


# ---------------------------------------------------------------------------
# Top-level
# ---------------------------------------------------------------------------

def run_all(only: Optional[List[str]] = None) -> Dict[str, Any]:
    targets = list(RAG_TARGETS.keys()) if only is None else only
    per_workstream: Dict[str, Dict[str, Any]] = {}
    comparisons: Dict[str, Dict[str, Any]] = {}
    for ws in targets:
        result = run_rag_audit(ws)
        per_workstream[ws] = result
        comparisons[ws] = compare_rag_vs_non_rag(
            workstream=ws,
            rag_audit=result["audit"],
            non_rag_path=NON_RAG_PATHS[ws],
        )

    overall_substantive = any(
        c.get("substantively_important_disagreement") for c in comparisons.values()
    )
    overall_false_positives_closed = sum(
        len(c["false_positive_resolution"]["closed_by_rag"])
        for c in comparisons.values()
    )
    overall_false_positives_open = sum(
        len(c["false_positive_resolution"]["still_present_in_rag"])
        for c in comparisons.values()
    )
    f_w2_006_resolved = (
        overall_false_positives_closed > 0
        and overall_false_positives_open == 0
    )

    summary = {
        "iteration": TARGET_ITERATION,
        "comparison_kind": "rag_vs_non_rag_replay",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "workstreams": comparisons,
        "rollup": {
            "false_positives_closed_by_rag": overall_false_positives_closed,
            "false_positives_still_present_in_rag": overall_false_positives_open,
            "f_0_2_17_w2_006_resolution_claim": f_w2_006_resolved,
            "substantively_important_disagreement_anywhere": overall_substantive,
        },
        "per_workstream_artifact_paths": {
            ws: {
                "rag_audit_path": result["rag_audit_path"],
                "non_rag_audit_path": str(NON_RAG_PATHS[ws]),
                "source_artifact_paths": result["source_artifact_paths"],
            }
            for ws, result in per_workstream.items()
        },
    }

    summary_path = REPLAY_DIR / "comparison-rag-vs-non-rag.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"summary written → {summary_path}", flush=True)
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(RAG_TARGETS.keys()),
        default=None,
    )
    args = parser.parse_args(argv)
    summary = run_all(only=args.only)
    if summary["rollup"]["substantively_important_disagreement_anywhere"]:
        print(
            "HALT: substantively important RAG-vs-non-RAG disagreement detected",
            flush=True,
        )
        return 2
    print(
        "OK: replays complete; "
        f"false_positives_closed={summary['rollup']['false_positives_closed_by_rag']} "
        f"false_positives_still_present={summary['rollup']['false_positives_still_present_in_rag']} "
        f"F-0.2.17-W2-006_resolved={summary['rollup']['f_0_2_17_w2_006_resolution_claim']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
