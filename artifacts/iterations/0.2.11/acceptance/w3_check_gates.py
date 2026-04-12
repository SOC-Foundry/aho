"""W3 acceptance helper: run gate checks against 0.2.10 artifacts.

Temporarily patches .aho.json to point to 0.2.10 so all gates
resolve against the completed iteration's artifact set.
"""
import json
import sys
from pathlib import Path

from aho.paths import find_project_root

root = find_project_root()
aho_json = root / ".aho.json"
orig = aho_json.read_text()
cfg = json.loads(orig)
cfg["current_iteration"] = "0.2.10"
aho_json.write_text(json.dumps(cfg, indent=2))

try:
    from aho.postflight.artifacts_present import check as ap_check
    from aho.postflight.iteration_complete import check_qwen_artifacts_present
    from aho.postflight.bundle_completeness import check as bc_check

    # artifacts_present
    s, m = ap_check()
    print(f"artifacts_present: {s.upper()}: {m}")
    if s != "ok":
        sys.exit(1)

    # iteration_complete (qwen artifacts)
    ok, m = check_qwen_artifacts_present()
    print(f"iteration_complete: {'OK' if ok else 'FAIL'}: {m}")
    if not ok:
        sys.exit(1)

    # bundle_completeness
    s, m = bc_check()
    print(f"bundle_completeness: {s.upper()}: {m}")
    if s not in ("ok", "skip"):
        sys.exit(1)

    print("ALL GATES OK")
finally:
    aho_json.write_text(orig)
