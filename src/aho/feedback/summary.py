"""Workstream summary table rendering for iteration close."""
import json
from pathlib import Path

from aho.paths import find_project_root


def render_summary() -> str:
    """Render the workstream summary table from checkpoint data."""
    root = find_project_root()
    ckpt_path = root / ".aho-checkpoint.json"

    if not ckpt_path.exists():
        return "(no checkpoint found)"

    ckpt = json.loads(ckpt_path.read_text())
    iteration = ckpt.get("iteration", "unknown")

    lines = [
        f"ITERATION {iteration} WORKSTREAM SUMMARY",
        "=" * 50,
        "",
    ]

    workstreams = ckpt.get("workstreams", {})
    executor = ckpt.get("executor", "unknown")
    for ws_id in sorted(workstreams.keys()):
        ws = workstreams[ws_id]
        if isinstance(ws, str):
            status = ws
            agent = executor
        else:
            status = ws.get("status", "pending")
            agent = ws.get("agent", executor)
        lines.append(f"  {ws_id:<6} {status:<15} ({agent})")

    complete = sum(1 for ws in workstreams.values() if (ws if isinstance(ws, str) else ws.get("status", "")) in ("complete", "pass", "clean"))
    total = len(workstreams)
    lines.append("")
    lines.append(f"  {complete}/{total} workstreams complete")

    return "\n".join(lines)
