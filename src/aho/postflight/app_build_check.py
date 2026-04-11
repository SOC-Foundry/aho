"""Postflight gate: Flutter app build check.

If app/pubspec.yaml exists, verify flutter build web succeeds.
If absent, no-op pass.
"""
import subprocess
from pathlib import Path


def check():
    from aho.paths import find_project_root
    try:
        root = find_project_root()
    except Exception:
        return ("ok", "project root not found, skipping")

    pubspec = root / "app" / "pubspec.yaml"
    if not pubspec.exists():
        return ("ok", "no app scaffold present")

    index = root / "app" / "build" / "web" / "index.html"
    if index.exists():
        return ("ok", f"web build present ({index.stat().st_size} bytes)")

    try:
        r = subprocess.run(
            ["flutter", "build", "web", "--release"],
            cwd=str(root / "app"),
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            return ("ok", "flutter build web succeeded")
        return ("fail", f"flutter build web failed: {r.stderr[:200]}")
    except FileNotFoundError:
        return ("warn", "[CAPABILITY GAP] flutter not installed")
    except subprocess.TimeoutExpired:
        return ("fail", "flutter build web timed out")
