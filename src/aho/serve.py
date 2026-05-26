"""serve - `aho serve` ready-and-waiting mode for the W1 container.

Sequence at start:
  1. Install SIGTERM/SIGINT handlers (aho.signal).
  2. Run tier auto-detect, persist marker file.
  3. Start /healthz + /readyz HTTP server on AHO_HEALTH_PORT.
  4. Register readiness probes for: tier-detect-complete, secrets-broker-
     reachable, council-stubs-importable. /readyz transitions 503→200 once
     all probes return True.
  5. Wait on the shutdown event. On SIGTERM: drain ≤30s, flush OTEL, exit 0.

This module is the container's CMD. The harness baseline assumes the entry
point holds the container alive after readiness; W2 is the iteration that
adds in-flight work (council wrappers, ChromaDB writes).
"""
from __future__ import annotations

import os
import sys
import time
from typing import Optional

from . import health
from . import signal as aho_signal
from . import tier_detect


class _State:
    tier: Optional[str] = None
    tier_detect_complete: bool = False
    council_imports_ok: bool = False


def _probe_tier_detect_complete() -> bool:
    return _State.tier_detect_complete


def _probe_council_imports_ok() -> bool:
    return _State.council_imports_ok


def _probe_secrets_broker_reachable() -> bool:
    """Soft probe - broker reachability is required for FULL readiness, but
    we do not block start on the broker being absent (tests may not start it).
    Caller can disable this probe via AHO_REQUIRE_BROKER=0.
    """
    require = os.environ.get("AHO_REQUIRE_BROKER", "1") != "0"
    if not require:
        return True
    try:
        from . import secrets_client
        return secrets_client.is_reachable(timeout=0.5)
    except Exception:
        return False


def _try_council_imports() -> bool:
    try:
        from .council import dispatch as _dispatch  # noqa: F401
        from .council import triage as _triage      # noqa: F401
        from .council import audit as _audit        # noqa: F401
        from .council import embed as _embed        # noqa: F401
    except Exception as exc:
        sys.stderr.write(f"council import failed: {exc}\n")
        return False
    return True


def _flush_otel() -> None:
    """Best-effort OTEL flush at shutdown. No-op if OTEL is not initialised."""
    try:
        from opentelemetry import trace
        provider = trace.get_tracer_provider()
        flush = getattr(provider, "force_flush", None)
        if flush is not None:
            flush(timeout_millis=5_000)
    except Exception:
        pass


def serve_main(argv: Optional[list[str]] = None) -> int:
    aho_signal.install_handlers()

    # Probe tier and persist marker.
    try:
        _State.tier = tier_detect.detect_tier()
        try:
            tier_detect.write_tier_file(_State.tier)
        except OSError as exc:
            # /var/run/aho may be read-only in some hosts; log + continue.
            sys.stderr.write(f"tier marker file write failed: {exc}\n")
        _State.tier_detect_complete = True
        sys.stdout.write(f"TIER {_State.tier}\n")
        sys.stdout.flush()
    except tier_detect.TierDetectError as exc:
        sys.stderr.write(f"tier-detect failed: {exc}\n")
        # Mark complete with a default of base - base-tier is the safe assumption.
        _State.tier = "base"
        _State.tier_detect_complete = True

    # Verify council stubs import cleanly.
    _State.council_imports_ok = _try_council_imports()

    # Register readiness probes.
    health.add_readiness_probe("tier_detect", _probe_tier_detect_complete)
    health.add_readiness_probe("council_imports", _probe_council_imports_ok)
    health.add_readiness_probe("secrets_broker", _probe_secrets_broker_reachable)

    # Start HTTP server.
    server = health.start()
    sys.stdout.write(f"HEALTH {server.server_address[0]}:{server.server_address[1]}\n")
    sys.stdout.flush()

    sys.stdout.write("READY\n")
    sys.stdout.flush()

    # Wait for shutdown signal.
    aho_signal.wait_for_shutdown()
    sys.stdout.write("DRAIN_START\n")
    sys.stdout.flush()

    drain_deadline = time.monotonic() + 30.0
    # Components have no in-flight work in W1, so drain is a no-op past
    # health-server shutdown. Reserve the budget for W2 to fill.
    while time.monotonic() < drain_deadline and not _drain_done():
        time.sleep(0.1)

    health.stop()
    _flush_otel()
    sys.stdout.write("EXIT\n")
    sys.stdout.flush()
    return 0


def _drain_done() -> bool:
    # W1 has no in-flight work; the drain is complete the moment SIGTERM
    # arrives. W2 wires real component-quiesce checks here.
    return True
