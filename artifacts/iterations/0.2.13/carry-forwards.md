# Carry-Forwards — 0.2.13

**Generated:** 2026-04-13 W10 Close

---

## TO 0.2.14: MODEL VIABILITY + DEFERRED REPAIR

- **Model viability assessment** — The dominant problem. GLM-4.6V-Flash-9B at Q4_K_M cannot produce structured output (80% timeout, 20% wrong schema). Nemotron-mini:4b returns "feature" 80% of the time. Options: heavier quantization (Q8_0), different evaluator model (Qwen-as-evaluator), text-mode parsing (accept unstructured GLM output), or abandon local LLM evaluation. **0.2.14 W0 candidate — must resolve before any dispatch work.**

- **G083 bulk fix (35 definitive sites)** — Deferred from W6-W8. Sites identified in 0.2.12 G083 scan. Tiered repair plan (agents/ → council/ → remainder) remains valid. Blocked on model viability: fixing exception handlers around non-functional models produces correct error handling of useless responses. **0.2.14 mid-iteration candidate, after model viability resolved.**

- **G083 ambiguous triage (117 sites)** — Deferred from W9. Classification-only (safe | G083-class | needs-human-review). Execution deferred to 0.2.15+. **0.2.14 late-iteration candidate.**

- **Nemoclaw decision (ADR-047)** — Deferred from W3-W4. Original premise: benchmark Nemoclaw vs direct Ollama on latency/quality/cost, then decide keep/replace/hybrid. Premise needs revision per W2.5 substrate findings — decision depends on which models survive viability assessment. **0.2.14, after model viability.**

- **OpenClaw audit** — Deferred from W5. Status remains "unknown" in council inventory. 7-section audit shape defined (matches Qwen/GLM/Nemotron audits from 0.2.12). **0.2.14 candidate, independent of model viability.**

- **Casing-variant Gotcha/gotch design decision** — Kyle input needed. Nemotron returns casing variants of categories ("Gotcha", "gotch"). Current parser: case-insensitive substring for close matches, NemotronParseError for distant mismatches. Options: soft-match, strict, or new diagnostic category. **Kyle decision before 0.2.14 plan.**

- **Pattern C protocol: terminal-event session requirement** — Protocol doc should specify that `workstream_complete` events require a fresh executor session after audit, not an inline emit during the audit session. W0 role-crossing and the hygiene session exposed this gap. **0.2.14 harness update.**

- **Audit archive duplication prevention** — Triple-audit session created timestamp coherence risk. Protocol should specify one-audit-per-session or document batch-audit semantics. **0.2.14 protocol doc update.**

- **Pre-existing G083 site: `nemotron_client.py:164` (`_call()`)** — Disclosed in W2 acceptance, confirmed in W2 audit. `except Exception as e: return f"Error: {e}"`. In the raw-call path (used by evaluator.py), not the classifier path. **0.2.14 G083 Tier 3 candidate.**

- **OTEL per-agent instrumentation** — Deferred from 0.2.13 design. Traces for per-agent dispatch metrics. **0.2.14+ candidate.**

- **README content review** — Deferred from 0.2.12→0.2.13→0.2.14. Staleness noted at 0.2.11 boundary. **0.2.14 candidate.**

- **Postflight robustness** — W0 patched the 2-tuple ValueError as a tactical fix. Proper architecture (plugin return contract, error handling) deferred. **0.2.14 candidate.**

- **Qwen cameo execution** — Deferred from W8.5. Site scoped in W0 (`workstream_gate.py:24`). Three-executor forensics data (Claude, Gemini, Qwen) still desired. **0.2.14 candidate, after model viability.**

- **workstream_start event emission** — 0.2.13 never emitted workstream_start events for any workstream. Event log has complete events but no starts. Cosmetic gap but reduces lifecycle traceability. **0.2.14 harness fix.**

---

## AUDIT FINDINGS — W10 (added post-audit reconciliation, 2026-04-13)

- **Root directory hygiene** — 22+ `patch_*.py` and `run_acceptance_w*.py` scripts at repo root, plus `install.fish` backup variants. Disposition criteria for 0.2.14 W0: (a) grep references in `src/` and `artifacts/` before any deletion, (b) move iteration-scratch scripts to `artifacts/iterations/{iter}/scratch/`, (c) promote any reusable migration logic to `scripts/migrations/`, (d) delete one-shot scripts only with Kyle confirmation. Bonus: `firebase-debug.log` should not be tracked (add to `.gitignore`). **0.2.14 W0 candidate.**

- **3–4 workstream cap for 0.2.14 cadence** — Kyle directive. Last two iterations both planned 11–20 workstreams and shipped 4–9. Surgical work compresses well; planning should size down. 0.2.14 plan should not exceed 4 work workstreams plus W0 setup and Wn close. **0.2.14 planning constraint.**

- **README/CHANGELOG narrative gap** — 2 iterations behind. Append-only, narrative-preserving update needed in 0.2.14 W0. Story lost includes: 0.2.12 council audits, gotchas G078–G083, 0.2.13 dispatch repair (W1 GLM parser, W2 Nemotron classifier), Pattern C trial, W2.5 substrate findings. **0.2.14 W0 candidate.**

- **workstream_start protocol gap** — Zero `workstream_start` events fired in 0.2.13. Pattern C protocol doc (`artifacts/harness/pattern-c-protocol.md`) should explicitly require `workstream_start` emit when Claude begins a workstream, mirroring `workstream_complete` on the other end. Lifecycle events should bracket every workstream: start at entry, complete at terminal. **0.2.14 W0 — patch protocol doc.**
