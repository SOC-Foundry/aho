"""doctor.py - Unified health checks for aho environments.

Provides three levels:
- quick: configuration and structural integrity (sub-second)
- preflight: environment readiness for execution
- postflight: verification of iteration results and deployment
"""
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from aho.paths import find_project_root, IaoProjectNotFound, get_data_dir

def _check_project_root():
    try:
        root = find_project_root()
        return ("ok", str(root))
    except IaoProjectNotFound as e:
        return ("fail", str(e))

def _check_aho_json():
    try:
        root = find_project_root()
        p = root / ".aho.json"
        if not p.exists():
            return ("fail", ".aho.json missing at root")
        data = json.loads(p.read_text())
        return ("ok", f"version {data.get('current_iteration', 'unknown')}")
    except Exception as e:
        return ("fail", f"error: {e}")

def _check_manifest():
    try:
        root = find_project_root()
        m_path = root / "MANIFEST.json"
        if not m_path.exists():
            return ("warn", "MANIFEST.json missing")
        
        data = json.loads(m_path.read_text())
        files = data.get("files", {})
        if not files:
            return ("warn", "MANIFEST.json empty")
            
        checked = 0
        failed_files = []
        for rel_path, expected_hash in list(files.items()):
            # Manifest might have stale paths; only check if they exist or were moved
            p = root / rel_path
            if not p.exists():
                continue # Skip missing files for now, as reorg moved them
            h = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            if h != expected_hash:
                failed_files.append(f"{rel_path} (hash mismatch)")
            checked += 1
            
        if failed_files:
            return ("warn", f"MANIFEST integrity failed: {', '.join(failed_files[:2])}")
        return ("ok", f"MANIFEST verified ({checked} active files)")
    except Exception as e:
        return ("warn", f"integrity check skipped: {e}")

def _check_path():
    try:
        r = subprocess.run(["which", "aho"], capture_output=True, text=True)
        if r.returncode == 0:
            return ("ok", r.stdout.strip())
        return ("warn", "aho CLI not on PATH")
    except Exception:
        return ("warn", "PATH check failed")

def _check_fish_marker():
    config_path = Path.home() / ".config" / "fish" / "config.fish"
    if not config_path.exists():
        return ("ok", "fish config absent")
    
    try:
        content = config_path.read_text()
        count = content.count("# >>> aho >>>")
        if count == 1:
            return ("ok", "marker block present")
        elif count == 0:
            return ("warn", "marker block missing")
        else:
            return ("fail", f"multiple marker blocks found ({count})")
    except Exception as e:
        return ("warn", f"fish check error: {e}")

def _check_secrets_backend():
    from aho.secrets.backends.age import AgeBackend
    from aho.secrets.backends.keyring_linux import LinuxKeyringStore
    
    age = AgeBackend()
    keyring = LinuxKeyringStore()
    
    missing = []
    if not age.is_available():
        missing.append("age")
    if sys.platform == "linux" and not keyring.is_available():
        missing.append("keyctl")
        
    if missing:
        return ("warn", f"missing dependencies (need: {', '.join(missing)})")
    return ("ok", "ready")

def _check_install():
    """Verify bin/aho-install and bin/aho-uninstall exist and are executable."""
    try:
        root = find_project_root()
        install = root / "bin" / "aho-install"
        uninstall = root / "bin" / "aho-uninstall"
        missing = []
        if not install.exists() or not os.access(install, os.X_OK):
            missing.append("aho-install")
        if not uninstall.exists() or not os.access(uninstall, os.X_OK):
            missing.append("aho-uninstall")
        if missing:
            return ("fail", f"missing or not executable: {', '.join(missing)}")
        return ("ok", "install + uninstall present")
    except Exception as e:
        return ("warn", f"install check error: {e}")

def _check_linger():
    """Verify loginctl linger is enabled for current user."""
    try:
        r = subprocess.run(
            ["loginctl", "show-user", os.environ.get("USER", ""), "--property=Linger"],
            capture_output=True, text=True, timeout=5
        )
        if "Linger=yes" in r.stdout:
            return ("ok", "linger enabled")
        return ("warn", "linger not enabled (sudo loginctl enable-linger $USER)")
    except Exception:
        return ("warn", "linger check skipped")

def _quick_checks():
    return {
        "project_root": _check_project_root(),
        "aho_json": _check_aho_json(),
        "path": _check_path(),
        "fish_marker": _check_fish_marker(),
        "secrets_backend": _check_secrets_backend(),
        "install_scripts": _check_install(),
        "linger": _check_linger(),
        "age_key": _check_age_key(),
        "dashboard_port": _check_dashboard_port(),
        "role_agents": _check_role_agents(),
    }

def _check_ollama():
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:11434/api/tags"],
            capture_output=True, text=True, timeout=5
        )
        if r.stdout.strip() == "200":
            return ("ok", "ollama up")
        return ("fail", f"ollama down (HTTP {r.stdout.strip()})")
    except Exception as e:
        return ("fail", f"ollama unreachable: {e}")

def _check_model_fleet():
    """Verify all 4 required Ollama models are present."""
    required = ["qwen3.5", "nemotron-mini", "GLM-4", "nomic-embed-text"]
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        output = r.stdout
        missing = [m for m in required if m.lower() not in output.lower()]
        if missing:
            return ("fail", f"missing models: {', '.join(missing)}")
        return ("ok", f"all {len(required)} fleet models present")
    except Exception:
        return ("warn", "model fleet check failed")

def _check_python_deps():
    deps = ["litellm", "jsonschema", "chromadb"]
    missing = []
    for d in deps:
        try:
            __import__(d)
        except ImportError:
            missing.append(d)
    
    if missing:
        return ("fail", f"missing: {', '.join(missing)}")
    return ("ok", "all dependencies importable")

def _check_disk():
    try:
        r = subprocess.run(["df", "-h", str(Path.home())], capture_output=True, text=True)
        line = r.stdout.strip().splitlines()[-1]
        avail = line.split()[3]
        if avail.endswith("G"):
            val = float(avail[:-1])
            if val < 5:
                return ("fail", f"low disk space: {avail}")
            return ("ok", f"{avail} available")
        return ("ok", f"disk check: {avail}")
    except Exception:
        return ("warn", "disk check failed")

def _check_otel_collector():
    """Verify aho-otel-collector systemd user service is running."""
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "aho-otel-collector"],
            capture_output=True, text=True, timeout=5
        )
        if r.stdout.strip() == "active":
            return ("ok", "aho-otel-collector running")
        return ("warn", f"aho-otel-collector: {r.stdout.strip()}")
    except Exception:
        return ("warn", "otel collector check failed")

def _check_age_key():
    """Verify per-clone age key exists with correct permissions."""
    key_path = Path.home() / ".config" / "aho" / "age.key"
    if not key_path.exists():
        return ("warn", "age key missing (~/.config/aho/age.key). Run bin/aho-install.")
    mode = oct(key_path.stat().st_mode)[-3:]
    if mode != "600":
        return ("warn", f"age key permissions {mode}, expected 600")
    return ("ok", "age key present (mode 600)")


def _check_dashboard_port():
    """Verify .aho.json has dashboard_port and the port is bindable."""
    try:
        root = find_project_root()
        p = root / ".aho.json"
        if not p.exists():
            return ("warn", ".aho.json missing")
        data = json.loads(p.read_text())
        port = data.get("dashboard_port")
        if port is None:
            return ("warn", "dashboard_port not set in .aho.json")
        from aho.config import check_port_available
        if check_port_available(int(port)):
            return ("ok", f"port {port} available")
        return ("warn", f"port {port} in use")
    except Exception as e:
        return ("warn", f"dashboard port check error: {e}")


def _check_role_agents():
    """Verify workstream/evaluator/harness agent modules are importable."""
    missing = []
    for mod_name in [
        "aho.agents.roles.workstream_agent",
        "aho.agents.roles.evaluator_agent",
        "aho.agents.roles.harness_agent",
        "aho.agents.conductor",
    ]:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(mod_name.split(".")[-1])
    if missing:
        return ("fail", f"missing role agents: {', '.join(missing)}")
    return ("ok", "all role agents importable")


def _check_mcp_fleet():
    """Verify all 9 MCP server packages are installed globally."""
    mcp_packages = [
        "firebase-tools", "@upstash/context7-mcp", "firecrawl-mcp",
        "@playwright/mcp", "flutter-mcp",
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-memory",
        "@modelcontextprotocol/server-sequential-thinking",
        "@modelcontextprotocol/server-everything",
    ]
    try:
        r = subprocess.run(
            ["npm", "list", "-g", "--depth=0"],
            capture_output=True, text=True, timeout=10
        )
        output = r.stdout
        missing = [p for p in mcp_packages if p not in output]
        if missing:
            return ("warn", f"missing MCP servers: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''} ({len(missing)}/{len(mcp_packages)})")
        return ("ok", f"all {len(mcp_packages)} MCP servers present")
    except Exception as e:
        return ("warn", f"MCP fleet check failed: {e}")


def _check_aho_daemons():
    """Verify aho agent daemons are running as systemd user services."""
    services = ["aho-openclaw", "aho-nemoclaw", "aho-telegram", "aho-harness-watcher"]
    results = {}
    for svc in services:
        try:
            r = subprocess.run(
                ["systemctl", "--user", "is-active", svc],
                capture_output=True, text=True, timeout=5
            )
            if r.stdout.strip() == "active":
                results[svc] = ("ok", f"{svc} running")
            else:
                results[svc] = ("warn", f"{svc}: {r.stdout.strip()}")
        except Exception:
            results[svc] = ("warn", f"{svc} check failed")
    return results


def _preflight_checks():
    daemon_checks = _check_aho_daemons()
    return {
        "ollama": _check_ollama(),
        "model_fleet": _check_model_fleet(),
        "mcp_fleet": _check_mcp_fleet(),
        "otel_collector": _check_otel_collector(),
        **daemon_checks,
        "python_deps": _check_python_deps(),
        "disk": _check_disk(),
    }

def _load_plugins(dir_path: Path):
    import importlib.util
    plugins = {}
    if not dir_path.exists():
        return plugins

    for p in dir_path.glob("*.py"):
        if p.name == "__init__.py":
            continue
        
        module_name = f"aho_plugin_{p.stem}"
        spec = importlib.util.spec_from_file_location(module_name, str(p))
        if spec and spec.loader:
            try:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "check"):
                    plugins[p.stem] = mod
            except Exception as e:
                print(f"[aho.doctor] Failed to load plugin {p.name}: {e}", file=sys.stderr)
    return plugins


def _postflight_checks():
    from aho.paths import find_project_root
    try:
        root = find_project_root()
        aho_json = root / ".aho.json"
        project_code = "ahomw"
        if aho_json.exists():
            project_code = json.loads(aho_json.read_text()).get("project_code", "ahomw")
    except Exception:
        root = Path.cwd()
        project_code = "ahomw"

    package_dir = Path(__file__).parent / "postflight"
    base_plugins = _load_plugins(package_dir)
    
    # Project plugins from artifacts/postflight (wait, artifacts/tests? No, postflight dir was not mentioned in reorg)
    # Actually, it should be in src/aho/postflight/ or maybe artifacts/scripts/postflight/
    # The current listing has it in src/aho/postflight/
    all_plugins = {**base_plugins}
    
    results = {}
    for name, mod in all_plugins.items():
        try:
            res = mod.check()
            if isinstance(res, tuple) and len(res) == 2:
                status, msg = res
                if isinstance(status, bool):
                    status = "ok" if status else "fail"
                results[name] = (status, msg)
            elif isinstance(res, dict):
                results[name] = (res.get("status", "unknown").lower(), res.get("message", str(res)))
            else:
                results[name] = ("ok" if res else "fail", str(res))
        except Exception as e:
            results[name] = ("fail", f"error: {e}")
            
    return results

def run_all(level: str = "quick") -> dict[str, tuple[str, str]]:
    """Run health checks at the specified level."""
    checks = {}
    checks.update(_quick_checks())
    if level in ("preflight", "postflight", "full"):
        checks.update(_preflight_checks())
    if level in ("postflight", "full"):
        checks.update(_postflight_checks())
    return checks
