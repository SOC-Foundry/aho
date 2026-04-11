"""Tests for the W6 Qwen-managed artifact loop.

These tests do not call Ollama. They cover schema validation, template
rendering against the real artifacts/prompts/ directory, and the loop's dry-run
path which exercises file writing without network I/O.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from aho.artifacts.loop import ARTIFACT_KINDS, run_artifact_loop
from aho.artifacts.schemas import ARTIFACTS, validate_artifact
from aho.artifacts.templates import render_prompt

CTX = {
    "iteration": "0.1.2",
    "prefix": "iao",
    "project": "iao",
    "project_code": "ahomw",
    "now_utc": "2026-04-08T00:00:00Z",
    "workstreams": [
        {"id": "W1", "description": "test", "status": "pass", "agent": "Gemini"},
        {"id": "W6", "description": "loop", "status": "pass", "agent": "Gemini"}
    ],
    "prior_artifacts": {},
    "trident_block": "(trident placeholder for tests)",
    "ten_pillars_block": "(pillars placeholder for tests)",
    "seed": "",
    "agent_questions": [],
}


class ArtifactLoopTests(unittest.TestCase):
    def test_kinds_match_schemas(self):
        self.assertEqual(set(ARTIFACT_KINDS), set(ARTIFACTS.keys()))
        self.assertEqual(ARTIFACT_KINDS[0], "design")
        self.assertIn("bundle", ARTIFACT_KINDS)

    def test_validate_rejects_short(self):
        ok, msg = validate_artifact("design", "too short")
        self.assertFalse(ok)
        self.assertIn("too short", msg)

    def test_validate_accepts_long_enough(self):
        # design requires "Phase 0", "iteration", "workstream" AND sections §1-§10
        sections = "\n".join([f"§{i}" for i in range(1, 11)])
        body = f"Phase 0\nWhat is iao\n{sections}\niteration workstream " + ("word " * 6000)
        ok, msg = validate_artifact("design", body)
        self.assertTrue(ok, f"Validation failed: {msg}")


    def test_validate_unknown_kind(self):
        ok, msg = validate_artifact("nope", "x" * 5000)
        self.assertFalse(ok)
        self.assertIn("unknown", msg)

    def test_render_design_prompt(self):
        rendered = render_prompt("design", CTX)
        self.assertIn("0.1.2", rendered)
        self.assertIn("W1", rendered)
        self.assertIn("W6", rendered)

    def test_render_all_templates_smoke(self):
        for kind in ARTIFACT_KINDS:
            out = render_prompt(kind, CTX)
            self.assertGreater(len(out), 50, f"{kind} rendered empty")

    def test_loop_dry_run_writes_file(self):
        with TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            result = run_artifact_loop(
                "report", "0.1.2", dry_run=True, output_path=out
            )
            self.assertTrue(result.output_path.exists())
            self.assertIn("DRY RUN", result.output_path.read_text())


if __name__ == "__main__":
    unittest.main()
