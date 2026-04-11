# Run File — aho 0.1.11

**Generated:** 2026-04-10T21:13:24Z
**Iteration:** 0.1.11
**Phase:** 0

## About this Report

This run file is a canonical iteration artifact produced during the `iteration close` sequence. It serves as the primary feedback interface between the autonomous agent and the human supervisor. Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the iteration's ground truth: the execution checkpoint and the extracted agent questions.

---

## Workstream Summary

| Workstream | Status | Agent | Wall Clock |
|---|---|---|---|
| W0 | pass | Gemini CLI | - |
| W1 | pass | Gemini CLI | - |
| W2 | pass | Gemini CLI | - |
| W3 | pass | Gemini CLI | - |
| W4 | pass | Gemini CLI | - |

---

## Agent Questions for Kyle

(none — no questions surfaced during execution)

---

## Kyle's Notes for Next Iteration

### Verdict: GRADUATE WITH CONDITIONS

0.1.11 landed the primary objective: the run file filename rename. `aho-run-0.1.11.md` exists, the generator writes the new name, postflight modules `run_complete` and `run_quality` are renamed, the prompt template is `run.md.j2`, and the bundle §5 references the new name. Test suite hygiene (W2) and the information-density detector (W3) also landed. The project root rename to `~/dev/projects/aho` happened during this run (Kyle executed it manually, the editable pip install was reinstalled, `./bin/aho` works from the new path).

Four conditions worth naming. None are blockers.

### Conditions carried forward

**Condition 1 — Build log synthesis file is empty.** The Qwen synthesis loop went into an evaluator rejection cycle for ~2 hours before Kyle killed it. The loop kept producing output that referenced real files (`src/aho/feedback/run_report.py` → now `run.py`, `run_report_complete.py` → now `run_complete.py`) and the evaluator kept flagging them as hallucinated because the W7 dynamic baseline from 0.1.10 loaded BEFORE 0.1.11 W1 renamed the files. The baseline knew the old names and treated the Qwen output's correct new names as wrong, then Kyle's plan doc referenced both old and new names (old as "renaming from", new as "renaming to") which made everything flagged regardless. This is **aho-G060** — register it. Fix for next run: evaluator reloads baseline immediately before each synthesis evaluation instead of at module init.

**Condition 2 — Kyle had to manually scrub the build log and event log to work around aho-G060.** The sed workaround block from Kyle's close sequence replaced literal file paths with prose ("the run generator", "the new density test") to get synthesis past the evaluator. This is a symptom of Condition 1, not a separate problem, but it's worth naming because any future run where the evaluator's baseline gets out of sync will hit the same wall.

**Condition 3 — `docs/harness/model-fleet.md` still says "IAO Model Fleet" and references the old project name.** It's one of three harness docs that the W1 sweep in 0.1.9 didn't update. `base.md` and `agents-architecture.md` both use `src/aho/` correctly. `model-fleet.md` is stale — version header says "0.1.4", title says "IAO", and prose references "IAO utilizes". Small cleanup for the next run. Historical phase charter (`iao-phase-0.md`) stays as-is because it's a historical document.

**Condition 4 — smoke_instrumentation.py event logging under wrong iteration.** Kyle's workaround sed also rewrote `"iteration": "0.1.10"` to `"iteration": "0.1.11"` in the event log. Root cause: smoke_instrumentation.py reads the iteration from an env var or hardcoded value, not from `.aho-checkpoint.json`. This is **aho-G061** — register it. Fix for next run: script reads iteration from checkpoint at runtime.

### What landed cleanly

**W0 Environment hygiene.** Project root was still at `~/dev/projects/iao` when W0 ran. Logged as discrepancy, proceeded with the old path. Kyle executed the rename manually mid-run and reinstalled the pip package from the new location.

**W1 Run file filename rename.** The core deliverable. Generator output filename changed to `aho-run-{version}.md`. Postflight modules renamed: `run_report_complete` → `run_complete`, `run_report_quality` → `run_quality`. Prompt template renamed: `run-report.md.j2` → `run.md.j2`. Bundle §5 correctly references the new name. Historical files in 0.1.9/0.1.10 keep their `aho-run-report-*` names as historical records.

**W2 Test suite hygiene.** Both pre-existing failures fixed. `test_secrets_backends` age test skips when no TTY. `test_artifacts_loop` "Phase 0" expectation updated to match current loop output.

**W3 Information density detector.** Implemented as a secondary signal in `repetition_detector.py`. Flags degenerate output when unique/total token ratio drops below 10% over a 500-token window. Catches the "Wait, checking..." pattern that evaded the rolling-window detector in 0.1.10. Two new tests in `test_density_check.py` pass.

**W4 Dogfood.** All six verification checks passed. Manual build log present. Run file named correctly. Bundle §5 references new name. No lingering `run-report` strings in source. Test suite green. §22 shows 6 components. The synthesis file is empty but that's Condition 1, not a verification failure — ADR-042 makes synthesis optional.

### Direction for next run

1. Fix aho-G060: evaluator reloads baseline before each evaluation
2. Fix aho-G061: smoke_instrumentation.py reads iteration from checkpoint
3. Update `docs/harness/model-fleet.md` to aho naming and current version
4. Project root rename is done — verify `~/dev/projects/aho` is canonical going forward
5. Consider: can we teach the evaluator to handle "old name → new name" references during a rename run? Or should rename runs explicitly exclude the evaluator from synthesis?

The rename arc is fully complete. Internal code is aho, filesystem root is aho, filenames are aho-run-*, all identifiers are ahomw-*. From 0.1.12 onward the scope opens up — no more rename baggage, no more carryover filename fixes.

---

## Reference: The Eleven Pillars

1. **Delegate everything delegable.** The paid orchestrator is the most expensive resource in the system. Any task that can run on a free local model must run on a free local model. The orchestrator decides; it does not execute. Drafting, classification, retrieval, validation, grading, routing all belong to the local fleet. The orchestrator's minutes are spent on judgment, scope, and novelty.
2. **The harness is the contract.** Agent instructions live in versioned harness files that change at phase or iteration boundaries, not in per-run markdown regenerated from scratch. The orchestrator points at the harness; it does not carry the contract in its own context. Projects run against harness overlays on a shared base.
3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out. The harness is artifact-agnostic at its core and specialized at its overlays.
4. **Wrappers are the tool surface.** Agents never call raw tools. Every tool is invoked through a `/bin` wrapper, versioned with the harness and instrumented for the event log.
5. **Three octets, three meanings: phase, iteration, run.** Phase is strategic scope. Iteration is tactical scope. Run is execution instance. Every artifact carries the full phase.iteration.run label.
6. **Transitions are durable.** Moving between phases, iterations, or runs writes state to a durable artifact before the transition is considered complete. Every gate is a write point. No implicit state.
7. **Generation and evaluation are separate roles.** The model that produced an artifact is never the model that grades it.
8. **Efficacy is measured in cost delta.** Every run records orchestrator token cost, local fleet compute time, wall clock, delegate ratio, and quality signal.
9. **The gotcha registry is the harness's memory.** Every failure mode lands in the registry.
10. **Runs are interrupt-disciplined, not interrupt-free.** No mid-run prompts for preference. The single exception: unavoidable capability gaps — routed through OpenClaw, logged, resumed from last checkpoint.
11. **The human holds the keys.** No agent writes to git. No agent merges. No agent pushes. No agent manages secrets.

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Run file generated 2026-04-10T21:13:24Z*
