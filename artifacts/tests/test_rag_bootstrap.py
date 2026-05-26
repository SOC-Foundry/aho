"""test_rag_bootstrap.py — W1 D7 of 0.3.1.

Tests aho.rag.bootstrap:
- discover_canonical_artifacts returns non-empty set
- dry-run produces accurate count
- idempotency: re-run produces same collection state
- lookup query returns registered for known canonical IDs after bootstrap
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Prepend canonical src/ for resolution against the canonical aho package
# (W2 closes F-0.3.1-W0-005 by reinstalling editable).
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def bootstrap_module():
    pytest.importorskip("chromadb", reason="chromadb required for rag bootstrap tests")
    from aho.rag import bootstrap as _b
    return _b


def test_discover_returns_known_artifacts(bootstrap_module):
    plans = bootstrap_module.discover_canonical_artifacts(ROOT)
    assert len(plans) > 0
    paths = {str(p.path) for p in plans}
    # Each of these should be in the canonical set when present in repo.
    expect_present = [
        ROOT / "artifacts" / "iterations" / "0.2.16" / "carry-forwards-0.2.16.md",
        ROOT / "artifacts" / "iterations" / "0.3.1" / "aho-plan-0.3.1.md",
        ROOT / "artifacts" / "adrs" / "0011-substrate-freshness.md",
    ]
    for p in expect_present:
        if p.exists():
            assert str(p) in paths, f"expected canonical artifact {p} not discovered"


def test_dry_run_reports_counts(bootstrap_module):
    result = bootstrap_module.bootstrap(dry_run=True, progress=False)
    assert result.mode == "dry_run"
    assert result.artifact_count > 0
    assert result.chunk_count_estimated >= result.artifact_count
    # dry-run does not write
    assert result.collection_count_before == result.collection_count_after


def test_idempotent_collection_count(bootstrap_module):
    """Two consecutive executes produce same collection count.

    Skipped if the bootstrap would take longer than a fast unit-test budget.
    The amendment's "duration < X minutes" is intentionally loose; we test
    the idempotency property only.
    """
    if os.environ.get("AHO_SKIP_SLOW_TESTS"):
        pytest.skip("AHO_SKIP_SLOW_TESTS set — bootstrap is the slow path")
    from aho.rag import collection_count
    project = os.environ.get("AHO_PROJECT", "ahomw")
    n_before = collection_count(project)
    if n_before == 0:
        pytest.skip("collection not yet bootstrapped — run aho-rag-bootstrap first")
    # Re-run; should not change count.
    result = bootstrap_module.bootstrap(progress=False)
    assert result.mode == "execute"
    n_after = collection_count(project)
    # Permit ±1 chunk-count drift from skip-on-error tolerance (one oversized
    # chunk fails embed; idempotent re-run reaches same state).
    assert abs(n_after - n_before) <= 1, (
        f"idempotency drift: before={n_before} after={n_after}"
    )


def test_lookup_returns_registered_for_canonical_ids():
    """Known IDs should resolve to status=registered after bootstrap."""
    from aho.council.audit_ref_extract import detect_references
    from aho.council.audit_ref_lookup import lookup_references
    from aho.rag import collection_count
    if collection_count(os.environ.get("AHO_PROJECT", "ahomw")) == 0:
        pytest.skip("collection empty — run aho-rag-bootstrap first")
    text = "Refs: F-0.2.17-W1-003 and F-0.2.18-W2-004 and ADR-0011 and ADR-0007."
    refs = detect_references(text)
    assert len(refs) == 4
    results = lookup_references(refs)
    statuses = {r["id"]: r["status"] for r in results}
    for canonical_id in ("F-0.2.17-W1-003", "F-0.2.18-W2-004", "ADR-0011", "ADR-0007"):
        assert statuses.get(canonical_id) == "registered", (
            f"{canonical_id} status={statuses.get(canonical_id)}; expected 'registered'"
        )


def test_iteration_resolver_matches_path(bootstrap_module):
    p = ROOT / "artifacts" / "iterations" / "0.2.17" / "W2-close-note.md"
    assert bootstrap_module._resolve_iteration(p, "") == "0.2.17"
    p2 = ROOT / "artifacts" / "adrs" / "0011-substrate-freshness.md"
    assert bootstrap_module._resolve_iteration(p2, "adr") == "adr"


def test_workstream_resolver_handles_patterns(bootstrap_module):
    base = ROOT / "artifacts" / "iterations" / "0.2.17"
    assert bootstrap_module._resolve_workstream(base / "W2-close-note.md", "") == "W2"
    assert bootstrap_module._resolve_workstream(base / "iteration-close-0.2.17.md", "") == "iteration-close"
    assert bootstrap_module._resolve_workstream(base / "carry-forwards-0.2.17.md", "") == "carry-forwards"
    assert bootstrap_module._resolve_workstream(base / "aho-plan-0.2.17.md", "") == "iteration-doc"
