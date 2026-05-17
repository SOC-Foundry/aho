"""health — /healthz and /readyz endpoints on AHO_HEALTH_PORT (default 8080).

/healthz: 200 if the process is alive (unconditional once handler is registered).
/readyz: 200 only after each registered readiness probe returns True. 503 otherwise.

Probes register via add_readiness_probe(name, callable). The callable returns
bool — True = ready, False = not yet. Default state during startup is 503.
"""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, List

_probes: Dict[str, Callable[[], bool]] = {}
_lock = threading.Lock()
_server: ThreadingHTTPServer | None = None
_thread: threading.Thread | None = None


def add_readiness_probe(name: str, fn: Callable[[], bool]) -> None:
    with _lock:
        _probes[name] = fn


def list_probe_names() -> List[str]:
    with _lock:
        return sorted(_probes.keys())


def _evaluate_readiness() -> tuple[bool, Dict[str, bool]]:
    with _lock:
        probes = dict(_probes)
    results = {}
    overall = True
    for name, fn in probes.items():
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        results[name] = ok
        if not ok:
            overall = False
    return overall, results


class _Handler(BaseHTTPRequestHandler):
    server_version = "aho-health/0.2.18"

    def log_message(self, format, *args):  # noqa: A002, ARG002
        # Quiet stdlib's per-request stderr line — we route via aho.logger if needed.
        return

    def _write_json(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):  # noqa: N802
        if self.path == "/healthz":
            self._write_json(200, {"status": "ok"})
            return
        if self.path == "/readyz":
            ready, results = _evaluate_readiness()
            self._write_json(
                200 if ready else 503,
                {"ready": ready, "probes": results},
            )
            return
        self._write_json(404, {"error": "not_found", "path": self.path})


def start(port: int | None = None, host: str = "0.0.0.0") -> ThreadingHTTPServer:
    """Start the health HTTP server in a background thread. Idempotent."""
    global _server, _thread
    if _server is not None:
        return _server
    bind_port = int(port if port is not None else os.environ.get("AHO_HEALTH_PORT", 8080))
    _server = ThreadingHTTPServer((host, bind_port), _Handler)
    _thread = threading.Thread(
        target=_server.serve_forever,
        name="aho-health",
        daemon=True,
    )
    _thread.start()
    return _server


def stop(timeout: float = 5.0) -> None:
    global _server, _thread
    if _server is not None:
        _server.shutdown()
        _server.server_close()
        _server = None
    if _thread is not None:
        _thread.join(timeout=timeout)
        _thread = None
