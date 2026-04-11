"""Postflight gate: verify canonical artifacts carry current iteration version."""
import json
import re
from pathlib import Path


def _load_canonical_yaml(yaml_path: Path) -> list[dict]:
    """Load canonical artifacts list from YAML."""
    try:
        import yaml
        data = yaml.safe_load(yaml_path.read_text())
        return data.get("artifacts", [])
    except ImportError:
        pass

    # Minimal parser fallback
    entries = []
    current = None
    for line in yaml_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("- path:"):
            if current:
                entries.append(current)
            current = {"path": _unquote(stripped.split(":", 1)[1].strip())}
        elif current and ":" in stripped:
            key, val = stripped.split(":", 1)
            current[key.strip()] = _unquote(val.strip())
    if current:
        entries.append(current)
    return entries


def _unquote(s: str) -> str:
    """Remove surrounding quotes without stripping backslashes."""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def check():
    """Check all canonical artifacts carry current iteration version."""
    from aho.paths import find_project_root, get_harness_dir
    root = find_project_root()

    aho_json = root / ".aho.json"
    if not aho_json.exists():
        return ("fail", ".aho.json not found")
    config = json.loads(aho_json.read_text())
    expected = config.get("current_iteration", "")
    if not expected:
        return ("fail", "current_iteration not set in .aho.json")

    yaml_path = get_harness_dir() / "canonical_artifacts.yaml"
    if not yaml_path.exists():
        return ("fail", "canonical_artifacts.yaml not found")

    entries = _load_canonical_yaml(yaml_path)
    if not entries:
        return ("fail", "canonical_artifacts.yaml is empty")

    mismatches = []
    for entry in entries:
        fpath = root / entry["path"]
        pattern = entry.get("pattern", "")
        if not fpath.exists():
            mismatches.append(f"{entry['path']}: file missing")
            continue
        text = fpath.read_text()
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            mismatches.append(f"{entry['path']}: pattern not found")
            continue
        found = match.group(1)
        if found != expected:
            mismatches.append(f"{entry['path']}: found {found}, expected {expected}")

    if mismatches:
        return ("fail", "; ".join(mismatches[:3]) + (f" (+{len(mismatches)-3} more)" if len(mismatches) > 3 else ""))
    return ("ok", f"all {len(entries)} canonical artifacts at {expected}")
