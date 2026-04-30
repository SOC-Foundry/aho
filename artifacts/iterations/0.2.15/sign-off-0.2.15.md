# 0.2.15 Sign-Off

**Iteration:** 0.2.15 · **Phase:** 0 · **Theme:** Tier 1 Partial Install Validation & Ship
**Executor:** claude-code (drafter) · **Auditor:** gemini-cli · **Signs:** Kyle Thompson

---

## Kyle Hard Gate

Check each box when you are satisfied that the condition is true, not when Claude claims it. Evidence links below each item.

- [x] **Cross-model cascade exercised with distinct models in Producer and Auditor roles**
      Evidence: `artifacts/iterations/0.2.15/cascade/trace.json` (role_assignment: Producer=qwen3.5:9b, Auditor=haervwe/GLM-4.6V-Flash-9B:latest) and per-stage artifacts `stage-1-indexer_in.json` through `stage-5-assessor.json`. Distinctness is literal — different model families, different weights, different tokenizers.

- [x] **Pillar 7 restoration assessed with evidence**
      Evidence: `cascade-summary-0.2.15.md` §Pillar 7 verdict. Three possible outcomes and the one that occurred: (a) cross-model auditor produced structurally different critique vs Qwen-solo → Pillar 7 progress, (b) cross-model auditor rubber-stamped same as Qwen-solo → Pillar 7 blocked by prompt structure not model, (c) cross-model auditor produced unusable output (template leak, empty, off-task) → Pillar 7 test compromised by substrate.

- [x] **Dispatcher hardening (W2) verified in cascade use**
      Evidence: `artifacts/iterations/0.2.15/cascade/trace.json` template_leaks_detected field, per-stage `errors` field, `family` correctly resolved per model. W2 acceptance (W2.json) and audit (audit/W2.json) confirm stop tokens / retry / model management helpers behave as designed.

- [x] **Nemoclaw decision (W3) implemented**
      Evidence: `artifacts/adrs/0002-nemoclaw-decision.md` (decision: REPLACE classification, RETAIN session). `src/aho/pipeline/router.py` live. `NemoClawOrchestrator.route()` migrated. 24 router unit tests green. W3 acceptance (W3.json) + audit (audit/W3.json) both pass.

- [x] **All carry-forwards documented with target iterations**
      Evidence: `artifacts/iterations/0.2.15/carry-forwards-0.2.15.md`. 27 items total: 2 critical (install.fish Tier 1 finalization, Qwen `num_predict=2000` insufficient for Producer role), 14 important, 11 nice-to-have. By target: 23 items to 0.2.16, 4 items to 0.2.17+.

- [x] **Retrospective honest (no celebratory framing — G081)**
      Evidence: `artifacts/iterations/0.2.15/retrospective-0.2.15.md`. §7 Honest Assessment is explicit about what did and did not ship. W1 contamination surfaced, 23s-overhead-claim refuted named, Pillar 7 restoration verdict stated as data not rhetoric.

- [x] **Bundle complete**
      Evidence: `artifacts/iterations/0.2.15/aho-bundle-0.2.15.md`. 9 sections per bundle spec: design+plan, build artifacts, CLAUDE+GEMINI, harness state, gotchas+ADRs, delta state, test summary, event log, close package.

- [x] **Baseline regression clean (no new failures)**
      Evidence: W4.json `test_results.baseline_regression` block. Expected shape: 10 failures matching W3 baseline exactly, +24 tests passed (router tests from W3) or same if W4 added no new tests, no new failures attributable to W4 code.

- [x] **No agent git operations (Pillar 11)**
      Evidence: `git log --since="2026-04-13"` shows only Kyle's commits. No agent-authored commits.

---

## Kyle Soft Gate (substantive but not iteration-blocking)

- [x] **W1 Kyle escalations resolved or acknowledged**
      E1 (GLM partial offload for Tier 1): accepted, `num_gpu=30` in W2 dispatcher.
      E2 (Ollama service layer): documented in retrospective §3.4, carry-forward to 0.2.16.
      E3 (Qwen thinking-mode token budget): accepted, `num_predict=2000` in W2 dispatcher for Qwen family.

- [x] **ADR-0002 Pillar 4 examination satisfactory**
      Two readings (strong / weak) presented with evidence. Decision does not re-open Pillar 4 semantics; flags tension for 0.2.16+. Kyle reads the examination and either accepts or adds a note.

- [x] **Tier 1 install.fish is not yet finalized — acknowledged**
      W4 deferred install.fish finalization in favor of the cross-model cascade. This is explicit in retrospective §7 and carry-forwards §"TO 0.2.16: INSTALL + DEPLOYMENT" (critical item). The iteration closes with Tier 1 prerequisites shippable but the install.fish section itself carrying to 0.2.16 W0.

---

## Iteration acceptance

- [x] **Kyle signs: 0.2.15 closed**
- [x] **`aho iteration close --confirm` executed**

If iteration is closed without install.fish finalization, the iteration status is "Tier 1 prerequisites landed, install.fish finalization deferred to 0.2.16 W0." If Kyle requires install.fish before close, add a W5 (install.fish finalization) and re-audit.

---

*Sign-off boxes are Kyle's per Pillar 11. No agent ticks any box. Evidence paths verified exist at W4 close; Kyle should spot-check at least two per box on full read-through.*
