"""Context enrichment for artifact generation via RAG."""
import json
from pathlib import Path
from aho.rag.archive import query_archive


def get_rag_context(project_code: str, artifact_type: str, iteration: str) -> str:
    """Retrieve relevant archive snippets for the current artifact task."""
    query = f"{artifact_type} for iteration {iteration}"
    results = query_archive(project_code, query, top_k=3, prefer_recent=True)
    
    if not results:
        return ""
        
    lines = ["## RAG Enrichment Context", ""]
    for res in results:
        meta = res["metadata"]
        lines.append(f"### Source: {meta.get('filename')} (Iter {meta.get('iteration')})")
        lines.append(res["document"][:1000])
        lines.append("")
    return "\n".join(lines)


def build_full_context(project_code: str, artifact_type: str, iteration: str, base_context: str = "") -> str:
    """Build the full prompt context including RAG and base artifacts."""
    rag_context = get_rag_context(project_code, artifact_type, iteration)
    return f"{base_context}\n\n{rag_context}"
