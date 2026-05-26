"""0.3.1 W1 — emit workstream_complete via direct python emit_workstream_complete()
per F-0.2.17-W0-004 CLI argparse workaround pattern.

Status: pass_with_findings (drafter-arbitrated from llama self-audit halt).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("AHO_ITERATION", "0.3.1")
os.environ.setdefault("AHO_WORKSTREAM", "W1")

from aho.workstream_events import emit_workstream_complete  # noqa: E402
from aho.logger import LOG_PATH  # noqa: E402

SUMMARY = (
    "install.fish idempotency hardening + structured per-step output + aho rag "
    "bootstrap (closes F-0.3.1-W0-002 structurally, D8-verified registered_count=20 "
    "vs 0 at W0 D9) + bin/aho-doctor wrapper (closes F-0.3.1-W0-001 structurally; "
    "forward-only deployment from W2) + 13-fact substrate freshness telemetry "
    "(closes F-0.2.18-W1-004; closes F-0.3.1-W0-004 + W0-005 operationally; closes "
    "W0-003 partially) + dashboard surface + tests + self-audit (bootstrap test 11; "
    "first non-vacuous filter-eligibility check in 0.3.1; W4-0.2.17 filter "
    "regression check passes non-vacuously). 8 deliverables passed acceptance. "
    "D8 halted on 2 auditor narrative-lift / retrieval-relevance findings (F0 D2 "
    "F-0.2.17-W6-001-style, F1 F-0.2.17-W5-001 F-0.2.18-W0-008 shape); drafter "
    "arbitrated halt to pass_with_findings. Four structural closures + two partial "
    "closures + one new info-severity carry-forward (F-0.3.1-W1-001 chunking). "
    "Acceptance: 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba; "
    "Audit (UNTOUCHED): 3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d."
)


def main() -> int:
    print(f"emitting workstream_complete for 0.3.1 W1", flush=True)
    print(f"  AHO_ITERATION = {os.environ.get('AHO_ITERATION')}", flush=True)
    print(f"  AHO_WORKSTREAM = {os.environ.get('AHO_WORKSTREAM')}", flush=True)
    print(f"  LOG_PATH = {LOG_PATH}", flush=True)
    event = emit_workstream_complete(
        workstream_id="W1",
        status="pass_with_findings",
        summary=SUMMARY,
        source_agent="claude-code",
    )
    if event is None:
        print("GUARD HIT: workstream_complete already emitted for 0.3.1 W1.", flush=True)
        return 0
    print("emit returned event:", flush=True)
    print(json.dumps(event, indent=2, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
