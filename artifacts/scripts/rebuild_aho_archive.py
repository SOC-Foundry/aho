#!/usr/bin/env python3
"""Rebuild the ChromaDB archive as `aho_archive` from a filtered source.
Excludes diagnostic appendices and historical iteration docs.
"""
import re
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

SOURCE_DIRS = [
    "docs/harness",
    "docs/phase-charters",
    "docs/roadmap",
    "docs/adrs",
]
SOURCE_FILES = [
    "docs/iterations/0.1.8/iao-design-0.1.8.md",
    "docs/iterations/0.1.8/iao-plan-0.1.8.md",
    "docs/iterations/0.1.9/iao-design-0.1.9.md",
    "docs/iterations/0.1.9/iao-plan-0.1.9.md",
]

DIAGNOSTIC_HEADER_RE = re.compile(
    r"^##\s+(Appendix\s+[A-Z]|Diagnostic|Exhibit)",
    re.MULTILINE,
)

def strip_diagnostic_appendices(text: str) -> str:
    """Remove any section whose header matches DIAGNOSTIC_HEADER_RE, up to the next H2."""
    match = DIAGNOSTIC_HEADER_RE.search(text)
    if not match:
        return text
    before = text[: match.start()]
    after_start = match.end()
    next_h2 = re.search(r"^##\s+", text[after_start:], re.MULTILINE)
    if next_h2:
        after = text[after_start + next_h2.start() :]
        return strip_diagnostic_appendices(before + after)
    else:
        return before

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def collect_source_docs() -> list[tuple[Path, str]]:
    docs = []
    for d in SOURCE_DIRS:
        p = Path(d)
        if not p.exists(): continue
        for f in p.rglob("*.md"):
            docs.append((f, f.read_text(encoding="utf-8")))
    for f in SOURCE_FILES:
        p = Path(f)
        if p.exists():
            docs.append((p, p.read_text(encoding="utf-8")))
    return docs

def main():
    client = chromadb.PersistentClient(path="data/chroma")
    embedding_fn = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text",
    )

    temp_name = "aho_archive_new"
    try:
        client.delete_collection(temp_name)
    except Exception:
        pass
    new_col = client.create_collection(
        name=temp_name,
        embedding_function=embedding_fn,
    )

    docs = collect_source_docs()
    print(f"Collected {len(docs)} source documents")

    ids = []
    contents = []
    metadatas = []
    for path, raw in docs:
        filtered = strip_diagnostic_appendices(raw)
        chunks = chunk_text(filtered)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{path.as_posix()}#chunk-{i}"
            ids.append(chunk_id)
            contents.append(chunk)
            metadatas.append({
                "source_file": path.as_posix(),
                "chunk_index": i,
                "source_iteration": "0.1.9",
                "chunk_type": "harness" if "docs/harness" in path.as_posix() else "iteration_doc",
            })

    if contents:
        new_col.add(ids=ids, documents=contents, metadatas=metadatas)
    print(f"Added {len(contents)} chunks to {temp_name}")

    if new_col.count() == 0:
        raise SystemExit(f"ERROR: {temp_name} has 0 documents — aborting")

    # Smoke-check: focus on harness docs
    results = new_col.query(query_texts=["pillar"], n_results=20, include=["documents", "metadatas"])
    for doc, meta in zip(results.get("documents", [[]])[0], results.get("metadatas", [[]])[0]):
        if ("ahomw-Pillar-" in doc or "split-agent" in doc) and meta.get("chunk_type") == "harness":
             raise SystemExit(f"ERROR: {temp_name} still contains retired patterns in HARNESS — rebuild filter failed. Source: {meta.get('source_file')}")

    try:
        client.delete_collection("aho_archive")
        print("Deleted aho_archive")
    except Exception as e:
        print(f"Warning: could not delete aho_archive: {e}")

    final_col = client.create_collection(
        name="aho_archive",
        embedding_function=embedding_fn,
    )
    all_data = new_col.get()
    if all_data["ids"]:
        batch_size = 100
        for i in range(0, len(all_data["ids"]), batch_size):
            final_col.add(
                ids=all_data["ids"][i:i+batch_size],
                documents=all_data["documents"][i:i+batch_size],
                metadatas=all_data["metadatas"][i:i+batch_size],
            )
    client.delete_collection(temp_name)
    print(f"Created aho_archive with {final_col.count()} documents")

if __name__ == "__main__":
    main()
