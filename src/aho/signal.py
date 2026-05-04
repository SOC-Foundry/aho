"""signal — SIGTERM / SIGINT graceful-drain primitive for the container.

Sets a process-global shutdown flag readable by all components. Caller is
responsible for noticing the flag in their loops. Caller is also responsible
for installing the handler at process start (idempotent).

Drain budget per ADR 0007 §k8s-readiness: ≤30s. The handler itself does not
sleep — components are expected to exit their work loops promptly. Flush of
OTEL is left to caller's exit path.
"""
from __future__ import annotations

import signal as _stdlib_signal
import threading
from typing import Callable, List

_shutdown = threading.Event()
_handlers_installed = False
_callbacks: List[Callable[[], None]] = []


def shutdown_initiated() -> bool:
    return _shutdown.is_set()


def wait_for_shutdown(timeout: float | None = None) -> bool:
    """Block until shutdown is requested (or timeout). Returns True if signaled."""
    return _shutdown.wait(timeout)


def request_shutdown() -> None:
    """Programmatic trigger — equivalent to receiving SIGTERM."""
    _shutdown.set()
    for cb in list(_callbacks):
        try:
            cb()
        except Exception:
            # A failing callback must not block other callbacks or the shutdown.
            # We deliberately swallow here; components are responsible for their own logging.
            pass


def register_shutdown_callback(cb: Callable[[], None]) -> None:
    _callbacks.append(cb)


def _handler(signum, _frame):  # noqa: ARG001
    request_shutdown()


def install_handlers() -> None:
    """Install SIGTERM + SIGINT → request_shutdown. Idempotent."""
    global _handlers_installed
    if _handlers_installed:
        return
    _stdlib_signal.signal(_stdlib_signal.SIGTERM, _handler)
    _stdlib_signal.signal(_stdlib_signal.SIGINT, _handler)
    _handlers_installed = True


def reset_for_tests() -> None:
    """Test-only — clears flag, callbacks, and handler-installed state."""
    global _handlers_installed
    _shutdown.clear()
    _callbacks.clear()
    _handlers_installed = False
