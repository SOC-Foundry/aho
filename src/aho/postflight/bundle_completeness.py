"""Postflight gate: verify bundle includes all iteration artifacts.

Two failure categories:
1. Sidecar drift — file exists on disk in artifacts/iterations/<version>/
   but is not included in the bundle's §12. Fix: regenerate bundle.
2. Canonical missing — a §1-§5 canonical section references a file that
   does not exist on disk. Fix: generate the underlying artifact first,
   then regenerate bundle.

Reports both categories separately so W13 close knows whether to
regenerate the bundle or generate the underlying artifact first.
"""
import json
from pathlib import Path

from aho.paths import find_project_root, get_artifacts_root


# Canonical section prefixes matched by the bundle generator
_CANONICAL_PREFIXES = {"design", "plan", "build-log", "report", "run", "bundle"}


def check():
    """Verify bundle completeness for the current iteration."""
    root = find_project_root()
    artifacts = get_artifacts_root()

    # Read current iteration
    aho_json = root / ".aho.json"
    if not aho_json.exists():
        return ("skip", ".aho.json not found")

    data = json.loads(aho_json.read_text())
    iteration = data.get("current_iteration", "unknown")
    parts = iteration.split(".")
    version = f"{parts[0]}.{parts[1]}.{parts[2]}" if len(parts) >= 3 else iteration
    prefix = data.get("artifact_prefix", data.get("name", "aho"))

    iter_dir = artifacts / "iterations" / version
    if not iter_dir.exists():
        return ("skip", f"iteration dir {version} not found")

    # Find the bundle file
    bundle_path = iter_dir / f"{prefix}-bundle-{iteration}.md"
    if not bundle_path.exists():
        return ("skip", f"bundle not yet generated for {iteration}")

    bundle_content = bundle_path.read_text()
    failures = []

    # Category 1: Sidecar drift — .md files in iteration dir not in bundle §12
    sidecar_missing = []
    for md_file in sorted(iter_dir.glob("*.md")):
        name_lower = md_file.name.lower()
        # Skip canonical files (§1-§5 sources) and the bundle itself
        is_canonical = any(f"-{cp}-" in name_lower or f"-{cp}." in name_lower for cp in _CANONICAL_PREFIXES)
        if is_canonical:
            continue
        # Check if the sidecar's filename appears in the bundle
        if md_file.name not in bundle_content:
            sidecar_missing.append(md_file.name)

    # Category 2: Canonical missing — expected canonical files not on disk
    # report/run are alternates — either satisfies the report requirement
    _CANONICAL_ALTERNATES = {
        "report": ["report", "run"],
    }
    canonical_missing = []
    for doc_type in ["design", "plan", "run", "build-log", "report"]:
        variants = _CANONICAL_ALTERNATES.get(doc_type, [doc_type])
        candidates = []
        for v in variants:
            candidates.append(iter_dir / f"{prefix}-{v}-{iteration}.md")
            candidates.append(iter_dir / f"{prefix}-{v}-{version}.md")
        if not any(c.exists() for c in candidates):
            canonical_missing.append(f"{prefix}-{doc_type}-{iteration}.md")

    # Category 3: ADRs — check artifacts/adrs/ files appear in bundle §6
    adrs_dir = artifacts / "adrs"
    adr_missing = []
    if adrs_dir.exists():
        for adr in sorted(adrs_dir.glob("*.md")):
            if adr.name not in bundle_content:
                adr_missing.append(adr.name)

    # Build result
    if sidecar_missing or canonical_missing or adr_missing:
        parts = []
        if sidecar_missing:
            parts.append(f"sidecar drift: {', '.join(sidecar_missing)}")
        if canonical_missing:
            parts.append(f"canonical missing: {', '.join(canonical_missing)}")
        if adr_missing:
            parts.append(f"ADR missing from §6: {', '.join(adr_missing)}")
        return ("fail", "; ".join(parts))

    return ("ok", "bundle includes all iteration artifacts")
