# Tier 1 Roster Validation — aho 0.2.15

**Iteration:** 0.2.15 W0 | **Dispatcher:** direct Ollama HTTP, `/api/chat`, `num_ctx=32768`
**Stop tokens:** Qwen-native (`<|endoftext|>`, `<|im_end|>`) sent to all 4 models (W2 adds per-family tokens)
**Methodology:** Clean-slate, fixed-dispatcher evidence. Not recycled from 0.2.13 W2.5.

---

## Per-Model Status

| Model | Classification | Probe A (Identity) | Probe B (Structured) | Probe C (Language) | Extra |
|-------|---------------|-------------------|---------------------|-------------------|-------|
| Qwen 3.5:9B | `operational` | pass | pass | pass | Regression check — no change from W1.5 |
| Llama 3.2:3B | `operational` | pass | pass | pass | First integration — implicit via model-agnostic dispatcher |
| GLM-4.6V-Flash-9B | `partial` | partial | partial | pass | Template token leakage (`<\|begin_of_box\|>`) |
| Nemotron-mini:4b | `compromised` | **fail** | pass | pass | Classify probe D: pass (feature-bias resolved) |

---

## Qwen 3.5:9B — `operational`

Regression check only. No change from 0.2.14 W1.5 baseline.

- **Identity:** "Qwen3.5" — correct, clean (8.66s)
- **Structured:** exact JSON, schema match (27.31s)
- **Language:** English throughout, on-topic (56.85s)

No findings. Workhorse model confirmed stable.

---

## Llama 3.2:3B — `operational`

First real integration. Model was on disk since 0.2.14 W1.5, never dispatched.

- **Identity:** "LLaMA" — correct family name (1.83s)
- **Structured:** exact JSON, schema match (0.71s)
- **Language:** English throughout, on-topic (5.33s)

Integration status: **clean**. Dispatcher is model-agnostic at `/api/chat` level — Llama dispatches without code changes. Ollama applies Llama 3.x chat template server-side; no template leakage despite receiving Qwen stop tokens. W2 should add Llama-native stop tokens (`<|eot_id|>`, `<|end_of_text|>`) for correctness.

Speed note: 0.71s structured output vs Qwen's 27.31s — 3B model is substantially faster for triage-class tasks.

---

## GLM-4.6V-Flash-9B — `partial`

Re-test of 0.2.13 W2.5 compromised model. **Outcome: substrate artifact confirmed.**

- **Identity:** "GLM-4.5V" wrapped in `<|begin_of_box|>...<|end_of_box|>` — template token leakage (20.14s)
- **Structured:** correct JSON wrapped in template tokens — extraction needed, parseable (16.28s)
- **Language:** clean English, no template tokens (27.81s)

0.2.13 W2.5 finding was "80% timeout at 180s, wrong-schema JSON." On fixed dispatcher: zero timeouts, correct JSON schema, template token leakage only. The 0.2.13 findings were **substrate artifacts of the broken dispatcher** (`/api/generate`, 4K context default).

Retain decision: **RETAIN**. Template tokens are strippable; W2 dispatcher hardening addresses via GLM-specific stop tokens or post-processing. Candidate for Auditor role in W4 cross-model cascade.

**W1 correction (clean-state retest):** GLM requires `num_gpu=30` (partial CPU offload) on 8GB VRAM. Full GPU offload (41 layers) crashes with CUDA OOM — model buffer (5539 MiB) + CUDA runtime exceeds available VRAM. Inference is slower with partial offload (~36s vs ~2s for smaller models) but functional. Template leak confirmed stop-token fixable: use `<|end_of_box|>` as stop token + strip `<|begin_of_box|>` prefix. GLM's `thinking` field contains Chinese reasoning. See `ollama-probes/R02-clean.json`, `ollama-probes/R11-diagnostic.json`.

---

## Nemotron-mini:4b — `compromised`

Re-test of 0.2.13 W2.5 compromised model. **Outcome: feature-bias resolved, identity failure discovered.**

- **Identity:** returns `"You can use a model like this: 'BERT'"` — persona hallucination, does not know own name (1.76s)
- **Structured:** parseable JSON, schema match, minor case difference in items (3.36s)
- **Language:** English, on-topic, terse (0.3s)
- **Classify (D):** returns `"bug"` — correct. **0.2.13 W2.5 80% feature-bias was a substrate artifact.**

By strict criteria (`compromised` = any probe fail), Nemotron is `compromised` due to identity failure. However, the failure mode is identity confusion only — structural capabilities (JSON, classification, language) are intact. The model does not need to know its own name to classify text or produce structured output.

Retain decision: **RETAIN WITH CAVEAT**. Usable for classification/triage roles where identity is irrelevant. Not suitable for roles requiring model self-awareness. Very fast inference (0.09s classify).

---

## Methodological Lessons

1. **0.2.13 W2.5 findings for both GLM and Nemotron were substrate artifacts.** The broken dispatcher (`/api/generate`, 4K context, no chat template) contaminated all model-quality measurements. On fixed dispatcher, both models demonstrate functional capability.

2. **GLM's template token leakage is a dispatcher concern, not a model defect.** The `<|begin_of_box|>`/`<|end_of_box|>` tokens are GLM's structured-output markers; they need to be handled in W2 dispatcher hardening.

3. **Nemotron's identity confusion is a model-level issue, distinct from the substrate artifact.** The feature-bias was substrate; the identity failure is new and intrinsic. Both are less severe than the original findings.

---

## Pillar 7 Path Forward

With GLM `partial` and Nemotron `compromised` (but structurally functional):

- **W4 cross-model cascade has non-Qwen candidates.** GLM is the strongest Auditor candidate (9B parameters, template issue addressable in W2). Nemotron is viable for triage/classification roles.
- Roster: 2 operational (Qwen, Llama), 1 partial (GLM), 1 compromised-but-functional (Nemotron).
- Pillar 7 restoration attempt in W4 is meaningful — not Qwen-solo-with-extra-steps.

---

*Evidence from fixed dispatcher only. No 0.2.13 findings recycled. Raw response field inspected for each probe.*
