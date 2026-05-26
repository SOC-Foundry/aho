"""_otel_stub - minimal OTEL span helper for council stubs.

W1 stubs need to emit a span per call carrying `stub: true`. The opentelemetry
SDK is already an aho dependency, but the harness's full OTEL init lives in
the host-side aho.otel module (which 0.2.16 W0 set up). For container-resident
stubs we want a lightweight call site that uses whichever tracer provider is
already configured, falling back to a no-op tracer if OTEL is not installed
or initialised.

This is deliberately not a full-stack OTEL setup - that is W2's job. W1's bar
is that the call site exists, the span name is correct, and the attributes
are well-formed.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

try:
    from opentelemetry import trace
    _tracer = trace.get_tracer("aho.council.stub")
    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover - opentelemetry is a hard dep
    _tracer = None
    _OTEL_AVAILABLE = False


def emit_stub_span(name: str, attributes: Optional[Mapping[str, Any]] = None) -> None:
    """Open + close a span with the given name + attrs. Synchronous; no-op
    if OTEL is unavailable.
    """
    if not _OTEL_AVAILABLE or _tracer is None:
        return
    attrs = dict(attributes or {})
    with _tracer.start_as_current_span(name) as span:
        for k, v in attrs.items():
            try:
                span.set_attribute(k, v)
            except Exception:
                # Span attribute rejection is a soft failure - never block stub work.
                pass
