"""council.audit_ref_extract — detect reference-shaped tokens in audit targets.

W3 of 0.2.17 closes F-0.2.17-W2-006 by enriching the auditor prompt with
RAG retrievals for every reference ID present in the audit target. Step 1
of that pipeline is detecting which reference-shaped tokens are present.

Patterns supported (case-sensitive on the reference family — `F-`, `AF`,
`ADR`, `D`, `G`, `B`, `W`, `Sec` — but tolerant of a single space or hyphen
between `ADR` and its number):

- Carry-forward IDs: F-{phase.iteration.run}-W{n}-{seq}, F-W{n}-{seq},
  F-host-{seq}, W{n}-AF{seq}.
- Audit finding IDs: AF{nnn}, AF-{phase.iteration.run}-W{n}-{seq}, AF-{n}.
- ADR references: ADR {n}, ADR-{n}.
- Gotcha references: G{n}, Sec{n}.
- Deliverable IDs: D{n}, B{n}.{n}.

Empty / non-string input raises RefExtractError. The detector itself is
deliberately permissive: false positives are downstream of D2, where RAG
retrieval will tag unmatched IDs as `unverified` rather than auto-fail.
"""
from __future__ import annotations

import re
from typing import Dict, List, NamedTuple


class RefExtractError(ValueError):
    """Caller passed an unusable audit target."""


class DetectedRef(NamedTuple):
    """A single reference-shaped token, post-deduplication.

    `kind` is the family the matcher hit — used by the auditor prompt to
    explain to llama what the registered-references section contains.
    `id` is the canonical surface form (whitespace normalised — `ADR 0007`
    and `ADR-0007` both surface as `ADR-0007` so dedup is meaningful).
    """

    id: str
    kind: str


# Order matters — longest / most-specific patterns first so the carry-forward
# `F-0.2.17-W0-001` does not dissolve into the shorter `F-W0-...` family.
# Each entry is (kind, compiled regex). Patterns use word boundaries to
# avoid `D1` matching inside `2D2` or similar dross.
_PATTERNS: List[tuple] = [
    # Audit finding (full form): AF-0.2.17-W1-001
    ("audit_finding_full", re.compile(r"\bAF-\d+\.\d+\.\d+-W\d+-\d+\b")),
    # Carry-forward (full form): F-0.2.17-W0-001
    ("carry_forward_full", re.compile(r"\bF-\d+\.\d+\.\d+-W\d+-\d+\b")),
    # Carry-forward (host): F-host-001
    ("carry_forward_host", re.compile(r"\bF-host-\d+\b")),
    # Carry-forward (short): F-W0-004
    ("carry_forward_short", re.compile(r"\bF-W\d+-\d+\b")),
    # Workstream-scoped AF: W4-AF002
    ("audit_finding_ws_scoped", re.compile(r"\bW\d+-AF\d+\b")),
    # Audit finding (short numbered): AF-1, AF-12
    ("audit_finding_short", re.compile(r"\bAF-\d+\b")),
    # Audit finding (bare): AF001, AF003
    ("audit_finding_bare", re.compile(r"\bAF\d+\b")),
    # ADR reference — tolerate space or hyphen separator: ADR 0007 or ADR-0007
    ("adr", re.compile(r"\bADR[\s-]\d{1,4}\b")),
    # Bucket / sub-deliverable: B2.3, B1.5
    ("bucket", re.compile(r"\bB\d+\.\d+\b")),
    # Gotcha: G081, G22 — at least one digit, anchored on word boundary
    ("gotcha", re.compile(r"\bG\d{2,4}\b")),
    # Section reference: Sec1, Sec12
    ("section", re.compile(r"\bSec\d+\b")),
    # Deliverable: D1, D12. Two digits max — D123 is not a deliverable shape.
    ("deliverable", re.compile(r"\bD\d{1,2}\b")),
]


def _canonicalise(kind: str, raw: str) -> str:
    """Normalise surface forms so dedup is meaningful.

    - `ADR 0007` and `ADR-0007` both surface as `ADR-0007`.
    - All other kinds round-trip — they have one canonical written form.
    """
    if kind == "adr":
        # Replace any whitespace span between ADR and the number with a hyphen.
        return re.sub(r"^ADR[\s-]+", "ADR-", raw)
    return raw


def detect_references(target: str) -> List[DetectedRef]:
    """Scan `target` for reference-shaped tokens. Returns a deduplicated
    ordered list — first appearance wins for ordering, kind is the most-
    specific family that matched.

    Raises RefExtractError on empty / non-string input.
    """
    if not isinstance(target, str):
        raise RefExtractError(
            f"audit target must be str, got {type(target).__name__}"
        )
    if not target.strip():
        raise RefExtractError("audit target must be non-empty")

    # Walk patterns in declared order, recording (start_offset, kind, id) for
    # every match. Then sort by start offset for stable insertion order
    # (so the prompt section reads "in target order, dedup'd").
    hits: List[tuple] = []
    claimed: List[tuple] = []  # (start, end) ranges already absorbed

    def _overlaps(span: tuple) -> bool:
        s, e = span
        for cs, ce in claimed:
            if s < ce and e > cs:
                return True
        return False

    for kind, pattern in _PATTERNS:
        for m in pattern.finditer(target):
            span = m.span()
            if _overlaps(span):
                # A more-specific pattern already absorbed this region.
                continue
            claimed.append(span)
            hits.append((span[0], kind, _canonicalise(kind, m.group(0))))

    hits.sort(key=lambda h: h[0])

    seen: Dict[str, str] = {}
    ordered: List[DetectedRef] = []
    for _, kind, ident in hits:
        if ident in seen:
            continue
        seen[ident] = kind
        ordered.append(DetectedRef(id=ident, kind=kind))
    return ordered


__all__ = ["detect_references", "DetectedRef", "RefExtractError"]
