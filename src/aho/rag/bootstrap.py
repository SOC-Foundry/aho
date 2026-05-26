"""aho.rag.bootstrap — ingest canonical artifact set into per-project ChromaDB
collection. Closes F-0.3.1-W0-002.

The W0 D9 audit surfaced that chromadb pip install creates the python module
but does NOT ingest the canonical artifact set into the per-project collection.
This module ingests the canonical set so RAG enrichment in aho.council.audit
resolves references to registered (rather than all-unverified).

Canonical artifact set (per W1 plan-doc amendment §D2):
- artifacts/iterations/*/carry-forwards-*.md
- artifacts/iterations/*/aho-plan-*.md
- artifacts/iterations/*/W*-close-note.md
- artifacts/iterations/*/iteration-close-*.md
- artifacts/adrs/*.md
- docs/retrospectives/*.md

Idempotency: index_artifact uses upsert keyed on doc_id, so re-running produces
the same collection state with the same chunk shas. Re-ingesting on already-
populated collection is a no-op at the data layer (embeddings recomputed and
upserted; identical chunks → identical embeddings under the same model).

`--rebuild` drops the collection first via `chroma_client.delete_collection(name)`
and recreates. Escape hatch for corrupted state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Hosts may run this module via `python -m aho.rag.bootstrap`, in which case
# the package is on sys.path. The fish wrapper sets sys.path explicitly.
from aho.rag import (
    _client,
    _collection_name,
    _get_or_create_collection,
    collection_count,
    index_artifact,
)


DEFAULT_PROJECT = os.environ.get("AHO_PROJECT", "ahomw")


# Glob patterns per amendment §D2. All paths relative to project root.
CANONICAL_GLOBS: List[Tuple[str, str, str]] = [
    # (glob_pattern, default_iteration_if_unresolved, default_workstream_if_unresolved)
    ("artifacts/iterations/*/carry-forwards-*.md", "", "carry-forwards"),
    ("artifacts/iterations/*/aho-plan-*.md",       "", "iteration-doc"),
    ("artifacts/iterations/*/W*-close-note.md",     "", ""),
    ("artifacts/iterations/*/iteration-close-*.md", "", "iteration-close"),
    ("artifacts/adrs/*.md",                          "adr", "adr"),
    ("docs/retrospectives/*.md",                     "retrospective", "retrospective"),
]


@dataclass
class ArtifactPlan:
    path: Path
    iteration: str
    workstream: str
    size_bytes: int
    estimated_chunks: int


@dataclass
class BootstrapResult:
    project: str
    mode: str                       # "dry_run" | "execute" | "rebuild"
    artifact_count: int = 0
    chunk_count_total: int = 0
    chunk_count_estimated: int = 0
    indexed_paths: List[str] = field(default_factory=list)
    skipped_paths: List[Dict[str, str]] = field(default_factory=list)
    started_at_utc: str = ""
    completed_at_utc: str = ""
    duration_seconds: float = 0.0
    collection_count_before: int = 0
    collection_count_after: int = 0


def _project_root() -> Path:
    # The aho package lives at <root>/src/aho/, so package_root.parent.parent is project root.
    return Path(__file__).resolve().parent.parent.parent.parent


def _resolve_iteration(p: Path, fallback: str) -> str:
    """Iteration ID lives in path component artifacts/iterations/<iter>/..."""
    parts = p.parts
    if "iterations" in parts:
        idx = parts.index("iterations")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return fallback or "unknown"


def _resolve_workstream(p: Path, fallback: str) -> str:
    """Workstream extracted from filename pattern. Examples:
    - W2-close-note.md → W2
    - iteration-close-0.2.17.md → iteration-close
    - aho-plan-0.3.1.md → iteration-doc
    """
    name = p.name
    # W<N>-close-note.md or W<N>-anything
    import re
    m = re.match(r"^(W\d+)[-.]", name)
    if m:
        return m.group(1)
    if name.startswith("iteration-close"):
        return "iteration-close"
    if name.startswith("carry-forwards"):
        return "carry-forwards"
    if name.startswith("aho-plan"):
        return "iteration-doc"
    return fallback or "unknown"


def _estimate_chunks(path: Path, chunk_size: int = 4000, overlap: int = 500) -> int:
    """Estimate chunk count via file size; matches aho.rag._chunk_text behavior."""
    try:
        n = path.stat().st_size
    except OSError:
        return 1
    if n <= chunk_size:
        return 1
    step = chunk_size - overlap
    return max(1, (n - overlap) // step + 1)


def discover_canonical_artifacts(project_root: Optional[Path] = None) -> List[ArtifactPlan]:
    """Glob the canonical artifact set; return one ArtifactPlan per file.

    Deduplicates: a file matching multiple globs is included once with the
    first-matching glob's default iteration/workstream as fallback.
    """
    root = project_root or _project_root()
    seen: Dict[Path, ArtifactPlan] = {}
    for pattern, default_iter, default_ws in CANONICAL_GLOBS:
        for p in sorted(root.glob(pattern)):
            if not p.is_file():
                continue
            if p in seen:
                continue
            iteration = _resolve_iteration(p, default_iter)
            workstream = _resolve_workstream(p, default_ws)
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            est_chunks = _estimate_chunks(p)
            seen[p] = ArtifactPlan(
                path=p,
                iteration=iteration,
                workstream=workstream,
                size_bytes=size,
                estimated_chunks=est_chunks,
            )
    return list(seen.values())


def _drop_collection(project: str) -> None:
    """Drop the per-project iteration-context collection. Idempotent."""
    client = _client()
    name = _collection_name(project)
    try:
        client.delete_collection(name=name)
    except Exception:  # noqa: BLE001 — chromadb raises NotFoundError or InvalidCollection
        pass


def bootstrap(
    *,
    project: str = DEFAULT_PROJECT,
    dry_run: bool = False,
    rebuild: bool = False,
    project_root: Optional[Path] = None,
    progress: bool = True,
) -> BootstrapResult:
    """Ingest the canonical artifact set into the project's iteration-context
    collection.

    dry_run: discover + report counts; do not embed or write.
    rebuild: drop existing collection first, then ingest.
    """
    if dry_run and rebuild:
        raise ValueError("dry_run and rebuild are mutually exclusive")

    mode = "dry_run" if dry_run else ("rebuild" if rebuild else "execute")
    t0 = time.monotonic()
    started_at = _utc_now()

    if rebuild:
        _drop_collection(project)

    count_before = collection_count(project) if not rebuild else 0
    plans = discover_canonical_artifacts(project_root)

    result = BootstrapResult(
        project=project,
        mode=mode,
        artifact_count=len(plans),
        chunk_count_estimated=sum(p.estimated_chunks for p in plans),
        collection_count_before=count_before,
        started_at_utc=started_at,
    )

    if dry_run:
        # Report only.
        for plan in plans:
            result.indexed_paths.append(str(plan.path))
        result.completed_at_utc = _utc_now()
        result.duration_seconds = time.monotonic() - t0
        result.collection_count_after = count_before
        return result

    # Execute path.
    total_chunks = 0
    for i, plan in enumerate(plans, start=1):
        if progress:
            print(
                f"[{i}/{len(plans)}] {plan.path.relative_to(project_root or _project_root())} "
                f"iter={plan.iteration} ws={plan.workstream} est_chunks={plan.estimated_chunks}",
                flush=True,
            )
        try:
            index_artifact(
                plan.path,
                project=project,
                iteration=plan.iteration,
                workstream=plan.workstream,
            )
            total_chunks += plan.estimated_chunks
            result.indexed_paths.append(str(plan.path))
        except Exception as exc:  # noqa: BLE001 — bootstrap-level boundary
            result.skipped_paths.append({
                "path": str(plan.path),
                "reason": f"{type(exc).__name__}: {exc}",
            })
            if progress:
                print(f"  SKIPPED: {type(exc).__name__}: {exc}", flush=True)

    result.chunk_count_total = total_chunks
    result.collection_count_after = collection_count(project)
    result.completed_at_utc = _utc_now()
    result.duration_seconds = time.monotonic() - t0
    return result


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Ingest canonical artifact set into per-project ChromaDB iteration-context collection. Closes F-0.3.1-W0-002."
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover + report planned ingestion shape; do not embed or write.",
    )
    ap.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop existing collection first, then ingest from scratch.",
    )
    ap.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help=f"Project name for collection (default: {DEFAULT_PROJECT} from $AHO_PROJECT).",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit result as JSON on stdout.",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-artifact progress prints during execute.",
    )
    args = ap.parse_args(argv)

    result = bootstrap(
        project=args.project,
        dry_run=args.dry_run,
        rebuild=args.rebuild,
        progress=not args.quiet,
    )

    if args.json:
        d = asdict(result)
        d["indexed_paths_count"] = len(result.indexed_paths)
        # Trim long indexed-paths list for compact JSON unless explicitly asked.
        if len(d["indexed_paths"]) > 5:
            d["indexed_paths"] = d["indexed_paths"][:5] + [f"… {len(result.indexed_paths) - 5} more"]
        print(json.dumps(d, indent=2))
    else:
        mode = result.mode
        print()
        print(f"aho-rag-bootstrap ({mode})  project={result.project}")
        print(f"  artifacts discovered:    {result.artifact_count}")
        print(f"  est. chunks (size-based): {result.chunk_count_estimated}")
        if mode == "dry_run":
            print(f"  collection count (frozen): {result.collection_count_before}")
            print(f"  duration: {result.duration_seconds:.1f}s")
            print("  (dry-run; no embedding or write performed)")
        else:
            print(f"  collection count before: {result.collection_count_before}")
            print(f"  collection count after:  {result.collection_count_after}")
            print(f"  artifacts indexed:       {len(result.indexed_paths)}")
            print(f"  artifacts skipped:       {len(result.skipped_paths)}")
            print(f"  duration: {result.duration_seconds:.1f}s")
            if result.skipped_paths:
                print(f"  skipped:")
                for s in result.skipped_paths:
                    print(f"    - {s['path']}: {s['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
