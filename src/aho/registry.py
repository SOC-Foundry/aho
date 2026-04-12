#!/usr/bin/env python3
"""Query the project script registry. Path-agnostic via aho.paths."""
import os, json, sys, argparse
from pathlib import Path

from aho.paths import find_project_root, IaoProjectNotFound


def load_registry():
    try:
        root = find_project_root()
    except IaoProjectNotFound:
        return None
    p = root / "data" / "script_registry.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def query_gotchas(phase=None):
    try:
        root = find_project_root()
    except IaoProjectNotFound:
        return "Error: Project root not found."
    from aho.paths import get_registries_dir
    p = get_registries_dir() / ("gotcha" + "_archive.json")
    if not p.exists():
        return "Error: Gotcha archive not found."
    
    data = json.loads(p.read_text())
    gotchas = data.get("gotchas", [])
    
    # Filter by phase if requested (optional, assuming ID or title might contain it)
    # The current schema in gotcha_archive doesn't have a 'phase' field per gotcha,
    # but some have 'id': 'aho-Gxxx' or 'aho-Gxxx'.
    
    output = []
    output.append(f"Gotcha Registry - Phase {phase if phase is not None else 'All'}")
    output.append("-" * 60)
    for g in gotchas:
        output.append(f"[{g.get('id', 'N/A')}] {g.get('title', 'Untitled')}")
        output.append(f"Pattern: {g.get('pattern', g.get('description', 'N/A'))}")
        output.append(f"Mitigation: {g.get('mitigation', g.get('fix', 'N/A'))}")
        output.append("-" * 60)
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Query project script registry")
    parser.add_argument("query", nargs="?", help="Topic/keyword search in path/purpose")
    parser.add_argument("--pipeline", help="Filter by pipeline")
    parser.add_argument("--writes-checkpoint", action="store_true")
    parser.add_argument("--linked-gotcha", help="Filter by linked gotcha ID")
    parser.add_argument("--raw", action="store_true")
    args = parser.parse_args()

    reg = load_registry()
    if not reg:
        print("Error: Registry not found (set IAO_PROJECT_ROOT or cd into project)")
        sys.exit(1)

    results = []
    for s in reg.get("scripts", []):
        match = True
        if args.query:
            q = args.query.lower()
            if q not in s["path"].lower() and q not in s.get("purpose", "").lower():
                match = False
        if args.pipeline and s.get("pipeline") != args.pipeline:
            match = False
        if args.writes_checkpoint and not any("checkpoint" in o.lower() for o in s.get("outputs", [])):
            match = False
        if args.linked_gotcha and args.linked_gotcha not in s.get("linked_gotchas", []):
            match = False
        if match:
            results.append(s)

    if not results:
        print("No scripts matching query found.")
        sys.exit(0)

    if args.raw:
        print(json.dumps(results, indent=2))
    else:
        print(f"Found {len(results)} scripts:")
        print("-" * 60)
        for s in results:
            print(f"Path:    {s['path']}")
            print(f"Purpose: {s.get('purpose', '')}")
            if s.get("pipeline") != "none":
                print(f"Pipeline: {s.get('pipeline')}")
            if s.get("inputs"):
                print(f"Inputs:  {', '.join(s['inputs'])}")
            if s.get("outputs"):
                print(f"Outputs: {', '.join(s['outputs'])}")
            print("-" * 60)


if __name__ == "__main__":
    main()
