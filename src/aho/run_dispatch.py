"""aho run dispatch — connects to OpenClaw daemon and dispatches a task.

0.2.10 W7 — Persona 3 entry point implementation.
Reads pwd, connects to openclaw socket, sends run command, streams result.
"""
import json
import os
import socket
from pathlib import Path


def _get_socket_path() -> Path:
    """Get OpenClaw socket path from XDG_RUNTIME_DIR."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(runtime_dir) / "openclaw.sock"


def dispatch_run(
    task: str,
    cwd: str,
    agent_hint: str = None,
    dry_run: bool = False,
    timeout: float = 120.0,
) -> dict:
    """Dispatch a task to the OpenClaw daemon via Unix socket.

    Returns dict with keys: ok, response, output_path, model, error.
    """
    sock_path = _get_socket_path()

    if dry_run:
        print(f"[DRY RUN] aho run")
        print(f"  task:   {task}")
        print(f"  cwd:    {cwd}")
        print(f"  agent:  {agent_hint or 'auto'}")
        print(f"  socket: {sock_path}")
        return {"ok": True, "response": "(dry run)", "output_path": None}

    if not sock_path.exists():
        return {
            "ok": False,
            "error": f"OpenClaw daemon not running (no socket at {sock_path}). "
                     "Start with: systemctl --user start aho-openclaw",
        }

    # Build request
    request = {
        "cmd": "run",
        "task": task,
        "cwd": str(cwd),
    }
    if agent_hint:
        request["agent_hint"] = agent_hint

    # Connect and send
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(str(sock_path))
        s.sendall((json.dumps(request) + "\n").encode("utf-8"))

        # Read response
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()

        result = json.loads(data.decode("utf-8").strip())

        if result.get("ok"):
            print(result.get("response", ""))
            output_path = result.get("output_path")
            if output_path:
                print(f"\nOutput written to: {output_path}")

        return result

    except socket.timeout:
        return {"ok": False, "error": f"Timed out after {timeout}s waiting for response"}
    except ConnectionRefusedError:
        return {"ok": False, "error": "Connection refused — OpenClaw daemon may have crashed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
