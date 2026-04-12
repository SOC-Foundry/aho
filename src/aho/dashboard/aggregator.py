"""Dashboard state aggregator.

Collects system, component, daemon, trace, MCP, and model state
into a single JSON-serialisable dict for /api/state.

All data sources are existing files or wrapper outputs.
No mutations. Read-only aggregation with 2s cache.
"""
import json
import subprocess
import time
from pathlib import Path

from aho.paths import find_project_root, get_data_dir

_cache = {"data": None, "ts": 0}
_CACHE_TTL = 2  # seconds


def get_state(force: bool = False) -> dict:
    """Return full dashboard state dict, cached for _CACHE_TTL seconds."""
    now = time.time()
    if not force and _cache["data"] and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["data"]

    state = {
        "system": _system_state(),
        "components": _component_state(),
        "daemons": _daemon_state(),
        "traces": _trace_state(),
        "mcp": _mcp_state(),
        "models": _model_state(),
        "install": _install_completeness(),
    }
    _cache["data"] = state
    _cache["ts"] = now
    return state


def _system_state() -> dict:
    """Read iteration metadata from .aho.json and .aho-checkpoint.json."""
    root = find_project_root()
    result = {"iteration": "unknown", "phase": 0, "run_type": "unknown", "last_close": None}

    aho_json = root / ".aho.json"
    if aho_json.exists():
        data = json.loads(aho_json.read_text())
        result["iteration"] = data.get("current_iteration", "unknown")
        result["phase"] = data.get("phase", 0)

    ckpt = root / ".aho-checkpoint.json"
    if ckpt.exists():
        data = json.loads(ckpt.read_text())
        result["run_type"] = data.get("run_type", "unknown")
        result["last_close"] = data.get("closed_at")
        result["status"] = data.get("status")
        result["current_workstream"] = data.get("current_workstream")

    return result


def _component_state() -> list:
    """Parse components.yaml and return list of component dicts with status."""
    root = find_project_root()
    components_path = root / "artifacts" / "harness" / "components.yaml"
    if not components_path.exists():
        return []

    try:
        import yaml
    except ImportError:
        # Fall back to basic parsing if pyyaml not available
        return _parse_components_basic(components_path)

    data = yaml.safe_load(components_path.read_text())
    components = data.get("components", [])
    result = []
    for comp in components:
        entry = {
            "name": comp.get("name", "unknown"),
            "kind": comp.get("kind", "unknown"),
            "path": comp.get("path", ""),
            "status": comp.get("status", "unknown"),
            "owner": comp.get("owner", ""),
            "notes": comp.get("notes", ""),
            "verified": _verify_component(comp, root),
        }
        result.append(entry)
    return result


def _parse_components_basic(path: Path) -> list:
    """Minimal YAML-ish parser for components.yaml without pyyaml."""
    components = []
    current = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            if current:
                components.append(current)
            current = {"name": stripped.split(":", 1)[1].strip(), "verified": "unknown"}
        elif ":" in stripped and current:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"')
            if key in ("kind", "path", "status", "owner", "notes"):
                current[key] = val
    if current:
        components.append(current)
    return components


def _verify_component(comp: dict, root: Path) -> str:
    """Quick verification of component presence. Returns ok/missing/unknown."""
    kind = comp.get("kind", "")
    path_str = comp.get("path", "")

    if kind == "python_module":
        full = root / path_str
        return "ok" if full.exists() else "missing"

    if kind == "agent":
        full = root / path_str
        return "ok" if full.exists() else "missing"

    if kind == "llm":
        full = root / path_str
        return "ok" if full.exists() else "missing"

    if kind == "external_service":
        full = root / path_str
        return "ok" if full.exists() else "missing"

    if kind == "mcp_server":
        readiness = _load_mcp_readiness()
        comp_name = comp.get("name", "")
        for entry in readiness:
            if comp_name.endswith(entry.get("server", "")) or entry.get("server", "") in comp_name:
                return "ok" if entry.get("cli_smoke") == "pass" else "missing"
        return "unknown"

    return "unknown"


_DAEMONS = ["openclaw", "nemoclaw", "telegram", "harness-watcher", "otel-collector", "jaeger", "dashboard"]


def _daemon_state() -> list:
    """Check systemd user service status for 4 daemons."""
    result = []
    for name in _DAEMONS:
        unit = f"aho-{name}.service"
        status = "unknown"
        try:
            out = subprocess.run(
                ["systemctl", "--user", "is-active", unit],
                capture_output=True, text=True, timeout=5,
            )
            status = out.stdout.strip()
        except Exception:
            pass
        result.append({"name": name, "unit": unit, "status": status})
    return result


def _trace_state() -> list:
    """Return last 20 events from the event log."""
    log_path = get_data_dir() / "aho_event_log.jsonl"
    if not log_path.exists():
        return []
    try:
        lines = log_path.read_text().splitlines()
        tail = lines[-20:] if len(lines) > 20 else lines
        events = []
        for line in reversed(tail):  # newest first
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events
    except Exception:
        return []


def _load_mcp_readiness() -> list:
    """Load smoke test results from data/mcp_readiness.json."""
    readiness_path = get_data_dir() / "mcp_readiness.json"
    if not readiness_path.exists():
        return []
    try:
        data = json.loads(readiness_path.read_text())
        return data.get("results", [])
    except (json.JSONDecodeError, KeyError):
        return []


def _mcp_state() -> list:
    """Check MCP server status via smoke readiness data, npm list, and dart version."""
    npm_packages = [
        "firebase-tools",
        "@upstash/context7-mcp",
        "firecrawl-mcp",
        "@playwright/mcp",
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-memory",
        "@modelcontextprotocol/server-sequential-thinking",
        "@modelcontextprotocol/server-everything",
    ]

    try:
        out = subprocess.run(
            ["npm", "list", "-g", "--depth=0"],
            capture_output=True, text=True, timeout=10,
        )
        installed_text = out.stdout
    except Exception:
        installed_text = ""

    readiness = _load_mcp_readiness()
    readiness_by_server = {r["server"]: r["cli_smoke"] for r in readiness if "server" in r}

    result = []
    for pkg in npm_packages:
        installed = pkg in installed_text
        # Map npm package name to smoke script name
        smoke_name = pkg.split("/")[-1].replace("@", "")
        if pkg == "firebase-tools":
            smoke_name = "firebase-tools"
        elif pkg == "@upstash/context7-mcp":
            smoke_name = "context7"
        elif pkg == "firecrawl-mcp":
            smoke_name = "firecrawl"
        elif pkg == "@playwright/mcp":
            smoke_name = "playwright"

        smoke_status = readiness_by_server.get(smoke_name, "unknown")
        if smoke_status == "pass":
            status = "ok"
        elif installed:
            status = "ok"
        else:
            status = "missing"
        result.append({"name": pkg, "installed": installed, "smoke": smoke_status, "status": status})

    # Dart MCP server (SDK-bundled, not npm)
    try:
        dart_out = subprocess.run(
            ["dart", "--version"], capture_output=True, text=True, timeout=5,
        )
        dart_installed = dart_out.returncode == 0
    except Exception:
        dart_installed = False

    dart_smoke = readiness_by_server.get("dart", "unknown")
    dart_status = "ok" if dart_smoke == "pass" or dart_installed else "missing"
    result.append({"name": "dart-mcp-server", "installed": dart_installed, "smoke": dart_smoke, "status": dart_status})

    return result


def _model_state() -> list:
    """Check ollama model fleet status."""
    root = find_project_root()
    fleet_file = root / "artifacts" / "harness" / "model-fleet.txt"
    if not fleet_file.exists():
        return []

    declared = [
        m.strip() for m in fleet_file.read_text().splitlines()
        if m.strip() and not m.strip().startswith("#")
    ]

    try:
        out = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        )
        installed = [line.split()[0] for line in out.stdout.splitlines()[1:] if line.strip()]
    except Exception:
        installed = []

    result = []
    for model in declared:
        status = "ok" if model in installed else "missing"
        result.append({"name": model, "status": status})
    return result


def _install_completeness() -> dict:
    """Check install completeness for both project-local and system-local components."""
    base_dir = Path.home() / ".local/share/aho"

    # System-local directories
    dirs = {
        "bin": base_dir / "bin",
        "harness": base_dir / "harness",
        "registries": base_dir / "registries",
        "agents": base_dir / "agents",
        "secrets": base_dir / "secrets",
        "runtime": base_dir / "runtime",
        "traces": base_dir / "traces",
        "jaeger": base_dir / "jaeger",
    }
    dir_status = {}
    for name, path in dirs.items():
        dir_status[name] = "present" if path.is_dir() else "missing"

    # CLI symlink
    cli_symlink = Path.home() / ".local/bin/aho"
    cli_status = "present" if cli_symlink.exists() else "missing"

    # System binaries
    binaries = {
        "fish": "fish",
        "python3": "python3",
        "node": "node",
        "npm": "npm",
        "age": "age",
        "jq": "jq",
        "rg": "rg",
        "fd": "fd",
        "ollama": "ollama",
        "otelcol-contrib": "otelcol-contrib",
        "jaeger-all-in-one": "jaeger-all-in-one",
    }
    binary_status = {}
    for name, cmd in binaries.items():
        try:
            result = subprocess.run(
                ["which", cmd], capture_output=True, text=True, timeout=2,
            )
            binary_status[name] = "present" if result.returncode == 0 else "missing"
        except Exception:
            binary_status[name] = "unknown"

    return {
        "base_dir": str(base_dir),
        "directories": dir_status,
        "cli_symlink": cli_status,
        "binaries": binary_status,
    }
