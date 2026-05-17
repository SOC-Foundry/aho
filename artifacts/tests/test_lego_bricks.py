"""W4 D2 — per-component brick acceptance tests.

Each of the ten bricks must:
  - render green against synthetic-healthy signal state
  - red against an injected fault in its own signal slice
  - unknown when its slice of signal_state is empty

Plus the brick spec list itself must cover the W4 plan-doc §D2 component
list verbatim — drift between the plan and the spec list fails this
test loud.
"""
from __future__ import annotations

from typing import Any, Dict

import pytest

from aho.claw3d.lego.bricks import (
    BRICK_GREEN,
    BRICK_RED,
    BRICK_UNKNOWN,
    BrickSpec,
    brick_specs,
    evaluate_all,
    evaluate_brick,
    render_brick_grid,
    synthetic_signal_state,
)


W4_PLAN_DOC_COMPONENT_LIST = (
    "aho.dispatcher",
    "aho.adversarial",
    "aho.workstream",
    "aho.secrets_client",
    "aho.otel",
    "aho.health",
    "aho.signal",
    "aho.council.audit",
    "aho.council.triage",
    "aho.council.embed+aho.rag",
)


def test_brick_spec_list_matches_w4_plan_doc_d2():
    """Spec list ordering and component IDs must match the W4 plan §D2
    component list. Drift is an acceptance failure."""
    actual = tuple(s.component_id for s in brick_specs())
    assert actual == W4_PLAN_DOC_COMPONENT_LIST, (
        f"brick spec drift from W4 plan §D2 list:\n"
        f"  expected: {W4_PLAN_DOC_COMPONENT_LIST}\n"
        f"  actual:   {actual}"
    )


def test_brick_spec_list_has_exactly_ten_entries():
    assert len(brick_specs()) == 10


def test_synthetic_healthy_state_every_brick_greens():
    """Every brick reports green against synthetic_signal_state(healthy=True)."""
    state = synthetic_signal_state(healthy=True)
    states = evaluate_all(state)
    reds = [s for s in states if s.color == BRICK_RED]
    unknowns = [s for s in states if s.color == BRICK_UNKNOWN]
    assert reds == [], f"unexpected red bricks under healthy state: {reds}"
    assert unknowns == [], f"unexpected unknown bricks under healthy state: {unknowns}"


def test_synthetic_unhealthy_state_every_brick_reds():
    """Every brick reports red against synthetic_signal_state(healthy=False)."""
    state = synthetic_signal_state(healthy=False)
    states = evaluate_all(state)
    not_red = [s for s in states if s.color != BRICK_RED]
    assert not_red == [], (
        f"every brick should red on full-fault synthetic state; "
        f"non-red brick(s): {[(s.component_id, s.color) for s in not_red]}"
    )


def test_empty_signal_state_every_brick_unknown():
    """Empty signal state (no counters, no presence, no flags) → every
    brick is unknown."""
    state: Dict[str, Any] = {"counters": {}, "presence": {}, "flags": {}}
    states = evaluate_all(state)
    not_unknown = [s for s in states if s.color != BRICK_UNKNOWN]
    assert not_unknown == [], (
        f"every brick should be unknown on empty state; "
        f"non-unknown brick(s): {[(s.component_id, s.color) for s in not_unknown]}"
    )


# ---------------------------------------------------------------------------
# Per-brick fault-injection — for each spec, isolate the brick by
# constructing a signal_state that's healthy elsewhere but fault-injected
# in this brick's signal slice. Spec must red.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("brick_index", list(range(10)))
def test_isolated_fault_injection_reds_only_target_brick(brick_index):
    """Pick one brick. Construct a signal state where every other brick
    is healthy and only this brick's fault counter is non-zero. The
    target brick must red; all other bricks must green."""
    specs = brick_specs()
    target = specs[brick_index]

    # Determine the fault counter for this spec by probing red_predicate
    # against single-counter overrides. The brick's `signal_keys`
    # documents the candidate fault counters; we pick the first that
    # makes red_predicate return True with value=1.
    healthy = synthetic_signal_state(healthy=True)
    fault_state = {
        "counters": dict(healthy["counters"]),
        "presence": {},
        "flags": {},
    }
    fault_counter = None
    for key in target.signal_keys:
        candidate = {
            "counters": dict(fault_state["counters"]),
            "presence": {},
            "flags": {},
        }
        candidate["counters"][key] = 1
        if target.red_predicate(candidate):
            fault_counter = key
            fault_state["counters"][key] = 1
            break
    assert fault_counter is not None, (
        f"could not identify a fault counter for brick "
        f"{target.component_id}; signal_keys={target.signal_keys}"
    )

    states = evaluate_all(fault_state)
    by_id = {s.component_id: s for s in states}
    assert by_id[target.component_id].color == BRICK_RED, (
        f"brick {target.component_id} did not red on fault counter "
        f"{fault_counter}=1"
    )
    # Other bricks must remain green (we kept them on healthy counters).
    other_non_green = [
        (cid, s.color)
        for cid, s in by_id.items()
        if cid != target.component_id and s.color != BRICK_GREEN
    ]
    assert other_non_green == [], (
        f"injecting fault in {target.component_id} unexpectedly affected "
        f"other bricks: {other_non_green}"
    )


def test_render_brick_grid_summary_counts_match_states():
    state = synthetic_signal_state(healthy=True)
    states = evaluate_all(state)
    grid = render_brick_grid(states)
    assert grid["kind"] == "claw3d_brick_grid"
    assert grid["summary"]["green"] == len(states)
    assert grid["summary"]["red"] == 0
    assert grid["summary"]["unknown"] == 0
    assert grid["summary"]["total"] == 10


def test_council_audit_brick_surfaces_filter_activity():
    """The aho.council.audit brick's extra_render must surface filter
    activity — eligible_count, suppressed_count, audit_count."""
    state = synthetic_signal_state(healthy=True)
    state["counters"]["aho.council.audit.finding_filter.suppressed_count"] = 2
    states = evaluate_all(state)
    by_id = {s.component_id: s for s in states}
    audit = by_id["aho.council.audit"]
    assert audit.color == BRICK_GREEN
    assert audit.detail.get("filter_suppressed_count") == 2
    assert audit.detail.get("filter_eligible_count") == 3
    assert audit.detail.get("audit_count") == 3


def test_brick_spec_signal_keys_are_documented_strings():
    """Each spec's signal_keys list must be a non-empty list of strings.
    Drift / typos in the documented signal surface fail this test
    loud."""
    for spec in brick_specs():
        assert isinstance(spec.signal_keys, list)
        assert len(spec.signal_keys) >= 1
        for key in spec.signal_keys:
            assert isinstance(key, str) and key.strip()
