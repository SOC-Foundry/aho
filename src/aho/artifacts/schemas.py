"""Artifact kind metadata and minimal validation.

Each aho iteration produces six canonical artifacts. This module defines
their identifiers, default filenames, and the cheap structural checks the
loop applies after Qwen returns text.

aho 0.1.7 W2: inverted min_words to max_words to discourage Qwen padding,
and added required_sections for structural gatekeeping.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ArtifactKind:
    name: str            # canonical id, e.g. "design"
    filename_stem: str   # e.g. "design" -> {prefix}-design-{iter}.md
    max_words: int       # maximum word count (inversion from 0.1.4 min_words)
    required_sections: tuple[str, ...]  # headers or section markers that must appear
    required_terms: tuple[str, ...]  # must appear (case-insensitive) in body
    min_words: int = 50  # absolute minimum to avoid empty responses


# Canonical ordering: design -> plan -> build-log -> report -> bundle
SCHEMAS: Dict[str, ArtifactKind] = {
    "design": ArtifactKind(
        "design",
        "design",
        3000,
        (
            "Phase 0",
            "§1",
            "§2",
            "§3",
            "§4",
            "§5",
            "§6",
            "§7",
            "§8",
            "§9",
        ),
        ("iteration", "workstream"),
    ),
    "plan": ArtifactKind(
        "plan",
        "plan",
        2500,
        (
            "Phase",
            "Section A",
            "Section B",
            "Section C",
            "Section D",
            "Section E",
        ),
        ("workstream", "executor"),
    ),
    "build-log": ArtifactKind(
        "build-log",
        "build-log",
        1500,
        ("# Build Log", "## W0"),
        ("start:",),
    ),
    "report": ArtifactKind(
        "report",
        "report",
        1000,
        ("# Report", "## Executive Summary", "## Workstream Detail"),
        ("status",),
    ),
    "run": ArtifactKind(
        "run",
        "run",
        5000,  # Run report is structural/mechanical, high max
        ("## Workstream Summary", "## Sign-off"),
        ("iteration",),
        min_words=200,
    ),
    "bundle": ArtifactKind(
        "bundle",
        "bundle",
        1000000,  # Bundle is an aggregate, no practical max
        (),  # Sections checked by separate logic in bundle.py
        ("iteration",),
    ),
}


def validate_artifact(kind: str, text: str) -> tuple[bool, str]:
    """Return (ok, message). Cheap structural validation only."""
    spec = SCHEMAS.get(kind)
    if spec is None:
        return False, f"unknown artifact kind: {kind}"
    
    words = len(text.split())
    if words < spec.min_words:
        return False, f"too short: {words} words (min {spec.min_words})"
    
    # max_words is now a warning/soft gate, but we'll include it in the message
    msg_suffix = f"({words} words)"
    if words > spec.max_words:
        msg_suffix += f" - WARNING: exceeded max_words {spec.max_words}"

    lower = text.lower()
    missing_terms = [t for t in spec.required_terms if t.lower() not in lower]
    if missing_terms:
        return False, f"missing required terms: {missing_terms} {msg_suffix}"
    
    missing_sections = [s for s in spec.required_sections if s not in text]
    if missing_sections:
        return False, f"missing required sections: {missing_sections} {msg_suffix}"

    return True, f"ok {msg_suffix}"
ARTIFACTS = SCHEMAS
