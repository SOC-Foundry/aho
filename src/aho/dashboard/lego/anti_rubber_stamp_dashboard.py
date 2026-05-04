"""W4 D6 — anti-rubber-stamp verification dashboard (four surfaces + overview).

Three original failure-mode surfaces, plus the new D1 deterministic
post-hoc filter as a fourth hardening surface. Plus an overview surface
aggregating all four into a single state.

Surfaces:

  1. **nemotron_raise_on_malformed** — G083 protection on triage. Reds
     when nemotron triage emits an out-of-rubric category that the
     hardening would have raised on. Green when triage invocations
     proceed without malformed output.
  2. **llama_confidence_floor_lock** — Rubber-stamp protection on
     audit. Reds when the floor lock fires (model said clean at low
     confidence; hardening rewrote disposition to surface_to_drafter).
     Green when no lock fires across audit invocations.
  3. **role_collapse_tripwire** — D4's surface, surfaced here too as
     part of the anti-rubber-stamp verification view.
  4. **deterministic_post_hoc_filter** — NEW W4 D1. Surfaces filter
     suppression activity per audit, with drill-down to individual
     suppressed_findings records.

Plus an **overview** surface that combines the four into one
"hardening healthy?" state — green only if all four surfaces are
green or unknown (no firings indicate either healthy or no signal),
red if any surface reds.

The drill-down for surface 4 takes a list of audit dispositions and
their suppressed_findings — drafter or operator can inspect what was
suppressed per audit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .bricks import BRICK_GREEN, BRICK_RED, BRICK_UNKNOWN, _counter


SURFACE_IDS = (
    "nemotron_raise_on_malformed",
    "llama_confidence_floor_lock",
    "role_collapse_tripwire",
    "deterministic_post_hoc_filter",
)


SURFACE_DESCRIPTIONS = {
    "nemotron_raise_on_malformed": (
        "Nemotron triage out-of-rubric protection (G083). Hardening raises"
        " CouncilTriageMalformedError; this surface counts how often that"
        " hardening fired vs how many triage invocations succeeded."
    ),
    "llama_confidence_floor_lock": (
        "Llama audit confidence-floor lock. Hardening rewrites"
        " clean+low-confidence dispositions to surface_to_drafter; this"
        " surface counts lock firings."
    ),
    "role_collapse_tripwire": (
        "Drafter/auditor role-collapse trip-wire. Same signal as D4."
    ),
    "deterministic_post_hoc_filter": (
        "W4 D1 deterministic post-hoc filter on RAG-aware audit findings."
        " Suppresses findings where BOTH a registered anchor AND a fake-"
        "ID phrase appear in the description. Suppressed findings are"
        " recorded structurally for drafter / operator inspection."
    ),
}


@dataclass
class SurfaceState:
    surface_id: str
    description: str
    color: str  # green | red | unknown
    headline: str
    detail: Dict[str, Any] = field(default_factory=dict)
    drill_down: List[Dict[str, Any]] = field(default_factory=list)


def _nemotron_surface(state: Dict[str, Any]) -> SurfaceState:
    invocations = _counter(state, "aho.council.triage.invocation_count")
    malformed = _counter(state, "aho.council.triage.malformed_count")
    if malformed > 0:
        color = BRICK_RED
        headline = (
            f"Nemotron triage emitted {malformed} out-of-rubric output(s);"
            " hardening raised on each"
        )
    elif invocations > 0:
        color = BRICK_GREEN
        headline = (
            f"{invocations} triage invocation(s) succeeded with no"
            " out-of-rubric outputs"
        )
    else:
        color = BRICK_UNKNOWN
        headline = "no triage activity in window"
    return SurfaceState(
        surface_id="nemotron_raise_on_malformed",
        description=SURFACE_DESCRIPTIONS["nemotron_raise_on_malformed"],
        color=color,
        headline=headline,
        detail={
            "triage_invocation_count": invocations,
            "triage_malformed_count": malformed,
        },
    )


def _llama_floor_surface(state: Dict[str, Any]) -> SurfaceState:
    invocations = _counter(state, "aho.council.audit.invocation_count")
    locks = _counter(state, "aho.council.audit.confidence_floor_lock_count")
    if locks > 0:
        color = BRICK_RED
        headline = (
            f"Confidence-floor lock fired {locks} time(s); hardening"
            " prevented clean disposition at low confidence"
        )
    elif invocations > 0:
        color = BRICK_GREEN
        headline = (
            f"{invocations} audit invocation(s) with no confidence-floor"
            " lock firings"
        )
    else:
        color = BRICK_UNKNOWN
        headline = "no audit activity in window"
    return SurfaceState(
        surface_id="llama_confidence_floor_lock",
        description=SURFACE_DESCRIPTIONS["llama_confidence_floor_lock"],
        color=color,
        headline=headline,
        detail={
            "audit_invocation_count": invocations,
            "audit_confidence_floor_lock_count": locks,
        },
    )


def _role_collapse_surface(state: Dict[str, Any]) -> SurfaceState:
    fired = _counter(state, "aho.council.dispatch.role_collapse_tripwire_fired")
    invocations = _counter(state, "aho.council.dispatch.invocation_count")
    if fired > 0:
        color = BRICK_RED
        headline = (
            f"Role-collapse trip-wire fired {fired} time(s); drafter and"
            " auditor would have shared a model family"
        )
    elif invocations > 0:
        color = BRICK_GREEN
        headline = (
            f"{invocations} dispatch invocation(s); trip-wire never fired"
        )
    else:
        color = BRICK_UNKNOWN
        headline = "no dispatch activity in window"
    return SurfaceState(
        surface_id="role_collapse_tripwire",
        description=SURFACE_DESCRIPTIONS["role_collapse_tripwire"],
        color=color,
        headline=headline,
        detail={
            "dispatch_invocation_count": invocations,
            "tripwire_fired_count": fired,
        },
    )


def _filter_surface(
    state: Dict[str, Any],
    *,
    audit_disposition_records: Optional[List[Dict[str, Any]]] = None,
) -> SurfaceState:
    """The new W4 D1 hardening surface.

    Filter suppression activity is healthy (green) when the filter is
    eligible and operating — suppressions are NOT red. The filter is the
    fix, not the symptom. Red would indicate a filter error
    (filter_error_count > 0); the W4 D1 implementation cannot raise from
    the happy path, so red here is reserved for instrumentation problems.
    """
    eligible = _counter(state, "aho.council.audit.finding_filter.eligible_count")
    suppressed = _counter(state, "aho.council.audit.finding_filter.suppressed_count")
    errors = _counter(state, "aho.council.audit.finding_filter.error_count")

    if errors > 0:
        color = BRICK_RED
        headline = (
            f"Filter encountered {errors} error(s) — instrumentation"
            " problem requiring drafter inspection"
        )
    elif eligible > 0:
        color = BRICK_GREEN
        if suppressed > 0:
            headline = (
                f"Filter eligible on {eligible} audit(s); suppressed"
                f" {suppressed} fake-ID-on-registered-anchor finding(s)"
                " across the window"
            )
        else:
            headline = (
                f"Filter eligible on {eligible} audit(s); no findings of"
                " the F-0.2.17-W3-001 false-positive shape arose"
            )
    else:
        color = BRICK_UNKNOWN
        headline = (
            "filter has not yet seen an audit with registered references in"
            " window"
        )

    drill_down: List[Dict[str, Any]] = []
    for rec in audit_disposition_records or []:
        sf = rec.get("suppressed_findings") or []
        if not sf:
            continue
        drill_down.append({
            "audit_path": rec.get("audit_path"),
            "iteration": rec.get("iteration"),
            "workstream": rec.get("workstream"),
            "audit_kind": rec.get("audit_kind"),
            "suppressed_findings": sf,
        })

    return SurfaceState(
        surface_id="deterministic_post_hoc_filter",
        description=SURFACE_DESCRIPTIONS["deterministic_post_hoc_filter"],
        color=color,
        headline=headline,
        detail={
            "filter_eligible_count": eligible,
            "filter_suppressed_count": suppressed,
            "filter_error_count": errors,
        },
        drill_down=drill_down,
    )


def evaluate_all_surfaces(
    state: Dict[str, Any],
    *,
    audit_disposition_records: Optional[List[Dict[str, Any]]] = None,
) -> List[SurfaceState]:
    """Evaluate all four hardening surfaces."""
    return [
        _nemotron_surface(state),
        _llama_floor_surface(state),
        _role_collapse_surface(state),
        _filter_surface(state, audit_disposition_records=audit_disposition_records),
    ]


def evaluate_overview(surfaces: List[SurfaceState]) -> SurfaceState:
    """Aggregate four surfaces into a single overview state. Green if no
    surface reds; red if any surface reds. Unknown only if every surface
    is unknown."""
    reds = [s for s in surfaces if s.color == BRICK_RED]
    greens = [s for s in surfaces if s.color == BRICK_GREEN]
    if reds:
        color = BRICK_RED
        headline = f"{len(reds)} of 4 hardening surfaces firing red"
    elif greens:
        color = BRICK_GREEN
        headline = (
            f"{len(greens)} of 4 hardening surfaces green; remaining"
            " surfaces have no signal in window"
        )
    else:
        color = BRICK_UNKNOWN
        headline = "no hardening signal in window"
    return SurfaceState(
        surface_id="anti_rubber_stamp_overview",
        description=(
            "At-a-glance state of all four anti-rubber-stamp hardening"
            " surfaces. Red if any of the four reds; green if at least"
            " one is green and none red; unknown if no signal."
        ),
        color=color,
        headline=headline,
        detail={
            "red_count": len(reds),
            "green_count": len(greens),
            "unknown_count": sum(1 for s in surfaces if s.color == BRICK_UNKNOWN),
            "total": len(surfaces),
        },
    )


def render_dashboard(
    state: Dict[str, Any],
    *,
    audit_disposition_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Render the full D6 anti-rubber-stamp dashboard payload — four
    surfaces + overview, in JSON form."""
    surfaces = evaluate_all_surfaces(
        state, audit_disposition_records=audit_disposition_records
    )
    overview = evaluate_overview(surfaces)
    return {
        "kind": "anti_rubber_stamp_verification_dashboard",
        "schema_version": 1,
        "overview": {
            "color": overview.color,
            "headline": overview.headline,
            "detail": overview.detail,
        },
        "surfaces": [
            {
                "surface_id": s.surface_id,
                "description": s.description,
                "color": s.color,
                "headline": s.headline,
                "detail": s.detail,
                "drill_down": s.drill_down,
            }
            for s in surfaces
        ],
    }


__all__ = [
    "SURFACE_DESCRIPTIONS",
    "SURFACE_IDS",
    "SurfaceState",
    "evaluate_all_surfaces",
    "evaluate_overview",
    "render_dashboard",
]
