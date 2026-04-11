"""Post-flight check: Gemini compatibility and CLI sync."""
import subprocess
from pathlib import Path
from aho.paths import get_prompts_dir


def check() -> tuple[str, str]:
    """Validate aho doctor and versioning CLI commands."""
    errors = []
    
    # Prefer local binary for tests if present
    aho_bin = "./bin/aho" if Path("./bin/aho").exists() else "aho"
    
    # 1. Verify aho doctor quick exits 0
    try:
        r = subprocess.run([aho_bin, "doctor", "quick"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            errors.append(f"aho doctor quick failed (exit {r.returncode})")
    except Exception as e:
        errors.append(f"aho doctor execution failed: {e}")

    # 2. Verify aho log workstream-complete help shows required positional args
    try:
        r = subprocess.run([aho_bin, "log", "workstream-complete", "--help"], capture_output=True, text=True, timeout=10)
        if "workstream_id" not in r.stdout or "summary" not in r.stdout:
            errors.append("aho log workstream-complete missing expected positional args in help text")
    except Exception as e:
        errors.append(f"aho log check failed: {e}")

    # 3. Verify no --start references in plan templates
    prompts_dir = get_prompts_dir()
    if prompts_dir.exists():
        for p in prompts_dir.glob("*.j2"):
            if "--start" in p.read_text():
                errors.append(f"Stale --start flag found in {p.name}")

    if errors:
        return ("fail", f"{len(errors)} compatibility issues: {'; '.join(errors[:2])}")
    return ("ok", "Gemini-primary CLI sync verified")
