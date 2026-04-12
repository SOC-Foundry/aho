"""W7 acceptance: line count preserved after migration."""
from pathlib import Path
p = Path.home() / ".local/share/aho/events/aho_event_log.jsonl"
# Main file may be small after rotation; check .1 too
total = 0
for f in [p, p.parent / f"{p.name}.1", p.parent / f"{p.name}.2", p.parent / f"{p.name}.3"]:
    if f.exists():
        total += f.read_text().count("\n")
print(total)
assert total > 100, f"Only {total} lines across all event log files"
