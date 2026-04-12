"""Component manifest loader and renderer.

Source of truth: artifacts/harness/components.yaml
0.2.10 W13: category-appropriate presence checks.
"""
import json
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Component:
    name: str
    kind: str
    path: str
    status: str = "active"
    owner: str = "soc-foundry"
    workload_pct: Optional[float] = None
    dependencies: list[str] = field(default_factory=list)
    next_iteration: Optional[str] = None
    notes: Optional[str] = None


def load_components(yaml_path: Path = None) -> list[Component]:
    """Load components from components.yaml."""
    if yaml_path is None:
        from aho.paths import get_harness_dir
        yaml_path = get_harness_dir() / "components.yaml"

    if not yaml_path.exists():
        return []

    # Use PyYAML if available, otherwise simple parser
    try:
        import yaml
        data = yaml.safe_load(yaml_path.read_text())
    except ImportError:
        data = _parse_yaml_simple(yaml_path)

    components = []
    for entry in data.get("components", []):
        components.append(Component(
            name=entry.get("name", "unknown"),
            kind=entry.get("kind", "python_module"),
            path=entry.get("path", ""),
            status=entry.get("status", "active"),
            owner=entry.get("owner", "soc-foundry"),
            dependencies=entry.get("dependencies", []),
            next_iteration=entry.get("next_iteration"),
            notes=entry.get("notes"),
        ))
    return components


def _parse_yaml_simple(yaml_path: Path) -> dict:
    """Minimal YAML parser for components.yaml when PyYAML is unavailable."""
    import re
    text = yaml_path.read_text()
    components = []
    current = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            if current:
                components.append(current)
            current = {"name": stripped.split(":", 1)[1].strip().strip('"')}
        elif current and ":" in stripped and not stripped.startswith("#"):
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in ("name", "kind", "path", "status", "owner", "next_iteration", "notes"):
                current[key] = val

    if current:
        components.append(current)

    return {"components": components}


def attribute_workload(events: list[dict]) -> dict[str, float]:
    """Count events per source_agent/target, normalize to percentages."""
    if not events:
        return {}

    counts = Counter()
    for ev in events:
        source = ev.get("source_agent") or ev.get("component") or "unknown"
        counts[source] += 1

    total = sum(counts.values())
    if total == 0:
        return {}

    return {k: round(v / total, 4) for k, v in counts.most_common()}


def check_installed(components: list[Component] = None) -> list[dict]:
    """Check presence of every component using category-appropriate method.

    Returns list of {name, kind, status, check_method, present} dicts.
    """
    if components is None:
        components = load_components()

    from aho.paths import find_project_root
    try:
        root = find_project_root()
    except Exception:
        root = Path.cwd()

    results = []
    for c in components:
        check = _check_component_presence(c, root)
        results.append({
            "name": c.name,
            "kind": c.kind,
            "status": c.status,
            "check_method": check["method"],
            "present": check["present"],
            "detail": check.get("detail", ""),
        })
    return results


def _check_component_presence(comp: Component, root: Path) -> dict:
    """Check if a single component is present using its kind-appropriate method."""
    kind = comp.kind
    path = comp.path

    if kind == "python_module":
        # Check if Python module file exists
        full = root / path
        if full.exists():
            return {"method": "file_exists", "present": True}
        # Try importing
        mod_name = path.replace("/", ".").replace(".py", "").replace("src.", "")
        if mod_name.startswith("aho."):
            try:
                __import__(mod_name)
                return {"method": "import", "present": True}
            except ImportError:
                pass
        return {"method": "file_exists", "present": False, "detail": f"{path} not found"}

    elif kind == "agent":
        # Agents are Python modules or systemd services
        full = root / path
        if full.exists():
            return {"method": "file_exists", "present": True}
        return {"method": "file_exists", "present": False, "detail": f"{path} not found"}

    elif kind == "llm":
        # Map component names to ollama model names
        _LLM_MAP = {
            "qwen-client": "qwen",
            "nemotron-client": "nemotron",
            "glm-client": "glm",
            "nomic-embed": "nomic",
        }
        search_name = _LLM_MAP.get(comp.name, comp.name).lower()
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if search_name in r.stdout.lower():
                return {"method": "ollama_list", "present": True}
            return {"method": "ollama_list", "present": False, "detail": f"{search_name} not in ollama list"}
        except Exception:
            return {"method": "ollama_list", "present": False, "detail": "ollama not reachable"}

    elif kind == "external_service":
        # External services checked via systemd or process
        if "systemd" in path or "service" in path:
            svc_name = comp.name
            try:
                r = subprocess.run(
                    ["systemctl", "--user", "is-active", f"aho-{svc_name}"],
                    capture_output=True, text=True, timeout=5
                )
                active = r.stdout.strip() == "active"
                return {"method": "systemd", "present": active, "detail": r.stdout.strip()}
            except Exception:
                pass
        # Fallback: check file path
        full = root / path
        if full.exists():
            return {"method": "file_exists", "present": True}
        return {"method": "file_exists", "present": False, "detail": f"{path} not found"}

    elif kind == "mcp_server":
        # dart mcp-server is SDK-bundled
        if "dart" in comp.name.lower():
            try:
                dr = subprocess.run(["dart", "--version"], capture_output=True, text=True, timeout=5)
                return {"method": "dart_sdk", "present": dr.returncode == 0}
            except Exception:
                return {"method": "dart_sdk", "present": False, "detail": "dart not available"}

        # Map component names to npm package names
        _NPM_MAP = {
            "mcp-firebase-tools": "firebase-tools",
            "mcp-context7": "@upstash/context7-mcp",
            "mcp-firecrawl": "firecrawl-mcp",
            "mcp-playwright": "@playwright/mcp",
            "mcp-server-filesystem": "@modelcontextprotocol/server-filesystem",
            "mcp-server-memory": "@modelcontextprotocol/server-memory",
            "mcp-server-sequential-thinking": "@modelcontextprotocol/server-sequential-thinking",
            "mcp-server-everything": "@modelcontextprotocol/server-everything",
        }
        npm_name = _NPM_MAP.get(comp.name, comp.name)
        try:
            r = subprocess.run(
                ["npm", "list", "-g", "--depth=0"],
                capture_output=True, text=True, timeout=10
            )
            if npm_name in r.stdout:
                return {"method": "npm_global", "present": True}
            return {"method": "npm_global", "present": False, "detail": f"{npm_name} not in npm global"}
        except Exception:
            return {"method": "npm_global", "present": False, "detail": "npm not available"}

    else:
        return {"method": "unknown", "present": False, "detail": f"unknown kind: {kind}"}


def render_section(yaml_path: Path = None) -> str:
    """Render markdown table for §23 and run report Component Activity."""
    components = load_components(yaml_path)
    if not components:
        return "*(no components loaded)*"

    lines = [
        "| Component | Kind | Status | Owner | Notes |",
        "|---|---|---|---|---|",
    ]

    for c in components:
        notes = c.notes or ""
        if c.next_iteration:
            notes = f"next: {c.next_iteration}" + (f"; {notes}" if notes else "")
        lines.append(f"| {c.name} | {c.kind} | {c.status} | {c.owner} | {notes} |")

    lines.append("")
    lines.append(f"**Total components:** {len(components)}")

    status_counts = Counter(c.status for c in components)
    summary = ", ".join(f"{count} {status}" for status, count in status_counts.most_common())
    lines.append(f"**Status breakdown:** {summary}")

    return "\n".join(lines)
