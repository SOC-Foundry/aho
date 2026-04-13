# Retrospective — aho 0.2.14

**Phase:** 0 | **Iteration:** 0.2.14 | **Executor:** claude-code (drafter) | **Auditor:** gemini-cli
**Theme:** Council wiring verification + cascade smoke test
**Status:** 4 workstreams delivered (W0, W1, W1.5, W2). W1.5 added mid-iteration after W1 audit findings.
**Execution model:** Pattern C modified (Claude drafts, Gemini audits, Kyle signs)

---

## §1 What was planned

3 workstreams across 2 sessions:

- **W0 — Setup + Hygiene.** Version bumps, root cleanup proposal, README/CHANGELOG append, Pattern C protocol patches, `emit_workstream_complete()` side-effect fix, council model docs, council inventory, NoSQL manual staging.
- **W1 — Vet + Wire + Smoke.** Council vetting (all 16 members), pipeline schemas + cascade orchestrator build, integration test on dummy document, NoSQL smoke test on 247K-char manual. Two internal hard gates.
- **W2 — Close + Sign-off.** Council health rerun, wiring sign-off package, retrospective, carry-forwards, bundle, sign-off sheet.

Charter was binary: does the council exist as a verifiable wired system? Answer that before any 0.2.15 measurement.

Success criterion: wiring verified, sign-off on member operational status, NoSQL smoke test executes 5-stage cascade end-to-end.

## §2 What was delivered

4 workstreams shipped:

- **W0** — Setup, hygiene, model docs, inventory. 9 acceptance checks, all pass. `emit_workstream_complete` patched with sibling-preservation test. NoSQL manual extracted (201 pages, 247K chars). Audit: pass (no Gemini audit archive located; accepted on substance).
- **W1** — Full council vetting (16 members → 12 operational, 2 substrate-compromised, 1 configured-incomplete, 1 gap). Pipeline built (`schemas.py`, `dispatcher.py`, `orchestrator.py`). Root cleanup executed (29 files moved). Smoke test run-1 completed 5/5 stages. Audit: `pass_with_findings` — Gemini identified two dispatcher bugs and characterization drift.
- **W1.5** — Substrate repair workstream added mid-iteration. Dispatcher migrated from `/api/generate` to `/api/chat`. `num_ctx` set to 32768. Stop tokens added. 6 unit tests. Re-smoke (run-2): all 6 hard gates pass. Audit: `pass`.
- **W2** — Close. Council health rerun (35.3/100, stale formula). Wiring sign-off package. This retrospective. Carry-forwards. Bundle. Sign-off sheet.

W1.5 was not in the original plan. It was added because Gemini's W1 audit surfaced dispatcher bugs that contaminated the smoke test results. Adding W1.5 was a substrate-truth response — the iteration could not honestly close on W1's smoke test data when the dispatcher was misconfigured. This was scope expansion in service of honesty, not iteration overrun.

## §3 W1 substrate findings — the headline

The smoke test in W1 appeared to complete — 5/5 stages, 0 exceptions, all artifacts written. Claude characterized the results as cascade-proven with model-quality limitations. Gemini's audit looked at the raw artifacts and found something different.

**Two compounding dispatcher bugs:**

1. **`num_ctx` defaulted to 4096.** Ollama's default context window is 4096 tokens. The 247K-character NoSQL document was truncated to approximately the last 4K tokens before the model ever saw it. The indexer_in stage analyzed only pages 194-201 (the document tail) because that's all that fit in 4K tokens. The producer received truncated indexer_in output about the document tail plus the truncated document itself — insufficient context to understand the task.

2. **`/api/generate` used instead of `/api/chat`.** The generate endpoint does not apply the chat template. For Qwen (a chat model with `<|im_start|>` / `<|im_end|>` template tokens), this caused: (a) system prompt not properly delineated from user content, (b) chat template special tokens leaked as visible output, (c) model attempted to simulate multi-turn conversations within a single response, (d) language drift to Chinese (model's training distribution without chat template constraint).

**These are not model-quality issues. They are dispatcher configuration issues that contaminated all model-quality measurements from run-1.**

Gemini's W1 audit identified two characterization drifts: Claude called indexer_out's output "honest empty response" when raw artifacts showed turn-simulation leakage and truncation; Claude attributed quality issues primarily to context truncation when template leakage was an equally significant cause.

**Run-1 vs run-2 comparison (the proof):** Producer went from 222-character Chinese customer-service persona to 3,908-character substantive English NoSQL scaling analysis. The only change: dispatcher configuration. Same model, same prompts, same document.

## §4 Cascade architecture is real

Five-stage pipeline executed end-to-end on a 247K-character technical document with substantive, on-topic output per stage (run-2 data):

- **Indexer_in** (486s, 3,550 chars): Analyzed Sections 71-100, identified optimization strategies, proposed technical deltas.
- **Producer** (464s, 3,908 chars): Generated scaling performance analysis with metrics table, covering data pipeline architectures from the source document.
- **Auditor** (571s, 2,174 chars): Single coherent JSON. Validated producer's analysis, identified decision ambiguity between Options 3 and 4.
- **Indexer_out** (213s, 2,031 chars): Responded to auditor's findings by proposing 3 substantive configuration deltas.
- **Assessor** (134s, 3,062 chars): Comprehensive meta-assessment. Validated cross-stage coherence. Accepted all 3 indexer_out deltas. Quality score 92 (model self-assessment — signal, not ground truth).

Cross-stage coherence validated: auditor's findings about producer ambiguity appear in indexer_out's proposed deltas, which appear in assessor's accepted validations. This is actual sequential handoff with information flow, not five parallel generations.

Total wall clock: 31.1 minutes on consumer hardware (2080 SUPER, Q4_K_M quantization). VRAM: 7.2/8.2 GB stable, no OOM.

## §5 Pillar 7 violation persists

All 5 cascade roles bound to Qwen 3.5:9B. The model that produced artifacts also audited them. This is a known, acknowledged violation of Pillar 7 ("Generation and evaluation are separate roles").

**Why it persists:** W1 vetting found only one operational LLM capable of structured analytical output. Nemotron defaults to "feature" 80% of the time. GLM times out 80% of the time and uses wrong JSON schema. OpenClaw is a Qwen wrapper, not a distinct capability. No other LLM was available for role separation.

**Path to restoration:** 0.2.15 matrix testing with expanded roster. Llama 3.2 3B already on disk (triage officer candidate — lightweight, fast, different training). DeepSeek-Coder-V2 16B-Lite for code specialization. Mistral-Nemo 12B for long-context. Gemma 2 9B as Pillar 7 evaluation partner (different weights, different training distribution from Qwen). Real role-model fit data from the matrix determines which models take which roles.

## §6 Council composition reframing

Mid-iteration realization: the current composition (Qwen + Nemotron + GLM + OpenClaw) was inherited from earlier work and never revisited against operational evidence.

- 0.2.13 W2.5 showed Nemotron and GLM substrate-compromised
- 0.2.14 W1 vetting confirmed both still substrate-compromised
- OpenClaw confirmed as Qwen wrapper — cosmetic council member

The council's LLM layer is effectively Qwen-solo. This has been true since at least 0.2.12, masked by parsers that silently converted failures to positive results (fixed in 0.2.13 W1-W2).

Council composition review is now a 0.2.15 carry-forward with specific candidates:

- **Llama 3.2 3B** — triage officer, lightweight classification, already on NZXTcos disk
- **DeepSeek-Coder-V2 16B-Lite** — code specialization (Q4_K_M, NOT Q2 — quantization quality tradeoff documented in W1.5 session)
- **Mistral-Nemo 12B** — long-context candidate
- **Gemma 2 9B** — Pillar 7 evaluation partner

Architectural question also surfaced: capability-routed cascade (triage officer routes to specialist by task type) vs current fixed role-assigned cascade (same sequence regardless of input). Both valid designs with different matrix implications. 0.2.15 design decision.

## §7 Pattern C trial — second iteration data

0.2.14 is the second iteration using Pattern C (first was 0.2.13).

**What worked:**

- **State-machine discipline held.** After 0.2.13 W0 corrections (role-crossing, terminal event ambiguity), the checkpoint lifecycle was clean for 0.2.14. `workstream_start` emitted at workstream begin (0.2.13 fired zero). No role-crossing incidents. Audit-then-terminal-event sequence respected.
- **Gemini audits caught real issues.** W1 audit identified the dispatcher bugs and characterization drift that Claude missed. This was the highest-value audit in Pattern C's history — it directly caused W1.5 to exist, which fixed the substrate and produced honest smoke test data. Without the audit, 0.2.14 would have closed on contaminated data.
- **Audit overhead bounded.** W1 audit: 42 min (complex, highest-value). W1.5 audit: 25 min. Overhead is proportional to workstream complexity.

**What didn't work:**

- **W1's "smoke test passed" framing was based on parsed JSON, not raw response inspection.** Claude verified that stages completed, that JSON was parseable, that traces existed — and characterized this as success with quality caveats. Gemini looked at the raw response text and found template token leakage, truncation, and turn simulation that the parsed-JSON view did not expose. **Protocol gap:** no rule requiring raw response inspection. Now a carry-forward: "Raw response field is ground truth for output integrity inspection."
- **Auditor rubber-stamp pattern.** W1.5 auditor (assessor stage) accepted all 4 deltas proposed by indexer_out. Its `additional_findings` section showed real critique capability (identified areas for improvement), but the `delta_validations` section accepted everything. Bifurcation between the "validate" role (rubber-stamp) and the "find issues" role (genuine critique) is a prompt design problem. The auditor can critique but the validation structure doesn't force it to act on its own critique.
- **Checkpoint corruption from test suite.** `test_workstream_events.py` doesn't mock `find_project_root`, causing real checkpoint writes during test runs. Checkpoint accumulated spurious entries (W_V3_TEST, W_V1_COMPAT, etc.) that are test artifacts, not real workstreams. Caused checkpoint resets 3 times during W1. Deferred fix.

**Pattern C value assessment after two iterations:**

The W1 audit that surfaced dispatcher bugs is sufficient evidence that Pattern C produces value. A single-agent iteration would have closed 0.2.14 on run-1 data — cascade "proven" with contaminated results. The audit overhead (42 min for W1, 25 min for W1.5) was trivially small compared to the cost of building 0.2.15 measurement on a broken substrate.

## §8 Honest read on whether the council is real

**What exists:**

- Cascade architecture: 5-stage pipeline with sequential handoff, trace events, per-stage artifacts, delta staging. Mechanically proven on a real 247K-character document.
- Wiring: dispatcher → Ollama HTTP API, role-configurable model assignment, cascade orchestrator, pipeline schemas (RoleAssignment, PipelineTrace, DeltaProposal, DeltaValidation).
- Cross-stage coherence: information flows from indexer_in through producer through auditor through indexer_out to assessor. Downstream stages reference upstream findings. This is not parallel hallucination.
- Council infrastructure: 12/16 members operational, Nemoclaw dispatch with role bypass, ChromaDB + nomic-embed-text for future retrieval.

**What does not exist:**

- Pillar 7 separation. One LLM does everything. The model that generates is the model that evaluates. This is structurally present (roles are assignable to different models) but not materially realized.
- Multi-model role fitness data. No evidence that Qwen is the right model for any particular role. No comparison data. No matrix.
- Auditor structural integrity. The auditor can critique but its validation structure doesn't force it to act on its own findings. Rubber-stamp pattern in delta validations alongside genuine critique in additional findings.
- Chat-model discipline. Every stage ends with helpful follow-up questions or offers of assistance — a chat-model training artifact. System prompts need "output final deliverable, do not ask follow-up questions" baked in.
- Thick council. Two LLMs substrate-compromised since 0.2.13. One LLM is a wrapper of the only working one. Roster expansion is planned but not yet landed.

**Assessment:** Council is real-but-thin. The cascade works mechanically and produces coherent output when the dispatcher is correctly configured. But "works mechanically with one model" is the floor of what "council" means, not the ceiling. 0.2.15's matrix work — expanded roster, role-model fit measurement, Pillar 7 restoration — is what determines whether the council becomes a genuine multi-agent system or remains a Qwen pipeline with extra steps.

Not failure. Substrate truth. The wiring is done. What runs through it is the next question.
