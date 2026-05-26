"""W4 D3 - materiality four-bucket surface acceptance tests.

Verifies:
  - normalize_materiality_state coerces partial / malformed input
    without crashing and fills missing buckets / severities to zero
  - each bucket surface renders the right counter
  - overview aggregates all four buckets with correct catch-rate components
  - render_dashboard_payload produces the JSON contract the dashboard
    expects
  - materiality_state_from_otel_counters maps the canonical OTEL counter
    names to the canonical bucket IDs
  - bucket coverage matches the four ADR-0010 buckets exactly (drift
    surfaces loud)
"""
from __future__ import annotations

import pytest

from aho.claw3d.lego.materiality_surfaces import (
    BUCKET_DESCRIPTIONS,
    CANONICAL_BUCKETS,
    COUNTER_TO_BUCKET,
    SEVERITIES,
    materiality_state_from_otel_counters,
    normalize_materiality_state,
    render_all_buckets,
    render_bucket_surface,
    render_dashboard_payload,
    render_overview,
)


def test_canonical_buckets_match_adr_0010_four_bucket_protocol():
    assert CANONICAL_BUCKETS == (
        "caught_by_llama",
        "caught_by_drafter",
        "escaped",
        "carry_forward_resolution",
    )
    assert set(BUCKET_DESCRIPTIONS.keys()) == set(CANONICAL_BUCKETS)


def test_counter_to_bucket_covers_w2_materiality_counters():
    expected = {
        "aho.materiality.claim_vs_artifact_mismatches.caught_by_llama":
            "caught_by_llama",
        "aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter":
            "caught_by_drafter",
        "aho.materiality.claim_vs_artifact_mismatches.escaped":
            "escaped",
        "aho.materiality.carry_forward_resolution_rate":
            "carry_forward_resolution",
    }
    assert COUNTER_TO_BUCKET == expected


def test_normalize_materiality_state_fills_missing_buckets():
    norm = normalize_materiality_state({})
    for b in CANONICAL_BUCKETS:
        assert norm["buckets"][b]["count"] == 0
        for sev in SEVERITIES:
            assert norm["buckets"][b]["by_severity"][sev] == 0
        assert norm["buckets"][b]["last_seen_utc"] is None


def test_normalize_materiality_state_passes_through_partial_input():
    raw = {
        "iteration": "0.2.17",
        "workstream": "W4",
        "buckets": {
            "caught_by_llama": {
                "count": 5,
                "by_severity": {"info": 1, "critical": 4},
                "last_seen_utc": "2026-05-03T15:30:00+00:00",
            },
        },
    }
    norm = normalize_materiality_state(raw)
    assert norm["iteration"] == "0.2.17"
    assert norm["workstream"] == "W4"
    assert norm["buckets"]["caught_by_llama"]["count"] == 5
    assert norm["buckets"]["caught_by_llama"]["by_severity"]["important"] == 0
    assert norm["buckets"]["caught_by_llama"]["by_severity"]["info"] == 1
    assert norm["buckets"]["caught_by_drafter"]["count"] == 0


def test_render_bucket_surface_returns_canonical_shape():
    state = {
        "buckets": {
            "caught_by_llama": {
                "count": 3,
                "by_severity": {"info": 1, "important": 1, "critical": 1},
            },
        },
    }
    s = render_bucket_surface("caught_by_llama", state)
    assert s.bucket_id == "caught_by_llama"
    assert s.count == 3
    assert s.by_severity == {"info": 1, "important": 1, "critical": 1}
    assert s.description == BUCKET_DESCRIPTIONS["caught_by_llama"]


def test_render_bucket_surface_unknown_bucket_raises():
    with pytest.raises(ValueError):
        render_bucket_surface("not_a_bucket", {})


def test_render_all_buckets_returns_four_surfaces_in_canonical_order():
    surfaces = render_all_buckets({})
    assert [s.bucket_id for s in surfaces] == list(CANONICAL_BUCKETS)


def test_render_overview_aggregates_catch_rate_components():
    raw = {
        "iteration": "0.2.17",
        "workstream": "W4",
        "buckets": {
            "caught_by_llama":          {"count": 10, "by_severity": {"info": 4, "important": 4, "critical": 2}},
            "caught_by_drafter":        {"count": 3,  "by_severity": {"info": 1, "important": 2, "critical": 0}},
            "escaped":                  {"count": 1,  "by_severity": {"info": 0, "important": 0, "critical": 1}},
            "carry_forward_resolution": {"count": 7,  "by_severity": {"info": 7, "important": 0, "critical": 0}},
        },
    }
    overview = render_overview(raw)
    assert overview.iteration == "0.2.17"
    assert overview.workstream == "W4"
    assert overview.catch_rate_components == {
        "caught_by_llama": 10,
        "caught_by_drafter": 3,
        "escaped": 1,
    }
    assert overview.carry_forward_resolution_count == 7
    assert len(overview.buckets) == 4


def test_render_dashboard_payload_shape_is_complete():
    raw = {
        "iteration": "0.2.17",
        "workstream": "W4",
        "buckets": {
            "caught_by_llama":   {"count": 5, "by_severity": {"info": 1, "important": 3, "critical": 1}},
            "caught_by_drafter": {"count": 2, "by_severity": {"info": 1, "important": 1, "critical": 0}},
            "escaped":           {"count": 0, "by_severity": {"info": 0, "important": 0, "critical": 0}},
            "carry_forward_resolution": {"count": 4, "by_severity": {"info": 4, "important": 0, "critical": 0}},
        },
    }
    payload = render_dashboard_payload(raw)
    assert payload["kind"] == "materiality_four_bucket_dashboard"
    assert payload["schema_version"] == 1
    assert payload["overview"]["catch_rate_components"]["caught_by_llama"] == 5
    assert payload["overview"]["total_caught"] == 7
    assert payload["overview"]["total_escaped"] == 0
    assert payload["overview"]["carry_forward_resolution_count"] == 4
    assert len(payload["buckets"]) == 4
    bucket_ids = [b["bucket_id"] for b in payload["buckets"]]
    assert bucket_ids == list(CANONICAL_BUCKETS)


def test_materiality_state_from_otel_counters_maps_canonical_names():
    counters = {
        "aho.materiality.claim_vs_artifact_mismatches.caught_by_llama": {
            "info": 2, "important": 5, "critical": 3,
        },
        "aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter": {
            "info": 1, "important": 1, "critical": 0,
        },
        "aho.materiality.claim_vs_artifact_mismatches.escaped": {
            "info": 0, "important": 0, "critical": 1,
        },
        "aho.materiality.carry_forward_resolution_rate": {
            "info": 4, "important": 0, "critical": 0,
        },
        "aho.materiality.unrelated_counter": {"info": 99},
    }
    state = materiality_state_from_otel_counters(
        counters, iteration="0.2.17", workstream="W4",
    )
    assert state["iteration"] == "0.2.17"
    assert state["workstream"] == "W4"
    assert state["buckets"]["caught_by_llama"]["count"] == 10
    assert state["buckets"]["caught_by_llama"]["by_severity"] == {
        "info": 2, "important": 5, "critical": 3,
    }
    assert state["buckets"]["escaped"]["count"] == 1
    # Unknown counter is ignored - buckets fill normally.
    assert "unrelated" not in state["buckets"]
