"""D8 — Anti-rubber-stamp hardening tests.

Three explicit failure-mode tests + three mutation tests that verify the
hardening is what catches each failure mode (not some other code path).

Failure modes covered:
1. Nemotron triage out-of-rubric output → CouncilTriageMalformedError
   (NOT a categories[-1] fallback to a "best-guess" category)
2. Llama audit clean-disposition + low-confidence → confidence-floor lock
   forces disposition to surface_to_drafter
3. Council dispatch drafter+auditor same-model-family → CouncilRoleCollapseError

Each mutation test removes / weakens the hardening and confirms the
underlying test would have passed in error — i.e. the hardening is
load-bearing.
"""
from __future__ import annotations

import json
from typing import Any, Dict
from unittest.mock import patch

import pytest

from aho.council import audit as audit_mod
from aho.council import dispatch as dispatch_mod
from aho.council import triage as triage_mod


# ---------------------------------------------------------------------------
# Helpers — mock the council._client.chat surface so we control model output
# ---------------------------------------------------------------------------

def _mock_chat_payload(content: str) -> Dict[str, Any]:
    return {"message": {"role": "assistant", "content": content}}


# ---------------------------------------------------------------------------
# Failure mode 1 — nemotron out-of-rubric must raise
# ---------------------------------------------------------------------------

def test_nemotron_raises_on_out_of_rubric_category():
    """Triage classify must raise when the model returns a category outside
    the rubric. NO categories[-1] fallback (G083 silent rubber-stamp).
    """
    bad_output = json.dumps({
        "category": "this-category-does-not-exist-in-rubric",
        "confidence": 0.99,
        "rationale_summary": "model invented a fifth category",
    })
    with patch.object(triage_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        with pytest.raises(triage_mod.CouncilTriageMalformedError) as exc:
            triage_mod.classify("any input artifact text")
    assert "not in rubric" in str(exc.value)
    assert "categories[-1]" in str(exc.value)


def test_nemotron_raises_on_garbled_json():
    bad_output = "not json at all { unbalanced"
    with patch.object(triage_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        with pytest.raises(triage_mod.CouncilTriageMalformedError):
            triage_mod.classify("artifact text")


def test_mutation_nemotron_hardening_is_load_bearing(monkeypatch):
    """Mutation: if the rubric were widened to accept any string, the
    test_nemotron_raises_on_out_of_rubric_category test would PASS the
    bad output (wrongly returning a non-rubric category). Verify the
    hardening — strict rubric — is what catches the failure mode.
    """
    bad_output = json.dumps({
        "category": "wild-category-not-in-rubric",
        "confidence": 0.99,
        "rationale_summary": "x",
    })

    # Bypass rubric check by stubbing _validate_classify_payload with a
    # permissive variant. This simulates what would happen if the
    # categories[-1]-style fallback existed.
    def permissive(payload):
        return {
            "category": payload.get("category", "unknown"),
            "confidence": float(payload.get("confidence", 0.0)),
            "rationale_summary": payload.get("rationale_summary", ""),
        }

    monkeypatch.setattr(triage_mod, "_validate_classify_payload", permissive)
    with patch.object(triage_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        # WITHOUT the hardening, the bad category passes through:
        result = triage_mod.classify("artifact text")
    assert result["category"] == "wild-category-not-in-rubric", (
        "mutation failed to bypass hardening — test isn't measuring what it claims"
    )


# ---------------------------------------------------------------------------
# Failure mode 2 — llama clean+low_confidence must lock to surface_to_drafter
# ---------------------------------------------------------------------------

def test_llama_confidence_floor_locks_clean_at_low_confidence():
    """Audit must rewrite disposition=clean to surface_to_drafter when
    confidence < floor. The clean disposition is structurally unreachable
    below the floor.
    """
    bad_output = json.dumps({
        "disposition": "clean",
        "confidence": 0.6,
        "findings": [],
        "evidence_traces": ["spot-check phrase from artifact"],
    })
    with patch.object(audit_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        result = audit_mod.audit("a clean-looking artifact with no defects")
    assert result["disposition"] == "surface_to_drafter", (
        f"floor lock failed; disposition stayed {result['disposition']!r} "
        f"at confidence {result['confidence']}"
    )
    assert result["confidence_floor_locked"] is True
    assert result["confidence_floor"] == 0.85


def test_llama_high_confidence_clean_passes_through():
    good_output = json.dumps({
        "disposition": "clean",
        "confidence": 0.95,
        "findings": [],
        "evidence_traces": ["phrase from artifact"],
    })
    with patch.object(audit_mod, "chat", return_value=_mock_chat_payload(good_output)):
        result = audit_mod.audit("a clean-looking artifact with no defects")
    assert result["disposition"] == "clean"
    assert result["confidence_floor_locked"] is False


def test_mutation_confidence_floor_is_load_bearing(monkeypatch):
    """Mutation: if the floor were 0.0, low-confidence clean would
    rubber-stamp through. Verify the floor logic is the load-bearing piece.
    """
    bad_output = json.dumps({
        "disposition": "clean",
        "confidence": 0.6,
        "findings": [],
        "evidence_traces": ["x"],
    })
    monkeypatch.setattr(audit_mod, "_confidence_floor", lambda: 0.0)
    with patch.object(audit_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        result = audit_mod.audit("a clean-looking artifact with no defects")
    # WITHOUT the floor, the disposition stays clean:
    assert result["disposition"] == "clean", (
        "mutation failed — floor logic wasn't actually bypassed"
    )
    assert result["confidence_floor_locked"] is False


def test_enforce_confidence_floor_unit_table():
    """Direct unit table for the post-validation floor enforcer."""
    cases = [
        ("clean", 0.95, "clean", False),
        ("clean", 0.85, "clean", False),
        ("clean", 0.84999, "surface_to_drafter", True),
        ("clean", 0.0, "surface_to_drafter", True),
        ("halt", 0.5, "halt", False),
        ("surface_to_drafter", 0.0, "surface_to_drafter", False),
    ]
    for disp_in, conf, disp_expected, lock_expected in cases:
        out = audit_mod.enforce_confidence_floor(disp_in, conf)
        assert out["disposition"] == disp_expected, (
            f"enforce({disp_in},{conf}) → {out['disposition']!r}, "
            f"expected {disp_expected!r}"
        )
        assert out["confidence_floor_locked"] is lock_expected


# ---------------------------------------------------------------------------
# Failure mode 3 — drafter+auditor same family must raise
# ---------------------------------------------------------------------------

def test_dispatch_role_collapse_drafter_auditor_same_family():
    """Role-collapse trip-wire fires when drafter and auditor would land on
    the same model family in a single iteration's dispatch session.
    """
    d = dispatch_mod.CouncilDispatch(iteration="role-collapse-test", tier="base")
    d.record_role_family("drafter", "llama")
    with pytest.raises(dispatch_mod.CouncilRoleCollapseError) as exc:
        d.record_role_family("auditor", "llama")
    assert "role-collapse" in str(exc.value)
    assert "auditor" in str(exc.value)


def test_dispatch_role_collapse_auditor_first_then_drafter():
    """Order doesn't matter — auditor first, then drafter same family also raises."""
    d = dispatch_mod.CouncilDispatch(iteration="role-collapse-test-2", tier="base")
    d.record_role_family("auditor", "qwen")
    with pytest.raises(dispatch_mod.CouncilRoleCollapseError):
        d.record_role_family("drafter", "qwen")


def test_dispatch_non_collapse_roles_share_family_freely():
    """Non-(drafter|auditor) role pairs may share family without trip-wire."""
    d = dispatch_mod.CouncilDispatch(iteration="non-collapse-test", tier="base")
    d.record_role_family("triage", "nemotron")
    d.record_role_family("retrieval", "nemotron")  # not a collapse pair
    snapshot = d.role_family_snapshot()
    assert snapshot["triage"] == "nemotron"
    assert snapshot["retrieval"] == "nemotron"


def test_mutation_role_collapse_is_load_bearing(monkeypatch):
    """Mutation: if _COLLAPSE_ROLES were empty, the trip-wire would never
    fire. Verify the role-pair check is the load-bearing piece.
    """
    monkeypatch.setattr(dispatch_mod, "_COLLAPSE_ROLES", set())
    d = dispatch_mod.CouncilDispatch(iteration="mut-test", tier="base")
    d.record_role_family("drafter", "llama")
    # WITHOUT the collapse rule, auditor on llama is silently accepted:
    d.record_role_family("auditor", "llama")
    snapshot = d.role_family_snapshot()
    assert snapshot["drafter"] == "llama"
    assert snapshot["auditor"] == "llama"


# ---------------------------------------------------------------------------
# Substantive drafting → escalate (related G083 surface)
# ---------------------------------------------------------------------------

def test_dispatch_substantive_drafting_at_base_escalates():
    d = dispatch_mod.CouncilDispatch(iteration="escalate-test", tier="base")
    with pytest.raises(dispatch_mod.CouncilDispatchEscalateRequired) as exc:
        d.dispatch("substantive_drafting", "drafter", "anything")
    assert exc.value.target == "partial_tier_or_external_drafter"


def test_dispatch_unknown_route_raises():
    d = dispatch_mod.CouncilDispatch(iteration="unknown-route-test", tier="base")
    with pytest.raises(dispatch_mod.CouncilDispatchUnknownRouteError):
        d.dispatch("mystery_shape", "phantom", None)
