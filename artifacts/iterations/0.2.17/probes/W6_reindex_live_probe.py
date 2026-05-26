"""W6 D2.2 live verification - F-0.2.17-W6-PROBE round-trip through the
gap_carry_forward_writer.append_to_file → ChromaDB re-index hook.

Process:
  1. Snapshot carry-forwards-0.2.16.md content + sha256.
  2. Append a synthetic F-0.2.17-W6-PROBE entry via the writer.
     The writer's new re-index hook fires after the append.
  3. Query the project iteration-context RAG for the probe entry's text;
     verify a result references F-0.2.17-W6-PROBE.
  4. Restore original file content (byte-perfect rollback).
  5. Manually re-index the restored file so ChromaDB mirrors the file again
     (idempotent overwrite - `index_artifact` is keyed by path-derived
     doc id, not content).
  6. Verify final file sha256 matches the pre-probe sha256.

If any step fails, the probe halts and prints a structured failure summary
to stdout. The carry-forwards file is restored even on failure (best-effort
finally block).

Pillar 11: writes only to artifacts/iterations/. No git ops.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from aho import gap_carry_forward_writer as gcfw  # noqa: E402
from aho import rag as _rag  # noqa: E402

CARRY_FWD = (
    ROOT
    / "artifacts"
    / "iterations"
    / "0.2.16"
    / "carry-forwards-0.2.16.md"
)


PROBE_ID = "F-0.2.17-W6-PROBE"
PROBE_TITLE = "ChromaDB re-index hook live verification probe (D2.2)"
PROBE_BODY = (
    "synthetic probe entry verifying the gap_carry_forward_writer "
    "append_to_file path triggers a ChromaDB re-index. Removed at the "
    "end of the same probe run."
)


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    if not CARRY_FWD.exists():
        print(f"FAIL: carry-forwards file not found at {CARRY_FWD}")
        return 2

    original_text = CARRY_FWD.read_text(encoding="utf-8")
    pre_sha = _sha256(CARRY_FWD)
    print(f"[probe] pre-sha256={pre_sha}", flush=True)

    started_utc = datetime.now(timezone.utc).isoformat()
    post_append_sha = ""
    post_restore_sha = ""
    hit = None

    try:
        # Step 2 - append probe entry
        append_result = gcfw.append_to_file(
            file_path=CARRY_FWD,
            entry={
                "id": PROBE_ID,
                "title": PROBE_TITLE,
                "severity": "info",
                "what_surfaced": PROBE_BODY,
                "disposition": "remove at end of probe run",
                "target": "0.2.17 W6 (probe - temporary, not a real carry-forward)",
                "source": "0.2.17 W6 D2.2 live verification",
            },
        )
        print(
            f"[probe] append_result.entries_added={append_result['entries_added']} "
            f"reindex={append_result['reindex']}",
            flush=True,
        )
        post_append_sha = _sha256(CARRY_FWD)
        print(f"[probe] post-append-sha256={post_append_sha}", flush=True)

        if append_result["reindex"]["reindex_status"] != "ok":
            print(
                "FAIL: reindex did not return ok - "
                f"{append_result['reindex']!r}",
                flush=True,
            )
            return 3

        # Step 3a - embedding-similarity query (best-effort signal)
        query_text = f"{PROBE_ID} probe entry verifying re-index hook live"
        project = os.environ.get("AHO_PROJECT", "ahomw")
        retrievals = _rag.query(query_text, k=10, project=project)
        print(f"[probe] retrieved {len(retrievals)} results", flush=True)
        for r in retrievals:
            doc = r.get("document") or ""
            if PROBE_ID in doc:
                hit = r
                break

        # Step 3b - DETERMINISTIC chunk inspection. Use collection.get()
        # with a path metadata filter to fetch all chunks indexed for the
        # carry-forwards file, then scan their `documents` text for the
        # PROBE_ID. This avoids the failure mode where the chunk containing
        # the probe entry doesn't rank in the top-k by embedding similarity
        # against a generic query string but is in fact present in the index.
        client = _rag._client()
        coll = client.get_or_create_collection(
            name=_rag._collection_name(project)
        )
        path_filter = str(CARRY_FWD)
        getr = coll.get(
            where={"source_artifact_path": path_filter},
            include=["documents", "metadatas"],
        )
        chunks_for_path = (getr.get("documents") or [])
        chunk_ids_for_path = (getr.get("ids") or [])
        chunks_with_probe = [
            (cid, doc)
            for cid, doc in zip(chunk_ids_for_path, chunks_for_path)
            if doc and PROBE_ID in doc
        ]
        print(
            f"[probe] deterministic chunk-scan: chunks_for_path="
            f"{len(chunks_for_path)} chunks_with_probe={len(chunks_with_probe)}",
            flush=True,
        )
        if not chunks_with_probe:
            print(
                f"FAIL: probe ID {PROBE_ID} not present in any chunk of "
                f"the indexed carry-forwards file.",
                flush=True,
            )
            return 4
        deterministic_hit_id = chunks_with_probe[0][0]
        print(
            f"[probe] deterministic hit: chunk_id={deterministic_hit_id}",
            flush=True,
        )

        if hit is None:
            top_ids = [r.get("id") for r in retrievals[:5]]
            print(
                f"[probe] embedding-similarity query did NOT surface the "
                f"probe in top 10 (top: {top_ids}); deterministic scan "
                f"confirms the chunk IS in the index. The file is "
                f"re-indexed correctly post-append; embedding-similarity "
                f"ranking against this generic query just doesn't bring "
                f"the chunk to top-k. RAG ranking is a separate concern "
                f"from F-0.2.17-W4-001 closure.",
                flush=True,
            )
            hit = {
                "id": deterministic_hit_id,
                "score": -1.0,
                "similarity": -1.0,
                "source_artifact_path": str(CARRY_FWD),
                "verification_path": "deterministic_chunk_scan",
            }
        else:
            print(
                f"[probe] embedding hit: id={hit['id']} score={hit['score']:.4f} "
                f"similarity={hit['similarity']:.4f} "
                f"source={hit.get('source_artifact_path')}",
                flush=True,
            )
            hit["verification_path"] = "embedding_similarity_top_10"
    finally:
        # Always restore the file contents - byte-perfect rollback.
        CARRY_FWD.write_text(original_text, encoding="utf-8")
        post_restore_sha = _sha256(CARRY_FWD)
        print(f"[probe] restore-sha256={post_restore_sha}", flush=True)

    if post_restore_sha != pre_sha:
        print(
            f"FAIL: restored sha256 {post_restore_sha} != pre-sha {pre_sha}",
            flush=True,
        )
        return 5

    # Step 5 - re-index the restored content so ChromaDB mirrors the file
    re_doc_id = _rag.index_artifact(
        CARRY_FWD,
        project=os.environ.get("AHO_PROJECT", "ahomw"),
        iteration="0.2.16",
        workstream="carry-forwards",
    )
    print(f"[probe] re-indexed (post-restore) doc_id={re_doc_id}", flush=True)

    completed_utc = datetime.now(timezone.utc).isoformat()
    summary = {
        "status": "ok",
        "pre_sha": pre_sha,
        "post_append_sha": post_append_sha,
        "post_restore_sha": post_restore_sha,
        "probe_id": PROBE_ID,
        "retrieval_score": hit["score"],
        "retrieval_similarity": hit["similarity"],
        "retrieval_source_path": hit.get("source_artifact_path"),
        "started_utc": started_utc,
        "completed_utc": completed_utc,
    }
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
