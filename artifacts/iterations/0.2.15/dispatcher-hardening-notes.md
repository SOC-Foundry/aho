# Dispatcher Hardening Design Notes — aho 0.2.15 W2

**Iteration:** 0.2.15 W2 | **Date:** 2026-04-19

---

## Summary

Hardened `src/aho/pipeline/dispatcher.py` from single-model Qwen-only dispatch (0.2.14 W1.5) to multi-model Tier 1 dispatch supporting all 4 roster models. Changes driven by W0 vetting findings and W1 Ollama fitness report.

---

## Design Decisions

### D1 — Per-model-family config registry

**Decision:** Static `MODEL_FAMILY_CONFIG` dict keyed by family name, with model-ID-to-family resolution via longest-prefix match.

**Why not per-model-id config?** Model IDs include version tags (`:9b`, `:latest`, `:3b`) that change. Family grouping is stable — all Llama 3.x variants share the same stop tokens and template behavior. The prefix-match approach handles both short names (`qwen3.5:9b`) and qualified names (`haervwe/GLM-4.6V-Flash-9B:latest`).

**Fallback:** Unknown models fall back to Qwen config (ChatML). This is a safe default because ChatML stop tokens are widely compatible. If a future model has incompatible stop tokens, it must be added to the registry — the fallback will produce harmless but possibly verbose output, not data corruption.

### D2 — GLM template leak fix

**Decision:** Add `<|end_of_box|>` as GLM stop token + strip `<|begin_of_box|>` prefix from response content.

**Evidence:** W1 R11-diagnostic.json probe 4 confirmed this approach:
- Without stops: output wrapped in `<|begin_of_box|>...<|end_of_box|>`
- With `<|end_of_box|>` as stop: output is `<|begin_of_box|>content` — strippable prefix
- With both as stops: empty output (begin fires before content)

**Why not both as stops?** `<|begin_of_box|>` fires before any content, producing empty output. Only `<|end_of_box|>` as stop, plus prefix strip, yields the content.

### D3 — Qwen num_predict=2000

**Decision:** Set `num_predict=2000` for Qwen family in options.

**Evidence:** W1 F001 — Qwen 3.5:9B uses ~150-200 internal thinking tokens per response. With default num_predict (typically 128-512), visible output can be empty. 2000 provides adequate budget for thinking + visible output.

**Why not disable thinking mode?** `/no_think` prefix or `think: false` option may suppress analytical quality. The token budget approach preserves thinking capability while ensuring visible output.

### D4 — GLM num_gpu=30

**Decision:** Set `num_gpu=30` (of 41 layers) for GLM family.

**Evidence:** W1 R2 — GLM full-GPU (41 layers) requires model buffer 5539 MiB + CUDA runtime ~1.2 GiB, exceeding available VRAM on 8GB hardware. `num_gpu=30` loads at 7239 MiB with partial CPU offload. Inference is ~36s vs ~2s for smaller models, but functional.

**Tradeoff:** 18x slower inference for GLM. Acceptable for Auditor role (W4) where quality matters more than speed. Not suitable for triage/latency-sensitive roles.

### D5 — Error types over error strings

**Decision:** Five specific exception types (`DispatchError`, `MalformedResponseError`, `TemplateLeakError`, `ModelUnavailableError`, `DispatchTimeoutError`) with inheritance from `DispatchError`.

**G083 compliance:** No `except Exception` blocks. Each failure mode has its own type. Callers can catch `DispatchError` for broad handling or specific types for targeted recovery.

**Dual mode:** `raise_on_error=False` (default) returns error dicts for backward compatibility with existing cascade code. `raise_on_error=True` raises typed exceptions for callers that want exception-based flow control.

### D6 — Retry policy: transient only

**Decision:** Retry on connection errors, timeouts, and non-404 HTTP errors. Do NOT retry on:
- Template leak (systemic — model will leak again)
- 404 (model not found — permanent)
- Malformed response (data issue — same response on retry)

**Backoff:** Exponential with configurable base (default 1s). Delays: 1s, 2s for default 2 retries.

### D7 — Model management helpers

**Decision:** Added `unload_model()`, `list_loaded_models()`, `ensure_model_ready()` as public functions.

**Evidence:**
- W1 F004: Nemotron auto-loads on Ollama restart and after evictions. Explicit unload needed before loading large models.
- W1 F006/F007: GLM CUDA OOM crash kills ALL loaded models. Cascade code should verify model presence and pre-evict when needed.
- W1 R3: `keep_alive:0` unloads within 5s grace period.

These helpers are tools for the cascade orchestrator (W4), not called by `dispatch()` itself. The dispatcher is stateless per-call; model lifecycle management belongs to the caller.

### D8 — Parameter validation

**Decision:** Validate `num_ctx` before sending to Ollama. Clamp to `[256, 262144]` range.

**Evidence:** W1 R7 — Ollama silently accepts invalid `num_ctx` (e.g., 999999999) with HTTP 200. Client-side validation prevents accidental OOM or nonsensical context windows.

---

## What was NOT changed

- **Dispatch is still stateless per-call.** No connection pooling, no session management. urllib.request is adequate for cascade stage dispatch where each call is minutes apart.
- **No Nemoclaw integration.** W3 tests Nemoclaw and publishes ADR. This dispatcher is the direct-Ollama path.
- **No parallel dispatch.** Cascade stages are serialized (W1 F003: only Llama + Nemotron can coexist in VRAM). No threading needed.
- **No keep_alive tuning in dispatch options.** Default Ollama keep_alive is adequate. Model lifecycle managed externally via `unload_model()` / `ensure_model_ready()`.

---

## Test Coverage

| Test class | Count | Covers |
|---|---|---|
| TestModelFamilyResolution | 8 | prefix match, case insensitivity, unknown fallback |
| TestFamilyStopTokens | 4 | per-family stop tokens in payload |
| TestGLMConfig | 3 | num_gpu=30, prefix strip, clean passthrough |
| TestQwenConfig | 2 | num_predict=2000, Llama has no num_predict |
| TestTemplateLeak | 5 | detection, no-retry on leak, raise mode |
| TestErrorTypes | 5 | hierarchy, malformed JSON, missing content, 404, timeout |
| TestRetryBackoff | 3 | connection retry, no-retry on 404, exhaustion |
| TestParameterValidation | 6 | valid, clamp low/high, invalid type, negative, sent to Ollama |
| TestResponseMetadata | 2 | family and retries_used in result |
| TestModelManagement | 3 | unload keep_alive=0, list models, error returns empty |
| TestBackwardCompatibility | 2 | STOP_TOKENS and DEFAULT_NUM_CTX constants |
| TestPostprocessing | 3 | strip prefix, no prefix, prefix absent |
| **Total** | **46** | |

Plus 6 existing tests in `test_dispatcher_chat_api.py` — all pass (backward compat verified).

---

*No git operations performed. `__pycache__` cleared after src/aho/ touch (G070).*
