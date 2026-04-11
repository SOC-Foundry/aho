"""Configuration and validation for aho."""
import json
import re
import socket
from pathlib import Path


IAO_VERSION_REGEX = re.compile(r"^\d+\.\d+\.\d+$")

# Machine-specific dashboard port defaults
_MACHINE_PORTS = {
    "NZXTcos": 7800,
    "P3": 7900,
}

_DEFAULT_PORT = 7800
_DEFAULT_ROLE = "localhost"


def validate_iteration_version(version: str) -> None:
    """Raise ValueError if version string is not exactly three octets.

    aho versioning is locked to X.Y.Z. The Z field is the iteration
    run number, not a patch or minor. Four-octet versioning is a
    pattern-match error from kjtcom and must be rejected.
    """
    if not isinstance(version, str):
        raise ValueError(f"Version must be string, got {type(version).__name__}")
    if not IAO_VERSION_REGEX.match(version):
        raise ValueError(
            f"Iteration version '{version}' does not match X.Y.Z three-octet format. "
            f"aho versioning is locked to three octets; see aho-G107 in gotcha registry."
        )


def get_dashboard_port(aho_json_path: Path = None) -> int:
    """Read dashboard_port from .aho.json, defaulting by machine name."""
    if aho_json_path is None:
        from aho.paths import find_project_root
        aho_json_path = find_project_root() / ".aho.json"

    if aho_json_path.exists():
        data = json.loads(aho_json_path.read_text())
        port = data.get("dashboard_port")
        if port is not None:
            return int(port)

    hostname = socket.gethostname()
    return _MACHINE_PORTS.get(hostname, _DEFAULT_PORT)


def get_aho_role(aho_json_path: Path = None) -> str:
    """Read aho_role from .aho.json, defaulting to 'localhost'."""
    if aho_json_path is None:
        from aho.paths import find_project_root
        aho_json_path = find_project_root() / ".aho.json"

    if aho_json_path.exists():
        data = json.loads(aho_json_path.read_text())
        return data.get("aho_role", _DEFAULT_ROLE)

    return _DEFAULT_ROLE


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if port is bindable on the given host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False
