"""W6 D3 - final 0.2.17 self-audit with the stabilized auditor primitive
(bootstrap test 7).

Runs `aho.council.audit` against the W6 acceptance archive itself with
rag_enrichment=True and the W4 D1 deterministic post-hoc filter active.

Model: llama3.2:3b
RAG enrichment: enabled (D2 of this workstream just put the carry-forwards
file into chromadb; W4-001 / W1-001 should now appear `registered` rather
than `unverified`).
Filter: enabled.

After the audit returns, this probe:
  1. Emits the disposition through `aho.audit_disposition_emitter` to
     `artifacts/iterations/0.2.17/audit/W6.json`.
  2. Logs filter activity (suppressed count, eligibility) + RAG enrichment
     summary (registered_count vs unverified_count, with an explicit
     check that W1-001 / W4-001 land in the registered set).
  3. Halts. Does NOT emit workstream_complete.

CLI:
    AHO_ITERATION=0.2.17 AHO_COUNCIL_EMBED_TIMEOUT_S=300 \
        python W6_self_audit.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from aho.audit_disposition_emitter import (  # noqa: E402
    emit_disposition,
)
from aho.council.audit import (  # noqa: E402
    CouncilAuditMalformedError,
    audit as council_audit,
)

ITER_ROOT = ROOT / "artifacts" / "iterations" / "0.2.17"
ACCEPTANCE_PATH = ITER_ROOT / "acceptance" / "W6.json"


def main() -> int:
    if not ACCEPTANCE_PATH.exists():
        print(f"FAIL: acceptance archive not found at {ACCEPTANCE_PATH}")
        return 2

    artifact_text = ACCEPTANCE_PATH.read_text()
    print(
        f"[W6 self-audit] target: {ACCEPTANCE_PATH}",
        flush=True,
    )
    print(
        f"[W6 self-audit] target size: {len(artifact_text)} chars",
        flush=True,
    )
    print(
        f"[W6 self-audit] start: {datetime.now(timezone.utc).isoformat()}",
        flush=True,
    )

    try:
        result = council_audit(
            artifact_text,
            contract=(
                "W6 acceptance archive - F-0.2.17-W1-001 secrets-test"
                " hash-fingerprint redesign closure + F-0.2.17-W4-001"
                " ChromaDB re-index hook closure + final 0.2.17 self-audit."
                " Auditor must spot-check whether D1 closure evidence"
                " (image rebuild, ghcr push retry, pull-clean image-id"
                " match, healthcheck, four W1 D3 gates revalidated) is"
                " internally consistent; whether D2 closure evidence"
                " (re-index hook, 3 unit tests, live verification probe"
                " with deterministic chunk-scan) is internally consistent;"
                " whether the carry_forwards_closed list and"
                " outstanding_pre_03x_gates list are mutually exclusive"
                " (W1-001 / W4-001 should appear in closed only;"
                " W1-003 / W5-001 / W5-002 should appear in outstanding"
                " only); whether the Pillar 11 invariant evidence is"
                " internally consistent. D3 itself is bootstrap test 7."
            ),
            rag_enrichment=True,
        )
    except CouncilAuditMalformedError as exc:
        print(f"FAIL: model output malformed: {exc}")
        return 3

    print(
        f"[W6 self-audit] disposition: {result['disposition']}"
        f" / confidence: {result['confidence']}",
        flush=True,
    )
    print(
        f"[W6 self-audit] findings_count: {len(result['findings'])}",
        flush=True,
    )
    print(
        f"[W6 self-audit] filter_eligible:"
        f" {result['finding_filter']['filter_eligible']}",
        flush=True,
    )
    print(
        f"[W6 self-audit] filter model_findings_count:"
        f" {result['finding_filter']['model_findings_count']}",
        flush=True,
    )
    print(
        f"[W6 self-audit] filter active_findings_count:"
        f" {result['finding_filter']['active_findings_count']}",
        flush=True,
    )
    print(
        f"[W6 self-audit] filter suppressed_count:"
        f" {result['finding_filter']['suppressed_count']}",
        flush=True,
    )
    if result.get("suppressed_findings"):
        print(
            "[W6 self-audit] suppressed_findings:",
            json.dumps(result["suppressed_findings"], indent=2),
            flush=True,
        )

    # RAG enrichment summary - explicitly check W4-001 / W1-001 status
    rag = result.get("rag_enrichment") or {}
    print(
        f"[W6 self-audit] rag detected={rag.get('detected_count')} "
        f"registered={rag.get('registered_count')} "
        f"unverified={rag.get('unverified_count')}",
        flush=True,
    )
    refs_by_id = {
        r.get("id"): r for r in (rag.get("references") or [])
    }
    for target_id in ("F-0.2.17-W1-001", "F-0.2.17-W4-001"):
        ref = refs_by_id.get(target_id)
        if ref is None:
            print(
                f"[W6 self-audit] {target_id} NOT in detected references",
                flush=True,
            )
        else:
            print(
                f"[W6 self-audit] {target_id} status="
                f"{ref.get('status')} top_path="
                f"{ref.get('top_source_artifact_path')}",
                flush=True,
            )

    emit = emit_disposition(
        audit=result,
        iteration="0.2.17",
        workstream="W6",
        audit_kind="self",
        target_artifact_path=ACCEPTANCE_PATH,
        iteration_root=ROOT / "artifacts" / "iterations",
    )
    print(
        f"[W6 self-audit] emitted: {emit['output_path']}"
        f" sha256={emit['sha256']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
