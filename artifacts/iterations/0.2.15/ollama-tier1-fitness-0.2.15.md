# Ollama Tier 1 Fitness Report — aho 0.2.15 W1

**Iteration:** 0.2.15 W1 | **Probe date:** 2026-04-13
**Hardware:** NVIDIA GeForce RTX 2080 SUPER, 8192 MiB VRAM
**Ollama version:** 0.20.2
**Desktop VRAM baseline:** ~704 MiB (KDE Plasma, Chrome, Signal, etc.)
**Models tested:** 4 Tier 1 roster members

**Revision note:** Initial W1 probes ran against contaminated Ollama state (resident Qwen + orphan runner from crashed probe). Post-W1 diagnostic by Kyle identified the contamination. Clean-state retests performed for R2 and R11. Corrected findings below. Original probe artifacts preserved in R02-lru-eviction.json; corrected artifacts in R02-clean.json and R11-diagnostic.json.

---

## Executive Summary

**8 met / 3 partial / 0 failed**

Ollama is viable as Tier 1 control plane for all 4 Tier 1 roster members (Qwen 3.5:9B, Llama 3.2:3B, GLM-4.6V-Flash-9B, Nemotron-mini:4B) on 8GB VRAM hardware, with a constraint: **GLM requires partial GPU offloading** (`num_gpu=30` of 41 layers) due to CUDA memory pressure. Full GPU offload for GLM exceeds available VRAM.

**Critical correction from initial W1 findings:** Initial W1 probes reported "3362 MiB base overhead" — this was not base overhead but resident Nemotron model weights + Ollama runtime. Post-W1 diagnostic confirmed Ollama baseline is ~704 MiB (including desktop processes). However, GLM's full-GPU requirement (5539 MiB model buffer + ~1.2 GiB CUDA runtime + KV/compute) still exceeds available VRAM even on clean state. The correction is that GLM IS loadable via partial offload, not that the hardware constraint was imaginary.

Three requirements remain `partial`:
- **R2 LRU eviction** — predictable for 3 models; GLM full-GPU crashes (CUDA OOM), loadable with num_gpu=30
- **R7 Error reporting** — invalid num_ctx silently accepted (200). Client-side validation needed in dispatcher.
- **R11 Chat template** — GLM template leak is stop-token fixable (use `<|end_of_box|>` + strip `<|begin_of_box|>` prefix). W2 dispatcher scope.

R5 (multi-model routing) promotes to `meets` — GLM routes correctly with partial offload. R6 (context preservation) confirmed `meets`.

**Recommended Tier 1 roster:** Qwen 3.5:9B, Llama 3.2:3B, GLM-4.6V-Flash-9B (num_gpu=30), Nemotron-mini:4B — 4 chat LLMs. All operational on 8GB VRAM with proper configuration.

---

## Per-Requirement Table

| Req | Requirement | Critical | Classification | Evidence | Workaround |
|-----|-------------|----------|---------------|----------|------------|
| R1 | Concurrent model awareness | no | **meets** | /api/ps reports name, size_vram, context_length, expires_at. Accurate for all loaded models. | — |
| R2 | LRU eviction predictability | **yes** | **partial** | LRU-consistent for 3 fully-loadable models. GLM full-GPU (41 layers) crashes with CUDA OOM even on clean VRAM. GLM loadable with num_gpu=30 (partial offload, 7239 MiB). | GLM uses num_gpu=30. Dispatcher manages offload config per model. |
| R3 | Explicit unload API | no | **meets** | keep_alive:0 unloads all 3 models within 5s. Grace period (not immediate). | — |
| R4 | Request queuing | no | **meets** | Concurrent requests succeed. Partial parallelism (ratio 0.65). No 503 or rejection. | — |
| R5 | Multi-model routing by name | **yes** | **meets** | All 4 models route by exact name with correct model_returned. GLM routes correctly with num_gpu=30. | — |
| R6 | Context preservation / leak | **yes** | **meets** | No cross-request context leak. Secret-word test passed for Qwen and Llama. Stateless per-request confirmed. | — |
| R7 | Error reporting fidelity | no | **partial** | 404 for unknown model, 400 for malformed JSON. Invalid num_ctx (999999999) silently accepted (200). | Client-side parameter validation in dispatcher. |
| R8 | Timeout / hang detection | no | **meets** | 3s client timeout triggers cleanly. Server aborts inference, unloads model. No zombie. | — |
| R9 | Model-swap latency | no | **meets** | Avg 2.97s. Qwen: 4-6s, Llama: 1-2s, Nemotron: 1-2s. All <10s. | — |
| R10 | Stop token handling | no | **meets** | Native stop tokens work for all models. Not visible in output. Custom stops pass through. | Qwen: custom stops match thinking-mode content — use native stops only. |
| R11 | Chat template application | **yes** | **partial** | Qwen, Llama, Nemotron: clean. GLM: template leak (`<\|begin_of_box\|>...<\|end_of_box\|>`). Diagnostic confirms stop-token fixable. | W2 dispatcher: add `<\|end_of_box\|>` to GLM stops, strip `<\|begin_of_box\|>` prefix. |
| R12 | Embedding endpoint coexistence | no | **meets** | /api/embed with nomic-embed-text returns 768-dim vectors. Chat unaffected. | — |

---

## Critical Requirement Analysis

### R2 — LRU Eviction: `partial`

LRU eviction is predictable for the 3 fully-loadable models on 8GB VRAM (704 MiB desktop baseline):
- Qwen (6.43GB): loads alone, evicts everything else. Cannot coexist with other models.
- Llama (2.75GB) + Nemotron (3.05GB) = 5.8GB: can coexist.
- GLM full-GPU (41 layers, 5539 MiB buffer): crashes with CUDA OOM. Root cause: `cudaMalloc failed: out of memory` allocating 1704 MiB. Ollama scheduler reports 6.5 GiB available but CUDA runtime context (~1.2 GiB) is not accounted for.
- GLM partial-GPU (30/41 layers): loads at 7239 MiB VRAM. Inference ~36s (vs 2s for smaller models). Functional.

Clean-state retest confirmed: GLM crashes on empty VRAM (705 MiB, 0 GPU processes). Not a contaminated-baseline artifact.

**Shippability impact:** 4-model cascade requires GLM with num_gpu=30. W2 dispatcher must include per-model GPU layer configuration.

### R5 — Multi-model Routing: `meets` (revised from partial)

All 4 models route correctly by exact name with num_gpu=30 for GLM. model_returned matches model_requested. R5 promoted from `partial` to `meets` after GLM loads via partial offload.

### R6 — Context Preservation: `meets`

Clean pass. No cross-request contamination. Ollama's /api/chat is correctly stateless per-request.

### R11 — Chat Template: `partial`

Qwen, Llama, Nemotron: clean, no template leakage. GLM template leak confirmed and diagnosed:

- Without stop tokens: output wrapped in `<|begin_of_box|>...<|end_of_box|>` (e.g., `<|begin_of_box|>bug<|end_of_box|>`)
- With `<|begin_of_box|>` + `<|end_of_box|>` as stops: empty output (begin fires before content)
- With only `<|end_of_box|>` as stop: output is `<|begin_of_box|>feature` — content present, strippable prefix

**Verdict: stop-token fixable.** W2 dispatcher adds `<|end_of_box|>` to GLM stop tokens and strips `<|begin_of_box|>` from response content.

---

## Kyle Escalations

### E1 — Ollama State Hygiene (was: GLM Non-Functional)

Initial W1 finding "GLM non-functional on 8GB VRAM" was partially incorrect. The "3362 MiB base overhead" figure was resident Nemotron + Ollama runtime, not base. Clean-state measurement: ~704 MiB desktop + ~449 MiB Ollama base = ~1153 MiB overhead.

However, GLM full-GPU (41 layers) STILL cannot load on clean state — CUDA runtime context + model buffer exceeds available VRAM. GLM IS loadable with partial offload (num_gpu=30).

**Real finding:** Ollama orphan runner processes can accumulate from crashed probes without /api/ps tracking them, contending for VRAM. Additionally, Nemotron auto-loads on Ollama restart and after model evictions — cannot be permanently suppressed via keep_alive:0 alone. W2 dispatcher hardening scope includes state management (pre-operation eviction, orphan detection, keep_alive control).

**Decision needed:** Accept GLM with num_gpu=30 in Tier 1 roster (slower inference, ~36s vs ~2s). No GLM removal needed — model is functional with partial offload.

### E2 — Ollama Service Layer

Ollama runs as system-level systemd service (`/etc/systemd/system/ollama.service`), not user-level. Restart requires `sudo systemctl restart ollama`. install.fish and harness docs should reflect this.

**Decision needed:** install.fish and harness docs updated to use system-level Ollama commands. W2 or documentation scope.

### E3 — Qwen Thinking-Mode Token Budget

Qwen 3.5:9B uses ~150-200 internal thinking tokens per response, consuming num_predict budget. With num_predict=500, visible output can be empty. W2 dispatcher must account for this — recommended minimum num_predict=2000 for Qwen, or investigate disabling thinking mode via /no_think prefix.

---

## Tier 1 Shippability Assessment

**Ollama is viable as Tier 1 control plane for all 4 Tier 1 roster models on 8GB VRAM.**

The control plane works correctly: model loading, routing, unloading, queuing, timeout handling, embedding coexistence, and context isolation all function as specified. GLM requires partial GPU offloading (num_gpu=30) to fit — inference is slower (~36s) but functional. Template handling is correct for 3 models; GLM template leak is stop-token fixable in W2.

The initial W1 finding of "hardware-limited, 3-model cascade only" was partially incorrect — it measured contaminated baseline state AND misattributed the VRAM constraint. Post-correction: GLM is loadable with partial offload. 4-model roster is feasible with appropriate dispatcher configuration.

**Recommended Tier 1 roster:** Qwen 3.5:9B, Llama 3.2:3B, GLM-4.6V-Flash-9B (num_gpu=30), Nemotron-mini:4B.
**Deferred to Tier 2+ (16GB+ VRAM):** Gemma 2 9B, DeepSeek-Coder-V2 16B, Mistral-Nemo 12B (not tested, out of 0.2.15 scope).

---

## Ancillary Findings

### F001 — Qwen Thinking-Mode Behavior

Qwen 3.5:9B generates ~150-200 internal thinking tokens before visible output. These consume num_predict budget and are stripped from the response. W2 dispatcher should set num_predict >= 2000 for Qwen to ensure adequate visible output.

### F002 — Ollama VRAM Overhead (revised)

Initial W1 reported "3362 MiB base overhead" — this was resident Nemotron (2913 MiB) + Ollama runtime (~449 MiB), not base. Post-correction measurement: Ollama clean-state baseline VRAM is ~704 MiB (including desktop GPU processes). Ollama process itself adds ~449 MiB when a runner starts.

Nemotron auto-loads on Ollama restart and reappears when VRAM becomes available after model eviction. This keep_alive/auto-load behavior is not configurable via the service file (no OLLAMA_KEEP_ALIVE env set). Worth W2 investigation.

### F003 — Model Coexistence Constraints

On 8GB VRAM (~7488 MiB available after desktop): only Llama + Nemotron can coexist (5.8GB combined). Qwen (6.43GB) and GLM (7.2GB with num_gpu=30) run solo. Cascade stages must be serialized — no parallel multi-model inference.

### F004 — Nemotron Auto-Load Behavior

Nemotron persistently auto-loads on Ollama restart and when VRAM becomes available. Multiple /api/generate POST calls appear in journalctl immediately after restart. Cannot be permanently suppressed via keep_alive:0 alone. W2 dispatcher should account for this — explicit unload before loading large models.

### F005 — GLM Internal Reasoning Language

GLM-4.6V-Flash-9B's `thinking` field in /api/chat responses contains Chinese reasoning even when prompt and response are in English. The thinking field is present in Ollama 0.20.2 /api/chat responses. For classification tasks, thinking may be in English; for identity/general tasks, thinking is in Chinese. This consumes context budget proportionally. If GLM serves as Auditor in W4 cascade, analytical reasoning is emitted in Chinese within `thinking`, not visible in cascade artifacts unless explicitly captured.

### F006 — GLM CUDA OOM Crash Behavior

When GLM full-GPU load fails (CUDA OOM), the crash kills ALL loaded models — VRAM drops to baseline. This is destructive to concurrent model state. W2 dispatcher should verify model presence via /api/ps after any GLM operation and reload if needed.

---

*Probe evidence in `artifacts/iterations/0.2.15/ollama-probes/R01-R12`, `R02-clean.json`, `R11-diagnostic.json`. Raw HTTP responses and journalctl crash logs inspected for all ambiguous results. No git operations performed.*
