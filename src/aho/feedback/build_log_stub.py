import json
import pathlib
from datetime import datetime, timezone
from collections import Counter

def generate_stub(iteration: str, project_root: pathlib.Path = None) -> pathlib.Path:
    if project_root is None:
        from aho.paths import find_project_root
        try:
            project_root = find_project_root()
        except Exception:
            project_root = pathlib.Path.cwd()
    
    checkpoint_path = project_root / ".aho-checkpoint.json"
    from aho.logger import event_log_path as _event_log_path
    event_log_path = _event_log_path()
    iterations_dir = project_root / "artifacts" / "iterations" / iteration
    output_path = iterations_dir / f"aho-build-log-{iteration}.md"
    
    # Ensure output dir exists
    iterations_dir.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint
    checkpoint = {}
    if checkpoint_path.exists():
        try:
            checkpoint = json.loads(checkpoint_path.read_text())
        except Exception:
            pass
            
    # Load and filter event log
    events = []
    if event_log_path.exists():
        with open(event_log_path, "r") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                    if ev.get("iteration") == iteration:
                        events.append(ev)
                except Exception:
                    continue
                    
    # Synthesis
    run_type = checkpoint.get("run_type", "unknown")
    workstreams = checkpoint.get("workstreams", {})
    
    # Histogram
    event_types = [ev.get("event_type", "unknown") for ev in events]
    type_counts = Counter(event_types)
    
    # Workstream stats
    ws_stats = {}
    for ev in events:
        ws = ev.get("workstream")
        if not ws:
            # Try to map based on timestamp if workstream is null? 
            # For now, only events with explicit workstream are counted per-WS
            continue
            
        if ws not in ws_stats:
            ws_stats[ws] = {
                "count": 0,
                "first": ev.get("timestamp"),
                "last": ev.get("timestamp"),
                "agent": ev.get("source_agent") or ev.get("executor") or checkpoint.get("executor")
            }
        
        ws_stats[ws]["count"] += 1
        ts = ev.get("timestamp")
        if ts:
            if not ws_stats[ws]["first"] or ts < ws_stats[ws]["first"]:
                ws_stats[ws]["first"] = ts
            if not ws_stats[ws]["last"] or ts > ws_stats[ws]["last"]:
                ws_stats[ws]["last"] = ts

    # Markdown generation
    lines = []
    lines.append(f"# aho {iteration} — Build Log (Stub)")
    lines.append("")
    lines.append(f"**Run Type:** {run_type}")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("> **Auto-generated from checkpoint + event log. No manual build log was authored for this run.**")
    lines.append("")
    lines.append("## Workstream Synthesis")
    lines.append("")
    lines.append("| Workstream | Agent | Status | Events | First | Last |")
    lines.append("|------------|-------|--------|--------|-------|------|")
    
    sorted_ws = sorted(workstreams.keys())
    for ws in sorted_ws:
        status = workstreams[ws]
        stats = ws_stats.get(ws, {})
        agent = stats.get("agent", checkpoint.get("executor", "unknown"))
        count = stats.get("count", 0)
        first = stats.get("first", "-")
        last = stats.get("last", "-")
        lines.append(f"| {ws} | {agent} | {status} | {count} | {first} | {last} |")
        
    lines.append("")
    lines.append("## Event Type Histogram")
    lines.append("")
    for etype, count in type_counts.most_common():
        lines.append(f"- **{etype}:** {count}")
    
    lines.append("")
    lines.append("## Event Log Tail (Last 20)")
    lines.append("")
    lines.append("```json")
    for ev in events[-20:]:
        lines.append(json.dumps(ev))
    lines.append("```")
    
    output_path.write_text("\n".join(lines))
    return output_path

if __name__ == "__main__":
    import sys
    it = sys.argv[1] if len(sys.argv) > 1 else "0.1.14"
    print(f"Generating stub for {it}...")
    p = generate_stub(it)
    print(f"Done: {p}")
