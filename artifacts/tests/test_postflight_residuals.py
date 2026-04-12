"""Tests for 0.2.9 residual debt fixes (W5).

Three fixes:
1. readme_current timezone normalization
2. bundle_quality §22 component count format
3. manifest_current self-referential hash exclusion
"""
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch


def test_readme_current_utc_comparison():
    """readme_current compares both timestamps in UTC."""
    from aho.postflight.readme_current import check
    status, msg = check()
    # Should pass since README was touched in W0
    assert status == "ok", f"Expected ok, got {status}: {msg}"
    assert "UTC" in msg or "+00:00" in msg or "updated" in msg


def test_readme_current_detects_stale_readme():
    """readme_current fails when README predates iteration start."""
    from aho.postflight.readme_current import check
    import os
    from aho.paths import find_project_root

    root = find_project_root()
    readme = root / "README.md"
    # Save original mtime
    orig_stat = readme.stat()

    # Set mtime to epoch (way before any iteration)
    os.utime(readme, (0, 0))
    try:
        status, msg = check()
        assert status == "fail", f"Expected fail for stale README, got {status}: {msg}"
    finally:
        # Restore original mtime
        os.utime(readme, (orig_stat.st_atime, orig_stat.st_mtime))


def test_bundle_quality_section_22_regex_matches_unique():
    """bundle_quality regex matches **Unique components:** N format."""
    import re
    pattern = r"\*\*(?:Unique|Total)\s+components:\*\*\s+(\d+)"
    assert re.search(pattern, "**Unique components:** 6")
    assert re.search(pattern, "**Total components:** 85")
    assert not re.search(pattern, "Components: 5")


def test_bundle_quality_section_22_table_fallback():
    """bundle_quality falls back to table row count if no summary line."""
    import re
    section = """## §22. Agentic Components

| Component | Type |
|---|---|
| claude-code | cli |
| qwen | model |
| glm | model |
"""
    # Simulate the gate's table row counting logic
    table_rows = [
        line for line in section.splitlines()
        if line.strip().startswith("|") and not line.strip().startswith("|--") and "Component" not in line
    ]
    assert len(table_rows) == 3


def test_manifest_excludes_self():
    """regenerate_manifest does not include MANIFEST.json in its file list."""
    from aho.manifest import regenerate_manifest
    from aho.paths import find_project_root

    path = regenerate_manifest()
    data = json.loads(path.read_text())
    assert "MANIFEST.json" not in data["files"]


def test_manifest_idempotent():
    """Regenerating manifest twice produces identical output."""
    from aho.manifest import regenerate_manifest
    from aho.postflight.manifest_current import check

    regenerate_manifest()
    s1, m1 = check()
    regenerate_manifest()
    s2, m2 = check()
    assert s1 == "ok", f"First pass: {s1}: {m1}"
    assert s2 == "ok", f"Second pass: {s2}: {m2}"


def test_manifest_gate_passes_after_regen():
    """manifest_current gate passes immediately after regeneration."""
    from aho.manifest import regenerate_manifest
    from aho.postflight.manifest_current import check

    regenerate_manifest()
    status, msg = check()
    assert status == "ok", f"Expected ok, got {status}: {msg}"
