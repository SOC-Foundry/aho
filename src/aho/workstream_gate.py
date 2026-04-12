"""workstream_gate.py — Agent-side pause/proceed handshake.

Called at workstream boundaries before emitting workstream_start.
Polls .aho-checkpoint.json every 5 seconds until proceed_awaited is false.

Timeout None = block indefinitely. Explicit timeout supported for safety
in non-interactive runs.
"""
import json
import time
from pathlib import Path

from aho.paths import find_project_root


def _read_proceed_awaited() -> bool:
    """Read proceed_awaited from checkpoint. Returns False if missing or unreadable."""
    try:
        ckpt = find_project_root() / ".aho-checkpoint.json"
        if not ckpt.exists():
            return False
        data = json.loads(ckpt.read_text())
        return bool(data.get("proceed_awaited", False))
    except Exception:
        return False


def wait_if_paused(timeout_seconds: float | None = None, poll_interval: float = 5.0) -> bool:
    """Block until proceed_awaited is false (or timeout expires).

    Returns True if execution may proceed, False if timed out while still paused.
    """
    if not _read_proceed_awaited():
        return True  # not paused, proceed immediately

    print("[workstream-gate] proceed_awaited=true, waiting for /ws proceed...", flush=True)
    elapsed = 0.0
    while _read_proceed_awaited():
        if timeout_seconds is not None and elapsed >= timeout_seconds:
            print(f"[workstream-gate] timed out after {timeout_seconds}s, still paused", flush=True)
            return False
        time.sleep(poll_interval)
        elapsed += poll_interval

    print("[workstream-gate] proceed_awaited cleared, resuming", flush=True)
    return True
