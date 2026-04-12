#!/usr/bin/env python3
"""Artifact enforcement post-flight check. (G61, ADR-019)"""
import os
import json
from pathlib import Path
from aho.paths import find_project_root, get_iterations_dir

def check(iteration=None):
    """ADR-019/G103: Verify all 3 artifacts (build, report, bundle) are present."""
    base_dir = Path.cwd()
    try:
        base_dir = find_project_root()
    except Exception:
        pass

    if not iteration:
        iteration = os.environ.get("AHO_ITERATION", os.environ.get("IAO_ITERATION"))
        if not iteration:
            try:
                aho_json = base_dir / ".aho.json"
                if aho_json.exists():
                    iteration = json.loads(aho_json.read_text()).get("current_iteration")
            except Exception:
                pass
        if not iteration:
            iteration = "unknown"
        
    try:
        config_path = base_dir / ".aho.json"
        config = json.loads(config_path.read_text())
        project = config.get("artifact_prefix") or config.get("project_code") or "aho"
        bundle_kind = config.get("bundle_format", "bundle")
    except Exception:
        base_dir = Path.cwd()
        project = "aho"
        bundle_kind = "bundle"
        
    failures = []
    # Primary artifacts: build, report, bundle (base)
    # aho 0.1.13: artifacts live in artifacts/iterations/<version>/
    parts = iteration.split('.')
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
    iter_dir = get_iterations_dir() / version

    for atype in ["build", "report", bundle_kind]:
        # Handle naming variants: build/build-log, report/run
        atypes = [atype]
        if atype == "build":
            atypes.append("build-log")
        elif atype == "report":
            atypes.append("run")
            
        found = False
        for a in atypes:
            for prefix in [project, "aho", "aho", "kjtcom"]:
                paths = [
                    iter_dir / f"{prefix}-{a}-{iteration}.md",
                    get_iterations_dir() / f"{prefix}-{a}-{iteration}.md",
                ]
                for path in paths:
                    if path.exists():
                        found = True
                        break
                if found: break
            if found: break
        
        if not found:
            failures.append(f"{atype}_artifact missing")
            continue
            
        size = path.stat().st_size
        # Thresholds: bundle must be > 100KB, others > 100 bytes
        threshold = 100000 if atype == bundle_kind else 100
        if size < threshold:
            failures.append(f"{atype}_artifact too small ({size} bytes)")
            
    if failures:
        return ("fail", ", ".join(failures))
    return ("ok", f"all 3 artifacts present ({project})")

if __name__ == "__main__":
    status, msg = check()
    print(f"  {status.upper()}: artifacts_present ({msg})")
    import sys
    sys.exit(0 if status == "ok" else 1)
