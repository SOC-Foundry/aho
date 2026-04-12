"""W7 acceptance: log_event writes to new path."""
from aho.logger import log_event, event_log_path
before = event_log_path().stat().st_size
log_event("w7_acceptance", source_agent="claude-code", target="self", action="verify")
after = event_log_path().stat().st_size
assert after > before, f"File did not grow: {before} -> {after}"
print("ok")
