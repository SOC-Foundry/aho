"""W2 D1 pre-seed probe - index sealed 0.2.16 W0–W4 + 0.2.17 W0/W1.

Run from repo root with AHO_CHROMA_DIR set to the host-side dev path
(or unset to use /var/lib/aho/chroma → ~/.local/share/aho/chroma fallback).

Output:
    indexed N artifacts; 0 errors
    collection size: M
    expected size: M
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ITER_ROOT = ROOT / "artifacts" / "iterations"

EXPECTED_PATHS: list[Path] = []

# 0.2.16 W0-W4 sealed acceptance + audit
for ws in ("W0", "W1", "W2", "W3", "W4"):
    EXPECTED_PATHS.append(ITER_ROOT / "0.2.16" / "acceptance" / f"{ws}.json")
    EXPECTED_PATHS.append(ITER_ROOT / "0.2.16" / "audit" / f"{ws}.json")

# 0.2.16 iteration-level docs
for fname in (
    "carry-forwards-0.2.16.md",
    "aho-plan-0.2.16.md",
    "aho-design-0.2.16.md",
    "iteration-close-0.2.16.md",
    "retrospective-0.2.16.md",
):
    EXPECTED_PATHS.append(ITER_ROOT / "0.2.16" / fname)

# 0.2.17 W0 sealed acceptance + amendment + audit
EXPECTED_PATHS.extend([
    ITER_ROOT / "0.2.17" / "acceptance" / "W0.json",
    ITER_ROOT / "0.2.17" / "acceptance" / "W0-amendment-b2-3.json",
    ITER_ROOT / "0.2.17" / "audit" / "W0.json",
    ITER_ROOT / "0.2.17" / "W0-close-note.md",
])

# 0.2.17 W1 sealed acceptance + audit + close
EXPECTED_PATHS.extend([
    ITER_ROOT / "0.2.17" / "acceptance" / "W1.json",
    ITER_ROOT / "0.2.17" / "audit" / "W1.json",
    ITER_ROOT / "0.2.17" / "W1-close-note.md",
])

# 0.2.17 plan + W1 plan + W2 plan
EXPECTED_PATHS.extend([
    ITER_ROOT / "0.2.17" / "aho-plan-0.2.17.md",
    ITER_ROOT / "0.2.17" / "W1-plan-doc.md",
    ITER_ROOT / "0.2.17" / "W2-plan-doc.md",
])


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from aho.rag import seed_iteration_context, collection_count

    project = "ahomw"
    missing = [p for p in EXPECTED_PATHS if not p.exists()]
    if missing:
        print(f"missing {len(missing)} expected paths:")
        for p in missing:
            print(f"  {p}")
        return 2

    result = seed_iteration_context(project, EXPECTED_PATHS)
    print(f"indexed {result['indexed']} artifacts; {len(result['errors'])} errors")
    if result["errors"]:
        for e in result["errors"]:
            print(f"  ERR {e['path']}: {e['error']}")
    count = collection_count(project)
    print(f"collection size: {count}")
    print(f"expected size: {len(EXPECTED_PATHS)}")
    return 0 if result["indexed"] == len(EXPECTED_PATHS) else 1


if __name__ == "__main__":
    sys.exit(main())
