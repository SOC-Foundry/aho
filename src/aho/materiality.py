"""aho.materiality - OTEL counter primitives for the four-bucket protocol.

Counters (per ADR-0010 materiality measurement protocol):
  - claim_vs_artifact_mismatches.caught_by_llama      (incremented in W2)
  - claim_vs_artifact_mismatches.caught_by_drafter    (placeholder, W3 wires)
  - claim_vs_artifact_mismatches.escaped              (placeholder, W3 wires)
  - carry_forward_resolution_rate                     (placeholder, W3 wires)

W2's bar: OTEL signals emit, structurally correct. Downstream renderer
(claw3d brick) lands in W3. The counters are real OTEL Counter
instruments under the global MeterProvider - whether the recorded
measurements reach an exporter depends on the host OTEL config.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

try:
    from opentelemetry import metrics as _otel_metrics
    _meter = _otel_metrics.get_meter("aho.materiality")
    _otel_available = True
except ImportError:  # pragma: no cover
    _otel_metrics = None
    _meter = None
    _otel_available = False


COUNTER_NAMES = (
    "aho.materiality.claim_vs_artifact_mismatches.caught_by_llama",
    "aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter",
    "aho.materiality.claim_vs_artifact_mismatches.escaped",
    "aho.materiality.carry_forward_resolution_rate",
)


def _build_counters() -> Dict[str, Any]:
    if not _otel_available or _meter is None:
        return {name: None for name in COUNTER_NAMES}
    return {
        name: _meter.create_counter(
            name,
            description=_DESCRIPTIONS[name],
            unit="1",
        )
        for name in COUNTER_NAMES
    }


_DESCRIPTIONS = {
    "aho.materiality.claim_vs_artifact_mismatches.caught_by_llama":
        "Count of executor claim/artifact mismatches surfaced by the llama auditor seat.",
    "aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter":
        "Count of mismatches surfaced by the drafter (gap-net) after auditor pass.",
    "aho.materiality.claim_vs_artifact_mismatches.escaped":
        "Count of mismatches escaped from a sealed iteration (surfaced retrospectively).",
    "aho.materiality.carry_forward_resolution_rate":
        "Count of carry-forwards explicitly closed by reference in a workstream output.",
}


_counters = _build_counters()


def _baseline_attributes() -> Dict[str, str]:
    """Resource-attribute parity with the audit primitives."""
    return {
        "aho.iteration": os.environ.get("AHO_ITERATION", "unknown"),
        "aho.workstream": os.environ.get("AHO_WORKSTREAM", "unknown"),
        "aho.tier": os.environ.get("AHO_TIER", "base"),
        "aho.role": os.environ.get("AHO_ROLE", "drafter"),
    }


def record_caught_by_llama(
    *, severity: str = "info", count: int = 1, extra: Optional[Dict[str, Any]] = None
) -> None:
    counter = _counters["aho.materiality.claim_vs_artifact_mismatches.caught_by_llama"]
    if counter is None:
        return
    attrs = _baseline_attributes()
    attrs["aho.materiality.severity"] = severity
    if extra:
        for k, v in extra.items():
            attrs[k] = v
    counter.add(count, attributes=attrs)


def record_caught_by_drafter(
    *, severity: str = "info", count: int = 1, extra: Optional[Dict[str, Any]] = None
) -> None:
    counter = _counters["aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter"]
    if counter is None:
        return
    attrs = _baseline_attributes()
    attrs["aho.materiality.severity"] = severity
    if extra:
        for k, v in extra.items():
            attrs[k] = v
    counter.add(count, attributes=attrs)


def record_escaped(
    *, severity: str = "info", count: int = 1, extra: Optional[Dict[str, Any]] = None
) -> None:
    counter = _counters["aho.materiality.claim_vs_artifact_mismatches.escaped"]
    if counter is None:
        return
    attrs = _baseline_attributes()
    attrs["aho.materiality.severity"] = severity
    if extra:
        for k, v in extra.items():
            attrs[k] = v
    counter.add(count, attributes=attrs)


def record_carry_forward_resolution(
    *, count: int = 1, extra: Optional[Dict[str, Any]] = None
) -> None:
    counter = _counters["aho.materiality.carry_forward_resolution_rate"]
    if counter is None:
        return
    attrs = _baseline_attributes()
    if extra:
        for k, v in extra.items():
            attrs[k] = v
    counter.add(count, attributes=attrs)


def counters_introspect() -> Dict[str, bool]:
    """For probes - confirms each counter is built (otel available)."""
    return {name: _counters.get(name) is not None for name in COUNTER_NAMES}
