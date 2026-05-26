"""council.audit_ref_lookup - RAG retrieval per detected audit reference.

Step 2 of the W3 reference-resolution pipeline. D1 detects reference-shaped
tokens. D2 (this module) queries `aho.rag` for each detected reference
against the project's iteration-context collection, then returns a
structured result per reference for the auditor prompt to consume.

Per the plan doc:
- k=3 retrievals per reference.
- Zero retrievals → mark `unverified` (the auditor flags for verification
  rather than auto-flagging as fake).
- Backend failure (chromadb missing, embed unreachable) RAISES - silent
  pass-through would defeat the load-bearing fix from F-0.2.17-W2-006.

The returned shape is per-reference (so the prompt can render
ID + status + top-1 snippet). A coalesced retrieval set is also computed
(unique chunk-id → list of references that hit it) for any callers that
want a flatter view.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .audit_ref_extract import DetectedRef
from ..rag import (
    RagBackendUnavailable,
    RagError,
    RagInputError,
    query as rag_query,
)


DEFAULT_K_PER_REF = 3
# Pool multiplier - RAG returns top-k by cosine similarity for arbitrary
# text, but for opaque reference IDs (`F-0.2.17-W0-001`) embedding
# similarity is low signal: every query returns *something*, regardless
# of whether the ID is actually in the corpus. We pull a wider pool then
# filter to retrievals whose document contains the literal reference ID.
# This is what makes the `unverified` status meaningful - without literal
# substring filtering, the spurious-ID acceptance gate cannot fail.
DEFAULT_POOL_MULTIPLIER = 8
SNIPPET_PROMPT_LEN = 200


class RefLookupError(RuntimeError):
    """RAG retrieval failed in a way that must surface to the auditor."""


class RefLookupResult(dict):
    """Per-reference lookup result. Shape:

    {
        "id": "F-0.2.17-W0-003",
        "kind": "carry_forward_full",
        "status": "registered" | "unverified",
        "retrievals": [
            {
                "chunk_id": str,
                "score": float,
                "similarity": float,
                "recency": float,
                "source_iteration": str,
                "source_workstream": str,
                "source_artifact_path": str,
                "snippet": str,  # truncated to SNIPPET_PROMPT_LEN
            },
            ...
        ],
    }
    """


def _truncate(text: str, n: int = SNIPPET_PROMPT_LEN) -> str:
    if not isinstance(text, str):
        return ""
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _snippet_around_match(
    document: Optional[str],
    variants: Sequence[str],
    *,
    width: int = SNIPPET_PROMPT_LEN,
) -> str:
    """Return a window of `document` centred on the first variant match.
    Falls back to the head of the document if no variant matches (which
    shouldn't happen on the registered path because the caller filters
    on substring presence first, but this keeps the function defensible).
    """
    if not isinstance(document, str) or not document:
        return ""
    idx = -1
    matched_len = 0
    for v in variants:
        i = document.find(v)
        if i != -1:
            idx = i
            matched_len = len(v)
            break
    if idx == -1:
        return _truncate(document, width)
    half = max((width - matched_len) // 2, 0)
    start = max(0, idx - half)
    end = min(len(document), idx + matched_len + half)
    snippet = document[start:end]
    if start > 0:
        snippet = "…" + snippet.lstrip()
    if end < len(document):
        snippet = snippet.rstrip() + "…"
    return snippet


def _normalise_retrieval(
    raw: Dict[str, Any],
    *,
    snippet_variants: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    if snippet_variants:
        snippet = _snippet_around_match(raw.get("document"), snippet_variants)
    else:
        snippet = _truncate(raw.get("snippet") or "")
    return {
        "chunk_id": raw.get("id"),
        "score": float(raw.get("score", 0.0)),
        "similarity": float(raw.get("similarity", 0.0)),
        "recency": float(raw.get("recency", 0.0)),
        "source_iteration": raw.get("source_iteration"),
        "source_workstream": raw.get("source_workstream"),
        "source_artifact_path": raw.get("source_artifact_path"),
        "snippet": snippet,
    }


def _id_search_variants(ref: DetectedRef) -> List[str]:
    """Surface forms to look for in retrieved documents. ADR is the only
    family with two written forms (`ADR 0007` and `ADR-0007`); the rest
    have a single canonical surface form so the canonical string is the
    sole variant.
    """
    if ref.kind == "adr" and ref.id.startswith("ADR-"):
        return [ref.id, ref.id.replace("ADR-", "ADR ", 1)]
    return [ref.id]


def _document_contains_ref(document: Optional[str], ref: DetectedRef) -> bool:
    if not isinstance(document, str) or not document:
        return False
    return any(variant in document for variant in _id_search_variants(ref))


def lookup_references(
    refs: Sequence[DetectedRef],
    *,
    k: int = DEFAULT_K_PER_REF,
    project: Optional[str] = None,
) -> List[RefLookupResult]:
    """Query the RAG store for each detected reference. Returns one
    RefLookupResult per input reference, in input order.

    `project` defaults to env (`AHO_PROJECT`) → `ahomw`, matching the
    `aho.rag.query` default.

    Raises RefLookupError on backend failure. A reference with zero
    retrievals is marked `unverified`, NOT raised - that path is the
    explicit auditor signal "ID looks shaped right but is not in the
    iteration-context collection."
    """
    if not isinstance(refs, (list, tuple)):
        raise RefLookupError(
            f"refs must be a sequence, got {type(refs).__name__}"
        )
    if not isinstance(k, int) or k < 1:
        raise RefLookupError(f"k must be a positive int, got {k!r}")

    out: List[RefLookupResult] = []
    for ref in refs:
        if not isinstance(ref, DetectedRef):
            raise RefLookupError(
                f"refs entry must be DetectedRef, got {type(ref).__name__}"
            )
        pool = max(k * DEFAULT_POOL_MULTIPLIER, k)
        try:
            raw = rag_query(ref.id, k=pool, project=project)
        except RagBackendUnavailable as exc:
            raise RefLookupError(
                f"RAG backend unavailable while looking up {ref.id!r}: {exc}"
            ) from exc
        except (RagInputError, RagError) as exc:
            raise RefLookupError(
                f"RAG retrieval failed for {ref.id!r}: {exc}"
            ) from exc

        # Filter to retrievals that literally contain the reference ID.
        # Embedding similarity for opaque IDs is too noisy to define
        # "registered" - substring presence is the load-bearing signal.
        variants = _id_search_variants(ref)
        filtered = [
            _normalise_retrieval(r, snippet_variants=variants)
            for r in raw
            if _document_contains_ref(r.get("document"), ref)
        ]
        retrievals = filtered[:k]
        status = "registered" if retrievals else "unverified"
        out.append(
            RefLookupResult(
                id=ref.id,
                kind=ref.kind,
                status=status,
                retrievals=retrievals,
            )
        )
    return out


def coalesce_retrievals(
    results: Sequence[RefLookupResult],
) -> List[Dict[str, Any]]:
    """Flatten per-reference results into a unique-chunk view. Each entry:

    {
        "chunk_id": str,
        "matched_by": [reference_ids...],
        "score": float (max across matches),
        "snippet": str,
        "source_iteration": str,
        "source_workstream": str,
        "source_artifact_path": str,
    }

    Sorted by descending max-score. Useful for diagnostics and for any
    flatter prompt formatter that wants to deduplicate across references.
    """
    by_chunk: Dict[str, Dict[str, Any]] = {}
    for r in results:
        for retrieval in r.get("retrievals", []):
            cid = retrieval["chunk_id"]
            entry = by_chunk.get(cid)
            if entry is None:
                entry = {
                    "chunk_id": cid,
                    "matched_by": [r["id"]],
                    "score": retrieval["score"],
                    "snippet": retrieval["snippet"],
                    "source_iteration": retrieval["source_iteration"],
                    "source_workstream": retrieval["source_workstream"],
                    "source_artifact_path": retrieval["source_artifact_path"],
                }
                by_chunk[cid] = entry
            else:
                if r["id"] not in entry["matched_by"]:
                    entry["matched_by"].append(r["id"])
                if retrieval["score"] > entry["score"]:
                    entry["score"] = retrieval["score"]
    return sorted(by_chunk.values(), key=lambda e: e["score"], reverse=True)


__all__ = [
    "lookup_references",
    "coalesce_retrievals",
    "RefLookupResult",
    "RefLookupError",
    "DEFAULT_K_PER_REF",
    "SNIPPET_PROMPT_LEN",
]
