#!/usr/bin/env python3
"""Semantic search over aho archive via ChromaDB + nomic-embed-text. Generalized from kjtcom."""
import os
import sys
import json
import time
import requests
import chromadb
from pathlib import Path

from aho.paths import find_project_root
from aho.logger import log_event

# Configuration
try:
    PROJECT_ROOT = find_project_root()
    PROJECT_NAME = os.environ.get("AHO_PROJECT_NAME", os.environ.get("IAO_PROJECT_NAME", PROJECT_ROOT.name)
except Exception:
    PROJECT_ROOT = Path.cwd()
    PROJECT_NAME = "unknown"

CHROMA_DIR = str(PROJECT_ROOT / "data" / "chromadb")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/embed")
MODEL = 'nomic-embed-text'
COLLECTION_NAME = f"{PROJECT_NAME}_archive"

def get_embedding(text):
    """Get embedding for a single query."""
    start = time.time()
    resp = requests.post(OLLAMA_URL, json={
        'model': MODEL,
        'input': [text]
    }, timeout=30)
    resp.raise_for_status()
    latency = int((time.time() - start) * 1000)
    
    agent = os.environ.get("AHO_AGENT", os.environ.get("IAO_AGENT", "aho-cli"))
    log_event("llm_call", agent, MODEL, "embed",
              input_summary=text[:200],
              output_summary="1 embedding returned",
              latency_ms=latency, status="success")
    return resp.json()['embeddings'][0]


def query(text, n_results=5, version_filter=None):
    """Search ChromaDB for chunks matching the query."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    embedding = get_embedding(text)

    where_filter = None
    if version_filter:
        where_filter = {'version': version_filter}

    start = time.time()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where_filter,
        include=['documents', 'metadatas', 'distances']
    )
    latency = int((time.time() - start) * 1000)
    
    agent = os.environ.get("AHO_AGENT", os.environ.get("IAO_AGENT", "aho-cli"))
    log_event("api_call", agent, "chromadb", "query",
              input_summary=text[:200],
              output_summary=f"{len(results['ids'][0])} results returned",
              latency_ms=latency, status="success")

    return results


def main(args=None):
    if args is None:
        if len(sys.argv) < 2:
            print('Usage: aho rag query "your question" [n_results] [version_filter]')
            sys.exit(1)
        q = sys.argv[1]
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        version = sys.argv[3] if len(sys.argv) > 3 else None
        output_json = '--json' in sys.argv
    else:
        q = args.query
        n = args.n_results
        version = args.version_filter
        output_json = getattr(args, 'json', False)

    print(f'Query: "{q}" (top {n})')
    if version:
        print(f'Filter: version={version}')
    print('---')

    try:
        results = query(q, n_results=n, version_filter=version)
    except Exception as e:
        print(f"ERROR: {e}")
        return # Don't exit if called from CLI

    for i in range(len(results['ids'][0])):
        doc_id = results['ids'][0][i]
        distance = results['distances'][0][i]
        meta = results['metadatas'][0][i]
        doc = results['documents'][0][i]

        print(f'\n[{i+1}] Score: {1 - distance:.3f} | {meta.get("filename", "?")} '
              f'| {meta.get("version", "?")} | {meta.get("file_type", "?")}')
        print(f'    {doc[:200]}...' if len(doc) > 200 else f'    {doc}')

    # Also output as JSON for programmatic use
    if output_json:
        output = []
        for i in range(len(results['ids'][0])):
            output.append({
                'id': results['ids'][0][i],
                'score': 1 - results['distances'][0][i],
                'metadata': results['metadatas'][0][i],
                'text': results['documents'][0][i]
            })
        print('\n---JSON---')
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
