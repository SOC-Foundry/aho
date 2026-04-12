"""Post-flight check: trident + pillars present in design and README.

Refactored 0.2.11 W6: §3 Trident structural verification with
per-check CheckResult detail. Pillar count flexible (10 or 11)
for design docs; README requires all 11.
"""
import re
import json
from pathlib import Path
from aho.paths import find_project_root
from aho.postflight import CheckResult, GateResult, worst_status
from aho.postflight.layout import detect_layout, LayoutVariant


def _check_trident(content: str) -> list[CheckResult]:
    """Verify §3 Trident structure in design doc content."""
    checks = []

    # Check 1: heading present
    has_heading = bool(re.search(r"##\s+§?3\.?\s+Trident", content))
    checks.append(CheckResult(
        name="trident_heading",
        status="ok" if has_heading else "fail",
        message="§3 Trident heading present" if has_heading else "§3 Trident heading missing",
    ))

    if not has_heading:
        # Remaining checks meaningless without heading
        for name, msg in [
            ("trident_mermaid_fence", "mermaid fence"),
            ("trident_graph_bt", "graph BT"),
            ("trident_classdef_shaft", "classDef shaft"),
            ("trident_classdef_prong", "classDef prong"),
            ("trident_edges", "edge arrows"),
        ]:
            checks.append(CheckResult(name=name, status="fail", message=f"Skipped — Trident heading missing"))
        return checks

    # Extract §3 content (from heading to next §)
    section_match = re.search(r"##\s+§?3\.?\s+Trident(.*?)(?=\n##\s+§|\Z)", content, re.DOTALL)
    section = section_match.group(1) if section_match else ""

    # Check 2: mermaid fence
    has_mermaid = "```mermaid" in section
    checks.append(CheckResult(
        name="trident_mermaid_fence",
        status="ok" if has_mermaid else "fail",
        message="mermaid code fence present" if has_mermaid else "mermaid code fence missing in §3",
    ))

    # Check 3: graph BT
    has_graph_bt = "graph BT" in section
    checks.append(CheckResult(
        name="trident_graph_bt",
        status="ok" if has_graph_bt else "fail",
        message="graph BT direction present" if has_graph_bt else "graph BT missing — Trident must be bottom-to-top",
    ))

    # Check 4: classDef shaft
    has_shaft = bool(re.search(r"classDef\s+shaft", section))
    checks.append(CheckResult(
        name="trident_classdef_shaft",
        status="ok" if has_shaft else "fail",
        message="classDef shaft present" if has_shaft else "classDef shaft missing",
    ))

    # Check 5: classDef prong
    has_prong = bool(re.search(r"classDef\s+prong", section))
    checks.append(CheckResult(
        name="trident_classdef_prong",
        status="ok" if has_prong else "fail",
        message="classDef prong present" if has_prong else "classDef prong missing",
    ))

    # Check 6: edge arrows (at least one -->)
    edges = re.findall(r"--+>", section)
    has_edges = len(edges) >= 1
    checks.append(CheckResult(
        name="trident_edges",
        status="ok" if has_edges else "fail",
        message=f"{len(edges)} edge arrows found" if has_edges else "No edge arrows (-->) found in Trident",
    ))

    return checks


def check():
    """Returns dict with status, message, checks."""
    try:
        root = find_project_root()
        config = json.loads((root / ".aho.json").read_text())
        iteration = config.get("current_iteration", "")
        prefix = config.get("artifact_prefix") or "aho"

        parts = iteration.split(".")
        version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration

        all_checks = []

        # Check design doc
        design_path = root / "artifacts" / "iterations" / version / f"{prefix}-design-{version}.md"
        if design_path.exists():
            content = design_path.read_text()

            # §3 Trident checks (always, regardless of layout variant)
            all_checks.extend(_check_trident(content))

            # Pillar enumeration: exactly 11 required (canonical per README)
            pillar_count = 0
            for i in range(1, 12):
                if re.search(rf"\b{i}\.\s+", content) or f"Pillar {i}" in content:
                    pillar_count += 1
            if pillar_count == 11:
                all_checks.append(CheckResult(
                    name="design_pillars",
                    status="ok",
                    message=f"All 11 pillars enumerated in design doc",
                ))
            else:
                all_checks.append(CheckResult(
                    name="design_pillars",
                    status="fail",
                    message=f"Only {pillar_count} pillars found in design (need exactly 11)",
                ))
        else:
            all_checks.append(CheckResult(
                name="design_doc",
                status="fail",
                message=f"Design doc not found: {design_path.name}",
            ))

        # Check README — all 11 pillars required
        readme_path = root / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text()
            missing_pillars = []
            for i in range(1, 12):
                if not re.search(rf"\b{i}\.\s+", readme_content):
                    if f"Pillar {i}" not in readme_content and f"Pillar-{i}" not in readme_content:
                        missing_pillars.append(str(i))

            if "### The Eleven Pillars of AHO" not in readme_content:
                all_checks.append(CheckResult(
                    name="readme_pillars_header",
                    status="fail",
                    message="README missing '### The Eleven Pillars of AHO' header",
                ))
            elif missing_pillars:
                all_checks.append(CheckResult(
                    name="readme_pillars",
                    status="fail",
                    message=f"README missing pillars: {', '.join(missing_pillars)}",
                ))
            else:
                all_checks.append(CheckResult(
                    name="readme_pillars",
                    status="ok",
                    message="All 11 pillars present in README",
                ))
        else:
            all_checks.append(CheckResult(
                name="readme",
                status="fail",
                message="README.md not found",
            ))

        rollup = worst_status([c.status for c in all_checks])
        fail_count = sum(1 for c in all_checks if c.status == "fail")
        if fail_count:
            msg = f"{fail_count} errors: {'; '.join(c.message for c in all_checks if c.status == 'fail')}"
        else:
            msg = "Trident + pillars present in design and README"

        return GateResult(status=rollup, message=msg, checks=all_checks).to_dict()
    except Exception as e:
        return GateResult(status="fail", message=f"error: {e}").to_dict()


if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", default=None)
    args = parser.parse_args()
    # If iteration specified, temporarily override
    if args.iteration:
        root = find_project_root()
        import json as _json
        _orig = (root / ".aho.json").read_text()
        _cfg = _json.loads(_orig)
        _cfg["current_iteration"] = args.iteration
        (root / ".aho.json").write_text(_json.dumps(_cfg, indent=2))
        try:
            result = check()
        finally:
            (root / ".aho.json").write_text(_orig)
    else:
        result = check()

    status = result.get("status", "unknown")
    msg = result.get("message", "")
    checks = result.get("checks", [])
    print(f"{status}: {msg}")
    for c in checks:
        print(f"  {c['status']:8s} {c['name']}: {c['message']}")
    sys.exit(0 if status == "ok" else 1)
