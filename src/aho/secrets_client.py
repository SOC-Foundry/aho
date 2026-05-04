"""secrets_client — container-side client for the host secrets broker.

Connects to the host-mounted unix socket at AHO_SECRETS_SOCKET (default
/run/host-services/aho-secrets.sock). Sends a single JSON-line request,
reads a single JSON-line response, closes the connection.

Same get_secret(project, name) signature as src/aho/secrets/store.py:62
so call sites switching from the in-process backend to the broker do not
change shape.
"""
from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Optional

DEFAULT_SOCKET_PATH = "/run/host-services/aho-secrets.sock"
DEFAULT_TIMEOUT_SECONDS = 5.0


class SecretsBrokerError(RuntimeError):
    pass


class SecretsBrokerAuthError(SecretsBrokerError):
    pass


class SecretsBrokerUnreachable(SecretsBrokerError):
    pass


def socket_path() -> Path:
    return Path(os.environ.get("AHO_SECRETS_SOCKET", DEFAULT_SOCKET_PATH))


def is_reachable(timeout: float = 1.0) -> bool:
    """Return True if the broker socket exists and accepts a connection."""
    path = socket_path()
    if not path.exists():
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _request(payload: dict, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    path = socket_path()
    if not path.exists():
        raise SecretsBrokerUnreachable(f"broker socket not present at {path}")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        try:
            sock.connect(str(path))
        except OSError as exc:
            raise SecretsBrokerUnreachable(f"connect failed: {exc}") from exc
        line = (json.dumps(payload) + "\n").encode("utf-8")
        sock.sendall(line)
        buf = bytearray()
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            if b"\n" in buf:
                break
        if not buf:
            raise SecretsBrokerError("broker returned empty response")
        first_line = buf.split(b"\n", 1)[0]
        try:
            response = json.loads(first_line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SecretsBrokerError(f"broker returned non-JSON response: {first_line!r}") from exc
    finally:
        sock.close()
    return response


def get_secret(project: str, name: str, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> Optional[str]:
    """Round-trip get_secret(project, name) through the host broker.

    Raises SecretsBrokerAuthError on auth failure (UID/project mismatch).
    Raises SecretsBrokerUnreachable if the socket is missing or unreachable.
    Returns None if the secret is not present in the host store.
    Returns the decrypted string value on success.
    """
    response = _request(
        {"op": "get_secret", "project": project, "name": name},
        timeout=timeout,
    )
    if not response.get("ok"):
        error = response.get("error", "unknown")
        if error in ("auth_failed", "uid_not_registered", "project_mismatch"):
            raise SecretsBrokerAuthError(error)
        raise SecretsBrokerError(error)
    if "value" not in response:
        return None
    return response["value"]
