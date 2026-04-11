"""Postflight gate: MANIFEST.json hash currency check.

FAIL if any file in MANIFEST.json has a stale hash.
"""
import hashlib
import json
from pathlib import Path


def check():
    from aho.paths import find_project_root
    try:
        root = find_project_root()
    except Exception:
        return ("fail", "project root not found")

    manifest_path = root / "MANIFEST.json"
    if not manifest_path.exists():
        return ("fail", "MANIFEST.json missing")

    data = json.loads(manifest_path.read_text())
    files = data.get("files", {})
    if not files:
        return ("fail", "MANIFEST.json has no files")

    mismatches = []
    missing = []
    checked = 0
    for rel_path, expected_hash in files.items():
        p = root / rel_path
        if not p.exists():
            missing.append(rel_path)
            continue
        h = hashlib.blake2b(p.read_bytes(), digest_size=8).hexdigest()
        if h != expected_hash:
            mismatches.append(rel_path)
        checked += 1

    if mismatches:
        return ("fail", f"stale hashes: {', '.join(mismatches[:3])}")
    if missing:
        return ("warn", f"checked {checked}, {len(missing)} files missing from disk")
    return ("ok", f"all {checked} file hashes current")
