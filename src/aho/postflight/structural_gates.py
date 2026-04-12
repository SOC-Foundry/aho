"""Structural gate post-flight check.

Validates that generated artifacts contain all required section headers.
Added in aho 0.1.7 W2. Updated in 0.1.14 W4 to support W-based layouts.
Refactored 0.2.11 W4: emits per-check CheckResult detail.
"""
import json
import re
from pathlib import Path

from aho.artifacts.schemas import SCHEMAS
from aho.logger import log_event
from aho.paths import get_iterations_dir
from aho.postflight import CheckResult, GateResult, worst_status
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
        required = ["## Workstreams", "### W0", "### W1", "## Success criteria"]
    elif artifact_type == "plan" and variant == LayoutVariant.W_BASED:
        required = ["## W0", "## W1"]
    elif artifact_type == "build-log":
        if "Auto-generated" in content or "## Workstream Synthesis" in content:
            required = ["Build Log", "## Workstream Synthesis"]
        elif variant == LayoutVariant.W_BASED:
            required = ["Build Log", "## W0"]
        else:
            required = schema.required_sections
    else:
        required = schema.required_sections

    if not required:
        return {"status": "PASS", "message": "No required sections defined", "errors": []}

    for section in required:
        if section.startswith("§"):
            if f"§{section[1:]}" not in content:
                errors.append(f"Missing section: {section}")
        elif section.startswith("#"):
            if section not in content:
                errors.append(f"Missing header: {section}")
        else:
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
    """Entry point for post-flight runner. Returns dict with checks[] detail."""
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
                return GateResult(
                    status="fail",
                    message="Could not determine iteration version",
                ).to_dict()

    iter_dir = get_iterations_dir() / version

    try:
        with open(".aho.json") as f:
            meta = json.load(f)
        prefix = meta.get("artifact_prefix", "aho")
    except Exception:
        prefix = "aho"

    checks = []
    for artifact_type, filename_pattern in [
        ("design", f"{prefix}-design-{version}.md"),
        ("plan", f"{prefix}-plan-{version}.md"),
        ("build-log", f"{prefix}-build-log-{version}.md"),
        ("report", f"{prefix}-report-{version}.md"),
    ]:
        path = iter_dir / filename_pattern
        result = check_artifact(path, artifact_type)
        raw_status = result["status"].lower()
        # Map PASS→ok, FAIL→fail, DEFERRED→deferred
        status = {"pass": "ok", "fail": "fail", "deferred": "deferred"}.get(raw_status, raw_status)
        errors = result.get("errors", [])
        message = result["message"]
        if errors:
            message = f"{message}: {'; '.join(errors)}"
        checks.append(CheckResult(
            name=f"structural_{artifact_type}",
            status=status,
            message=message,
            evidence_path=str(path) if path.exists() else None,
        ))

    rollup = worst_status([c.status for c in checks])
    pass_count = sum(1 for c in checks if c.status == "ok")
    fail_count = sum(1 for c in checks if c.status == "fail")
    deferred_count = sum(1 for c in checks if c.status == "deferred")

    return GateResult(
        status=rollup,
        message=f"Structural gates: {pass_count} pass, {fail_count} fail, {deferred_count} deferred",
        checks=checks,
    ).to_dict()
