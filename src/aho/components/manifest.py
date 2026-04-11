"""Component manifest loader and renderer.

Source of truth: artifacts/harness/components.yaml
"""
import json
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
