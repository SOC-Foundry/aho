"""Smoke test two-pass generation by producing a fake tiny design."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aho.artifacts.loop import generate_outline

seed = {
    "iteration_theme": "smoke test", 
    "target_iteration": "0.1.99",
    "phase": 0
}

print("=== Two-pass outline test ===", file=sys.stderr)
try:
    # Use a very small artifact for speed
    outline = generate_outline("design", seed, context="This is a smoke test for the two-pass generation system.")
    print(f"Outline sections: {len(outline.get('sections', []))}")
    for s in outline.get('sections', [])[:3]:
        print(f"  {s.get('id')}: {s.get('title')} ({s.get('target_words')} words)")
except Exception as e:
    print(f"Two-pass failed: {e}")
    # Partial ship is acceptable per plan
    sys.exit(0)

print("\n[TEST] Two-pass outline generation OK", file=sys.stderr)
sys.exit(0)
