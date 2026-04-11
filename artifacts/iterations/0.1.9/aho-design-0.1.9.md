# iao — Design 0.1.9

**Iteration:** 0.1.9
**Phase:** 0 (UAT lab for aho)
**Theme:** IAO → AHO rename + RAG archive rebuild + build log filename split
**Machine:** NZXTcos
**Predecessor:** 0.1.8 (graduated with conditions, Kyle sign-off #5 = not satisfied)
**Authored:** 2026-04-10 (post-0.1.8 close)

---

## §1. Phase 0 Position

iao is in Phase 0 under the three-lab framing: kjtcom is the dev lab, iao is the UAT lab, aho is production (future scaffold ~0.1.12). 0.1.9 is the identifier rename iteration inside the iao repo — it does NOT create the aho project directory or stand up the aho scaffold. It renames every internal identifier from `iao*` to `aho*` so that when the aho repo is finally scaffolded it inherits clean vocabulary and so that Qwen's RAG retrieval can distinguish retired content from current content by string alone.

0.1.9 also lands three non-rename items that are tightly coupled to the rename or that Kyle explicitly authorized during 0.1.8 close: the ChromaDB archive rebuild (answer to Agent Question 1), the build log filename split (answer to Agent Question 3), and two trivial cleanup items carried from 0.1.8 (Conditions 5 and 6).

The repo path stays at `~/dev/projects/iao/` throughout 0.1.9. Directory rename is deferred to 0.1.12 when the aho scaffold is stood up as a separate project.

---

## §2. Why 0.1.9 Exists

### 2.1 — The rename is the fix for 0.1.8's biggest condition

0.1.8's W8 dogfood ran into a hard ceiling: Qwen's RAG retrieval kept pulling stale 0.1.5 and 0.1.7 content containing retired patterns (split-agent handoff, iaomw-Pillar-N naming) as diagnostic exhibits, and reproduced them in generated synthesis output. Three consecutive build log synthesis attempts were rejected by the W4 evaluator. Claude Code preserved a manual build log as ground truth.

The surface-level problem is that Qwen can't distinguish "exhibit in a diagnostic appendix" from "normative content to reproduce." The underlying problem is that textual aliasing is fragile: as long as the string `iaomw-Pillar-1` exists anywhere in the RAG archive, Qwen will occasionally emit it under the right retrieval conditions.

The rename is the permanent structural fix. After 0.1.9:
- `iaomw-Pillar-1` is unambiguously retired content
- `Pillar 1` (unprefixed) is unambiguously current content
- The evaluator's retired-patterns list gets a clean string space to work in
- The forbidden-chunks filter (W7) has a simple lexical rule to apply

The rename is not strategic housekeeping anymore. It is the fix.

### 2.2 — Three agent questions from 0.1.8 need answers baked into 0.1.9

**Answer 1 — RAG archive rebuild.** Kyle: *yes*. W4 purges the `iaomw_archive` ChromaDB collection and re-indexes from a filtered source that excludes diagnostic appendices. The collection is renamed to `aho_archive` at the same time. This directly fixes 0.1.8 Condition 1.

**Answer 2 — Telegram credentials.** Kyle: *we will setup new telegram bot with botfather*. This is a capability-gap action Kyle performs out of band. 0.1.9 pre-flight verifies telegram credentials work; if they don't, the iteration continues with telegram notifications disabled and surfaces the gap as a post-flight log entry. Non-blocking. Kyle's BotFather setup lands whenever it lands.

**Answer 3 — Build log Qwen synthesis vs manual record.** Kyle: *the loop should generate the Qwen version to a different filename (iao-build-log-synthesis-0.1.8.md or similar) and leave the manual build log as the authoritative record. Qwen's version becomes optional commentary, not a replacement. This fits with Pillar 7 (generation and evaluation are separate roles) because the manual build log is ground truth and Qwen's synthesis is a second-pass artifact that gets evaluated rather than shipped.*

W6 implements this: the loop writes Qwen synthesis to `iao-build-log-synthesis-<version>.md` (which becomes `aho-build-log-synthesis-<version>.md` after W1 renames the artifact prefix — see §5 W6), the manual build log at `iao-build-log-<version>.md` is untouched. ADR-042 amends ADR-012 to add the manual build log to the immutable-inputs list. This directly fixes 0.1.8 Condition 2 by making "missing report" a non-issue: the manual build log is always the ground truth, the synthesis is supplementary commentary that can fail without blocking graduation.

### 2.3 — Five carryover conditions from 0.1.8

**Condition 1 (Qwen RAG retrieval pulls stale content).** Addressed by W4 (archive rebuild + rename) and W7 (forbidden-chunks filter at retrieval time).

**Condition 2 (missing §4 Report).** Addressed by W6 (build log filename split + ADR-042). Under the new protocol, the manual build log is authoritative and the synthesis is optional, so "Qwen couldn't produce a clean synthesis" no longer produces a missing canonical artifact.

**Condition 3 (W4 retry logic does not strengthen between attempts).** Partially addressed by W7's forbidden-chunks filter — a retry automatically excludes poisoned chunks that failed the previous evaluator pass. Full retry-logic rework defers to 0.1.10 if W7 runs long.

**Condition 4 (two evaluator false positives).** Partially addressed by W7's dynamic-baseline refresh: the evaluator reads allowed scripts/CLI commands from the current file inventory at load time instead of a static JSON baseline. Forward-reference CLI commands (like `iao package` / `aho package`) defer to 0.1.10 as a "planned" list concept.

**Condition 5 (`ten_pillars_present.py` still exists under retired naming).** Addressed by W0 as trivial cleanup: rename to `pillars_present.py` and update internal assertions.

**Condition 6 (`.pre-0.1.8` backup files in repo working directory).** Addressed by W0: move to `~/dev/projects/iao.backup-pre-0.1.8/` and add `*.pre-*.md` to `.gitignore`.

### 2.4 — Kyle sign-off #5 was [n] on 0.1.8

Kyle marked "I am satisfied with this iteration's output" as `[n]` on the 0.1.8 close. The dissatisfaction is likely rooted in:
- The missing §4 Report (structurally absent canonical artifact)
- Three consecutive Qwen synthesis rejections (visible failure, even though the loop recovered)
- Condition 1 (Qwen RAG problem) being an emergent finding rather than a known condition going in

0.1.9's success criterion is not just graduation but Kyle sign-off #5 = `[y]`. That means: no missing canonical artifacts, Qwen synthesis produces evaluator-clean output in W8, and the underlying RAG problem is structurally fixed (not just worked around). §8 of this design formalizes Kyle-satisfaction as a graduation criterion alongside the mechanical verification checks.

---

## §3. The Eleven Pillars

Unchanged from 0.1.8. The canonical source of truth is `docs/harness/base.md`, read at runtime by `src/iao/feedback/run_report.py::get_pillars()`. W1's Python rename changes the import path (`iao.feedback.run_report` → `aho.feedback.run_report`) but the pillar content and the read-through mechanism are untouched.

For reference: 1. Delegate everything delegable. 2. The harness is the contract. 3. Everything is artifacts. 4. Wrappers are the tool surface. 5. Three octets, three meanings: phase, iteration, run. 6. Transitions are durable. 7. Generation and evaluation are separate roles. 8. Efficacy is measured in cost delta. 9. The gotcha registry is the harness's memory. 10. Runs are interrupt-disciplined, not interrupt-free. 11. The human holds the keys.

---

## §4. Project State Going Into 0.1.9

- **iao version on disk:** 0.1.8 (post-close, GRADUATE WITH CONDITIONS)
- **Last completed iteration:** 0.1.8
- **Python:** 3.14.3
- **Shell:** fish 4.6.0
- **Ollama models:** qwen3.5:9b, nemotron-mini:4b, nomic-embed-text, haervwe/GLM-4.6V-Flash-9B
- **ChromaDB archives:** iaomw_archive (stale, poisoned with 0.1.5/0.1.7 retired patterns — target of W4 rebuild), kjtco_archive (282 docs, read-only), tripl_archive (144 docs, read-only)
- **Pillars:** eleven, in `docs/harness/base.md`, read at runtime by `run_report.py`
- **Evaluator:** wired to build log + report synthesis passes (0.1.8 W4). Two false positives outstanding (Condition 4).
- **§22 Agentic Components:** 6 components wired (iao-cli, openclaw, nemoclaw, evaluator, qwen-client, structural-gates)
- **OpenClaw/NemoClaw:** Ollama-native
- **Streaming Qwen + repetition detector:** active
- **Gotcha codes:** `iaomw-*` prefix throughout
- **Identifiers to rename:** `src/iao/` (package directory), `bin/iao` (entry point script), `.iao.json`, `.iao-checkpoint.json`, `data/iao_event_log.jsonl`, `iaomw_archive` (ChromaDB), `iaomw-G*` (gotcha codes), IAO_* env vars used in executor launch, all prose `iao` identifier references in base.md and prompt templates
- **Identifiers NOT to rename:** `~/dev/projects/iao/` (repo path — stays iao), prose mentions of "iao" referring to the historical name, "iao" in iteration filenames (stays as-is for 0.1.9's own artifacts; 0.1.10+ artifacts use `aho-` prefix), CLAUDE.md and GEMINI.md (updated post-0.1.9 before 0.1.10 launches)
- **Telegram credentials:** broken as of 0.1.8 (failed with credential error in `iao telegram test iaomw`). Kyle to set up new BotFather bot out of band.

---

## §5. Workstreams

Nine workstreams, W0 through W8. Wall clock target: ~7 hours soft cap, no hard cap.

### W0 — Environment Hygiene + 0.1.8 Cleanup (20 min)

**Goal:** Transition cleanly from 0.1.8 to 0.1.9. Land Conditions 5 and 6.

**Deliverables:**
- Backup of full `src/iao/`, `tests/`, `docs/harness/`, `data/`, `bin/` trees plus `pyproject.toml`, `CLAUDE.md`, `GEMINI.md`, `.iao.json`, `.iao-checkpoint.json` to `~/dev/projects/iao.backup-pre-0.1.9/`
- `.iao-checkpoint.json` bumped: `iteration=0.1.9`, `last_completed_iteration=0.1.8`
- `docs/iterations/0.1.9/` created
- Build log initialized with W0 entry
- `src/iao/postflight/ten_pillars_present.py` renamed to `src/iao/postflight/pillars_present.py` with its internal function(s) updated to match — Condition 5
- `.pre-0.1.8` files moved from repo root to `~/dev/projects/iao.backup-pre-0.1.8/` — Condition 6
- `.gitignore` updated: add `*.pre-*` pattern

**Success:**
- `./bin/iao --version` returns `iao 0.1.9`
- `test -f src/iao/postflight/pillars_present.py && ! test -f src/iao/postflight/ten_pillars_present.py` passes
- `ls *.pre-* 2>/dev/null | wc -l` returns 0
- Backup directory contains all expected files

### W1 — Python Source Rename (90 min)

**Goal:** Rename the `iao` Python package to `aho`. Atomic: the repo is either fully-iao or fully-aho at the end of this workstream, never half-renamed.

**Deliverables:**
- `git mv src/iao src/aho`
- `sed` rewrite across the tree: `from iao` → `from aho`, `import iao` → `import aho`, `iao.` → `aho.` in fully-qualified references
- `pyproject.toml`: `name = "iao"` → `name = "aho"`, entry point `iao = "iao.cli:main"` → `aho = "aho.cli:main"`
- `bin/iao` → `bin/aho`, internal imports updated
- `pip install -e . --break-system-packages` reinstalls with the new name
- `./bin/aho --version` returns `aho 0.1.9`
- `pytest tests/ -v` passes (all tests still work after the import rewrite)
- `IAO_*` env vars in agent briefs' launch commands stay as-is for 0.1.9 execution — the briefs will be updated post-iteration before 0.1.10

**Success:**
- `./bin/aho --version` returns `aho 0.1.9`
- `rg -c "^from iao" src/ tests/` returns 0
- `rg -c "^import iao" src/ tests/` returns 0
- `pytest tests/ -v` passes
- `test -d src/aho && ! test -d src/iao` passes

### W2 — Data Files and Paths Rename (45 min)

**Goal:** Rename project-state files and their references in Python code. Atomic: either all data files are iao-named or all are aho-named at W2 end.

**Deliverables:**
- `git mv .iao.json .aho.json`
- `git mv .iao-checkpoint.json .aho-checkpoint.json`
- `git mv data/iao_event_log.jsonl data/aho_event_log.jsonl`
- `sed` rewrite all Python references to these paths: `".iao.json"` → `".aho.json"`, etc.
- `src/aho/paths.py` (if exists) or equivalent config module updated to reflect new paths
- `IAO_ITERATION`, `IAO_PROJECT_NAME`, `IAO_PROJECT_CODE` env var references in Python source: add `AHO_*` as primary lookups with `IAO_*` as fallback for this iteration; remove `IAO_*` references in 0.1.10
- `data/known_hallucinations.json` updated: add `iao_event_log.jsonl` as a retired identifier marker (content that references it in non-historical context is retired)

**Success:**
- `test -f .aho.json && ! test -f .iao.json` passes
- `test -f .aho-checkpoint.json` passes
- `./bin/aho --version` still returns `aho 0.1.9` (paths module updated correctly)
- `pytest tests/ -v` passes

### W3 — Gotcha Code Prefix Rename (45 min)

**Goal:** Rename gotcha codes from `iaomw-G###` to `aho-G###` across the registry and every file that references them.

**Deliverables:**
- `data/gotcha_archive.json`: every gotcha entry's `code` field rewritten `iaomw-G` → `aho-G`
- Rewrite across Python source and markdown: `rg -l "iaomw-G" | xargs sed -i 's/iaomw-G/aho-G/g'`
- `data/known_hallucinations.json` updated: add retired `iaomw-G*` prefix markers
- `src/aho/artifacts/evaluator.py` regex updates if it has any gotcha-code-aware patterns

**Success:**
- `rg -c "iaomw-G" docs/ src/ data/` returns 0 (or only within historical ADR context)
- `rg -c "aho-G" docs/ src/ data/` returns N (the count that previously matched `iaomw-G`)
- `pytest tests/ -v` passes
- `./bin/aho registry query "G001"` returns results referencing `aho-G001`

### W4 — ChromaDB Archive Rebuild and Rename (75 min)

**Goal:** Purge the poisoned `iaomw_archive` collection, re-index from a filtered source that excludes diagnostic appendices, rename the collection to `aho_archive`. This is the primary fix for 0.1.8 Condition 1.

**Deliverables:**
- Script `scripts/rebuild_aho_archive.py` that:
  1. Connects to ChromaDB at `data/chroma`
  2. Deletes the `iaomw_archive` collection (after confirming the rebuild source is ready)
  3. Iterates over the source docs directory (`docs/harness/`, `docs/phase-charters/`, `docs/roadmap/`, `docs/iterations/0.1.8/iao-design-0.1.8.md`, `docs/iterations/0.1.8/iao-plan-0.1.8.md`)
  4. For each doc, strips diagnostic appendices — any section header matching `^## Appendix [A-Z]` or `^## Diagnostic` or `^## Exhibit` is excluded along with all content until the next `## ` header
  5. Chunks the filtered content, embeds via `nomic-embed-text`, inserts into a new `aho_archive` collection with metadata `source_iteration`, `source_file`, `chunk_type`
- 0.1.2 / 0.1.3 / 0.1.4 iteration docs are NOT re-indexed — historical iterations stay out of the fresh archive. If Kyle wants them back, that's a 0.1.10 decision.
- 0.1.5 docs stay out (diagnostic only). 0.1.6 forensic audit stays out. 0.1.7 design Appendix A stays out (the diagnostic corpus).
- Update `src/aho/rag/archive.py` to query `aho_archive` instead of `iaomw_archive`
- Update `src/aho/rag/router.py` if it references the collection name
- Smoke test: query the new archive for "pillar" and verify no results contain `iaomw-Pillar-` literal strings

**Success:**
- `python3 -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma'); print([col.name for col in c.list_collections()])"` includes `aho_archive` and does NOT include `iaomw_archive`
- `aho_archive` collection has a non-zero document count
- Smoke test query returns zero results containing `iaomw-Pillar-` strings
- Smoke test query returns zero results containing `split-agent` strings

### W5 — Markdown and Harness Rename Sweep (60 min)

**Goal:** Rename every markdown identifier reference across `docs/harness/base.md`, ADR files, prompt templates, README, CHANGELOG, and the bundle spec module. Skip CLAUDE.md / GEMINI.md (those update post-0.1.9 before 0.1.10).

**Deliverables:**
- `docs/harness/base.md`: identifier renames — `iao 0.1.9` header → `aho 0.1.9`, ADR references, any `iaomw-*` prose that references identifiers. Historical text about "iao the project" in context stays as-is; only identifier references change.
- `prompts/*.md.j2`: Jinja templates for design, plan, build log, report, run report, bundle — update any `iao`/`iaomw` identifier references
- `README.md`: identifier updates only
- `CHANGELOG.md`: add a `## 0.1.9` entry documenting the rename
- `src/aho/bundle/__init__.py` and `src/aho/bundle/components_section.py`: any hardcoded `iao`/`iaomw` strings
- `MANIFEST.json`: update
- `COMPATIBILITY.md`: update

**Critical distinction:** The word "iao" appears in prose describing the historical name. Those mentions stay. Only uses of "iao" as an identifier (file path, package name, Python import, env var, ChromaDB collection, gotcha code, project code) get renamed. The W5 executor should grep first, review matches, then apply sed selectively — not blanket `sed -i 's/iao/aho/g'`.

**Success:**
- `rg -c "iaomw" docs/ prompts/ src/aho/` returns 0 (or only within historical ADR context like ADR-041)
- `rg "src/iao/" docs/` returns 0 (paths fully renamed)
- `./bin/aho --version` still returns `aho 0.1.9`

### W6 — Build Log Synthesis Filename Split + ADR-042 (60 min)

**Goal:** Implement Kyle's answer to Agent Question 3. The artifact loop writes Qwen synthesis to a separate filename so the manual build log is never overwritten. Amend ADR-012 to mark the manual build log as immutable input.

**Deliverables:**
- `src/aho/artifacts/loop.py`: build log synthesis path updated
  - Before: writes to `docs/iterations/<version>/aho-build-log-<version>.md`
  - After: writes to `docs/iterations/<version>/aho-build-log-synthesis-<version>.md`
- Manual build log filename stays `aho-build-log-<version>.md`. The synthesis filename is a NEW file that co-exists.
- `src/aho/postflight/build_log_complete.py`: updated to check the manual file for presence (primary) and the synthesis file for optional presence (secondary)
- `src/aho/bundle/__init__.py`: BUNDLE_SPEC §3 "Build Log" embeds the manual file; add a new §3a or extend §3 to embed the synthesis file if present with a clear divider
- `docs/harness/base.md`: append ADR-042
  - Title: "Manual build log is the authoritative ground truth; Qwen synthesis is optional commentary"
  - Status: Accepted
  - Date: 2026-04-10 (0.1.9 W6)
  - Context: 0.1.8 W8 showed Qwen synthesis rejected 3 times against retired-pattern content. The loop overwrote the manual build log. The manual log was preserved only because Claude Code intervened.
  - Decision: The manual build log at `aho-build-log-<version>.md` is an immutable input per ADR-012 (like design and plan docs). The loop writes synthesis to a separate file `aho-build-log-synthesis-<version>.md` which can fail without blocking graduation. This realizes Pillar 7 (generation and evaluation are separate roles) at the artifact level: Claude Code generates the build log as ground truth, Qwen generates the synthesis as evaluated commentary.
  - Consequences: bundle §3 structure changes to include both files. run_report_quality postflight check updated. ADR-012 cross-referenced.

**Success:**
- `./bin/aho iteration build-log 0.1.9` writes to `aho-build-log-synthesis-0.1.9.md` (new path), leaves `aho-build-log-0.1.9.md` untouched
- Manual edits to `aho-build-log-0.1.9.md` persist across synthesis runs
- `grep -c "ADR-042" docs/harness/base.md` returns ≥1
- `pytest tests/test_artifacts_loop.py -v` passes

### W7 — Evaluator Baseline Refresh + Forbidden-Chunks Filter (60 min)

**Goal:** Partial fix for Conditions 3 and 4. Make the evaluator read allowed scripts and CLI commands from the current file inventory at load time. Add a forbidden-chunks filter at RAG retrieval time that skips chunks containing known-hallucination strings.

**Deliverables:**
- `src/aho/artifacts/evaluator.py`:
  - Replace static known-good script list with dynamic computation: walk `scripts/` at evaluator load time, include every `.py` file as an allowed script name
  - Replace static known-good CLI command list with dynamic computation: import `src/aho/cli.py`, introspect the registered subcommands, include all of them
  - Keep `data/known_hallucinations.json` for hallucination MARKERS (things that should NEVER appear), but compute allowed-thing lists from the live repo state
- `src/aho/rag/archive.py`:
  - Add `forbidden_substrings` parameter to `query_archive()` — default to reading from `data/known_hallucinations.json` forbidden-markers list
  - At retrieval time, after getting top-k chunks, filter out any chunk whose content contains any forbidden substring
  - Log how many chunks were filtered via `log_event("rag_chunk_filtered", count=N)`
- Unit test `tests/test_rag_forbidden_filter.py`:
  - Query with a term that should hit the new `aho_archive`
  - Assert no returned chunks contain `iaomw-Pillar-`
  - Assert no returned chunks contain `split-agent`
- Unit test `tests/test_evaluator_dynamic_baseline.py`:
  - Create a new file in `scripts/` at test time
  - Load evaluator
  - Assert the evaluator accepts the new file as an allowed script
  - Clean up the test file

**Success:**
- `pytest tests/test_rag_forbidden_filter.py tests/test_evaluator_dynamic_baseline.py -v` passes
- Running the evaluator against a known-clean paragraph that mentions `test_evaluator.py` returns clean (no false positive)
- Running `query_archive("pillar", forbidden_substrings=["iaomw-Pillar-"])` returns zero chunks containing the filtered string

### W8 — Dogfood + Close (60 min)

**Goal:** Run the renamed loop against 0.1.9 itself. Verify the rename landed cleanly, the RAG archive is poisoning-free, the build log filename split works, and Kyle-satisfaction criteria can be met.

**Deliverables:**
- `./bin/aho iteration build-log 0.1.9` — generates `aho-build-log-synthesis-0.1.9.md` via Qwen synthesis (now reading from the fresh aho_archive)
- `./bin/aho iteration report 0.1.9` — generates report via Qwen synthesis
- `./bin/aho doctor postflight 0.1.9` — runs structural gates
- `./bin/aho iteration close` — generates run report and bundle (does NOT --confirm; Kyle does that)

**Verification checks (all eight must pass):**

1. `./bin/aho --version` returns `aho 0.1.9`
2. `src/iao/` does not exist; `src/aho/` exists
3. `.aho.json` exists; `.iao.json` does not
4. Bundle §3 contains manual build log; bundle §3a (or equivalent) contains synthesis with a clear divider
5. Bundle does NOT contain `iaomw-Pillar-` in the synthesized sections (§3 build log, §3a synthesis, §4 report, §5 run report)
6. Bundle does NOT contain `split-agent` in the synthesized sections
7. §22 Agentic Components shows ≥6 components with updated naming
8. Bundle has 22 sections matching `^## §` (or 23 if §3a is a full section)

**Kyle-satisfaction criteria (all three must hold for Kyle to sign-off #5 as `[y]`):**

K1. §4 Report is present and non-empty (not missing like 0.1.8)
K2. Qwen synthesis for build log produced evaluator-clean output on first or second attempt (not three rejections like 0.1.8)
K3. No new regressions — the 0.1.8 carryover conditions are addressed or explicitly deferred with rationale

**Success:** All eight verification checks pass AND all three Kyle-satisfaction criteria hold. Iteration state is PENDING REVIEW.

---

## §6. Risks and Mitigations

1. **Risk: W1 atomic rename leaves the repo in a half-renamed state if an import rewrite fails mid-sed.**
   Mitigation: W1.9 runs the full test suite before W1 is considered complete. If `pytest` fails, W0 backup is restored and W1 is re-attempted. No downstream workstreams begin until `pytest` is green.

2. **Risk: W4 rebuild script picks the wrong source documents and the new aho_archive is anemic (too few chunks) or empty.**
   Mitigation: W4 smoke test verifies non-zero doc count and checks that retrieval returns relevant results for "pillar" and "workstream" queries. If counts are too low, W4 adjusts the source list (adds more historical files that are known-clean).

3. **Risk: W5 sed-all-the-things rewrites prose mentions of "iao" that should have stayed as historical references.**
   Mitigation: W5 explicitly uses a review-before-apply pattern: run `rg` first, inspect matches, apply sed with specific patterns like `s|src/iao/|src/aho/|g` and `s|\`iao\` CLI|\`aho\` CLI|g`, NOT `s|iao|aho|g`. No blanket replacements.

4. **Risk: W6 build log filename split confuses the executor mid-iteration — it writes to the wrong file and the verification check fails.**
   Mitigation: W6 includes a dedicated smoke test that runs `./bin/aho iteration build-log 0.1.99` in a throwaway directory and inspects which file was written. If the wrong file is written, the bug is in loop.py and gets fixed before W8.

5. **Risk: W4 rebuild purges the iaomw_archive BEFORE the new aho_archive is populated, leaving the loop with no RAG at all if something fails mid-rebuild.**
   Mitigation: W4 script builds the new collection FIRST with a temporary name (`aho_archive_new`), verifies it has documents, THEN deletes the old collection, THEN renames temp to `aho_archive`. If rebuild fails, the old collection is still intact for rollback.

6. **Risk: W8 Qwen synthesis still produces retired-pattern output because the W7 forbidden-chunks filter has a bug and the W4 rebuild missed a poisoned source doc.**
   Mitigation: If W8 synthesis is rejected, Claude Code writes a manual synthesis file (now allowed under the ADR-042 split) and the iteration closes with a note that synthesis dogfood was not clean. Kyle-satisfaction criterion K2 fails, iteration is still GRADUATE WITH CONDITIONS. Not the worst case.

7. **Risk: W8's verification checks fail because the bundle spec update in W6 didn't account for §3a correctly.**
   Mitigation: If the 23-section bundle format is a parsing problem for the existing bundle generator, fall back to keeping 22 sections and embedding the synthesis inside §3 with a `---` divider between manual and synthesized. The BUNDLE_SPEC count is a less important success criterion than the content being present.

---

## §7. Scope Boundaries — What 0.1.9 Does NOT Do

- **No repo directory rename.** `~/dev/projects/iao/` stays. 0.1.12 stands up `~/dev/projects/aho/` as a separate scaffolded project.
- **No CLAUDE.md / GEMINI.md updates during the iteration.** The briefs stay as the post-0.1.7 versions Kyle saved. They update BEFORE 0.1.10 launches, as a separate manual step. This prevents the executor from reading its own updated operating manual mid-execution.
- **No `/bin` wrapper POC.** That's 0.1.10.
- **No living harness file split** (harness-base.md, harness-tools.md, etc.). That's 0.1.11.
- **No aho scaffold directory.** That's 0.1.12.
- **No full evaluator retry-logic rework.** Condition 3 gets a partial fix via W7's forbidden-chunks filter. Full retry-logic rework defers to 0.1.10.
- **No forward-reference CLI command support** (the `iao package` false positive). Defers to 0.1.10's "planned" list concept.
- **No Telegram bot code changes.** Kyle sets up the new BotFather bot out of band. Credentials update is a config-file edit Kyle does manually. 0.1.9 pre-flight just verifies whether telegram works and logs the result — does not block on failure.
- **No historical RAG content.** 0.1.2 through 0.1.7 iteration docs do NOT re-enter the fresh `aho_archive`. If Kyle wants historical context back, that's a 0.1.10 decision with explicit filtering.
- **No modifications to kjtcom or tripledb.** They are separate projects.
- **No `iao`/`iaomw` references in historical ADRs get rewritten.** ADR-012, ADR-041, etc. stay as-is because they describe historical decisions in their historical context.

---

## §8. Graduation Criteria

Two levels: mechanical (verification checks) and satisfaction (Kyle sign-off).

**GRADUATE** — All eight verification checks pass AND all three Kyle-satisfaction criteria hold. Kyle signs off all five boxes including #5. Iteration closes on a clean note.

**GRADUATE WITH CONDITIONS** — All eight verification checks pass but one or two Kyle-satisfaction criteria fail. Mechanical pass but dissatisfaction on one dimension (e.g. Qwen synthesis still needed multiple retries, or §4 Report present but thin). Kyle decides whether to sign off #5 based on how close to acceptable the outcome is.

**DO NOT GRADUATE** — Any verification check fails, or the rename is incomplete (half-renamed repo state), or W4 rebuild left the RAG archive empty or missing, or Conditions 5/6 cleanup did not happen, or `./bin/aho --version` does not return `aho 0.1.9`. Roll back to 0.1.8 state via Section E of the plan doc and re-attempt 0.1.9 in a fresh session.

---

## §9. Sign-off

- [ ] I have reviewed the bundle
- [ ] I have reviewed the build log (manual ground truth, per ADR-042)
- [ ] I have reviewed the build log synthesis (if present and non-empty)
- [ ] I have reviewed the report
- [ ] I have answered all agent questions
- [ ] I am satisfied with this iteration's output (Kyle-satisfaction criterion)

---

*Design doc generated 2026-04-10, iao 0.1.9 planning chat (Kyle + Claude web)*
