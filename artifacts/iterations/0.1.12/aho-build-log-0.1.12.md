# Build Log — aho 0.1.12

**Start:** 2026-04-11T02:36:42Z
**Agent:** Claude Code
**Phase:** 0
**Run:** 0.1.12
**Theme:** Evaluator baseline reload + smoke checkpoint-awareness + model-fleet.md cleanup

---

## W0 — Environment hygiene

**Actions:**
- Confirmed pwd, version, tests green
- Bumped checkpoint and version to 0.1.12
- Backed up files for W1-W3
- pip install -e .

---

## W1 — Evaluator baseline reload (aho-G060)

**Actions:**
- Removed global caches _ALLOWED_CLI_COMMANDS and _ALLOWED_SCRIPTS from evaluator.py
- get_allowed_scripts() and get_allowed_cli_commands() now compute fresh each call (~10ms overhead)
- Registered aho-G060 in gotcha_archive.json
- Added regression test tests/test_evaluator_reload.py — PASSED

**Discrepancies:** none

---

## W2 — smoke_instrumentation checkpoint-awareness (aho-G061)

**Actions:**
- Added checkpoint-read at script start before aho imports (sets AHO_ITERATION env var)
- Updated .aho.json current_iteration to 0.1.12
- Registered aho-G061 in gotcha_archive.json
- Smoke test: 8 events, all stamped iteration 0.1.12, 6 unique components

**Discrepancies:** none

---

## W3 — model-fleet.md cleanup

**Actions:**
- Updated model-fleet.md: title, version 0.1.4→0.1.12, all IAO identifier refs→aho
- Replaced "Trident" prong references with Pillar 1 and Pillar 8
- Updated Section 6 future extensions to remove stale 0.1.5-era speculation
- Bumped agents-architecture.md header from iao 0.1.7 to aho 0.1.12
- Verified: rg "IAO" model-fleet.md returns 0 matches

**Discrepancies:** none

---

## W4 — Dogfood + close

**Actions:**
- First build-log attempt: killed degenerate Qwen thinking loop (gotcha ID validation bug)
- Fixed evaluator gotcha ID matching: g.get("id") or g.get("code")
- Fixed new gotcha entries to use "id" field for consistency
- Added thinking-token repetition detection to qwen_client.py
- Second build-log attempt: succeeded, 633 words, 215s
- Report: succeeded, 684 words, 209s
- Iteration close: succeeded, 4/4 workstreams pass

**Verification results:**
- V1 synthesis non-empty: PASS
- V2 event log stamped 0.1.12: PASS (42 events)
- V3 model-fleet.md clean: PASS (0 IAO matches)
- V4 §22 ≥6 components: PASS (6: aho-cli, evaluator, nemoclaw, openclaw, qwen-client, structural-gates)
- V5 manual build log in §3: PASS
- V6 run file named correctly: PASS
- V7 tests green: PASS (56 passed, 1 skipped)

**Discrepancies:**
- Qwen thinking-token degeneration required qwen_client.py fix (thinking_detector added) — beyond original 0.1.12 scope but necessary for W4 completion
- Gotcha archive field inconsistency (id vs code) required evaluator fix

---

**End:** 2026-04-11T03:38:42Z
