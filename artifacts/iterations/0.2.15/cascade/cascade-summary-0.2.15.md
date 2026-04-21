# Cross-Model Cascade Summary — aho 0.2.15 W4

**Run ID:** `w4-cross-model-1776790990`
**Started:** 2026-04-21T17:03:14Z · **Completed:** 2026-04-21T17:09:21Z
**Document:** `artifacts/iterations/0.2.15/cascade/nosql-manual-text.txt` (247,275 chars — PDF-extracted from 0.2.14 NoSQL manual)
**Dispatcher:** W2-hardened `src/aho/pipeline/dispatcher.py`, `/api/chat`, `num_ctx=32768`
**Stage order:** canonical (`indexer_in → producer → auditor → indexer_out → assessor`) per `src/aho/pipeline/orchestrator.py`

---

## Role assignment

| # | Role | Model | Family | Rationale |
|---|---|---|---|---|
| 1 | indexer_in | `llama3.2:3b` | llama3 | Fast triage-tier (W0: 0.71s structured output). |
| 2 | producer | `qwen3.5:9b` | qwen | Strongest general capability, workhorse. |
| 3 | auditor | `haervwe/GLM-4.6V-Flash-9B:latest` | glm | **Different family from producer — Pillar 7 separation.** `num_gpu=30` partial offload. |
| 4 | indexer_out | `llama3.2:3b` | llama3 | Fast triage on auditor findings. |
| 5 | assessor | `nemotron-mini:4b` | nemotron | Structured assessment. Compromised on identity (W0) but functional for classify-class tasks. |

Producer ≠ Auditor by weights, family, tokenizer, and training distribution. This is the first cross-model cascade run in aho history.

Baseline for comparison: 0.2.14 W1.5 run-2 (Qwen-solo, same document, same orchestrator, W1.5-fixed dispatcher) — 14,725 total output chars across 5 stages, 1,867.34s wall clock, 0 exceptions.

---

## Per-stage metrics

| # | Role | Model | Wall | Chars | eval_tokens | prompt_tokens | thinking_chars | Template leak | Error |
|---|---|---|---|---|---|---|---|---|---|
| 1 | indexer_in | llama3.2:3b | 20.31s | 613 | 131 | 32,768 | 0 | none | none |
| 2 | producer | qwen3.5:9b | 151.67s | **0** | 2,000 | 32,768 | 8,026 | none | none |
| 3 | auditor | GLM 9B | 138.87s | 777 | 1,816 | 233 | 8,002 | none | none |
| 4 | indexer_out | llama3.2:3b | 10.5s | 1,669 | 336 | 247 | 0 | none | none |
| 5 | assessor | nemotron-mini:4b | 2.08s | 65 | 16 | 854 | 0 | none | none |

**Totals:** 366.85s wall clock · 3,124 output chars · 0 dispatcher errors · 0 template leaks detected · 2 distinct model families in Producer vs Auditor.

VRAM hygiene: explicit `unload_model()` between stages kept load points clean. Nemotron auto-load (W1 F004) was suppressed by pre-stage unloads. No GLM OOM (W1 F007) — GLM loaded cleanly at ~8,143 MiB with `num_gpu=30`.

---

## The headline: Producer emitted 0 chars

Qwen 3.5:9b in the Producer role on the 247K-char document with 32,768-context produced **empty visible content** despite completing its 2,000-token num_predict budget. The inspection reveals:

- `message.content` = `""` (0 chars)
- `message.thinking` = 8,026 chars of internal reasoning
- `eval_count` = 2,000 (exactly hit the W2 num_predict cap for Qwen family)
- `prompt_eval_count` = 32,768 (context fully consumed)
- `done_reason` = "length" (from raw body — cut by num_predict, not by natural stop)

**What happened:** Qwen's thinking-mode internal reasoning consumed the entire 2,000-token output budget before emitting any visible content. W1 F001 warned thinking-mode uses "~150-200 internal tokens per response" — on this cascade prompt (large document + indexer_in output + Producer system prompt), the thinking phase ran much longer. 2,000 is not a headroom, it is a hard cap, and the cap was reached mid-think.

**This reproduces W3 F001 (cascade integration flake) live.** W3 deselected `test_cascade_end_to_end` from baseline because of the same symptom. The W4 cross-model run confirms the root cause: on prompts of this size class, Qwen's `num_predict=2000` is insufficient for both thinking and visible output.

**Remediation options (none adopted in W4 — carried forward):**

1. Raise Qwen `num_predict` to 6,000–8,000 in `MODEL_FAMILY_CONFIG`. Risk: larger num_predict does not guarantee content appears; thinking can grow unboundedly.
2. Suppress thinking mode via `/no_think` prefix or `think: false` option (verify API support). Loses analytical depth.
3. Switch to a non-thinking Qwen variant for Producer role. Requires re-vetting.
4. Shorten the Producer's input (chunked document, pre-summarized by indexer_in). Requires cascade architecture change.

Decision deferred to 0.2.16 — see carry-forwards-0.2.15.md.

---

## Pillar 7 assessment — cross-model auditor did NOT rubber-stamp

The Pillar 7 value hypothesis was: **a different-family Auditor produces structurally different critique than a same-family Auditor (Qwen-solo rubber-stamp pattern, 0.2.14 W1.5)**.

Because Producer emitted 0 chars, the W4 Auditor did not audit a real analytical draft. It audited the literal string `[stage producer failed: None]` (the cascade's failure marker). This is a weaker Pillar 7 test than planned — we did not compare GLM-critique-of-Qwen-output against Qwen-critique-of-Qwen-output.

However, the Auditor's behavior is still informative:

### §A · GLM identified the failure

GLM's processed output (verbatim):

> ```json
> {
>   "analysis_review": "The Producer Analysis is not accurate as it only contains '[stage producer failed: None]', which does not analyze the provided technical notes about data storage systems.",
>   "delta_validations": [
>     {"accepted": true, "reasoning": "The text mentions '100ms' multiple times as a target latency value for systems like Neo4j and Redis, so extracting this metric is warranted despite the lack of an explicit question."}
>   ],
>   "additional_findings": [
>     "The original text lacks a clear problem statement or question that can be answered with a single numerical value.",
>     "The Producer Analysis does not provide any meaningful analysis beyond a system-level failure message."
>   ]
> }
> ```

This is **not a rubber-stamp pattern**. Compare to 0.2.14 W1.5 assessor (Qwen), which accepted all 4 delta proposals with generic reasoning. GLM here:

- Explicitly flagged the Producer Analysis as inadequate with citation.
- Validated one delta proposal with a substantive reasoning line (cites "100ms" appearances in the source text).
- Surfaced two independent findings in `additional_findings`, both correct.

The auditor would not produce this output by pattern-matching a template. The failure-detection behaviour requires actual reading of the Producer input.

### §B · Thinking field landed in English, 8K chars

W1 F005 predicted GLM emits Chinese internal reasoning. The auditor's `thinking` field is 8,002 chars — substantial — and **English**, not Chinese. Representative excerpt:

> "First, I need to review the Producer Analysis and Indexer-in's proposed deltas. First, the Producer Analysis says '[stage producer failed: None]'. That seems like a placeholder or maybe an error message? So the analysis part from the Producer is just that string."

The Chinese-thinking observation from W1 was on an identity probe (model-name query). On this analytical task, GLM's thinking mirrors the task language. This is a refined data point on F005: thinking language is task-context-dependent, not fixed per model.

**Observability note:** 8,002 chars of analytical reasoning lives in the `thinking` field but does not propagate to Indexer-out or Assessor. Downstream stages see only the 777-char `content` conclusion. This is a carry-forward for 0.2.16 — whether to propagate `thinking` as part of stage handoff.

### §C · Pillar 7 verdict

- **Claim A (GLM-as-Auditor does not rubber-stamp):** supported by the evidence above. Single data point, but a clean one.
- **Claim B (cross-model cascade produces better output than Qwen-solo):** **not supported** by this run. Total chars 3,124 vs 14,725 baseline — worse. Root cause is Producer failure, not the cross-model assignment. Under controlled Producer conditions (num_predict raised, or thinking-mode suppressed), the cross-model cascade remains worth testing.
- **Claim C (cross-model cascade introduces new failure modes):** supported. The cascade handoff forwarded an error-marker string as Producer output to the Auditor. The Auditor handled it correctly — but downstream stages propagated attempts to "fix" a failure marker they should have halted on. No stage explicitly errored on the empty Producer output; all treated it as content. This is a cascade-protocol gap independent of model choice.

**Verdict:** Pillar 7 has its first real, small data point — GLM in the Auditor role behaves substantively differently from the Qwen-solo rubber-stamp pattern. The test was partially compromised by a substrate issue (Qwen num_predict exhaustion) that is independently addressable. Re-running the cascade with a fixed Producer substrate is the next step; it would be the first fair Pillar 7 comparison. That re-run belongs to 0.2.16 W0 or W1 — not W4.

---

## Stage-by-stage quality read

### Stage 1 — Llama indexer_in (20s, 613 chars)

Llama 3.2:3B summarized the document reasonably and proposed extracting "100ms" as a latency target. The output is terse but on-topic. `prompt_eval_count=32768` confirms the document was truncated at the context boundary (247K chars → 32K tokens) — Llama saw only a window of the document, consistent with W1.5 baseline context-truncation behavior.

### Stage 2 — Qwen producer (152s, 0 chars)

Fatal for this cascade. 8,026 chars of thinking, 0 chars of content, num_predict hit. See "Producer emitted 0 chars" above.

### Stage 3 — GLM auditor (139s, 777 chars)

Substantive. Identified Producer failure. Validated Indexer-in's 100ms delta with specific reasoning. Produced two additional findings. No template leakage (W2 fix confirmed in production). `num_gpu=30` partial offload held — no OOM. Inference at ~1 token/s roughly matches W1 R2 partial-offload measurements.

### Stage 4 — Llama indexer_out (11s, 1,669 chars)

Picked up on Auditor's critique of Producer and proposed deltas to "enhance Producer Analysis." Cascade information flow worked — Auditor's findings reached Indexer-out. However, Indexer-out proposing deltas about a failed Producer is misdirected; a robust cascade would halt or escalate on empty Producer output, not propose fixes to it.

### Stage 5 — Nemotron assessor (2s, 65 chars)

Vacuous. Output: `" Sure, I'll incorporate those deltas into my work product output."` That is a chat-model helpfulness response, not an Assessor's meta-evaluation. Nemotron-mini:4b cannot substantively assume the Assessor role on this kind of input. This is **consistent with W0 finding** (Nemotron classified as `compromised` on identity and instruction-following, functional only on narrow classify tasks). The W4 launch prompt anticipated this risk; the finding confirms Nemotron is not an Assessor-class model.

---

## Cascade protocol gaps surfaced

1. **Empty-content handoff is not an error.** The dispatcher returned `error=None` on a 0-char producer response. My runner converted that to `"[stage producer failed: None]"` as a cascade input to next stage — which propagated downstream. The dispatcher should surface empty content (when not expected) as a distinct condition; or the cascade should halt on empty content from a stage whose output is load-bearing.

2. **No stage timeouts defined per role.** W4 used a blanket 1800s per-stage timeout. Nemotron completed in 2s; GLM needed 139s. Role-appropriate timeouts would flag stalls faster.

3. **Thinking-field propagation unsettled.** 8,002 chars of GLM auditor reasoning did not reach downstream. If cascade quality depends on reasoning being visible downstream, this is a design gap.

4. **No role-compatibility assertion.** Nemotron-as-Assessor was attempted despite W0 classification of `compromised`. The cascade should refuse (or flag) model assignments that violate role-compatibility gates. Not in scope for W4 but measurable.

---

## What the next cascade run should test

- **Controlled Producer run:** num_predict=8000 for Qwen family; or `/no_think` prefix added. Measure whether content appears.
- **Real Pillar 7 comparison:** With Producer working, run (a) Qwen-solo cascade and (b) cross-model cascade on the same document. Compare Auditor output structure directly.
- **Assessor role without Nemotron:** Assign Qwen or GLM to the Assessor role to isolate whether the 65-char vacuous output is role-prompt weakness or Nemotron role-fit weakness.
- **Thinking-field propagation experiment:** Modify cascade to include `thinking` in Auditor's handoff to Indexer-out. Measure whether downstream stages use the additional signal.

None of these are W4 scope; all are carry-forwards.

---

*Raw response inspection performed per stage. Full per-stage artifacts at `stage-1-indexer_in.json` through `stage-5-assessor.json`. Trace at `trace.json`. No template leaks. 0 git operations. 0 cross-project contamination (all references to aho canonical).*
