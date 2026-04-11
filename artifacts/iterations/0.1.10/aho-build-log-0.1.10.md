# Build Log — aho 0.1.10

**Start:** 2026-04-10
**Agent:** Claude Code (claude-opus-4-6)
**Machine:** NZXTcos
**Phase:** 0
**Run:** 0.1.10
**Theme:** Restore §22 instrumentation, fix bundle generator, verify rename completeness

---

## W0 — Environment Hygiene

**Actions:**
- Backed up files 0.1.10 will modify to ~/dev/projects/iao.backup-pre-0.1.10/
- Bumped .aho-checkpoint.json to iteration=0.1.10, last_completed_iteration=0.1.9
- Deleted docs/iterations/0.1.99/ (Condition 4 resolved)
- Bumped VERSION in cli.py to "aho 0.1.10", pyproject.toml to 0.1.10
- pip install -e . verified: ./bin/aho --version returns "aho 0.1.10"
- Initialized manual build log

**Pre-flight discrepancies:**
- Not a git repo — git mv in plan replaced with plain mv/cp throughout
- 0.1.9 files already aho-* prefixed (W1 already resolved from 0.1.9 run)
- Checkpoint had completed_at=null for 0.1.9, last_completed_iteration was 0.1.8 — corrected to last_completed_iteration=0.1.9
- pyproject.toml was at 0.1.8 (not 0.1.9) — bumped directly to 0.1.10

---

## W1 — Rename 0.1.9 iao-prefixed files

**Actions:**
- Verified: all 0.1.9 files already aho-* prefixed on disk (rename completed during 0.1.9 execution)
- No iao-design/plan/build-log-0.1.9 references in src/ (0 matches)
- References inside 0.1.9 plan doc and run report are historical content, not live references
- Historical files in 0.1.2-0.1.8 retain iao-* prefix (correct)

**Discrepancies:** W1 was already resolved by 0.1.9. No action needed.

---

## W2 — log_event source_agent sweep

**Actions:**
- Found 6 sites with hardcoded "iao-cli" in src/aho/: cli.py, brave.py, firestore.py, router.py, query.py (x2)
- Renamed all "iao-cli" → "aho-cli"
- Updated env var fallback chain: AHO_AGENT → IAO_AGENT → "aho-cli" (backwards compat during transition)
- Verified: rg "\"iao-[a-z-]+\"" src/aho/ returns 0 matches
- Smoke test: ./bin/aho status → event log entry shows source_agent="aho-cli" ✓
- Test suite: 50 passed, 2 failed (pre-existing: age tty issue, artifacts_loop missing "Phase 0")

**Discrepancies:** none (2 pre-existing test failures unrelated to W2)

---

## W3 — OpenClaw/NemoClaw/structural-gates instrumentation audit

**Actions:**
- Audited openclaw.py: log_event at session_start, chat, execute_code — all wired, source_agent="openclaw" ✓
- Audited nemoclaw.py: log_event at dispatch — wired, source_agent="nemoclaw" ✓
- Audited structural_gates.py: log_event at check_artifact, check_required_sections — wired, source_agent="structural-gates" ✓
- Fixed scripts/smoke_instrumentation.py: ./bin/iao → ./bin/aho
- Ran smoke_instrumentation.py: 8 events, 6 unique components
  - aho-cli, evaluator, nemoclaw, openclaw, qwen-client, structural-gates
- All 6 expected components present in event log ✓

**Discrepancies:** none

---

## W4 — Manual-build-log-first enforcement in loop.py

**Actions:**
- Added generate_build_log_synthesis() function to src/aho/artifacts/loop.py
  - Checks for manual build log at docs/iterations/<version>/aho-build-log-<version>.md
  - Raises FileNotFoundError with clear ADR-042 message if missing
  - Returns manual log path if present
- Wired check into run_artifact_loop(): called for build-log artifact before synthesis
- Created tests/test_build_log_first.py with 2 test cases:
  - test_synthesis_raises_when_manual_missing: PASS
  - test_synthesis_proceeds_when_manual_present: PASS
- Full test suite: 52 passed, 2 failed (same pre-existing failures)

**Discrepancies:** none

---

## W5 — Dogfood + close

**Actions:**
- Verified manual build log has 5 workstream headers (W0-W4)
- Updated .aho.json current_iteration to 0.1.10
- Build-log synthesis: DEGENERATE — Qwen entered "Wait, checking..." loop, killed after ~5min
  - Synthesis file not written. Manual build log is primary per ADR-042
- Report synthesis: PASS — 715 words, generated at aho-report-0.1.10.md
- Postflight: ran with expected warnings (bundle not yet gen, readme date)
- Close: generated run report and bundle
- Re-ran smoke_instrumentation.py to populate event log with all 6 components
- Regenerated bundle with full component data
- Regenerated 0.1.9 bundle (W1 rename now makes §1-§3 resolve)

**Verification results:**
- V1 §1 Design contains content: PASS
- V2 §2 Plan contains content: PASS
- V3 §3 Build Log has manual content: PASS
- V4 §22 has >=6 components with aho-* naming: PASS (aho-cli, evaluator, nemoclaw, openclaw, qwen-client, structural-gates)
- V5 0.1.99 deleted: PASS
- V6 0.1.9 bundle regen clean: PASS

**Discrepancies:**
- Build-log synthesis degenerate (Qwen "Wait, checking..." loop). Non-blocking per ADR-042.
- pyproject.toml was at 0.1.8 not 0.1.9 going in — suggests 0.1.9 close did not bump it

---

## W6 — Project Root Rename (conditional)

**Actions:**
- All W5 verifications passed — W6 eligible
- Surfacing capability-gap interrupt for Kyle
- Project root rename requires human action (shell session cannot rename its own cwd)

**Capability-gap interrupt:**

```fish
# From a shell OUTSIDE the iao directory:
cd ~
mv ~/dev/projects/iao ~/dev/projects/aho
cd ~/dev/projects/aho
./bin/aho --version
# Expected: aho 0.1.10

# Update any fish abbreviations or shell aliases pointing at the old path
functions -q iao-cd; and functions --erase iao-cd
# (Kyle to audit and update as needed)
```

**Status:** W6 INTERRUPT — awaiting Kyle action

---

