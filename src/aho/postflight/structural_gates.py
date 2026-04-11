"""Structural gate post-flight check.

Validates that generated artifacts contain all required section headers.
Added in aho 0.1.7 W2. Updated in 0.1.14 W4 to support W-based layouts.
"""
import json
import re
from pathlib import Path

from aho.artifacts.schemas import SCHEMAS
from aho.logger import log_event
from aho.paths import get_iterations_dir
from aho.postflight.layout import detect_layout, LayoutVariant


def check_artifact(path: Path, artifact_type: str) -> dict:
    if not path.exists():
        return {"status": "DEFERRED", "message": f"Artifact not found: {path}", "errors": []}

    schema = SCHEMAS.get(artifact_type)
    if schema is None:
        return {"status": "PASS", "message": "No schema defined for artifact type", "errors": []}
    
    variant = detect_layout(path)
    content = path.read_text()
    errors = []

    if artifact_type == "design" and variant == LayoutVariant.W_BASED:
        # W-based design requirements
        required = ["## Workstreams", "### W0", "### W1", "## Success criteria"]
    elif artifact_type == "plan" and variant == LayoutVariant.W_BASED:
        # W-based plan requirements (gates are inline as **Gate:** not ## headers)
        required = ["## W0", "## W1"]
    elif artifact_type == "build-log":
        # Build logs may be stubs (Auto-generated) or manual; both use synthesis table
        if "Auto-generated" in content or "## Workstream Synthesis" in content:
            required = ["Build Log", "## Workstream Synthesis"]
        elif variant == LayoutVariant.W_BASED:
            required = ["Build Log", "## W0"]
        else:
            required = schema.required_sections
    else:
        # Fallback to schema-based requirements (§ markers)
        required = schema.required_sections

    if not required:
        return {"status": "PASS", "message": "No required sections defined", "errors": []}

    for section in required:
        # Handle both exact matches and pattern matches
        if section.startswith("§"):
            # Section header like "§1" must appear as "## §1" or similar
            if f"§{section[1:]}" not in content:
                errors.append(f"Missing section: {section}")
        elif section.startswith("#"):
            # Exact header match
            if section not in content:
                errors.append(f"Missing header: {section}")
        else:
            # Substring match in header or body
            if section not in content:
                errors.append(f"Missing section reference: {section}")

    result_status = "FAIL" if errors else "PASS"
    log_event("structural_gate", "structural-gates", artifact_type, "check",
              output_summary=f"status={result_status} errors={len(errors)} variant={variant.value}",
              status="success" if not errors else "failed")
    if errors:
        return {"status": "FAIL", "message": f"{len(errors)} structural failures", "errors": errors}
    return {"status": "PASS", "message": f"All {len(required)} required sections present", "errors": []}


def check_required_sections(content: str, required: list[str]) -> dict:
    """Simple section presence check — useful for smoke tests."""
    errors = [s for s in required if s not in content]
    status = "FAIL" if errors else "PASS"
    log_event("structural_gate", "structural-gates", "inline", "check_required_sections",
              output_summary=f"status={status} errors={len(errors)}",
              status="success" if not errors else "failed")
    return {"status": status, "errors": errors}


def check(version: str = None) -> dict:
    """Entry point for post-flight runner."""
    if version is None:
        try:
            with open(".aho.json") as f:
                version = json.load(f).get("current_iteration", "")
        except Exception:
            from aho.paths import find_project_root
            try:
                root = find_project_root()
                version = json.loads((root / ".aho.json").read_text()).get("current_iteration", "")
            except Exception:
                return {"status": "FAIL", "message": "Could not determine iteration version"}

    iter_dir = get_iterations_dir() / version
    results = {}

    try:
        with open(".aho.json") as f:
            meta = json.load(f)
        prefix = meta.get("artifact_prefix", "aho")
    except Exception:
        prefix = "aho"

    for artifact_type, filename_pattern in [
        ("design", f"{prefix}-design-{version}.md"),
        ("plan", f"{prefix}-plan-{version}.md"),
        ("build-log", f"{prefix}-build-log-{version}.md"),
        ("report", f"{prefix}-report-{version}.md"),
    ]:
        path = iter_dir / filename_pattern
        results[artifact_type] = check_artifact(path, artifact_type)

    all_pass = all(r["status"] == "PASS" for r in results.values() if r["status"] != "DEFERRED")
    all_errors = []
    for at, r in results.items():
        for e in r.get("errors", []):
            all_errors.append(f"{at}: {e}")

    return {
        "status": "PASS" if all_pass else "FAIL",
        "message": f"Structural gates: {sum(1 for r in results.values() if r['status'] == 'PASS')} pass, {sum(1 for r in results.values() if r['status'] == 'FAIL')} fail, {sum(1 for r in results.values() if r['status'] == 'DEFERRED')} deferred",
        "errors": all_errors,
        "per_artifact": results,
    }
