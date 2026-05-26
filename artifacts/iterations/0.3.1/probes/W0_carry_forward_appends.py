"""0.3.1 W0 — append two W0 carry-forwards to the canonical carry-forwards
file via aho.gap_carry_forward_writer.append_to_file.

Entry payloads source: artifacts/iterations/0.3.1/acceptance/W0.json
`carry_forwards_added` field. Two separate append calls (one per entry).

Per W0 close note + drafter directive: F-0.3.1-W0-001 + F-0.3.1-W0-002 are
the two W0 carry-forwards. The reindex hook from F-0.2.17-W4-001 closure
fires post-append; post-reindex collection-level bootstrap remains a W1
concern (F-0.3.1-W0-002 closure mechanism).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from aho.gap_carry_forward_writer import append_to_file  # noqa: E402

CARRY_FWD_FILE = ROOT / "artifacts" / "iterations" / "0.2.16" / "carry-forwards-0.2.16.md"


def _sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


ENTRY_W0_001 = {
    "id": "F-0.3.1-W0-001",
    "title": (
        "Drafter substrate prerequisite gap — W0 prompt assumed inherited "
        "substrate without explicit pre-flight verification"
    ),
    "severity": "important",
    "what_surfaced": (
        "W0 prompt (drafter, claude-web) assumed a8cos had inherited NZXTcos's "
        "substrate via install.fish but did not include an explicit pre-flight "
        "substrate-verification step in the W0 sequence. Surfaced as "
        "chromadb-absent halt during D9 first invocation. The W0_audit.py "
        "template ported from 0.2.18 ran on NZXTcos host Python where chromadb "
        "was substrate-resident; a8cos host Python (python3.14) had no chromadb "
        "at session start."
    ),
    "mechanism": (
        "Drafter authored W0 prompt without auditing a8cos's host Python "
        "dependency state. During arbitration, drafter retracted the W0 "
        "prompt's over-broad Pillar 11 interpretation: Pillar 11 scope is "
        "git operations only, plus secret decryption, /etc/sudoers, "
        "customer-lane crossings, hardware procurement, disruptive reboots. "
        "Substrate component installation is executor scope going forward "
        "across 0.3.1."
    ),
    "disposition": (
        "Every future W prompt includes a D0 substrate-verification "
        "deliverable that probes required components (chromadb, ollama "
        "models present, broker socket, audit dependencies importable) "
        "before any other work. Drafter chat-side process improvement "
        "applied retroactively to remaining 0.3.1 workstreams (W1-W7) and "
        "canonical pattern for 0.3.2+. Structural closure via install.fish "
        "--check mode at W1/W2 substrate-freshness work."
    ),
    "target": "0.3.1 W1-W7 + 0.3.2+",
    "source": (
        "0.3.1 W0 D9 first-invocation halt (acceptance/W0.json sha "
        "ab37497914bb9b194e7434138bd88a9d3a1278185d1cb37dd11836983731a7ff "
        "deliverables[D9].initial_halt_record) + drafter arbitration "
        "2026-05-24"
    ),
}

ENTRY_W0_002 = {
    "id": "F-0.3.1-W0-002",
    "title": (
        "ChromaDB iteration-context collection empty post-install; RAG "
        "enrichment returns all-unverified until bootstrap"
    ),
    "severity": "important",
    "what_surfaced": (
        "W0 D9 audit emitted with rag_enrichment.registered_count=0 against "
        "rag_enrichment.detected_count=26. ChromaDB importable (post-install) "
        "but collection contains zero documents. Every detected reference "
        "(D1-D9, ADR-0007/0009/0011/0012, F-0.2.17-* and F-0.2.18-* "
        "carry-forwards) returned status=unverified."
    ),
    "mechanism": (
        "chromadb pip install creates the python module but does NOT ingest "
        "the canonical artifact set (carry-forwards-0.2.16.md, plan-docs, "
        "ADRs, close-notes) into the project collection. RAG enrichment in "
        "aho.council.audit_ref_lookup queries the empty collection and "
        "returns 0 hits per reference. Distinguishable from F-0.2.17-W6-001 "
        "(lookup-ranking-on-opaque-IDs) by: W6-001 returns SOME registered "
        "refs from a populated collection; W0-002 returns ZERO registered "
        "refs because the collection itself is empty."
    ),
    "disposition": (
        "0.3.1 W1 substrate-freshness scope expands to include "
        "`aho rag bootstrap` (or equivalent) deliverable that ingests the "
        "canonical artifact set on a fresh chromadb install. Closure "
        "verified when W1 self-audit RAG enrichment shows registered_count "
        "> 0 for known-registered IDs (e.g., F-0.2.17-W1-003)."
    ),
    "target": "0.3.1 W1",
    "source": (
        "0.3.1 W0 D9 self-audit (audit/W0.json sha "
        "9749cfed8fd5268e0facf36915459f616200e7c43de21ff778f75f9e83115e14 "
        "F1 finding 'ADR-0011 unverified status echo')"
    ),
    "audit_traceability": (
        "audit/W0.json findings[1] id=ADR-0011 severity=important; "
        "rag_enrichment.unverified_count == rag_enrichment.detected_count == "
        "26 (empty-collection signature)"
    ),
}


def _run_append(label: str, entry: dict) -> dict:
    pre_sha = _sha256_of(CARRY_FWD_FILE)
    pre_size = CARRY_FWD_FILE.stat().st_size
    pre_lines = len(CARRY_FWD_FILE.read_text(encoding="utf-8").splitlines())
    print(f"\n=== {label} ===", flush=True)
    print(f"pre  sha256 = {pre_sha}", flush=True)
    print(f"pre  size   = {pre_size} bytes / {pre_lines} lines", flush=True)
    ret = append_to_file(file_path=str(CARRY_FWD_FILE), entry=entry)
    post_sha = _sha256_of(CARRY_FWD_FILE)
    post_size = CARRY_FWD_FILE.stat().st_size
    post_lines = len(CARRY_FWD_FILE.read_text(encoding="utf-8").splitlines())
    print(f"post sha256 = {post_sha}", flush=True)
    print(f"post size   = {post_size} bytes / {post_lines} lines", flush=True)
    print("writer return dict:", flush=True)
    print(json.dumps(ret, indent=2, default=str), flush=True)
    return {
        "label": label,
        "entry_id": entry["id"],
        "pre_sha": pre_sha,
        "post_sha": post_sha,
        "pre_size": pre_size,
        "post_size": post_size,
        "pre_lines": pre_lines,
        "post_lines": post_lines,
        "writer_return": ret,
    }


def main() -> int:
    if not CARRY_FWD_FILE.exists():
        raise SystemExit(f"carry-forwards file missing: {CARRY_FWD_FILE}")
    r1 = _run_append("F-0.3.1-W0-001", ENTRY_W0_001)
    r2 = _run_append("F-0.3.1-W0-002", ENTRY_W0_002)
    summary = {
        "file_path": str(CARRY_FWD_FILE),
        "appends": [r1, r2],
    }
    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
