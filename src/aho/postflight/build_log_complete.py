#!/usr/bin/env python3
"""Build log completeness post-flight check. (ADR-042, 0.1.9)"""
import os
import re
import json
from pathlib import Path

def check(iteration=None):
    """ADR-042: Verify manual build log contains all workstreams from design."""
    if not iteration:
        iteration = os.environ.get("AHO_ITERATION", os.environ.get("IAO_ITERATION", "unknown"))
        
    from aho.paths import find_project_root
    try:
        root = find_project_root()
        aho_json = root / ".aho.json"
        prefix = "aho"
        if aho_json.exists():
            config = json.loads(aho_json.read_text())
            prefix = config.get("artifact_prefix") or config.get("name") or config.get("project_code") or "aho"
    except Exception:
        root = Path.cwd()
        prefix = "aho"
        
    # Resolve iteration directory
    parts = iteration.split(".")
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
    iter_dir = root / "artifacts" / "iterations" / version
    if not iter_dir.exists():
        # Fallback to root docs for legacy or phase-level checks
        iter_dir = root / "docs"

    # 1. Resolve design path
    design_path = None
    planning_iter = f"{parts[0]}.{parts[1]}.0" if len(parts) >= 3 else iteration
    
    # Try current iteration dir first, then parent docs
    search_paths = [
        iter_dir / f"{prefix}-design-{iteration}.md",
        iter_dir / f"{prefix}-design-{planning_iter}.md",
        root / "docs" / f"{prefix}-design-{iteration}.md",
        root / "docs" / f"{prefix}-design-{planning_iter}.md",
    ]
    
    for p in search_paths:
        if p.exists():
            design_path = p
            break

    if not design_path:
        return ("warn", "design doc not found, skipping completeness check")

    # 2. Extract workstream IDs from design
    design_text = design_path.read_text()
    # Matches ## W0, ### W1, etc.
    expected_ids = re.findall(r'^##+ (W\d+[a-z]?)', design_text, re.MULTILINE)
    if not expected_ids:
        return ("ok", "no workstreams found in design")

    # 3. Find build log (ADR-042: manual build log is authoritative)
    manual_path = iter_dir / f"{prefix}-build-log-{iteration}.md"
    if not manual_path.exists():
        # Try without -log suffix for legacy
        manual_path = iter_dir / f"{prefix}-build-{iteration}.md"
        if not manual_path.exists():
            return ("fail", f"manual build log missing at {prefix}-build-log-{iteration}.md")

    # 4. Check for workstream headers in build log
    build_text = manual_path.read_text()
    missing = []
    for wid in expected_ids:
        if not re.search(rf'^##+ {wid}\b', build_text, re.MULTILINE):
            missing.append(wid)
            
    if missing:
        return ("fail", f"missing workstreams in manual build log: {', '.join(missing)}")
    
    # Optional: check if synthesis exists (informative)
    synthesis_path = iter_dir / f"{prefix}-build-log-synthesis-{iteration}.md"
    status_msg = f"all {len(expected_ids)} workstreams logged in manual file"
    if synthesis_path.exists():
        status_msg += " (synthesis present)"
        
    return ("ok", status_msg)

if __name__ == "__main__":
    status, msg = check()
    print(f"  {status.upper()}: build_log_complete ({msg})")
