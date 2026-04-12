"""Post-flight check: run report quality gate.

Refactored 0.2.11 W4: emits per-check CheckResult detail.
"""
import json
from pathlib import Path

from aho.postflight import CheckResult, GateResult, worst_status


def check(version: str = None) -> dict:
    """Validate run report quality. Returns dict with status, message, checks."""
    if version is None:
        try:
            from aho.paths import find_project_root
            root = find_project_root()
            with open(root / ".aho.json") as f:
                version = json.load(f).get("current_iteration", "")
        except Exception:
            version = ""

    if not version:
        return GateResult(
            status="deferred",
            message="Could not determine current iteration version",
        ).to_dict()

    try:
        from aho.paths import find_project_root
        root = find_project_root()
        with open(root / ".aho.json") as f:
            config = json.load(f)
        prefix = config.get("artifact_prefix") or config.get("name") or "aho"
    except Exception:
        prefix = "aho"
        root = Path.cwd()

    # Try both aho-run-X.Y.Z.md and aho-report-X.Y.Z.md
    run_path = root / "artifacts" / "iterations" / version / f"{prefix}-run-{version}.md"
    if not run_path.exists():
        run_path = root / "artifacts" / "iterations" / version / f"{prefix}-report-{version}.md"
    if not run_path.exists():
        return GateResult(
            status="deferred",
            message=f"Run file does not exist for {version}",
        ).to_dict()

    content = run_path.read_text()
    size_bytes = run_path.stat().st_size
    checks = []

    # Check: minimum size
    if size_bytes < 1500:
        checks.append(CheckResult(
            name="min_size",
            status="fail",
            message=f"Run file size {size_bytes} < 1500 bytes minimum",
            evidence_path=str(run_path),
        ))
    else:
        checks.append(CheckResult(
            name="min_size",
            status="ok",
            message=f"Run file size {size_bytes} bytes",
            evidence_path=str(run_path),
        ))

    # Check: workstream summary table has W0
    if "| W0 |" not in content:
        checks.append(CheckResult(
            name="ws_table_w0",
            status="fail",
            message="Workstream summary table missing W0 row",
        ))
    else:
        checks.append(CheckResult(
            name="ws_table_w0",
            status="ok",
            message="W0 row present in workstream table",
        ))

    # Check: workstream row count
    ws_row_count = sum(1 for line in content.splitlines() if line.strip().startswith("| W"))
    if ws_row_count < 4:
        checks.append(CheckResult(
            name="ws_row_count",
            status="fail",
            message=f"Workstream table has only {ws_row_count} rows (expected >= 4)",
        ))
    else:
        checks.append(CheckResult(
            name="ws_row_count",
            status="ok",
            message=f"Workstream table has {ws_row_count} rows",
        ))

    # Check: sign-off section
    if "## Sign-off" not in content:
        checks.append(CheckResult(
            name="signoff_section",
            status="fail",
            message="Sign-off section missing",
        ))
    else:
        checkbox_count = content.count("- [ ]") + content.count("- [x]") + content.count("- [X]")
        if checkbox_count < 5:
            checks.append(CheckResult(
                name="signoff_section",
                status="fail",
                message=f"Sign-off section has {checkbox_count} checkboxes (expected >= 5)",
            ))
        else:
            checks.append(CheckResult(
                name="signoff_section",
                status="ok",
                message=f"Sign-off section present with {checkbox_count} checkboxes",
            ))

    # Check: agent questions section
    if "## Agent Questions" not in content:
        checks.append(CheckResult(
            name="agent_questions",
            status="fail",
            message="Agent Questions section missing",
        ))
    else:
        checks.append(CheckResult(
            name="agent_questions",
            status="ok",
            message="Agent Questions section present",
        ))

    rollup = worst_status([c.status for c in checks])
    fail_count = sum(1 for c in checks if c.status == "fail")
    if fail_count > 0:
        msg = f"{fail_count} quality check failures"
    else:
        msg = "Run file passes quality gate"

    return GateResult(status=rollup, message=msg, checks=checks).to_dict()
