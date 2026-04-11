"""Smoke test for §22 instrumentation coverage.
Clears the event log, runs minimal invocations of each instrumented component,
asserts the event log has at least 4 unique source_agent names.
"""
import json
import os
import sys
from pathlib import Path

# aho-G061: Read iteration from checkpoint BEFORE importing aho modules,
# so the logger picks up the correct iteration at import time.
_ckpt = json.loads(Path(".aho-checkpoint.json").read_text())
os.environ["AHO_ITERATION"] = _ckpt["iteration"]

LOG_PATH = Path("data/aho_event_log.jsonl")
LOG_PATH.write_text("")  # clear

# 1. Invoke the CLI (use 'status' — a real subcommand that logs)
import subprocess
subprocess.run(["./bin/aho", "status"], capture_output=True)

# 2. Invoke the evaluator
from aho.artifacts.evaluator import evaluate_text
evaluate_text("sample content for smoke test", artifact_type="smoke")

# 3. Invoke a structural gate
from aho.postflight.structural_gates import check_required_sections
check_required_sections("# Header\n", required=["# Header"])

# 4. Invoke OpenClaw (if Ollama is up; skip gracefully if not)
try:
    from aho.agents.openclaw import OpenClawSession
    session = OpenClawSession()
    # just creating the session should log session_start
    del session
except Exception as e:
    print(f"OpenClaw smoke skipped: {e}", file=sys.stderr)

# 5. Invoke NemoClaw dispatch (with explicit role to skip Nemotron classify)
try:
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator()
    orch.dispatch("smoke test task", role="assistant")
    orch.close_all()
except Exception as e:
    print(f"NemoClaw smoke skipped: {e}", file=sys.stderr)

# Read back the event log
if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
    print("FAIL: event log is empty after smoke test")
    sys.exit(1)

events = [json.loads(line) for line in LOG_PATH.read_text().splitlines() if line.strip()]
components = set(e.get("source_agent", "unknown") for e in events)
print(f"Events logged: {len(events)}")
print(f"Unique components: {sorted(components)}")
print(f"Component count: {len(components)}")

if len(components) < 4:
    print(f"FAIL: expected >=4 unique components, got {len(components)}")
    sys.exit(1)

print("PASS")
