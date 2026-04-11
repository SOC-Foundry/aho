# Investigation 11 — Synthesis and Open Questions

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Part A — What 0.1.4 Actually Shipped

iao 0.1.4 delivered a functional but incomplete system. The wins are real: the local model fleet (Qwen, Nemotron, GLM, nomic-embed) is installed, reachable, and smoke-tested. ChromaDB is seeded with 443 documents across three project archives. The artifact loop works — it generated the 0.1.5 design (5132 words) and plan (3274 words) documents, proving the template→Qwen→validation pipeline is functional end-to-end. All 8 W1 cleanup deliverables shipped, including the run-report checkpoint-read fix, question extraction, doctor CLI, version validation, and age binary. The closing sequence produced all four W7 artifacts (build-log, report, run-report, bundle). What did NOT ship: OpenClaw and NemoClaw are stubs that raise NotImplementedError (blocked by Python 3.14 / tiktoken). The kjtcom gotcha migration ported 8 entries but the ambiguous-pile pause mechanism never fired. The Telegram integration is notifications-only (one-way send, no bot framework). Three ADRs (036-038) were never written. `.iao.json` was never formally closed — it still says `current_iteration: "0.1.4"` with `completed_at: null`.

---

## Part B — Why 0.1.5 Got Stuck

0.1.5 never truly started — it generated artifacts but never executed. The sequence was: a Gemini CLI session ran the artifact loop, which produced `iao-design-0.1.5.md` (~10 min generation time) and `iao-plan-0.1.5.md`. The Gemini session then either timed out waiting for a subsequent artifact or ended its session. A Claude Code session was started but focused on 0.1.4 cleanup rather than 0.1.5 execution. The fundamental issue is not a broken loop — the loop works — but three compounding factors: (1) Qwen generation is slow (~5-15 min per artifact) with zero progress output (`stream: false`, `timeout: 1800s`), making it impossible for agents or operators to tell if the process is generating or hung; (2) `.iao.json` was never bumped past 0.1.4, so no clean starting state existed for 0.1.5; (3) the generated 0.1.5 design is a Qwen hallucination of 0.1.4's scope — it describes work already done rather than work that needs doing, and claims Phase 1 status when the project is still in Phase 0. There was no human-authored iteration brief to ground 0.1.5, so the loop produced a plausible-sounding but incorrect design.

---

## Part C — Answers to 11 Questions

### 1. What is Claw3D?

**Claw3D is a kjtcom component, not an iao component.** It is a Three.js 3D visualization of kjtcom's PCB board architecture, deployed as `claw3d.html` on `kylejeromethompson.com`. It renders system components as chips on a virtual PCB board. It shares no code, architecture, or models with OpenClaw or NemoClaw. Kyle's run-report note ("configure and deploy openclaw, claw3d and nemoclaw") groups three unrelated things. The iao postflight modules that once checked Claw3D deployment were removed during sterilization (stale `.pyc` files remain). See Investigation 8 for full details.

### 2. Did the 0.1.4 W3 ambiguous pile ever get written?

**No.** `/tmp/iao-0.1.4-ambiguous-gotchas.md` was never created. The `iao iteration resume` CLI command was never implemented. The checkpoint records W3 as `"paused"` with `"reason": "ambiguous_review"`, but this appears to be a manual checkpoint update rather than the result of the designed pause flow actually executing. 8 kjtcom entries were migrated (with `kjtcom_source_id` markers), but the Nemotron classification and pause mechanism never fired. See Investigation 5.

### 3. Gotcha registry refactor — Option A or Option B?

**Recommendation: Option A (single file with `project_code` field).**

Rationale: The registry has 13 entries. Even with full kjtcom migration, we're looking at ~100 entries. A single file with a `project_code` field on each entry is simpler to implement, simpler to query, and serves the primary use case (cross-project gotcha lookup). Option B (one file per project) adds complexity for a problem that doesn't exist yet (file size, concurrent writes). Option B becomes attractive at Phase 1+ if the registry exceeds ~500 entries. See Investigation 6.

### 4. Cross-project gotcha lookup — auto-include or only on empty result?

**Recommendation: Always include, with project_code ranking.**

Return all matching gotchas across all projects, sorted by relevance, with the home project ranked first as a tiebreaker. "Only on empty result" creates inconsistent UX where the same query returns different results depending on whether the home project has entries. A gotcha like "heredocs break agents" is equally relevant regardless of which project you're working in. See Investigation 6.

### 5. What specifically is broken in the artifact loop?

**Ranked failure modes:**

1. **(Most probable) Qwen is slow with no progress output.** Qwen 9B on an RTX 2080 generates ~15-25 tok/s. A 5000-word design takes ~5-10 minutes. With `stream: false` and `timeout: 1800s`, the caller sees nothing for the entire duration. Agents interpret silence as a hang.
2. **(Contributing) No heartbeat or progress logging.** The only stderr output is retry messages after a failed attempt. There's nothing during generation.
3. **(Minor) `num_ctx: 8192` may be tight.** With ~920 words of prompt and a 5000-word target output, the total token count approaches the context limit. This could cause truncation.
4. **(Ruled out) Template bugs, ChromaDB garbage, Ollama OOM, template rendering failures.** All components work individually. The loop produced two valid artifacts. See Investigation 3.

### 6. Should the 34.7 KB Qwen-generated iao-design-0.1.5.md be salvaged or discarded?

**Recommendation: Discard.**

The document is structurally coherent (5132 words, proper heading hierarchy, trident and pillars included) but substantively wrong:
- It claims Phase 1 ("Production Readiness") when the project is still in Phase 0
- It describes 0.1.4's scope (model fleet integration, kjtcom migration, run-report fixes) as if these are 0.1.5 work — but they were already done
- It references non-existent files (`iao-version.py`, `projects.json`)
- Its workstream descriptions are generic paraphrases of 0.1.4's plan, not forward-looking
- It doesn't address any of the actual 0.1.5/0.1.6 needs (artifact loop UX, OpenClaw beyond stubs, Claw3D scoping, gotcha schema refactor)

The document demonstrates that the Qwen loop can produce structurally valid artifacts, but without a human-authored iteration brief grounding the scope, Qwen hallucinates a plausible-sounding repeat of the previous iteration. The 0.1.5 plan (3274 words) has the same problem.

**Salvage path:** Keep the files as evidence of the loop's capabilities but do not use them as input for 0.1.6 planning. Write a human-authored 0.1.6 design brief instead.

### 7. Agentic component checklist — new BUNDLE_SPEC section, new file per iteration, or subsection in run report?

**Recommendation: Subsection in run report.**

Rationale:
- The run report is already the canonical human↔agent feedback interface
- Kyle's note asking for this checklist was written IN the run report — it's the natural location
- A new BUNDLE_SPEC section (§22) adds structural overhead to every iteration, even ones that don't touch agentic components
- A separate file per iteration fragments the feedback loop — the checklist should be visible alongside workstream status and agent questions

Implementation: Add a "## Agentic Component Status" section to the run-report template (`prompts/run-report.md.j2`) with columns: Component | Model/Version | Tasks Assigned | Status | Notes. The data can be populated from the checkpoint and system state at render time.

### 8. What should be explicitly deferred from 0.1.6 to 0.1.7?

- **Telegram bot framework** — notifications work; two-way bot is nice-to-have
- **Model fleet benchmark capture** — fleet works; formal benchmarks can wait
- **Architecture documentation** (`agents-architecture.md`) — write after implementation stabilizes
- **`model-fleet.md` expansion** to 1500 words — functional fleet > documented fleet
- **Postflight plugin system** for kjtcom-specific checks — complex refactor, not blocking
- **Phase graduation evaluation** — still in Phase 0, graduation criteria not met

### 9. Single executor or allow Claude Code fallback for 0.1.6?

**Recommendation: Allow Claude Code fallback, with Gemini as primary.**

Rationale:
- The artifact loop (Qwen-managed) works but is slow. Gemini CLI can drive it.
- If the Gemini session encounters the same "apparent hang" (slow Qwen generation with no progress), having Claude Code available as a fallback prevents the entire iteration from stalling.
- Claude Code (this session) demonstrated the ability to diagnose issues, read code, and produce analysis that Gemini sessions did not.
- The risk of dual-executor is coordination confusion. Mitigate by: Gemini runs W0-W5, Claude Code runs W6-W7 (matching the 0.1.4 design's split-agent intent), with clear checkpoint handoff.

However: if the artifact loop UX is fixed (streaming output, heartbeat logging), a single Gemini executor may be sufficient. The "dual executor" recommendation is conditional on the loop remaining opaque.

### 10. Stale global `iao` install — root cause and minimum fix?

**Root cause:** `/home/kthompson/iao-middleware/bin/` is on the fish PATH and contains a legacy v0.1.0 bash dispatcher script called `iao`. This shadows the pip-installed entry point at `~/.local/bin/iao`.

**Minimum fix:** Remove `~/iao-middleware/bin/` from fish PATH (edit the PATH-setting line in fish config). Then `which iao` will resolve to `~/.local/bin/iao` → `iao.cli:main` → current v0.1.4 source. No reinstall needed — the editable install is already in place.

### 11. What are the unknowns this audit could NOT answer?

1. **Where is the actual kjtcom gotcha source data?** `~/dev/projects/kjtcom/data/gotcha_archive.json` has an empty registry. The real data may be in `template/gotcha/gotcha_registry.json` or in the Flutter app assets. Only Kyle knows which file is authoritative.

2. **How many total kjtcom gotchas exist?** Without the source file, we can't determine how many entries need migration or how many are ambiguous.

3. **What does Kyle mean by "configure and deploy" for Claw3D?** Is it deploying `claw3d.html` to Firebase, building postflight checks, or something else? Evidence says it's a kjtcom concern, but Kyle may have a different intent.

4. **Should 0.1.5 be formally closed/skipped or left as-is?** The iteration produced artifacts but never executed. Does Kyle want to mark it as skipped in the iteration history, or jump straight to 0.1.6?

5. **Is Python 3.14 negotiable?** If iao can pin to Python 3.13, tiktoken installs and open-interpreter works. If Python 3.14 is a hard requirement, OpenClaw needs a different backend.

6. **What is the target for the agentic component checklist?** Kyle's note is brief. Does he want a full manifest of every LLM, MCP, agent, and harness used, or a simpler status table?

7. **Should the 0.1.4 iteration be re-closed properly** (bump `.iao.json`, set `completed_at`), or is the current state acceptable?

8. **Is the `~/iao-middleware/` directory archivable?** Does it contain anything needed, or can it be deleted?

---

## Part D — Recommended Shape for 0.1.6

- **W0: Iteration bookkeeping and prerequisite fixes**
  - Fix fish PATH (remove iao-middleware shadow)
  - Clean `.iao.json` state (close 0.1.4, skip 0.1.5, set current to 0.1.6)
  - Delete stale `.pyc` files from postflight cache
  - Clean `.iao-checkpoint.json` for 0.1.6
  - *No dependencies. Can proceed from evidence.*

- **W1: Artifact loop UX hardening**
  - Add streaming or heartbeat output to QwenClient
  - Reduce default timeout from 1800s to 600s
  - Consider increasing `num_ctx` to 16384
  - Add elapsed-time logging to `run_artifact_loop()`
  - *No dependencies. Can proceed from evidence.*

- **W2: Gotcha registry refactor**
  - Add `project_code` field to all existing entries
  - Fix the `d.append()` bug (use `d["gotchas"].append()`)
  - Build cross-project query API with project_code ranking
  - *Depends on Kyle's ruling on Q3 and Q4.*

- **W3: kjtcom gotcha migration completion**
  - Identify correct kjtcom source file (Kyle ruling needed)
  - Run Nemotron classification on remaining entries
  - Implement fresh migration pass (skip already-migrated by checking `kjtcom_source_id`)
  - Handle ambiguous entries (simplified batch review, not pause/resume)
  - *Depends on W2 and Kyle's ruling on Q1 (kjtcom source location).*

- **W4: OpenClaw/NemoClaw beyond stubs**
  - Decide backend: open-interpreter (needs tiktoken fix) or custom Qwen/Ollama wrapper
  - Implement functional `OpenClaw.chat()` that sends code tasks to Qwen
  - Implement Nemotron task classification in NemoClaw
  - Write `smoke_nemoclaw.py`
  - *Depends on Kyle's ruling on Q5 (Python 3.14 negotiability).*

- **W5: Agentic component checklist in run report**
  - Add "Agentic Component Status" section to run-report template
  - Populate from checkpoint and system state at render time
  - *Depends on Kyle's ruling on Q6 (scope of checklist).*

- **W6: Missing ADRs and documentation**
  - Write ADR-036 (gotcha migration), ADR-037 (telegram), ADR-038 (agents)
  - Expand `model-fleet.md` if time permits
  - *No dependencies. Can proceed from evidence.*

- **W7: Dogfood + closing sequence**
  - Run artifact loop with streaming/heartbeat fixes from W1
  - Generate build-log, report, run-report, bundle
  - Formally close 0.1.6
  - *Depends on all prior workstreams.*

---

## Part E — Things Kyle Should Decide Before 0.1.6 Planning Begins

1. **Is Claw3D in iao's scope or kjtcom's?** Evidence says kjtcom. If Kyle agrees, remove from 0.1.6 scope.
2. **Which file is the authoritative kjtcom gotcha source?** `data/gotcha_archive.json` is empty; is `template/gotcha/gotcha_registry.json` the right source?
3. **Single file with project_code (Option A) or one file per project (Option B) for gotcha registry?** Recommendation is Option A.
4. **Should 0.1.5 be formally skipped or quietly superseded?** Design and plan exist but are substantively wrong.
5. **Is Python 3.14 a hard requirement?** If so, OpenClaw needs a Qwen/Ollama backend instead of open-interpreter.
6. **What scope for the agentic component checklist?** Full manifest or simple status table?
7. **Should `~/iao-middleware/` be archived or deleted?** It contains the stale global `iao` binary.
8. **Gemini-only or Gemini + Claude Code for 0.1.6 execution?** Recommendation is allow Claude Code fallback.
