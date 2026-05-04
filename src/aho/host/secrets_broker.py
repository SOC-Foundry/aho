"""secrets_broker — host-side unix-socket broker for container secrets.

Responsibilities:
- Listen on ${XDG_RUNTIME_DIR}/aho-secrets.sock (mode 0600).
- Authenticate connecting peer via SO_PEERCRED (Linux ucred struct).
- Maintain an in-memory map of registered UIDs → project labels.
- Allow control ops (register, unregister, status, shutdown) only from the
  broker-owner UID — i.e., the host user who started the broker.
- Allow data op (get_secret) only from a registered UID, and only when the
  requested project matches the registration's project label.
- Return the secret value via existing aho.secrets.store.get_secret. Never
  enumerate the keystore. Never log the secret value — only the request shape.

Protocol: line-delimited JSON. One request, one response, server closes.

Pillar 11: broker NEVER touches git. Broker NEVER writes to the secrets
store — read-only round-trips against the operator-controlled store.
"""
from __future__ import annotations

import json
import os
import socket
import struct
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

# SO_PEERCRED returns struct ucred { pid: int32, uid: uint32, gid: uint32 }
# on Linux. Total wire size: 12 bytes. Format string per `man 7 socket`.
_UCRED_STRUCT = "iII"
_UCRED_SIZE = struct.calcsize(_UCRED_STRUCT)


def default_socket_path() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        raise RuntimeError("XDG_RUNTIME_DIR not set; broker requires it for socket path")
    return Path(runtime_dir) / "aho-secrets.sock"


@dataclass
class Registration:
    uid: int
    project: str


class SecretsBroker:
    """In-process broker. start() runs blocking; serve_forever() blocks the caller."""

    def __init__(self, socket_path: Optional[Path] = None) -> None:
        self.socket_path: Path = socket_path or default_socket_path()
        self.owner_uid: int = os.getuid()
        self._registrations: Dict[int, Registration] = {}
        self._lock = threading.Lock()
        self._server_socket: Optional[socket.socket] = None
        self._stop = threading.Event()

    # --- registration management (in-memory) -------------------------------

    def register(self, uid: int, project: str) -> None:
        with self._lock:
            self._registrations[uid] = Registration(uid=uid, project=project)

    def unregister(self, uid: int) -> None:
        with self._lock:
            self._registrations.pop(uid, None)

    def lookup(self, uid: int) -> Optional[Registration]:
        with self._lock:
            return self._registrations.get(uid)

    def registrations(self) -> Dict[int, Registration]:
        with self._lock:
            return dict(self._registrations)

    # --- transport ---------------------------------------------------------

    def listen(self) -> socket.socket:
        if self.socket_path.exists():
            self.socket_path.unlink()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(self.socket_path))
        os.chmod(self.socket_path, 0o600)
        srv.listen(8)
        self._server_socket = srv
        return srv

    def stop(self) -> None:
        self._stop.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass

    def serve_forever(self) -> None:
        if self._server_socket is None:
            self.listen()
        sys.stdout.write(f"LISTENING {self.socket_path}\n")
        sys.stdout.flush()
        while not self._stop.is_set():
            try:
                conn, _addr = self._server_socket.accept()  # type: ignore[union-attr]
            except OSError:
                # socket closed during shutdown
                break
            t = threading.Thread(target=self._handle, args=(conn,), daemon=True)
            t.start()

    # --- per-connection handler --------------------------------------------

    @staticmethod
    def _read_peer_uid(conn: socket.socket) -> int:
        creds = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, _UCRED_SIZE)
        _pid, uid, _gid = struct.unpack(_UCRED_STRUCT, creds)
        return uid

    def _handle(self, conn: socket.socket) -> None:
        try:
            peer_uid = self._read_peer_uid(conn)
            data = self._read_line(conn)
            if data is None:
                self._write(conn, {"ok": False, "error": "empty_request"})
                return
            try:
                request = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                self._write(conn, {"ok": False, "error": "malformed_json"})
                return
            response = self._dispatch(peer_uid, request)
            self._write(conn, response)
        finally:
            try:
                conn.close()
            except OSError:
                pass

    @staticmethod
    def _read_line(conn: socket.socket, max_bytes: int = 65536) -> Optional[bytes]:
        buf = bytearray()
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                return bytes(buf) if buf else None
            buf.extend(chunk)
            if b"\n" in buf:
                return bytes(buf.split(b"\n", 1)[0])
            if len(buf) > max_bytes:
                return bytes(buf[:max_bytes])

    @staticmethod
    def _write(conn: socket.socket, response: dict) -> None:
        line = (json.dumps(response) + "\n").encode("utf-8")
        try:
            conn.sendall(line)
        except OSError:
            pass

    # --- request dispatch --------------------------------------------------

    def _dispatch(self, peer_uid: int, request: dict) -> dict:
        op = request.get("op")
        if op in ("register", "unregister", "status", "shutdown"):
            if peer_uid != self.owner_uid:
                self._log_request(peer_uid, op, project=request.get("project"), name=None,
                                  outcome="auth_failed_control")
                return {"ok": False, "error": "auth_failed"}
            return self._dispatch_control(op, request)
        if op == "get_secret":
            return self._dispatch_data(peer_uid, request)
        return {"ok": False, "error": f"unknown_op:{op}"}

    def _dispatch_control(self, op: str, request: dict) -> dict:
        if op == "register":
            uid = request.get("uid")
            project = request.get("project")
            if not isinstance(uid, int) or not isinstance(project, str) or not project:
                return {"ok": False, "error": "bad_request"}
            self.register(uid, project)
            self._log_request(uid, "register", project=project, name=None, outcome="ok")
            return {"ok": True}
        if op == "unregister":
            uid = request.get("uid")
            if not isinstance(uid, int):
                return {"ok": False, "error": "bad_request"}
            self.unregister(uid)
            self._log_request(uid, "unregister", project=None, name=None, outcome="ok")
            return {"ok": True}
        if op == "status":
            regs = self.registrations()
            return {
                "ok": True,
                "owner_uid": self.owner_uid,
                "registrations": [
                    {"uid": r.uid, "project": r.project} for r in regs.values()
                ],
            }
        if op == "shutdown":
            self._log_request(self.owner_uid, "shutdown", project=None, name=None, outcome="ok")
            response = {"ok": True}
            # Defer actual stop until after we send the response.
            threading.Thread(target=self.stop, daemon=True).start()
            return response
        return {"ok": False, "error": f"unknown_control:{op}"}

    def _dispatch_data(self, peer_uid: int, request: dict) -> dict:
        project = request.get("project")
        name = request.get("name")
        if not isinstance(project, str) or not isinstance(name, str) or not project or not name:
            return {"ok": False, "error": "bad_request"}
        registration = self.lookup(peer_uid)
        if registration is None:
            self._log_request(peer_uid, "get_secret", project=project, name=name,
                              outcome="uid_not_registered")
            return {"ok": False, "error": "uid_not_registered"}
        if registration.project != project:
            self._log_request(peer_uid, "get_secret", project=project, name=name,
                              outcome="project_mismatch")
            return {"ok": False, "error": "project_mismatch"}
        try:
            from aho.secrets.store import get_secret
            value = get_secret(project, name)
        except RuntimeError as exc:
            self._log_request(peer_uid, "get_secret", project=project, name=name,
                              outcome=f"store_locked")
            return {"ok": False, "error": "store_locked", "detail": str(exc)}
        self._log_request(peer_uid, "get_secret", project=project, name=name,
                          outcome="ok" if value is not None else "missing")
        return {"ok": True, "value": value}

    @staticmethod
    def _log_request(uid: int, op: str, project: Optional[str], name: Optional[str],
                     outcome: str) -> None:
        # Request shape only — never the secret value.
        sys.stdout.write(
            f"BROKER op={op} uid={uid} project={project} name={name} outcome={outcome}\n"
        )
        sys.stdout.flush()


def run_broker_cli(argv: Optional[list[str]] = None) -> int:
    """Entry point for `aho host secrets-broker` subcommand."""
    import argparse
    p = argparse.ArgumentParser(prog="aho host secrets-broker")
    p.add_argument("--socket", type=Path, default=None,
                   help="Override socket path (default: $XDG_RUNTIME_DIR/aho-secrets.sock)")
    p.add_argument("--start", action="store_true",
                   help="Start the broker (foreground; daemonize externally if desired)")
    p.add_argument("--status", action="store_true",
                   help="Connect to a running broker and print its registration table")
    p.add_argument("--shutdown", action="store_true",
                   help="Connect to a running broker and request shutdown")
    args = p.parse_args(argv)

    if not (args.start or args.status or args.shutdown):
        p.error("one of --start, --status, --shutdown required")

    if args.start:
        broker = SecretsBroker(socket_path=args.socket)
        try:
            broker.serve_forever()
        except KeyboardInterrupt:
            broker.stop()
        return 0

    # --status / --shutdown: client mode against a running broker.
    return _broker_client(args)


def _broker_client(args) -> int:
    path = args.socket or default_socket_path()
    if not path.exists():
        sys.stderr.write(f"broker socket not present at {path}\n")
        return 2
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    try:
        sock.connect(str(path))
        op = "shutdown" if args.shutdown else "status"
        sock.sendall((json.dumps({"op": op}) + "\n").encode("utf-8"))
        buf = bytearray()
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
            if b"\n" in buf:
                break
        line = buf.split(b"\n", 1)[0]
        sys.stdout.write(line.decode("utf-8") + "\n")
        return 0
    except OSError as exc:
        sys.stderr.write(f"broker connection failed: {exc}\n")
        return 3
    finally:
        sock.close()


if __name__ == "__main__":
    sys.exit(run_broker_cli())
