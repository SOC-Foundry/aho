"""Pipeline registry — tracks pipelines in consumer projects."""
import json
from pathlib import Path

from aho.paths import find_project_root


def list_pipelines() -> list[str]:
    """Return names of pipelines declared in .aho.json."""
    try:
        root = find_project_root()
        iao_json = root / ".aho.json"
        if iao_json.exists():
            data = json.loads(iao_json.read_text())
            return data.get("pipelines", [])
    except Exception:
        pass
    return []


def get_pipeline_status(name: str) -> dict:
    """Return checkpoint data for a named pipeline."""
    try:
        root = find_project_root()
        checkpoint = root / "pipelines" / name / "checkpoint.json"
        if checkpoint.exists():
            return json.loads(checkpoint.read_text())
    except Exception:
        pass
    return {"pipeline": name, "phases": {}, "status": "not found"}
