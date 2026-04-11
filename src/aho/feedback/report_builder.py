"""Mechanical report builder for aho iterations.

Reads checkpoint, event log, postflight results, and component manifest
to produce a structured report. Qwen commentary is optional and never
structural. ADR-042 extended: mechanical is authoritative.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _load_checkpoint(root: Path) -> dict:
    ckpt = root / ".aho-checkpoint.json"
    if ckpt.exists():
        return json.loads(ckpt.read_text())
    return {}


def _load_events(data_dir: Path, iteration: str) -> list[dict]:
    log = data_dir / "aho_event_log.jsonl"
    if not log.exists():
        return []
    events = []
    for line in log.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("iteration") == iteration:
                events.append(ev)
        except json.JSONDecodeError:
            continue
    return events


def _load_postflight_cache(root: Path) -> dict:
    """Load postflight results by running checks if available."""
    try:
        from aho.doctor import _postflight_checks
        return _postflight_checks()
    except Exception:
        return {}


def _section_header(iteration: str, checkpoint: dict, config: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prefix = config.get("artifact_prefix") or "aho"
    status = checkpoint.get("status", "unknown")
    run_type = checkpoint.get("run_type", "unknown")
    phase = checkpoint.get("phase", config.get("phase", 0))
    return (
        f"# Report — {prefix} {iteration}\n\n"
        f"**Generated:** {now}\n"
        f"**Iteration:** {iteration}\n"
        f"**Phase:** {phase}\n"
        f"**Run type:** {run_type}\n"
        f"**Status:** {status}\n"
    )


def _section_executive_summary(checkpoint: dict, events: list[dict], postflight: dict) -> str:
    ws = checkpoint.get("workstreams", {})
    total = len(ws)
    passed = sum(1 for v in ws.values() if (v if isinstance(v, str) else v.get("status", "")) == "pass")
    failed = sum(1 for v in ws.values() if (v if isinstance(v, str) else v.get("status", "")) == "fail")
    pending = total - passed - failed

    pf_total = len(postflight)
    pf_ok = sum(1 for s, _ in postflight.values() if s == "ok")
    pf_fail = sum(1 for s, _ in postflight.values() if s == "fail")

    lines = [
        "## Executive Summary\n",
        f"This iteration executed {total} workstreams: {passed} passed, {failed} failed, {pending} pending/partial.",
        f"{len(events)} events logged during execution.",
        f"Postflight: {pf_ok}/{pf_total} gates passed, {pf_fail} failed.",
        "",
    ]
    return "\n".join(lines)


def _wall_clock_for_ws(events: list[dict], workstream_id: str) -> str:
    """Compute wall clock duration from first/last event timestamps for a workstream."""
    ws_events = [e for e in events if e.get("workstream_id") == workstream_id]
    if not ws_events:
        return "-"
    timestamps = []
    for e in ws_events:
        ts = e.get("timestamp")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except (ValueError, TypeError):
                continue
    if len(timestamps) < 2:
        return "-"
    first = min(timestamps)
    last = max(timestamps)
    delta_seconds = (last - first).total_seconds()
    return f"{int(delta_seconds // 60)}m {int(delta_seconds % 60)}s"


def _section_workstream_detail(checkpoint: dict, events: list[dict]) -> str:
    ws = checkpoint.get("workstreams", {})
    from collections import Counter
    ws_event_counts = Counter(ev.get("workstream_id") for ev in events if ev.get("workstream_id"))

    lines = [
        "## Workstream Detail\n",
        "| Workstream | Status | Agent | Events | Wall Clock |",
        "|---|---|---|---|---|",
    ]
    executor = checkpoint.get("executor", "unknown")
    for ws_id in sorted(ws.keys()):
        ws_val = ws[ws_id]
        if isinstance(ws_val, str):
            status = ws_val
            agent = executor
        else:
            status = ws_val.get("status", "unknown")
            agent = ws_val.get("agent", ws_val.get("executor", executor))
        count = ws_event_counts.get(ws_id, 0)
        wall = _wall_clock_for_ws(events, ws_id)
        lines.append(f"| {ws_id} | {status} | {agent} | {count} | {wall} |")
    lines.append("")
    return "\n".join(lines)


def _section_component_activity(root: Path) -> str:
    components_yaml = root / "artifacts" / "harness" / "components.yaml"
    if not components_yaml.exists():
        return "## Component Activity\n\n*(components.yaml not yet created)*\n"

    try:
        from aho.components.manifest import load_components, render_section
        return "## Component Activity\n\n" + render_section() + "\n"
    except Exception:
        return "## Component Activity\n\n*(component manifest not loadable)*\n"


def _section_postflight(postflight: dict) -> str:
    if not postflight:
        return "## Postflight Results\n\n*(no postflight data)*\n"

    lines = [
        "## Postflight Results\n",
        "| Gate | Status | Message |",
        "|---|---|---|",
    ]
    for name, (status, msg) in sorted(postflight.items()):
        lines.append(f"| {name} | {status} | {msg} |")
    lines.append("")
    return "\n".join(lines)


def _section_risk_register(events: list[dict]) -> str:
    risks = [ev for ev in events if ev.get("status") in ("warn", "reject", "error")]
    if not risks:
        return "## Risk Register\n\n*(no warnings or rejections logged)*\n"

    lines = ["## Risk Register\n"]
    for ev in risks[:20]:
        ts = ev.get("timestamp", "?")
        typ = ev.get("event_type", "?")
        err = ev.get("error") or ev.get("output_summary") or ev.get("action", "")
        lines.append(f"- **{ts}** [{typ}] {err}")
    lines.append("")
    return "\n".join(lines)


def _section_carryovers(root: Path, iteration: str) -> str:
    """Parse carryovers from prior run's Kyle's Notes."""
    config = {}
    aho_json = root / ".aho.json"
    if aho_json.exists():
        config = json.loads(aho_json.read_text())
    prefix = config.get("artifact_prefix") or "aho"
    last = config.get("last_completed_iteration")
    if not last:
        return "## Carryovers\n\n*(no prior iteration)*\n"

    parts = last.split(".")
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else last
    prior_run = root / "artifacts" / "iterations" / version / f"{prefix}-run-{last}.md"
    if not prior_run.exists():
        return "## Carryovers\n\n*(prior run report not found)*\n"

    text = prior_run.read_text()
    # Extract Kyle's Notes section
    import re
    match = re.search(r"## Kyle's Notes.*?\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not match or not match.group(1).strip() or match.group(1).strip().startswith("<!--"):
        return "## Carryovers\n\n*(no notes from prior iteration)*\n"

    return f"## Carryovers\n\nFrom {last} Kyle's Notes:\n\n{match.group(1).strip()}\n"


def _section_next_recommendation(checkpoint: dict, postflight: dict) -> str:
    ws = checkpoint.get("workstreams", {})
    failed_ws = [k for k, v in ws.items() if (v if isinstance(v, str) else v.get("status", "")) == "fail"]
    failed_gates = [k for k, (s, _) in postflight.items() if s == "fail"]

    lines = ["## Next Iteration Recommendation\n"]
    if failed_ws:
        lines.append(f"- Retry failed workstreams: {', '.join(failed_ws)}")
    if failed_gates:
        lines.append(f"- Address failed postflight gates: {', '.join(failed_gates)}")
    if not failed_ws and not failed_gates:
        lines.append("- All workstreams passed and postflight gates green. Proceed to next iteration.")
    lines.append("")
    return "\n".join(lines)


def build_report(iteration: str, project_root: Path = None) -> Path:
    """Build a mechanical report for the given iteration.

    Returns the path to the written report file.
    """
    if project_root is None:
        from aho.paths import find_project_root
        project_root = find_project_root()

    config = {}
    aho_json = project_root / ".aho.json"
    if aho_json.exists():
        config = json.loads(aho_json.read_text())

    prefix = config.get("artifact_prefix") or "aho"
    checkpoint = _load_checkpoint(project_root)
    data_dir = project_root / "data"
    events = _load_events(data_dir, iteration)
    postflight = _load_postflight_cache(project_root)

    sections = [
        _section_header(iteration, checkpoint, config),
        _section_executive_summary(checkpoint, events, postflight),
        _section_workstream_detail(checkpoint, events),
        _section_component_activity(project_root),
        _section_postflight(postflight),
        _section_risk_register(events),
        _section_carryovers(project_root, iteration),
        _section_next_recommendation(checkpoint, postflight),
    ]

    content = "\n---\n\n".join(sections)

    parts = iteration.split(".")
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
    iter_dir = project_root / "artifacts" / "iterations" / version
    iter_dir.mkdir(parents=True, exist_ok=True)
    output = iter_dir / f"{prefix}-report-{iteration}.md"
    output.write_text(content)
    return output
