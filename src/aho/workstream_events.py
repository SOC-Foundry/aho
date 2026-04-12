"""workstream_events.py — Emit workstream_start and workstream_complete events.

Events are appended to data/aho_event_log.jsonl via aho.logger.log_event().
Both events include: iteration, workstream_id, timestamp, source_agent,
outcome (for complete), one-line summary.

Idempotency: start is idempotent (re-emitting start for an already-started
workstream is a no-op). Complete guards against double-complete by checking
the event log for an existing workstream_complete with the same workstream_id
and iteration.
"""
import json
import os
from pathlib import Path

from aho.logger import log_event, LOG_PATH, _ITERATION


def _scan_events(iteration: str, workstream_id: str, event_type: str) -> bool:
    """Check if an event of given type already exists for this workstream."""
    log_path = Path(LOG_PATH)
    if not log_path.exists():
        return False
    for line in log_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if (ev.get("iteration") == iteration
                    and ev.get("workstream_id") == workstream_id
                    and ev.get("event_type") == event_type):
                return True
        except json.JSONDecodeError:
            continue
    return False


def emit_workstream_start(workstream_id: str, summary: str = "",
                          source_agent: str | None = None) -> dict | None:
    """Emit a workstream_start event. Idempotent — skips if already started."""
    iteration = _ITERATION
    if _scan_events(iteration, workstream_id, "workstream_start"):
        return None  # already started

    agent = source_agent or os.environ.get("AHO_EXECUTOR", "claude-code")
    return log_event(
        event_type="workstream_start",
        source_agent=agent,
        target=workstream_id,
        action="start",
        input_summary=summary,
        workstream_id=workstream_id,
    )


def emit_workstream_complete(workstream_id: str, status: str = "pass",
                             summary: str = "",
                             source_agent: str | None = None) -> dict | None:
    """Emit a workstream_complete event. Guards against double-complete."""
    iteration = _ITERATION
    if _scan_events(iteration, workstream_id, "workstream_complete"):
        return None  # already completed

    agent = source_agent or os.environ.get("AHO_EXECUTOR", "claude-code")
    return log_event(
        event_type="workstream_complete",
        source_agent=agent,
        target=workstream_id,
        action="complete",
        output_summary=summary,
        status=status,
        workstream_id=workstream_id,
    )
