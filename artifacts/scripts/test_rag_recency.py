"""Verify RAG recency weighting promotes 0.1.4 content over 0.1.2 content."""
from aho.rag.archive import query_archive

query = "artifact loop workstream structure"

print("=== Without recency preference ===")
results = query_archive("ahomw", query, top_k=5, prefer_recent=False)
for r in results:
    # results from prefer_recent=False use old distance-only return format
    # wait, my new implementation returns the same dict for both but different count
    # let's check
    print(f"  {r['metadata'].get('iteration', '?')} / {r['metadata'].get('filename', '?')}")

print("\n=== With recency preference ===")
results = query_archive("ahomw", query, top_k=5, prefer_recent=True)
for r in results:
    print(f"  {r['metadata'].get('iteration', '?')} / {r['metadata'].get('filename', '?')}  (sim={r['similarity']:.2f} rec={r['recency']:.2f} score={r['score']:.2f})")
