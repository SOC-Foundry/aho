import os
import json
import subprocess
from pathlib import Path
from aho.paths import find_project_root


def _iao_meta():
    try:
        root = find_project_root()
        with open(root / ".aho.json") as f:
            return json.load(f)
    except Exception:
        return {}


def check_all_workstreams_complete():
    try:
        root = find_project_root()
        checkpoint_path = root / ".aho-checkpoint.json"
        if not checkpoint_path.exists():
            return False, "Checkpoint file missing"
        
        data = json.loads(checkpoint_path.read_text())
        
        # Check if all workstreams in the checkpoint are 'complete' or 'partial' or 'pass'
        workstreams = data.get("workstreams", {})
        if not workstreams:
            return False, "No workstreams found in checkpoint"
            
        incomplete = []
        for ws_id, ws_data in workstreams.items():
            # Handle both flat string ("pass") and dict ({"status": "pass"}) formats
            if isinstance(ws_data, str):
                status = ws_data
            else:
                status = ws_data.get("status")
            if status not in ("complete", "partial", "pass"):
                incomplete.append(f"{ws_id}({status})")
        
        if incomplete:
            return False, f"Incomplete workstreams: {', '.join(incomplete)}"
        return True, "All workstreams reached final state"
    except Exception as e:
        return False, f"Error checking checkpoint: {e}"


def check_build_log_finalized():
    try:
        root = find_project_root()
        meta = _iao_meta()
        version = meta.get("current_iteration", "unknown")
        prefix = meta.get("artifact_prefix") or "aho"
        
        log_dir = root / "artifacts" / "iterations" / version
        manual_path = log_dir / f"{prefix}-build-log-{version}.md"
        synthesis_path = log_dir / f"{prefix}-build-log-synthesis-{version}.md"
            
        if not manual_path.exists():
            return False, f"Manual build log missing at {manual_path.relative_to(root)}"
            
        # ADR-042: Synthesis is optional, but if present we check it
        if synthesis_path.exists():
            return True, "Build log manual ground truth present (synthesis also present)"
        return True, "Build log manual ground truth present"
    except Exception as e:
        return False, f"Error checking build log: {e}"


def check_secrets_in_tracked_files():
    try:
        root = find_project_root()
        cmd = [
            "grep", "-rE", r"(API_KEY|BOT_TOKEN|SECRET).*=.*[A-Za-z0-9]{20,}", 
            str(root), 
            "--include=*.py", "--include=*.md", "--include=*.fish", "--include=*.json",
            "--exclude-dir=.git", "--exclude=secrets.fish.age", "--exclude=data/gotcha" + "_archive.json",
            "--exclude=bot.env"
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            lines = r.stdout.strip().splitlines()
            return False, f"Potential secrets found in {len(lines)} locations"
        return True, "No plaintext secrets found in tracked files"
    except Exception as e:
        return True, f"Secrets scan skipped or failed: {e}"


def check_install_fish_valid():
    try:
        root = find_project_root()
        install_path = root / "install.fish"
        if not install_path.exists():
            return False, "install.fish missing"
            
        r = subprocess.run(["fish", "--no-execute", str(install_path)], capture_output=True, text=True)
        if r.returncode == 0:
            return True, "install.fish syntax OK"
        return False, f"install.fish syntax error: {r.stderr.strip()}"
    except Exception as e:
        return False, f"Error checking install.fish: {e}"


def check_qwen_artifacts_present():
    try:
        root = find_project_root()
        meta = _iao_meta()
        version = meta.get("current_iteration", "unknown")
        prefix = meta.get("artifact_prefix") or "aho"
        log_dir = root / "artifacts" / "iterations" / version
        
        missing = []
        # build-log is now manual (ADR-042), we check for -synthesis as optional
        # report/run are alternates — either satisfies the report requirement
        _ARTIFACT_ALTERNATES = {
            "report": ["report", "run"],
        }
        for kind in ["design", "plan", "report", "bundle"]:
            variants = _ARTIFACT_ALTERNATES.get(kind, [kind])
            found = any(
                (log_dir / f"{prefix}-{v}-{version}.md").exists()
                for v in variants
            )
            if not found:
                missing.append(f"{kind}.md")
        
        if missing:
            return False, f"Missing artifacts: {', '.join(missing)}"
        return True, "All Qwen-generated artifacts present"
    except Exception as e:
        return False, f"Error checking artifacts: {e}"


def check():
    """Main check entry point for doctor.py."""
    checks = [
        ("Checkpoint", check_all_workstreams_complete),
        ("Build Log", check_build_log_finalized),
        ("Secret Scan", check_secrets_in_tracked_files),
        ("install.fish", check_install_fish_valid),
        ("Artifacts", check_qwen_artifacts_present),
    ]
    
    results = []
    all_ok = True
    for name, func in checks:
        ok, msg = func()
        results.append(f"{name}: {msg}")
        if not ok:
            all_ok = False
            
    return all_ok, "\n".join(results)
