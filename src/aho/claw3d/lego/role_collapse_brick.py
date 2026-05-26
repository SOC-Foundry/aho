"""W4 D4 - role-collapse trip-wire brick.

Single dedicated brick rendering the W2 D5 OTEL invariant: in any single
iteration, drafter and auditor must not collapse onto the same model
family. ``aho.council.dispatch.record_role_family`` raises
``CouncilRoleCollapseError`` when the invariant is violated; the brick
surfaces whether that has fired.

Distinct from D2's ``aho.adversarial`` brick - D2 sits in the per-
component grid alongside other components for at-a-glance health
review, while D4 is a focused one-brick surface dedicated to the
invariant. Both read the same signal source so they cannot disagree.

Signal source:

  - ``aho.council.dispatch.role_collapse_tripwire_fired`` - counter
    incremented when the trip-wire raises ``CouncilRoleCollapseError``
    (counter is recorded out-of-band by the dispatch error path; this
    brick reads the aggregated value rather than re-deriving it from
    span attributes).
  - ``aho.council.dispatch.invocation_count`` - sanity check that
    dispatch is alive.

Render contract: this brick returns a single ``BrickState`` with extra
detail captured in ``role_pair_snapshot`` - useful for drafter
inspection when the trip-wire fires (which (drafter, auditor) family
pair would have collapsed).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .bricks import (
    BRICK_GREEN,
    BRICK_RED,
    BRICK_UNKNOWN,
    BrickState,
    _counter,
)


SIGNAL_KEYS = (
    "aho.council.dispatch.role_collapse_tripwire_fired",
    "aho.council.dispatch.invocation_count",
)


@dataclass
class RoleCollapseBrickState:
    color: str  # green | red | unknown
    reason: str
    tripwire_fired_count: int
    dispatch_invocation_count: int
    role_pair_snapshot: Optional[Dict[str, str]] = None


def evaluate(signal_state: Dict[str, Any]) -> RoleCollapseBrickState:
    """Evaluate the trip-wire brick against signal state. Red wins over
    green; if neither matches the brick is unknown.

    ``signal_state`` may include a ``role_pair_snapshot`` under
    ``flags`` - when the trip-wire fires, the snapshot identifies which
    roles would have collapsed onto which family.
    """
    fired = _counter(signal_state, "aho.council.dispatch.role_collapse_tripwire_fired")
    invocations = _counter(signal_state, "aho.council.dispatch.invocation_count")
    flags = signal_state.get("flags") or {}
    snapshot = flags.get("role_pair_snapshot")

    if fired > 0:
        return RoleCollapseBrickState(
            color=BRICK_RED,
            reason=(
                f"role-collapse trip-wire fired {fired} time(s) - drafter and"
                " auditor would have shared a model family in this iteration"
            ),
            tripwire_fired_count=fired,
            dispatch_invocation_count=invocations,
            role_pair_snapshot=snapshot if isinstance(snapshot, dict) else None,
        )
    if invocations > 0:
        return RoleCollapseBrickState(
            color=BRICK_GREEN,
            reason=(
                f"{invocations} dispatch invocation(s) recorded with no"
                " role-collapse trip-wire fire"
            ),
            tripwire_fired_count=0,
            dispatch_invocation_count=invocations,
            role_pair_snapshot=snapshot if isinstance(snapshot, dict) else None,
        )
    return RoleCollapseBrickState(
        color=BRICK_UNKNOWN,
        reason="no dispatch activity in window - invariant inactive, not violated",
        tripwire_fired_count=0,
        dispatch_invocation_count=0,
        role_pair_snapshot=None,
    )


def to_brick_state(state: RoleCollapseBrickState) -> BrickState:
    """Adapt a RoleCollapseBrickState into the generic BrickState shape
    used by D2's grid render."""
    return BrickState(
        component_id="aho.adversarial.role_collapse_tripwire",
        color=state.color,
        reason=state.reason,
        detail={
            "tripwire_fired_count": state.tripwire_fired_count,
            "dispatch_invocation_count": state.dispatch_invocation_count,
            "role_pair_snapshot": state.role_pair_snapshot,
        },
    )


def render(signal_state: Dict[str, Any]) -> Dict[str, Any]:
    """JSON render of the single trip-wire brick - the dashboard
    surface contract for D4."""
    s = evaluate(signal_state)
    return {
        "kind": "role_collapse_tripwire_brick",
        "schema_version": 1,
        "color": s.color,
        "reason": s.reason,
        "tripwire_fired_count": s.tripwire_fired_count,
        "dispatch_invocation_count": s.dispatch_invocation_count,
        "role_pair_snapshot": s.role_pair_snapshot,
        "signal_keys": list(SIGNAL_KEYS),
    }


__all__ = [
    "RoleCollapseBrickState",
    "SIGNAL_KEYS",
    "evaluate",
    "render",
    "to_brick_state",
]
