"""workstream_events.py — Emit workstream_start and workstream_complete events.

Events are appended to data/aho_event_log.jsonl via aho.logger.log_event().
Both events include: iteration, workstream_id, timestamp, source_agent,
outcome (for complete), one-line summary.

Idempotency: start is idempotent (re-emitting start for an already-started
workstream is a no-op). Complete guards against double-complete by checking
the event log for an existing workstream_complete with the same workstream_id
and iteration.

Schema v2 (0.2.11 W2): workstream_complete events may include
acceptance_results — a list of AcceptanceResult dicts. When present,
schema_version=2 is set. When absent, schema_version is omitted (v1 compat).

Schema v3 (0.2.13 W0): agents_involved extended from list[str] to
list[dict] with {agent: str, role: "primary"|"auditor"|"cameo"}.
AgentInvolvement model in acceptance.py normalizes bare strings to
{agent: str, role: "primary"} for backward compatibility.
"""
import json
import os
from dataclasses import asdict
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
    """Emit a workstream_start event. Idempotent — skips if already started.

    Also updates checkpoint: workstreams[WID] = "in_progress".
    """
    iteration = _ITERATION
    if _scan_events(iteration, workstream_id, "workstream_start"):
        return None  # already started

    agent = source_agent or os.environ.get("AHO_EXECUTOR", "claude-code")

    # Update checkpoint to in_progress
    try:
        from aho.paths import find_project_root
        root = find_project_root()
        ckpt_path = root / ".aho-checkpoint.json"
        if ckpt_path.exists():
            ckpt = json.loads(ckpt_path.read_text())
            ckpt.setdefault("workstreams", {})[workstream_id] = "in_progress"
            ckpt["current_workstream"] = workstream_id
            ckpt_path.write_text(json.dumps(ckpt, indent=2) + "\n")
    except Exception:
        pass

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
                             acceptance_results: list | None = None,
                             agents_involved: list[dict | str] | None = None,
                             token_count: int | None = None,
                             harness_contributions: list[str] | None = None,
                             ad_hoc_forensics_minutes: int | None = None,
                             source_agent: str | None = None) -> dict | None:
    """Emit a workstream_complete event. Guards against double-complete.

    Schema v2: acceptance_results → schema_version=2
    Schema v3: efficacy fields (agents_involved, token_count,
               harness_contributions, ad_hoc_forensics_minutes) → schema_version=3
    v1 compat: no extra fields, no schema_version.
    """
    iteration = _ITERATION
    if _scan_events(iteration, workstream_id, "workstream_complete"):
        return None  # already completed

    agent = source_agent or os.environ.get("AHO_EXECUTOR", "claude-code")
    event = log_event(
        event_type="workstream_complete",
        source_agent=agent,
        target=workstream_id,
        action="complete",
        output_summary=summary,
        status=status,
        workstream_id=workstream_id,
    )

    has_v2 = acceptance_results is not None
    has_v3 = any(x is not None for x in [agents_involved, token_count,
                                          harness_contributions, ad_hoc_forensics_minutes])

    if (has_v2 or has_v3) and event is not None:
        v3_fields = {}
        if agents_involved is not None:
            from aho.acceptance import AgentInvolvement
            normalized = []
            for a in agents_involved:
                ai = AgentInvolvement.model_validate(a)
                normalized.append(ai.model_dump())
            v3_fields["agents_involved"] = normalized
        if token_count is not None:
            v3_fields["token_count"] = token_count
        if harness_contributions is not None:
            v3_fields["harness_contributions"] = harness_contributions
        if ad_hoc_forensics_minutes is not None:
            v3_fields["ad_hoc_forensics_minutes"] = ad_hoc_forensics_minutes
        _patch_last_event_with_extras(acceptance_results, v3_fields)

    return event


def _patch_last_event_with_extras(acceptance_results: list | None,
                                   v3_fields: dict | None = None) -> None:
    """Patch the last event in the log to include acceptance_results and/or v3 efficacy fields."""
    log_path = Path(LOG_PATH)
    if not log_path.exists():
        return

    lines = log_path.read_text().splitlines()
    if not lines:
        return

    try:
        last_event = json.loads(lines[-1])
    except json.JSONDecodeError:
        return

    schema_version = 1

    if acceptance_results is not None:
        serialized = []
        for r in acceptance_results:
            if hasattr(r, '__dataclass_fields__'):
                serialized.append(asdict(r))
            elif hasattr(r, 'model_dump'):
                serialized.append(r.model_dump())
            elif isinstance(r, dict):
                serialized.append(r)
            else:
                serialized.append(str(r))
        last_event["acceptance_results"] = serialized
        schema_version = 2

    if v3_fields:
        for k, v in v3_fields.items():
            last_event[k] = v
        schema_version = 3

    if schema_version > 1:
        last_event["schema_version"] = schema_version

    lines[-1] = json.dumps(last_event)
    log_path.write_text("\n".join(lines) + "\n")


def load_acceptance_file(path: str | Path) -> list[dict]:
    """Load AcceptanceResult records from a JSON file.

    Returns list of dicts. Raises ValueError on invalid JSON.
    """
    p = Path(path)
    data = json.loads(p.read_text())
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")
    return data
