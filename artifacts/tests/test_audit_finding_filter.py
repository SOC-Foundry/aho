"""W4 D1 — deterministic post-hoc filter on RAG-aware audit findings.

Acceptance gates from the W4 plan doc:

1. Suppresses the F-0.2.17-W1-003 fake-ID finding from the W2 self-audit-rag
   sealed artifact (registered anchor + fake-ID phrase).
2. Does NOT over-suppress the W3 self-audit (sealed) — three findings
   present, none have a fake-ID phrase, all stay active.
3. Synthetic positive: registered anchor + fake-ID phrase → suppress with
   the right structured record.
4. Synthetic negative: unverified anchor + fake-ID phrase → NO suppression
   (auditor's flag stays active because flagging an unverified ID is
   legitimate).

Plus integration tests against the audit primitive's contract:
- filter runs between model parse and disposition return
- structural pre-check findings (AUDIT-G081, AUDIT-PILLAR11) bypass the
  filter
- model_findings_count / active_findings_count / suppressed_count fields
  surface in the return dict
- OTEL span tags carry filter activity
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from aho.council import audit as audit_mod
from aho.council.audit_finding_filter import (
    FAKE_ID_PHRASES,
    SUPPRESSION_REASON,
    AuditFindingFilterError,
    filter_findings,
)


# Repository-anchored paths to the sealed artifacts D1 acceptance gates
# read against. Paths are relative to the repo root; the test resolves
# parent directories until it finds the artifacts/ tree.
def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "artifacts" / "iterations" / "0.2.17").is_dir():
            return parent
    raise RuntimeError("could not locate aho repo root from test file")


W2_SELF_AUDIT_RAG_PATH = (
    _repo_root()
    / "artifacts/iterations/0.2.17/audit/replay/W2-self-audit-rag.json"
)
W3_SELF_AUDIT_PATH = (
    _repo_root() / "artifacts/iterations/0.2.17/audit/W3.json"
)


# ---------------------------------------------------------------------------
# Acceptance gate 1 — W2 self-audit-rag fake-ID finding suppresses
# ---------------------------------------------------------------------------

def test_filter_suppresses_w2_self_audit_rag_fake_id_finding():
    """Run the filter against the sealed W2 self-audit-rag artifact. The
    single G081 finding ('F-0.2.17-W1-003 does not look real') must
    suppress because:
      - F-0.2.17-W1-003 appears as `registered` in rag_enrichment.references
      - The description contains 'does not look real' and 'matches naming
        conventions' — both fake-ID phrases.
    """
    payload = json.loads(W2_SELF_AUDIT_RAG_PATH.read_text())
    findings = payload["findings"]
    rag_enrichment = payload["rag_enrichment"]

    assert len(findings) == 1, (
        "W2 self-audit-rag fixture expected to contain exactly the one "
        "false-positive finding the filter targets"
    )

    out = filter_findings(findings, rag_enrichment)

    assert out["filter_eligible"] is True
    assert out["registered_id_count"] >= 1
    assert len(out["active_findings"]) == 0
    assert len(out["suppressed_findings"]) == 1

    suppressed = out["suppressed_findings"][0]
    assert suppressed["reason"] == SUPPRESSION_REASON
    assert suppressed["matched_registered_anchor"] == "F-0.2.17-W1-003"
    assert suppressed["matched_phrase"] in FAKE_ID_PHRASES
    assert suppressed["finding"]["id"] == "G081"


# ---------------------------------------------------------------------------
# Acceptance gate 2 — W3 self-audit findings are NOT over-suppressed
# ---------------------------------------------------------------------------

def test_filter_does_not_oversuppress_w3_self_audit():
    """Run the filter against the sealed W3 self-audit. The three findings
    are:
      - F-0.2.17-W3-001 'inconsistently honors the registered-references
        prompt rule'  → no fake-ID phrase, stays active
      - G081 'No celebratory framing in G081' → no fake-ID phrase
      - AUDIT-PILLAR11 'Possible Pillar 11 reference (agent-side git op)'
        → no fake-ID phrase

    Active count must remain 3, suppressed count must be 0. Filter
    structural narrowness verified.
    """
    payload = json.loads(W3_SELF_AUDIT_PATH.read_text())
    findings = payload["findings"]
    rag_enrichment = payload.get("rag_enrichment", {})

    assert len(findings) == 3
    out = filter_findings(findings, rag_enrichment)

    assert len(out["active_findings"]) == 3
    assert len(out["suppressed_findings"]) == 0


# ---------------------------------------------------------------------------
# Acceptance gate 3 — synthetic positive (registered + fake-ID phrase)
# ---------------------------------------------------------------------------

def test_filter_suppresses_synthetic_registered_plus_fake_phrase():
    """Inject {id: F-FAKE-1, description: 'F-0.2.17-W1-003 looks like a
    placeholder ID'} against an audit context where F-0.2.17-W1-003 is
    `registered`. Filter must suppress with reason=registered_id_flagged_as_fake."""
    finding = {
        "id": "F-FAKE-1",
        "severity": "important",
        "description": "F-0.2.17-W1-003 looks like a placeholder ID",
    }
    rag_enrichment = {
        "enabled": True,
        "references": [
            {
                "id": "F-0.2.17-W1-003",
                "kind": "carry_forward_full",
                "status": "registered",
            }
        ],
    }
    out = filter_findings([finding], rag_enrichment)

    assert len(out["active_findings"]) == 0
    assert len(out["suppressed_findings"]) == 1
    suppressed = out["suppressed_findings"][0]
    assert suppressed["reason"] == SUPPRESSION_REASON
    assert suppressed["matched_registered_anchor"] == "F-0.2.17-W1-003"
    # 'looks like a placeholder' is one of the canonical phrases.
    assert suppressed["matched_phrase"] == "looks like a placeholder"


# ---------------------------------------------------------------------------
# Acceptance gate 4 — synthetic negative (unverified + fake-ID phrase)
# ---------------------------------------------------------------------------

def test_filter_does_not_suppress_unverified_anchor_with_fake_phrase():
    """Inject {id: AF-1, description: 'F-0.2.17-W9-999 cannot be
    corroborated'} against context where F-0.2.17-W9-999 is NOT in
    registered-references. Filter must NOT suppress — auditor's flag of an
    unverified ID is legitimate."""
    finding = {
        "id": "AF-1",
        "severity": "important",
        "description": "F-0.2.17-W9-999 cannot be corroborated",
    }
    rag_enrichment = {
        "enabled": True,
        "references": [
            {
                "id": "F-0.2.17-W9-999",
                "kind": "carry_forward_full",
                "status": "unverified",
            }
        ],
    }
    out = filter_findings([finding], rag_enrichment)

    assert len(out["active_findings"]) == 1
    assert len(out["suppressed_findings"]) == 0


# ---------------------------------------------------------------------------
# Structural narrowness mutation tests
# ---------------------------------------------------------------------------

def test_filter_keeps_finding_when_phrase_matches_but_no_anchor_in_description():
    """Fake-ID phrase present but description has no anchor token at all.
    Must NOT suppress — there's no registered anchor being flagged."""
    finding = {
        "id": "AF-1",
        "severity": "info",
        "description": "Some claim does not look real to me",
    }
    rag_enrichment = {
        "enabled": True,
        "references": [
            {"id": "F-0.2.17-W1-003", "kind": "carry_forward_full", "status": "registered"}
        ],
    }
    out = filter_findings([finding], rag_enrichment)
    assert len(out["active_findings"]) == 1
    assert len(out["suppressed_findings"]) == 0


def test_filter_keeps_finding_when_anchor_registered_but_no_fake_phrase():
    """Registered anchor present in description but no fake-ID phrase.
    Must NOT suppress — the auditor is flagging something else about a
    known ID, which is legitimate."""
    finding = {
        "id": "G081",
        "severity": "important",
        "description": "F-0.2.17-W1-003 incident response timing exceeded the SLA",
    }
    rag_enrichment = {
        "enabled": True,
        "references": [
            {"id": "F-0.2.17-W1-003", "kind": "carry_forward_full", "status": "registered"}
        ],
    }
    out = filter_findings([finding], rag_enrichment)
    assert len(out["active_findings"]) == 1
    assert len(out["suppressed_findings"]) == 0


def test_filter_handles_disabled_rag_enrichment():
    """rag_enrichment=None / disabled → filter is a no-op."""
    finding = {
        "id": "F-FAKE-1",
        "severity": "important",
        "description": "F-0.2.17-W1-003 looks like a placeholder ID",
    }
    out = filter_findings([finding], None)
    assert out["filter_eligible"] is False
    assert len(out["active_findings"]) == 1
    assert len(out["suppressed_findings"]) == 0


def test_filter_handles_empty_findings_list():
    out = filter_findings([], {"references": []})
    assert out["active_findings"] == []
    assert out["suppressed_findings"] == []


def test_filter_raises_on_non_dict_finding():
    with pytest.raises(AuditFindingFilterError):
        filter_findings(["not a dict"], {"references": []})


# ---------------------------------------------------------------------------
# Integration with aho.council.audit
# ---------------------------------------------------------------------------

def _mock_chat_payload(content: str) -> Dict[str, Any]:
    return {"message": {"role": "assistant", "content": content}}


def _mock_enrichment(monkeypatch, registered_ids: List[str]):
    """Stub _build_enrichment so tests don't hit ChromaDB."""
    def fake_build(artifact, *, max_refs=30, project=None):
        return {
            "section_text": "## Registered references retrieved from project context\n",
            "detected_count": len(registered_ids),
            "registered_count": len(registered_ids),
            "unverified_count": 0,
            "truncated": False,
            "results": [
                {
                    "id": ident,
                    "kind": "carry_forward_full",
                    "status": "registered",
                    "retrievals": [
                        {
                            "source_artifact_path": "/fake/path.md",
                            "snippet": "test snippet",
                        }
                    ],
                }
                for ident in registered_ids
            ],
        }

    monkeypatch.setattr(audit_mod, "_build_enrichment", fake_build)


def test_audit_integration_suppresses_fake_id_finding(monkeypatch):
    """End-to-end: model emits the W2-shaped fake-ID finding, audit
    primitive returns it suppressed with active_findings==0 and
    suppressed_findings populated."""
    _mock_enrichment(monkeypatch, ["F-0.2.17-W1-003"])
    bad_output = json.dumps({
        "disposition": "halt",
        "confidence": 0.95,
        "findings": [{
            "id": "G081",
            "severity": "critical",
            "description": (
                "The artifact references F-0.2.17-W1-003 but the ID does "
                "not look real (matches naming conventions)"
            ),
        }],
        "evidence_traces": ["F-0.2.17-W1-003"],
    })
    with patch.object(audit_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        result = audit_mod.audit("an artifact mentioning F-0.2.17-W1-003 in passing")

    assert result["finding_filter"]["filter_eligible"] is True
    assert result["finding_filter"]["model_findings_count"] == 1
    assert result["finding_filter"]["active_findings_count"] == 0
    assert result["finding_filter"]["suppressed_count"] == 1
    assert len(result["suppressed_findings"]) == 1
    assert result["suppressed_findings"][0]["reason"] == SUPPRESSION_REASON
    # Per F-0.2.18-W0-007 unsupported-halt downgrade: model said halt with
    # exactly one finding, that finding was filter-suppressed, and no
    # pre-check fired → halt is materially unsupported → downgrade to
    # surface_to_drafter (preserves human-review backstop, never auto-clean).
    assert result["disposition"] == "surface_to_drafter"
    assert result["unsupported_halt_downgrade"] is True
    # No model findings in final list, but pre-check findings (none here)
    # would still flow through.
    assert result["findings"] == []


def test_audit_integration_filter_bypasses_structural_pre_checks(monkeypatch):
    """Structural pre-check findings (AUDIT-G081, AUDIT-PILLAR11) are
    regex-grounded and must NOT be filtered. Verify they flow through
    even if the model also produces a fake-ID-shaped finding."""
    _mock_enrichment(monkeypatch, ["F-0.2.17-W1-003"])
    bad_output = json.dumps({
        "disposition": "halt",
        "confidence": 0.95,
        "findings": [{
            "id": "G081",
            "severity": "critical",
            "description": (
                "F-0.2.17-W1-003 does not look real (matches naming conventions)"
            ),
        }],
        "evidence_traces": ["F-0.2.17-W1-003"],
    })
    artifact_with_pillar11 = (
        "executor session log mentions git commit and F-0.2.17-W1-003 in "
        "context of post-incident review"
    )
    with patch.object(audit_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        result = audit_mod.audit(artifact_with_pillar11)

    assert result["finding_filter"]["suppressed_count"] == 1
    # AUDIT-PILLAR11 from structural pre-check (regex-grounded) is NOT
    # filtered — it flows through.
    pillar11_ids = [f["id"] for f in result["findings"]]
    assert "AUDIT-PILLAR11" in pillar11_ids


def test_audit_integration_filter_no_op_when_no_registered_ids(monkeypatch):
    """When no registered references are detected (filter_eligible=False),
    every model finding flows through unchanged."""
    _mock_enrichment(monkeypatch, [])
    bad_output = json.dumps({
        "disposition": "halt",
        "confidence": 0.95,
        "findings": [{
            "id": "F-FAKE-1",
            "severity": "info",
            "description": "F-0.2.17-W9-999 looks like a placeholder",
        }],
        "evidence_traces": ["F-0.2.17-W9-999"],
    })
    with patch.object(audit_mod, "chat", return_value=_mock_chat_payload(bad_output)):
        result = audit_mod.audit("artifact with unverified F-0.2.17-W9-999 reference")

    assert result["finding_filter"]["filter_eligible"] is False
    assert result["finding_filter"]["suppressed_count"] == 0
    assert len(result["findings"]) == 1
