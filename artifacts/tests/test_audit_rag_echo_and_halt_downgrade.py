"""0.2.18 W0 - RAG-status-echo filter + unsupported-halt-downgrade.

Two structural fixes lock-in:

A. F-0.2.18-W0-006 - RAG enrichment status echo. The model paraphrased
   the registered-references context section as findings whose
   description was the literal template `{ID} ({kind}) - status:
   `registered|unverified``. Filter extension drops these with reason
   `rag_enrichment_status_echo`. Tight whole-description anchor; any
   substantive content beyond the template keeps the finding active.

B. F-0.2.18-W0-007 - unsupported-halt downgrade. When the model returns
   `halt` but every model finding is filter-suppressed and no
   deterministic pre-check fired, the halt is materially unsupported.
   Downgrade to `surface_to_drafter` (never `clean` - preserves the
   human-review backstop). Any active finding (model or pre-check)
   keeps the halt.
"""
from __future__ import annotations

from unittest.mock import patch

from aho.council.audit_finding_filter import (
    RAG_STATUS_ECHO_REASON,
    SUPPRESSION_REASON,
    filter_findings,
)


# ---------------------------------------------------------------------------
# Gap A - RAG enrichment status echo suppression
# ---------------------------------------------------------------------------

def _rag_with_registered(*ids: str) -> dict:
    return {
        "references": [
            {"id": i, "status": "registered"} for i in ids
        ],
    }


def _rag_empty() -> dict:
    return {"references": []}


def test_rag_echo_registered_suppressed():
    findings = [{
        "id": "F-0.2.17-W6-003",
        "severity": "info",
        "description": "F-0.2.17-W6-003 (carry_forward_full) - status: `registered`",
    }]
    out = filter_findings(findings, _rag_with_registered("F-0.2.17-W6-003"))
    assert out["active_findings"] == []
    assert len(out["suppressed_findings"]) == 1
    assert out["suppressed_findings"][0]["reason"] == RAG_STATUS_ECHO_REASON


def test_rag_echo_unverified_suppressed_even_without_registered_set():
    """Echo rule fires regardless of registered-set membership - it's a
    description-shape rule, not a registered-anchor rule."""
    findings = [{
        "id": "G070",
        "severity": "critical",
        "description": "G070 (gotcha) - status: `unverified`",
    }]
    out = filter_findings(findings, _rag_empty())
    assert out["active_findings"] == []
    assert len(out["suppressed_findings"]) == 1
    assert out["suppressed_findings"][0]["reason"] == RAG_STATUS_ECHO_REASON


def test_rag_echo_with_trailing_period_suppressed():
    findings = [{
        "id": "ADR-0007",
        "severity": "info",
        "description": "ADR-0007 (adr) - status: `registered`.",
    }]
    out = filter_findings(findings, _rag_with_registered("ADR-0007"))
    assert out["active_findings"] == []


def test_rag_echo_with_substantive_content_kept():
    """Any sentence beyond the template defeats the anchor - keep active."""
    findings = [{
        "id": "F-0.2.17-W6-003",
        "severity": "info",
        "description": (
            "F-0.2.17-W6-003 (carry_forward_full) - status: `registered`. "
            "However, the closure notes claim a test was amended but no test existed."
        ),
    }]
    out = filter_findings(findings, _rag_with_registered("F-0.2.17-W6-003"))
    assert len(out["active_findings"]) == 1
    assert out["suppressed_findings"] == []


def test_rag_echo_em_dash_variant_suppressed():
    findings = [{
        "id": "G071",
        "severity": "info",
        "description": "G071 (gotcha) - status: `unverified`",
    }]
    out = filter_findings(findings, _rag_empty())
    assert out["active_findings"] == []


def test_rag_echo_hyphen_variant_suppressed():
    """Plain ASCII hyphen also matches (model output varies)."""
    findings = [{
        "id": "G071",
        "severity": "info",
        "description": "G071 (gotcha) - status: `unverified`",
    }]
    out = filter_findings(findings, _rag_empty())
    assert out["active_findings"] == []


def test_rag_echo_does_not_suppress_real_finding():
    """A finding with substance and an anchor stays active."""
    findings = [{
        "id": "F-0.2.17-W6-003",
        "severity": "important",
        "description": (
            "F-0.2.17-W6-003 closure says gitignore drift fully resolved, "
            "but `.aho.json` and `MANIFEST.json` are still tracked."
        ),
    }]
    out = filter_findings(findings, _rag_with_registered("F-0.2.17-W6-003"))
    assert len(out["active_findings"]) == 1
    assert out["suppressed_findings"] == []


def test_existing_fake_id_rule_still_fires():
    """The F-0.2.17-W3-001 rule must keep working alongside the new one."""
    findings = [{
        "id": "AF-1",
        "severity": "important",
        "description": (
            "ADR-0007 looks like a placeholder and not corroborated."
        ),
    }]
    out = filter_findings(findings, _rag_with_registered("ADR-0007"))
    assert out["active_findings"] == []
    assert out["suppressed_findings"][0]["reason"] == SUPPRESSION_REASON


def test_two_echo_findings_both_suppressed():
    """The literal 0.2.18 W0 v2 audit shape: 2 echoes, both should drop."""
    findings = [
        {
            "id": "G070",
            "severity": "critical",
            "description": "G070 (gotcha) - status: `unverified`",
        },
        {
            "id": "F-0.2.17-W6-003",
            "severity": "info",
            "description": "F-0.2.17-W6-003 (carry_forward_full) - status: `registered`",
        },
    ]
    out = filter_findings(findings, _rag_with_registered("F-0.2.17-W6-003"))
    assert out["active_findings"] == []
    assert len(out["suppressed_findings"]) == 2
    assert all(s["reason"] == RAG_STATUS_ECHO_REASON for s in out["suppressed_findings"])


# ---------------------------------------------------------------------------
# Gap B - unsupported-halt downgrade (audit.py orchestration rule)
# ---------------------------------------------------------------------------

def _audit_with_mocked_model(
    *,
    model_disposition: str,
    model_confidence: float,
    model_findings: list,
    artifact_text: str = "Some innocuous artifact text without git ops or banned phrases.",
):
    """Helper: invoke audit() with a stubbed Ollama call returning the
    given model output, so we can exercise the orchestration rules
    without hitting the real model.
    """
    from aho.council import audit as audit_mod
    import json

    response = {
        "disposition": model_disposition,
        "confidence": model_confidence,
        "findings": model_findings,
        "evidence_traces": ["some phrase from the artifact"],
    }

    fake_chat = {
        "message": {
            "role": "assistant",
            "content": json.dumps(response),
        }
    }

    with patch.object(audit_mod, "chat", return_value=fake_chat), \
         patch.object(audit_mod, "_build_enrichment", return_value={
             "section_text": "",
             "detected_count": 0,
             "registered_count": 0,
             "unverified_count": 0,
             "truncated": False,
             "results": [],
         }):
        return audit_mod.audit(artifact_text, rag_enrichment=False)


def test_halt_with_only_echo_findings_downgrades_to_surface_to_drafter():
    out = _audit_with_mocked_model(
        model_disposition="halt",
        model_confidence=0.9,
        model_findings=[
            {"id": "G070", "severity": "info",
             "description": "G070 (gotcha) - status: `unverified`"},
        ],
    )
    assert out["disposition"] == "surface_to_drafter"
    assert out["unsupported_halt_downgrade"] is True


def test_halt_with_substantive_finding_keeps_halt():
    out = _audit_with_mocked_model(
        model_disposition="halt",
        model_confidence=0.9,
        model_findings=[
            {"id": "AF-1", "severity": "critical",
             "description": "Deliverable D7 claimed pass but no SHA recorded."},
        ],
    )
    assert out["disposition"] == "halt"
    assert out["unsupported_halt_downgrade"] is False


def test_halt_with_no_model_findings_at_all_downgrades():
    out = _audit_with_mocked_model(
        model_disposition="halt",
        model_confidence=0.9,
        model_findings=[],
    )
    assert out["disposition"] == "surface_to_drafter"
    assert out["unsupported_halt_downgrade"] is True


def test_halt_with_pre_check_fail_keeps_halt():
    """Banned phrase in artifact triggers pre-check `extra_findings`; halt
    must not downgrade."""
    out = _audit_with_mocked_model(
        model_disposition="halt",
        model_confidence=0.9,
        model_findings=[
            {"id": "G070", "severity": "info",
             "description": "G070 (gotcha) - status: `unverified`"},
        ],
        artifact_text="Workstream landed beautifully - all tests pass.",
    )
    # G081 banned phrase → AUDIT-G081 extra_finding → halt preserved
    assert out["disposition"] == "halt"
    assert out["unsupported_halt_downgrade"] is False


def test_clean_disposition_unaffected_by_downgrade_rule():
    out = _audit_with_mocked_model(
        model_disposition="clean",
        model_confidence=0.95,
        model_findings=[],
    )
    assert out["disposition"] == "clean"
    assert out["unsupported_halt_downgrade"] is False


def test_surface_to_drafter_with_only_echoes_stays_surface_to_drafter():
    """Downgrade rule is halt-specific - surface_to_drafter is already
    the human-review disposition; no further demotion."""
    out = _audit_with_mocked_model(
        model_disposition="surface_to_drafter",
        model_confidence=0.9,
        model_findings=[
            {"id": "G070", "severity": "info",
             "description": "G070 (gotcha) - status: `unverified`"},
        ],
    )
    assert out["disposition"] == "surface_to_drafter"
    assert out["unsupported_halt_downgrade"] is False
