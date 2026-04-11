# Report — aho 0.2.1

**Generated:** 2026-04-11T14:34:28Z
**Iteration:** 0.2.1
**Phase:** 0
**Run type:** mixed
**Status:** closed

---

## Executive Summary

This iteration executed 7 workstreams: 7 passed, 0 failed, 0 pending/partial.
247 events logged during execution.
Postflight: 12/15 gates passed, 0 failed.

---

## Workstream Detail

| Workstream | Status | Agent | Events |
|---|---|---|---|
| W0 | pass | claude-code | 0 |
| W1 | pass | claude-code | 0 |
| W2 | pass | claude-code | 0 |
| W3 | pass | claude-code | 0 |
| W4 | pass | claude-code | 0 |
| W5 | pass | claude-code | 0 |
| W6 | pass | claude-code | 0 |

---

## Component Activity

| Component | Kind | Status | Owner | Notes |
|---|---|---|---|---|
| openclaw | agent | stub | soc-foundry | next: 0.1.16; ephemeral Python only; global wrapper + install pending 0.1.16 |
| nemoclaw | agent | stub | soc-foundry | next: 0.1.16; orchestration layer; routing logic stubbed; global wrapper pending 0.1.16 |
| telegram | external_service | stub | soc-foundry | next: 0.1.16; deferred since 0.1.4 charter; bridge real implementation pending 0.1.16 |
| qwen-client | llm | active | soc-foundry |  |
| nemotron-client | llm | active | soc-foundry |  |
| glm-client | llm | active | soc-foundry |  |
| chromadb | external_service | active | soc-foundry |  |
| ollama | external_service | active | soc-foundry |  |
| opentelemetry | external_service | active | soc-foundry | dual emitter alongside JSONL; activated 0.1.15 W2 |
| assistant-role | agent | active | soc-foundry |  |
| base-role | agent | active | soc-foundry |  |
| code-runner-role | agent | active | soc-foundry |  |
| reviewer-role | agent | active | soc-foundry |  |
| cli | python_module | active | soc-foundry |  |
| config | python_module | active | soc-foundry |  |
| doctor | python_module | active | soc-foundry |  |
| logger | python_module | active | soc-foundry |  |
| paths | python_module | active | soc-foundry |  |
| harness | python_module | active | soc-foundry |  |
| compatibility | python_module | active | soc-foundry |  |
| push | python_module | active | soc-foundry |  |
| registry | python_module | active | soc-foundry |  |
| ollama-config | python_module | active | soc-foundry |  |
| artifact-loop | python_module | active | soc-foundry |  |
| artifact-context | python_module | active | soc-foundry |  |
| artifact-evaluator | python_module | active | soc-foundry |  |
| artifact-schemas | python_module | active | soc-foundry |  |
| artifact-templates | python_module | active | soc-foundry |  |
| repetition-detector | python_module | active | soc-foundry |  |
| bundle | python_module | active | soc-foundry |  |
| components-section | python_module | active | soc-foundry |  |
| report-builder | python_module | active | soc-foundry | mechanical report builder, added 0.1.15 W0 |
| feedback-run | python_module | active | soc-foundry |  |
| feedback-prompt | python_module | active | soc-foundry |  |
| feedback-questions | python_module | active | soc-foundry |  |
| feedback-summary | python_module | active | soc-foundry |  |
| feedback-seed | python_module | active | soc-foundry |  |
| build-log-stub | python_module | active | soc-foundry |  |
| pipeline-scaffold | python_module | active | soc-foundry |  |
| pipeline-validate | python_module | active | soc-foundry |  |
| pipeline-registry | python_module | active | soc-foundry |  |
| pipeline-pattern | python_module | active | soc-foundry |  |
| pf-artifacts-present | python_module | active | soc-foundry |  |
| pf-build-log-complete | python_module | active | soc-foundry |  |
| pf-bundle-quality | python_module | active | soc-foundry |  |
| pf-gemini-compat | python_module | active | soc-foundry |  |
| pf-iteration-complete | python_module | active | soc-foundry |  |
| pf-layout | python_module | active | soc-foundry |  |
| pf-manifest-current | python_module | active | soc-foundry | added 0.1.15 W0 |
| pf-changelog-current | python_module | active | soc-foundry | added 0.1.15 W0 |
| pf-pillars-present | python_module | active | soc-foundry |  |
| pf-pipeline-present | python_module | active | soc-foundry |  |
| pf-readme-current | python_module | active | soc-foundry |  |
| pf-run-complete | python_module | active | soc-foundry |  |
| pf-run-quality | python_module | active | soc-foundry |  |
| pf-structural-gates | python_module | active | soc-foundry |  |
| preflight-checks | python_module | active | soc-foundry |  |
| rag-archive | python_module | active | soc-foundry |  |
| rag-query | python_module | active | soc-foundry |  |
| rag-router | python_module | active | soc-foundry |  |
| secrets-store | python_module | active | soc-foundry |  |
| secrets-session | python_module | active | soc-foundry |  |
| secrets-cli | python_module | active | soc-foundry |  |
| secrets-backend-age | python_module | active | soc-foundry |  |
| secrets-backend-base | python_module | active | soc-foundry |  |
| secrets-backend-fernet | python_module | active | soc-foundry |  |
| secrets-backend-keyring | python_module | active | soc-foundry |  |
| install-migrate-config | python_module | active | soc-foundry |  |
| install-secret-patterns | python_module | active | soc-foundry |  |
| brave-integration | python_module | active | soc-foundry |  |
| firestore | python_module | active | soc-foundry |  |
| component-manifest | python_module | active | soc-foundry | added 0.1.15 W1 |

**Total components:** 72
**Status breakdown:** 69 active, 3 stub

---

## Postflight Results

| Gate | Status | Message |
|---|---|---|
| app_build_check | ok | web build present (1502 bytes) |
| artifacts_present | ok | all 3 artifacts present (aho) |
| build_log_complete | warn | design doc not found, skipping completeness check |
| bundle_quality | ok | Bundle valid (322 KB, run_type: mixed) |
| canonical_artifacts_current | ok | all 8 canonical artifacts at 0.2.1 |
| changelog_current | ok | CHANGELOG.md contains 0.2.1 |
| gemini_compat | ok | Gemini-primary CLI sync verified |
| iteration_complete | ok | Checkpoint: All workstreams reached final state
Build Log: Build log manual ground truth present
Secret Scan: No plaintext secrets found in tracked files
install.fish: install.fish syntax OK
Artifacts: All Qwen-generated artifacts present |
| manifest_current | ok | all 71 file hashes current |
| pillars_present | ok | Eleven pillars present in design and README |
| pipeline_present | ok | SKIP — no pipelines declared in .aho.json |
| readme_current | ok | README updated during this iteration (mtime: 2026-04-11T14:22:10.679480+00:00) |
| run_complete | deferred | Kyle's notes section not yet filled in |
| run_quality | ok | Run file passes quality gate |
| structural_gates | pass | Structural gates: 4 pass, 0 fail, 0 deferred |

---

## Risk Register

- **2026-04-11T14:22:30.809794+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:22:30.825151+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T14:22:30.829811+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:22:32.024493+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T14:22:32.025510+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T14:30:58.655814+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:30:58.671447+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T14:30:58.676367+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:31:00.471629+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T14:31:00.472414+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T14:31:44.311152+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:31:44.325988+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T14:31:44.330558+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:31:46.138197+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T14:31:46.138865+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T14:33:45.478379+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:33:45.493965+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T14:33:45.498778+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T14:33:47.381494+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T14:33:47.382589+00:00** [evaluator_run] severity=warn errors=1

---

## Carryovers

*(no notes from prior iteration)*

---

## Next Iteration Recommendation

- All workstreams passed and postflight gates green. Proceed to next iteration.
