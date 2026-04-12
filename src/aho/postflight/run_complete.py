"""Post-flight check: run report completeness and component floor."""
import json
import re
from pathlib import Path
from aho.paths import find_project_root


def check():
    """Returns (status, message). DEFERRED if Kyle's notes not yet filled in."""
    try:
        root = find_project_root()
        aho_json_path = root / ".aho.json"
        if not aho_json_path.exists():
             return ("fail", ".aho.json missing")
             
        config = json.loads(aho_json_path.read_text())
        iteration = config.get("current_iteration", "")
        prefix = config.get("artifact_prefix") or "aho"

        parts = iteration.split(".")
        version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration

        checkpoint_path = root / ".aho-checkpoint.json"
        run_type = "mixed"
        if checkpoint_path.exists():
            try:
                ckpt = json.loads(checkpoint_path.read_text())
                run_type = ckpt.get("run_type", "mixed")
            except Exception:
                pass

        # §22 floor check (Agentic Components)
        # We check the event log directly since §22 is derived from it
        from aho.logger import event_log_path as _event_log_path
        log_path = _event_log_path()
        unique_components = 0
        if log_path.exists():
            try:
                from collections import defaultdict
                events = []
                for line in log_path.read_text().splitlines():
                    if not line.strip(): continue
                    ev = json.loads(line)
                    if ev.get("iteration") == iteration:
                        events.append(ev)
                
                grouped = defaultdict(list)
                for ev in events:
                    source = ev.get("source_agent") or ev.get("component") or "unknown"
                    grouped[source].append(ev)
                unique_components = len(grouped)
            except Exception:
                pass

        FLOORS = {"agent_execution": 6, "reorg_docs": 2, "hygiene": 1, "mixed": 3}
        floor = FLOORS.get(run_type, 3)
        
        if unique_components < floor:
             return ("fail", f"Component floor not met: {unique_components} < {floor} (run_type: {run_type})")

        report_path = root / "artifacts" / "iterations" / version / f"{prefix}-run-{iteration}.md"

        if not report_path.exists():
            return ("warn", "Run report not yet generated")

        content = report_path.read_text()

        if "<!-- Fill in after reviewing the bundle -->" in content:
            return ("deferred", "Kyle's notes section not yet filled in")

        from aho.feedback.prompt import validate_signoff
        ok, missing = validate_signoff(report_path)
        if not ok:
            return ("deferred", f"Sign-off incomplete: {', '.join(missing[:2])}")

        return ("ok", f"Run report complete and signed off (Components: {unique_components} >= {floor})")
    except Exception as e:
        return ("fail", f"error: {e}")
