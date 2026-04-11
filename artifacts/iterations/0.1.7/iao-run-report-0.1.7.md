# Run Report — iao 0.1.7

**Generated:** 2026-04-10T05:28:57Z
**Iteration:** 0.1.7
**Phase:** 0

## About this Report

This run report is a canonical iteration artifact produced during the `iteration close` sequence. It serves as the primary feedback interface between the autonomous agent and the human supervisor. Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the iteration's ground truth: the execution checkpoint and the extracted agent questions.

The report includes a workstream summary, a collection of technical or procedural questions surfaced by the agent during execution, and a sign-off section for the reviewer.

---

## Workstream Summary

| Workstream | Status | Agent | Wall Clock |
|---|---|---|---|
| W0 | complete | gemini-cli | - |
| W1 | complete | gemini-cli | - |
| W2 | complete | gemini-cli | - |
| W3 | complete | gemini-cli | - |
| W4 | complete | gemini-cli | - |
| W5 | complete | gemini-cli | - |
| W6 | complete | gemini-cli | - |
| W7 | complete | gemini-cli | - |
| W8 | complete | unknown | - |
| W9 | complete | gemini-cli | - |

---

## Agent Questions for Kyle

(none — no questions surfaced during execution)

---

## Kyle's Notes for Next Iteration

### Verdict: GRADUATE WITH CONDITIONS

0.1.7 shipped the structural repairs. All ten workstreams executed, 22-section bundle is intact, §22 exists, build log and report fall within the new maximum word-count ceilings, no runaway footer repetition, no hallucinated subpackage trees, no fabricated changelog, no "Phase 1 (Production Readiness)" mislabel. OpenClaw and NemoClaw are Ollama-native without open-interpreter or tiktoken. Streaming with repetition detection ran clean. Bundle is 112 KB, wall clock 11:45.

Conditions carried to 0.1.8:

**1. Real regression — split-agent language in §3 Build Log Synthesis.** The paragraph contains: *"The iteration followed the bounded sequential pattern with split-agent execution (Gemini W0-W5, Claude W6-W7)."* Split-agent was retired in 0.1.4, is explicitly banned in both agent briefs' retired-patterns blocks, and is listed as a hallucination trigger in the W3 evaluator baseline. Qwen generated it anyway and the evaluator did not flag it. Meanwhile the §5 run report workstream summary shows W0–W7 and W9 as `gemini-cli` and W8 as `unknown` — no Claude involvement actually happened. The evaluator is either not wired to the build log synthesis pass or its retired-patterns check is incomplete.

**2. §22 Agentic Components is thin.** Only two components present: `nemotron-client` (1 task, classify) and `qwen-client` (8 tasks, generate). Missing: the iao CLI itself, OpenClaw/NemoClaw smoke-test invocations, the evaluator, the repetition detector, the structural gates, the subprocess sandbox, any MCP invocations. W7 shipped the section and the event-log instrumentation — it just isn't wired to most of the components that ran. Per-run traceability promise is ~20% delivered.

**3. W8 listed as "unknown" agent in §5 run report.** The workstream summary table shows W8's agent column as `unknown`. Every other workstream says `gemini-cli`. Minor instrumentation gap in the W8 execution path.

**4. `scripts/query_registry.py` exists in the §20 file inventory.** Hash: `66d084d49e06a444  scripts/query_registry.py`. The agent briefs and the W3 evaluator's baseline assert `query_registry.py` is a kjtcom file that does not exist in iao. The bundle's own file inventory contradicts that assertion. Either a shim, leftover, or wrapper. Needs audit before 0.1.8 pillar rewrite, because the "retired patterns" and "anti_hallucination_list" entries for `query_registry.py` are now technically false statements.

**5. Base harness still carries kjtcom-era Pillar 3 phrasing.** §6 Harness shows `base.md` line: *"iaomw-Pillar-3 (Diligence) - First action: query_registry.py"*. The harness document that is supposed to be the source of truth currently documents the hallucination pattern it wants agents to avoid.

None of the conditions are fatal. Iteration graduates.

---

### Direction shift landing in 0.1.8 and beyond

Strategic reframe from the post-0.1.7 review supersedes the original "Phase 0 exit = first public push to soc-foundry/iao" target.

**Three labs, one trajectory.** kjtcom is the dev lab — where patterns were discovered under fire on production workloads. iao is the UAT lab — where patterns get proven in isolation. aho is production — a new repo to be scaffolded under `~/dev/projects/aho/` around 0.1.12, where proven patterns land in a clean implementation with no iaomw-era scar tissue. Every iao iteration from 0.1.8 forward is pattern-proving, not production-shipping.

**Rename: IAO → AHO (Agentic Harness Orchestration).** Iterative Agentic Orchestration was about the loop. Agentic Harness Orchestration is about the actual deliverable — the harness is the product, the loop is one thing the harness enforces. The rename happens in iao first as a dedicated iteration with zero other scope, so muscle memory is built before aho is stood up.

**Package-first delivery via AUR.** The 0.1.6 forensic headline was `which iao` resolving to a stale shadow binary. That entire bug class exists because no package manager owns the path. Moving aho to pacman/AUR ownership kills it by convention. Distribution target is AUR via a known maintainer. State layout is XDG-compliant: `~/.config/aho/`, `~/.local/share/aho/`, `~/.cache/aho/`.

**Living harness replaces per-iteration regenerated agent briefs.** Current CLAUDE.md/GEMINI.md are regenerated every iteration — that cycle is how 0.1.5 resurrected retired patterns, and how 0.1.7's synthesis paragraph still slipped in a split-agent reference. Target state: a versioned harness tree committed in the repo (`harness-base.md`, `harness-tools.md`, `harness-gotchas.md`, `harness-retired.md`, `harness-phase-{N}.md`) that changes at phase or iteration boundaries. CLAUDE.md and GEMINI.md shrink to ~500-line phase-specific pointers carrying only the per-iteration delta. Harness SHA recorded in bundle metadata gives §22 the missing dimension.

**`/bin` as the unified tool surface.** Every tool — local LLM, MCP server, CLI utility, pacman binary, pip/npm/npx component, agent primitive — is invoked through a versioned wrapper in `/bin`. Agents never call raw tools. This kills the stale-binary-shadowing bug class, makes §22 trivial to populate, and gives the living harness a hot-swap surface. MCP servers are installed globally (XDG) and invoked through wrappers that inject aho's structured context at call time.

**Feature framing.** aho is primarily an orchestration and efficacy system — a cost-delta wedge where a paid orchestrator (Claude Code, Gemini CLI) delegates most work to a free local fleet (Qwen, Nemotron, GLM) routed through a versioned tool surface. Secondarily it is a pipeline and middleware framework for DB/SIEM migrations (kjtcom and tripledb's current domain). Feature 2 is the first library built on top of feature 1, not a parallel product.

---

### The 11 AHO Pillars (supersede the iaomw-Pillar-1..10 reference block above in this run report)

1. **Delegate everything delegable.** The paid orchestrator is the most expensive resource in the system. Any task that can run on a free local model must run on a free local model. The orchestrator decides; it does not execute. Drafting, classification, retrieval, validation, grading, routing belong to the local fleet. The orchestrator's minutes are spent on judgment, scope, and novelty.

2. **The harness is the contract.** Agent instructions live in versioned harness files that change at phase or iteration boundaries, not in per-run markdown regenerated from scratch. The orchestrator points at the harness; it does not carry the contract in its own context. Projects run against their own harness overlays on top of a shared base. Swapping the harness swaps behavior without touching execution code.

3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out. Code, reports, schemas, analyses, migrations, audits, designs — all artifacts. The harness is artifact-agnostic at its core and artifact-specialized at its overlays. A harness that has to know "this is a Python refactor" versus "this is a SIEM migration" at its core is overfit.

4. **Wrappers are the tool surface.** Agents never call raw tools. Every tool is invoked through a `/bin` wrapper. Wrappers are versioned with the harness, instrumented for the event log, and replayable from recorded inputs. If a run touched a binary that wasn't wrapped, that is a harness gap, not a shortcut.

5. **Three octets, three meanings: phase, iteration, run.** Phase is strategic scope — what problem class this version of the project is solving. Iteration is tactical scope — what this attempt adds, fixes, or proves. Run is execution instance — which try within the iteration. Every artifact, every log entry, every state file carries the full phase.iteration.run label.

6. **Transitions are durable.** Moving between phases, iterations, or runs writes state to a durable artifact before the transition is considered complete. No implicit state. If the machine dies mid-run, the next process picks up from the last written checkpoint with full fidelity. Every gate is a write point.

7. **Generation and evaluation are separate roles.** The model that produced an artifact is never the model that grades it. Self-evaluation is a failure mode the harness structurally prevents — not through instructions but through topology. Drafter and reviewer are different agents behind different wrappers with different prompts and ideally different underlying weights.

8. **Efficacy is measured in cost delta.** The claim "aho is better and cheaper" means nothing without numbers. Every run records orchestrator token cost, local fleet compute time, wall clock, delegate ratio (fraction of decisions that never reached the orchestrator), and output quality signal. Those numbers ship with the run report, not buried in logs. Without this pillar, aho is theater.

9. **The gotcha registry is the harness's memory.** Every failure mode encountered across every run in every project lands in a structured registry. The registry is queried during pre-flight of subsequent runs. A mature harness has more gotchas than an immature one — gotcha count is the harness's compound-interest metric. Erasing a gotcha is a semantic deletion, not a cleanup.

10. **Runs are interrupt-disciplined, not interrupt-free.** Once a run launches, agents do not ping for preference, clarification, or approval. The single exception is unavoidable human-in-the-loop actions: sudo operations, credential prompts, physical device interactions, anything the machine structurally cannot do on its own. For these, the orchestrator routes the request through OpenClaw to a defined human-notification channel (Telegram bridge when wired, stdout prompt with hard timeout as fallback), logs the interrupt as a first-class event, and resumes from the last durable checkpoint on response. Interrupts for preference or scope are harness failures and produce gotcha entries. Interrupts for capability gaps are expected and instrumented.

11. **The human holds the keys.** No agent writes to git. No agent merges. No agent pushes. No agent manages secrets. No wrapper surfaces `git commit` or `git push` under any role. This is the safety rail that makes everything else possible — a misbehaving iteration cannot corrupt the source of truth because it cannot reach the source of truth.

---

### Recommended next steps — iteration sequencing

- **0.1.8** — Pillar rewrite landed in base.md. CLAUDE.md and GEMINI.md updated with the 11 pillars and new Phase 0 UAT framing. Resolve the `scripts/query_registry.py` mystery file. Fix the §22 instrumentation gap (wire OpenClaw, NemoClaw, evaluator, structural gates, subprocess sandbox to the event log). Fix the W8 "unknown" agent gap. Fix the split-agent evaluator blind spot — the W3 evaluator must catch retired-pattern language in Qwen synthesis passes, not just in design/plan drafts. No rename yet.

- **0.1.9** — Full IAO → AHO rename inside the iao repo. Zero other scope. All identifiers updated: `src/iao/` → `src/aho/`, `./bin/iao` → `./bin/aho`, `.iao.json` → `.aho.json`, ChromaDB collection names, gotcha code prefix `iaomw-*` → `aho-*`, BUNDLE_SPEC references, both agent briefs, ADR entries. Repo directory stays at `~/dev/projects/iao/` until 0.1.12; only internal identifiers change.

- **0.1.10** — First `/bin` wrapper POC. Wrap QwenClient behind `./bin/qwen` end-to-end with full event-log instrumentation feeding §22. Establish the wrapper contract (input format, output format, error codes, event-log schema).

- **0.1.11** — Living harness file tree landed (`harness-base.md`, `harness-tools.md`, `harness-gotchas.md`, `harness-retired.md`, `harness-phase-0.md`). Launch-root agent briefs shrink to thin phase-specific pointers. Harness SHA recorded in bundle metadata.

- **0.1.12** — aho scaffold directory stood up under `~/dev/projects/aho/`. No code. Four-dir skeleton, phase charter, pillar reference, README explaining relationship to iao. Everything substantive still ships in iao.

- **0.2.0** — First aho code port. Stabilized `/bin` wrappers, XDG state layout, living harness architecture ported to aho as a clean second implementation.

### Open questions to resolve before the 0.1.8 design doc

1. **Phase 0 exit criterion under the three-lab framing.** Original target: first public push to soc-foundry/iao GitHub. New framing: patterns ready for aho port. The public-push target may never apply — aho may be the repo that becomes public, not iao.
2. **Top-level directory naming in the eventual aho repo.** `/artifacts` collides with "iteration artifacts" (the five canonical outputs). Candidates: `/harness`, `/methodology`, `/docs`. Pick before 0.1.12.
3. **Versioning semantics under Pillar 5.** Current iao uses `0.1.7` = phase 0, iteration 1.7 (compound). New pillar says phase.iteration.run. For aho fresh start: use `0.1.1` meaning phase 0, iteration 1, run 1? iao continues on current scheme as it winds down.
4. **npm/npx scope in the AUR package.** Playwright, mermaid-cli, Telegram bot tooling, or something else? Determines whether `nodejs`/`npm` are hard `depends` or `optdepends`.

---

### Terminal steps to close this run (fish shell, NZXTcos)

No sudo required for the close itself. All commands run from `~/dev/projects/iao`.

---

## Reference: The Ten Pillars of IAO

1. **iaomw-Pillar-1 (Trident)** — Cost / Delivery / Performance triangle governs every decision.
2. **iaomw-Pillar-2 (Artifact Loop)** — design → plan → build → report → bundle. Every iteration produces all five.
3. **iaomw-Pillar-3 (Diligence)** — First action: `iao registry query "<topic>"`. Read before you code.
4. **iaomw-Pillar-4 (Pre-Flight Verification)** — Validate the environment before execution. Pre-flight failures block launch.
5. **iaomw-Pillar-5 (Agentic Harness Orchestration)** — The harness is the product; the model is the engine.
6. **iaomw-Pillar-6 (Zero-Intervention Target)** — Interventions are failures in planning. The agent does not ask permission.
7. **iaomw-Pillar-7 (Self-Healing Execution)** — Max 3 retries per error with diagnostic feedback. Pattern-22 enforcement.
8. **iaomw-Pillar-8 (Phase Graduation)** — Formalized via MUST-have deliverables + Qwen graduation analysis.
9. **iaomw-Pillar-9 (Post-Flight Functional Testing)** — Build is a gatekeeper. Existence checks are necessary but insufficient.
10. **iaomw-Pillar-10 (Continuous Improvement)** — Run report → Kyle's notes → next iteration design seed. Feedback loop is first-class.

---

## Sign-off

- [y] I have reviewed the bundle
- [y] I have reviewed the build log
- [y] I have reviewed the report
- [y] I have answered all agent questions above
- [n] I am satisfied with this iteration's output

---

*Run report generated 2026-04-10T05:28:57Z*
