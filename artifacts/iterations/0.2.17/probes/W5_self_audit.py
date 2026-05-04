"""W5 D8 — self-audit with stabilized auditor (bootstrap test 6).

Runs `aho.council.audit` against the W5 acceptance archive itself with
rag_enrichment=True and the W4 D1 deterministic post-hoc filter active.
This audit exercises the full stabilized stack: model + RAG + filter.

After the audit returns, this probe:
  1. Emits the disposition through `aho.audit_disposition_emitter` to
     `artifacts/iterations/0.2.17/audit/W5.json`.
  2. Logs filter activity (suppressed count, eligibility) to stdout for
     drafter review.
  3. Halts. Does NOT emit workstream_complete.

CLI:
    python W5_self_audit.py
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
ACCEPTANCE_PATH = ITER_ROOT / "acceptance" / "W5.json"


def main() -> int:
    if not ACCEPTANCE_PATH.exists():
        print(f"FAIL: acceptance archive not found at {ACCEPTANCE_PATH}")
        return 2

    artifact_text = ACCEPTANCE_PATH.read_text()
    print(
        f"[W5 self-audit] target: {ACCEPTANCE_PATH}",
        flush=True,
    )
    print(
        f"[W5 self-audit] target size: {len(artifact_text)} chars",
        flush=True,
    )
    print(
        f"[W5 self-audit] start: {datetime.now(timezone.utc).isoformat()}",
        flush=True,
    )

    try:
        result = council_audit(
            artifact_text,
            contract=(
                "W5 acceptance archive — ADR consolidation + repo-resident"
                " component decomposition + repo-resident claw3d brick spec +"
                " 0.2.17 retrospective + W5 self-audit. Auditor must"
                " spot-check whether deliverables D1-D7 actually correspond"
                " to file paths + sha256 hashes claimed in the archive,"
                " whether carry-forward IDs referenced are real, whether the"
                " three-iteration evidence build claims (W2 baseline / W3"
                " partial / W4 structural) correspond to sealed archive"
                " shas, and whether the Pillar 11 invariant evidence is"
                " internally consistent. D8 itself is bootstrap test 6 of"
                " the auditor primitive."
            ),
            rag_enrichment=True,
        )
    except CouncilAuditMalformedError as exc:
        print(f"FAIL: model output malformed: {exc}")
        return 3

    print(
        f"[W5 self-audit] disposition: {result['disposition']}"
        f" / confidence: {result['confidence']}",
        flush=True,
    )
    print(
        f"[W5 self-audit] findings_count: {len(result['findings'])}",
        flush=True,
    )
    print(
        f"[W5 self-audit] filter_eligible:"
        f" {result['finding_filter']['filter_eligible']}",
        flush=True,
    )
    print(
        f"[W5 self-audit] filter model_findings_count:"
        f" {result['finding_filter']['model_findings_count']}",
        flush=True,
    )
    print(
        f"[W5 self-audit] filter active_findings_count:"
        f" {result['finding_filter']['active_findings_count']}",
        flush=True,
    )
    print(
        f"[W5 self-audit] filter suppressed_count:"
        f" {result['finding_filter']['suppressed_count']}",
        flush=True,
    )
    if result.get("suppressed_findings"):
        print(
            "[W5 self-audit] suppressed_findings:",
            json.dumps(result["suppressed_findings"], indent=2),
            flush=True,
        )

    emit = emit_disposition(
        audit=result,
        iteration="0.2.17",
        workstream="W5",
        audit_kind="self",
        target_artifact_path=ACCEPTANCE_PATH,
        iteration_root=ROOT / "artifacts" / "iterations",
    )
    print(
        f"[W5 self-audit] emitted: {emit['output_path']}"
        f" sha256={emit['sha256']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
