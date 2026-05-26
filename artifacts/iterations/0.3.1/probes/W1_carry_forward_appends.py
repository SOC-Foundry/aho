"""0.3.1 W1 — append W1 carry-forward closures + partial closures + new
entry to the canonical carry-forwards-0.2.16.md file via
aho.gap_carry_forward_writer.append_to_file.

Seven appends:
- 4 structural closures: F-0.2.18-W1-004, F-0.3.1-W0-001, F-0.3.1-W0-002, F-0.3.1-W0-004
- 2 partial closures (W2 completes): F-0.3.1-W0-003, F-0.3.1-W0-005
- 1 new W1-execution surface: F-0.3.1-W1-001 (nomic-embed chunk-size cap)

Each append triggers the F-0.2.17-W4-001 reindex hook (post-W4-of-0.2.17
closure). Expected: reindex_status=ok for all seven.
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


# ─────────────────────────────────────────────────────────────────────────
# Structural closures
# ─────────────────────────────────────────────────────────────────────────

ENTRY_F_0_2_18_W1_004 = {
    "id": "F-0.2.18-W1-004",
    "title": "Substrate decoherence — closed by 0.3.1 W1 D4 telemetry implementation",
    "severity": "important",
    "what_surfaced": (
        "0.2.18 W1: tailnet FQDN nzxtcos.tail78a311.ts.net baked into image at "
        "W0 probe time; tailnet rolled (a8 host rebuilt); seven days later W2 "
        "pre-flight tripped on stale FQDN; unscheduled image rebuild triggered. "
        "Closure target moved to 0.3.1 W1 substrate-freshness telemetry per "
        "ADR-0011 lightweight tier."
    ),
    "mechanism": (
        "Closure: 0.3.1 W1 D4 ships src/aho/observability.py (record_observable, "
        "last_verified_age_seconds, snapshot_all_facts) + src/aho/substrate_probes.py "
        "(13 fact probes including tailnet_domain) + bin/aho-probe-substrate fish "
        "wrapper + OTEL gauge aho.observable.last_verified_age_seconds + dashboard "
        "/api/substrate JSON + /substrate HTML brick grid. Tailnet-FQDN closure "
        "invariant verified on a8cos: probe shows last_verified_age_seconds < 1h "
        "after fresh probe (tail8492.ts.net, the post-incident tailnet domain). "
        "install.fish step substrate_facts_probed_recently invokes the probe set "
        "when observables.jsonl mtime > 24h."
    ),
    "disposition": (
        "Closed structurally. Re-decoherence detection now telemetry-driven: any "
        "stale fact older than its warning_age_seconds threshold surfaces in red "
        "on the dashboard brick grid + summary tile (stale_count > 0)."
    ),
    "target": "0.3.1 W1 (closed)",
    "source": (
        "0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D4] evidence"
    ),
    "audit_traceability": (
        "D8 self-audit (audit/W1.json sha 3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d) "
        "rag_enrichment confirms F-0.2.18-W1-004 referenced and resolved during enrichment."
    ),
}

ENTRY_F_0_3_1_W0_001 = {
    "id": "F-0.3.1-W0-001",
    "title": "Drafter substrate-prerequisite gap — closed by 0.3.1 W1 D3 aho-doctor wrapper",
    "severity": "important",
    "what_surfaced": (
        "0.3.1 W0 D9 first-invocation halt: drafter authored W0 prompt without "
        "auditing a8cos host Python dependency state. chromadb absent surfaced as "
        "halt-and-surface; drafter retracted over-broad Pillar 11 interpretation "
        "(git-only scope going forward) and authorized executor-side substrate "
        "component installation."
    ),
    "mechanism": (
        "Closure: 0.3.1 W1 D3 ships bin/aho-doctor fish wrapper + "
        "bin/_aho_doctor_eval.py internal evaluator. Signature: aho-doctor "
        "--workstream W1|W2|W3 [--required-steps id_list] [--remediate] [--json]. "
        "Invokes install.fish --check, parses 19-step JSONL output, evaluates "
        "per-workstream required-step list, exits 0 if all pass / 1 if any fail / "
        "2 if substrate-gap upstream / 3 if unknown workstream. Forward-only "
        "deployment: W2 first dogfoods at D0."
    ),
    "disposition": (
        "Closed structurally. install.fish --check is the canonical pre-flight "
        "surface across every W's D0. Per-workstream required-step lists documented "
        "in aho-doctor source. W0 D9 chromadb-absent class of failure now caught "
        "structurally before any substantive work."
    ),
    "target": "0.3.1 W1 (closed)",
    "source": (
        "0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D3] evidence + D8 drafter arbitration"
    ),
    "audit_traceability": (
        "D8 self-audit referenced F-0.3.1-W0-001 in rag_enrichment registered set "
        "(20 of 28 detected refs resolved as registered including this one)."
    ),
}

ENTRY_F_0_3_1_W0_002 = {
    "id": "F-0.3.1-W0-002",
    "title": "ChromaDB collection empty post-install — closed by 0.3.1 W1 D2 bootstrap; D8-verified",
    "severity": "important",
    "what_surfaced": (
        "0.3.1 W0 D9 self-audit emitted with rag_enrichment.registered_count=0 "
        "against detected_count=26. ChromaDB importable (post-install) but "
        "collection contained zero documents. Every detected reference returned "
        "status=unverified."
    ),
    "mechanism": (
        "Closure: 0.3.1 W1 D2 ships bin/aho-rag-bootstrap fish wrapper + "
        "src/aho/rag/bootstrap.py Python module. Ingests canonical artifact set "
        "(carry-forwards files, plan-docs, close notes, iteration-close notes, "
        "ADRs, retrospectives) via existing aho.rag.index_artifact (upsert; "
        "idempotent). Subcommands: --dry-run / --rebuild / --json / --quiet. "
        "Bootstrap on a8cos: 52 of 53 artifacts indexed → 263 chunks; duration "
        "175.9s; idempotent on re-run (263 → 263). install.fish step "
        "chromadb_collection_populated invokes the bootstrap as remediation."
    ),
    "disposition": (
        "Closed structurally AND verified operationally. D8 self-audit on this "
        "very W1 acceptance archive emitted with rag_enrichment.registered_count=20 "
        "(vs 0 at W0 D9 with the same audit primitive). 20/28 detected refs "
        "resolved as registered with non-null top_source_artifact_path. "
        "F-0.2.17-W1-003 + F-0.2.18-W2-004 + F-0.3.1-W0-002 + F-0.3.1-W0-001 + "
        "F-0.2.18-W0-008 all queried directly post-bootstrap return status=registered."
    ),
    "target": "0.3.1 W1 (closed; D8-verified)",
    "source": (
        "0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D2] evidence + D8 audit archive (sha 3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d) "
        "rag_enrichment.registered_count=20"
    ),
    "audit_traceability": (
        "D8 RAG enrichment shows 20 registered / 8 unverified out of 28 detected refs "
        "— the registered_count > 0 is the operational closure signal for this entry."
    ),
}

ENTRY_F_0_3_1_W0_004 = {
    "id": "F-0.3.1-W0-004",
    "title": "Canonical-root .aho-checkpoint.json absent — closed by 0.3.1 W1 D1 install.fish step",
    "severity": "important",
    "what_surfaced": (
        "0.3.1 W0 workstream_complete emit: find_project_root() correctly returned "
        "~/Development/Projects/socfoundry/aho but no .aho-checkpoint.json existed "
        "at that path. emit_workstream_complete's checkpoint-advance code path "
        "short-circuited on ckpt_path.exists() check (fail-soft); event landed in "
        "event log but per-workstream completion state did not advance. Legacy "
        "stale checkpoint at /home/kthompson/dev/projects/aho/.aho-checkpoint.json "
        "(mtime 2026-05-16, iteration=0.2.16, W2=in_progress) untouched."
    ),
    "mechanism": (
        "Closure: 0.3.1 W1 D1 install.fish adds step canonical_checkpoint_present. "
        "Check: test -f $project_root/.aho-checkpoint.json. Remediation: python "
        "writer that generates initial-state checkpoint per existing schema "
        "(iteration / phase / run_type / current_workstream / workstreams / "
        "executor / auditor / started_at / status / proceed_awaited). Step runs "
        "after symlinks step; subsequent emit_workstream_complete invocations "
        "find the checkpoint and advance per-workstream state correctly."
    ),
    "disposition": (
        "Closed structurally. .aho-checkpoint.json now present at canonical project "
        "root with current iteration (0.3.1) / current workstream (W1) / status=active. "
        "Future emit_workstream_complete invocations advance per-workstream state."
    ),
    "target": "0.3.1 W1 (closed)",
    "source": (
        "0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D1] evidence + canonical_checkpoint_present step in install.fish"
    ),
}

# ─────────────────────────────────────────────────────────────────────────
# Partial closures (W2 completes)
# ─────────────────────────────────────────────────────────────────────────

ENTRY_F_0_3_1_W0_003 = {
    "id": "F-0.3.1-W0-003",
    "title": "OTEL collector endpoint post-NZXTcos-decommission — W1 probe; W2 Beacon migration completes",
    "severity": "important",
    "what_surfaced": (
        "0.3.1 W0 workstream_complete emit: OTLP span exports failed with "
        "StatusCode.UNAVAILABLE on 127.0.0.1:4317. NZXTcos decommissioned per "
        "CLAUDE.md §Deployment hosts; the OTEL collector substrate host moved off "
        "NZXTcos but no a8cos-local or alternate-host endpoint configured."
    ),
    "mechanism": (
        "Partial closure in W1: D4 ships substrate fact #2 (otel_collector_endpoint) "
        "as a 1h-warn-age probe. The probe currently reports fail because no "
        "a8cos-local OTLP receiver is running yet. The probe itself is the W1 "
        "telemetry surface — visibility into endpoint-reachability state lives in "
        "observables.jsonl + dashboard. Full closure in W2 via Beacon migration."
    ),
    "disposition": (
        "Partially closed in 0.3.1 W1 (probe + visibility). Full closure in 0.3.1 W2: "
        "extract beacon's otel/config.py + exporter.py + buffer.py pattern, copy "
        "into src/aho/observability/otlp_exporter.py, wire metrics + audit "
        "dispositions to beacon's gRPC endpoint over Tailscale per W2 "
        "plan-doc-amendment scope expansion Track 2 (Beacon integration) + Track 3 "
        "(OTEL endpoint migration). Fact #2 probe will flip from fail to ok "
        "post-W2."
    ),
    "target": "0.3.1 W2",
    "source": (
        "0.3.1 W0 close note + handoff brief observation 2 + 0.3.1 W1 acceptance "
        "archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D4] partial-closure section"
    ),
}

ENTRY_F_0_3_1_W0_005 = {
    "id": "F-0.3.1-W0-005",
    "title": "Legacy sys.path drift in editable-install metadata — W1 probe; W2 pip install -e re-install completes",
    "severity": "important",
    "what_surfaced": (
        "0.3.1 W0 D9 substrate probe surfaced sys.path includes "
        "/home/kthompson/dev/projects/aho/src (legacy pre-migration path). "
        "Editable install at ~/.local/lib/python3.14/site-packages/aho-0.2.18.dist-info "
        "direct_url.json points at file:///home/kthompson/dev/projects/aho "
        "(legacy). Imports resolve correctly because executor probe scripts do "
        "sys.path.insert(0, str(ROOT/'src')) before importing aho, but the "
        "editable-install metadata is stale."
    ),
    "mechanism": (
        "Partial closure in W1: D4 ships substrate fact #13 (sys_path_clean) as a "
        "1h-warn-age probe. The probe currently reports fail (legacy entry "
        "detected). install.fish step python_sys_path_clean is probe-only with no "
        "remediation defined — by design, W2 owns the remediation. Bin wrappers "
        "(aho-rag-bootstrap, aho-claw3d) work around in-band via PYTHONPATH "
        "prepending the canonical src/."
    ),
    "disposition": (
        "Partially closed in 0.3.1 W1 (probe + visibility). Full closure in 0.3.1 W2 "
        "Track 4: pip install --user --break-system-packages -e "
        "~/Development/Projects/socfoundry/aho re-installs editable pointing at "
        "canonical path; verify post-install sys.path no longer includes legacy "
        "/home/kthompson/dev/projects/aho/src. Fact #13 probe will flip from fail "
        "to ok post-W2; per-wrapper PYTHONPATH workarounds can be removed in a "
        "subsequent cleanup pass."
    ),
    "target": "0.3.1 W2",
    "source": (
        "0.3.1 W0 handoff brief observation 3 + 0.3.1 W1 acceptance archive "
        "(sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D4] partial-closure section"
    ),
}

# ─────────────────────────────────────────────────────────────────────────
# New W1-execution surface
# ─────────────────────────────────────────────────────────────────────────

ENTRY_F_0_3_1_W1_001 = {
    "id": "F-0.3.1-W1-001",
    "title": "D2 ingestion skip — single artifact chunk exceeded nomic-embed-text size cap",
    "severity": "cosmetic",
    "what_surfaced": (
        "During 0.3.1 W1 D2 bootstrap, 52 of 53 canonical artifacts indexed "
        "successfully. 1 artifact skipped: "
        "artifacts/iterations/0.2.17/iteration-close-0.2.17.md chunk-5 (out of 6 "
        "chunks) failed embed with HTTP 400 Bad Request from Ollama /api/embed. "
        "Cause: chunk content exceeds nomic-embed-text effective input size cap. "
        "Other 5 chunks of the same file did index successfully."
    ),
    "mechanism": (
        "aho.rag._chunk_text uses chunk_size=4000 with overlap=500. Per "
        "src/aho/rag/__init__.py docstring: nomic-embed-text in Ollama 0.20 caps "
        "around ~7000 chars for whitespace-heavy text and ~5000 for dense JSON. "
        "The 4000-char chunks usually fit but iteration-close-0.2.17.md chunk-5 "
        "evidently contained dense content that exceeded the embedder's "
        "tokenization budget. The bootstrap module's per-chunk try/except catches "
        "the embed failure, records the skip in result.skipped_paths, and "
        "continues — design works as intended."
    ),
    "disposition": (
        "Cosmetic visibility item. The artifact is partially queryable (5 of 6 "
        "chunks indexed). Closure could be tighter chunk sizing (3000 with 500 "
        "overlap) at bootstrap time, OR a per-chunk size guard that splits "
        "oversized chunks further before embedding. Not a structural defect; not "
        "a blocker for D8 closure gates. Track for visibility."
    ),
    "target": "0.3.2 (peer to F-0.2.17-W6-001 retrieval-quality work) OR 0.3.1 W2 if chunking refinement is in scope (drafter to decide at W2 plan-doc-amendment time)",
    "source": (
        "0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) "
        "deliverables[D2].evidence; bootstrap result.skipped_paths in run-1 JSON output"
    ),
}


ALL_ENTRIES = [
    ("F-0.2.18-W1-004", ENTRY_F_0_2_18_W1_004),
    ("F-0.3.1-W0-001",  ENTRY_F_0_3_1_W0_001),
    ("F-0.3.1-W0-002",  ENTRY_F_0_3_1_W0_002),
    ("F-0.3.1-W0-004",  ENTRY_F_0_3_1_W0_004),
    ("F-0.3.1-W0-003",  ENTRY_F_0_3_1_W0_003),
    ("F-0.3.1-W0-005",  ENTRY_F_0_3_1_W0_005),
    ("F-0.3.1-W1-001",  ENTRY_F_0_3_1_W1_001),
]


def _run_append(label, entry):
    pre_sha = _sha256_of(CARRY_FWD_FILE)
    pre_size = CARRY_FWD_FILE.stat().st_size
    pre_lines = len(CARRY_FWD_FILE.read_text(encoding="utf-8").splitlines())
    print(f"\n=== {label} ===", flush=True)
    print(f"pre  sha256 = {pre_sha}", flush=True)
    ret = append_to_file(file_path=str(CARRY_FWD_FILE), entry=entry)
    post_sha = _sha256_of(CARRY_FWD_FILE)
    post_size = CARRY_FWD_FILE.stat().st_size
    post_lines = len(CARRY_FWD_FILE.read_text(encoding="utf-8").splitlines())
    print(f"post sha256 = {post_sha}", flush=True)
    print(f"size {pre_size} -> {post_size}; lines {pre_lines} -> {post_lines}", flush=True)
    print(f"target_section: {ret['target_section']}", flush=True)
    print(f"entries_added:  {ret['entries_added']}", flush=True)
    print(f"reindex_status: {ret['reindex']['reindex_status']}", flush=True)
    return {
        "label": label,
        "entry_id": entry["id"],
        "pre_sha": pre_sha,
        "post_sha": post_sha,
        "writer_return": ret,
    }


def main() -> int:
    if not CARRY_FWD_FILE.exists():
        raise SystemExit(f"carry-forwards file missing: {CARRY_FWD_FILE}")
    results = []
    for label, entry in ALL_ENTRIES:
        results.append(_run_append(label, entry))
    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps({
        "file_path": str(CARRY_FWD_FILE),
        "appends": [
            {
                "label": r["label"],
                "entry_id": r["entry_id"],
                "pre_sha": r["pre_sha"],
                "post_sha": r["post_sha"],
                "entries_added": r["writer_return"]["entries_added"],
                "lines_added": r["writer_return"]["lines_added"],
                "target_section": r["writer_return"]["target_section"],
                "reindex_status": r["writer_return"]["reindex"]["reindex_status"],
                "doc_id": r["writer_return"]["reindex"].get("doc_id"),
            }
            for r in results
        ],
        "total_appends": len(results),
        "all_reindex_ok": all(r["writer_return"]["reindex"]["reindex_status"] == "ok" for r in results),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
