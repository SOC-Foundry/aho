"""Post-flight check: README currency enforcement (ahomw-ADR-033)."""
from datetime import datetime, timezone


def check():
    """Returns (status, message). FAIL if README mtime < iteration start."""
    import json
    from aho.paths import find_project_root

    try:
        root = find_project_root()
        readme = root / "README.md"
        if not readme.exists():
            return ("fail", "README.md does not exist")

        ckpt_path = root / ".aho-checkpoint.json"
        if not ckpt_path.exists():
            return ("warn", "No checkpoint — cannot verify README currency")

        ckpt = json.loads(ckpt_path.read_text())
        started_at = ckpt.get("started_at", "")
        if not started_at:
            return ("warn", "Checkpoint has no started_at timestamp")

        # Parse iteration start time — always use UTC
        start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        readme_mtime = datetime.fromtimestamp(readme.stat().st_mtime, tz=timezone.utc)

        if readme_mtime < start_time:
            return ("fail", f"README.md last modified {readme_mtime.isoformat()} < iteration start {started_at}")

        return ("ok", f"README updated during this iteration (mtime: {readme_mtime.isoformat()})")
    except Exception as e:
        return ("fail", f"error: {e}")
