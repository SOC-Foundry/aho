"""council.dispatch - real implementation (W2).

Routes work to a council seat by (work_shape, role, tier). Returns the
component's result plus dispatch metadata. Three hard rules:

1. Substantive drafting at base tier RAISES CouncilDispatchEscalateRequired.
   Base tier doesn't host substantive drafters; it escalates out.
2. Role-collapse trip-wire - if drafter and auditor in the same iteration
   would land on the same model family, RAISES CouncilRoleCollapseError.
3. Unknown (work_shape, role, tier) RAISES CouncilDispatchUnknownRouteError.

No silent fallbacks anywhere. G083 discipline.

Wire-up env:
- AHO_ITERATION - dispatch state keys off this for role-collapse tracking
- AHO_TIER - defaults to base if unset
"""
from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Optional, Tuple

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.council.dispatch")
except ImportError:  # pragma: no cover
    _otel_trace = None
    _tracer = None


class CouncilDispatchInputError(ValueError):
    """Caller passed bad inputs (None role / unknown role / etc)."""


class CouncilDispatchUnknownRouteError(RuntimeError):
    """No handler registered for (work_shape, role, tier)."""


class CouncilDispatchEscalateRequired(RuntimeError):
    """Tier cannot service the work - escalate to a higher tier or external
    drafter. The exception carries `target` describing the escalation hop.
    """

    def __init__(self, message: str, *, target: str) -> None:
        super().__init__(message)
        self.target = target


class CouncilRoleCollapseError(RuntimeError):
    """Drafter and auditor would collapse onto the same model family in
    this iteration - the harness's anti-rubber-stamp invariant. Trip-wires
    fire here, never silently approve.
    """


# ---------------------------------------------------------------------------
# Routing table - (work_shape, role, tier) → (model_id, family, handler_kind)
#
# handler_kind is a string the dispatch loop uses to pick the actual
# callable lazily (avoids circular imports at module load).
# ---------------------------------------------------------------------------

ROUTING_TABLE: Dict[Tuple[str, str, str], Dict[str, str]] = {
    ("structural_audit", "audit", "base"): {
        "model_id": "llama3.2:3b",
        "family": "llama",
        "handler_kind": "council.audit",
    },
    ("classify", "triage", "base"): {
        "model_id": "nemotron-mini:4b",
        "family": "nemotron",
        "handler_kind": "council.triage.classify",
    },
    ("registry_delta_draft", "triage", "base"): {
        "model_id": "nemotron-mini:4b",
        "family": "nemotron",
        "handler_kind": "council.triage.draft_registry_delta",
    },
    ("embed", "retrieval", "base"): {
        "model_id": "nomic-embed-text",
        "family": "nomic",
        "handler_kind": "council.embed",
    },
    ("retrieve", "retrieval", "base"): {
        "model_id": "nomic-embed-text",
        "family": "nomic",
        "handler_kind": "rag.query",
    },
}

# Work-shapes that are known but NOT routable at base tier - they escalate.
ESCALATE_AT_BASE: Dict[str, str] = {
    "substantive_drafting": "partial_tier_or_external_drafter",
    "deep_synthesis": "partial_tier_or_external_drafter",
    "creative_authoring": "external_drafter",
}

# Roles that participate in the role-collapse invariant (drafter ↔ auditor).
_COLLAPSE_ROLES = {"drafter", "auditor"}


def _tier() -> str:
    return os.environ.get("AHO_TIER", "base")


def _iteration() -> str:
    return os.environ.get("AHO_ITERATION", "unknown")


# ---------------------------------------------------------------------------
# Per-iteration state for role-collapse tracking
# ---------------------------------------------------------------------------

class CouncilDispatch:
    """Stateful dispatch coordinator. Tracks per-iteration role assignments
    to enforce the role-collapse invariant.

    A new instance starts with an empty role tracker; the module-level
    `dispatch()` function uses a process-global instance keyed on iteration.
    """

    def __init__(
        self,
        *,
        iteration: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> None:
        self.iteration = iteration if iteration is not None else _iteration()
        self.tier = tier if tier is not None else _tier()
        self._role_family: Dict[str, str] = {}

    def role_family_snapshot(self) -> Dict[str, str]:
        return dict(self._role_family)

    def record_role_family(self, role: str, family: str) -> None:
        """Record a (role, family) pair. Raises CouncilRoleCollapseError if
        the assignment would collapse drafter and auditor onto the same
        family.

        Public so test fixtures can simulate cross-call state.
        """
        if role in _COLLAPSE_ROLES:
            counterpart = "auditor" if role == "drafter" else "drafter"
            existing = self._role_family.get(counterpart)
            if existing is not None and existing == family:
                raise CouncilRoleCollapseError(
                    f"role-collapse: iteration={self.iteration} "
                    f"role={role} family={family} would match counterpart "
                    f"{counterpart!r} already on family={family!r}"
                )
        self._role_family[role] = family

    def dispatch(
        self,
        work_shape: str,
        role: str,
        payload: Any = None,
    ) -> Dict[str, Any]:
        if not isinstance(work_shape, str) or not work_shape:
            raise CouncilDispatchInputError(
                f"work_shape must be non-empty str, got {work_shape!r}"
            )
        if not isinstance(role, str) or not role:
            raise CouncilDispatchInputError(
                f"role must be non-empty str, got {role!r}"
            )

        # Escalate-at-base check before route lookup.
        if self.tier == "base" and work_shape in ESCALATE_AT_BASE:
            target = ESCALATE_AT_BASE[work_shape]
            self._emit_span(
                work_shape=work_shape,
                role=role,
                model_id=None,
                family=None,
                tier_decision=f"escalate:{target}",
                latency_ms=0,
                error="CouncilDispatchEscalateRequired",
            )
            raise CouncilDispatchEscalateRequired(
                f"work_shape={work_shape!r} cannot run at tier={self.tier!r}; "
                f"escalate to {target}",
                target=target,
            )

        key = (work_shape, role, self.tier)
        route = ROUTING_TABLE.get(key)
        if route is None:
            self._emit_span(
                work_shape=work_shape,
                role=role,
                model_id=None,
                family=None,
                tier_decision="unknown",
                latency_ms=0,
                error="CouncilDispatchUnknownRouteError",
            )
            raise CouncilDispatchUnknownRouteError(
                f"no route for (work_shape={work_shape}, role={role}, tier={self.tier})"
            )

        # Role-collapse tracking - drafter/auditor only.
        # Note: handlers in the base routing table are not 'drafter' role,
        # so a base-tier dispatch normally won't trip this. The invariant
        # surfaces when a downstream caller (or a test fixture) manually
        # records a 'drafter' family before this call.
        self.record_role_family(role, route["family"])

        handler = _resolve_handler(route["handler_kind"])
        start = time.monotonic()
        try:
            result = handler(payload)
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            self._emit_span(
                work_shape=work_shape,
                role=role,
                model_id=route["model_id"],
                family=route["family"],
                tier_decision=self.tier,
                latency_ms=latency_ms,
                error=type(exc).__name__,
            )
            raise
        latency_ms = int((time.monotonic() - start) * 1000)
        self._emit_span(
            work_shape=work_shape,
            role=role,
            model_id=route["model_id"],
            family=route["family"],
            tier_decision=self.tier,
            latency_ms=latency_ms,
        )
        return {
            "work_shape": work_shape,
            "role": role,
            "tier_decision": self.tier,
            "model_id": route["model_id"],
            "family": route["family"],
            "handler_kind": route["handler_kind"],
            "latency_ms": latency_ms,
            "iteration": self.iteration,
            "result": result,
        }

    def _emit_span(
        self,
        *,
        work_shape: str,
        role: str,
        model_id: Optional[str],
        family: Optional[str],
        tier_decision: str,
        latency_ms: int,
        error: Optional[str] = None,
    ) -> None:
        if _tracer is None:
            return
        with _tracer.start_as_current_span("aho.council.dispatch") as span:
            try:
                span.set_attribute("aho.council.role", role)
                span.set_attribute("aho.council.work_shape", work_shape)
                span.set_attribute("aho.tier", self.tier)
                span.set_attribute("aho.council.tier_decision", tier_decision)
                span.set_attribute("aho.council.latency_ms", latency_ms)
                span.set_attribute("aho.iteration", self.iteration)
                if model_id is not None:
                    span.set_attribute("aho.model", model_id)
                if family is not None:
                    span.set_attribute("aho.council.family", family)
                if error is not None:
                    span.set_attribute("aho.council.error", error)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Handler resolution - lazy to avoid circular imports
# ---------------------------------------------------------------------------

def _resolve_handler(kind: str) -> Callable[[Any], Any]:
    if kind == "council.audit":
        from . import audit as _audit
        return _audit.audit
    if kind == "council.triage.classify":
        from . import triage as _triage
        return _triage.classify
    if kind == "council.triage.draft_registry_delta":
        from . import triage as _triage
        return lambda payload: _triage.draft_registry_delta(
            payload["executor_output"], payload["registry_snapshot"]
        )
    if kind == "council.embed":
        from . import embed as _embed
        return _embed.embed
    if kind == "rag.query":
        from .. import rag as _rag
        return lambda payload: _rag.query(
            payload["text"],
            k=payload.get("k", 5),
            project=payload.get("project"),
        )
    raise CouncilDispatchUnknownRouteError(f"unknown handler_kind: {kind}")


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_GLOBAL_DISPATCH: Optional[CouncilDispatch] = None


def get_dispatch(*, fresh: bool = False) -> CouncilDispatch:
    """Return the process-global dispatch instance. `fresh=True` discards
    the existing instance - useful for tests.
    """
    global _GLOBAL_DISPATCH
    if fresh or _GLOBAL_DISPATCH is None:
        _GLOBAL_DISPATCH = CouncilDispatch()
    return _GLOBAL_DISPATCH


def dispatch(work_shape: str, role: str, payload: Any = None) -> Dict[str, Any]:
    """Convenience wrapper around the global dispatch instance."""
    return get_dispatch().dispatch(work_shape, role, payload)
