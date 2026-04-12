"""Generate BUNDLE_SPEC §22 Agentic Components from event log.

Added in aho 0.1.7 W7 to address Kyle's 0.1.4 run report note about
per-run component traceability.
"""
import json
from collections import defaultdict
from pathlib import Path


def generate_components_section(iteration: str, event_log_path: Path = None) -> str:
    if event_log_path is None:
        from aho.logger import event_log_path as _elp
        event_log_path = _elp()
        if not event_log_path.exists():
            event_log_path = Path("data/aho_event_log.jsonl")

    if not event_log_path.exists():
        return "## §22. Agentic Components\n\n*(no event log found)*\n"

    events = []
    for line in event_log_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("iteration") == iteration:
                events.append(ev)
        except json.JSONDecodeError:
            continue

    if not events:
        return f"## §22. Agentic Components\n\n*(no events recorded for iteration {iteration})*\n"

    grouped = defaultdict(list)
    for ev in events:
        source = ev.get("source_agent") or ev.get("component") or "unknown"
        grouped[source].append(ev)

    lines = [
        "## §22. Agentic Components",
        "",
        f"Per-run manifest of every model, agent, CLI command, and tool invoked during iteration {iteration}.",
        "",
        "| Component | Type | Tasks | Status | Notes |",
        "|---|---|---|---|---|",
    ]

    for component, events_list in sorted(grouped.items()):
        event_types = sorted(set(ev.get("event_type", "") for ev in events_list if ev.get("event_type")))
        tasks = sorted(set(ev.get("action", "") for ev in events_list if ev.get("action")))
        statuses = [ev.get("status", "") for ev in events_list]
        status_summary = f"{statuses.count('success')} ok / {statuses.count('error')} err / {len(statuses)} total"
        notes = "; ".join(sorted(set(str(ev.get("target", "")) for ev in events_list if ev.get("target"))))[:200]
        lines.append(
            f"| {component} | {', '.join(event_types)} | {', '.join(tasks)[:200]} | {status_summary} | {notes} |"
        )

    lines.extend(["", f"**Total events:** {len(events)}", f"**Unique components:** {len(grouped)}", ""])
    return "\n".join(lines)
