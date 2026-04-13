# Council Models — aho 0.2.14

**Purpose:** Model documentation review for W1 vetting. Per-model capabilities, constraints, and limitations.
**Sources:** Ollama model pages, project docs, vendor documentation.

---

## Summary Table

| Model | Context Window | Structured Output | Quantizations (Ollama) | Key Limitation |
|-------|---------------|-------------------|------------------------|----------------|
| Qwen 3.5:9B | 256K tokens | Tools tag; Ollama `format: "json"` available server-side. No native grammar-constrained JSON. | q4_K_M (default), q8_0, fp16 | Structured output relies on prompt engineering, not model-native enforcement. |
| Nemotron-mini:4b | 4,096 tokens | Function calling supported. No native JSON mode. | q2_K through fp16 (16 variants) | 4K context window. English-only. Distilled 4B model — limited analytical depth. |
| GLM-4.6V-Flash-9B | 128K tokens (modelfile defaults to 65K) | Tool use supported. No explicit JSON mode. | Q4_K_M only (community upload) | Community model (`haervwe/GLM-4.6V-Flash-9B`), single quant, no official support. |
| OpenClaw | Delegates to Qwen 3.5:9B | Delegates to underlying model | N/A (wrapper) | Session wrapper — capabilities are the underlying model's capabilities. |

---

## Qwen 3.5:9B

**Identity clarification:** The repo references `qwen3.5:9b` throughout. This is Qwen 3.5 — a distinct family from Qwen 3 (`qwen3`) and Qwen 2.5 (`qwen2.5`). Qwen 3.5 has 256K context; Qwen 3 8B has 40K. The distinction matters.

**Ollama page:** `ollama.com/library/qwen3.5`

**Capabilities:**
- Multimodal (vision + text), tools, thinking mode, 201 languages
- Parameter sizes: 0.8B–397B. Repo uses 9B.
- Chat template: Standard OpenAI-style messages array
- Thinking mode available (`"think": true`) but repo currently sets `think: False` in `OLLAMA_DEFAULTS`

**Structured output:**
- Ollama tags include "tools" — function calling supported
- Ollama `format: "json"` enforces JSON output at server level, but compliance depends on model following instructions
- No native grammar-constrained JSON generation documented
- For council grading, prompt engineering is the primary enforcement mechanism

**Known limitations:**
- At 9B parameters, complex multi-step analytical reasoning is limited
- Q4_K_M quantization reduces capability vs. fp16 — Q8_0 available as intermediate
- JSON parse failures remain a real risk for structured output tasks

---

## Nemotron-mini:4b

**Ollama page:** `ollama.com/library/nemotron-mini`

**Developer:** NVIDIA. Minitron architecture, distilled/pruned from larger model.

**Capabilities:**
- Optimized for: roleplay, RAG QA, function calling
- English-only
- Chat template: Standard messages format, NVIDIA ChatML internally
- Last updated: Sep 2024

**Structured output:**
- Has "tools" tag on Ollama (function calling)
- No native JSON mode documented
- At 4B parameters, structured output reliability is questionable

**Known limitations:**
- **4,096 token context window** — severely limited for multi-document or long-prompt tasks. Any shared prompt template must account for this ceiling or Nemotron must receive a shorter prompt.
- English-only
- 0.2.13 W2.5 finding: 8/10 classification inputs returned "feature" regardless of content. Model has severe feature-bias — effectively defaulting rather than classifying.

---

## GLM-4.6V-Flash-9B

**Identity clarification:** Two GLM-4 models exist on Ollama. The repo uses the community vision model (`haervwe/GLM-4.6V-Flash-9B`), not the official text-only `glm4:9b`.

**Ollama page:** `ollama.com/haervwe/GLM-4.6V-Flash-9B`

**Capabilities:**
- Vision/multimodal, tool use, hybrid thinking
- Image understanding, document analysis, UI screenshot replication
- Context: 128K tokens (modelfile defaults to 65K for VRAM management)

**Structured output:**
- Tool use supported
- No explicit JSON mode documented
- 0.2.13 W2.5 finding: 4/5 evaluation inputs timed out at 180s; 1/5 returned wrong JSON schema. Model has evaluation capability in text output but cannot deliver structured JSON within reasonable timeout at Q4_K_M.

**Known limitations:**
- **Community upload, not official library.** Single quantization (Q4_K_M only). No fallback if `haervwe` stops maintaining.
- VRAM-intensive: requires 16GB+ for default context
- Official `glm4:9b` is text-only with full quant range — possible fallback for non-vision tasks
- Newer GLM-4.6/4.7 official entries exist but are text-only cloud variants

---

## OpenClaw

**Type:** Internal aho component, not an external LLM.

**Location:** `src/aho/agents/openclaw.py`

**Function:** Session wrapper around QwenClient. Provides `OpenClawSession` with role-based dispatch (assistant, evaluator, workstream). Runs as Unix socket daemon (`aho-openclaw.service`).

**Underlying model:** Delegates to `qwen3.5:9b` by default (configurable via `orchestrator.json`). Structured output capabilities, context window, and limitations are those of the underlying Ollama model.

**W1 action:** Resolve exact model binding, verify socket reachability, test dispatch path.

---

## Cross-cutting Observations

1. **Structured output is the weak link across all models.** None have documented native grammar-constrained JSON generation. Ollama's server-side `format: "json"` helps but is not a guarantee. JSON parse failures are a model-layer risk for council grading.

2. **Context window variance: 4K (Nemotron) vs. 128K (GLM) vs. 256K (Qwen 3.5).** Shared prompt templates must account for Nemotron's 4K ceiling.

3. **GLM vision usage relies on a community model** with a single quantization and no official support path. Risk: dependency on community maintainer.

4. **0.2.13 substrate findings remain the dominant constraint.** Parser fixes (W1, W2) are durable, but the models behind them (GLM, Nemotron) cannot produce usable structured output at current quantization. Q8_0 or alternative model selection are 0.2.15+ decisions pending 0.2.14 wiring verification.
