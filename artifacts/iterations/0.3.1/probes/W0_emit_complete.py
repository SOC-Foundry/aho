"""0.3.1 W0 — emit workstream_complete via direct python emit_workstream_complete()
per F-0.2.17-W0-004 (CLI argparse choices workaround; carry-forward to 0.3.x).

Status: pass_with_findings (drafter-arbitrated from llama self-audit halt).
Summary: per drafter directive (W0 close-handoff).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("AHO_ITERATION", "0.3.1")
os.environ.setdefault("AHO_WORKSTREAM", "W0")

from aho.workstream_events import emit_workstream_complete  # noqa: E402
from aho.logger import LOG_PATH  # noqa: E402

SUMMARY = (
    "Plan-doc + ADR-0011/0012 placement + CLAUDE.md rewrite + carry-forward "
    "fold-in + W0 self-audit. 9 deliverables passed acceptance. D9 self-audit "
    "halted on substrate state (chromadb absent then collection empty "
    "post-install); executor remediated (installed chromadb 1.5.9; bumped "
    "audit timeouts for CPU-inference latency on Radeon 780M); drafter "
    "arbitrated halt to pass_with_findings. Two new carry-forwards: W0-001 "
    "drafter substrate-prerequisite gap, W0-002 ChromaDB collection empty "
    "post-install. Pillar 11 scope corrected mid-W0 (git-ops-only, substrate "
    "installation is executor-scope); formal Pillar 10/11 amendments + new "
    "Pillars 12/13 land at W6 ADR consolidation."
)


def main() -> int:
    print(f"emitting workstream_complete for 0.3.1 W0", flush=True)
    print(f"  AHO_ITERATION = {os.environ.get('AHO_ITERATION')}", flush=True)
    print(f"  AHO_WORKSTREAM = {os.environ.get('AHO_WORKSTREAM')}", flush=True)
    print(f"  LOG_PATH = {LOG_PATH}", flush=True)
    event = emit_workstream_complete(
        workstream_id="W0",
        status="pass_with_findings",
        summary=SUMMARY,
        source_agent="claude-code",
    )
    if event is None:
        print(
            "GUARD HIT: workstream_complete already emitted for 0.3.1 W0 "
            "(returned None — emitter saw existing event in log).",
            flush=True,
        )
        return 0
    print("emit returned event:", flush=True)
    print(json.dumps(event, indent=2, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
