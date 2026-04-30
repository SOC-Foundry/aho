# Carry-Forwards — 0.2.15

**Generated:** 2026-04-21 W4 Close
**Format:** Item · Origin · Severity · Target · Notes

Severity scale: **critical** (blocks a downstream iteration), **important** (measurable impact on correctness, observability, or hygiene), **nice-to-have** (improvement with no immediate cost if deferred).

---

## TO 0.2.16: SUBSTRATE + HARNESS HYGIENE

- **`test_workstream_events.py` checkpoint corruption — fix, don't defer again.** Origin: carried from 0.2.14; recurred in 0.2.15 W0 (F002) and W3 (F005). Severity: **important**. The test writes directly to the real `.aho-checkpoint.json` because it does not mock `find_project_root`. Symptoms: spurious workstream entries (`W_V3_TEST`, `W_V1_COMPAT`, ...) written during the baseline regression run, requiring manual checkpoint restore afterward. Third recurrence. Fix is straightforward: add a `find_project_root` mock to the test file's fixture or autouse-patch it via `conftest.py`. **Target: 0.2.16 W0.**

- **Cascade integration flake (`test_cascade_end_to_end`).** Origin: 0.2.15 W3 F001. Severity: **important**. Qwen emits empty `message.content` on long system prompts under certain VRAM + dispatcher conditions. Reproducible-but-not-always. W3 deselected it from baseline comparison. **Target: 0.2.16 W0** — build a controlled repro harness (varied system-prompt length, varied VRAM state) and diagnose. Suspect: Qwen thinking-mode interaction with truncated context; or `num_predict` exhaustion on ChatML prompts over the 32K token boundary.

- **Remaining `except Exception` sites in `src/aho/agents/nemoclaw.py`.** Origin: 0.2.15 W3 F003. Severity: **important**. Two remaining sites at lines 77 (dispatch method) and 134 (handler dispatch branch) in the OpenClaw path, intentionally not narrowed in W3 because W3 scope was the classifier layer. Narrowing is a 20-minute change once the failure modes are enumerated. **Target: 0.2.16 W1 or dedicated hygiene iteration.**

- **`emit_workstream_complete()` side-effect root cause still unresolved.** Origin: 0.2.14 W0. Severity: **nice-to-have**. Symptomatic fix (sibling-preservation) held across 0.2.14 and 0.2.15 without regression. Root cause of the original sibling corruption was never identified. If the symptom never recurs, this is self-resolving; if it recurs, investigate. **Target: 0.2.16+ reactive.**

- **Gotcha registry canonical file location.** Origin: 0.2.14 carry-forward. Severity: **nice-to-have**. Gotchas are referenced inline in CLAUDE.md, design docs, and carry-forwards. No single queryable registry file exists. Pillar 9 calls it "the harness's memory." Worth promoting to a canonical file. **Target: 0.2.16 W0 candidate.**

- **Baseline contamination protocol.** Origin: 0.2.15 W1 (revised). Severity: **important**. W1 spent hours on probe data that Kyle later identified as contaminated by Ollama state. Current protocol says "clean state" but does not specify assertion mechanics. Proposal: before any Ollama-dependent probe, assert `list_loaded_models() == []` and Ollama process VRAM delta vs desktop baseline is within tolerance. Fail fast. **Target: 0.2.16 W0 protocol update.**

## TO 0.2.16: CASCADE + PILLAR 7

- **Auditor role-prompt bifurcation (STILL not fixed).** Origin: 0.2.14 W1.5 observation, deferred in 0.2.15 by design. Severity: **important**. `delta_validations` rubber-stamps, `additional_findings` does real critique. Cross-model cascade in 0.2.15 W4 tests whether changing the model breaks the pattern — if the rubber-stamp persists across models, the prompt is the bottleneck, not the model. **Target: 0.2.16 prompt engineering workstream.**

- **Does cascade propagate the GLM thinking field?** Origin: 0.2.15 W1 F005, W4 observation. Severity: **important**. GLM emits analytical reasoning in its `thinking` field (Chinese for identity, English for classification). Orchestrator currently propagates only `content` downstream. If the Auditor's signal lives in `thinking` but Indexer-out and Assessor never see it, the cascade loses information at the GLM handoff. Decision: propagate `thinking` as part of stage handoff, or explicitly accept that thinking is internal and only `content` flows. **Target: 0.2.16 W1 cascade architecture.**

- **Capability-routed vs role-assigned cascade architectural decision.** Origin: 0.2.14 carry-forward, deferred by 0.2.15 design. Severity: **nice-to-have**. Current architecture is fixed 5-stage role sequence. Expanded roster (when Tier 2/3 lands) naturally suggests capability routing (Triage Officer routes to Specialist by task type). Both valid; different matrix implications. **Target: 0.2.17+ when roster expansion is on deck.**

- **Executor-as-outer-loop-judge (Critic/Arbiter).** Origin: 0.2.14 carry-forward, deferred by 0.2.15. Severity: **nice-to-have**. Two-tier evaluator at orchestrator boundary: lower-tier Critic (council LLM) first-pass, Claude/Gemini Arbiter second-tier with calibration authority. Calibration signals persist harness-wide. Adds Pillar 7 separation at the orchestrator boundary. **Target: 0.2.16 or 0.2.17 architectural design.**

- **OpenClaw disposition.** Origin: 0.2.14 W0 (confirmed Qwen wrapper), 0.2.15 W3 (session layer retained but no usage data). Severity: **nice-to-have**. Three OpenClawSession instances still held warm behind the aho-nemoclaw daemon socket. Retain / repurpose (different model) / deprecate. **Target: 0.2.16 council composition review.**

## TO 0.2.16: INSTALL + DEPLOYMENT

- **install.fish Tier 1 section finalization.** Origin: 0.2.15 W4 scope — deferred. Severity: **critical** (blocks "Tier 1 shippable" claim). W4 prioritized the cross-model cascade over install.fish. Content is fully derivable from W0 vetting, W1 fitness report, W2 dispatcher, W3 ADR. Items: machine detection (VRAM check, Arch-family check), Tier 1 decision (VRAM 8-16GB), model pulls (Qwen/Llama/GLM/Nemotron), dispatcher config generation, baseline vetting probe. **Target: 0.2.16 W0 — first deliverable.**

- **Tier 1 hardware requirements documentation.** Origin: 0.2.15 W1 fitness + W2 dispatcher decisions. Severity: **important**. 8GB VRAM minimum. GLM requires `num_gpu=30` partial offload. 4-model roster cannot be co-resident (total 19.3GB). Cascade must serialize. install.fish should surface these constraints, not silently apply them. **Target: 0.2.16 W0 alongside install.fish.**

- **Ollama service layer documentation.** Origin: 0.2.15 W1 F008 (kyle escalation E2). Severity: **important**. Ollama runs as system-level systemd (`/etc/systemd/system/ollama.service`), not user-level. Restart requires `sudo`. install.fish and harness docs must reflect this or users will hit permission walls on first custom config. **Target: 0.2.16 W0.**

- **SSH key distribution to remote machines.** Origin: 0.2.15 planning notes (kyle-notes-0.2.15-planning.md). Severity: **nice-to-have**. Password auth working but not key-only. Not a blocker for Tier 1 install but is for orchestration-from-A8cos patterns. **Target: 0.2.16+.**

- **WARP/Tailscale coexistence on auraX9cos.** Origin: 0.2.15 planning notes. Severity: **nice-to-have**. Not validated under live WARP. Not on the Tier 1 path; relevant for multi-machine bootstrap. **Target: 0.2.16 or 0.2.17 fleet bootstrap arc.**

## TO 0.2.17+: ROSTER EXPANSION + RAG

- **nomic-embed-text + ChromaDB RAG integration.** Origin: 0.2.14 carry-forward, deferred in 0.2.15. Severity: **important** (unlocks retrieval). Nomic embed endpoint validated coexisting with chat in 0.2.15 W1 R12, but retrieval plumbing is not wired. **Target: 0.2.17.**

- **Tier 2/3 roster (Gemma 2 9B, DeepSeek-Coder-V2 16B-Lite, Mistral-Nemo 12B).** Origin: 0.2.14 carry-forward. Severity: **important** (real multi-model fleet). Requires >8GB VRAM. Waits for Luke's machine (24GB) or P3 clone installs. Gemma 2 as a Pillar 7 partner (different weights from Qwen) is the highest-value candidate. **Target: 0.2.17 or 0.2.18 fleet bootstrap.**

- **Fleet bootstrap iteration arc.** Origin: 0.2.15 planning notes. Severity: **important**. Sequence: 0.2.16 A8cos minimal (orchestration role), 0.2.17 Luke full (first Tier 2/3 deployment), 0.2.18 P3 production. A8cos cannot be an inference node (integrated GPU, no discrete VRAM) — it's an orchestration/dev role. **Target: 0.2.16 W0 re-planning.**

- **Firestore migration of staging directories.** Origin: 0.2.14 carry-forward. Severity: **nice-to-have**. Current staging uses local filesystem (`artifacts/iterations/*/deltas/staging/`). Firestore-hosted delta staging is a multi-machine coordination prerequisite. **Target: 0.2.17+ alongside fleet bootstrap.**

## TO 0.2.16: W4 CASCADE-SPECIFIC (NEW)

- **Qwen `num_predict=2000` is insufficient for cascade Producer role.** Origin: 0.2.15 W4 (this run). Severity: **critical** (blocks clean Pillar 7 comparison). On the 247K-char document at 32K context, Qwen's thinking-mode consumed the entire 2,000-token budget — `eval_count=2000`, `message.content=""`, `message.thinking=8026 chars`, `done_reason="length"`. This is the root cause of the W3 F001 cascade flake. Remediation paths (none adopted yet): raise Qwen num_predict to 6,000–8,000; use `/no_think` prefix; switch to non-thinking Qwen variant; shorten Producer's input via pre-summarization. **Target: 0.2.16 W0 — must fix before any fair cross-model cascade re-run.**

- **Cascade halt-on-empty-content semantics.** Origin: 0.2.15 W4. Severity: **important**. When a stage returns `error=None` but 0 chars of content, the cascade continues, converting the emptiness into a `[stage X failed: None]` string passed to the next stage. Downstream stages audit the failure marker as if it were content. The cascade should surface empty-content-from-load-bearing-stage as a distinct condition — halt, escalate, or retry. **Target: 0.2.16 W1 cascade architecture.**

- **Role-compatibility gate in cascade orchestrator.** Origin: 0.2.15 W4 — Nemotron-as-Assessor produced 65 chars of chat-model helpfulness. Severity: **important**. The cascade should refuse (or at minimum flag) model assignments that violate roster-role compatibility. W0 vetting classifies each model per criteria; cascade orchestrator does not consult that classification. Proposal: read `tier1-roster-validation-0.2.15.json` at cascade init and assert assigned models are compatible with assigned roles. **Target: 0.2.16 W1.**

- **Thinking field language is task-dependent, not model-fixed (revision of W1 F005).** Origin: 0.2.15 W4 observation. Severity: **nice-to-have**. W1 F005 said "GLM thinks in Chinese even when responding in English." W4 cascade captured 8K chars of GLM thinking in **English** on an analytical task with English input. F005 should be updated: thinking language tracks task context, not fixed per model. Not a harness change — a documentation refinement. **Target: 0.2.16 W0 — update W1 fitness report or reference doc.**

- **Cascade wall-clock characterization for cross-model.** Origin: 0.2.15 W4 (this run). Severity: **nice-to-have**. Cross-model cascade ran 366.85s vs 1,867s Qwen-solo baseline (5x faster) but produced 3,124 chars vs 14,725 (5x less). Most speed advantage is Nemotron (2s) and Llama (10-20s) being fast, not GLM or Qwen being different. Baseline expectations for fair comparison require Producer working. **Target: 0.2.16 documentation after Producer fix.**

- **VRAM-hygiene enforcement in `orchestrator.run_cascade()`.** Origin: 0.2.15 W4 — the W4 runner had to supplement orchestrator with explicit `unload_model()` calls between stages. Severity: **important**. Orchestrator relies on Ollama's LRU and does not handle Nemotron auto-load or GLM OOM-kills-all. Propose: `run_cascade()` accepts a `vram_hygiene=True` flag (default True for cross-model cascades) that calls `unload_model()` + 3s grace on any model-change boundary. **Target: 0.2.16 W0 or W1.**

- **Orchestrator `workstream_id` is hardcoded to `"W1"`.** Origin: 0.2.15 W4 observation. Severity: **nice-to-have**. `src/aho/pipeline/orchestrator.py:148,198` emits `pipeline_handoff` events with `workstream_id="W1"`. Fine for 0.2.14 W1 but wrong for every later workstream that runs a cascade. Make it a parameter with a sensible default. **Target: 0.2.16 W0.**

---

**Total items:** 27.

**By severity:** 2 critical, 14 important, 11 nice-to-have.

**By target:**
- 0.2.16: 23 items (substrate hygiene, cascade improvements, install.fish, documentation, W4 cascade-specific fixes)
- 0.2.17+: 4 items (fleet bootstrap, roster expansion, RAG, Firestore)

**Two critical items:**
1. `install.fish` Tier 1 section finalization — blocks the "Tier 1 shippable" claim.
2. Qwen `num_predict=2000` is insufficient for Producer role on long prompts — blocks clean Pillar 7 comparison and is the measured root cause of the cascade integration flake (W3 F001).

Everything else can slip without iteration damage.
