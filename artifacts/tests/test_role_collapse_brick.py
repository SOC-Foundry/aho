"""W4 D4 - role-collapse trip-wire brick acceptance tests.

Verifies:
  - tripwire_fired_count > 0 → red, with role_pair_snapshot surfaced
  - dispatch_invocation_count > 0 + no fire → green
  - empty signal → unknown (invariant inactive)
  - render produces the JSON contract D6 dashboard consumes
"""
from __future__ import annotations

from aho.claw3d.lego.bricks import BRICK_GREEN, BRICK_RED, BRICK_UNKNOWN
from aho.claw3d.lego.role_collapse_brick import (
    SIGNAL_KEYS,
    evaluate,
    render,
    to_brick_state,
)


def test_tripwire_fired_reds_with_snapshot():
    state = {
        "counters": {
            "aho.council.dispatch.role_collapse_tripwire_fired": 1,
            "aho.council.dispatch.invocation_count": 4,
        },
        "flags": {
            "role_pair_snapshot": {"drafter": "llama", "auditor": "llama"},
        },
    }
    s = evaluate(state)
    assert s.color == BRICK_RED
    assert s.tripwire_fired_count == 1
    assert s.dispatch_invocation_count == 4
    assert s.role_pair_snapshot == {"drafter": "llama", "auditor": "llama"}
    assert "role-collapse trip-wire fired" in s.reason


def test_dispatch_alive_no_fire_greens():
    state = {
        "counters": {
            "aho.council.dispatch.role_collapse_tripwire_fired": 0,
            "aho.council.dispatch.invocation_count": 12,
        },
    }
    s = evaluate(state)
    assert s.color == BRICK_GREEN
    assert s.tripwire_fired_count == 0
    assert s.dispatch_invocation_count == 12


def test_no_dispatch_activity_unknown():
    state = {"counters": {}}
    s = evaluate(state)
    assert s.color == BRICK_UNKNOWN
    assert s.tripwire_fired_count == 0
    assert s.dispatch_invocation_count == 0


def test_render_returns_json_contract():
    state = {
        "counters": {
            "aho.council.dispatch.role_collapse_tripwire_fired": 2,
            "aho.council.dispatch.invocation_count": 5,
        },
        "flags": {"role_pair_snapshot": {"drafter": "qwen", "auditor": "qwen"}},
    }
    out = render(state)
    assert out["kind"] == "role_collapse_tripwire_brick"
    assert out["schema_version"] == 1
    assert out["color"] == BRICK_RED
    assert out["tripwire_fired_count"] == 2
    assert out["role_pair_snapshot"] == {"drafter": "qwen", "auditor": "qwen"}
    assert out["signal_keys"] == list(SIGNAL_KEYS)


def test_to_brick_state_adapts_for_grid_render():
    s = evaluate({
        "counters": {
            "aho.council.dispatch.role_collapse_tripwire_fired": 0,
            "aho.council.dispatch.invocation_count": 8,
        },
    })
    bs = to_brick_state(s)
    assert bs.component_id == "aho.adversarial.role_collapse_tripwire"
    assert bs.color == BRICK_GREEN
    assert bs.detail["dispatch_invocation_count"] == 8
    assert bs.detail["tripwire_fired_count"] == 0
