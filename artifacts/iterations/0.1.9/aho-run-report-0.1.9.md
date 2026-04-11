# Run Report — aho 0.1.9

**Generated:** 2026-04-10T15:00:07Z
**Iteration:** 0.1.9
**Phase:** 0

## About this Report

This run report is a canonical iteration artifact produced during the `iteration close` sequence. It serves as the primary feedback interface between the autonomous agent and the human supervisor. Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the iteration's ground truth: the execution checkpoint and the extracted agent questions.

The report includes a workstream summary, a collection of technical or procedural questions surfaced by the agent during execution, and a sign-off section for the reviewer.

---

## Workstream Summary

| Workstream | Status | Agent | Wall Clock |
|---|---|---|---|
| W0 | pass | Gemini CLI | - |
| W1 | pass | Gemini CLI | - |
| W2 | pass | Gemini CLI | - |
| W3 | pass | Gemini CLI | - |
| W4 | pass | Gemini CLI | - |
| W5 | pass | Gemini CLI | - |
| W6 | pass | Gemini CLI | - |
| W7 | pass | Gemini CLI | - |
| W8 | pass | Gemini CLI | - |

---

## Agent Questions for Kyle

(none — no questions surfaced during execution)

---

## Kyle's Notes for Next Iteration

### Verdict: GRADUATE WITH CONDITIONS

The rename arc landed its core: `src/iao/` → `src/aho/`, `bin/iao` → `bin/aho`, `.iao.json` → `.aho.json`, `.iao-checkpoint.json` → `.aho-checkpoint.json`, `data/iao_event_log.jsonl` → `data/aho_event_log.jsonl`. The rebuild script for the ChromaDB archive shipped. `ten_pillars_present.py` was renamed to `pillars_present.py`, resolving an 0.1.8 carryover. All 0.1.8-era tests (test_synthesis_evaluator, test_rag_forbidden_filter, test_evaluator_dynamic_baseline, test_workstream_agent) are on disk. The project root path at `~/dev/projects/iao/` is unchanged, as intended — that rename comes at the end of whichever run closes out the rename arc.

Three meaningful problems surfaced, all addressable in the next run. Details below.

### What landed cleanly

Confirmed from §20 file inventory:
- Full `src/aho/` package tree with all subpackages (agents, artifacts, bundle, feedback, install, integrations, pipelines, postflight, preflight, rag, secrets, telegram)
- `bin/aho` as the CLI entry point
- `.aho.json`, `.aho-checkpoint.json` as state files
- `data/aho_event_log.jsonl` as the event log
- `scripts/rebuild_aho_archive.py` as the rebuild tool
- `src/aho/postflight/pillars_present.py` (was `ten_pillars_present.py` in 0.1.8 — Condition 5 resolved)
- ChromaDB shows three collection directories under `data/chroma/` — assuming one is the rebuilt archive
- All historical iteration files in `docs/iterations/0.1.2/` through `docs/iterations/0.1.8/` retain their original `iao-*` prefixes (correct — historical records stay as-is)

### Conditions carried forward

**Condition 1 — Bundle generator cannot locate the manual build log, design, or plan.**

§1 Design, §2 Plan, and the manual build log all show `(missing)` in the bundle, but §20 File Inventory shows they exist on disk at:
- `docs/iterations/0.1.9/iao-design-0.1.9.md` (hash `70793d26c4863ad9`)
- `docs/iterations/0.1.9/iao-plan-0.1.9.md` (hash `17e468b53921ef09`)
- `docs/iterations/0.1.9/iao-build-log-0.1.9.md` (hash `a19c1c00b3729bfc`)

The bundle generator was updated to look for `aho-*` prefixed files, but these three files were authored before the rename propagated, so they kept the `iao-*` prefix. The generator can't find them and reports `(missing)`. Fix: bundle generator should accept both prefixes during the transition run, OR the files should be renamed on disk as part of the next run's cleanup. The second option is cleaner — once renamed, the generator has a single naming convention to maintain.

**Condition 2 — §22 Agentic Components regressed from 6 components to 3.**

0.1.8's §22 showed: evaluator, iao-cli, nemoclaw, openclaw, qwen-client, structural-gates.
0.1.9's §22 shows: evaluator, iao-cli (still named `iao-cli`, not `aho-cli`), qwen-client.

Three components disappeared: nemoclaw, openclaw, structural-gates. And `iao-cli` kept its old name in the `source_agent` field of event log entries, meaning the rename sweep touched file paths and imports but missed string literals in `log_event()` calls. The regression has two causes:

1. **String literals in log_event calls were not swept.** The `source_agent="iao-cli"` (or equivalent) is a string literal, not a path or import — `sed` patterns that matched `src/iao/` and `from iao` didn't touch these. Every `log_event` call site that hardcodes a component name needs an audit.

2. **OpenClaw, NemoClaw, structural-gates instrumentation may not be firing at all.** If they were firing with their original `source_agent` strings, they'd still appear in §22 (just under the old name). Their absence means either the code paths weren't executed during 0.1.9 W8 dogfood, or the rename broke the wiring. Needs investigation.

This is a functional regression against 0.1.8's traceability baseline.

**Condition 3 — Qwen synthesis build log describes workstreams that cannot be verified.**

§3 Build Log shows only `### BUILD LOG (QWEN SYNTHESIS)` — no `### BUILD LOG (MANUAL)` section. Qwen's synthesis describes W0-W8 with specific claims ("appendix filter applied to exclude deprecated entries", "Query latency improved by 18%", "12,847 documents indexed") that have no ground truth to check against. The ADR-042 pattern was that the manual build log is authoritative and the synthesis is commentary — but if the bundle generator can't find the manual log (Condition 1), then Qwen's hallucinated narrative becomes the only visible build log content.

The W4 synthesis evaluator from 0.1.8 did not reject this output because it doesn't contain retired-pattern markers — it contains plausible-sounding invented content about workstreams that may or may not have happened. The evaluator catches `split-agent` and `iaomw-Pillar-1` but not "Query latency improved by 18%."

This is the same class of problem that Kyle's post-0.1.8 Amendment 1 was designed to address: Nemotron-as-evaluator reading the output with reasoning about whether content is verifiable. Worth considering for a future run.

**Condition 4 — `docs/iterations/0.1.99/` garbage file still on disk.**

File inventory line 2979 shows `docs/iterations/0.1.99/aho-build-log-synthesis-0.1.99.md` still present. This was a throwaway test directory created erroneously during 0.1.9 execution. Delete as part of the next run's environment hygiene.

**Condition 5 — Run report workstream summary has no wall clock data.**

All 9 workstreams show `-` in the Wall Clock column. Either the checkpoint wasn't tracking wall clock per workstream, or the run report generator isn't reading it. Minor but noted.

**Condition 6 — Report synthesis content does not match actual workstream results.**

§4 Report's workstream score table shows W0-W7 at 10/10 and "W8 | N/A | Reserved for future iteration" — but the run report workstream summary shows W0-W8 all `pass`. The report is Qwen-synthesized and the run report is mechanical; they disagree about whether W8 ran. Related to Condition 3 (Qwen invents content without ground truth).

### Direction for next run

Next run (0.1.10) should be scoped narrowly to fix the regressions and complete what 0.1.9 started:

1. Rename the three `iao-*` files in `docs/iterations/0.1.9/` to `aho-*` on disk, OR update the bundle generator to accept both prefixes — one approach, not both
2. Sweep `log_event()` source_agent strings across `src/aho/` and rename `iao-cli` → `aho-cli` (plus any other hardcoded component names that kept old naming)
3. Audit OpenClaw, NemoClaw, structural-gates instrumentation — confirm they fire during a run, confirm they log under `aho-*` names
4. Delete `docs/iterations/0.1.99/`
5. Restore the manual-build-log-first protocol: the loop should fail loudly if synthesis is requested without a manual build log present, not silently ship hallucinated content as the only record
6. Dogfood and verify all six conditions above are resolved

Project root rename (`~/dev/projects/iao/` → `~/dev/projects/aho/`) is still pending and belongs at the end of whichever run finally closes the rename arc cleanly.

The Qwen RAG archive rebuild appears to have happened (the synthesis didn't trigger retired-pattern rejects), but without a manual build log or a detailed verification in §3, it can't be confirmed. Next run should include a smoke query against the rebuilt archive that checks for `iaomw-Pillar-1` and similar retired markers in results, and log the result to the build log.

### Open questions

1. Did the ChromaDB archive actually get rebuilt to `aho_archive` or `ahomw_archive`? The file inventory shows three chroma collection directories but doesn't reveal their names. Need to query ChromaDB directly to confirm.

2. Are OpenClaw and NemoClaw still Ollama-native (0.1.7 W8 work preserved) or did the rename break their client wiring?

3. Is the W4 0.1.8 synthesis evaluator still wired to the synthesis pass post-rename, or was it disconnected during the W1/W2 import rewrite?

---

## Reference: The Eleven Pillars

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

---

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Run report generated 2026-04-10T15:00:07Z*
