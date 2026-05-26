"""W4 D2 - per-component claw3d bricks.

Each brick is a structured visualization of one ``aho.*`` component's
operational state. A brick reads a small slice of OTEL state and reduces
it to one of three colors:

  - **green** - recent activity matches the healthy predicate (no errors,
    expected emit count, etc.)
  - **red** - fault predicate matches (error count > 0, signal missing
    when it should be present, trip-wire fired, etc.)
  - **unknown** - neither predicate matches (no signal in window, e.g.
    component was idle or OTEL collector hadn't started yet)

Brick specs are deliberately small and inspectable. Each spec names the
signal keys it reads from the aggregated OTEL state, so a reviewer can
verify "this brick reds because ``aho.council.audit.error_count > 0``"
without re-reading code paths.

The brick layer reads aggregated OTEL state - it does not poll Ollama,
ChromaDB, or systemd directly. The aggregator
(``aho.claw3d.otel_aggregator``) is the single owner of OTEL parsing.

Coverage is the W4 plan-doc §D2 list of ten components:

  aho.dispatcher, aho.adversarial, aho.workstream, aho.secrets_client,
  aho.otel, aho.health, aho.signal, aho.council.audit (with filter
  status), aho.council.triage, aho.council.embed + aho.rag (combined).

The ``aho.adversarial`` brick is the role-collapse trip-wire surface; it
overlaps with D4 by design - D4 is the single dedicated trip-wire brick,
while D2's aho.adversarial brick wraps the same signal in the per-
component grid view.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


BRICK_GREEN = "green"
BRICK_RED = "red"
BRICK_UNKNOWN = "unknown"

BRICK_COLORS = (BRICK_GREEN, BRICK_RED, BRICK_UNKNOWN)


@dataclass
class BrickSpec:
    """One component's brick definition.

    ``signal_keys`` is the documented set of OTEL counter / span / log
    attribute names this brick consumes. Listed for inspection - the
    actual predicates may also tolerate aliases or fall-throughs, but
    ``signal_keys`` is the canonical reference for "what feeds this
    brick".

    ``red_predicate`` returns True when the brick should color red.
    ``green_predicate`` returns True when the brick should color green.
    Both can return False, in which case the brick is ``unknown`` (no
    signal in window).

    Predicates take a ``signal_state`` dict - see
    ``synthetic_signal_state`` for the canonical shape. They must be
    pure functions: same input → same output.
    """

    component_id: str
    description: str
    signal_keys: List[str]
    red_predicate: Callable[[Dict[str, Any]], bool]
    green_predicate: Callable[[Dict[str, Any]], bool]
    extra_render: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None


@dataclass
class BrickState:
    """One brick's evaluated state at a point in time."""

    component_id: str
    color: str  # green | red | unknown
    reason: str
    detail: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Signal accessors - small, audited helpers for reading the signal_state
# dict shape that bricks rely on.
# ---------------------------------------------------------------------------

def _counter(state: Dict[str, Any], key: str) -> int:
    counters = state.get("counters") or {}
    raw = counters.get(key, 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _present(state: Dict[str, Any], key: str) -> bool:
    presence = state.get("presence") or {}
    return bool(presence.get(key))


def _flag(state: Dict[str, Any], key: str, default: bool = False) -> bool:
    flags = state.get("flags") or {}
    val = flags.get(key)
    if val is None:
        return default
    return bool(val)


# ---------------------------------------------------------------------------
# Brick specs - ten components per W4 plan §D2.
#
# Each spec's predicates are deliberately small. Anything fancier should
# move into the aggregator so brick logic stays inspectable.
# ---------------------------------------------------------------------------


def _audit_filter_extra(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "filter_eligible_count": _counter(
            state, "aho.council.audit.finding_filter.eligible_count"
        ),
        "filter_suppressed_count": _counter(
            state, "aho.council.audit.finding_filter.suppressed_count"
        ),
        "audit_count": _counter(state, "aho.council.audit.invocation_count"),
        "audit_error_count": _counter(state, "aho.council.audit.error_count"),
    }


_BRICK_SPECS: List[BrickSpec] = [
    BrickSpec(
        component_id="aho.dispatcher",
        description="Pipeline dispatcher - local model dispatch wrapper",
        signal_keys=[
            "aho.pipeline.dispatcher.invocation_count",
            "aho.pipeline.dispatcher.error_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.pipeline.dispatcher.error_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.pipeline.dispatcher.invocation_count") > 0
            and _counter(s, "aho.pipeline.dispatcher.error_count") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.adversarial",
        description="Adversarial Authorship dispatch - role-collapse trip-wire",
        signal_keys=[
            "aho.council.dispatch.role_collapse_tripwire_fired",
            "aho.council.dispatch.invocation_count",
        ],
        red_predicate=lambda s: _counter(
            s, "aho.council.dispatch.role_collapse_tripwire_fired"
        ) > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.council.dispatch.invocation_count") > 0
            and _counter(s, "aho.council.dispatch.role_collapse_tripwire_fired") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.workstream",
        description="Workstream events - checkpoint emit + isolation guard",
        signal_keys=[
            "aho.workstream.event_count",
            "aho.workstream.checkpoint_write_error_count",
        ],
        red_predicate=lambda s: _counter(
            s, "aho.workstream.checkpoint_write_error_count"
        ) > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.workstream.event_count") > 0
            and _counter(s, "aho.workstream.checkpoint_write_error_count") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.secrets_client",
        description="Secrets broker client - read-only host ↔ container bridge",
        signal_keys=[
            "aho.secrets_client.read_count",
            "aho.secrets_client.error_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.secrets_client.error_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.secrets_client.read_count") > 0
            and _counter(s, "aho.secrets_client.error_count") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.otel",
        description="OTEL exporter - logs.jsonl + metrics.jsonl liveness",
        signal_keys=[
            "aho.otel.logs_emitted_count",
            "aho.otel.metrics_emitted_count",
            "aho.otel.exporter_error_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.otel.exporter_error_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.otel.logs_emitted_count") > 0
            and _counter(s, "aho.otel.metrics_emitted_count") > 0
        ),
    ),
    BrickSpec(
        component_id="aho.health",
        description="Health probe - periodic /health checks across components",
        signal_keys=[
            "aho.health.probe_success_count",
            "aho.health.probe_failure_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.health.probe_failure_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.health.probe_success_count") > 0
            and _counter(s, "aho.health.probe_failure_count") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.signal",
        description="Signal / alert subsystem - telegram + halt-and-surface",
        signal_keys=[
            "aho.signal.emit_count",
            "aho.signal.error_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.signal.error_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.signal.emit_count") > 0
            and _counter(s, "aho.signal.error_count") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.council.audit",
        description=(
            "Council auditor (llama3.2 + RAG + post-hoc filter) - disposition"
            " emit count, filter activity"
        ),
        signal_keys=[
            "aho.council.audit.invocation_count",
            "aho.council.audit.error_count",
            "aho.council.audit.finding_filter.eligible_count",
            "aho.council.audit.finding_filter.suppressed_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.council.audit.error_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.council.audit.invocation_count") > 0
            and _counter(s, "aho.council.audit.error_count") == 0
        ),
        extra_render=_audit_filter_extra,
    ),
    BrickSpec(
        component_id="aho.council.triage",
        description="Council triage (nemotron) - rubric classification",
        signal_keys=[
            "aho.council.triage.invocation_count",
            "aho.council.triage.malformed_count",
        ],
        red_predicate=lambda s: _counter(
            s, "aho.council.triage.malformed_count"
        ) > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.council.triage.invocation_count") > 0
            and _counter(s, "aho.council.triage.malformed_count") == 0
        ),
    ),
    BrickSpec(
        component_id="aho.council.embed+aho.rag",
        description=(
            "Embedding + RAG retrieval - ChromaDB query liveness, audit"
            " enrichment retrieval count"
        ),
        signal_keys=[
            "aho.council.embed.invocation_count",
            "aho.rag.query_count",
            "aho.rag.error_count",
        ],
        red_predicate=lambda s: _counter(s, "aho.rag.error_count") > 0,
        green_predicate=lambda s: (
            _counter(s, "aho.rag.query_count") > 0
            and _counter(s, "aho.rag.error_count") == 0
        ),
    ),
]


def brick_specs() -> List[BrickSpec]:
    """Canonical ordered list of brick specs. Read-only - callers must not
    mutate the returned list (it shares state with the module-level
    constant)."""
    return list(_BRICK_SPECS)


def evaluate_brick(spec: BrickSpec, signal_state: Dict[str, Any]) -> BrickState:
    """Evaluate one brick against signal state. Red wins over green; if
    neither predicate matches the brick is ``unknown``."""
    if spec.red_predicate(signal_state):
        detail = spec.extra_render(signal_state) if spec.extra_render else {}
        return BrickState(
            component_id=spec.component_id,
            color=BRICK_RED,
            reason="red_predicate matched",
            detail=detail,
        )
    if spec.green_predicate(signal_state):
        detail = spec.extra_render(signal_state) if spec.extra_render else {}
        return BrickState(
            component_id=spec.component_id,
            color=BRICK_GREEN,
            reason="green_predicate matched",
            detail=detail,
        )
    return BrickState(
        component_id=spec.component_id,
        color=BRICK_UNKNOWN,
        reason="no signal in window",
        detail=spec.extra_render(signal_state) if spec.extra_render else {},
    )


def evaluate_all(signal_state: Dict[str, Any]) -> List[BrickState]:
    return [evaluate_brick(spec, signal_state) for spec in _BRICK_SPECS]


# ---------------------------------------------------------------------------
# Synthetic state fixtures - used by tests, probes, and dashboards that
# need to demonstrate brick rendering without a live OTEL collector.
# ---------------------------------------------------------------------------

def synthetic_signal_state(*, healthy: bool = True) -> Dict[str, Any]:
    """Synthetic signal state matching a 5-min synthetic load test.

    ``healthy=True`` produces counters consistent with normal operation
    across all ten components (every brick should evaluate green).
    ``healthy=False`` introduces one fault per component so every brick
    reds.
    """
    if healthy:
        counters: Dict[str, int] = {
            "aho.pipeline.dispatcher.invocation_count": 12,
            "aho.pipeline.dispatcher.error_count": 0,
            "aho.council.dispatch.invocation_count": 4,
            "aho.council.dispatch.role_collapse_tripwire_fired": 0,
            "aho.workstream.event_count": 8,
            "aho.workstream.checkpoint_write_error_count": 0,
            "aho.secrets_client.read_count": 5,
            "aho.secrets_client.error_count": 0,
            "aho.otel.logs_emitted_count": 200,
            "aho.otel.metrics_emitted_count": 60,
            "aho.otel.exporter_error_count": 0,
            "aho.health.probe_success_count": 30,
            "aho.health.probe_failure_count": 0,
            "aho.signal.emit_count": 2,
            "aho.signal.error_count": 0,
            "aho.council.audit.invocation_count": 3,
            "aho.council.audit.error_count": 0,
            "aho.council.audit.finding_filter.eligible_count": 3,
            "aho.council.audit.finding_filter.suppressed_count": 0,
            "aho.council.triage.invocation_count": 6,
            "aho.council.triage.malformed_count": 0,
            "aho.council.embed.invocation_count": 18,
            "aho.rag.query_count": 18,
            "aho.rag.error_count": 0,
        }
    else:
        counters = {
            "aho.pipeline.dispatcher.invocation_count": 5,
            "aho.pipeline.dispatcher.error_count": 1,
            "aho.council.dispatch.invocation_count": 4,
            "aho.council.dispatch.role_collapse_tripwire_fired": 1,
            "aho.workstream.event_count": 4,
            "aho.workstream.checkpoint_write_error_count": 1,
            "aho.secrets_client.read_count": 2,
            "aho.secrets_client.error_count": 1,
            "aho.otel.logs_emitted_count": 0,
            "aho.otel.metrics_emitted_count": 0,
            "aho.otel.exporter_error_count": 1,
            "aho.health.probe_success_count": 10,
            "aho.health.probe_failure_count": 1,
            "aho.signal.emit_count": 1,
            "aho.signal.error_count": 1,
            "aho.council.audit.invocation_count": 2,
            "aho.council.audit.error_count": 1,
            "aho.council.audit.finding_filter.eligible_count": 0,
            "aho.council.audit.finding_filter.suppressed_count": 0,
            "aho.council.triage.invocation_count": 3,
            "aho.council.triage.malformed_count": 1,
            "aho.council.embed.invocation_count": 9,
            "aho.rag.query_count": 9,
            "aho.rag.error_count": 1,
        }
    return {"counters": counters, "presence": {}, "flags": {}}


def render_brick_grid(states: List[BrickState]) -> Dict[str, Any]:
    """Render a list of brick states into a JSON grid suitable for the
    dashboard /api/state endpoint or for SVG renderers."""
    return {
        "kind": "claw3d_brick_grid",
        "schema_version": 1,
        "bricks": [
            {
                "component_id": s.component_id,
                "color": s.color,
                "reason": s.reason,
                "detail": s.detail,
            }
            for s in states
        ],
        "summary": {
            "green": sum(1 for s in states if s.color == BRICK_GREEN),
            "red": sum(1 for s in states if s.color == BRICK_RED),
            "unknown": sum(1 for s in states if s.color == BRICK_UNKNOWN),
            "total": len(states),
        },
    }


__all__ = [
    "BRICK_GREEN",
    "BRICK_RED",
    "BRICK_UNKNOWN",
    "BRICK_COLORS",
    "BrickSpec",
    "BrickState",
    "brick_specs",
    "evaluate_brick",
    "evaluate_all",
    "synthetic_signal_state",
    "render_brick_grid",
]
