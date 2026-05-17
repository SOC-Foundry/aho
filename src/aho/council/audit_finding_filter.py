"""council.audit_finding_filter — deterministic post-hoc filter on RAG-aware
audit findings (W4 D1, drafter-arbitrated path c from F-0.2.17-W3-001).

Closes the small-model prompt-following inconsistency surfaced by W3 D4: with
the registered-references context section in place, llama3.2:3b sometimes
still ignored the rule and flagged registered IDs with fake-ID-shaped
descriptions. The filter is the structural fix.

After the model returns its findings list, this filter:
1. Extracts anchor-shaped reference tokens from each finding's description
   via the same `audit_ref_extract` regex set used to build the RAG
   enrichment section.
2. Checks if any extracted anchor appears in the audit's
   ``rag_enrichment.references`` list with status ``"registered"``.
3. Checks if the finding's description contains a fake-ID phrase
   (substring match, case-insensitive). The phrase set is intentionally
   small and explicit — exactly the shapes that surfaced as false
   positives during W2 self-audit and W3 D4 RAG replays.
4. If BOTH conditions are met, the finding is dropped from the active
   list and recorded in a structured ``suppressed_findings`` entry with
   the reason ``"registered_id_flagged_as_fake"``, the matched phrase,
   and the matched registered anchor. Auditable, falsifiable, and
   inspectable downstream.

Structural narrowness is the load-bearing G083 protection. Findings with
a fake-ID phrase but no registered anchor stay active (the auditor is
flagging an unverified ID — legitimate). Findings with a registered
anchor but no fake-ID phrase stay active (the auditor is flagging
something else about a known ID — legitimate). The filter only
suppresses the specific F-0.2.17-W3-001 failure mode.

0.2.18 W0 extension — RAG enrichment status echo (F-0.2.18-W0-006).
A second false-positive shape: llama3.2:3b sometimes paraphrases the
"## Registered references retrieved from project context" table into
findings whose description is the literal status-line template
``{ID} ({kind}) — status: `registered|unverified`.`` with no
substantive content. These are non-findings — the auditor is just
echoing the ground-truth context section back. The
``_RAG_STATUS_ECHO_PATTERN`` matches that exact shape and the filter
drops matched findings with reason ``"rag_enrichment_status_echo"``.
The match is anchored on the entire description (with optional
trailing punctuation), so any added substantive sentence keeps the
finding active.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .audit_ref_extract import RefExtractError, detect_references


# Phrase set is the canonical W4 plan-doc D1 list. Case-insensitive
# substring match — "whole-phrase" in plan-doc parlance is the entire
# phrase as a contiguous token sequence inside the description.
#
# Adding to this list expands suppression coverage. Do NOT add open-ended
# phrases ("suspicious", "weird") — those would erode the structural
# narrowness G083 hardening relies on.
FAKE_ID_PHRASES: Tuple[str, ...] = (
    "not real",
    "does not look real",
    "looks placeholder",
    "looks like a placeholder",
    "matches naming conventions",
    "not corroborated",
    "cannot be corroborated",
    "appears fictitious",
    "appears fabricated",
)


SUPPRESSION_REASON = "registered_id_flagged_as_fake"
RAG_STATUS_ECHO_REASON = "rag_enrichment_status_echo"

# 0.2.18 W0 (F-0.2.18-W0-006). Tight-anchored template: the description
# must consist *entirely* of the status-line template, optionally with
# leading/trailing whitespace and an optional trailing period. Any added
# substantive content (a sentence after the status line) prevents the
# match and keeps the finding active. Reference-ID alphabet covers all
# shapes used by detect_references (ADRs, gotchas, carry-forwards,
# deliverables, workstream IDs).
_RAG_STATUS_ECHO_PATTERN = re.compile(
    r"^\s*"
    r"[A-Za-z][A-Za-z0-9._-]*"          # anchor ID
    r"\s*\(\s*[a-z][a-z_]*\s*\)\s*"     # (kind)
    r"[—–\-]\s*"              # em-dash, en-dash, or hyphen
    r"status\s*:\s*"
    r"[`'\"]?(?:registered|unverified)[`'\"]?"
    r"\s*\.?\s*$",
    re.IGNORECASE,
)


class AuditFindingFilterError(ValueError):
    """Caller passed an unusable findings list or rag_enrichment payload."""


def _registered_id_set(rag_enrichment: Optional[Dict[str, Any]]) -> set:
    """Return the set of anchor IDs marked status=registered in the RAG
    enrichment block. Empty set when enrichment is missing, disabled, or
    has no `references` field."""
    if not isinstance(rag_enrichment, dict):
        return set()
    references = rag_enrichment.get("references") or []
    if not isinstance(references, list):
        return set()
    out = set()
    for ref in references:
        if not isinstance(ref, dict):
            continue
        if ref.get("status") != "registered":
            continue
        ident = ref.get("id")
        if isinstance(ident, str) and ident:
            out.add(ident)
    return out


def _matched_phrase(description: str) -> Optional[str]:
    """Return the canonical phrase (lower-cased) if any FAKE_ID_PHRASES
    appears as a substring of description (case-insensitive). None if
    no phrase hits."""
    if not isinstance(description, str) or not description:
        return None
    needle = description.lower()
    for phrase in FAKE_ID_PHRASES:
        if phrase in needle:
            return phrase
    return None


def _extracted_anchor_ids(description: str) -> List[str]:
    """Run the W3 D1 detection regex set against description text. Empty
    list on any extraction failure (description must remain a sentence,
    not a structured payload — silent fall-through here is correct
    because the absence of detected anchors is itself a "no suppression"
    signal, not a hard error)."""
    if not isinstance(description, str) or not description.strip():
        return []
    try:
        refs = detect_references(description)
    except RefExtractError:
        return []
    return [r.id for r in refs]


def _filter_one(
    finding: Dict[str, Any],
    registered: set,
    *,
    eligible_for_fake_id_rule: bool,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Decide whether to suppress one finding.

    Returns (suppress, suppression_record). suppression_record is the
    structured entry to append to the audit's ``suppressed_findings``
    list when ``suppress`` is True.

    `eligible_for_fake_id_rule` gates the F-0.2.17-W3-001 rule only — the
    RAG status-echo rule (F-0.2.18-W0-006) fires regardless of registered
    set size since it's description-shape-driven, not phrase-driven.
    """
    description = finding.get("description", "") if isinstance(finding, dict) else ""

    # F-0.2.18-W0-006 — RAG enrichment status echo (description-shape rule).
    if isinstance(description, str) and _RAG_STATUS_ECHO_PATTERN.match(description):
        return True, {
            "reason": RAG_STATUS_ECHO_REASON,
            "matched_description": description.strip(),
            "finding": dict(finding),
        }

    if not eligible_for_fake_id_rule:
        return False, None

    # F-0.2.17-W3-001 — registered-ID flagged as fake (phrase + anchor).
    phrase = _matched_phrase(description)
    if phrase is None:
        return False, None

    anchors = _extracted_anchor_ids(description)
    matched_anchor = next((a for a in anchors if a in registered), None)
    if matched_anchor is None:
        return False, None

    record: Dict[str, Any] = {
        "reason": SUPPRESSION_REASON,
        "matched_phrase": phrase,
        "matched_registered_anchor": matched_anchor,
        "finding": dict(finding),
    }
    return True, record


def filter_findings(
    findings: Iterable[Dict[str, Any]],
    rag_enrichment: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Apply the deterministic post-hoc filter.

    ``findings`` is the model-returned findings list (already
    schema-validated by the audit primitive). ``rag_enrichment`` is the
    audit's RAG enrichment summary dict (may be None when enrichment
    was disabled — in which case nothing is suppressed).

    Returns a dict shaped:
        {
            "active_findings": [...],     # ordered subset of findings to keep
            "suppressed_findings": [...], # structured suppression records
            "filter_enabled": bool,       # always True (filter ran)
            "filter_eligible": bool,      # rag_enrichment provided registered IDs
            "registered_id_count": int,   # size of the registered set
        }

    Raises AuditFindingFilterError if findings is not iterable.
    """
    try:
        finding_list: List[Dict[str, Any]] = list(findings) if findings is not None else []
    except TypeError as exc:
        raise AuditFindingFilterError(
            f"findings must be iterable, got {type(findings).__name__}"
        ) from exc

    registered = _registered_id_set(rag_enrichment)
    eligible = bool(registered)

    active: List[Dict[str, Any]] = []
    suppressed: List[Dict[str, Any]] = []

    for finding in finding_list:
        if not isinstance(finding, dict):
            # Schema validation upstream guarantees dict shape; if a
            # caller bypasses it, fail loud rather than silently letting
            # a non-finding through the filter.
            raise AuditFindingFilterError(
                f"finding must be dict, got {type(finding).__name__}"
            )
        suppress, record = _filter_one(
            finding,
            registered,
            eligible_for_fake_id_rule=eligible,
        )
        if suppress and record is not None:
            suppressed.append(record)
        else:
            active.append(finding)

    return {
        "active_findings": active,
        "suppressed_findings": suppressed,
        "filter_enabled": True,
        "filter_eligible": eligible,
        "registered_id_count": len(registered),
    }


__all__ = [
    "AuditFindingFilterError",
    "FAKE_ID_PHRASES",
    "SUPPRESSION_REASON",
    "RAG_STATUS_ECHO_REASON",
    "filter_findings",
]
