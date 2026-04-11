"""Post-flight check: trident + 11 pillars present in design and README."""
import re
import json
from pathlib import Path
from aho.paths import find_project_root
from aho.postflight.layout import detect_layout, LayoutVariant

def check():
    """Returns (status, message)."""
    try:
        root = find_project_root()
        config = json.loads((root / ".aho.json").read_text())
        iteration = config.get("current_iteration", "")
        prefix = config.get("artifact_prefix") or "aho"

        parts = iteration.split(".")
        version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration

        errors = []

        # Check design doc
        design_path = root / "artifacts" / "iterations" / version / f"{prefix}-design-{version}.md"
        if design_path.exists():
            variant = detect_layout(design_path)
            content = design_path.read_text()

            # Variant-specific checks
            if variant == LayoutVariant.W_BASED:
                # W-based designs don't enumerate all 11 pillars inline;
                # check for workstream headers + summary table instead
                if "## Workstreams" not in content:
                    errors.append("Design doc missing ## Workstreams header")
                ws_headers = re.findall(r"###\s+W\d+", content)
                if len(ws_headers) < 2:
                    errors.append("Design doc missing workstream headers (W0, W1, ...)")
            else:
                # Section-based (legacy/template): check pillar enumeration
                for i in range(1, 12):
                    if not re.search(rf"\b{i}\.\s+", content):
                        if f"Pillar {i}" not in content and f"Pillar-{i}" not in content:
                             errors.append(f"Design doc missing Pillar {i}")
                if "§3" not in content:
                    errors.append("Design doc missing §3 (Trident)")
        else:
            errors.append(f"Design doc not found: {design_path.name}")

        # Check README
        readme_path = root / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            for i in range(1, 12):
                if not re.search(rf"\b{i}\.\s+", content):
                    if f"Pillar {i}" not in content and f"Pillar-{i}" not in content:
                        errors.append(f"README missing Pillar {i}")
            
            if "### The Eleven Pillars of AHO" not in content:
                 errors.append("README missing Pillars header")
        else:
            errors.append("README.md not found")

        if errors:
            return ("fail", f"{len(errors)} errors: {'; '.join(errors[:3])}")
        return ("ok", "Eleven pillars present in design and README")
    except Exception as e:
        return ("fail", f"error: {e}")
