# Nemoclaw vs Direct Dispatch — Empirical Comparison (0.2.15 W3)

**Probe date:** 2026-04-21
**Model:** nemotron-mini:4b (both paths)
**Ollama endpoint:** 127.0.0.1:11434
**Paths measured:**
- **A**: `nemotron_client.classify()` via `/api/generate` (what `NemoClawOrchestrator.route()` calls in-process)
- **B**: `dispatcher.dispatch("nemotron-mini:4b", ...)` via `/api/chat` (W2 hardened dispatcher)
- **C**: Nemoclaw daemon socket (`aho-nemoclaw`, Unix socket IPC) — only usable with the daemon's hardwired `[assistant, code_runner, reviewer]` categories

Raw payloads archived at `artifacts/iterations/0.2.15/nemoclaw-comparison/raw/probe-results.json`.

---

## Metric Table

| Metric | Path A: Nemoclaw (in-process classify) | Path B: Direct dispatch (W2 /api/chat) |
|---|---|---|
| Wall clock per call (mean) | **~1.42 s** (0.14 / 1.78 / 1.64 / 1.67 / 1.87) | **~1.79 s** (1.84 / 1.66 / 1.70 / 1.84 / 1.89) |
| Correctness on bug/feature | **5 / 5** | **4 / 5** (missed "Add dark mode" → "bug") |
| Correctness on role classify (A is not usable here; using C socket) | **C: 1 / 5** (4 returned unmatched prose: `'(The Eleven Pillars Of Agile)'`, `'AI'`, `'AI'`, `''`) | **4 / 5** (only `"discovery"` didn't match) |
| Token overhead | Same underlying prompt; `/api/generate` has no chat-template overhead | Same prompt; `/api/chat` adds server-side template wrapping |
| Error handling fidelity | `NemotronParseError`, `NemotronConnectionError` at client layer; **but `NemoClawOrchestrator.dispatch` wraps in `except Exception` (G083 violation, 3 sites in `nemoclaw.py`)** | 5 specific types (`DispatchError`, `MalformedResponseError`, `TemplateLeakError`, `ModelUnavailableError`, `DispatchTimeoutError`); retry with exponential backoff; 404 surfaced cleanly |
| Code complexity (LOC) | `nemoclaw.py` 167 + `nemotron_client.py` 175 + `bin/aho-nemoclaw` (fish) 42 + systemd unit = **~400 LOC + running daemon + Unix socket + systemd user service** | Single function call through `dispatcher.dispatch()` (W2, already shipped) + ~25 LOC classify wrapper |
| Dependencies | `opentelemetry`, `requests`, `socketserver`, `openclaw`, `nemotron_client` | `urllib.request` (stdlib), `json` (stdlib), `time` (stdlib) |

---

## The 23-second-overhead claim

The W3 launch prompt references "~23s overhead Nemoclaw adds." **This is not supported by measurement.** In the probe:

- Socket IPC roundtrip (Path C) — `aho-nemoclaw route "..."`: wall clock 1.68–1.87 s per call
- Direct dispatcher (Path B) for equivalent work: 1.66–1.89 s per call

The two paths are within measurement noise. The IPC + daemon dispatch overhead is effectively zero; wall clock is dominated by model inference on Nemotron-mini:4b (3 GB resident, 1.6–1.9 s per short classify at Q4_K_M on the 2080 SUPER).

The 23 s figure does not appear in any 0.2.15 artifact. It may have originated from a conflation with `OpenClawSession` initialization cost (Qwen 3.5:9b first load), not the classifier path. Recording it here so future W3-rereads do not propagate the claim without measurement.

---

## Correctness finding: `/api/chat` is better for role classify, `/api/generate` slightly better for this bug/feature sample

Role classify (3 categories, daemon-compatible):
- **Daemon (nemotron_client via /api/generate):** 1/5 matched — 4 responses were prose or `AI` stub output that do not contain any of the category names. The `classify()` parser then raises `NemotronParseError`, which the daemon surfaces as `"ok": false`.
- **Direct dispatch via /api/chat:** 4/5 matched. The one non-match (`"discovery"` for the remediation/discovery question) is the model attempting to answer rather than classify — arguably a prompt-engineering issue, not an endpoint issue.

Bug/feature (2 categories):
- Path A: 5/5.
- Path B: 4/5 (missed task 2: "Add dark mode support" → `" bug"`).

Both paths used identical prompts. The endpoint differs: `/api/generate` does not apply Nemotron's chat template; `/api/chat` does. With 2 categories and short inputs, Path A happens to track better on this 5-sample set; with 3 categories and heterogeneous inputs, Path B tracks better.

### Migration finding — long-bias-via-system quirk on Nemotron + `/api/chat`

Discovered during W3 implementation, not in the initial probe: the original Nemoclaw `route()` bias text ("Prefer 'assistant' for general tasks. Use 'code_runner' only if the task requires executing code. Use 'reviewer' only if the task is about evaluating an artifact.") when placed into the `/api/chat` system role on Nemotron-mini:4b reliably produces empty `message.content` with `done_reason=stop`. No template leak, no HTTP error — just zero output tokens. The same bias concatenated into a flat `/api/generate` prompt (the prior Nemoclaw path) worked. A compact one-sentence bias ("Use code_runner for coding/execution tasks, reviewer for evaluating artifacts, assistant otherwise.") is tolerated on `/api/chat`.

This is a Nemotron + chat-template behaviour: the model emits its turn-end token before producing any visible content when the system prompt is above some length/structure threshold. It is not a dispatcher bug — the hardened dispatcher correctly relays whatever the server produces. `classify_task` surfaces this as a `ClassificationError` (empty response does not match any category), which is the intended failure mode.

The migration ships with the short bias in `NemoClawOrchestrator.route()`. The quirk is documented so future callers understand why the bias was compressed. Future models (non-Nemotron) may not need this compression.

Neither sample size is large enough for a correctness verdict. **The substantive difference is in capability shape, not per-call accuracy on this sample:**

1. `/api/chat` (Path B) applies chat template server-side, producing outputs that more reliably contain only category names. On the role task, 4/5 Path B responses were directly parseable vs 1/5 for the daemon path.
2. `/api/generate` (Path A) is more susceptible to template-free prose drift — this is a material finding re: the 0.2.13 "Nemotron 80% feature-bias" history, which was partially a substrate artifact of template-free dispatch (see `tier1-roster-validation-0.2.15.md`).

---

## What Nemoclaw uniquely provides beyond the dispatcher

Reviewing `src/aho/agents/nemoclaw.py` line by line, the daemon contributes:

1. **Classification routing** (`route()` method) — thin wrapper around `nemotron_client.classify()`. The dispatcher can replicate this in ~15 lines with better template handling.

2. **Persistent per-role OpenClaw sessions** (`dispatch()` method) — `NemoClawOrchestrator` holds three `OpenClawSession` objects (one per role). Each session is a Qwen 3.5:9b chat with role-specific system prompt and persistent history. **This is real value** — avoids re-initializing QwenClient per dispatch, maintains multi-turn context per role.

3. **Unix socket IPC** — allows multiple clients to share the same warm sessions.

**Items 2 and 3 are orthogonal to the W2 dispatcher hardening.** The dispatcher is stateless per call; it does not replace session management. However, items 2 and 3 are a property of the OpenClaw session layer, not of the Nemoclaw classifier layer. The daemon bundles both concerns into one systemd unit.

---

## Error handling: Nemoclaw has pre-existing G083 violations

`src/aho/agents/nemoclaw.py` has three `except Exception` blocks (lines 62, 119, 126). On `dispatch()` line 62, a caught exception is returned as the string `f"[error] {e}"` — callers receive a success-shaped string that is actually an error. G083 applies: exception handlers must raise or return a failure sentinel that callers recognize as such.

The hardened dispatcher (W2) has no `except Exception` blocks. Five typed exceptions with defined semantics; retry only on transient classes.

---

## Decision implication

The classification layer of Nemoclaw (the `route()` path and its `nemotron_client.classify()` dependency) is **architecturally obsolete** given W2 dispatcher hardening. The session layer (`OpenClawSession` × 3, socket IPC) is **orthogonal** — it provides value that the dispatcher does not replicate.

**Recommendation: REPLACE classification layer, preserve session layer.**

- Introduce `src/aho/pipeline/router.py` — a thin routing function that uses the hardened dispatcher on `/api/chat` with category-name enforcement. ~25 LOC.
- Update `src/aho/agents/nemoclaw.py` `route()` to call the new router. Keep the daemon, keep the OpenClaw sessions, keep the socket — those are not obsolete.
- Deprecate `nemotron_client.classify()` entrypoint (kept for back-compat during 0.2.15 → 0.2.16 transition; callers migrate).
- The `NemoClawHandler.dispatch` `except Exception` at line 119 is a G083 violation and should be narrowed, but that is a separate hygiene fix — scoping to W3 if budget permits.

Full daemon removal is not justified by the evidence. The socket + role-session architecture has its own value proposition (session persistence, shared warm sessions) that 0.2.15 W3 does not evaluate.

---

*Probe script: `artifacts/iterations/0.2.15/nemoclaw-comparison/probe.py`. Raw JSON: `raw/probe-results.json`. No git operations performed during this workstream.*
