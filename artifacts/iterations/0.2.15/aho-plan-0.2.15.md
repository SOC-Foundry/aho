# aho-plan-0.2.15

**Iteration:** 0.2.15
**Theme:** Tier 1 Partial Install Validation & Ship
**Phase:** 0 (Clone-to-Deploy)

Execution plan for workstreams defined in `aho-design-0.2.15.md`. Pillars and trident defined in design doc; not repeated here per convention.

---

## Workstream summary

| N | Theme | Gate |
|---|---|---|
| W0 | Setup + Tier 1 roster re-vetting on fixed dispatcher | 4 LLMs have explicit status with evidence; no `unknown` |
| W1 | Ollama Tier 1 capability audit | Every requirement has pass/partial/fail with evidence |
| W2 | Dispatcher protocol hardening | Dispatcher handles all 4 LLMs with family-appropriate config, graceful failure |
| W3 | Nemoclaw re-vetting + ADR dispatcher choice | ADR published with measured rationale |
| W4 | Integration + close | Tier 1 install.fish shippable; all 4 LLMs wired; cross-model cascade validated |

---

## W0 — Setup + Tier 1 roster re-vetting

**Scope:**
1. Version bump to 0.2.15, iteration scaffolding (directory structure, checkpoint init, event log continuity)
2. Integrate Llama 3.2 3B into pipeline dispatcher (currently on disk at NZXTcos, not wired)
3. Re-vet all 4 chat LLMs on fixed dispatcher with clean-slate methodology

**Per-model vetting criteria (each LLM must pass all):**
- **Identity probe** — model returns correct model_name when asked; no persona drift
- **Chat template honoring** — no template tokens (`<|endoftext|>`, `<|im_start|>`, `<|eot_id|>`, family-specific markers) as visible output text
- **Structured output** — produces parseable JSON on structured-output task without wrapping, prose prefix, or template leakage
- **Stop token respect** — output terminates at model-family stop tokens; no multi-turn simulation
- **Language stability** — output remains in requested language (no Chinese drift, no language-switch mid-output)

**Per-model test artifact:** `artifacts/iterations/0.2.15/vetting/{model}-probe.json` — identity response, structured output response, raw response field, classification

**Models:**
- **Qwen 3.5:9B** — regression check only (proven in 0.2.14 W1.5); verify still clean on current dispatcher
- **Llama 3.2:3B** — full vetting. Llama 3.x stop tokens are `<|eot_id|>`, `<|end_of_text|>`. Template is different from Qwen — dispatcher may need model-family-aware stop token selection (carry to W2 if needed).
- **GLM-4.6V-Flash-9B** — full re-vet. 0.2.13 W2.5 finding was 80% timeout, wrong-schema JSON — measured on broken dispatcher. Re-test produces evidence for retain/remove decision. Halt condition: if fails on fixed dispatcher with same symptoms, removal decision stands.
- **Nemotron-mini:4b** — full re-vet. 0.2.13 W2.5 finding was 80% feature-bias on classify task — measured on broken dispatcher. Re-test classify task specifically. Halt condition: if feature-bias persists on fixed dispatcher, removal decision stands.

**Classification per model:**
- `operational` — passes all 5 criteria
- `partial` — passes identity + structured output + template; fails one of language or stop token
- `compromised` — fails structured output or template; not usable in cascade

**Deliverables:**
- `tier1-roster-validation-0.2.15.md` — human-readable per-model status with evidence quotes
- `tier1-roster-validation-0.2.15.json` — machine-readable, strict schema
- `src/aho/pipeline/dispatcher.py` — Llama 3.2 integration (model-family stop token dispatch if needed)
- `artifacts/iterations/0.2.15/vetting/` — 4 per-model probe artifacts

**Acceptance:**
- All 4 LLMs have `operational` / `partial` / `compromised` status with evidence
- No `unknown` status remaining
- Llama 3.2 3B integrated and vetted (first real integration)
- GLM and Nemotron re-test methodology matches W1 vetting discipline (clean-slate, fixed-dispatcher evidence, not recycled 0.2.13 findings)
- Checkpoint at `pending_audit`, W0 acceptance archive written

**Estimated budget:** 3-4 hours Claude session. Each model re-vet is ~20-40 min wall-clock (load, probe sequence, structured output test, raw response inspection).

---

## W1 — Ollama Tier 1 capability audit

**Scope:** Define Tier 1 requirement list for Ollama as control plane. Probe each requirement against all operational LLMs from W0. Classify per requirement.

**Requirement list (draft; finalize at W1 begin):**

1. **Concurrent model awareness** — `/api/ps` accurately reports loaded models, VRAM usage, context length
2. **LRU eviction predictability** — with 4 models totaling 19.3GB on 8GB VRAM, verify eviction order when new model requested (oldest unused evicts first)
3. **Explicit unload API** — `keep_alive: 0` in request forces unload; `/api/chat` with minimal prompt + `keep_alive: 0` works per model
4. **Request queuing** — second request while first is mid-inference queues, does not 503
5. **Multi-model routing by name** — all 4 operational model names resolve correctly via `/api/chat` `model` field
6. **Context preservation** — no leak across concurrent requests (stateless per-request confirmed)
7. **Error reporting fidelity** — malformed requests, unknown models, timeout — each returns distinguishable error
8. **Timeout / hang detection** — client-side timeout triggers cleanly; no zombie requests on Ollama side
9. **Model-swap latency** — time to evict Qwen and load Llama 3.2 measured (expectation: seconds, not minutes)
10. **Stop token handling** — Ollama passes user-provided stop tokens through correctly per model family
11. **Chat template application** — `/api/chat` endpoint applies per-model-family templates correctly (template leak absence per W0 vetting)
12. **Embedding endpoint presence** — `/api/embed` accessible and does not interfere with `/api/chat` (nomic validation deferred; verify coexistence only)

**Classification per requirement:**
- `meets` — probe confirms behavior matches requirement
- `partial` — works but with caveat (e.g., LRU eviction works but is slow, or error reporting works but messages are opaque)
- `fails` — behavior does not match requirement

**Deliverables:**
- `ollama-tier1-fitness-0.2.15.md` — per-requirement probe evidence, classification, workaround notes where `partial`
- `artifacts/iterations/0.2.15/ollama-probes/` — raw probe output per requirement

**Acceptance:**
- All requirements classified with evidence
- Any `fails` classifications documented with specific workaround or "Tier 1 not supported, defer to Tier 2+" notation
- Decision criterion: if any critical requirement (multi-model routing, LRU eviction, explicit unload) fails, Tier 1 feasibility is at risk — document and escalate to Kyle before W2 begin

**Estimated budget:** 2-3 hours. Most probes are quick HTTP calls; LRU eviction test requires sequential multi-model loads to observe.

---

## W2 — Dispatcher protocol hardening

**Scope:** Harden `src/aho/pipeline/dispatcher.py` for multi-model Tier 1 use based on W0 roster and W1 capability findings.

**Specific hardening concerns:**

1. **Model-family stop tokens** — current dispatcher hardcodes Qwen stop tokens (`<|endoftext|>`, `<|im_end|>`). Must dispatch family-appropriate tokens:
   - Qwen 3.5: `<|endoftext|>`, `<|im_end|>`
   - Llama 3.x: `<|eot_id|>`, `<|end_of_text|>`
   - GLM: verify from model docs during W0
   - Nemotron: verify from model docs during W0
   - Implementation: model-family lookup table, selection based on `model_id` prefix or explicit mapping

2. **Error handling per failure mode** — replace any blanket `except Exception` with specific error types (G083 compliance):
   - `MalformedResponseError` — JSON parse failure, missing expected fields
   - `TemplateLeakError` — detected template tokens in response
   - `ModelUnavailableError` — model not loaded and can't load (OOM, missing)
   - `TimeoutError` — request exceeded configured timeout
   - `DispatchError` — catch-all for unexpected, raises to orchestrator

3. **Retry + backoff** — configurable retry count (default 2) with exponential backoff; idempotent retries only (no retry on template-leak, which indicates systemic issue)

4. **Per-stage timeout enforcement** — dispatcher respects stage-level timeout passed by orchestrator; does not ignore or extend silently

5. **Model-swap handling** — if request targets model not currently loaded and VRAM requires eviction, dispatcher either waits gracefully or surfaces `ModelSwapInProgress` status to orchestrator (design decision: wait-with-timeout, not fail)

**Deliverables:**
- Updated `src/aho/pipeline/dispatcher.py`
- New / expanded `artifacts/tests/test_dispatcher_chat_api.py` — unit tests for each hardening concern (~12-15 tests)
- `artifacts/iterations/0.2.15/dispatcher-hardening-notes.md` — design decisions documented

**Acceptance:**
- All hardening concerns addressed with code + unit test
- No new `except Exception` blocks (G083)
- Canonical paths preserved (G075, G082)
- Unit tests pass
- Integration sanity check — dispatcher still produces clean output on W1.5-baseline-style probe

**Estimated budget:** 2-3 hours. Unit test writing is the bulk.

---

## W3 — Nemoclaw re-vetting + ADR dispatcher choice

**Scope:** Nemoclaw on fixed dispatcher: explicit routing test with all 4 operational LLMs. Multi-model routing via Nemoclaw. Measured comparison: direct Ollama (current, W2-hardened) vs Nemoclaw for equivalent operations. ADR documenting dispatcher choice.

**Tests:**
1. Nemoclaw explicit routing to each of 4 operational LLMs — output clean (per W0 vetting criteria applied through Nemoclaw path)
2. Nemoclaw multi-model routing — dispatch sequence Qwen → Llama → GLM → Nemotron works without state corruption
3. Latency comparison — direct Ollama HTTP vs Nemoclaw for equivalent `/api/chat` request, N=10 per model, report mean and stddev
4. Error handling comparison — malformed request, unknown model, timeout — does each path surface errors cleanly?

**ADR document:**
- Location: `artifacts/adrs/adr-NNN-tier1-dispatcher-choice.md`
- **ADR number (NNN):** determined at W3 execution time by reading `artifacts/adrs/` index and using next available number. Do NOT fabricate.
- **Decision:** direct Ollama HTTP (current) / Nemoclaw wrapper / thin custom wrapper
- **Rationale:** measured evidence from tests above; Pillar 4 (wrappers are tool surface) weighed against latency and Tier 1 simplicity
- **Tradeoffs:** latency cost of wrapper vs observability benefit; testability; future extensibility
- **Alternatives considered:** each with why-not

**Deliverables:**
- `artifacts/iterations/0.2.15/nemoclaw-test-results.md` — probe evidence
- `artifacts/adrs/adr-NNN-tier1-dispatcher-choice.md` — the ADR
- `artifacts/iterations/0.2.15/dispatcher-decision-0.2.15.md` — iteration-level summary (distinct from the canonical ADR)

**Acceptance:**
- All 4 LLMs routed via Nemoclaw with W0 vetting criteria applied (operational / partial / compromised per path)
- Latency data collected and documented
- ADR published with correct next-available number (verified against ADR index)
- Decision explicit and evidence-based
- Pillar 4 examination present in ADR

**Estimated budget:** 2-3 hours. Latency testing is the wall-clock sink.

---

## W4 — Integration + close

**Scope:** Full cascade run with cross-model role assignment. Tier 1 install.fish finalized. Iteration close.

**Cross-model cascade run:**
- Target document: same NoSQL manual used in 0.2.14 W1.5 (for baseline comparison) OR smaller test document if bandwidth limited
- Role assignment depends on W0 outcomes:
  - Producer = Qwen 3.5:9B
  - Indexer_in / Indexer_out = Llama 3.2:3B (fast triage-tier)
  - Auditor = GLM if operational, Nemotron if operational, Qwen if both compromised
  - Assessor = Qwen if no other option; different operational model otherwise
- Output directory: `artifacts/iterations/0.2.15/smoke-test/cross-model-run-1/`

**Comparison to 0.2.14 W1.5 baseline:**
- Did cross-model Auditor reduce rubber-stamp pattern? (check `delta_validations` distribution — any rejections or conditionals when Auditor ≠ Producer?)
- Did cross-model assignment produce different output characteristics? (length, language consistency, technical specificity)
- Did new failure modes emerge from model diversity? (handoff format mismatches, schema differences)

**install.fish Tier 1 section:**
- Machine detection logic (VRAM check, Arch-family check)
- Tier 1 decision: `if VRAM >= 8GB and < 16GB then Tier 1`
- Tier 1 install steps:
  - Core aho install (unchanged)
  - Ollama install + verify
  - Model pulls: Qwen 3.5:9B, Llama 3.2:3B (plus GLM and Nemotron if operational post-W0)
  - Dispatcher config generation
  - Baseline vetting probe on install target machine
- Explicit "what's NOT installed at Tier 1" — nomic-embed-text, Gemma 2, DeepSeek, Mistral-Nemo — all deferred to higher tiers

**Deliverables:**
- `artifacts/iterations/0.2.15/smoke-test/cross-model-run-1/` — full trace, per-stage artifacts, trace.json
- `artifacts/iterations/0.2.15/cross-model-cascade-comparison.md` — side-by-side with W1.5 baseline
- `install.fish` updated with Tier 1 section
- `artifacts/iterations/0.2.15/retrospective-0.2.15.md`
- `artifacts/iterations/0.2.15/carry-forwards.md`
- `artifacts/iterations/0.2.15/aho-bundle-0.2.15.md` (section spec per aho bundle convention — verify count/structure from aho canonical bundle spec, not memory recall)
- `aho-run-0.2.15.md` — sign-off sheet
- `artifacts/iterations/0.2.15/wiring-signoff-0.2.15.md` — Kyle decision input (distinct from 0.2.14's wiring-signoff; 0.2.15 adds "shippable Tier 1" dimension)

**Hard gate blocker:**
- All 4 LLMs wired through Ollama dispatcher (verified via W0 vetting + W2 integration)
- All 4 LLMs vetted with fixed-dispatcher evidence (W0 output)
- Cross-model cascade test completes successfully (this workstream)
- If any of the above fails, iteration has not met charter — rescope, extend, or accept partial close with explicit non-shipping status

**Estimated budget:** 4-5 hours. Cross-model cascade wall-clock is ~30-45 min. Retrospective + carry-forwards + bundle is 1-2 hours of writing.

---

## Cross-iteration carry tracking

Inherited from 0.2.14:
- `emit_workstream_complete()` side-effect root cause unresolved
- `test_workstream_events.py` checkpoint corruption
- Gotcha registry location unknown
- Auditor role-prompt bifurcation (not fixed in 0.2.15)
- Capability-routed vs role-assigned cascade architectural decision (not forced in 0.2.15)
- Executor-as-outer-loop-judge (Critic/Arbiter) candidate (0.2.16+)
- Cross-project contamination risk (ongoing vigilance required throughout 0.2.15)

Generated in 0.2.15 (candidate carry-forwards for 0.2.16+):
- nomic + ChromaDB RAG integration (deferred from 0.2.15)
- Tier 2/3 roster expansion (Gemma 2, DeepSeek, Mistral-Nemo) — requires P3 clone or Luke's machine
- Fleet bootstrap iteration arc (0.2.16 A8cos minimal, 0.2.17 Luke full, 0.2.18 P3 production)

---

## Process discipline

Same as 0.2.14 close. Summary:
- `workstream_start` fires AFTER AHO_ITERATION env confirmed set
- `workstream_complete` fires only after audit archive exists with pass or pass_with_findings
- Audit archive overwrites forbidden
- Sign-off boxes are Kyle's
- No git ops by agents
- Raw response is ground truth
- No speed claims without tuned-baseline measurement
- Cross-project contamination vigilance per CLAUDE.md / GEMINI.md

---

*Plan doc 0.2.15. Design doc at `artifacts/iterations/0.2.15/aho-design-0.2.15.md` contains pillars, trident, scope, contingencies. This plan expands workstream execution detail. ADR number for W3 determined at W3 execution time from ADR index — not pre-fabricated here.*
