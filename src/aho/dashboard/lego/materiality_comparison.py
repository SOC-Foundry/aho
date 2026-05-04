"""W4 D5 — materiality comparison surface (with vs without base container).

Side-by-side two-column rendering: pre-base-container baseline (0.2.16)
on the left, post-base-container actuals (0.2.17) on the right. Each
column uses the same four-bucket protocol shape so deltas are
inspectable.

The surface explicitly annotates that the comparison sample is below
the threshold (N=4 below threshold of 8 iterations) — drafter or
operator can see at a glance that the comparison is *suggestive*, not
*conclusive*.

Inputs:

  - ``baseline_state`` — normalized materiality state from
    ``aho.materiality_baseline_extract.reconstruct_baseline``.
  - ``post_state`` — normalized materiality state for the post-
    base-container iteration (0.2.17), built from live OTEL counter
    state via
    ``aho.dashboard.lego.materiality_surfaces.materiality_state_from_otel_counters``.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .materiality_surfaces import (
    BUCKET_DESCRIPTIONS,
    CANONICAL_BUCKETS,
    SEVERITIES,
    normalize_materiality_state,
)


N_ITERATIONS_THRESHOLD = 8


def _row(
    bucket_id: str, baseline_state: Dict[str, Any], post_state: Dict[str, Any]
) -> Dict[str, Any]:
    base_b = baseline_state["buckets"][bucket_id]
    post_b = post_state["buckets"][bucket_id]
    return {
        "bucket_id": bucket_id,
        "description": BUCKET_DESCRIPTIONS[bucket_id],
        "baseline": {
            "count": base_b["count"],
            "by_severity": dict(base_b["by_severity"]),
        },
        "post_base_container": {
            "count": post_b["count"],
            "by_severity": dict(post_b["by_severity"]),
        },
        "delta": {
            "count": post_b["count"] - base_b["count"],
            "by_severity": {
                sev: post_b["by_severity"][sev] - base_b["by_severity"][sev]
                for sev in SEVERITIES
            },
        },
    }


def render_comparison(
    baseline_state: Dict[str, Any],
    post_state: Dict[str, Any],
    *,
    n_iterations_observed: int,
) -> Dict[str, Any]:
    """Render the side-by-side comparison surface as a JSON contract."""
    bnorm = normalize_materiality_state(baseline_state)
    pnorm = normalize_materiality_state(post_state)

    rows: List[Dict[str, Any]] = [
        _row(b, bnorm, pnorm) for b in CANONICAL_BUCKETS
    ]

    annotations: List[str] = []
    if n_iterations_observed < N_ITERATIONS_THRESHOLD:
        annotations.append(
            f"N={n_iterations_observed} below threshold of "
            f"{N_ITERATIONS_THRESHOLD} iterations — comparison is"
            " suggestive, not conclusive. Statistical confidence requires"
            f" ≥{N_ITERATIONS_THRESHOLD} iteration data points."
        )
    else:
        annotations.append(
            f"N={n_iterations_observed} meets threshold of "
            f"{N_ITERATIONS_THRESHOLD} iterations."
        )

    # Surface baseline_provenance from the baseline state if present —
    # falsifiable by drafter / operator.
    provenance = baseline_state.get("baseline_provenance")

    return {
        "kind": "materiality_comparison_surface",
        "schema_version": 1,
        "left_column": {
            "label": "Pre-base-container",
            "iteration": bnorm["iteration"],
            "workstream": bnorm["workstream"],
        },
        "right_column": {
            "label": "Post-base-container",
            "iteration": pnorm["iteration"],
            "workstream": pnorm["workstream"],
        },
        "rows": rows,
        "n_iterations_observed": n_iterations_observed,
        "n_iterations_threshold": N_ITERATIONS_THRESHOLD,
        "below_threshold": n_iterations_observed < N_ITERATIONS_THRESHOLD,
        "annotations": annotations,
        "baseline_provenance": provenance,
    }


__all__ = [
    "N_ITERATIONS_THRESHOLD",
    "render_comparison",
]
