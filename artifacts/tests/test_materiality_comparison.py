"""W4 D5 — materiality comparison surface acceptance tests.

Verifies:
  - Baseline reconstruction from 0.2.16 audits produces non-pathological
    numbers (sanity-bounded, not "obviously wrong" per plan-doc halt
    condition).
  - Comparison surface renders side-by-side rows with deltas.
  - N < threshold annotation surfaces.
  - Schema contract.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aho.claw3d.lego.materiality_comparison import (
    N_ITERATIONS_THRESHOLD,
    render_comparison,
)
from aho.claw3d.lego.materiality_surfaces import (
    materiality_state_from_otel_counters,
)
from aho.materiality_baseline_extract import (
    BaselineExtractError,
    extract_carry_forward_resolution_count,
    reconstruct_0_2_16_baseline,
    reconstruct_baseline,
)


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "artifacts" / "iterations" / "0.2.16").is_dir():
            return parent
    raise RuntimeError("could not locate repo root")


REPO_ROOT = _repo_root()


def test_reconstruct_0_2_16_baseline_extracts_caught_count():
    baseline = reconstruct_0_2_16_baseline(REPO_ROOT)
    caught = baseline["buckets"]["caught_by_llama"]
    # Manually verified by Bash inspection earlier:
    # W0=3, W1=5, W2=2, W3=3, W4=2 → 15 total findings across 0.2.16.
    assert caught["count"] == 15, (
        f"caught_by_auditor count mismatch with manual Bash inspection: "
        f"got {caught['count']}, expected 15 (W0=3, W1=5, W2=2, W3=3, W4=2)"
    )
    # Sum-of-severities equals total count (no off-by-one in the rollup).
    sev_sum = sum(caught["by_severity"].values())
    assert sev_sum == caught["count"]


def test_reconstruct_0_2_16_baseline_provenance_is_inspectable():
    baseline = reconstruct_0_2_16_baseline(REPO_ROOT)
    prov = baseline["baseline_provenance"]
    # Five W*.json sources expected from 0.2.16 audit dir.
    assert len(prov["audit_sources"]) == 5
    assert prov["buckets_unknown"] == ["caught_by_drafter", "escaped"]
    assert "caught_by_llama" in prov["buckets_reconstructed"]
    assert "carry_forward_resolution" in prov["buckets_reconstructed"]


def test_reconstruct_baseline_raises_on_missing_root(tmp_path):
    with pytest.raises(BaselineExtractError):
        reconstruct_baseline(tmp_path / "nonexistent", iteration_label="x")


def test_reconstruct_baseline_handles_empty_audit_dir(tmp_path):
    (tmp_path / "audit").mkdir()
    base = reconstruct_baseline(tmp_path, iteration_label="empty")
    assert base["buckets"]["caught_by_llama"]["count"] == 0
    assert base["baseline_provenance"]["audit_sources"] == []


def test_reconstruct_baseline_normalises_severity_synonyms(tmp_path):
    (tmp_path / "audit").mkdir()
    payload = {
        "findings": {
            "AF1": {"severity": "high", "description": "x"},
            "AF2": {"severity": "moderate", "description": "y"},
            "AF3": {"severity": "low", "description": "z"},
        }
    }
    (tmp_path / "audit" / "W0.json").write_text(json.dumps(payload))
    base = reconstruct_baseline(tmp_path, iteration_label="t")
    bucket = base["buckets"]["caught_by_llama"]
    assert bucket["by_severity"]["critical"] == 1  # high → critical
    assert bucket["by_severity"]["important"] == 1  # moderate → important
    assert bucket["by_severity"]["info"] == 1  # low → info
    assert bucket["count"] == 3


def test_extract_carry_forward_resolution_handles_missing_path(tmp_path):
    assert extract_carry_forward_resolution_count(tmp_path / "missing.md") == 0
    assert extract_carry_forward_resolution_count(None) == 0


def test_extract_carry_forward_resolution_counts_closed_entries(tmp_path):
    p = tmp_path / "carry-forwards-x.md"
    p.write_text(
        "- **F-X-001 — closed in W2**: detail here\n"
        "- **F-X-002 — open**: detail\n"
        "- **F-X-003 — resolved by drafter**: detail\n"
        "- **AF002 — closed**: detail\n"
        "- **AF003 — closing per W3 close note**: detail\n"
    )
    n = extract_carry_forward_resolution_count(p)
    assert n == 3, (
        f"counter expected 3 (F-X-001 closed, F-X-003 resolved, AF002"
        f" closed); got {n}"
    )


def test_render_comparison_produces_side_by_side_rows():
    baseline = {
        "iteration": "0.2.16",
        "workstream": "(rolled-up)",
        "buckets": {
            "caught_by_llama":          {"count": 15, "by_severity": {"info": 10, "important": 4, "critical": 1}},
            "caught_by_drafter":        {"count": 0,  "by_severity": {}},
            "escaped":                  {"count": 0,  "by_severity": {}},
            "carry_forward_resolution": {"count": 7,  "by_severity": {"info": 7}},
        },
    }
    post = materiality_state_from_otel_counters(
        {
            "aho.materiality.claim_vs_artifact_mismatches.caught_by_llama": {
                "info": 4, "important": 2, "critical": 1,
            },
            "aho.materiality.carry_forward_resolution_rate": {
                "info": 3, "important": 0, "critical": 0,
            },
        },
        iteration="0.2.17",
        workstream="(rolled-up)",
    )

    cmp_out = render_comparison(baseline, post, n_iterations_observed=4)

    assert cmp_out["kind"] == "materiality_comparison_surface"
    assert cmp_out["schema_version"] == 1
    assert cmp_out["left_column"]["iteration"] == "0.2.16"
    assert cmp_out["right_column"]["iteration"] == "0.2.17"
    assert len(cmp_out["rows"]) == 4
    caught_row = next(r for r in cmp_out["rows"] if r["bucket_id"] == "caught_by_llama")
    assert caught_row["baseline"]["count"] == 15
    assert caught_row["post_base_container"]["count"] == 7
    assert caught_row["delta"]["count"] == -8
    assert caught_row["delta"]["by_severity"]["info"] == -6


def test_render_comparison_below_threshold_annotates_n():
    cmp_out = render_comparison({}, {}, n_iterations_observed=4)
    assert cmp_out["below_threshold"] is True
    assert cmp_out["n_iterations_threshold"] == N_ITERATIONS_THRESHOLD
    assert any(
        f"N=4 below threshold of {N_ITERATIONS_THRESHOLD}" in a
        for a in cmp_out["annotations"]
    )


def test_render_comparison_at_threshold_drops_warning():
    cmp_out = render_comparison({}, {}, n_iterations_observed=8)
    assert cmp_out["below_threshold"] is False
    assert any(
        f"N=8 meets threshold of {N_ITERATIONS_THRESHOLD}" in a
        for a in cmp_out["annotations"]
    )


def test_render_comparison_baseline_provenance_propagates():
    baseline = {
        "iteration": "0.2.16",
        "buckets": {b: {"count": 0} for b in
                    ("caught_by_llama", "caught_by_drafter",
                     "escaped", "carry_forward_resolution")},
        "baseline_provenance": {
            "iteration_root": "/x/y",
            "audit_sources": ["a.json"],
            "buckets_unknown": ["caught_by_drafter", "escaped"],
            "buckets_reconstructed": ["caught_by_llama"],
            "notes": ["test"],
        },
    }
    cmp_out = render_comparison(baseline, {}, n_iterations_observed=4)
    assert cmp_out["baseline_provenance"]["audit_sources"] == ["a.json"]
