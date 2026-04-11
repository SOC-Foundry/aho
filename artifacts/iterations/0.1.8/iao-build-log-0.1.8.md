# Build Log — iao 0.1.8

**Start:** 2026-04-10
**Agent:** claude-code
**Machine:** NZXTcos
**Phase:** 0 (UAT lab for aho)
**Iteration:** 0.1.8
**Theme:** Pillar rewrite + hardcoded-pillar cleanup + 0.1.7 carryover resolution

---

## W0 — Environment Hygiene

**Actions:**
- Backed up 5 state files to ~/dev/projects/iao.backup-pre-0.1.8/
- Bumped .iao-checkpoint.json iteration to 0.1.8
- Updated .iao.json current_iteration to 0.1.8, last_completed_iteration to 0.1.7
- Bumped VERSION in cli.py and pyproject.toml to 0.1.8
- Reinstalled package: `./bin/iao --version` returns `iao 0.1.8`
- Verified design and plan docs present

**Discrepancies:** none

---

## W1 — Base Harness Pillar Rewrite

**Actions:**
- Replaced Trident mermaid block + Ten Pillars section in base.md with Eleven Pillars
- Pillar text sourced from design doc section 3
- Rewrote preamble to avoid literal retired pillar string (would fail rg check)
- Updated base.md version header to 0.1.8
- Verified: 0 retired pillar references, Pillar 1 + 11 present, query_registry gone from pillar section

**Discrepancies:** none

---

## W2 — run_report.py De-hardcoding

**Actions:**
- Added `_load_pillars_from_base()` parser and `get_pillars()` cache accessor to run_report.py
- Replaced hardcoded 10-pillar list (lines 103-112) with `*get_pillars()` splat
- Updated section header from "Ten Pillars" to "Eleven Pillars"
- Fixed parser regex: `[^\n]*` instead of `.*` to prevent DOTALL cross-line header match
- Added `check_pillars_parseable()` pre-flight check in preflight/checks.py
- Added 6 unit tests in tests/test_run_report_pillars.py — all pass

**Discrepancies:** Initial regex used DOTALL `.*` in header pattern, causing it to span across lines and match wrong section content. Fixed on first retry.

---

## W3 — evaluator.py and templates.py Regex Cleanup

**Actions:**
- Removed `PILLAR_ID_RE` definition and all usages from evaluator.py
- Removed `pillar_ids` from `extract_references()` return dict
- Removed pillar validation block (lines 92-98) from `validate_references()`
- Updated templates.py: replaced old pillar regex with eleven-pillar section parser, kept `ten_pillars_block` as backward-compat alias
- Updated known_hallucinations.json: removed query_registry.py entries, added 10 retired pillar markers
- Updated test_evaluator.py: replaced pillar_ids test with anti-hallucination detection test
- All evaluator tests pass (4/4)

**Discrepancies:** none

---

## W4 — Evaluator Wired to Synthesis Pass

**Actions:**
- Added `artifact_type` parameter to `evaluate_text()` — synthesis artifacts auto-reject on any retired pattern match
- Updated system prompt in loop.py: "TEN PILLARS" replaced with "ELEVEN PILLARS", use `pillars_block` key
- Added `log_event("synthesis_evaluator_reject", ...)` calls in both two-pass and main loop paths
- Added `artifact_type=f"{artifact}_synthesis"` to all evaluate_text calls in loop.py
- Imported `log_event` into loop.py
- Added 3 regression tests in test_synthesis_evaluator.py: verified retired handoff pattern rejected in synthesis, warn without synthesis type, clean text accepted
- All 13 tests pass across evaluator, synthesis, and pillar test files

**Discrepancies:** none

---

## W5 — §22 Instrumentation Expansion

**Actions:**
- Wired cli.py: log_event on every subcommand dispatch (source_agent=iao-cli)
- Wired openclaw.py: log_event on session_start, chat, execute_code (source_agent=openclaw)
- Wired nemoclaw.py: log_event on dispatch with classified role (source_agent=nemoclaw)
- Wired evaluator.py: log_event on every evaluate_text call with severity (source_agent=evaluator)
- Wired qwen_client.py: log_event on DegenerateGenerationError raise (source_agent=repetition-detector)
- Wired structural_gates.py: log_event on every gate check with pass/fail (source_agent=structural-gates)
- Added check_required_sections() convenience function to structural_gates.py
- Smoke test passes with 6 unique components: evaluator, iao-cli, nemoclaw, openclaw, qwen-client, structural-gates

**Discrepancies:** none

---

## W6 — W8 Agent Instrumentation Fix

**Actions:**
- Extracted `build_workstream_summary(checkpoint)` function in run_report.py
- Added IAO_EXECUTOR env var fallback when per-workstream agent field is missing/null
- Updated `log_workstream_complete` in logger.py to write agent to checkpoint on each completion
- Added 3 unit tests: env fallback, checkpoint-preferred, no-unknown-agents — all pass

**Discrepancies:** none

---

## W7 — Baseline Updates for query_registry.py

**Actions:**
- Verified known_hallucinations.json has 0 query_registry references (W3 cleaned)
- Verified base.md has 0 query_registry references before ADR (W1 cleaned)
- Verified CLAUDE.md/GEMINI.md only have "Known shims" context references (already correct)
- Appended ADR-041 to docs/harness/base.md documenting scripts/query_registry.py as legitimate

**Discrepancies:** none

---

## W8 — Dogfood + Close

**Actions:**
- Ran `./bin/iao iteration build-log 0.1.8` — Qwen synthesis was rejected by evaluator (W4 working as designed: caught retired pattern references in Qwen output). Qwen repeatedly generates content containing retired patterns despite instructions. Restored manual build log.
- Generated run report mechanically
- 16/16 test suite passes

**Discrepancies:**
- Qwen synthesis for build-log rejected 3 times: Qwen generated text containing retired patterns (handoff language and old pillar naming) despite the updated system prompt. The evaluator (W4) correctly caught these. This validates that the evaluator wiring works but reveals that Qwen's RAG context still contains stale 0.1.7 content. Logged as 0.1.9 carryover.
- Qwen report synthesis skipped to avoid overwriting. Manual build log preserved as ground truth.

---
