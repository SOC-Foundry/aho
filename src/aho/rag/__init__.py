"""aho.rag - retrieval-augmented context against host-mounted ChromaDB.

W2 entry points (replaces W1 placeholder):
- query(text, k=5, project=None) -> list of ranked retrievals
- index_artifact(path, project, iteration, workstream) -> document id
- seed_iteration_context(project, paths) -> bulk index helper

Storage: ChromaDB persistent client at AHO_CHROMA_DIR (default
`/var/lib/aho/chroma` per W1 Dockerfile VOLUME, falls back to
`~/.local/share/aho/chroma` on hosts where /var/lib/aho is unavailable).

Embedding: aho.council.embed (nomic-embed-text). Index and query share the
same embedding shape - required for honest similarity scoring.

Recency weighting: combines cosine similarity with an exponential decay on
`iteration_seq_ordinal`. The current iteration (`AHO_ITERATION` env) gets
weight 1.0; older iterations decay by SIMILARITY_WEIGHT / RECENCY_WEIGHT
mix per `query()`.
"""
from __future__ import annotations

import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.rag")
except ImportError:  # pragma: no cover
    _otel_trace = None
    _tracer = None

DEFAULT_CHROMA_DIR = "/var/lib/aho/chroma"
FALLBACK_CHROMA_DIR = str(Path.home() / ".local" / "share" / "aho" / "chroma")
COLLECTION_SUFFIX = "-iteration-context"
DEFAULT_K = 5
SIMILARITY_WEIGHT = 0.55
RECENCY_WEIGHT = 0.45

# Ordinal anchors - current iteration. Set per AHO_ITERATION at query time.
# Decay halves every DECAY_HALFLIFE_ITERATIONS *iteration ordinal units*.
# 0.2.17 vs 0.2.16 = 1 unit; 0.2.17 vs 0.1.13 = (0.2*1000+17) - (0.1*1000+13)
# = 200+17 - 100+13 = 104 units (most-recent-iteration dominance is desired).
DECAY_HALFLIFE_ITERATIONS = 4.0


class RagError(RuntimeError):
    pass


class RagInputError(ValueError):
    pass


class RagBackendUnavailable(RagError):
    """ChromaDB is not importable, or the storage path is not writable."""


# ---------------------------------------------------------------------------
# Storage / client
# ---------------------------------------------------------------------------

def chroma_dir() -> Path:
    override = os.environ.get("AHO_CHROMA_DIR")
    if override:
        return Path(override)
    primary = Path(DEFAULT_CHROMA_DIR)
    try:
        primary.mkdir(parents=True, exist_ok=True)
        return primary
    except (PermissionError, OSError):
        fallback = Path(FALLBACK_CHROMA_DIR)
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _client():
    try:
        import chromadb
    except ImportError as exc:
        raise RagBackendUnavailable(f"chromadb not importable: {exc}") from exc
    return chromadb.PersistentClient(path=str(chroma_dir()))


def _collection_name(project: str) -> str:
    if not isinstance(project, str) or not project:
        raise RagInputError("project must be a non-empty string")
    return f"{project}{COLLECTION_SUFFIX}"


def _get_or_create_collection(project: str):
    client = _client()
    name = _collection_name(project)
    return client.get_or_create_collection(
        name=name,
        metadata={"project": project, "schema": "iteration-context-v1"},
    )


# ---------------------------------------------------------------------------
# Iteration ordinal + recency
# ---------------------------------------------------------------------------

_ITER_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def parse_iteration_ordinal(iteration: str) -> int:
    """Convert iteration like '0.2.17' → integer ordinal usable for decay.
    Encoding: phase * 1_000_000 + iteration * 1_000 + run.
    Unparseable input → 0 (oldest). Logged via warning at higher layers.
    """
    if not isinstance(iteration, str):
        return 0
    m = _ITER_PATTERN.search(iteration)
    if not m:
        return 0
    phase, iter_num, run = (int(g) for g in m.groups())
    return phase * 1_000_000 + iter_num * 1_000 + run


def current_iteration_ordinal() -> int:
    return parse_iteration_ordinal(os.environ.get("AHO_ITERATION", ""))


def recency_weight(source_ordinal: int, current_ordinal: int) -> float:
    """Exponential decay: halflife of DECAY_HALFLIFE_ITERATIONS ordinal units.
    Source > current (future) is clamped to 1.0.
    """
    if source_ordinal >= current_ordinal:
        return 1.0
    delta = (current_ordinal - source_ordinal) / 1.0  # 1 unit per .x bump
    return math.pow(0.5, delta / DECAY_HALFLIFE_ITERATIONS)


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def _read_text_safely(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _doc_id(project: str, iteration: str, workstream: str, path: Path) -> str:
    # Include parent dir to disambiguate acceptance/W0.json from
    # audit/W0.json - both share path.name. Using parent.name only
    # (not full path) keeps ids stable across host moves.
    rel = f"{path.parent.name}/{path.name}"
    return f"{project}::{iteration}::{workstream}::{rel}"


def _embed_text(text: str) -> List[float]:
    from ..council.embed import embed
    return embed(text)["vector"]


def _emit_span(name: str, attrs: Dict[str, Any]) -> None:
    if _tracer is None:
        return
    with _tracer.start_as_current_span(name) as span:
        try:
            for k, v in attrs.items():
                span.set_attribute(k, v)
        except Exception:
            pass


def index_artifact(
    path: str | Path,
    *,
    project: str,
    iteration: str,
    workstream: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Index a single artifact into the project's iteration-context
    collection. Reads the file, embeds via nomic, writes with metadata.
    Returns the doc id assigned. Idempotent - re-indexing the same path
    overwrites the existing entry.
    """
    p = Path(path)
    if not p.exists():
        raise RagInputError(f"artifact path does not exist: {p}")
    if not p.is_file():
        raise RagInputError(f"artifact path is not a file: {p}")
    text = _read_text_safely(p)
    if not text.strip():
        raise RagInputError(f"artifact is empty: {p}")

    iteration_ord = parse_iteration_ordinal(iteration)
    base_doc_id = _doc_id(project, iteration, workstream, p)

    # Chunk longer artifacts. nomic-embed-text in Ollama 0.20 caps around
    # ~7000 chars for whitespace-heavy text and ~5000 for dense JSON.
    # We slice at 4000 with 500-char overlap so a single concept can land
    # in adjacent chunks without breaking similarity.
    chunks = _chunk_text(text, chunk_size=4000, overlap=500)

    indexed_utc = datetime.now(timezone.utc).isoformat()
    ids: List[str] = []
    embeddings: List[List[float]] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for chunk_idx, chunk_text in enumerate(chunks):
        chunk_id = (
            base_doc_id if len(chunks) == 1 else f"{base_doc_id}::chunk{chunk_idx:03d}"
        )
        try:
            vector = _embed_text(chunk_text)
        except Exception as exc:  # noqa: BLE001 - embed boundary
            raise RagError(
                f"embed failed for chunk {chunk_idx} of {p}: {exc}"
            ) from exc
        meta: Dict[str, Any] = {
            "project": project,
            "source_iteration": iteration,
            "source_workstream": workstream,
            "source_artifact_path": str(p),
            "source_artifact_name": p.name,
            "iteration_seq_ordinal": iteration_ord,
            "indexed_utc": indexed_utc,
            "snippet_length": len(chunk_text),
            "chunk_idx": chunk_idx,
            "chunk_count": len(chunks),
        }
        if extra_metadata:
            for k, v in extra_metadata.items():
                meta[str(k)] = v
        ids.append(chunk_id)
        embeddings.append(vector)
        documents.append(chunk_text)
        metadatas.append(meta)

    collection = _get_or_create_collection(project)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    _emit_span(
        "aho.rag.index_artifact",
        {
            "aho.rag.project": project,
            "aho.rag.iteration": iteration,
            "aho.rag.workstream": workstream,
            "aho.rag.path": str(p),
            "aho.rag.chunk_count": len(chunks),
            "aho.rag.iteration_seq_ordinal": iteration_ord,
        },
    )
    return base_doc_id


def _chunk_text(text: str, *, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        raise RagInputError(f"chunk_size must be > 0, got {chunk_size}")
    if overlap < 0 or overlap >= chunk_size:
        raise RagInputError(
            f"overlap must be in [0, chunk_size); got {overlap}"
        )
    if len(text) <= chunk_size:
        return [text]
    chunks: List[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += step
    return chunks


def seed_iteration_context(
    project: str,
    paths: Iterable[str | Path],
    *,
    iteration_resolver: Optional[callable] = None,
    workstream_resolver: Optional[callable] = None,
) -> Dict[str, Any]:
    """Bulk-index a set of paths. Resolvers infer (iteration, workstream)
    from each path; defaults extract from path components matching the
    standard layout artifacts/iterations/{iter}/{audit|acceptance}/{ws}.json.

    Returns {indexed: int, errors: list[dict]}.
    """
    iteration_resolver = iteration_resolver or _default_iteration_resolver
    workstream_resolver = workstream_resolver or _default_workstream_resolver

    indexed = 0
    errors: List[Dict[str, str]] = []
    for raw in paths:
        p = Path(raw)
        try:
            iteration = iteration_resolver(p) or "unknown"
            workstream = workstream_resolver(p) or "unknown"
            index_artifact(
                p,
                project=project,
                iteration=iteration,
                workstream=workstream,
            )
            indexed += 1
        except (RagInputError, RagError) as exc:
            errors.append({"path": str(p), "error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - bulk seed boundary
            errors.append({
                "path": str(p),
                "error": f"unexpected: {type(exc).__name__}: {exc}",
            })
    _emit_span(
        "aho.rag.seed_iteration_context",
        {
            "aho.rag.project": project,
            "aho.rag.indexed": indexed,
            "aho.rag.errors": len(errors),
        },
    )
    return {"indexed": indexed, "errors": errors}


def _default_iteration_resolver(p: Path) -> Optional[str]:
    parts = p.parts
    if "iterations" in parts:
        i = parts.index("iterations")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


def _default_workstream_resolver(p: Path) -> Optional[str]:
    # Matches W0.json, W1-amendment-b2-3.json, W0-close-note.md, etc.
    m = re.match(r"(W\d+)", p.name)
    if m:
        return m.group(1)
    # Fallback: aho-plan-X.Y.Z.md → "iteration-doc"
    if p.stem.startswith(("aho-plan", "aho-design", "carry-forwards",
                          "iteration-close", "retrospective")):
        return "iteration-doc"
    return None


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def query(
    text: str,
    *,
    k: int = DEFAULT_K,
    project: Optional[str] = None,
    apply_recency: bool = True,
) -> List[Dict[str, Any]]:
    """Retrieve top-k entries ranked by similarity * recency.

    Returns list of dicts with keys: id, score, similarity, recency,
    document, source_iteration, source_workstream, source_artifact_path,
    snippet, metadata.
    """
    if not isinstance(text, str) or not text.strip():
        raise RagInputError("query text must be a non-empty string")
    if not isinstance(k, int) or k < 1:
        raise RagInputError(f"k must be a positive integer, got {k!r}")
    if project is None:
        project = os.environ.get("AHO_PROJECT", "ahomw")
    collection = _get_or_create_collection(project)

    # Pull a larger candidate pool when recency-weighting so reordering
    # doesn't truncate good late-bloomers.
    pool = max(k, k * 4) if apply_recency else k

    query_vector = _embed_text(text)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(pool, max(collection.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )

    current_ord = current_iteration_ordinal()
    if current_ord == 0:
        # No AHO_ITERATION → use the highest ordinal seen in the snapshot
        # so recency still produces a meaningful ranking.
        current_ord = _max_ordinal_in_results(results)

    ranked: List[Dict[str, Any]] = []
    if not results.get("ids") or not results["ids"][0]:
        _emit_span(
            "aho.rag.query",
            {
                "aho.rag.project": project,
                "aho.rag.text_length": len(text),
                "aho.rag.results_count": 0,
                "aho.rag.applied_recency": apply_recency,
            },
        )
        return ranked

    for rid, doc, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = max(0.0, 1.0 - float(dist))
        meta = meta or {}
        source_ord = int(meta.get("iteration_seq_ordinal", 0))
        recency = recency_weight(source_ord, current_ord) if apply_recency else 1.0
        score = (
            SIMILARITY_WEIGHT * similarity + RECENCY_WEIGHT * recency
            if apply_recency
            else similarity
        )
        snippet = doc[:400] if isinstance(doc, str) else ""
        ranked.append({
            "id": rid,
            "score": score,
            "similarity": similarity,
            "recency": recency,
            "source_iteration": meta.get("source_iteration"),
            "source_workstream": meta.get("source_workstream"),
            "source_artifact_path": meta.get("source_artifact_path"),
            "snippet": snippet,
            "document": doc,
            "metadata": dict(meta),
        })

    ranked.sort(key=lambda r: r["score"], reverse=True)
    ranked = ranked[:k]
    _emit_span(
        "aho.rag.query",
        {
            "aho.rag.project": project,
            "aho.rag.text_length": len(text),
            "aho.rag.results_count": len(ranked),
            "aho.rag.applied_recency": apply_recency,
        },
    )
    return ranked


def _max_ordinal_in_results(results: Dict[str, Any]) -> int:
    metas = results.get("metadatas") or [[]]
    if not metas or not metas[0]:
        return 0
    return max(
        int((m or {}).get("iteration_seq_ordinal", 0))
        for m in metas[0]
    )


def collection_count(project: str) -> int:
    collection = _get_or_create_collection(project)
    return collection.count()


__all__ = [
    "query",
    "index_artifact",
    "seed_iteration_context",
    "collection_count",
    "chroma_dir",
    "parse_iteration_ordinal",
    "current_iteration_ordinal",
    "recency_weight",
    "RagError",
    "RagInputError",
    "RagBackendUnavailable",
    "DEFAULT_CHROMA_DIR",
    "FALLBACK_CHROMA_DIR",
    "COLLECTION_SUFFIX",
]
