"""W2 D9 / D10 - audit replay against sealed W0 / W1 archives.

Llama3.2 audits the sealed acceptance archive(s) independently. Result is
compared structurally to Gemini's sealed audit.

Output paths (per source workstream `Wn`):
- artifacts/iterations/0.2.17/audit/replay/Wn-llama.json
- artifacts/iterations/0.2.17/audit/replay/Wn-comparison.json

CLI:
    python W2_audit_replay.py --workstream W0
    python W2_audit_replay.py --workstream W1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from aho.audit_disposition_emitter import emit_disposition  # noqa: E402
from aho.council.audit import audit as council_audit  # noqa: E402

ITER_ROOT = ROOT / "artifacts" / "iterations"
TARGET_ITERATION = "0.2.17"


# ---------------------------------------------------------------------------
# Structural comparison
# ---------------------------------------------------------------------------

# Map Gemini's verdict vocabulary to llama's structurally for agreement check.
GEMINI_TO_LLAMA_DISPOSITION: Dict[str, str] = {
    "pass": "clean",
    "pass_with_findings": "surface_to_drafter",
    "fail": "halt",
}

LLAMA_TO_GEMINI_DISPOSITION: Dict[str, str] = {
    "clean": "pass",
    "surface_to_drafter": "pass_with_findings",
    "halt": "fail",
}

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


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def _gemini_findings(gemini_audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = gemini_audit.get("findings") or {}
    if isinstance(findings, dict):
        return [
            {
                "id": fid,
                "severity": (info.get("severity") or "info").lower(),
                "description": (info.get("description") or info.get("summary") or info.get("title") or "").strip(),
            }
            for fid, info in findings.items()
        ]
    if isinstance(findings, list):
        return [
            {
                "id": str(f.get("id", f"AF-{i}")),
                "severity": str(f.get("severity") or "info").lower(),
                "description": str(f.get("description") or "").strip(),
            }
            for i, f in enumerate(findings)
        ]
    return []


def _llama_findings(llama_disposition: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "id": str(f.get("id", f"AF-{i}")),
            "severity": str(f.get("severity") or "info").lower(),
            "description": str(f.get("description") or "").strip(),
        }
        for i, f in enumerate(llama_disposition.get("findings") or [])
    ]


def _is_substantive_disagreement(text_a: str, text_b: str) -> bool:
    """A disagreement is substantively important if either side cites a
    Pillar 11 / secrets / git-op / rubber-stamp keyword and the other does
    not. Stylistic disagreements (different framing of the same finding)
    don't trip this.
    """
    norm_a = _normalise(text_a)
    norm_b = _normalise(text_b)
    a_hits = {kw for kw in SUBSTANTIVE_KEYWORDS if kw in norm_a}
    b_hits = {kw for kw in SUBSTANTIVE_KEYWORDS if kw in norm_b}
    return bool(a_hits ^ b_hits)


def _topical_overlap_findings(
    g_findings: List[Dict[str, Any]],
    l_findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """For each llama finding, find the gemini finding (if any) that shares
    a recognizable topic anchor (deliverable id, finding-id token, or
    keyword overlap >= 2 distinctive terms). Returns per-llama-finding
    overlap records.
    """
    def tokens(text: str) -> set[str]:
        norm = _normalise(text)
        # Pull alphabetic tokens of length >= 4 - drop common stopwords.
        toks = {t for t in norm.split() if len(t) >= 4}
        return toks - {"that", "this", "with", "from", "have", "been",
                       "into", "more", "than", "such", "they", "will",
                       "there", "these", "their", "what", "when",
                       "would", "could", "should", "must"}

    # Anchor patterns - letter/digit IDs that often co-occur across audits.
    anchor_re = re.compile(r"\b(?:AF\d+|AF-[0-9.]+|F-[0-9.\-A-Za-z]+|B[0-9.]+|D\d+|W\d+|G\d+)\b")
    out: List[Dict[str, Any]] = []
    for lf in l_findings:
        l_anchors = set(anchor_re.findall(lf["description"]))
        l_toks = tokens(lf["description"])
        overlap_partner = None
        overlap_kind = None
        for gf in g_findings:
            g_anchors = set(anchor_re.findall(gf["description"]))
            if l_anchors & g_anchors:
                overlap_partner = gf
                overlap_kind = "anchor_id_match"
                break
            g_toks = tokens(gf["description"])
            shared = l_toks & g_toks
            if len(shared) >= 2:
                overlap_partner = gf
                overlap_kind = f"keyword_overlap[{','.join(sorted(shared)[:4])}]"
                break
        out.append({
            "llama_finding_id": lf["id"],
            "llama_severity": lf["severity"],
            "llama_description": lf["description"][:200],
            "overlap_with_gemini": overlap_partner is not None,
            "overlap_kind": overlap_kind,
            "matched_gemini_finding": (
                {
                    "id": overlap_partner["id"],
                    "severity": overlap_partner["severity"],
                    "description": overlap_partner["description"][:200],
                }
                if overlap_partner
                else None
            ),
        })
    return out


def compare_audits(
    gemini_audit: Dict[str, Any],
    llama_disposition: Dict[str, Any],
) -> Dict[str, Any]:
    gemini_verdict = (gemini_audit.get("audit_result") or "").lower()
    llama_disp = (llama_disposition.get("disposition") or "").lower()
    expected_llama = GEMINI_TO_LLAMA_DISPOSITION.get(gemini_verdict)
    disposition_axis_agreement = expected_llama == llama_disp

    g_findings = _gemini_findings(gemini_audit)
    l_findings = _llama_findings(llama_disposition)

    # Severity-by-count comparison
    severity_count_a = {s: 0 for s in ("info", "important", "critical", "cosmetic")}
    severity_count_b = {s: 0 for s in ("info", "important", "critical", "cosmetic")}
    for f in g_findings:
        severity_count_a[f["severity"]] = severity_count_a.get(f["severity"], 0) + 1
    for f in l_findings:
        severity_count_b[f["severity"]] = severity_count_b.get(f["severity"], 0) + 1

    # Per-llama-finding topical overlap with gemini findings.
    overlaps = _topical_overlap_findings(g_findings, l_findings)
    novel_llama_findings = [o for o in overlaps if not o["overlap_with_gemini"]]

    # Substantive-keyword coverage gap (Pillar 11 / secrets / git-ops).
    # Only fires when there are NOVEL findings - keyword asymmetry on
    # already-overlapping findings is stylistic framing, not substantive.
    g_text_blob = " | ".join(f["description"] for f in g_findings)
    l_text_blob = " | ".join(f["description"] for f in l_findings)
    novel_blob = " | ".join(o["llama_description"] for o in novel_llama_findings)
    substantive_split = bool(novel_llama_findings) and (
        _is_substantive_disagreement(novel_blob, g_text_blob)
    )

    # Substantive-importance heuristic:
    # - Disposition mismatch alone is NOT substantive (severity-inflation
    #   on overlapping findings is stylistic).
    # - Keyword asymmetry on overlapping findings is NOT substantive
    #   (different framing of the same finding).
    # - Substantive iff:
    #   (a) llama produced novel findings that mention Pillar 11 / secrets /
    #       git-ops keywords gemini missed, OR
    #   (b) gemini's verdict was 'fail' but llama returned 'clean'/'pass'
    #       (i.e. llama would erase a sealed failure).
    novel_substantive = any(
        any(kw in _normalise(o["llama_description"]) for kw in SUBSTANTIVE_KEYWORDS)
        for o in novel_llama_findings
    )
    erase_failure = gemini_verdict == "fail" and llama_disp == "clean"

    disagreements: List[Dict[str, Any]] = []
    if not disposition_axis_agreement:
        disagreements.append({
            "axis": "disposition",
            "gemini_value": gemini_verdict,
            "llama_value": llama_disp,
            "expected_llama_for_match": expected_llama,
            "shape": "severity_inflation_or_deflation",
            # Disposition-axis disagreement alone is stylistic per the plan;
            # the substantive flag below is computed from finding content.
            "substantively_important": False,
        })

    finding_count_diff = len(g_findings) - len(l_findings)
    if abs(finding_count_diff) > 0:
        disagreements.append({
            "axis": "finding_count",
            "gemini_value": len(g_findings),
            "llama_value": len(l_findings),
            "diff": finding_count_diff,
            "substantively_important": False,
        })

    if novel_llama_findings:
        disagreements.append({
            "axis": "novel_llama_findings",
            "novel_count": len(novel_llama_findings),
            "novel_findings": [o["llama_description"] for o in novel_llama_findings],
            "substantively_important": novel_substantive,
        })

    if substantive_split:
        disagreements.append({
            "axis": "substantive_keyword_coverage",
            "gemini_findings": g_text_blob[:400],
            "llama_findings": l_text_blob[:400],
            "substantively_important": True,
        })

    if erase_failure:
        disagreements.append({
            "axis": "verdict_erases_sealed_failure",
            "gemini_value": gemini_verdict,
            "llama_value": llama_disp,
            "substantively_important": True,
        })

    return {
        "disposition_axis_agreement": disposition_axis_agreement,
        "expected_llama_disposition_for_match": expected_llama,
        "gemini_verdict": gemini_verdict,
        "llama_disposition": llama_disp,
        "finding_counts": {
            "gemini": len(g_findings),
            "llama": len(l_findings),
        },
        "severity_counts": {
            "gemini": severity_count_a,
            "llama": severity_count_b,
        },
        "per_llama_finding_overlaps": overlaps,
        "novel_llama_findings_count": len(novel_llama_findings),
        "disagreements": disagreements,
        "substantively_important_disagreement_present": any(
            d.get("substantively_important") for d in disagreements
        ),
        "drafter_arbitration_required": True,
        "comparison_generated_utc": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Replay runner
# ---------------------------------------------------------------------------

def gather_replay_target(workstream: str) -> Tuple[str, List[Path]]:
    """Build the combined audit-target text for a workstream replay."""
    iter_dir = ITER_ROOT / TARGET_ITERATION
    paths: List[Path] = []

    paths.append(iter_dir / "acceptance" / f"{workstream}.json")
    if workstream == "W0":
        paths.append(iter_dir / "acceptance" / "W0-amendment-b2-3.json")

    parts: List[str] = []
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"replay target missing: {p}")
        parts.append(f"=== {p.name} ===\n{p.read_text(encoding='utf-8')}\n")
    return "\n".join(parts), paths


def replay(workstream: str) -> Dict[str, Any]:
    iter_dir = ITER_ROOT / TARGET_ITERATION
    artifact, source_paths = gather_replay_target(workstream)
    gemini_audit_path = iter_dir / "audit" / f"{workstream}.json"
    if not gemini_audit_path.exists():
        raise FileNotFoundError(f"gemini audit missing: {gemini_audit_path}")
    gemini_audit = json.loads(gemini_audit_path.read_text(encoding="utf-8"))

    print(f"[{workstream}] running llama audit (artifact size: {len(artifact)} chars)…",
          flush=True)
    # Small-model schema violations are nondeterministic - retry up to 3
    # times before treating the malformed output as a real halt signal.
    last_exc = None
    llama_disp = None
    from aho.council.audit import CouncilAuditMalformedError
    for attempt in range(1, 4):
        try:
            llama_disp = council_audit(artifact)
            break
        except CouncilAuditMalformedError as exc:
            last_exc = exc
            print(f"[{workstream}] attempt {attempt}: malformed llama output ({exc}); retrying",
                  flush=True)
    if llama_disp is None:
        raise RuntimeError(
            f"llama audit malformed after 3 attempts: {last_exc}"
        )
    print(
        f"[{workstream}] llama disposition: {llama_disp['disposition']} "
        f"confidence={llama_disp['confidence']:.2f} "
        f"findings={len(llama_disp['findings'])} "
        f"latency={llama_disp['latency_ms']}ms",
        flush=True,
    )

    emitted = emit_disposition(
        audit=llama_disp,
        iteration=TARGET_ITERATION,
        workstream=workstream,
        audit_kind="replay",
        replay_source=workstream,
        target_artifact_text=artifact,
        iteration_root=ITER_ROOT,
    )
    print(f"[{workstream}] llama disposition written → {emitted['output_path']}",
          flush=True)

    comparison = compare_audits(gemini_audit, llama_disp)
    comparison_path = iter_dir / "audit" / "replay" / f"{workstream}-comparison.json"
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_doc = {
        "iteration": TARGET_ITERATION,
        "source_workstream": workstream,
        "source_artifact_paths": [str(p) for p in source_paths],
        "gemini_audit_path": str(gemini_audit_path),
        "llama_audit_replay_path": emitted["output_path"],
        **comparison,
    }
    comparison_path.write_text(
        json.dumps(comparison_doc, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[{workstream}] comparison written → {comparison_path}", flush=True)
    return {
        "llama_audit_path": emitted["output_path"],
        "comparison_path": str(comparison_path),
        "comparison": comparison_doc,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workstream", required=True, choices=["W0", "W1"])
    args = parser.parse_args(argv)
    result = replay(args.workstream)
    if result["comparison"]["substantively_important_disagreement_present"]:
        print("HALT: substantively important disagreement present", flush=True)
        return 2
    print("OK: replay complete; disagreements (if any) are stylistic", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
