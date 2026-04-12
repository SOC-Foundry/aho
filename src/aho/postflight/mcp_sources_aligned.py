"""Postflight gate: verify components.yaml MCP entries align with bin/aho-mcp.

Prevents source-of-truth drift between the component manifest and the
MCP wrapper's canonical package list. The drift that started in 0.2.4
and persisted for four iterations motivated this gate.

components.yaml has mcp_server entries with 'path' fields containing
the npm package name (or 'dart-mcp-server' for the SDK-bundled server).
bin/aho-mcp has a fish array of npm package names.
"""
import re
from pathlib import Path

from aho.paths import find_project_root

# SDK-bundled server not in bin/aho-mcp npm list
_SDK_SERVERS = {"dart-mcp-server"}


def check():
    """Diff MCP entries in components.yaml against bin/aho-mcp packages."""
    root = find_project_root()

    # Parse components.yaml for mcp_server paths
    components_path = root / "artifacts" / "harness" / "components.yaml"
    if not components_path.exists():
        return ("fail", "components.yaml not found")

    comp_packages = set()
    in_mcp = False
    for line in components_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:") and "kind:" not in stripped:
            in_mcp = False
        if "kind: mcp_server" in stripped:
            in_mcp = True
        if in_mcp and stripped.startswith("path:"):
            pkg = stripped.split(":", 1)[1].strip().strip('"')
            comp_packages.add(pkg)
            in_mcp = False

    # Parse bin/aho-mcp for mcp_packages list
    mcp_script = root / "bin" / "aho-mcp"
    if not mcp_script.exists():
        return ("fail", "bin/aho-mcp not found")

    script_packages = set()
    in_list = False
    for line in mcp_script.read_text().splitlines():
        if "set -g mcp_packages" in line:
            in_list = True
        if in_list:
            # Extract package names (lines end with \ for continuation)
            cleaned = line.replace("\\", "").strip()
            cleaned = cleaned.replace("set -g mcp_packages", "").strip()
            if cleaned and not cleaned.startswith("#"):
                script_packages.add(cleaned)
            if "\\" not in line and "set -g mcp_packages" not in line:
                break

    # Add SDK servers to the script set for comparison
    script_with_sdk = script_packages | _SDK_SERVERS

    # Compare
    in_comp_not_script = comp_packages - script_with_sdk
    in_script_not_comp = script_with_sdk - comp_packages

    if in_comp_not_script or in_script_not_comp:
        parts = []
        if in_comp_not_script:
            parts.append(f"in components.yaml but not bin/aho-mcp: {', '.join(sorted(in_comp_not_script))}")
        if in_script_not_comp:
            parts.append(f"in bin/aho-mcp but not components.yaml: {', '.join(sorted(in_script_not_comp))}")
        return ("fail", "; ".join(parts))

    return ("ok", f"MCP sources aligned: {len(comp_packages)} entries match")
