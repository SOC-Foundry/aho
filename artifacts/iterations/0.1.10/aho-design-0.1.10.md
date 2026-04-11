# aho — Design 0.1.10

**Run:** 0.1.10
**Phase:** 0 (UAT lab)
**Theme:** Restore §22 instrumentation, fix bundle generator, verify rename completeness
**Machine:** NZXTcos
**Predecessor:** 0.1.9 (graduated with conditions — rename landed, bundle generator broke)
**Authored:** 2026-04-10

---

## §1. Phase position

Phase 0 remains UAT lab for aho. 0.1.9 landed the Python source rename but surfaced three regressions that prevent this run from claiming the rename arc is complete: the bundle generator can't find the manual-prefixed artifacts, §22 instrumentation regressed from 6 components to 3, and Qwen's synthesis build log ran without a ground-truth manual build log to verify against. 0.1.10 is a focused fix run. No new scope beyond the six conditions carried from 0.1.9.

The project root rename (`~/dev/projects/iao/` → `~/dev/projects/aho/`) is still pending and belongs at the end of whichever run closes out the rename arc cleanly. 0.1.10 aims to BE that run — if all six conditions resolve cleanly, project root rename happens in W6 as the final workstream. If any condition carries forward, project root stays for a later run.

---

## §2. Why 0.1.10 exists

0.1.9 was declared GRADUATE WITH CONDITIONS with six carried-forward items:

1. **Bundle generator file-lookup bug.** §1 Design, §2 Plan, and the manual build log all showed `(missing)` in the 0.1.9 bundle because the generator looks for `aho-*` prefixed files but the actual files on disk still carry `iao-*` prefixes. The fix is either generator-side (accept both prefixes) or filesystem-side (rename the files on disk). The filesystem-side fix is cleaner long-term.

2. **§22 Agentic Components regressed from 6 to 3.** OpenClaw, NemoClaw, and structural-gates components disappeared from the 0.1.9 §22 table. `iao-cli` retained its old `source_agent` name instead of becoming `aho-cli`. The rename sweep missed string literals inside `log_event()` call sites.

3. **Qwen synthesis build log unverifiable.** Without a manual build log to ground-truth against, Qwen's synthesis invented workstream content that looked plausible but had no source of truth. The ADR-042 pattern (manual authoritative, synthesis optional commentary) depends on the manual file actually being present and visible to the bundle generator.

4. **`docs/iterations/0.1.99/` garbage.** Leftover from a prior throwaway test that was never cleaned up.

5. **Wall clock column empty in run report workstream summary.** Minor tracking gap.

6. **Report synthesis and run report disagree about W8 status.** Report says W8 is "N/A reserved for future iteration", run report says W8 passed. Symptom of Qwen inventing content without ground truth.

All six are mechanical fixes. None require new architecture. None require new amendments. The run is lean by design.

---

## §3. Project state going into 0.1.10

Verified from the 0.1.9 bundle §20 file inventory:
- Python package: `src/aho/` (complete)
- CLI entry point: `bin/aho`
- State files: `.aho.json`, `.aho-checkpoint.json`
- Event log: `data/aho_event_log.jsonl`
- Rebuild script: `scripts/rebuild_aho_archive.py`
- Renamed postflight check: `src/aho/postflight/pillars_present.py` (0.1.8 Condition 5)
- Tests: `test_synthesis_evaluator.py`, `test_rag_forbidden_filter.py`, `test_evaluator_dynamic_baseline.py`, `test_workstream_agent.py`
- ChromaDB: three collection directories present under `data/chroma/` — collection names not directly visible in the bundle, need runtime query to confirm which is the rebuilt aho archive
- Historical iteration files `iao-*` prefixed at `docs/iterations/0.1.2/` through `docs/iterations/0.1.8/` — correct, historical records preserved

Specific problem files going into 0.1.10:
- `docs/iterations/0.1.9/iao-design-0.1.9.md` — should be renamed to `aho-design-0.1.9.md`
- `docs/iterations/0.1.9/iao-plan-0.1.9.md` — should be renamed to `aho-plan-0.1.9.md`
- `docs/iterations/0.1.9/iao-build-log-0.1.9.md` — should be renamed to `aho-build-log-0.1.9.md`
- `docs/iterations/0.1.99/aho-build-log-synthesis-0.1.99.md` — should be deleted along with parent dir
- `src/aho/cli.py` — contains `log_event(component="iao-cli"...)` or equivalent string literal that needs updating
- Unknown sites in `src/aho/agents/openclaw.py`, `src/aho/agents/nemoclaw.py`, `src/aho/postflight/structural_gates.py` — instrumentation either disconnected or logging under wrong name

Project root: `~/dev/projects/iao/` (unchanged)

---

## §4. Workstreams

Six workstreams. Wall clock target: ~4 hours.

### W0 — Environment hygiene (15 min)

**Goal:** Clean transition from 0.1.9 to 0.1.10. Resolve Condition 4.

**Deliverables:**
- Backup of files 0.1.10 will modify: `src/aho/cli.py`, `src/aho/agents/openclaw.py`, `src/aho/agents/nemoclaw.py`, `src/aho/postflight/structural_gates.py`, `src/aho/bundle/__init__.py` (and any other bundle generator file), `src/aho/artifacts/loop.py`, all `docs/iterations/0.1.9/iao-*.md` files, to `~/dev/projects/iao.backup-pre-0.1.10/`
- `.aho-checkpoint.json` bumped: `iteration=0.1.10`, `last_completed_iteration=0.1.9`
- `docs/iterations/0.1.10/` created
- Manual build log initialized at `docs/iterations/0.1.10/aho-build-log-0.1.10.md` (follows ADR-042 naming from the start)
- `docs/iterations/0.1.99/` deleted (Condition 4)

**Success:**
- `./bin/aho --version` returns `aho 0.1.10`
- `test ! -d docs/iterations/0.1.99` passes
- `test -f docs/iterations/0.1.10/aho-build-log-0.1.10.md` passes

### W1 — Rename 0.1.9 iao-prefixed files (20 min)

**Goal:** Resolve Condition 1 filesystem-side. Rename the three `iao-*` files in `docs/iterations/0.1.9/` to match the current `aho-*` convention so the bundle generator can find them.

**Deliverables:**
- `git mv docs/iterations/0.1.9/iao-design-0.1.9.md docs/iterations/0.1.9/aho-design-0.1.9.md`
- `git mv docs/iterations/0.1.9/iao-plan-0.1.9.md docs/iterations/0.1.9/aho-plan-0.1.9.md`
- `git mv docs/iterations/0.1.9/iao-build-log-0.1.9.md docs/iterations/0.1.9/aho-build-log-0.1.9.md`
- Any cross-references inside these files to their old names (if any) updated via `sed`
- Verify: `command ls docs/iterations/0.1.9/` shows only `aho-*` prefixed files (plus `seed.json`)

**Success:**
- Three files renamed, no broken references inside
- `rg "iao-design-0.1.9\|iao-plan-0.1.9\|iao-build-log-0.1.9" docs/ src/` returns 0

**Scope boundary:** Do NOT rename historical iao-* files in `docs/iterations/0.1.2/` through `docs/iterations/0.1.8/`. Those are historical records and stay as-is.

### W2 — log_event source_agent rename sweep (45 min)

**Goal:** Resolve Condition 2 first part. Find and rewrite every `log_event()` call site that hardcodes `iao-*` as the component or source_agent, update to `aho-*`.

**Deliverables:**
- `rg` audit across `src/aho/` for hardcoded `iao-*` strings in `log_event()` calls:
  - `iao-cli` → `aho-cli`
  - Any other `iao-*` component names → `aho-*`
- Each found site edited with `str_replace` or `sed -i`
- Dry-run verification: `rg '"iao-[a-z-]+"' src/aho/` returns 0 matches after the sweep
- Unit smoke test: run `./bin/aho --version` and check that `data/aho_event_log.jsonl` gets an entry with `source_agent: "aho-cli"`, not `iao-cli`

**Success:**
- `rg '"iao-[a-z-]+"' src/aho/` returns 0
- Fresh event log entry after a test command shows `aho-cli`

### W3 — OpenClaw / NemoClaw / structural-gates instrumentation audit and restore (75 min)

**Goal:** Resolve Condition 2 second part. Figure out why these three components disappeared from §22 in 0.1.9 and restore their instrumentation.

**Deliverables:**
- Read `src/aho/agents/openclaw.py`, `src/aho/agents/nemoclaw.py`, `src/aho/postflight/structural_gates.py`
- For each, confirm:
  - The module imports `log_event` (or equivalent logger function)
  - `log_event` calls exist at the expected instrumentation points (session_start, chat, execute_code for openclaw; dispatch for nemoclaw; each gate check for structural_gates)
  - The `source_agent` or component name passed is `aho-*` not `iao-*`
  - The calls are reachable from the runtime paths that execute during a normal run
- If any instrumentation is missing or broken, restore it referencing the 0.1.8 W5 pattern
- Smoke test `scripts/smoke_instrumentation.py` (already exists from 0.1.8) — run it, verify event log receives entries from all six components: aho-cli, openclaw, nemoclaw, evaluator, qwen-client, structural-gates

**Success:**
- `python3 scripts/smoke_instrumentation.py` exits 0 with ≥6 unique components in the event log
- Each of openclaw, nemoclaw, structural-gates, aho-cli, evaluator, qwen-client appears in a fresh event log slice

### W4 — Manual-build-log-first enforcement in loop.py (45 min)

**Goal:** Resolve Condition 3. The loop's `build-log` synthesis path should require a manual build log to exist before generating synthesis content. If the manual file is missing, the loop fails loudly with a clear message instead of silently producing hallucinated commentary as the only visible build log.

**Deliverables:**
- Edit `src/aho/artifacts/loop.py`: in the build-log generation path, check for existence of `docs/iterations/<version>/aho-build-log-<version>.md` before invoking Qwen
  - If missing: raise a clear error with message `"Manual build log not found at <path>. Write the manual build log first, then run synthesis. See ADR-042."`
  - If present: proceed with synthesis, write to `aho-build-log-synthesis-<version>.md`
- Regression test `tests/test_build_log_first.py`:
  - Case 1: no manual log present → synthesis call raises the expected error
  - Case 2: manual log present → synthesis call succeeds and writes the synthesis file

**Success:**
- `pytest tests/test_build_log_first.py -v` passes
- Attempting `./bin/aho iteration build-log 0.1.99` (throwaway) without a manual file returns the clear error

### W5 — Dogfood + close (60 min)

**Goal:** Run the fixed loop against 0.1.10 itself. Verify all six 0.1.9 conditions are resolved.

**Deliverables:**
- Kyle writes the manual build log at `docs/iterations/0.1.10/aho-build-log-0.1.10.md` workstream-by-workstream during W0-W4 (not a separate step — this IS the workstream-by-workstream record)
- `./bin/aho iteration build-log 0.1.10` generates `aho-build-log-synthesis-0.1.10.md`
- `./bin/aho iteration report 0.1.10` generates the report
- `./bin/aho doctor postflight 0.1.10` runs structural gates
- `./bin/aho iteration close` generates run report and bundle (does NOT `--confirm`)

**Verification checks (all six must pass):**

1. Bundle §1 Design contains the 0.1.10 design doc content (not `(missing)`) — confirms Condition 1 fix landed
2. Bundle §2 Plan contains the 0.1.10 plan content (not `(missing)`)
3. Bundle §3 Build Log contains the manual build log as the primary section AND the synthesis as secondary with a divider
4. Bundle §22 Agentic Components shows ≥6 components with `aho-*` naming (specifically includes aho-cli, openclaw, nemoclaw, structural-gates, evaluator, qwen-client) — confirms Condition 2 fix landed
5. `docs/iterations/0.1.99/` does not exist on disk — confirms Condition 4 fix landed
6. Running the 0.1.9 bundle retroactively through the fixed generator (or re-running `./bin/aho iteration bundle 0.1.9`) shows §1, §2, §3 populated — confirms the W1 filesystem rename fix works for historical lookups

**Success:** All six verification checks pass.

### W6 — Project root rename (conditional, 30 min)

**Goal:** If W5 closes cleanly with all six conditions resolved, rename `~/dev/projects/iao/` to `~/dev/projects/aho/` as the final workstream of the rename arc. If ANY W5 verification fails, SKIP W6 — project root rename carries to the next run.

**Deliverables (only if W5 fully passes):**
- Exit the current tmux session (the rename cannot happen while the shell is cwd'd inside the renaming directory)
- From a shell outside the project: `mv ~/dev/projects/iao ~/dev/projects/aho`
- Re-enter the new path
- Verify `./bin/aho --version` still works
- Update `.gitignore` if any path references were absolute
- Update any shell aliases or fish abbreviations pointing at the old path (Kyle manual step, noted as a capability-gap interrupt)

**Success:**
- `test -d ~/dev/projects/aho && ! test -d ~/dev/projects/iao` passes
- `./bin/aho --version` returns `aho 0.1.10` from within `~/dev/projects/aho`
- The rename arc is declared complete

**Scope boundary:** This workstream is the ONLY place in 0.1.10 where the directory path `~/dev/projects/iao/` becomes `~/dev/projects/aho/`. All prior workstreams operate under the old path.

---

## §5. Risks and mitigations

1. **Risk: W1 rename breaks internal cross-references inside the three `iao-*` files.** Mitigation: after renaming, `rg` for cross-references inside the files; update any that reference their own old names. The files are design/plan/build-log — most cross-refs are to code, not to themselves.

2. **Risk: W2 sed sweep matches strings that look like `iao-*` but aren't instrumentation component names.** Mitigation: use a targeted pattern `rg '"iao-[a-z-]+"'` with double-quote boundaries to find ONLY string literals, and review before applying sed. Manual inspection of each match.

3. **Risk: W3 finds that OpenClaw/NemoClaw/structural-gates instrumentation was never wired correctly, not just missing from §22.** Mitigation: if audit reveals missing instrumentation, treat it as a restoration task using the 0.1.8 W5 code as reference. If the restoration is non-trivial, ship partial (at least aho-cli renamed) and carry the rest to the next run.

4. **Risk: W4 raises the loop error during W5 dogfood because Kyle hasn't written the manual build log progressively.** Mitigation: the design explicitly says Kyle writes the manual build log workstream-by-workstream during W0-W4. If the executor is Gemini/Claude Code, the "manual" log is whatever the executor writes with each workstream completion — same pattern as prior runs, just enforced at synthesis time.

5. **Risk: W6 rename breaks git history or working tree state.** Mitigation: the `mv` is a directory rename, not a git operation. Git sees it as the project root moving on the filesystem; the `.git/` directory moves with it. No git history impact. Kyle may need to update shell aliases and any absolute path references in configs — called out as a capability-gap interrupt.

6. **Risk: W6 runs while a tmux session is cwd'd inside the old directory and fails.** Mitigation: W6 explicitly exits the tmux session before invoking `mv`. Executor pauses with a capability-gap interrupt for Kyle to confirm the session is closed, then Kyle runs the `mv` and the executor resumes.

---

## §6. Scope boundaries — what 0.1.10 does NOT do

- **No new amendments from the post-0.1.8 review.** Nemotron-as-evaluator, pre/post-flight checks in run report, token-spend tracking, scoring registry, run-file filename rename — all candidates for future runs. Not 0.1.10.
- **No new workstream additions beyond the six listed.** If a new issue surfaces during execution, log it as a discrepancy in the build log and carry forward to the next run.
- **No aho git repo creation.** The repo directory stays `~/dev/projects/iao/` OR becomes `~/dev/projects/aho/` depending on W6, but the git history is unchanged. No new git init, no SOC-Foundry push, no aho scaffold as a separate project.
- **No CLAUDE.md or GEMINI.md updates during the run.** Those are per-phase universal files; they update at phase boundaries, not mid-phase.
- **No historical file rewrites.** `docs/iterations/0.1.2/` through `docs/iterations/0.1.8/` keep their `iao-*` prefixes as historical records.

---

## §7. Graduation criteria

**GRADUATE** — all six conditions from 0.1.9 resolved, all six W5 verification checks pass, W6 project root rename completed cleanly. Rename arc declared complete. Kyle signs off all five boxes including "satisfied with this iteration's output".

**GRADUATE WITH CONDITIONS** — five of six 0.1.9 conditions resolved, W5 verification has ≤1 failure, W6 conditionally skipped or deferred. Kyle decides sign-off #5 based on how close to clean the outcome is.

**DO NOT GRADUATE** — fewer than five conditions resolved, OR W5 shows §22 still regressed, OR bundle generator still reports `(missing)` for core artifacts, OR W4 error handling fails and Qwen synthesis still ships without manual grounding. Roll back via backup, re-attempt.

---

## §8. Sign-off

- [ ] I have reviewed the bundle
- [ ] I have reviewed the build log (manual, per ADR-042)
- [ ] I have reviewed the synthesis build log (if present, per ADR-042)
- [ ] I have reviewed the report
- [ ] I have answered all agent questions
- [ ] I am satisfied with this iteration's output

---

*Design generated 2026-04-10, aho 0.1.10 planning*
