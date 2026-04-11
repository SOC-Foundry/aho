# aho — Design 0.1.11

**Run:** 0.1.11
**Phase:** 0
**Theme:** Run file rename + project root confirmation + test suite hygiene
**Machine:** NZXTcos
**Predecessor:** 0.1.10 (graduated clean, W6 capability-gap interrupt pending)
**Authored:** 2026-04-10

---

## §1. Why 0.1.11 exists

0.1.10 graduated clean — the first clean graduation since 0.1.7. All internal identifiers are `aho`/`ahomw`. §22 instrumentation is restored to 6 components. ADR-042 enforcement is in code. The rename arc's internal work is done.

Three items remain from the post-0.1.8 review and the 0.1.10 close:

1. **The `run-report` → `run` filename rename.** Kyle requested this during the post-0.1.8 amendments. It was missed in 0.1.9 and 0.1.10. `aho-run-report-*.md` becomes `aho-run-*.md`. The run report generator, bundle spec, and postflight checks all need updating.

2. **Project root rename confirmation.** 0.1.10 W6 surfaced a capability-gap interrupt for Kyle to execute `mv ~/dev/projects/iao ~/dev/projects/aho`. If Kyle has done this, 0.1.11 confirms it and updates any references. If not, 0.1.11 W0 surfaces the interrupt again with the fish commands.

3. **Two pre-existing test failures.** `test_secrets_backends` (age tty issue) and `test_artifacts_loop` (missing "Phase 0" string). Both predate 0.1.10 and are not regressions, but they erode confidence in the test suite baseline. Worth cleaning up while the scope is small.

Additionally, Qwen synthesis went degenerate in 0.1.10 W5 ("Wait, checking..." loop). Non-blocking per ADR-042, but the repetition detector may need threshold tuning. W3 investigates this.

---

## §2. Workstreams

Five workstreams. Wall clock target: ~3 hours.

### W0 — Environment hygiene + project root confirmation (20 min)

**Goal:** Confirm project root is at `~/dev/projects/aho` (if Kyle ran the W6 commands) or surface the interrupt again if it's still at `~/dev/projects/iao`. Bump checkpoint to 0.1.11. Initialize manual build log.

**Success:** `command pwd` returns either `/home/kthompson/dev/projects/aho` (rename done) or `/home/kthompson/dev/projects/iao` (rename pending — log as discrepancy, continue). `./bin/aho --version` returns `aho 0.1.11`.

### W1 — Run file filename rename (60 min)

**Goal:** Rename the run report artifact from `aho-run-report-*.md` to `aho-run-*.md` going forward. Update all code and templates that generate or reference this filename.

**Deliverables:**
- `src/aho/feedback/run_report.py`: output filename pattern updated from `aho-run-report-{version}.md` to `aho-run-{version}.md`
- `src/aho/postflight/run_report_complete.py` → rename to `src/aho/postflight/run_complete.py`, update filename check
- `src/aho/postflight/run_report_quality.py` → rename to `src/aho/postflight/run_quality.py`, update filename check
- `src/aho/bundle/__init__.py`: §5 "Run Report" section updated to look for `aho-run-{version}.md`
- `prompts/run-report.md.j2`: if the template references the output filename, update it
- Any `__init__.py` imports in `postflight/` that reference the old module names
- Historical files (`aho-run-report-0.1.9.md`, `aho-run-report-0.1.10.md`) stay with their original names — only going-forward naming changes

**Success:**
- `./bin/aho iteration close` (in a future dogfood) produces `aho-run-0.1.11.md`, not `aho-run-report-0.1.11.md`
- `rg "run-report" src/aho/` returns 0 matches (or only within historical-context prose)
- `pytest tests/ -v` passes (minus the two pre-existing failures addressed in W2)

### W2 — Test suite hygiene (45 min)

**Goal:** Fix the two pre-existing test failures so the test suite is fully green.

**Deliverables:**

1. `test_secrets_backends` (age tty issue): The age backend test attempts to invoke `age` which requires a TTY for passphrase entry. In a headless agent environment, this fails. Fix: skip the test when no TTY is available (`@pytest.mark.skipif(not sys.stdin.isatty(), reason="age requires TTY")`), OR mock the age subprocess call in the test.

2. `test_artifacts_loop` (missing "Phase 0"): The test expects a "Phase 0" string in loop output that may have been removed or renamed during the 0.1.8 pillar rewrite or the 0.1.9 rename. Fix: read the test, determine what string it expects, update the expectation to match the current loop output.

**Success:** `pytest tests/ -v` passes with 0 failures.

### W3 — Qwen degenerate synthesis investigation (45 min)

**Goal:** Investigate the "Wait, checking..." degenerate pattern from 0.1.10 W5. Determine whether the repetition detector's threshold or pattern needs tuning.

**Deliverables:**
- Read `src/aho/artifacts/repetition_detector.py` — document the current window size, threshold, and detection algorithm
- Review the 0.1.10 event log for the degenerate event: what was the Qwen prompt, how long did it run before being killed, what was the output
- Determine: does "Wait, checking..." vary enough per token to evade the rolling-window detector? If yes, add a secondary detector for non-repeating but non-productive output patterns (low information density over a time window)
- If the fix is straightforward, implement it. If it requires significant architecture (e.g. an information-density scorer), document the finding and defer the implementation

**Success:** Either the repetition detector now catches the "Wait, checking..." pattern, OR the investigation is documented in the build log with a concrete fix proposal for a future run.

### W4 — Dogfood + close (60 min)

**Goal:** Run the loop against 0.1.11 itself. Verify the run file rename landed. Verify test suite is green.

**Deliverables:**
- Manual build log is present (written workstream-by-workstream during W0-W3)
- `./bin/aho iteration build-log 0.1.11` generates synthesis (may or may not succeed — ADR-042 non-blocking)
- `./bin/aho iteration report 0.1.11` generates report
- `./bin/aho iteration close` generates run file and bundle

**Verification checks:**

1. Close produces `aho-run-0.1.11.md`, NOT `aho-run-report-0.1.11.md`
2. Bundle §5 references the file as `aho-run-0.1.11.md`
3. `rg "run-report" src/aho/` returns 0 (or only historical context)
4. `pytest tests/ -v` shows 0 failures
5. §22 shows ≥6 components
6. Manual build log is present in bundle §3

**Success:** All six checks pass.

---

## §3. Scope boundaries

- No new amendments from the post-0.1.8 review (Nemotron evaluator, token tracking, scoring registry, etc.). Those are candidates for future runs.
- No CLAUDE.md / GEMINI.md updates — per-phase, not per-run.
- No new ADRs unless the W3 investigation produces a concrete architecture change.
- If the project root rename hasn't happened yet, 0.1.11 does NOT re-surface it as a workstream — it logs it as a discrepancy and continues. Kyle executes the rename on his own schedule.

---

## §4. Graduation criteria

**GRADUATE** — All six verification checks pass, test suite green (0 failures), run file filename is `aho-run-0.1.11.md`.

**GRADUATE WITH CONDITIONS** — Five of six checks pass, or test suite has ≤1 failure. Conditions documented.

**DO NOT GRADUATE** — Run file still named `aho-run-report-*.md` after W1 (the primary objective of this run didn't land), or test suite has more failures than it started with.

---

## §5. Sign-off

- [ ] I have reviewed the bundle
- [ ] I have reviewed the build log
- [ ] I have reviewed the report
- [ ] I have answered all agent questions
- [ ] I am satisfied with this iteration's output

---

*Design generated 2026-04-10, aho 0.1.11 planning*
