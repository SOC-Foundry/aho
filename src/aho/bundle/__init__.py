"""aho bundle generation and validation.

Implements the §1–§21 universal bundle specification per
ahomw-ADR-028 (amended in 0.1.4). Bundle is mechanical aggregation
of real files, not LLM synthesis.
"""
import json
import hashlib
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from aho.paths import find_project_root, get_artifacts_root

PROJECT_DIR = find_project_root()
ARTIFACTS_DIR = get_artifacts_root()
DOCS_DIR = ARTIFACTS_DIR  # post-0.1.13: docs moved under artifacts/
DATA_DIR = PROJECT_DIR / "data"

EXCLUSIONS = {
    Path.home() / ".config" / "fish" / "config.fish",
}


@dataclass
class BundleSection:
    number: int
    title: str
    min_chars: int
    allow_empty: bool = False


BUNDLE_SPEC = [
    BundleSection(1, "Design", 3000),
    BundleSection(2, "Plan", 3000),
    BundleSection(3, "Build Log", 1500),
    BundleSection(4, "Report", 1000),
    BundleSection(5, "Run Report", 1500),
    BundleSection(6, "Harness", 2000),
    BundleSection(7, "README", 1000),
    BundleSection(8, "CHANGELOG", 200),
    BundleSection(9, "CLAUDE.md", 500),
    BundleSection(10, "GEMINI.md", 500),
    BundleSection(11, ".aho.json", 100),
    BundleSection(12, "Sidecars", 0, allow_empty=True),
    BundleSection(13, "Gotcha Registry", 500),
    BundleSection(14, "Script Registry", 0, allow_empty=True),
    BundleSection(15, "ahomw MANIFEST", 100),
    BundleSection(16, "install.fish", 500),
    BundleSection(17, "COMPATIBILITY", 200),
    BundleSection(18, "projects.json", 100),
    BundleSection(19, "Event Log (tail 500)", 0, allow_empty=True),
    BundleSection(20, "File Inventory (sha256_16)", 500),
    BundleSection(21, "Environment", 500),
    BundleSection(22, "Component Checklist", 500),
    BundleSection(23, "Component Manifest", 500),
]


def _iao_data():
    p = PROJECT_DIR / ".aho.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def _prefix():
    d = _iao_data()
    return d.get("artifact_prefix") or d.get("name") or "project"


def _read_file(path):
    try:
        return Path(path).read_text(errors="ignore").rstrip()
    except Exception as e:
        return f"(read failed: {e})"


def _embed(label, path, lang="markdown"):
    out = [f"### {label} ({Path(path).name if path else 'MISSING'})"]
    if path and Path(path).exists() and path not in EXCLUSIONS:
        out.append(f"```{lang}")
        out.append(_read_file(path))
        out.append("```")
    else:
        out.append("(missing)")
    out.append("")
    return out


def _find_doc(prefix, doc_type, iteration):
    parts = iteration.split('.')
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
    for loc in [
        DOCS_DIR / "iterations" / version / f"{prefix}-{doc_type}-{iteration}.md",
        DOCS_DIR / "iterations" / version / f"{prefix}-{doc_type}-{version}.md",
        DOCS_DIR / f"{prefix}-{doc_type}-{iteration}.md",
        DOCS_DIR / "archive" / f"{prefix}-{doc_type}-{iteration}.md",
    ]:
        if loc.exists():
            return loc
    return None


def _tail(path, n=500):
    if not path or not Path(path).exists():
        return "(no events logged)"
    try:
        lines = Path(path).read_text(errors="ignore").splitlines()
        return "\n".join(lines[-n:])
    except Exception as e:
        return f"(read failed: {e})"


def _file_inventory(root, max_files=400):
    out = []
    for p in sorted(Path(root).rglob("*")):
        s = str(p)
        if not p.is_file():
            continue
        if "__pycache__" in s or ".egg-info" in s or s.endswith(".pyc"):
            continue
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            out.append(f"{h}  {p.relative_to(root)}")
        except Exception:
            continue
        if len(out) >= max_files:
            out.append("... (truncated)")
            break
    return "\n".join(out)


def _env_snapshot():
    info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "node": platform.node(),
    }
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        info["ollama"] = r.stdout.strip().splitlines()[:5]
    except Exception:
        info["ollama"] = "(unavailable)"
    try:
        r = subprocess.run(["df", "-h", str(Path.home())], capture_output=True, text=True, timeout=5)
        info["disk"] = r.stdout.strip().splitlines()[-1]
    except Exception:
        info["disk"] = "(unavailable)"
    return info


def build_bundle(iteration):
    prefix = _prefix()
    project_code = _iao_data().get("project_code", "")
    parts = iteration.split('.')
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
    sidecar_phase = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else iteration

    lines = []
    lines.append(f"# {prefix} - Bundle {iteration}")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat()}Z")
    lines.append(f"**Iteration:** {iteration}")
    lines.append(f"**Project code:** {project_code}")
    lines.append(f"**Project root:** {PROJECT_DIR}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # §1 Design
    lines += ["## §1. Design", ""]
    lines += _embed("DESIGN", _find_doc(prefix, "design", iteration))

    # §2 Plan
    lines += ["## §2. Plan", ""]
    lines += _embed("PLAN", _find_doc(prefix, "plan", iteration))

    # §3 Build Log
    lines += ["## §3. Build Log", ""]
    # ADR-042: Manual build log (authoritative)
    lines += _embed("BUILD LOG (MANUAL)", _find_doc(prefix, "build-log", iteration))
    # Optional: Qwen synthesis
    synthesis = _find_doc(prefix, "build-log-synthesis", iteration)
    if synthesis:
        lines += ["---", ""]
        lines += _embed("BUILD LOG (QWEN SYNTHESIS)", synthesis)

    # §4 Report
    lines += ["## §4. Report", ""]
    lines += _embed("REPORT", _find_doc(prefix, "report", iteration))

    # §5 Run Report
    lines += ["## §5. Run Report", ""]
    lines += _embed("RUN REPORT", _find_doc(prefix, "run", iteration))

    # §6 Harness
    lines += ["## §6. Harness", ""]
    lines += _embed("base.md", ARTIFACTS_DIR / "harness" / "base.md")

    # §7 README
    lines += ["## §7. README", ""]
    lines += _embed("README", PROJECT_DIR / "README.md")

    # §8 CHANGELOG
    lines += ["## §8. CHANGELOG", ""]
    lines += _embed("CHANGELOG", PROJECT_DIR / "CHANGELOG.md")

    # §9 CLAUDE.md
    lines += ["## §9. CLAUDE.md", ""]
    lines += _embed("CLAUDE.md", PROJECT_DIR / "CLAUDE.md")

    # §10 GEMINI.md
    lines += ["## §10. GEMINI.md", ""]
    lines += _embed("GEMINI.md", PROJECT_DIR / "GEMINI.md")

    # §11 .aho.json
    lines += ["## §11. .aho.json", ""]
    lines += _embed(".aho.json", PROJECT_DIR / ".aho.json", lang="json")

    # §12 Sidecars
    lines += ["## §12. Sidecars", ""]
    sidecar = DOCS_DIR / f"classification-{sidecar_phase}.json"
    if sidecar.exists():
        lines += _embed("classification", sidecar, lang="json")
    sterilization = DOCS_DIR / f"sterilization-log-{sidecar_phase}.md"
    if sterilization.exists():
        lines += _embed("sterilization-log", sterilization)
    if not sidecar.exists() and not sterilization.exists():
        lines.append("(no sidecars for this iteration)")
        lines.append("")

    # §13 Gotcha Registry
    lines += ["## §13. Gotcha Registry", ""]
    lines += _embed("gotcha_archive.json", DATA_DIR / "gotcha_archive.json", lang="json")

    # §14 Script Registry
    lines += ["## §14. Script Registry", ""]
    sr = DATA_DIR / "script_registry.json"
    if sr.exists():
        lines += _embed("script_registry.json", sr, lang="json")
    else:
        lines.append("(not yet created for aho)")
        lines.append("")

    # §15 ahomw MANIFEST
    lines += ["## §15. ahomw MANIFEST", ""]
    lines += _embed("MANIFEST.json", PROJECT_DIR / "MANIFEST.json", lang="json")

    # §16 install.fish
    lines += ["## §16. install.fish", ""]
    lines += _embed("install.fish", PROJECT_DIR / "install.fish", lang="fish")

    # §17 COMPATIBILITY
    lines += ["## §17. COMPATIBILITY", ""]
    lines += _embed("COMPATIBILITY.md", PROJECT_DIR / "COMPATIBILITY.md")

    # §18 projects.json
    lines += ["## §18. projects.json", ""]
    lines += _embed("projects.json", PROJECT_DIR / "projects.json", lang="json")

    # §19 Event Log
    lines += ["## §19. Event Log (tail 500)", ""]
    lines.append("```jsonl")
    lines.append(_tail(DATA_DIR / "aho_event_log.jsonl", 500))
    lines.append("```")
    lines.append("")

    # §20 File Inventory
    lines += ["## §20. File Inventory (sha256_16)", ""]
    lines.append("```")
    lines.append(_file_inventory(PROJECT_DIR))
    lines.append("```")
    lines.append("")

    # §21 Environment
    lines += ["## §21. Environment", ""]
    lines.append("```json")
    lines.append(json.dumps(_env_snapshot(), indent=2, default=str))
    lines.append("```")
    lines.append("")

    # §22 Component Checklist
    from aho.bundle.components_section import generate_components_section
    lines += [generate_components_section(iteration)]
    lines.append("")

    # §23 Component Manifest
    lines += ["## §23. Component Manifest", ""]
    try:
        from aho.components.manifest import render_section
        lines.append(render_section())
    except Exception as e:
        lines.append(f"*(component manifest unavailable: {e})*")
    lines.append("")

    iter_dir = DOCS_DIR / "iterations" / version
    iter_dir.mkdir(parents=True, exist_ok=True)
    output_path = iter_dir / f"{prefix}-bundle-{iteration}.md"
    output_path.write_text("\n".join(lines))
    return output_path


def validate_bundle(bundle_path):
    """Return list of validation errors. Empty list = passing."""
    errors = []
    path = Path(bundle_path)
    if not path.exists():
        return ["Bundle file does not exist"]

    content = path.read_text()
    size_bytes = path.stat().st_size

    if size_bytes < 50000:
        errors.append(f"Bundle size {size_bytes} < 50000 bytes minimum")

    for section in BUNDLE_SPEC:
        header = f"## §{section.number}."
        if header not in content:
            errors.append(f"Section {section.number} ({section.title}) header missing")

    return errors


def main():
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", default=os.environ.get("AHO_ITERATION", os.environ.get("IAO_ITERATION", "unknown")))
    args = parser.parse_args()
    path = build_bundle(args.iteration)
    print(f"Bundle generated: {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
