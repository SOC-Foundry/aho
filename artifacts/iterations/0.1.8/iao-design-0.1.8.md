# iao — Design 0.1.8

**Iteration:** 0.1.8
**Phase:** 0 (UAT lab for aho)
**Theme:** Pillar rewrite + hardcoded-pillar cleanup + 0.1.7 carryover resolution
**Machine:** NZXTcos
**Predecessor:** 0.1.7 (graduated with conditions 2026-04-10)
**Authored:** 2026-04-10 (post-0.1.7 close)

---

## §1. Phase 0 Position

iao is in Phase 0. Under the three-lab framing landed post-0.1.7:

- **kjtcom** is the dev lab — production location intelligence platform where patterns were discovered under fire
- **iao** is the UAT lab — where patterns get proven in isolation before being ported to production
- **aho** is production — a new repo to be scaffolded under `~/dev/projects/aho/` starting around 0.1.12, where proven patterns land in a clean implementation with no iaomw-era scar tissue

Phase 0 is pattern-proving. Graduation from Phase 0 means the pattern set is ready for aho port, not a public push to GitHub. Every iao iteration from 0.1.8 forward is proving patterns for aho, not production-shipping in iao itself. The rename IAO → AHO happens inside iao first as a dedicated iteration (planned ~0.1.9) before the aho scaffold is stood up.

0.1.8 is the pillar rewrite iteration. It lands the new eleven-pillar vocabulary in the living harness and in every hardcoded Python location that currently carries the retired `iaomw-Pillar-1..10` block. It also clears five conditions carried from 0.1.7's GRADUATE WITH CONDITIONS close. No rename. No `/bin` wrapper POC. No living harness file split. No aho scaffold.

---

## §2. Why 0.1.8 Exists

### 2.1 — Carryover conditions from 0.1.7

0.1.7 graduated with conditions. Five findings must be resolved in 0.1.8:

**Condition 1 — Split-agent language regression in §3 Build Log Synthesis.** Qwen's synthesis pass generated *"The iteration followed the bounded sequential pattern with split-agent execution (Gemini W0-W5, Claude W6-W7)"* despite the W3 evaluator baseline listing "split-agent" as a hallucination trigger. The run report workstream summary shows W0–W7 and W9 as `gemini-cli` and W8 as `unknown` — no Claude involvement actually happened. Qwen pattern-matched on stale RAG context and invented a split that wasn't there. The W3 evaluator either isn't wired to the synthesis pass or its retired-patterns check is incomplete. 0.1.8 W4 fixes the wiring.

**Condition 2 — §22 Agentic Components thin instrumentation.** Only two components are populated in the 0.1.7 bundle's §22: `nemotron-client` (1 task, classify) and `qwen-client` (8 tasks, generate). Missing: the iao CLI itself, OpenClaw/NemoClaw smoke-test invocations, the evaluator, the repetition detector, the structural gates, the subprocess sandbox, any MCP invocations. 0.1.7 W7 shipped the section infrastructure and the event-log schema; 0.1.8 W5 wires the remaining components.

**Condition 3 — W8 listed as `unknown` agent in run report workstream summary.** Every other workstream shows `gemini-cli`; W8 shows `unknown`. Close-sequence instrumentation gap in the path that determines the executor for each workstream. 0.1.8 W6 fixes it.

**Condition 4 — `scripts/query_registry.py` is a legitimate shim, not a hallucination.** Post-close audit revealed it as a 6-line Python wrapper around `iao.registry.main`, tracked by `src/iao/doctor.py` at line 70 as an expected shim alongside `scripts/build_context_bundle.py`. Prior agent briefs and `data/known_hallucinations.json` were wrong to list it as forbidden. 0.1.8 W3 updates the baseline. 0.1.8 W7 appends ADR-041 to base.md documenting the resolution.

**Condition 5 — Stale pillar phrasing hardcoded in four locations.** Post-close `rg` found:

1. `docs/harness/base.md` line 24 — *"iaomw-Pillar-3 (Diligence) - First action: query_registry.py"* — the living harness doc carries the retired phrasing that caused the original 0.1.5 hallucination
2. `src/iao/feedback/run_report.py` lines 103-112 — the entire `iaomw-Pillar-1..10` list as a hardcoded Python list. Every generated run report verbatim-reproduces the retired block from this source
3. `src/iao/artifacts/evaluator.py` line 21 — `PILLAR_ID_RE = re.compile(r"(iaomw-Pillar-\d+)")` encodes the retired naming convention
4. `src/iao/artifacts/templates.py` line 40 — template regex matches the retired pillar block format

Condition 5 is the most consequential finding. Kate-editing the run report doesn't help — the next run regenerates it from Python. The 0.1.7 run report Kyle just closed STILL contains the old pillar block because the generator ignored his edits. The fix is to centralize pillar content in `docs/harness/base.md` (W1) and rewrite `run_report.py` to read from there (W2). W3 cleans up the evaluator and template regex.

### 2.2 — Direction shift already landed

The strategic reframe that emerged from the post-0.1.7 review is captured in the updated CLAUDE.md and GEMINI.md. 0.1.8 operates under that reframe:

- Rename IAO → AHO (Agentic Harness Orchestration) — dedicated iteration, ~0.1.9. **Not 0.1.8.**
- Package-first delivery via AUR — ~0.1.10+. **Not 0.1.8.**
- Living harness architecture (`harness-base.md`, `harness-tools.md`, `harness-gotchas.md`, `harness-retired.md`, `harness-phase-{N}.md`) — ~0.1.11. **Not 0.1.8.**
- aho repo scaffold — ~0.1.12. **Not 0.1.8.**
- First aho code port — 0.2.0. **Not 0.1.8.**

0.1.8 is scoped to "clear the 0.1.7 conditions, rewrite the pillars, de-hardcode the pillar content from Python." Anything larger waits for its own iteration.

---

## §3. The Eleven Pillars

These pillars supersede the prior `iaomw-Pillar-1..10` numbering. They govern iao (UAT) work and aho (production) work alike. After 0.1.8 W1 lands, they live authoritatively in `docs/harness/base.md` and are read from there by Python code that needs to quote them.

1. **Delegate everything delegable.** The paid orchestrator is the most expensive resource in the system. Any task that can run on a free local model must run on a free local model. The orchestrator decides; it does not execute. Drafting, classification, retrieval, validation, grading, routing all belong to the local fleet. The orchestrator's minutes are spent on judgment, scope, and novelty.

2. **The harness is the contract.** Agent instructions live in versioned harness files that change at phase or iteration boundaries, not in per-run markdown regenerated from scratch. The orchestrator points at the harness; it does not carry the contract in its own context. Projects run against their own harness overlays on top of a shared base.

3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out. Code, reports, schemas, analyses, migrations, audits, designs — all artifacts. The harness is artifact-agnostic at its core and artifact-specialized at its overlays.

4. **Wrappers are the tool surface.** Agents never call raw tools. Every tool is invoked through a `/bin` wrapper. Wrappers are versioned with the harness, instrumented for the event log, and replayable from recorded inputs.

5. **Three octets, three meanings: phase, iteration, run.** Phase is strategic scope. Iteration is tactical scope. Run is execution instance. Every artifact carries the full phase.iteration.run label.

6. **Transitions are durable.** Moving between phases, iterations, or runs writes state to a durable artifact before the transition is considered complete. Every gate is a write point. No implicit state.

7. **Generation and evaluation are separate roles.** The model that produced an artifact is never the model that grades it. Drafter and reviewer are different agents behind different wrappers with different prompts and ideally different underlying weights.

8. **Efficacy is measured in cost delta.** Every run records orchestrator token cost, local fleet compute time, wall clock, delegate ratio (fraction of decisions that never reached the orchestrator), and output quality signal. Numbers ship with the run report.

9. **The gotcha registry is the harness's memory.** Every failure mode lands in the registry. A mature harness has more gotchas than an immature one — gotcha count is the compound-interest metric.

10. **Runs are interrupt-disciplined, not interrupt-free.** Once a run launches, agents do not ping for preference, clarification, or approval. The single exception is unavoidable capability gaps (sudo, credentials, physical access) — routed through OpenClaw to a defined notification channel, logged as a first-class event, resumed from the last durable checkpoint.

11. **The human holds the keys.** No agent writes to git. No agent merges. No agent pushes. No agent manages secrets. No wrapper surfaces `git commit` or `git push` under any role.

### 3.1 — On the retired Trident

The prior `iaomw-Pillar-1 (Trident: Cost/Delivery/Performance)` framing is absorbed into Pillar 1 (Delegate — the cost lever), Pillar 8 (Cost delta — the cost signal), and implicitly the wall-clock measurement in Pillar 8. The standalone Trident construct is retired as a separate element in 0.1.8. If a future iteration wants to reintroduce it as a decision framework parallel to the pillars, that's a conceptual redesign and belongs in aho, not in iao cleanup work.

---

## §4. Project State Going Into 0.1.8

- **iao version on disk:** 0.1.7 (post-close)
- **Last completed iteration:** 0.1.7 (graduated with conditions)
- **Python:** 3.14.3
- **Shell:** fish 4.6.0
- **Ollama models:** qwen3.5:9b, nemotron-mini:4b, nomic-embed-text, haervwe/GLM-4.6V-Flash-9B
- **ChromaDB archives:** iaomw_archive (17 docs), kjtco_archive (282 docs), tripl_archive (144 docs)
- **OpenClaw/NemoClaw:** Ollama-native (rebuilt 0.1.7 W8). No open-interpreter/tiktoken/Rust deps.
- **Streaming Qwen client:** active (0.1.7 W1)
- **Repetition detector:** active (0.1.7 W1)
- **Word-count gates:** inverted to maximums (0.1.7 W2)
- **Anti-hallucination evaluator:** active on design/plan drafts only (0.1.7 W3). Not wired to synthesis pass — this is carryover #1.
- **Rich structured seed:** available (0.1.7 W4)
- **RAG freshness weighting:** active (0.1.7 W5)
- **Two-pass generation:** behind `--two-pass` flag (0.1.7 W6)
- **BUNDLE_SPEC:** 22 sections (0.1.7 W7)
- **§22 Agentic Components:** infrastructure present, 2 of ~7 components wired — carryover #2
- **Base harness:** contains stale Pillar 3 text — carryover #5a
- **Run report generator:** contains hardcoded old pillar list — carryover #5b
- **Evaluator + templates:** contain old pillar regex — carryover #5c,d
- **`scripts/query_registry.py`:** exists as legitimate shim, tracked by `src/iao/doctor.py` line 70
- **`.iao.json` phase:** 0
- **Retired patterns:** split-agent handoff (0.1.4), open-interpreter (0.1.7), the ten-pillar `iaomw-Pillar-1..10` block (0.1.8, this iteration)
- **Agent briefs:** CLAUDE.md and GEMINI.md already updated post-0.1.7 to the eleven-pillar vocabulary and three-lab framing; 0.1.8 does not re-edit them

---

## §5. Workstreams

Nine workstreams, W0 through W8. Wall clock target: ~7:35 soft cap, no hard cap.

### W0 — Environment Hygiene (15 min)

**Goal:** Transition cleanly from 0.1.7 to 0.1.8.

**Deliverables:**
- Backup of state files that 0.1.8 will modify (base.md, run_report.py, evaluator.py, templates.py, known_hallucinations.json) to `~/dev/projects/iao.backup-pre-0.1.8/`
- `.iao.json` iteration field bumped to `0.1.8`
- `.iao-checkpoint.json` initialized for 0.1.8
- `docs/iterations/0.1.8/` directory created
- Build log initialized with W0 entry

**Success:**
- `./bin/iao --version` returns `iao 0.1.8`
- `jq .iteration .iao-checkpoint.json` returns `"0.1.8"`
- `test -f docs/iterations/0.1.8/iao-build-log-0.1.8.md` passes
- Backup directory contains all five expected files

### W1 — Base Harness Pillar Rewrite (60 min)

**Goal:** Replace the `iaomw-Pillar-1..10` block in `docs/harness/base.md` with the eleven aho pillars. Fix the stale Pillar 3 phrasing that references `query_registry.py`. Preserve ADRs and gotcha index sections untouched.

**Deliverables:**
- New pillar block in base.md (eleven pillars, authoritative text from §3 of this design)
- No lingering `iaomw-Pillar-` references in base.md
- A note at the top of base.md explaining the 0.1.8 rewrite and pointing at this design doc
- Structural verification: `rg -c "iaomw-Pillar-" docs/harness/base.md` returns 0

**Success:**
- `grep -c "Delegate everything delegable" docs/harness/base.md` returns ≥1
- `rg -c "iaomw-Pillar-" docs/harness/base.md` returns 0
- `rg -c "query_registry" docs/harness/base.md` returns 0 (or only within ADR context, not Pillar 3)

### W2 — run_report.py De-hardcoding (75 min)

**Goal:** Stop hardcoding pillars as a Python list in `src/iao/feedback/run_report.py`. Load the pillar block from `docs/harness/base.md` at runtime. Cache in-process so every run report in the same process uses the same snapshot.

**Deliverables:**
- New function `_load_pillars_from_base(base_md_path) -> list[str]` in run_report.py
- In-process cache `_PILLARS_CACHE` and accessor `get_pillars()`
- Hardcoded `PILLARS` list removed, replaced with `get_pillars()` call
- Pre-flight check in `src/iao/preflight/checks.py`: if base.md pillar section can't be parsed, fail pre-flight loudly before any artifact generation
- Unit test `tests/test_run_report_pillars.py` with three cases:
  1. `get_pillars()` returns exactly 11 entries
  2. Pillar 1 contains "Delegate everything delegable"
  3. No entry contains "iaomw-Pillar-"

**Success:**
- `pytest tests/test_run_report_pillars.py -v` passes
- Running `./bin/iao iteration report 0.1.99` in a throwaway directory produces a report containing eleven-pillar text, not the ten

### W3 — evaluator.py and templates.py Regex Cleanup (45 min)

**Goal:** Remove the pillar-specific regex from the evaluator and the pillar-block template regex. Update `data/known_hallucinations.json` to remove `query_registry.py` from the forbidden list (carryover #4) and add the retired `iaomw-Pillar-N` strings as forbidden instead.

**Deliverables:**
- `PILLAR_ID_RE` and its validation callers removed from `src/iao/artifacts/evaluator.py`
- Pillar-block template regex removed from `src/iao/artifacts/templates.py`
- `data/known_hallucinations.json` updated:
  - `query_registry.py` and related entries removed from forbidden list
  - `iaomw-Pillar-1` through `iaomw-Pillar-10` added to forbidden list
- Updated `tests/test_evaluator.py` if pillar-ID assertions exist

**Success:**
- `rg "iaomw-Pillar" src/iao/` returns only comments explaining the removal (ideally zero matches)
- `rg "query_registry" data/known_hallucinations.json` returns zero matches
- `pytest tests/test_evaluator.py -v` passes

### W4 — Evaluator Wired to Synthesis Pass (60 min)

**Goal:** Fix carryover #1. The 0.1.7 W3 evaluator runs on design and plan drafts but does not run on Qwen's synthesis passes for the build log and report. Wire it in.

**Deliverables:**
- Evaluator call after synthesis generation for build log and report in `src/iao/artifacts/loop.py`
- On reject: log to event log (`data/iao_event_log.jsonl`) with type `synthesis_evaluator_reject`, retry once with diagnostic feedback, accept on second try even if still flagged (log as carryover)
- Regression test `tests/test_synthesis_evaluator.py` using the 0.1.7 build log synthesis paragraph with split-agent language; assert evaluator rejects

**Success:**
- `pytest tests/test_synthesis_evaluator.py -v` passes
- Running the evaluator on the 0.1.7 bundle's §3 build log synthesis paragraph returns severity=reject with "split-agent" in the errors list

### W5 — §22 Instrumentation Expansion (90 min, partial ship acceptable)

**Goal:** Fix carryover #2. Wire six currently-unwired components to the event log so the next bundle's §22 shows full coverage.

**Deliverables (wire each of these to `data/iao_event_log.jsonl`):**
- `src/iao/cli.py` — log_event on every iao CLI subcommand invocation with type=`cli_invocation`, name=`<subcommand>`
- `src/iao/agents/openclaw.py` — log_event on session start/end and every chat/execute_code call
- `src/iao/agents/nemoclaw.py` — log_event on every dispatch with classification result
- `src/iao/artifacts/evaluator.py` — log_event on every evaluate_text call with severity
- `src/iao/artifacts/repetition_detector.py` — log_event on every DegenerateGenerationError raise
- `src/iao/postflight/structural_gates.py` — log_event on every gate check with pass/fail

**Smoke test:** `scripts/smoke_instrumentation.py` runs a minimal invocation of each component and verifies the event log has ≥6 unique component names.

**Partial-ship criterion:** At 60 minutes elapsed, if fewer than 6 components are wired, ship what's wired, log the rest as discrepancies in the build log, continue to W6. Any unwired component carries to 0.1.9.

**Success:**
- `jq '.component' data/iao_event_log.jsonl | sort -u | wc -l` returns ≥6 after smoke test runs
- `python3 scripts/smoke_instrumentation.py` exits 0

### W6 — W8 Agent Instrumentation Fix (30 min)

**Goal:** Fix carryover #3. The 0.1.7 run report workstream summary showed `unknown` for W8's agent column. Fix the lookup so every workstream has a concrete agent name.

**Deliverables:**
- Trace in `src/iao/feedback/run_report.py` of how the agent column is populated
- Fallback: read `IAO_EXECUTOR` env var when checkpoint has no agent for a workstream
- Update `src/iao/artifacts/loop.py` to write the agent value to the checkpoint at the start of each workstream
- Unit test `tests/test_workstream_agent.py` with a fixture that sets `IAO_EXECUTOR` and asserts no `unknown` rows

**Success:**
- `pytest tests/test_workstream_agent.py -v` passes
- Running the 0.1.8 dogfood close in W8 produces a run report workstream summary with zero `unknown` agent values

### W7 — Baseline Updates for query_registry.py (20 min)

**Goal:** Fix carryover #4. Append ADR-041 to base.md documenting that `scripts/query_registry.py` is a legitimate shim. Verify no lingering "forbidden" references remain.

**Deliverables:**
- ADR-041 appended to `docs/harness/base.md`:
  - Status: Accepted
  - Date: 2026-04-10 (iao 0.1.8 W7)
  - Context: the 0.1.7 audit that revealed the shim
  - Decision: `scripts/query_registry.py` is legitimate; canonical invocation is still `iao registry query "<topic>"`
  - Consequences: baseline updates in W1 and W3 already land the fix
- Verification across baselines:
  - `rg "query_registry" data/known_hallucinations.json` → 0 matches
  - `rg "query_registry" docs/harness/base.md` → only within ADR-041 context
  - `rg "query_registry" CLAUDE.md GEMINI.md` → only within "Known shims" context (already done)

**Success:**
- ADR-041 present in base.md
- All three grep verifications pass

### W8 — Dogfood + Close (60 min)

**Goal:** Run the repaired loop against 0.1.8 itself. Verify the six success criteria below. Generate run report and bundle, leave in PENDING REVIEW state for Kyle's sign-off.

**Deliverables:**
- `./bin/iao iteration build-log 0.1.8` — generates iao-build-log-0.1.8.md via Qwen synthesis (now evaluated per W4)
- `./bin/iao iteration report 0.1.8` — generates iao-report-0.1.8.md via Qwen synthesis (now evaluated per W4)
- `./bin/iao doctor postflight 0.1.8` — runs structural gates and post-flight checks
- `./bin/iao iteration close` (WITHOUT `--confirm`) — generates iao-run-report-0.1.8.md and iao-bundle-0.1.8.md

**Verification checks (all six must pass):**

1. Run report contains "Delegate everything delegable" — confirms the eleven pillars landed via W2's read-through from base.md
2. Run report contains zero `iaomw-Pillar-` references — confirms the retired block is gone
3. Build log contains zero `split-agent` references — confirms W4's synthesis evaluator works
4. §22 Agentic Components shows ≥6 unique components — confirms W5's instrumentation expansion
5. Run report workstream summary shows zero `unknown` agents — confirms W6's fix
6. Bundle contains exactly 22 sections matching `^## §` — confirms structural integrity

**Success:** All six checks pass. Iteration is in PENDING REVIEW state awaiting Kyle's `./bin/iao iteration close --confirm`.

---

## §6. Risks and Mitigations

1. **Risk: W1's base.md splicing fails because the current pillar section doesn't match the expected format.**
   Mitigation: The W1 splicer uses a regex anchored on the `## ` header that contains "illar" (case-insensitive). If the parser can't locate the section, STOP and surface the error as a capability-gap interrupt — Kyle hand-edits base.md.

2. **Risk: W2's pillar parser breaks on future base.md format changes.**
   Mitigation: Unit test the parser against a frozen base.md fixture checked into `tests/fixtures/`. Any future base.md rewrite must update the fixture and re-run the test.

3. **Risk: W4's evaluator wiring causes every synthesis output to reject because the retired-patterns list is too strict after W3's additions.**
   Mitigation: Hard cap at 1 retry. After retry, accept the artifact and log as carryover. The evaluator never blocks the iteration, only warns.

4. **Risk: W5's instrumentation expansion touches six files. High surface area for bugs.**
   Mitigation: One file at a time. After each wire-up, run `scripts/smoke_instrumentation.py`. If a file breaks the smoke test, revert that one file and log as partial ship.

5. **Risk: W3's removal of `PILLAR_ID_RE` breaks an unrelated caller in evaluator.py.**
   Mitigation: `rg "PILLAR_ID_RE" src/ tests/` before deletion. Update or remove all callers in the same workstream.

6. **Risk: W8 dogfood regenerates the run report and finds the old pillar block still present because W2's parser has a silent bug.**
   Mitigation: Verification check 1 and 2 catch this explicitly. If either fails, STOP, log to build log, surface to Agent Questions. Do not attempt mid-W8 fixes.

7. **Risk: Kyle runs the executor before W0's backup completes and the rollback procedure has nothing to fall back to.**
   Mitigation: W0.2 is blocking; W1 does not begin until W0.6 completes. The executor is instructed to halt at W0 if any backup cp fails.

---

## §7. Scope Boundaries — What 0.1.8 Does NOT Do

- **No rename.** IAO → AHO identifier rename is 0.1.9. All identifiers remain `iaomw-*`, `.iao.json`, `src/iao/`, `./bin/iao`, `iaomw_archive` throughout 0.1.8.
- **No `/bin` wrapper POC.** That's 0.1.10.
- **No living harness file split.** 0.1.8 updates base.md content in place; it does not split base.md into `harness-base.md`, `harness-tools.md`, etc. That split is 0.1.11.
- **No aho directory scaffold.** That's 0.1.12.
- **No Riverpod upgrade.** That's a kjtcom concern, not iao.
- **No Telegram bridge bidirectional review.** That's a future iteration; Pillar 10 interrupt channel is implementation-level work for later.
- **No Trident reintroduction.** See §3.1 — retired in 0.1.8, may return in aho as a parallel framework.
- **No new ADRs beyond ADR-041.** Any larger architectural decision waits for its own iteration.
- **No modifications to CLAUDE.md or GEMINI.md.** Already updated post-0.1.7 to the eleven pillars and three-lab framing. They stay as-is.
- **No modifications to kjtcom.** kjtcom is the dev lab; iao is the UAT lab. Cross-project contamination is exactly what caused the 0.1.5 hallucination.

---

## §8. Iteration Graduation Recommendation Format

On W8 completion, the run report should produce one of:

**GRADUATE** — All nine workstreams complete, all six dogfood verification checks pass, no regressions introduced, §22 shows ≥6 components, build log synthesis is evaluator-clean.

**GRADUATE WITH CONDITIONS** — At least seven of nine workstreams complete, all five 0.1.7 carryover conditions addressed (even if their associated 0.1.8 workstream shipped partial), dogfood verification has no more than one failure, any new issues documented as 0.1.9 carryovers in Kyle's Notes.

**DO NOT GRADUATE** — Any 0.1.7 carryover not addressed, dogfood verification has two or more failures, the generated run report still contains `iaomw-Pillar-` literals, the generated build log contains `split-agent` literals, W1 or W2 did not land (pillar rewrite is the critical path for the whole iteration), or the W4 evaluator wiring is not in place.

---

## §9. Sign-off

- [ ] I have reviewed the bundle
- [ ] I have reviewed the build log
- [ ] I have reviewed the report
- [ ] I have answered all agent questions
- [ ] I am satisfied with this iteration's output

---

*Design doc generated 2026-04-10, iao 0.1.8 planning chat (Kyle + Claude web)*
