"""Postflight gate: CHANGELOG.md contains entry for current iteration."""
import json
import os
from pathlib import Path


def check():
    iteration = os.environ.get("AHO_ITERATION", os.environ.get("IAO_ITERATION"))
    if not iteration:
        from aho.paths import find_project_root
        try:
            root = find_project_root()
            config = json.loads((root / ".aho.json").read_text())
            iteration = config.get("current_iteration", "unknown")
        except Exception:
            return ("warn", "cannot resolve iteration")

    from aho.paths import find_project_root
    try:
        root = find_project_root()
    except Exception:
        return ("fail", "project root not found")

    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        return ("fail", "CHANGELOG.md missing")

    content = changelog.read_text()
    if iteration in content:
        return ("ok", f"CHANGELOG.md contains {iteration}")
    return ("fail", f"CHANGELOG.md missing entry for {iteration}")
