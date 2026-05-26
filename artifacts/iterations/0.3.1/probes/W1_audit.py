"""0.3.1 W1 — invoke the council audit primitive against acceptance/W1.json.

First W-level audit on a populated ChromaDB collection in 0.3.1. RAG
enrichment expected to return registered_count > 0 for canonical IDs;
filter eligibility check should be non-vacuous for the first time since
0.3.1 W0 D9 (which ran against a 0-doc collection).

Adapted from 0.3.1 W0_audit.py template. ITERATION + WORKSTREAM updated.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from aho.audit_disposition_emitter import emit_disposition  # noqa: E402
from aho.council.audit import audit as council_audit  # noqa: E402
from aho.council.audit import CouncilAuditMalformedError  # noqa: E402

ITER_ROOT = ROOT / "artifacts" / "iterations"
ITERATION = "0.3.1"
WORKSTREAM = "W1"
ACCEPTANCE_PATH = ITER_ROOT / ITERATION / "acceptance" / f"{WORKSTREAM}.json"
AUDIT_DIR = ITER_ROOT / ITERATION / "audit"


def _run_audit(artifact_text: str) -> dict:
    last_exc = None
    for attempt in range(1, 4):
        try:
            return council_audit(artifact_text)
        except CouncilAuditMalformedError as exc:
            last_exc = exc
            print(
                f"  attempt {attempt}: malformed llama output ({exc}); retrying",
                flush=True,
            )
    raise SystemExit(f"llama audit malformed after 3 attempts: {last_exc}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rev", type=int, default=1)
    args = ap.parse_args(argv)

    if not ACCEPTANCE_PATH.exists():
        raise SystemExit(f"acceptance archive missing: {ACCEPTANCE_PATH}")

    artifact_text = ACCEPTANCE_PATH.read_text(encoding="utf-8")
    print(
        f"auditing {ACCEPTANCE_PATH} ({len(artifact_text)} chars), rev={args.rev}",
        flush=True,
    )

    disp = _run_audit(artifact_text)
    rag_enrichment = disp.get("rag_enrichment", {})
    print(
        f"disposition: {disp['disposition']} "
        f"confidence={disp['confidence']:.2f} "
        f"findings={len(disp['findings'])} "
        f"latency={disp['latency_ms']}ms",
        flush=True,
    )
    print(
        f"rag: detected={rag_enrichment.get('detected_count')} "
        f"registered={rag_enrichment.get('registered_count')} "
        f"unverified={rag_enrichment.get('unverified_count')}",
        flush=True,
    )

    canonical = AUDIT_DIR / f"{WORKSTREAM}.json"
    target = canonical if args.rev == 1 else AUDIT_DIR / f"{WORKSTREAM}-v{args.rev}.json"
    backup = None
    if args.rev != 1:
        if target.exists():
            raise SystemExit(f"refusing to overwrite existing re-audit at {target}")
        if not canonical.exists():
            raise SystemExit(f"--rev={args.rev} requested but canonical {canonical} missing")
        backup = AUDIT_DIR / f"{WORKSTREAM}.json.tmp-rev{args.rev}"
        canonical.rename(backup)

    try:
        emitted = emit_disposition(
            audit=disp,
            iteration=ITERATION,
            workstream=WORKSTREAM,
            audit_kind="self",
            target_artifact_path=ACCEPTANCE_PATH,
            iteration_root=ITER_ROOT,
        )
        if args.rev != 1:
            Path(emitted["output_path"]).rename(target)
            emitted["output_path"] = str(target)
    finally:
        if backup is not None and backup.exists():
            backup.rename(canonical)

    print(f"audit archive  -> {emitted['output_path']}", flush=True)
    print(f"audit sha256   -> {emitted['sha256'][:16]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
