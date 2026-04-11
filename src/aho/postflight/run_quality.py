"""Post-flight check: run report quality gate."""
import json
from pathlib import Path


def check(version: str = None) -> dict:
    """Validate run report quality.

    Returns dict with status (PASS/FAIL/DEFERRED), message, errors.
    """
    if version is None:
        try:
            from aho.paths import find_project_root
            root = find_project_root()
            with open(root / ".aho.json") as f:
                version = json.load(f).get("current_iteration", "")
        except Exception:
            version = ""

    if not version:
        return {"status": "DEFERRED", "message": "Could not determine current iteration version", "errors": []}

    try:
        from aho.paths import find_project_root
        root = find_project_root()
        with open(root / ".aho.json") as f:
            config = json.load(f)
        prefix = config.get("artifact_prefix") or config.get("name") or "aho"
    except Exception:
        prefix = "aho"
        root = Path.cwd()

    run_path = root / "artifacts" / "iterations" / version / f"{prefix}-run-{version}.md"

    if not run_path.exists():
        return {"status": "DEFERRED", "message": f"Run file does not exist at {run_path}", "errors": []}

    errors = []
    content = run_path.read_text()
    size_bytes = run_path.stat().st_size

    # Minimum size
    if size_bytes < 1500:
        errors.append(f"Run file size {size_bytes} < 1500 bytes minimum")

    # Workstream summary table — check for table rows
    if "| W0 |" not in content:
        errors.append("Workstream summary table missing W0 row")
    
    # Count workstream rows
    ws_row_count = sum(1 for line in content.splitlines() if line.strip().startswith("| W"))
    if ws_row_count < 4:
        errors.append(f"Workstream summary table has only {ws_row_count} rows (expected ≥ 4)")

    # Sign-off section with 5 checkboxes
    if "## Sign-off" not in content:
        errors.append("Sign-off section missing")
    checkbox_count = content.count("- [ ]") + content.count("- [x]") + content.count("- [X]")
    if checkbox_count < 5:
        errors.append(f"Sign-off section has {checkbox_count} checkboxes (expected ≥ 5)")

    # Agent questions section
    if "## Agent Questions" not in content:
        errors.append("Agent Questions section missing")

    if errors:
        return {"status": "fail", "message": f"{len(errors)} quality check failures", "errors": errors}
    return {"status": "ok", "message": "Run file passes quality gate", "errors": []}
