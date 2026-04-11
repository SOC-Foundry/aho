# Run Report — aho 0.1.10

**Generated:** 2026-04-10T16:33:27Z
**Iteration:** 0.1.10
**Phase:** 0

## About this Report

This run report is a canonical iteration artifact produced during the `iteration close` sequence. It serves as the primary feedback interface between the autonomous agent and the human supervisor. Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the iteration's ground truth: the execution checkpoint and the extracted agent questions.

The report includes a workstream summary, a collection of technical or procedural questions surfaced by the agent during execution, and a sign-off section for the reviewer.

---

## Workstream Summary

| Workstream | Status | Agent | Wall Clock |
|---|---|---|---|
| W0 | pass | Claude Code | - |
| W1 | pass | Claude Code | - |
| W2 | pass | Claude Code | - |
| W3 | pass | Claude Code | - |
| W4 | pass | Claude Code | - |
| W5 | pass | Claude Code | - |
| W6 | interrupt | Claude Code | - |

---

## Agent Questions for Kyle

(none — no questions surfaced during execution)

---

## Kyle's Notes for Next Iteration

### Verdict: GRADUATE

All six 0.1.9 conditions resolved. All six verification checks passed. §22 restored to 6 components with correct `aho-*` naming. Manual build log present and detailed. ADR-042 enforcement landed in code. The rename arc's internal work is complete — every identifier inside the repo is `aho`/`ahomw`. W6 project root rename surfaced as a capability-gap interrupt per Pillar 10 and is awaiting Kyle action.

This is the first clean graduation since 0.1.7. No conditions to carry — only the W6 directory rename which is Kyle's manual action, and the `run-report` → `run` filename rename which was missed across 0.1.9 and 0.1.10 (my fault, folding into the next run).

### Verification checks — all six pass

| # | Check | Result |
|---|---|---|
| V1 | §1 Design contains content | PASS |
| V2 | §2 Plan contains content | PASS |
| V3 | §3 Build Log has manual content with W0-W4 headers | PASS |
| V4 | §22 has ≥6 components with aho-* naming | PASS (aho-cli, evaluator, nemoclaw, openclaw, qwen-client, structural-gates) |
| V5 | 0.1.99 deleted | PASS |
| V6 | 0.1.9 bundle regen clean | PASS |

### What landed cleanly

**W0 Environment Hygiene.** Backed up modified files, bumped checkpoint and version to 0.1.10, deleted `docs/iterations/0.1.99/`. Caught that `pyproject.toml` was still at 0.1.8 (0.1.9 close didn't bump it) — corrected directly to 0.1.10. Also caught that `.aho-checkpoint.json` had `last_completed_iteration=0.1.8` instead of 0.1.9 — corrected. Pre-flight adaptation: not a git repo, so `git mv` from the plan was replaced with plain `mv`/`cp` throughout. Good adaptation by the executor.

**W1 Rename 0.1.9 iao-prefixed files.** Already resolved — 0.1.9's own run had already renamed its artifacts to `aho-*` prefix. The condition from 0.1.9's close was stale by the time 0.1.10 ran. W1 correctly verified this and moved on with no action. This is how carryover conditions should resolve: check before fixing, don't blindly re-apply.

**W2 log_event source_agent sweep.** Found 6 sites with hardcoded `"iao-cli"` across cli.py, brave.py, firestore.py, router.py, query.py. All renamed to `"aho-cli"`. Added backwards-compat env var fallback chain (`AHO_AGENT` → `IAO_AGENT` → `"aho-cli"`). Smoke test confirmed fresh event log entries show `source_agent="aho-cli"`. 50 tests pass, 2 pre-existing failures (age tty issue, artifacts_loop missing "Phase 0" — both unrelated to W2).

**W3 Instrumentation audit.** Audited all three components that disappeared from 0.1.9's §22: openclaw.py (session_start, chat, execute_code), nemoclaw.py (dispatch), structural_gates.py (check_artifact, check_required_sections). All were wired correctly — the 0.1.9 regression was caused by the log_event calls using `"iao-cli"` strings that the §22 generator didn't aggregate, not by missing wiring. Fixed `scripts/smoke_instrumentation.py` to use `./bin/aho`. Smoke test: 8 events, 6 unique components, all expected names present.

**W4 Manual-build-log-first enforcement.** Added `generate_build_log_synthesis()` to `loop.py` with a `FileNotFoundError` guard per ADR-042. Two regression tests pass. 52 tests pass total (same 2 pre-existing failures).

**W5 Dogfood + close.** All six verification checks passed. Build-log synthesis went degenerate — Qwen entered a "Wait, checking..." loop and was killed after ~5 minutes. Non-blocking per ADR-042 (manual build log is authoritative). Report synthesis succeeded at 715 words. 0.1.9 bundle regenerated cleanly with §1-§3 now populated. This is the first run where the bundle generator correctly finds and embeds all core artifacts.

**W6 Project root rename.** All W5 verifications passed, so W6 was eligible. Correctly surfaced as a capability-gap interrupt per Pillar 10: the executor can't `mv` a directory it's cwd'd inside. Fish commands for Kyle to run are in the build log.

### Notes on Qwen degenerate synthesis

0.1.8 saw Qwen synthesis rejected 3 times for retired-pattern content. 0.1.10 saw Qwen synthesis go degenerate with a "Wait, checking..." loop — a different failure mode. The repetition detector (0.1.7 W1) should have caught this, but the "Wait, checking..." pattern may not match the rolling-window detector's threshold if it varies slightly each iteration. Worth investigating whether the detector's window size or threshold needs tuning. Not a blocker — ADR-042's manual-build-log-first pattern means degenerate synthesis is non-blocking by design.

### Two pre-existing test failures

Both are unrelated to 0.1.10's work:
1. `test_secrets_backends` — age backend requires a TTY that doesn't exist in the agent's subprocess environment
2. `test_artifacts_loop` — expects "Phase 0" string that may have been removed or renamed during the pillar rewrite

Neither blocks graduation. Both should be investigated in a future run as part of test suite hygiene.

### Items for Kyle's manual action

**W6 project root rename** — run these from a shell OUTSIDE the iao directory:

```fish
cd ~
mv ~/dev/projects/iao ~/dev/projects/aho
cd ~/dev/projects/aho
./bin/aho --version
# Expected: aho 0.1.10
```

Then audit and update any fish abbreviations, aliases, or config paths referencing `~/dev/projects/iao`.

### Items for next run

1. **Rename `run-report` → `run` in filenames.** `aho-run-report-*.md` becomes `aho-run-*.md`. Update the run report generator, bundle spec, postflight checks. This was requested during the post-0.1.8 amendments and missed in 0.1.9 and 0.1.10.

2. **Investigate Qwen "Wait, checking..." degenerate pattern.** Either tune the repetition detector thresholds or add a secondary pattern detector for non-repeating but non-productive output.

3. **Fix the two pre-existing test failures** (age tty, artifacts_loop "Phase 0").

4. **Confirm project root rename landed** (depends on whether Kyle has executed the W6 capability-gap commands by next run launch).

---

## Reference: The Eleven Pillars

1. **Delegate everything delegable.** The paid orchestrator is the most expensive resource in the system. Any task that can run on a free local model must run on a free local model. The orchestrator decides; it does not execute. Drafting, classification, retrieval, validation, grading, routing all belong to the local fleet. The orchestrator's minutes are spent on judgment, scope, and novelty.
2. **The harness is the contract.** Agent instructions live in versioned harness files that change at phase or iteration boundaries, not in per-run markdown regenerated from scratch. The orchestrator points at the harness; it does not carry the contract in its own context. Projects run against harness overlays on a shared base.
3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out. The harness is artifact-agnostic at its core and specialized at its overlays.
4. **Wrappers are the tool surface.** Agents never call raw tools. Every tool is invoked through a `/bin` wrapper, versioned with the harness and instrumented for the event log.
5. **Three octets, three meanings: phase, iteration, run.** Phase is strategic scope. Iteration is tactical scope. Run is execution instance. Every artifact carries the full phase.iteration.run label.
6. **Transitions are durable.** Moving between phases, iterations, or runs writes state to a durable artifact before the transition is considered complete. Every gate is a write point. No implicit state.
7. **Generation and evaluation are separate roles.** The model that produced an artifact is never the model that grades it. Drafter and reviewer are different agents behind different wrappers.
8. **Efficacy is measured in cost delta.** Every run records orchestrator token cost, local fleet compute time, wall clock, delegate ratio, and quality signal.
9. **The gotcha registry is the harness's memory.** Every failure mode lands in the registry. A mature harness has more gotchas than an immature one.
10. **Runs are interrupt-disciplined, not interrupt-free.** No mid-run prompts for preference, clarification, or approval. The single exception: unavoidable capability gaps — routed through OpenClaw, logged, resumed from last checkpoint.
11. **The human holds the keys.** No agent writes to git. No agent merges. No agent pushes. No agent manages secrets.

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Run report generated 2026-04-10T16:33:27Z*
