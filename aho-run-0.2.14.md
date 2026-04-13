# aho-run-0.2.14

**Phase:** 0 | **Iteration:** 0.2.14
**Theme:** Council wiring verification + cascade smoke test
**Execution model:** Pattern C modified (Claude drafts, Gemini audits, Kyle signs)
**Sessions:** 2 | **Workstreams delivered:** 4 (W0, W1, W1.5, W2)

---

## What happened

3 workstreams planned (W0 setup, W1 vet+wire+smoke, W2 close). 4 delivered — W1.5 added mid-iteration after Gemini's W1 audit surfaced two dispatcher bugs (context truncation + template leakage) that contaminated run-1 smoke test data. W1.5 repaired the dispatcher, re-ran the smoke test, all 6 hard gates passed. W2 closes with sign-off package, retrospective, and carry-forwards.

Charter was binary: does the council exist as a verifiable wired system? Answer: yes, with substrate findings. Cascade architecture works end-to-end. Dispatcher honest after W1.5 fix. Council is real-but-thin — one operational LLM, Pillar 7 violated, expanded roster needed.

## Session 1 — W0 + W1

| Workstream | Scope | Acceptance | Audit |
|------------|-------|------------|-------|
| W0 | Setup + hygiene + model docs + inventory + NoSQL staging | pass (9/9 checks) | No audit archive located |
| W1 | Council vet (16 members) + pipeline build + smoke test run-1 | pass (12/12 checks) | pass_with_findings (42 min) — dispatcher bugs + characterization drift |

**W1 audit headline:** Gemini identified `/api/generate` template leakage and `num_ctx` 4096 default. Claude's "honest empty" and "model quality limitation" characterizations were drift — issues were dispatcher configuration, not model quality.

## Session 2 — W1.5 + W2

| Workstream | Scope | Acceptance | Audit |
|------------|-------|------------|-------|
| W1.5 | Dispatcher `/api/chat` migration + re-smoke (run-2) | pass (6 hard gates, 6 unit tests) | pass (25 min) |
| W2 | Close: sign-off package, retrospective, carry-forwards, bundle | pending_audit | — |

---

## Sign-off

- [ ] Kyle reviewed W0 acceptance + W1 audit findings
- [ ] Kyle confirmed W1.5 addition was warranted
- [ ] Kyle reviewed retrospective (honest characterization of substrate findings)
- [ ] Kyle reviewed wiring sign-off package (Hard Gate 3 decision: a/b/c)
- [ ] Kyle reviewed carry-forwards (18 items)
- [ ] Kyle ticked Hard Gate 3: wiring complete / partial / incomplete

---

## Kyle's Notes

Decisions the 0.2.15 matrix should now inform:

1. **Wiring complete sign-off (a/b/c)** — Sign-off package recommends (a): wiring complete, 0.2.15 proceeds to measurement matrix. See `artifacts/iterations/0.2.14/wiring-signoff.md`.

2. **Council roster for 0.2.15** — Add all 4 candidates or phased?
   - Llama 3.2 3B on NZXTcos already (~2GB)
   - DeepSeek-Coder-V2 16B-Lite + Mistral-Nemo 12B land with P3 clone
   - Gemma 2 9B any machine
   - Phased approach: start with Qwen + Llama (already on disk), expand as models pulled

3. **Capability-routed vs role-assigned cascade** — Decide in 0.2.15 W0 or carry as open? Fixed 5-stage sequence vs dynamic routing based on input classification.

4. **Dispatcher choice** — Direct-Ollama (current) or wrap with Nemoclaw (~20 lines for model_id routing) or new thin wrapper? Pillar 4 argues wrapper.

5. **Auditor role redesign** — Restructure validations to force genuine judgment, or accept current bifurcation (rubber-stamp validations + genuine critique in additional_findings)?

6. **Executor-as-outer-loop-judge architecture** — Implement in 0.2.15 alongside roster expansion, defer to 0.2.16, or skip entirely? Two-tier Critic + Arbiter pattern with harness-wide calibration signal storage, N=3 rejection threshold. Working names to be replaced after first real test.

7. **A8cos reframed** — Orchestration/dev machine (integrated GPU/CPU). P3 clone is model expansion target. 0.2.16+ candidate iteration for A8cos bootstrap focuses on orchestration role, not council execution.

---

## Artifacts

| Deliverable | Path |
|-------------|------|
| Design | `artifacts/iterations/0.2.14/aho-design-0.2.14.md` |
| Plan | `artifacts/iterations/0.2.14/aho-plan-0.2.14.md` |
| W0 acceptance | `artifacts/iterations/0.2.14/acceptance/W0.json` |
| W1 acceptance | `artifacts/iterations/0.2.14/acceptance/W1.json` |
| W1 audit | `artifacts/iterations/0.2.14/audit/W1.json` |
| W1.5 acceptance | `artifacts/iterations/0.2.14/acceptance/W1_5.json` |
| W1.5 audit | `artifacts/iterations/0.2.14/audit/W1_5.json` |
| W2 acceptance | `artifacts/iterations/0.2.14/acceptance/W2.json` |
| Wiring sign-off | `artifacts/iterations/0.2.14/wiring-signoff.md` |
| Retrospective | `artifacts/iterations/0.2.14/retrospective-0.2.14.md` |
| Carry-forwards | `artifacts/iterations/0.2.14/carry-forwards.md` |
| Bundle | `artifacts/iterations/0.2.14/aho-bundle-0.2.14.md` |
| Council vetting | `artifacts/iterations/0.2.14/council-vetting-results.md` |
| Dispatch decision | `artifacts/iterations/0.2.14/dispatch-decision.md` |
| Smoke test run-1 | `artifacts/iterations/0.2.14/smoke-test/run-1/` |
| Smoke test run-2 | `artifacts/iterations/0.2.14/smoke-test/run-2/` |
| Llama pull record | `artifacts/iterations/0.2.14/llama-3.2-3b-pulled.md` |
| Council models | `artifacts/council-models-0.2.14.md` |
| Council inventory | `artifacts/iterations/0.2.14/council-inventory.md` |
