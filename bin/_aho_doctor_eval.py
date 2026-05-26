"""_aho_doctor_eval.py — internal evaluator invoked by bin/aho-doctor.

Reads env vars set by the fish wrapper:
  AHO_DOCTOR_JSONL              path to install-state.jsonl
  AHO_DOCTOR_REQUIRED           space-separated required step_ids
  AHO_DOCTOR_WORKSTREAM         workstream id (informational)
  AHO_DOCTOR_JSON_OUT           "1" → emit JSON, anything else → plain text
  AHO_DOCTOR_FAILED_LIST_OUT    path to write newline-separated failed step_ids
                                (for the fish wrapper's --remediate cascade)

Exits 0 if all required steps passing, 1 otherwise.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List


def main() -> int:
    jsonl_path = os.environ["AHO_DOCTOR_JSONL"]
    required = os.environ["AHO_DOCTOR_REQUIRED"].split()
    workstream = os.environ.get("AHO_DOCTOR_WORKSTREAM", "unknown")
    json_out = os.environ.get("AHO_DOCTOR_JSON_OUT") == "1"
    failed_list_out = os.environ.get("AHO_DOCTOR_FAILED_LIST_OUT")

    latest: Dict[str, Dict[str, Any]] = {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            sid = d.get("step_id")
            if sid:
                latest[sid] = d

    missing: List[str] = []
    failed: List[Dict[str, str]] = []
    passing: List[str] = []
    for sid in required:
        if sid not in latest:
            missing.append(sid)
        else:
            st = latest[sid].get("final_status", "")
            if st in ("satisfied", "remediated", "check_only_pass"):
                passing.append(sid)
            else:
                failed.append({
                    "step_id": sid,
                    "final_status": st,
                    "observed_state": latest[sid].get("observed_state", ""),
                })

    result = {
        "workstream": workstream,
        "required_steps_count": len(required),
        "passing_count": len(passing),
        "failed_count": len(failed),
        "missing_count": len(missing),
        "failed": failed,
        "missing": missing,
    }

    if json_out:
        print(json.dumps(result, indent=2))
    else:
        n_ok = len(passing)
        n_fail = len(failed)
        n_miss = len(missing)
        n_req = len(required)
        line = f"workstream={workstream}: {n_ok}/{n_req} required steps passing"
        if n_fail or n_miss:
            line += f"  ({n_fail} failed, {n_miss} missing)"
        print(line)
        for f in failed:
            print(f"  FAILED:  {f['step_id']}  status={f['final_status']}  observed={f['observed_state']}")
        for sid in missing:
            print(f"  MISSING: {sid}  (no entry in install-state.jsonl)")

    if failed_list_out:
        try:
            with open(failed_list_out, "w", encoding="utf-8") as f:
                for x in failed:
                    f.write(x["step_id"] + "\n")
        except OSError:
            pass

    return 0 if (not failed and not missing) else 1


if __name__ == "__main__":
    sys.exit(main())
