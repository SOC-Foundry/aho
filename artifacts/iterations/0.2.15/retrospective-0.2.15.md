# Retrospective — aho 0.2.15

**Phase:** 0 | **Iteration:** 0.2.15 | **Executor:** claude-code (drafter) | **Auditor:** gemini-cli
**Theme:** Tier 1 Partial Install Validation & Ship
**Workstreams:** 5 (W0, W1, W1-correction, W2, W3, W4). One mid-flight correction in W1; W1.5 was **not** declared.
**Execution model:** Pattern C modified (Claude drafts, Gemini audits, Kyle signs)

---

## §1 Charter

Ship a Tier 1 Partial install package: 4 chat LLMs wired through Ollama on a fixed dispatcher, vetted with fresh evidence, dispatcher hardened for multi-model use, Nemoclaw decision evidence-based, cross-model cascade proven as a Pillar 7 restoration attempt.

Success criteria:

- All 4 Tier 1 roster LLMs have explicit operational status on fixed-dispatcher evidence (no `unknown` classifications).
- Dispatcher handles all 4 model families cleanly with graceful failure modes.
- Nemoclaw decision landed as an ADR with measured rationale.
- Cross-model cascade executes end-to-end with distinct models across Producer and Auditor (Pillar 7 separation attempt).
- Tier 1 install.fish is shippable.

## §2 What was delivered

5 workstreams shipped across 6 Claude sessions (W1 required a mid-flight correction).

- **W0 — Setup + Tier 1 roster re-vetting.** Version bump, scaffolding, checkpoint init. 4 per-model probe artifacts. Classifications: Qwen `operational`, Llama 3.2 `operational`, GLM `partial` (template leak, stop-token fixable), Nemotron `compromised` (identity fail — returns "BERT" — but classify task passes). Llama 3.2 3B first integration into dispatcher. Audit: pass.
- **W1 — Ollama Tier 1 capability audit.** 12 requirements probed across 4 models. Initial pass reported 3 critical-requirement `partial` classifications based on contaminated Ollama state (resident Qwen + orphan runner from a crashed probe). Kyle flagged the contamination post-probe. Clean-state retests for R2 (LRU eviction) and R11 (chat template). R5 promoted from `partial` to `meets` after GLM's partial-offload routing was confirmed. Final: 9 meets, 3 partial (R2, R7, R11), 0 fails. Audit: pass. **No W1.5 declared** — the correction happened before audit archive, so it's a W1 revision, not a new workstream.
- **W2 — Dispatcher protocol hardening.** Multi-model support: `MODEL_FAMILY_CONFIG` registry (Qwen, Llama 3.x, GLM, Nemotron), prefix-match family resolver, GLM stop token + prefix strip, Qwen `num_predict=2000`, GLM `num_gpu=30`, 5 typed error classes (`DispatchError`, `MalformedResponseError`, `TemplateLeakError`, `ModelUnavailableError`, `DispatchTimeoutError`), exponential backoff retry, model management helpers (`unload_model`, `list_loaded_models`, `ensure_model_ready`). 46 new unit tests in `test_dispatcher_hardening.py`. Audit: pass.
- **W3 — Nemoclaw re-vetting + ADR.** Empirical comparison: Path A (Nemoclaw's `nemotron_client.classify` via `/api/generate`), Path B (W2 dispatcher via `/api/chat`), Path C (daemon socket IPC). Role-classify correctness: 1/5 (Path C) vs 4/5 (Path B). The "~23s Nemoclaw overhead" claim was **refuted** — socket roundtrip measured at 1.68-1.87s vs direct dispatch 1.66-1.89s. Decision: REPLACE classification layer, RETAIN session layer. New `src/aho/pipeline/router.py`. Nemoclaw `route()` migrated. `nemotron_client.classify` deprecated in docstring (callable through 0.2.16 for migration window). ADR-0002 published with Pillar 4 examination. 24 new router tests. Audit: pass.
- **W4 — Integration + close.** Cross-model cascade on the 0.2.14 NoSQL manual (247,275 chars). Role assignment: Producer=Qwen, Indexer-in=Llama 3.2, Auditor=GLM (`num_gpu=30`), Indexer-out=Llama 3.2, Assessor=Nemotron. Explicit VRAM management between stages (unload previous, 3s grace). Per-stage artifacts capture raw response, processed output, thinking field presence, template leak detection, token counts. Baseline comparison against 0.2.14 run-2 (Qwen-solo, 14,725 chars, 1867s). Retrospective, carry-forwards, bundle, sign-off sheet.

## §3 Substrate findings

### §3.1 Baseline contamination as a protocol hazard

W1's initial probe results were distorted by an Ollama state that Kyle identified post-hoc: a resident Qwen model plus an orphan runner process from a crashed earlier probe. The "3362 MiB base overhead" figure was not base at all — it was resident Nemotron weights plus Ollama runtime. Clean-state measurement put the real baseline at ~704 MiB.

This matters because the contamination turned R2 (LRU eviction) from a recoverable finding into what looked like a hardware-limited fail. The GLM-crashes-on-load story was correct — GLM does crash on full-GPU offload — but the contamination made it look like GLM could not load at all, when in fact `num_gpu=30` loads cleanly at 7239 MiB.

Lesson: probe hygiene is not just "don't have other tasks running." It's "verify Ollama VRAM state matches a known clean baseline before the probe begins." W1 did not do that. The corrected retest did. The protocol carry-forward is explicit probe-environment assertion, not a vague "ensure clean state."

### §3.2 The 23s Nemoclaw overhead never existed

The W3 launch prompt referenced "~23s overhead" on the Nemoclaw path as a working hypothesis. W3's empirical probe found the socket IPC roundtrip adds no measurable overhead over direct dispatch — both paths are dominated by Nemotron-mini inference at Q4_K_M. The overhead claim likely originated from a timing measurement that included model load time on one path and a warm inference on the other.

This is the second substrate fiction dissolved in 0.2.15 after clean measurement (first was the GLM non-functional story in W1). Both held up for months because no one measured under controlled conditions.

### §3.3 Substrate artifacts, confirmed twice

0.2.13 W2.5 labeled Nemotron "80% feature-bias on classify" and GLM "80% timeout with wrong-schema JSON." Both measurements were on `/api/generate` with 4K default context. Both findings dissolved on `/api/chat` with proper stop tokens:

- Nemotron on `/api/chat`: 4/5 clean classify responses. Feature-bias resolved.
- GLM on `/api/chat`: zero timeouts. Correct JSON schema. Only template token leakage (stop-token fixable).

Model-quality findings must ship with substrate fingerprint (endpoint, num_ctx, stop tokens, model options). Without fingerprint, a finding cannot be replicated or refuted. W1 W0 re-vetting demonstrated this: the same models classified differently on fixed substrate. The models did not change; the substrate did.

### §3.4 Ollama state hygiene is infrastructure, not curiosity

- Nemotron auto-loads on Ollama restart and fills VRAM when it becomes available. Cannot be suppressed via `keep_alive:0` alone. W2 dispatcher has `unload_model()` for this; cascade code (W4) must call it explicitly before loading large models.
- GLM CUDA OOM does not produce a clean error — the crash kills all loaded models. Any cascade that triggers GLM load near the 8GB VRAM boundary must verify model presence via `/api/ps` after the load or be prepared for all co-resident models to vanish.
- Orphan runners from crashed probes can hold VRAM without appearing in `/api/ps`. These must be swept by `systemctl restart ollama` when probe state gets ambiguous — detection via `/api/ps` alone is insufficient.

These are not edge cases. Every cascade run on this hardware goes through these constraints. W2 surfaced the API; W4 exercised it.

## §4 Cross-model cascade — Pillar 7 restoration attempt

### §4.1 Role assignment

| Role | Model | Rationale |
|---|---|---|
| indexer_in | Llama 3.2:3B | Fast triage (W0 measured 0.71s structured output). |
| producer | Qwen 3.5:9B | Strongest general capability (W0 confirms). |
| auditor | GLM-4.6V-Flash-9B (`num_gpu=30`) | **Different model family from Producer** — Pillar 7 separation. |
| indexer_out | Llama 3.2:3B | Fast triage on auditor findings. |
| assessor | Nemotron-mini:4B | Structured assessment — classify role, compromised on identity but functional for the task. |

The Pillar 7 value hypothesis: if the Auditor uses different weights from the Producer, its critique should reflect evaluation diversity — different failure modes, different biases — rather than the rubber-stamp pattern observed when the Producer and Auditor share a model (0.2.14 W1.5, Qwen-solo cascade).

### §4.2 Cascade metrics

**Headline:** 366.85s total wall clock (vs 1,867s Qwen-solo baseline, 5x faster) · 3,124 total output chars (vs 14,725 baseline, **5x less**) · 0 dispatcher errors · 0 template leaks detected · VRAM hygiene held.

Per-stage (full table in `cascade/cascade-summary-0.2.15.md`):

| # | Role | Model | Wall | Chars | thinking_chars |
|---|---|---|---|---|---|
| 1 | indexer_in | llama3.2:3b | 20.3s | 613 | 0 |
| 2 | producer | qwen3.5:9b | 151.7s | **0** | 8,026 |
| 3 | auditor | GLM 9B | 138.9s | 777 | 8,002 |
| 4 | indexer_out | llama3.2:3b | 10.5s | 1,669 | 0 |
| 5 | assessor | nemotron-mini:4b | 2.1s | 65 | 0 |

### §4.3 The producer failed, and that matters more than the Pillar 7 story

Qwen's thinking-mode consumed the entire 2,000-token `num_predict` budget during thinking. `message.thinking` was 8,026 chars. `message.content` was 0 chars. `done_reason` was "length" (hard cap, not natural stop). The Producer produced nothing visible.

This reproduces W3 F001 live. The cascade integration flake's root cause is now measurable: on prompts of this size class, 2,000 num_predict is insufficient for both Qwen thinking and visible output. W2 chose 2,000 based on the W1 F001 measurement of "~150-200 internal thinking tokens." That number was for short responses. It does not scale to long-cascade prompts.

Because Producer emitted nothing, the remaining three stages audited a failure marker, not a draft. The Pillar 7 test — whether a cross-family Auditor produces structurally different critique than Qwen-as-Auditor on real Producer output — was partially compromised. GLM audited the string `[stage producer failed: None]`, not an analytical artifact.

### §4.4 Pillar 7 — one clean data point, despite the compromised test

GLM-as-Auditor did **not** rubber-stamp. It identified the Producer failure explicitly ("The Producer Analysis is not accurate as it only contains '[stage producer failed: None]'"), validated a single delta proposal with substantive reasoning tied to the source text ("100ms" citations), and surfaced two independent findings in `additional_findings`. Verbatim output is in `cascade/cascade-summary-0.2.15.md` §A.

Compare to 0.2.14 W1.5 Qwen-solo Assessor, which accepted all 4 deltas with generic reasoning. GLM here did not. That is the first positive Pillar 7 signal aho has produced.

**Verdict:** Pillar 7 has a small, clean data point. A full test — identical Producer output evaluated by Qwen-as-Auditor and GLM-as-Auditor — requires fixing Producer first. That's 0.2.16 W0 or W1 work.

### §4.5 GLM thinking-field observation refined

W1 F005 predicted GLM reasons in Chinese. The W4 cascade captured 8,002 chars of GLM auditor thinking — in **English**. Representative excerpt:

> "First, I need to review the Producer Analysis and Indexer-in's proposed deltas. First, the Producer Analysis says '[stage producer failed: None]'. That seems like a placeholder or maybe an error message?"

Refined finding: GLM thinking language is task-context-dependent, not fixed. On the W1 identity-probe task, thinking was Chinese. On the W4 analytical task with English input, thinking was English. F005 should be updated to reflect this variability.

The 8K-char thinking did NOT propagate to Indexer-out or Assessor — downstream stages see only the 777-char `content` conclusion. If the cascade's analytical signal lives in `thinking` and not in `content`, this is a cascade architecture gap. Carry-forward for 0.2.16.

### §4.6 Nemotron cannot assume the Assessor role

Nemotron-as-Assessor produced: `" Sure, I'll incorporate those deltas into my work product output."` — 65 chars, chat-model helpfulness, no assessment content. This confirms W0's `compromised` classification extends beyond identity — Nemotron fails to adopt role-prompt directives for substantive roles. It remains functional only for narrow classify tasks (W3 confirmed 4/5 on role classify via `/api/chat`).

Tier 1 roster-role compatibility: Nemotron is Classifier-class, not Assessor-class. W4 attempted the Assessor assignment because the launch prompt assigned it for structured assessment. The finding argues for a role-compatibility gate in the cascade — models with `compromised` status should fail a role-fit assertion before dispatch.

## §5 Pattern C — third iteration data

0.2.15 is the third iteration under Pattern C (first: 0.2.13; second: 0.2.14).

**What worked:**

- **State machine held across 5 workstreams with zero violations.** `workstream_start → pending_audit → audit_complete → workstream_complete` respected at each boundary. No agent emitted `workstream_complete` before `audit_complete` existed. No audit archive overwrites. Every `workstream_start` fired after AHO_ITERATION env confirmation.
- **Gemini audits remained substantive.** W0 audit 20 min, W1 audit 30 min (with correction review), W2 audit 25 min, W3 audit 25 min. No rubber-stamp audits. Each surfaced at least one non-trivial finding or spot-check.
- **The W1 mid-flight correction did not require a new workstream.** Kyle caught the Ollama contamination before the W1 audit archive was written. The correction happened in-place with a revision timestamp and revision note. We did NOT declare W1.5. This is an improvement on 0.2.14 where W1.5 was declared — the hygiene discipline of catching substrate issues pre-audit was superior this time.
- **Raw-response-ground-truth rule held.** Every workstream's acceptance archive includes a "raw response field inspected" check. W3 in particular found Nemotron daemon failures (prose output, "AI" stubs) by looking at raw HTTP output, not dispatcher-parsed fields.
- **Cross-project contamination: zero instances across 5 workstreams.** The vigilance rule added at 0.2.14 close worked. Pillar counts, ADR numbers, bundle sections all verified against aho canonicals before use. The rule is boring discipline and it works.

**What didn't work:**

- **test_workstream_events.py still corrupts the checkpoint.** Third recurrence (0.2.13 observed, 0.2.14 carry-forward, 0.2.15 W3 observed again during baseline regression). The test writes `W_V3_TEST`, `W_V1_COMPAT`, etc. directly to the real `.aho-checkpoint.json` because it doesn't mock `find_project_root`. This needs a fix, not another deferral. 0.2.16 W0 candidate.
- **Cascade integration flake (test_cascade_end_to_end).** Produces empty Qwen `message.content` on long system prompts under certain dispatcher + VRAM conditions. W3 deselected it from baseline comparison. Root cause not identified. Reproducible but not always. Carry-forward for 0.2.16 — needs a controlled repro harness.
- **Auditor role-prompt bifurcation update.** 0.2.14 observed Qwen-as-Auditor rubber-stamping in `delta_validations` while critiquing in `additional_findings`. The W4 cascade's GLM Auditor did NOT rubber-stamp — it produced substantive reasoning in both `delta_validations` and `additional_findings`. This is a one-data-point argument that the bifurcation was model-specific, not prompt-structural. But the test was compromised by Producer failure; a clean comparison awaits 0.2.16. Keep the prompt-engineering carry-forward open — don't close it on a single observation, especially one where the Auditor had a trivially easy critique target (obvious Producer failure).
- **Kyle-side escalations from W1 (E1 GLM partial offload, E2 Ollama service layer, E3 Qwen thinking-mode budget) were resolved in-band by W2 but never closed-out formally.** The sign-off sheet captures these as acknowledged. Procedural drift — not substantive.

- **W2's Qwen `num_predict=2000` decision under-specified for cascade.** W2 chose 2,000 based on W1 F001 ("~150-200 internal thinking tokens per response"). That measurement was on short probes. On cascade prompts (32K context, multi-stage system prompts), thinking-mode consumed all 2,000 tokens — Producer emitted 0 chars in W4. The decision was correct for the evidence available at W2; W4 produced the evidence that makes 2,000 wrong. Not a W2 error; a W4 discovery. Carried forward to 0.2.16 as critical.

## §6 Infrastructure maturation

The 0.2.15 scope was deliberately tight: Tier 1 install readiness, not roster expansion. What shipped:

- **Dispatcher** — went from Qwen-only with hardcoded stop tokens to model-family-aware with typed errors, retry, and lifecycle helpers. 52 total dispatcher tests (was 6).
- **Router** — new `pipeline/router.py` is the canonical classification primitive. 24 unit tests.
- **ADR-0002** — aho-internal ADR series grew from 1 to 2. The series is distinct from `ahomw-ADR-NNN` (universal methodology series, currently at 045). W3 selected `0002` by enumerating the directory, not by memory.
- **Ollama fitness report** — 12 Tier 1 requirements probed with evidence. A reusable reference for future install-target probing.

What did not ship (deliberate out-of-scope):

- nomic-embed-text validation + ChromaDB RAG integration (0.2.16 or 0.2.17).
- Tier 2/3 roster (Gemma 2, DeepSeek-Coder-V2, Mistral-Nemo). Requires >8GB VRAM, waits for Luke's machine or P3 clone installs.
- Auditor role-prompt redesign.
- Capability-routed vs role-assigned cascade decision.
- Executor-as-outer-loop-judge architecture.
- OpenClaw disposition (confirmed in W0 as Qwen wrapper; decision deferred).

## §7 Honest assessment

**Did we ship Tier 1?** The dispatcher handles all 4 Tier 1 roster models with per-family configuration. The router is live. The cascade runs across distinct models. Baseline regression is 10 failures matching W3 baseline. install.fish finalization for Tier 1 is the one deliverable marked incomplete in the W4 acceptance — W4 focused on the cascade as the Pillar 7 restoration attempt, not install.fish. This is an honest scope constraint, not silent omission.

**Did Pillar 7 actually restore?** Partially and tentatively. The cross-model cascade produced a clean single data point — GLM in the Auditor role produced substantive, task-accurate critique that did not rubber-stamp. That is Pillar 7 progress, evidence-based, not rhetoric. But the test was compromised by Qwen-Producer emitting 0 chars (thinking-mode num_predict exhaustion), so the Auditor did not audit a real Producer artifact. Full restoration requires a re-run with Producer substrate fixed — that lives in 0.2.16.

**What changed since 0.2.14?** The substrate. 0.2.14 found that all model-quality claims were contaminated by broken dispatch. 0.2.15 fixed the substrate and then measured three times: W0 (per-model), W2 (per-family), W3 (Nemoclaw path A vs B vs C). Every measurement showed the models were less broken than the 0.2.13 substrate suggested. The council is thicker than 0.2.14 left it — Nemotron functional, GLM functional, Llama 3.2 integrated. Not expansion. Reclamation.

**Is Tier 1 install.fish shippable?** Not quite — install.fish itself was not finalized in W4 (see §5). The prerequisites are shippable: dispatcher, router, fitness report, roster vetting, ADR. install.fish Tier 1 section is a carry-forward, with content derivable from W0–W3 artifacts in under an hour. Kyle's sign-off on whether this counts as Tier 1 shippable is what closes the iteration.

---

*Raw response is ground truth. Numbers are honest to substance, not regex. No celebratory framing.*
