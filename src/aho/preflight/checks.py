import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def check_python_version() -> tuple[bool, str]:
    v = sys.version_info
    if v.major == 3 and v.minor >= 10:
        return True, f"Python {v.major}.{v.minor}.{v.micro}"
    return False, f"Python {v.major}.{v.minor} is too old (need 3.10+)"

def check_pip() -> tuple[bool, str]:
    if shutil.which("pip"):
        try:
            r = subprocess.run(["pip", "--version"], capture_output=True, text=True)
            return True, r.stdout.strip()
        except Exception:
            return False, "pip found but execution failed"
    return False, "pip not found"

def check_ollama_daemon() -> tuple[bool, str]:
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
            if response.status == 200:
                return True, "Ollama daemon responding"
    except Exception:
        pass
    return False, "Ollama daemon unreachable at localhost:11434"

def check_ollama_models() -> tuple[bool, str]:
    required = ["qwen3.5:9b", "GLM-4.6V-Flash-9B", "nemotron-mini:4b", "nomic-embed-text"]
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if r.returncode != 0:
            return False, "Failed to run 'ollama list'"
        
        missing = []
        for model in required:
            if model not in r.stdout:
                missing.append(model)
        
        if missing:
            return False, f"Missing models: {', '.join(missing)}"
        return True, "All required Ollama models present"
    except Exception as e:
        return False, f"Error checking models: {e}"

def check_disk_space() -> tuple[bool, str]:
    # Need 5GB free
    total, used, free = shutil.disk_usage(Path.home())
    free_gb = free // (2**30)
    if free_gb >= 5:
        return True, f"{free_gb} GB free"
    return False, f"Low disk space: {free_gb} GB free (need 5GB)"

def check_iao_json_valid() -> tuple[bool, str]:
    from ..paths import find_project_root
    try:
        root = find_project_root()
        p = root / ".aho.json"
        if not p.exists():
            return False, ".aho.json missing"
        json.loads(p.read_text())
        return True, ".aho.json is valid"
    except Exception as e:
        return False, f"Invalid .aho.json: {e}"

def check_sleep_masked() -> tuple[bool, str]:
    if sys.platform != "linux":
        return True, "Non-Linux system, skipping sleep mask check"
    
    try:
        r = subprocess.run(["systemctl", "status", "sleep.target"], capture_output=True, text=True)
        if "masked" in r.stdout:
            return True, "Sleep target is masked"
        return False, "Sleep target is NOT masked"
    except Exception:
        return True, "systemctl check failed, assuming OK"

def check_age_installed() -> tuple[bool, str]:
    from ..secrets.backends.age import AgeBackend
    if AgeBackend().is_available():
        return True, "age binary found"
    return False, "age binary missing"

def check_keyring_available() -> tuple[bool, str]:
    if sys.platform == "linux":
        from ..secrets.backends.keyring_linux import LinuxKeyringStore
        if LinuxKeyringStore().is_available():
            return True, "keyctl found"
        return False, "keyctl missing"
    return True, f"Keyring backend check skipped on {sys.platform}"

def check_pillars_parseable() -> tuple[bool, str]:
    try:
        from aho.feedback.run import get_pillars
        pillars = get_pillars()
        if len(pillars) != 11:
            return False, f"expected 11 pillars, got {len(pillars)}"
        return True, "11 pillars parsed from base.md"
    except RuntimeError as e:
        return False, str(e)

def run_all_preflight():
    checks = [
        ("Python Version", check_python_version),
        ("pip", check_pip),
        ("Ollama Daemon", check_ollama_daemon),
        ("Ollama Models", check_ollama_models),
        ("Disk Space", check_disk_space),
        ("Project .aho.json", check_iao_json_valid),
        ("Sleep Mask", check_sleep_masked),
        ("age Tool", check_age_installed),
        ("Keyring Tool", check_keyring_available),
        ("Pillars Parseable", check_pillars_parseable),
    ]
    
    results = {}
    for name, func in checks:
        results[name] = func()
    return results
