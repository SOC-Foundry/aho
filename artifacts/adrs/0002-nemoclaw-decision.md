# ADR 0002 — Nemoclaw Retain / Remove / Replace Decision

**Status:** Accepted
**Date:** 2026-04-21
**Iteration of record:** aho 0.2.15 W3
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal architecture (not universal methodology)

---

## Context

`src/aho/agents/nemoclaw.py` (0.1.7 W8 rebuild, 0.2.2 W2 daemonized) provides:

1. A **classification/routing layer** — `NemoClawOrchestrator.route()` calls `aho.artifacts.nemotron_client.classify()`, which posts to Ollama `/api/generate` with `nemotron-mini:4b` to pick one of a fixed set of roles (`assistant`, `code_runner`, `reviewer`).
2. A **dispatch/session layer** — three `OpenClawSession` instances (Qwen 3.5:9b chats) held warm behind a Unix socket daemon (`aho-nemoclaw.service`), dispatched by role.
3. **IPC plumbing** — `bin/aho-nemoclaw` fish wrapper speaks newline-delimited JSON over the Unix socket at `~/.local/share/aho/nemoclaw.sock`.

Nemoclaw was built before the pipeline dispatcher had any model-family awareness. At the time, `/api/generate` with raw prompts and a hand-rolled parser was the only available primitive. aho 0.2.15 W2 hardened `src/aho/pipeline/dispatcher.py` with:

- Per-model-family stop tokens (Qwen, Llama 3.x, GLM, Nemotron)
- Five typed error classes (`DispatchError`, `MalformedResponseError`, `TemplateLeakError`, `ModelUnavailableError`, `DispatchTimeoutError`) — G083 compliant
- Retry with exponential backoff on transient failures; no retry on systemic failures
- Template leak detection
- Model management helpers (`unload_model`, `list_loaded_models`, `ensure_model_ready`)
- `/api/chat` endpoint (chat template applied server-side)

W3 asks: does Nemoclaw still contribute value on the classification path given the W2 dispatcher, or is it redundant?

Evidence is in `artifacts/iterations/0.2.15/nemoclaw-comparison/nemoclaw-vs-dispatch.md` and `raw/probe-results.json`. Summary:

| Dimension | Nemoclaw path (`classify` via `/api/generate`) | Hardened dispatcher (`/api/chat`) |
|---|---|---|
| Wall clock per classify call | ~1.42 s (bug/feature, 5 samples) | ~1.79 s (same samples) |
| Bug/feature correctness (5 inputs) | 5/5 | 4/5 (one divergence from Path A) |
| Role classify correctness (5 inputs, 3 categories) | 1/5 (4 responses drifted into prose / stub output) | 4/5 |
| Chat template application | None (`/api/generate`) | Server-side per model family |
| Error typing | Two client-layer types + upstream `except Exception` wrapper that returns `"[error] ..."` string (G083 violation at `nemoclaw.py:62`) | Five typed exceptions, retry/backoff, no blanket catches |
| Socket IPC roundtrip overhead | Present; immeasurable against inference baseline | N/A (in-process) |
| Code weight for classify capability | ~400 LOC across `nemoclaw.py` + `nemotron_client.py` + fish wrapper + systemd unit | ~15 LOC wrapping a stateless function call |

The "~23 s Nemoclaw overhead" referenced in the W3 launch prompt is not substantiated by measurement. Socket IPC roundtrip was within measurement noise of direct dispatch. Wall clock on both paths is dominated by model inference, not plumbing.

A second observation worth lifting: the 0.2.13 W2.5 "Nemotron 80% feature-bias" finding was in significant part a substrate artifact of template-free dispatch via `/api/generate`. On `/api/chat` in W3 probes, Nemotron produces cleaner classifier output (4/5 clean matches on role classify vs 1/5 via the daemon's `/api/generate` path). This is consistent with 0.2.15 W0's re-vetting finding that Nemotron's feature-bias dissolved once the dispatcher was fixed.

---

## Decision

**Replace the classification layer of Nemoclaw. Retain the dispatch/session layer.**

Specifically:

1. Introduce `src/aho/pipeline/router.py` — a stateless classification function `classify_task(task, categories, *, model=None, bias=None)` that uses the W2 hardened dispatcher on `/api/chat`. This supersedes `aho.artifacts.nemotron_client.classify()` as the canonical classification primitive.

2. Migrate `NemoClawOrchestrator.route()` to call `aho.pipeline.router.classify_task()`. The daemon, the socket IPC, the three `OpenClawSession` instances, and the systemd unit **stay in place** — they provide session persistence and warm-process sharing, which the stateless dispatcher does not replicate.

3. Mark `aho.artifacts.nemotron_client.classify()` as deprecated in its docstring. Leave it callable during 0.2.15–0.2.16 so existing call sites have a migration window; removal is a future-iteration concern.

4. `bin/aho-nemoclaw` and `aho-nemoclaw.service` are unchanged. Users who use `aho-nemoclaw route` or `dispatch` via the socket continue to work.

5. Fix the G083 violation at `nemoclaw.py:62` (`except Exception` swallowing dispatch errors into `"[error] ..."` string) as part of this migration, since we are editing that code path. The other two `except Exception` sites (`nemoclaw.py:119, 126`) are inside the `NemoClawHandler` socket handler; narrowing those is deferred to W4 or later and documented as a carry-forward.

This is a **replace** decision, not retain or remove:
- Retain (no-op) is inconsistent with the measured evidence — the `/api/generate` path classifies worse than `/api/chat` on role classify (1/5 vs 4/5) and the typed-exception gap is non-trivial.
- Remove is too aggressive — the session layer (persistent OpenClaw roles, socket IPC, systemd integration) provides value orthogonal to the dispatcher. Removing it because the classifier layer is obsolete would be scope creep.

---

## Pillar 4 examination

Pillar 4 (wrappers are the tool surface): *"Agents never call raw tools. Every tool is invoked through a /bin wrapper. Wrappers are versioned with the harness, instrumented for the event log, and replayable from recorded inputs."*

Two readings of Pillar 4 relative to this decision:

1. **Strong reading — every Ollama call must go through a `/bin/aho-*` wrapper.** Under this reading, the hardened dispatcher (called in-process from Python) violates Pillar 4 because `dispatcher.dispatch()` is a library call, not a wrapper invocation. The Nemoclaw daemon's socket wrapper (`bin/aho-nemoclaw`) is more Pillar-4-conformant.
2. **Weak reading — the tool surface is wrapped when agents invoke it from outside the process; intra-process library calls are not "raw tool" calls.** Under this reading, the dispatcher IS the versioned tool surface and is invoked from wrappers (e.g., `bin/aho-conductor`, `bin/aho-nemoclaw`) that internally call it. Raw `curl http://127.0.0.1:11434/api/chat` from an agent's hand would violate Pillar 4; `from aho.pipeline import dispatcher; dispatcher.dispatch(...)` in a wrapper-invoked Python process does not.

The pipeline dispatcher as written is consistent with the weak reading: it is a versioned library (lives under `src/aho/pipeline/`, event-logged via OTel spans in callers, replayable from recorded prompts). W3 does not re-decide Pillar 4 semantics; it notes this as a tension that 0.2.16+ may want to address if the weak reading is insufficient for an external-observer audit.

The proposed replacement (`src/aho/pipeline/router.py`) does not worsen Pillar 4 conformance relative to the current `nemotron_client.classify()`, which is itself a library function. It improves typed-error compliance (Pillar 9 / G083) and reduces duplicated tool-surface code.

---

## Consequences

**Immediate (W3):**

- New file: `src/aho/pipeline/router.py` with `classify_task()` and one error type (`ClassificationError` subclass of `DispatchError`).
- New tests: `artifacts/tests/test_pipeline_router.py` — unit coverage for correct classification, parse failure, unknown-model error, empty-category-list guard.
- `src/aho/agents/nemoclaw.py`:
  - `route()` now calls `pipeline.router.classify_task()`; no longer imports `nemotron_client.classify`.
  - `except Exception` at line 62 replaced with typed handler raising/surfacing the specific error.
  - The two handler-scope `except Exception` blocks remain (carry-forward note below).
- `aho.artifacts.nemotron_client.classify()` docstring updated to note deprecation; function body unchanged for now (no downstream breakage).
- `components.yaml`: `nemoclaw` note updated; `nemotron-client` note updated to "deprecated, use pipeline.router"; new entry for `pipeline-router`.
- `aho doctor` behaviour unchanged (the daemon systemd unit still exists and is still checked).
- Baseline regression test run and compared against W2 (10 failed, 351 passed).

**Downstream (W4 or later — not this workstream):**

- Full removal of `nemotron_client.classify()` after callers migrate.
- Narrowing the two remaining `except Exception` blocks in `NemoClawHandler` to typed handlers. Tracked as a carry-forward, not gated by W3.
- `aho doctor` could be extended to surface which classification path is in use (library router vs legacy nemotron_client) — future hygiene, not W3 scope.

**Risk:**

- Nemoclaw's classification is used by `src/aho/agents/conductor.py` via `self.nemoclaw.route()`. Because the route method is being updated to call the new router internally, the conductor behaviour is unchanged — same input, same output categories, different underlying endpoint. Integration sanity probe is part of W3 acceptance.

- Not a risk on this iteration, but worth recording: the session layer (OpenClawSession) still uses the older qwen_client pre-W2-harden path. Migrating OpenClaw to the hardened dispatcher is a distinct decision (carry-forward candidate).

**Observed during migration (behaviour note):**

Nemotron-mini:4b on `/api/chat` reliably emits empty `message.content` when the system-role prompt contains a long multi-sentence bias instruction. The same bias flattened into `/api/generate` (prior Nemoclaw path) worked. The fix was to compress the Nemoclaw `route()` bias from three sentences to one. The full explanation and probe evidence are in `artifacts/iterations/0.2.15/nemoclaw-comparison/nemoclaw-vs-dispatch.md` under "Migration finding — long-bias-via-system quirk". This is a Nemotron quirk; future models may not require the compression. Worth re-checking if Nemotron is ever replaced or if a higher quantization is deployed.

---

## Alternatives considered

- **Retain Nemoclaw classifier unchanged.** Rejected: `/api/chat` produces cleaner role-classify output on the same model (4/5 vs 1/5 on role classify task); G083 violation in the current handler is structural.

- **Remove Nemoclaw daemon entirely.** Rejected: conflates two concerns. The classification layer is obsolete; the session layer is not. Removing the daemon would require reimplementing persistent OpenClaw sessions elsewhere, out of W3 scope.

- **Replace daemon with thin routing function and delete the daemon (combined remove + replace).** Rejected for the same reason as "remove entirely" — the session-persistence property is not addressed.

- **Defer to W4.** Rejected: W4 is integration + close, not architecture. W3 exists to land this decision so W4 can rely on the migrated router in its cross-model cascade.

---

## References

- `src/aho/pipeline/dispatcher.py` — W2 hardened dispatcher (0.2.15 W2)
- `artifacts/iterations/0.2.15/acceptance/W2.json` — W2 acceptance archive
- `artifacts/iterations/0.2.15/audit/W2.json` — W2 audit pass (Gemini)
- `artifacts/iterations/0.2.15/tier1-roster-validation-0.2.15.md` — Nemotron W0 re-vetting (classify probe passed)
- `artifacts/iterations/0.2.15/ollama-tier1-fitness-0.2.15.md` — Ollama control-plane fitness (R11: chat template application)
- `artifacts/iterations/0.2.15/nemoclaw-comparison/nemoclaw-vs-dispatch.md` — W3 empirical comparison
- `artifacts/iterations/0.2.15/nemoclaw-comparison/raw/probe-results.json` — raw probe output
- `artifacts/adrs/0001-phase-a-externalization.md` — prior aho-internal ADR (for series convention)
- `artifacts/harness/base.md` — Pillar 4 text, G083 text

---

*0002 is the second aho-internal project ADR (separate from the `ahomw-ADR-NNN` universal methodology series, whose highest published member is ADR-045). Number chosen by enumerating `artifacts/adrs/` and selecting the next available in the aho-internal series.*
