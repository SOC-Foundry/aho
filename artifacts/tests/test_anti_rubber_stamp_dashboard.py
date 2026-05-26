"""W4 D6 - anti-rubber-stamp verification dashboard tests.

Verifies the four-surface dashboard:
  - Four surfaces in the canonical order
  - Each surface reds on its own fault, greens when its hardening is
    operating, unknown when its signal is absent
  - Overview aggregation collapses correctly
  - Filter surface drill-down surfaces suppressed_findings records
  - Render contract is stable
"""
from __future__ import annotations

from aho.claw3d.lego.anti_rubber_stamp_dashboard import (
    SURFACE_IDS,
    evaluate_all_surfaces,
    evaluate_overview,
    render_dashboard,
)
from aho.claw3d.lego.bricks import BRICK_GREEN, BRICK_RED, BRICK_UNKNOWN


def test_dashboard_has_four_surfaces_in_canonical_order():
    surfaces = evaluate_all_surfaces({"counters": {}})
    assert [s.surface_id for s in surfaces] == list(SURFACE_IDS)
    assert len(surfaces) == 4


def test_filter_surface_is_fourth_surface():
    surfaces = evaluate_all_surfaces({"counters": {}})
    assert surfaces[3].surface_id == "deterministic_post_hoc_filter"


def test_nemotron_surface_reds_on_malformed_count():
    state = {"counters": {
        "aho.council.triage.invocation_count": 5,
        "aho.council.triage.malformed_count": 2,
    }}
    s = evaluate_all_surfaces(state)[0]
    assert s.surface_id == "nemotron_raise_on_malformed"
    assert s.color == BRICK_RED
    assert s.detail["triage_malformed_count"] == 2


def test_nemotron_surface_greens_with_invocations_no_malformed():
    state = {"counters": {
        "aho.council.triage.invocation_count": 5,
        "aho.council.triage.malformed_count": 0,
    }}
    s = evaluate_all_surfaces(state)[0]
    assert s.color == BRICK_GREEN


def test_nemotron_surface_unknown_with_no_signal():
    s = evaluate_all_surfaces({"counters": {}})[0]
    assert s.color == BRICK_UNKNOWN


def test_llama_floor_surface_reds_on_lock_count():
    state = {"counters": {
        "aho.council.audit.invocation_count": 4,
        "aho.council.audit.confidence_floor_lock_count": 1,
    }}
    s = evaluate_all_surfaces(state)[1]
    assert s.surface_id == "llama_confidence_floor_lock"
    assert s.color == BRICK_RED
    assert s.detail["audit_confidence_floor_lock_count"] == 1


def test_llama_floor_surface_greens_no_lock():
    state = {"counters": {
        "aho.council.audit.invocation_count": 4,
        "aho.council.audit.confidence_floor_lock_count": 0,
    }}
    s = evaluate_all_surfaces(state)[1]
    assert s.color == BRICK_GREEN


def test_role_collapse_surface_reds_on_tripwire_fired():
    state = {"counters": {
        "aho.council.dispatch.invocation_count": 3,
        "aho.council.dispatch.role_collapse_tripwire_fired": 1,
    }}
    s = evaluate_all_surfaces(state)[2]
    assert s.surface_id == "role_collapse_tripwire"
    assert s.color == BRICK_RED


def test_filter_surface_greens_when_eligible_and_suppressing():
    state = {"counters": {
        "aho.council.audit.finding_filter.eligible_count": 3,
        "aho.council.audit.finding_filter.suppressed_count": 1,
    }}
    s = evaluate_all_surfaces(state)[3]
    assert s.surface_id == "deterministic_post_hoc_filter"
    assert s.color == BRICK_GREEN
    assert "suppressed 1" in s.headline.lower()
    assert s.detail["filter_eligible_count"] == 3
    assert s.detail["filter_suppressed_count"] == 1


def test_filter_surface_greens_when_eligible_no_suppression():
    state = {"counters": {
        "aho.council.audit.finding_filter.eligible_count": 5,
        "aho.council.audit.finding_filter.suppressed_count": 0,
    }}
    s = evaluate_all_surfaces(state)[3]
    assert s.color == BRICK_GREEN
    assert "no findings of the F-0.2.17-W3-001" in s.headline


def test_filter_surface_reds_on_filter_error():
    state = {"counters": {
        "aho.council.audit.finding_filter.eligible_count": 3,
        "aho.council.audit.finding_filter.error_count": 1,
    }}
    s = evaluate_all_surfaces(state)[3]
    assert s.color == BRICK_RED
    assert "instrumentation problem" in s.headline


def test_filter_surface_unknown_when_no_signal():
    s = evaluate_all_surfaces({"counters": {}})[3]
    assert s.color == BRICK_UNKNOWN


def test_filter_surface_drill_down_surfaces_suppressed_findings():
    audit_records = [
        {
            "audit_path": "audit/W4.json",
            "iteration": "0.2.17",
            "workstream": "W4",
            "audit_kind": "self",
            "suppressed_findings": [
                {
                    "reason": "registered_id_flagged_as_fake",
                    "matched_phrase": "does not look real",
                    "matched_registered_anchor": "F-0.2.17-W1-003",
                    "finding": {"id": "G081", "severity": "critical"},
                }
            ],
        }
    ]
    state = {"counters": {
        "aho.council.audit.finding_filter.eligible_count": 1,
        "aho.council.audit.finding_filter.suppressed_count": 1,
    }}
    s = evaluate_all_surfaces(state, audit_disposition_records=audit_records)[3]
    assert s.color == BRICK_GREEN
    assert len(s.drill_down) == 1
    drill = s.drill_down[0]
    assert drill["workstream"] == "W4"
    assert drill["suppressed_findings"][0]["matched_registered_anchor"] == "F-0.2.17-W1-003"


def test_filter_surface_drill_down_skips_records_with_no_suppression():
    """Audit records with empty suppressed_findings list should not show
    up in drill-down (drill is reserved for inspectable suppressions)."""
    audit_records = [
        {"audit_path": "audit/W3.json", "suppressed_findings": []},
        {"audit_path": "audit/W4.json"},  # no suppressed_findings key at all
    ]
    s = evaluate_all_surfaces({"counters": {}}, audit_disposition_records=audit_records)[3]
    assert s.drill_down == []


def test_overview_reds_when_any_surface_reds():
    state = {"counters": {
        "aho.council.triage.invocation_count": 2,
        "aho.council.triage.malformed_count": 0,
        "aho.council.audit.invocation_count": 2,
        "aho.council.audit.confidence_floor_lock_count": 0,
        "aho.council.dispatch.invocation_count": 2,
        "aho.council.dispatch.role_collapse_tripwire_fired": 1,  # red
        "aho.council.audit.finding_filter.eligible_count": 2,
        "aho.council.audit.finding_filter.suppressed_count": 0,
    }}
    surfaces = evaluate_all_surfaces(state)
    overview = evaluate_overview(surfaces)
    assert overview.color == BRICK_RED
    assert overview.detail["red_count"] == 1


def test_overview_greens_when_at_least_one_surface_greens_and_no_red():
    state = {"counters": {
        "aho.council.audit.invocation_count": 2,
        "aho.council.audit.confidence_floor_lock_count": 0,
    }}
    surfaces = evaluate_all_surfaces(state)
    overview = evaluate_overview(surfaces)
    assert overview.color == BRICK_GREEN


def test_overview_unknown_when_all_surfaces_unknown():
    surfaces = evaluate_all_surfaces({"counters": {}})
    overview = evaluate_overview(surfaces)
    assert overview.color == BRICK_UNKNOWN


def test_render_dashboard_returns_full_payload():
    state = {"counters": {
        "aho.council.audit.invocation_count": 1,
        "aho.council.audit.confidence_floor_lock_count": 0,
        "aho.council.audit.finding_filter.eligible_count": 1,
        "aho.council.audit.finding_filter.suppressed_count": 1,
    }}
    payload = render_dashboard(state)
    assert payload["kind"] == "anti_rubber_stamp_verification_dashboard"
    assert payload["schema_version"] == 1
    assert "overview" in payload
    assert len(payload["surfaces"]) == 4
    assert [s["surface_id"] for s in payload["surfaces"]] == list(SURFACE_IDS)
