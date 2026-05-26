"""run_container - host wrapper that registers + launches + unregisters a container.

Flow:
  1. Compute the host-visible UID the container will appear as. For default
     rootless podman without --user, the in-container root maps to the host
     user's UID (os.getuid()).
  2. POST register {uid, project} to the broker.
  3. Exec `podman run` with the broker socket bind-mounted read-only into the
     container at /run/host-services/aho-secrets.sock. Block on the run.
  4. POST unregister {uid} to the broker. Always runs, even on failure.

Pillar 11: this script does not invoke git, does not push, does not commit.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import socket
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def _send_to_broker(socket_path: Path, payload: dict, timeout: float = 3.0) -> dict:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(socket_path))
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        buf = bytearray()
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            if b"\n" in buf:
                break
        line = buf.split(b"\n", 1)[0]
        return json.loads(line.decode("utf-8"))
    finally:
        sock.close()


def run_container_cli(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="aho host run-container",
        description="Register UID with the broker, podman run, unregister on exit.",
    )
    p.add_argument("--project", required=True,
                   help="Project label to register with the broker (e.g. ahomw)")
    p.add_argument("--image", required=True, help="Container image tag")
    p.add_argument("--uid", type=int, default=None,
                   help="Host-visible UID the container will appear as. "
                        "Default: os.getuid() (default rootless podman behaviour).")
    p.add_argument("--socket", type=Path, default=None,
                   help="Broker socket path (default: $XDG_RUNTIME_DIR/aho-secrets.sock)")
    p.add_argument("--podman-flag", action="append", default=[],
                   help="Extra flag for `podman run`. Repeatable.")
    p.add_argument("cmd", nargs=argparse.REMAINDER,
                   help="Command to run inside the container (after `--`).")
    args = p.parse_args(argv)

    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        sys.stderr.write("XDG_RUNTIME_DIR not set\n")
        return 2
    socket_path = args.socket or Path(runtime_dir) / "aho-secrets.sock"
    if not socket_path.exists():
        sys.stderr.write(
            f"broker socket not present at {socket_path}; start with "
            f"`aho host secrets-broker --start`\n"
        )
        return 2
    container_uid = args.uid if args.uid is not None else os.getuid()

    register_resp = _send_to_broker(
        socket_path, {"op": "register", "uid": container_uid, "project": args.project}
    )
    if not register_resp.get("ok"):
        sys.stderr.write(f"broker register failed: {register_resp}\n")
        return 3

    cmd_argv = args.cmd[:]
    if cmd_argv and cmd_argv[0] == "--":
        cmd_argv = cmd_argv[1:]

    podman_argv = [
        "podman", "run", "--rm",
        "--name", f"aho-w1-{os.getpid()}",
        "-v", f"{socket_path}:/run/host-services/aho-secrets.sock:ro",
        "-e", f"AHO_SECRETS_SOCKET=/run/host-services/aho-secrets.sock",
    ]
    podman_argv.extend(args.podman_flag)
    podman_argv.append(args.image)
    podman_argv.extend(cmd_argv)

    sys.stdout.write(
        f"RUN-CONTAINER project={args.project} uid={container_uid} cmd={shlex.join(podman_argv)}\n"
    )
    sys.stdout.flush()

    try:
        result = subprocess.run(podman_argv)
        return result.returncode
    finally:
        try:
            _send_to_broker(socket_path, {"op": "unregister", "uid": container_uid})
        except OSError as exc:
            sys.stderr.write(f"broker unregister failed (non-fatal): {exc}\n")


if __name__ == "__main__":
    sys.exit(run_container_cli())
