"""ChromaDB archive collections for aho consumer projects.

Each project gets a collection {project_code}_archive populated from
artifacts/iterations/ with nomic-embed-text embeddings.
"""
import json
import hashlib
import re
from pathlib import Path
from typing import Iterable, Optional

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

CHROMADB_PATH = Path.home() / ".local/share/aho/chromadb"


def _get_client():
    if chromadb is None:
        raise RuntimeError("chromadb not installed; pip install chromadb")
    CHROMADB_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMADB_PATH))


def _get_embedder():
    return embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text",
    )


def seed_project_archive(project_code: str, project_path: Path) -> int:
    """Seed or re-seed a project's archive collection.

    Returns the number of documents added.
    """
    client = _get_client()
    embedder = _get_embedder()
    collection_name = f"{project_code}_archive"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedder,
    )

    docs = []
    ids = []
    metas = []

    def _process_file(md_file: Path, iteration: str):
        try:
            content = md_file.read_text(errors="ignore")
            if len(content) < 500:
                return
            doc_id = hashlib.sha256(f"{project_code}:{iteration}:{md_file.name}".encode()).hexdigest()[:16]
            if doc_id in ids:
                return
            docs.append(content[:4000])
            ids.append(doc_id)
            metas.append({
                "project_code": project_code,
                "iteration": iteration,
                "filename": md_file.name,
                "artifact_type": md_file.stem.replace(f"{project_code.rstrip('w')}-", "").split("-")[0],
            })
        except Exception:
            pass

    # Search in artifacts/iterations/ (aho style)
    from aho.paths import get_iterations_dir
    iterations_dir = get_iterations_dir()
    if iterations_dir.exists():
        for iter_dir in sorted(iterations_dir.iterdir()):
            if not iter_dir.is_dir():
                continue
            iteration = iter_dir.name
            for md_file in iter_dir.glob("*.md"):
                _process_file(md_file, iteration)

    # Search in artifacts/ (flat style fallback)
    from aho.paths import get_artifacts_root
    for flat_dir in [get_artifacts_root()]:
        if flat_dir.exists():
            for md_file in flat_dir.glob("*.md"):
                m = re.search(r"[vV]?(\d+\.\d+(\.\d+)*)", md_file.name)
                iteration = m.group(1) if m else "unknown"
                _process_file(md_file, iteration)

    if docs:
        collection.add(documents=docs, ids=ids, metadatas=metas)
    return len(docs)


def query_archive(
    project_code: str, 
    query: str, 
    top_k: int = 5, 
    prefer_recent: bool = True,
    forbidden_substrings: Optional[Iterable[str]] = None
) -> list[dict]:
    """Query with optional recency weighting and forbidden content filtering."""
    if forbidden_substrings is None:
        forbidden_substrings = ["ahomw-Pillar-", "split-agent"]

    client = _get_client()
    collection_name = f"{project_code}_archive"
    try:
        collection = client.get_collection(collection_name, embedding_function=_get_embedder())
    except Exception:
        return []
    
    pool_size = top_k * 5 if forbidden_substrings else (top_k * 3 if prefer_recent else top_k)
    results = collection.query(query_texts=[query], n_results=pool_size)
    
    output = []
    if results["ids"] and results["ids"][0]:
        for i, d, m, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            is_forbidden = False
            for sub in forbidden_substrings:
                if sub in d:
                    is_forbidden = True
                    break
            if is_forbidden:
                continue

            similarity = max(0.0, 1.0 - dist)
            iteration = m.get("iteration", "0.0.0")
            recency = _recency_score(iteration)
            score = 0.6 * similarity + 0.4 * recency if prefer_recent else similarity
            output.append({
                "id": i, 
                "document": d, 
                "metadata": m, 
                "similarity": similarity,
                "recency": recency,
                "score": score
            })
            
    if prefer_recent:
        output.sort(key=lambda x: x["score"], reverse=True)
        return output[:top_k]
    return output


_RECENCY_MAP = {
    "0.1.13": 1.00,
    "0.1.12": 0.98,
    "0.1.7": 0.90,
    "0.1.4": 0.85,
}


def _recency_score(iteration: str) -> float:
    v = iteration.lstrip("v")
    return _RECENCY_MAP.get(v, 0.30)


def list_archives() -> dict[str, int]:
    """List all known archives with document counts."""
    client = _get_client()
    archives = {}
    for coll in client.list_collections():
        name = coll.name
        if name.endswith("_archive"):
            archives[name] = coll.count()
    return archives
