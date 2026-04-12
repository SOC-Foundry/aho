"""MANIFEST.json generator and live-refresh daemon.

0.2.10 W11 — Regenerates MANIFEST.json when harness or registry files change.
Debounced at 5 seconds to prevent storm during bulk writes.
"""
import hashlib
import json
import os
import threading
import time
from pathlib import Path

from aho.paths import find_project_root
from aho.logger import log_event


def _blake2b_hash(path: Path) -> str:
    """Compute blake2b hash (8-byte digest) of a file."""
    return hashlib.blake2b(path.read_bytes(), digest_size=8).hexdigest()


def regenerate_manifest(root: Path = None) -> Path:
    """Regenerate MANIFEST.json from all tracked files."""
    if root is None:
        root = find_project_root()

    manifest_path = root / "MANIFEST.json"

    # Read existing manifest to get file list, or scan
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip .git, __pycache__, node_modules, .dart_tool
        dirnames[:] = [
            d for d in dirnames
            if d not in {".git", "__pycache__", "node_modules", ".dart_tool", ".mypy_cache"}
        ]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(root)
            rel_str = str(rel)
            # Skip binary files, large files, and self-referential MANIFEST.json
            if fpath.suffix in {".pyc", ".pyo", ".so", ".dll", ".exe", ".png", ".jpg", ".ico"}:
                continue
            if fname == "MANIFEST.json" and Path(dirpath) == root:
                continue
            # Skip event log files (runtime data, relocated to XDG in 0.2.11 W7)
            if fname.startswith("aho_event_log"):
                continue
            try:
                if fpath.stat().st_size > 1_000_000:  # 1MB cap
                    continue
                files[rel_str] = _blake2b_hash(fpath)
            except (PermissionError, OSError):
                continue

    config = json.loads((root / ".aho.json").read_text()) if (root / ".aho.json").exists() else {}
    manifest = {
        "version": config.get("current_iteration", "unknown"),
        "project_code": config.get("project_code", "aho"),
        "files": dict(sorted(files.items())),
    }

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path


class ManifestRefresher:
    """Debounced MANIFEST.json regenerator.

    Call trigger() when a watched file changes. After 5s of quiet,
    regenerates MANIFEST.json.
    """

    def __init__(self, root: Path = None, debounce: float = 5.0):
        self.root = root or find_project_root()
        self.debounce = debounce
        self._timer = None
        self._lock = threading.Lock()

    def trigger(self):
        """Signal that a file has changed. Debounced regeneration."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce, self._do_refresh)
            self._timer.daemon = True
            self._timer.start()

    def _do_refresh(self):
        """Actually regenerate the manifest."""
        try:
            path = regenerate_manifest(self.root)
            log_event("manifest_refresh", "harness-watcher", "manifest", "regenerate",
                      output_summary=f"MANIFEST.json refreshed: {path}")
        except Exception as e:
            log_event("manifest_refresh_error", "harness-watcher", "manifest", "error",
                      output_summary=str(e))
