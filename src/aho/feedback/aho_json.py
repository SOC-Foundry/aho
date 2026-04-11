"""Helpers for updating .aho.json during iteration close."""
import json
from pathlib import Path

from aho.paths import find_project_root


def update_last_completed(iteration: str):
    """Update last_completed_iteration in .aho.json."""
    p = find_project_root() / ".aho.json"
    data = json.loads(p.read_text())
    data["last_completed_iteration"] = iteration
    p.write_text(json.dumps(data, indent=2) + "\n")
