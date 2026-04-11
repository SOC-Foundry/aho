# Iteration 1 Close — aho

**Iteration:** 1 (runs 0.1.2–0.1.16)
**Graduated:** 2026-04-11
**Phase:** 0

---

## Iteration 1 Objective

Build the aho harness from scratch. Starting from a blank Python package (originally "iao"), deliver a complete agentic orchestration system with: artifact loop, evaluator, postflight gates, secrets architecture, gotcha registry, component manifest, mechanical report builder, and multi-agent coordination — all governed by the Eleven Pillars.

---

## Runs Delivered

| Run | Theme |
|---|---|
| 0.1.2 | Initial scaffolding and artifact loop |
| 0.1.3 | Bundle quality gates, src-layout migration |
| 0.1.4 | Evaluator and synthesis pipeline |
| 0.1.5 | Incomplete — scope folded into 0.1.6 |
| 0.1.6 | Precursor artifacts (no design doc) |
| 0.1.7 | "Let Qwen Cook" — artifact loop made Qwen-friendly |
| 0.1.8 | Pillar rewrite (10→11), hardcoded pillar cleanup |
| 0.1.9 | IAO→AHO rename, RAG archive rebuild |
| 0.1.10 | §22 instrumentation restore, bundle generator fix |
| 0.1.11 | Run file rename, project root confirmation, test hygiene |
| 0.1.12 | Evaluator baseline reload, smoke script checkpoint-awareness |
| 0.1.13 | Phase 0 realignment, folder reorg, /bin wrapper scaffolding |
| 0.1.14 | Terminology sweep, canonical artifacts, build log stub, postflight repair |
| 0.1.15 | Foundation for Phase 0 exit: components manifest, OTEL, Flutter scaffold |
| 0.1.16 | Close sequence repair, canonical artifacts gate, iteration 1 graduation |

---

## What Was Built

- **Secrets architecture** — age encryption + OS keyring backend with session management
- **Artifact loop** — Design → Plan → Build Log → Report → Bundle, Qwen-generated via Ollama
- **src-layout Python package** — installable via `pip install -e .`
- **IAO→AHO terminology sweep** — full rename across codebase and artifacts
- **Component manifest** — 72-entry YAML with status tracking and attribution
- **OTEL dual emitter** — OpenTelemetry traces to Jaeger + console
- **Flutter scaffold** — 5-page app shell with NavigationRail
- **Mechanical report builder** — checkpoint + event log → structured report (ADR-042)
- **Postflight gate library** — 17 plugin-based gates loaded dynamically by doctor
- **Build log stub generator** — auto-generates from checkpoint + event log when manual absent
- **Canonical artifacts discipline** — 7 versioned artifacts with automated currency check
- **Close sequence ordering** — tests → bundle → report → run file → postflight → checkpoint
- **Gotcha registry** — 16+ entries (G060–G115) with mitigations
- **Evaluator** — Qwen synthesis with ADR-015 self-grading cap, dynamic baseline reload
- **Human feedback loop** — run file → Kyle's Notes → seed JSON → next iteration context

---

## What Was Deferred (carries to Iteration 2)

- openclaw global wrapper (stub, next: 0.2.1)
- nemoclaw global wrapper (stub, next: 0.2.1)
- Telegram bridge real implementation (stub, next: 0.2.1)
- soc-foundry/aho first push (0.2.1)
- P3 clone-to-deploy validation (0.2.2)

---

## Lessons Learned

1. **Split-agent model works for tight runs.** Claude Code single-agent handled 5-workstream iterations in under 15 minutes. Gemini handoff is valuable for bulk execution but not required for foundation work.
2. **Mechanical-first artifacts are trustworthy.** The report builder and run file generator produce ground-truth outputs from checkpoint data. Qwen synthesis is optional commentary, never structural.
3. **Postflight as gatekeeper catches real issues.** The plugin architecture scales — 17 gates loaded dynamically, each independently testable.
4. **Component visibility kills the deferral pattern.** Once stubs are visible in every report (0.1.15+), deferred work can't hide.
5. **Ordering bugs are silent killers.** The 0.1.15 close sequence ran postflight before artifact generation, causing 5 false-flag failures. Fixed in 0.1.16.
6. **Prose drift across rename sweeps needs mechanical enforcement.** The canonical artifacts gate (0.1.16) ensures version headers stay current.

---

## Iteration 1 Exit Criteria Evaluation

| Criterion | Status |
|---|---|
| aho installable as Python package | pass |
| Secrets architecture functional | pass |
| Folders consolidated to /artifacts/ | pass |
| /bin wrapper scaffolding established | pass |
| Agent instructions (CLAUDE.md/GEMINI.md) written | pass |
| Artifact loop end-to-end | pass |
| Postflight gate library operational | pass |
| Component manifest with status tracking | pass |
| Close sequence mechanically correct | pass (fixed 0.1.16) |
| 80+ tests passing | pass |

---

*Iteration 1 graduated 2026-04-11. Iteration 2 (0.2.x) begins immediately.*
