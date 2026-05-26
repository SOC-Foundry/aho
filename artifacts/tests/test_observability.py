"""test_observability.py — W1 D7 of 0.3.1.

Tests aho.observability:
- record_observable appends valid JSONL
- last_verified_age_seconds scans + computes age
- fact_color tri-cascade green/yellow/red
- snapshot_all_facts returns per-fact rows
- stale_count agrees with snapshot
- ProbeRecord serializes correctly
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def isolated_log(tmp_path, monkeypatch):
    """Re-route OBSERVABLES_LOG to a tmp file for the test."""
    log_path = tmp_path / "observables.jsonl"
    monkeypatch.setenv("AHO_OBSERVABLES_LOG", str(log_path))
    # Reload module-level constant
    import aho.observability as obs_module
    monkeypatch.setattr(obs_module, "OBSERVABLES_LOG", log_path)
    return log_path


def test_record_observable_writes_jsonl(isolated_log):
    from aho.observability import record_observable
    rec = record_observable(
        "tailnet_domain",
        host="testhost",
        probe_outcome="ok",
        value_observed="example.ts.net",
        probe_command="probe_test",
        duration_ms=42,
    )
    assert rec.fact_id == "tailnet_domain"
    assert rec.probe_outcome == "ok"
    assert isolated_log.exists()
    lines = isolated_log.read_text().splitlines()
    assert len(lines) == 1
    d = json.loads(lines[0])
    assert d["fact_id"] == "tailnet_domain"
    assert d["host"] == "testhost"
    assert d["duration_ms"] == 42


def test_invalid_outcome_raises(isolated_log):
    from aho.observability import record_observable, ObservabilityError
    with pytest.raises(ObservabilityError):
        record_observable("foo", probe_outcome="bogus")


def test_age_seconds_zero_for_fresh_probe(isolated_log):
    from aho.observability import record_observable, last_verified_age_seconds
    record_observable("ollama_api_endpoint", host="testhost", probe_outcome="ok",
                       value_observed="ok")
    age = last_verified_age_seconds("ollama_api_endpoint", host="testhost")
    assert age is not None
    assert 0 <= age < 5


def test_age_returns_none_when_never_probed(isolated_log):
    from aho.observability import last_verified_age_seconds
    age = last_verified_age_seconds("nonexistent_fact")
    assert age is None


def test_fail_outcome_not_counted_for_age(isolated_log):
    """last_verified_age_seconds only considers probe_outcome=ok records."""
    from aho.observability import record_observable, last_verified_age_seconds
    record_observable("broker_socket", probe_outcome="fail", host="t")
    age = last_verified_age_seconds("broker_socket", host="t")
    assert age is None


def test_color_cascade():
    from aho.observability import fact_color
    assert fact_color(10, 3600) == "green"        # fresh
    assert fact_color(3600, 3600) == "yellow"     # equal to threshold = yellow zone
    assert fact_color(3 * 3600 + 1, 3600) == "red" # past 3x
    assert fact_color(None, 3600) == "red"        # never probed


def test_snapshot_all_facts_has_13_rows(isolated_log):
    from aho.observability import snapshot_all_facts, FACT_WARNING_AGE_SECONDS
    s = snapshot_all_facts()
    assert len(s) == 13
    assert set(r["fact_id"] for r in s) == set(FACT_WARNING_AGE_SECONDS.keys())
    for row in s:
        assert row["color"] in ("green", "yellow", "red")
        assert row["warning_age_seconds"] > 0


def test_stale_count_matches_snapshot(isolated_log):
    from aho.observability import snapshot_all_facts, stale_count
    s = snapshot_all_facts()
    expected = sum(1 for r in s if r["color"] in ("yellow", "red"))
    assert stale_count(s) == expected


def test_warning_threshold_lookup():
    from aho.observability import warning_age_seconds, ObservabilityError
    assert warning_age_seconds("tailnet_domain") == 30 * 24 * 3600
    with pytest.raises(ObservabilityError):
        warning_age_seconds("not_a_real_fact_id")


def test_host_unreachable_outcome_valid(isolated_log):
    """host_unreachable is a distinct outcome class; doesn't raise."""
    from aho.observability import record_observable
    rec = record_observable(
        "tailnet_domain",
        host="remote-host-fixture",
        probe_outcome="host_unreachable",
    )
    assert rec.probe_outcome == "host_unreachable"
    # And does NOT count toward age (only ok does)
    from aho.observability import last_verified_age_seconds
    age = last_verified_age_seconds("tailnet_domain", host="remote-host-fixture")
    assert age is None  # no successful probe yet
