# Run Report — iao 0.1.8

**Generated:** 2026-04-10T12:45:25Z
**Iteration:** 0.1.8
**Phase:** 0

## About this Report

This run report is a canonical iteration artifact produced during the `iteration close` sequence. It serves as the primary feedback interface between the autonomous agent and the human supervisor. Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the iteration's ground truth: the execution checkpoint and the extracted agent questions.

The report includes a workstream summary, a collection of technical or procedural questions surfaced by the agent during execution, and a sign-off section for the reviewer.

---

## Workstream Summary

| Workstream | Status | Agent | Wall Clock |
|---|---|---|---|
| W0 | complete | claude-code | - |
| W1 | complete | claude-code | - |
| W2 | complete | claude-code | - |
| W3 | complete | claude-code | - |
| W4 | complete | claude-code | - |
| W5 | complete | claude-code | - |
| W6 | complete | claude-code | - |
| W7 | complete | claude-code | - |
| W8 | complete | claude-code | - |

---

## Agent Questions for Kyle

1. **Qwen RAG context stale:** Qwen synthesis for build-log was rejected 3 times because it generated retired patterns (handoff language, old pillar naming). The evaluator correctly caught these (W4 validated). Root cause: Qwen's RAG archive still contains 0.1.7 content with stale patterns. Should the RAG archive be rebuilt before 0.1.9?
-- yes

2. **Telegram credentials:** `./bin/iao telegram test iaomw` failed with credential error. Non-blocking for 0.1.8. Should Telegram notification be configured for 0.1.9?
-- we will setup new telegram bot with botfather

3. **Build log as Qwen synthesis vs manual record:** The artifact loop overwrites the manual build log when `./bin/iao iteration build-log` is run. Should the build log be added to ADR-012 immutable artifacts, or should the loop generate it with a different filename (e.g. `build-log-synthesis`)?
-- the loop should generate the Qwen version to a different filename (iao-build-log-synthesis-0.1.8.md or similar) and leave the manual build log as the authoritative record. Qwen's version becomes optional commentary, not a replacement. This fits with Pillar 7 (generation and evaluation are separate roles) because the manual build log is ground truth and Qwen's synthesis is a second-pass artifact that gets evaluated rather than shipped.

---

## Kyle's Notes for Next Iteration

### Verdict: GRADUATE WITH CONDITIONS

All nine workstreams completed. Five 0.1.7 carryover conditions resolved. All six dogfood verification checks from the 0.1.8 design pass cleanly. The single biggest structural win landed: the run report's pillar block is now read from `docs/harness/base.md` at runtime — the first concrete instance of "harness is the contract" (Pillar 2) in living iao code. Kate-editing the old run report would have done nothing; the new read-through makes base.md the actual source of truth.

W4 validated itself in the strongest possible way: the evaluator caught Qwen synthesis rejecting three consecutive build log attempts for retired-pattern content. Before 0.1.8, those attempts would have shipped. After 0.1.8, Claude Code correctly preserved a manual build log instead. The loop's self-correcting topology works.

The condition worth naming is not a workstream failure but a revealed depth: Qwen's RAG retrieval keeps pulling stale 0.1.5/0.1.7 content containing the retired patterns as diagnostic exhibits, and reproduces them in generated artifacts without recognizing the exhibit context. The 0.1.7 W5 RAG freshness weighting didn't solve this; 0.1.9 will need to.

### Verification checks — all six pass

| # | Check | Result |
|---|---|---|
| V1 | Run report contains "Delegate everything delegable" | PASS (embedded via W2 read-through from base.md) |
| V2 | Run report section contains zero `iaomw-Pillar-` literals | PASS (0 matches in §5) |
| V3 | Build log section contains zero `split-agent` literals | PASS (0 matches in §3) |
| V4 | §22 Agentic Components ≥6 unique components | PASS (exactly 6: evaluator, iao-cli, nemoclaw, openclaw, qwen-client, structural-gates) |
| V5 | Workstream summary has zero `unknown` agents | PASS (all 9 show `claude-code`) |
| V6 | Bundle has 22 sections | PASS |

§22 shows 27 total events across 6 unique components, including the synthesis_evaluator_reject events from W8. That's the per-run traceability the 0.1.7 conditions were missing — this time it's actually populated.

### What landed cleanly

**W1 Base Harness Pillar Rewrite.** Retired ten-pillar block replaced in base.md. Zero `iaomw-Pillar-` references remain in the pillar section. Query_registry.py phrasing gone from Pillar 3. The preamble was rewritten to avoid triggering the evaluator's own retired-patterns grep against itself.

**W2 run_report.py De-hardcoding.** The load-bearing fix. `_load_pillars_from_base()` parses the pillar section out of base.md and returns a cached list. `get_pillars()` is the accessor. The hardcoded ten-pillar Python list is gone, replaced with a splat of `get_pillars()`. A single-line bug in the initial regex (using DOTALL `.*` in the header pattern) caused a cross-line match on the first try; fixed on retry. Six unit tests pass. The generated 0.1.8 run report shows "Reference: The Eleven Pillars" followed by the full eleven-pillar block read from base.md.

**W3 Evaluator + Templates Cleanup.** `PILLAR_ID_RE` removed from evaluator.py. `pillar_ids` removed from the extract_references return dict. The old pillar validation block deleted. `known_hallucinations.json` updated: query_registry.py entries removed, ten retired `iaomw-Pillar-N` markers added. templates.py updated with a forward-compat `ten_pillars_block` alias. Four evaluator tests pass.

**W4 Evaluator Wired to Synthesis.** The workstream that earned its keep in W8. An `artifact_type` parameter on `evaluate_text()` triggers auto-reject on retired patterns when the artifact is a synthesis type. Both the two-pass path and the main loop path log `synthesis_evaluator_reject` on failure. Three regression tests pass, including the 0.1.7 split-agent paragraph. In W8, this exact mechanism caught three real Qwen hallucinations.

**W5 §22 Instrumentation Expansion.** All six planned components wired: cli.py (cli_invocation), openclaw.py (session_start + chat + execute_code), nemoclaw.py (agent_msg), evaluator.py (evaluator_run), qwen_client.py (repetition-detector surface), structural_gates.py (structural_gate). Added a `check_required_sections()` convenience function. Smoke test passes with exactly 6 unique components.

**W6 W8 Agent Instrumentation.** `build_workstream_summary(checkpoint)` extracted as a named function. `IAO_EXECUTOR` env var fallback added. `log_workstream_complete` in logger.py now writes the agent to the checkpoint on each completion. Three unit tests pass. The 0.1.8 run report workstream summary shows `claude-code` for every row.

**W7 Baseline Updates for query_registry.py.** ADR-041 appended to base.md documenting the shim as legitimate. All three baseline audits pass.

**W8 Dogfood.** All six verification checks pass against the generated artifacts. The manual build log Claude Code preserved is what ships as ground truth.

### Conditions carried to 0.1.9

**Condition 1 — Qwen RAG retrieval pulls stale retired-pattern content.** Three sequential synthesis attempts in W8 produced output containing `split-agent`, `iaomw-Pillar-1`, and `iaomw-Pillar-10` despite the updated system prompt and the W1/W3 cleanups. The source is RAG retrieval: the ChromaDB `iaomw_archive` contains the 0.1.5 design doc, the 0.1.7 design doc Appendix A (which embeds the retired patterns verbatim as diagnostic exhibits), and the 0.1.4 design doc — all of which contain retired patterns in bodies the LLM cannot distinguish from normative content. The 0.1.7 W5 recency weighting helps but does not exclude these chunks.

Fix candidates for 0.1.9:
- Add a "forbidden chunks" filter at retrieval time that skips any chunk containing strings from `known_hallucinations.json` before the chunks reach the prompt
- Mark specific chunks (Appendix A sections, INCOMPLETE.md contents) as "diagnostic only" in archive metadata and exclude them by default
- Purge and re-index `iaomw_archive` from a filtered source that strips diagnostic appendices

Recommendation: implement the "forbidden chunks" filter first because it's the cheapest fix and composes with any later archive cleanup. The bad chunks keep existing but stop reaching Qwen's context window.

**Condition 2 — §4 Report is missing from the bundle.** After three rejected synthesis attempts, Claude Code skipped the report generation to avoid overwriting the manual build log. The bundle shows `### REPORT (MISSING)` at §4. This is structurally correct under Pillar 10 (don't ship garbage) but leaves one of the five canonical artifacts absent. 0.1.9 needs either a "synthesize from build log without RAG" fallback mode or an explicit manual-report escape hatch that Claude Code can invoke without shipping Qwen garbage.

**Condition 3 — W4 retry logic does not strengthen between attempts.** Attempt 1 produced 3 errors. Attempt 2 produced 5 errors (it got worse — Qwen added `iaomw-Pillar-10` on top of `iaomw-Pillar-1`). The retry-with-diagnostic-feedback mechanism adds a diagnostic message to the prompt but does not exclude the RAG chunks that poisoned the first attempt. A retry that reuses the same RAG context is effectively a re-roll with slightly different wording. 0.1.9 should make a retry mechanically different from the original: either strip the retrieved context entirely, or exclude any chunk that contains strings that failed the previous evaluator pass.

**Condition 4 — Two evaluator false positives.** The W8 event log shows:
- `hallucinated CLI command: iao package` — "iao package" is a forward reference to a 0.1.10+ feature (AUR package delivery). The evaluator's known-good CLI list doesn't allow forward references. Either add a "planned" list or relax strict enforcement on CLI commands.
- `hallucinated script: test_evaluator.py` — this is a real file created/updated in 0.1.8 W3. The evaluator's known-scripts baseline is out of date relative to what W3 shipped. 0.1.9 should refresh the baseline after each iteration, or compute the baseline dynamically from the current file inventory at evaluator load time.

Neither false positive blocked the iteration, but they erode trust in the evaluator's judgments and make it harder to distinguish "real regression" from "stale baseline."

**Condition 5 — `src/iao/postflight/ten_pillars_present.py` still exists under retired naming.** The file inventory at line 4206 shows this module unchanged. W1 and W3 touched pillar content in base.md, run_report.py, evaluator.py, and templates.py, but missed this post-flight check named after the retired framing. Rename to `pillars_present.py` and update its internal assertions. Small, 0.1.9 W0 or W1.

**Condition 6 — `.pre-0.1.8` backup files in repo working directory.** File inventory shows `CLAUDE.md.pre-0.1.8`, `GEMINI.md.pre-0.1.8`, `docs/harness/base.md.pre-0.1.8` in the repo root. These should live in `~/dev/projects/iao.backup-pre-0.1.8/` as the W0 plan specified, not in the working directory. Either `.gitignore` the `.pre-*` pattern or move the files out. Trivial cleanup for 0.1.9 W0.

### Direction check — 0.1.9 rename is reinforced by these findings

The core lesson from 0.1.8's W8 rejection cycle is that textual aliasing is fragile. As long as the strings `iaomw-Pillar-1` and `split-agent` exist anywhere in the archive, Qwen will reproduce them under the right retrieval conditions, and the evaluator will keep catching them. The permanent fix is the 0.1.9 IAO → AHO rename because it changes the string space entirely — the new canonical form is "Pillar 1" (no `iaomw-` prefix) and the retired patterns become lexically distinct from any current content. After the rename, a chunk containing `iaomw-Pillar-1` is unambiguously old content; a chunk containing "Pillar 1" is unambiguously current. The evaluator's job gets easier and Qwen's RAG retrieval gets cleaner in the same step.

This doesn't change the 0.1.9 scope — still a pure rename iteration with zero other work — but it moves the rename from "strategic housekeeping" to "the actual fix for 0.1.8's biggest condition."

### Recommended next steps — 0.1.9 scope

0.1.9 is the IAO → AHO rename inside the iao repo. Zero other scope. Workstream sketch:

- **W0** Environment hygiene + backup the full src/, docs/, tests/ trees plus the four .md files in repo root. Resolve the `.pre-0.1.8` backup files from Condition 6.
- **W1** Python source rename sweep. `src/iao/` → `src/aho/` (directory rename), import rewrite across the whole tree, `pyproject.toml` package name, `bin/iao` → `bin/aho`, entry point registration.
- **W2** Data file and path rename. `.iao.json` → `.aho.json`, `.iao-checkpoint.json` → `.aho-checkpoint.json`, `data/iao_event_log.jsonl` → `data/aho_event_log.jsonl`.
- **W3** Gotcha code prefix rename. `iaomw-G001` → `aho-G001` across the gotcha archive and every file that references the codes.
- **W4** ChromaDB collection rename. `iaomw_archive` → `ahomw_archive`. This is the critical path for Condition 1 — a fresh collection with fresh content excludes the poisoned 0.1.5/0.1.7 chunks by construction.
- **W5** base.md, agent briefs, bundle spec, ADR entries — every markdown mention of "iao" that refers to the project identifier becomes "aho". Careful: "iao" as a prose word inside sentences about the old project name should stay (history); "iao" as an identifier or file path should change.
- **W6** Condition 1 fix: forbidden-chunks filter at RAG retrieval. The rename gives this filter a clean string space to work in.
- **W7** Conditions 3, 4, 5: retry logic strengthening, evaluator baseline refresh, postflight check rename.
- **W8** Dogfood + close.

Wall clock estimate: ~8 hours. Partial ship acceptable for W6/W7 if the rename itself eats the budget.

### Open questions surfaced by 0.1.8

1. Should the evaluator's baseline be computed dynamically from the file inventory instead of maintained in a JSON? The `test_evaluator.py` false positive suggests yes — a static baseline decays fast.

2. Should diagnostic appendices in design docs be marked with a metadata flag that excludes them from RAG indexing? The 0.1.7 Appendix A is the diagnostic corpus that made 0.1.7 possible, but it's also the RAG poison making Qwen synthesize retired patterns.

3. Is a missing canonical artifact (like §4 Report here) a GRADUATE-blocker in some future iteration? Worth making the graduation criteria more explicit about "artifact missing" as a separate category.
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

*Run report generated 2026-04-10T12:45:25Z*
