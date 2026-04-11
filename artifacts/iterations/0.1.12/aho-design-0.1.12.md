# aho — Design 0.1.12

**Run:** 0.1.12
**Phase:** 0
**Theme:** Evaluator baseline reload + smoke script checkpoint-awareness + model-fleet.md cleanup
**Predecessor:** 0.1.11 (graduated with conditions)
**Authored:** 2026-04-10

---

## §1. Why 0.1.12 exists

0.1.11 graduated, the rename arc is done, and the project root is now `~/dev/projects/aho`. Four conditions carried forward, all of them targeted fixes for gotchas that surfaced during 0.1.11's execution. This is a narrow maintenance run — four workstreams, roughly 2.5 hours wall clock.

The big structural work (rename, synthesis evaluator, §22 instrumentation, filename conventions) is behind us. 0.1.12 clears the last four nits from 0.1.11 and positions us for broader scope in 0.1.13+.

---

## §2. Workstreams

### W0 — Environment hygiene (15 min)

**Goal:** Verify project root is `~/dev/projects/aho`, bump checkpoint and version to 0.1.12, initialize manual build log, backup files W1-W3 will modify.

**Success:** `command pwd` returns `/home/kthompson/dev/projects/aho`, `./bin/aho --version` returns `aho 0.1.12`.

### W1 — Evaluator baseline reload (aho-G060) (60 min)

**Goal:** Fix the evaluator baseline staleness that caused 0.1.11's 2-hour Qwen rejection loop. The dynamic baseline from 0.1.10 W7 loads at module init, so files created or renamed during the current run are invisible to the evaluator.

**Deliverables:**
- `src/aho/artifacts/evaluator.py`: replace the init-time baseline load with a reload-on-evaluate pattern. Options:
  - **Option A (simple):** Call `get_allowed_scripts()` and `get_allowed_cli_commands()` inside `evaluate_text()` on every invocation. Caching is lost but correctness is restored.
  - **Option B (cached with invalidation):** Keep the cache but add a file-mtime check against `scripts/` and `src/aho/cli.py`. If either changed since last load, invalidate.
  - Recommendation: Option A. Simpler, slower by ~10ms per evaluation, correct in the presence of mid-run changes.
- Register **aho-G060** in `data/gotcha_archive.json`: *"Evaluator dynamic baseline loads at init, misses files created or renamed mid-run. Fix: reload baseline before each synthesis evaluation."*
- Regression test `tests/test_evaluator_reload.py`:
  - Create a file `scripts/aho_g060_test.py` at test time
  - Call `evaluate_text()` with content referencing that file
  - Assert no "hallucinated script" error
  - Clean up

**Success:** `pytest tests/test_evaluator_reload.py -v` passes. A file created 5 seconds ago is recognized by the evaluator in the next `evaluate_text()` call.

### W2 — smoke_instrumentation checkpoint awareness (aho-G061) (30 min)

**Goal:** Fix the iteration-stamp bug where `smoke_instrumentation.py` logs events under the previous iteration's version.

**Deliverables:**
- `scripts/smoke_instrumentation.py`: read iteration from `.aho-checkpoint.json` at script start, set it on every `log_event` call. Remove any env var or hardcoded fallback that causes the wrong value.
- Register **aho-G061** in `data/gotcha_archive.json`: *"Scripts that emit events should read the current iteration from .aho-checkpoint.json, not from env vars or hardcoded values."*
- Smoke-test the smoke script: bump checkpoint to 0.1.12, run the script, verify events in the log are stamped `"iteration": "0.1.12"`.

**Success:** Running the smoke script after checkpoint bump produces events with the correct iteration stamp.

### W3 — model-fleet.md harness doc cleanup (20 min)

**Goal:** Update `docs/harness/model-fleet.md` from its stale 0.1.4 / "IAO" state to current aho naming and current version.

**Deliverables:**
- Title: "IAO Model Fleet" → "aho Model Fleet"
- Version header: `0.1.4` → `0.1.12`
- All prose references to "IAO" as an identifier → "aho". Prose describing "iao" as historical name can stay if it refers to the historical project.
- Section 3 "Deployment and Orchestration": `iao CLI` → `aho CLI`
- Section 6 "Future Extensions": 0.1.5-era speculation — either delete (outdated) or replace with current roadmap hints
- Section 5 "Security and Privacy": references "the Trident" which is retired from the pillar set. Rephrase to reference Pillars 1 (delegate) and 8 (cost delta) instead.
- Historical phase charter `iao-phase-0.md` stays unchanged — it's a historical document

**Success:** `rg -n "IAO" docs/harness/model-fleet.md` returns 0 matches (or only within historical context prose).

### W4 — Dogfood + close (45 min)

**Goal:** Run the loop against 0.1.12. Verify aho-G060 fix works end-to-end.

**Deliverables:**
- Manual build log present
- `./bin/aho iteration build-log 0.1.12` — should NOT hit the old file-rejection loop because of W1's reload fix
- `./bin/aho iteration report 0.1.12`
- `./bin/aho iteration close`

**Verification checks:**
1. Synthesis file at `docs/iterations/0.1.12/aho-build-log-synthesis-0.1.12.md` is non-empty (proves aho-G060 fix works)
2. Event log events during W4 are stamped `"iteration": "0.1.12"` (proves aho-G061 fix works)
3. `rg "IAO" docs/harness/model-fleet.md` returns 0 or only historical (proves W3 landed)
4. §22 shows ≥6 components
5. Bundle §3 has manual build log
6. Run file is `aho-run-0.1.12.md`
7. `pytest tests/ -v` shows 0 failures

**Success:** 7 of 7 checks pass.

---

## §3. Graduation criteria

**GRADUATE** — All 7 verification checks pass, no new conditions.
**GRADUATE WITH CONDITIONS** — 5-6 of 7 checks pass, conditions documented.
**DO NOT GRADUATE** — aho-G060 fix doesn't work (synthesis loop returns), or <5 checks pass.

---

## §4. Scope boundaries

- No new features. No amendments. No post-0.1.8 review items (Nemotron evaluator, token tracking, scoring registry).
- CLAUDE.md / GEMINI.md unchanged — per-phase, not per-run.
- Historical files (phase charter, 0.1.2-0.1.10 artifacts) unchanged.
- No git ops.

---

## §5. Sign-off

- [ ] I have reviewed the bundle
- [ ] I have reviewed the build log
- [ ] I have reviewed the report
- [ ] I have answered all agent questions
- [ ] I am satisfied with this iteration's output
