"""paths.py - Shared path resolution for aho components.

Resolution order:
  1. AHO_PROJECT_ROOT environment variable
  2. IAO_PROJECT_ROOT environment variable (legacy)
  3. Walk up from start (or cwd) looking for .aho.json
  4. Walk up from this file's location looking for .aho.json
  5. Raise AhoProjectNotFound
"""
import os
from pathlib import Path


class AhoProjectNotFound(Exception):
    """Raised when the project root cannot be resolved."""
    pass

# Legacy alias for backward compatibility
IaoProjectNotFound = AhoProjectNotFound


def find_project_root(start: Path | None = None) -> Path:
    env_root = os.environ.get("AHO_PROJECT_ROOT") or os.environ.get("IAO_PROJECT_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if (p / ".aho.json").exists():
            return p

    cur = (start or Path.cwd()).resolve()
    while cur != cur.parent:
        if (cur / ".aho.json").exists():
            return cur
        cur = cur.parent

    cur = Path(__file__).resolve().parent
    while cur != cur.parent:
        if (cur / ".aho.json").exists():
            return cur
        cur = cur.parent

    raise AhoProjectNotFound(
        "Could not resolve aho project root. Set AHO_PROJECT_ROOT, "
        "or cd into a project directory containing .aho.json."
    )


def get_artifacts_root() -> Path:
    return find_project_root() / "artifacts"


def get_harness_dir() -> Path:
    return get_artifacts_root() / "harness"


def get_adrs_dir() -> Path:
    return get_artifacts_root() / "adrs"


def get_iterations_dir() -> Path:
    return get_artifacts_root() / "iterations"


def get_prompts_dir() -> Path:
    return get_artifacts_root() / "prompts"


def get_templates_dir() -> Path:
    return get_artifacts_root() / "templates"


def get_scripts_dir() -> Path:
    return get_artifacts_root() / "scripts"


def get_tests_dir() -> Path:
    return get_artifacts_root() / "tests"


def get_registries_dir() -> Path:
    xdg_data = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
    registries = Path(xdg_data) / "aho" / "registries"
    registries.mkdir(parents=True, exist_ok=True)
    return registries

def get_data_dir() -> Path:
    return find_project_root() / "data"
