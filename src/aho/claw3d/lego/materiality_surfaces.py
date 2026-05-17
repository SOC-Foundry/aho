"""W4 D3 — materiality four-bucket dashboard surfaces.

Renders the four ADR-0010 materiality buckets as inspectable dashboard
surfaces. Each surface reads one counter from the W2 materiality OTEL
output (``aho.materiality.*``) and exposes:

  - the running total
  - per-severity breakdown (info / important / critical)
  - last-update timestamp (from the aggregator's window)

Plus an overview surface that combines all four buckets into a single
header rendering. The overview is the at-a-glance materiality view
the dashboard surfaces by default; the per-bucket surfaces are
drill-downs.

All surfaces consume a normalized ``materiality_state`` dict shape:

    {
        "buckets": {
            "caught_by_llama":              {"count": int,
                                             "by_severity": {info, important, critical},
                                             "last_seen_utc": str | None},
            "caught_by_drafter":            {... same shape ...},
            "escaped":                      {... same shape ...},
            "carry_forward_resolution":     {... same shape ...},
        },
        "iteration": "0.2.17",
        "workstream": "W4",
    }

Per ADR-0010, the four buckets are:

  1. caught_by_llama         — auditor catches a claim/artifact mismatch
  2. caught_by_drafter       — drafter (gap-net) catches one the auditor missed
  3. escaped                 — surfaced retrospectively, escaped sealed iteration
  4. carry_forward_resolution_rate — explicit carry-forward closure count

The first three feed the materiality protocol's catch-rate metric; the
fourth feeds the carry-forward closure rate. Together they render the
"is the auditor doing useful work?" question that 0.2.17's base-tier
auditor seat is supposed to answer empirically.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SEVERITIES = ("info", "important", "critical")


CANONICAL_BUCKETS = (
    "caught_by_llama",
    "caught_by_drafter",
    "escaped",
    "carry_forward_resolution",
)


COUNTER_TO_BUCKET = {
    "aho.materiality.claim_vs_artifact_mismatches.caught_by_llama": "caught_by_llama",
    "aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter": "caught_by_drafter",
    "aho.materiality.claim_vs_artifact_mismatches.escaped": "escaped",
    "aho.materiality.carry_forward_resolution_rate": "carry_forward_resolution",
}


BUCKET_DESCRIPTIONS = {
    "caught_by_llama": (
        "Claim/artifact mismatches surfaced by the llama auditor seat."
    ),
    "caught_by_drafter": (
        "Mismatches surfaced by the drafter (gap-net) after the auditor"
        " passed the artifact."
    ),
    "escaped": (
        "Mismatches surfaced retrospectively — escaped a sealed iteration."
    ),
    "carry_forward_resolution": (
        "Carry-forwards explicitly closed by reference in a workstream"
        " output."
    ),
}


@dataclass
class BucketSurface:
    bucket_id: str
    description: str
    count: int
    by_severity: Dict[str, int] = field(default_factory=dict)
    last_seen_utc: Optional[str] = None


@dataclass
class OverviewSurface:
    iteration: str
    workstream: str
    buckets: List[BucketSurface]
    catch_rate_components: Dict[str, int]
    carry_forward_resolution_count: int


def _empty_bucket_dict() -> Dict[str, Any]:
    return {
        "count": 0,
        "by_severity": {sev: 0 for sev in SEVERITIES},
        "last_seen_utc": None,
    }


def normalize_materiality_state(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce a raw materiality state dict into the normalized shape.

    Tolerates missing buckets (they fill to zero). Tolerates partial
    severity dicts (missing severities fill to zero). Returns a fresh
    dict — does not mutate input.
    """
    if not isinstance(raw, dict):
        raw = {}
    iteration = str(raw.get("iteration") or "unknown")
    workstream = str(raw.get("workstream") or "unknown")
    raw_buckets = raw.get("buckets") or {}
    out_buckets: Dict[str, Any] = {}
    for bucket_id in CANONICAL_BUCKETS:
        entry = raw_buckets.get(bucket_id) or {}
        merged = _empty_bucket_dict()
        try:
            merged["count"] = int(entry.get("count") or 0)
        except (TypeError, ValueError):
            merged["count"] = 0
        sev_in = entry.get("by_severity") or {}
        if isinstance(sev_in, dict):
            for sev in SEVERITIES:
                try:
                    merged["by_severity"][sev] = int(sev_in.get(sev) or 0)
                except (TypeError, ValueError):
                    merged["by_severity"][sev] = 0
        merged["last_seen_utc"] = entry.get("last_seen_utc")
        out_buckets[bucket_id] = merged
    return {
        "iteration": iteration,
        "workstream": workstream,
        "buckets": out_buckets,
    }


def render_bucket_surface(bucket_id: str, state: Dict[str, Any]) -> BucketSurface:
    """Render one bucket surface from a normalized materiality state."""
    if bucket_id not in CANONICAL_BUCKETS:
        raise ValueError(
            f"unknown bucket_id {bucket_id!r}; expected one of {CANONICAL_BUCKETS}"
        )
    norm = normalize_materiality_state(state)
    entry = norm["buckets"][bucket_id]
    return BucketSurface(
        bucket_id=bucket_id,
        description=BUCKET_DESCRIPTIONS[bucket_id],
        count=entry["count"],
        by_severity=dict(entry["by_severity"]),
        last_seen_utc=entry["last_seen_utc"],
    )


def render_all_buckets(state: Dict[str, Any]) -> List[BucketSurface]:
    return [render_bucket_surface(b, state) for b in CANONICAL_BUCKETS]


def render_overview(state: Dict[str, Any]) -> OverviewSurface:
    """Render the at-a-glance overview that aggregates all four buckets."""
    norm = normalize_materiality_state(state)
    buckets = render_all_buckets(norm)
    catch_rate = {
        "caught_by_llama": norm["buckets"]["caught_by_llama"]["count"],
        "caught_by_drafter": norm["buckets"]["caught_by_drafter"]["count"],
        "escaped": norm["buckets"]["escaped"]["count"],
    }
    carry_forward = norm["buckets"]["carry_forward_resolution"]["count"]
    return OverviewSurface(
        iteration=norm["iteration"],
        workstream=norm["workstream"],
        buckets=buckets,
        catch_rate_components=catch_rate,
        carry_forward_resolution_count=carry_forward,
    )


def render_dashboard_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    """Render the full D3 dashboard payload — the four bucket surfaces
    plus the overview, in JSON form suitable for /api/state or the
    dashboard renderer."""
    overview = render_overview(state)
    buckets = render_all_buckets(state)
    return {
        "kind": "materiality_four_bucket_dashboard",
        "schema_version": 1,
        "iteration": overview.iteration,
        "workstream": overview.workstream,
        "overview": {
            "catch_rate_components": overview.catch_rate_components,
            "carry_forward_resolution_count": overview.carry_forward_resolution_count,
            "total_caught": (
                overview.catch_rate_components["caught_by_llama"]
                + overview.catch_rate_components["caught_by_drafter"]
            ),
            "total_escaped": overview.catch_rate_components["escaped"],
        },
        "buckets": [
            {
                "bucket_id": b.bucket_id,
                "description": b.description,
                "count": b.count,
                "by_severity": b.by_severity,
                "last_seen_utc": b.last_seen_utc,
            }
            for b in buckets
        ],
    }


def materiality_state_from_otel_counters(
    counters: Dict[str, Dict[str, int]],
    *,
    iteration: str = "unknown",
    workstream: str = "unknown",
    last_seen_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a normalized materiality_state dict from the aggregator's
    OTEL counter shape.

    ``counters`` is a dict keyed by counter name (``aho.materiality.*``).
    Each value is itself a dict keyed by severity ('info'/'important'/
    'critical'), with int counts. Counters not in ``COUNTER_TO_BUCKET``
    are ignored — drift detection (via tests) catches missing wiring,
    not silent data loss.
    """
    buckets: Dict[str, Any] = {b: _empty_bucket_dict() for b in CANONICAL_BUCKETS}
    for counter_name, by_sev in (counters or {}).items():
        bucket_id = COUNTER_TO_BUCKET.get(counter_name)
        if bucket_id is None:
            continue
        if not isinstance(by_sev, dict):
            continue
        total = 0
        for sev in SEVERITIES:
            try:
                v = int(by_sev.get(sev) or 0)
            except (TypeError, ValueError):
                v = 0
            buckets[bucket_id]["by_severity"][sev] = v
            total += v
        buckets[bucket_id]["count"] = total
        buckets[bucket_id]["last_seen_utc"] = last_seen_utc
    return {
        "iteration": iteration,
        "workstream": workstream,
        "buckets": buckets,
    }


__all__ = [
    "BUCKET_DESCRIPTIONS",
    "BucketSurface",
    "CANONICAL_BUCKETS",
    "COUNTER_TO_BUCKET",
    "OverviewSurface",
    "SEVERITIES",
    "materiality_state_from_otel_counters",
    "normalize_materiality_state",
    "render_all_buckets",
    "render_bucket_surface",
    "render_dashboard_payload",
    "render_overview",
]
