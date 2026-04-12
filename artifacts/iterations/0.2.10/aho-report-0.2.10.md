# Report — aho 0.2.10

**Generated:** 2026-04-12T05:45:27Z
**Iteration:** 0.2.10
**Phase:** 0
**Run type:** single-agent
**Status:** active

---

## Executive Summary

This iteration executed 17 workstreams: 17 passed, 0 failed, 0 pending/partial.
126 events logged during execution.
Postflight: 10/18 gates passed, 7 failed.

---

## Workstream Detail

| Workstream | Status | Agent | Events | Wall Clock |
|---|---|---|---|---|
| W0 | pass | claude-code | 1 | - |
| W1 | pass | claude-code | 1 | - |
| W10 | pass | claude-code | 1 | - |
| W11 | pass | claude-code | 1 | - |
| W12 | pass | claude-code | 1 | - |
| W13 | pass | claude-code | 1 | - |
| W14 | pass | claude-code | 1 | - |
| W15 | pass | claude-code | 1 | - |
| W16 | pass | claude-code | 1 | - |
| W2 | pass | claude-code | 1 | - |
| W3 | pass | claude-code | 1 | - |
| W4 | pass | claude-code | 1 | - |
| W5 | pass | claude-code | 1 | - |
| W6 | pass | claude-code | 1 | - |
| W7 | pass | claude-code | 1 | - |
| W8 | pass | claude-code | 1 | - |
| W9 | pass | claude-code | 1 | - |

---

## Component Activity

| Component | Kind | Status | Owner | Notes |
|---|---|---|---|---|
| openclaw | agent | active | soc-foundry | global daemon, systemd user service, Unix socket; activated 0.2.2 W1 |
| nemoclaw | agent | active | soc-foundry | Nemotron orchestrator, systemd user service, Unix socket; activated 0.2.2 W2 |
| telegram | external_service | active | soc-foundry | send-only bridge, systemd user service, age-encrypted secrets; activated 0.2.2 W3 |
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
| workstream-agent | agent | active | soc-foundry | Qwen-bound, conductor-dispatched, activated 0.2.3 W2 |
| evaluator-agent | agent | active | soc-foundry | GLM-bound, review role, activated 0.2.3 W2 |
| harness-agent | agent | active | soc-foundry | Nemotron-bound, watcher daemon, activated 0.2.3 W2 |
| conductor | agent | active | soc-foundry | orchestrator pattern, dispatches to role-split agents, activated 0.2.3 W2 |
| mcp-firebase-tools | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-context7 | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-firecrawl | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-playwright | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-dart | mcp_server | active | dart-team | SDK-bundled (Dart 3.9+), replaces broken flutter-mcp, activated 0.2.8 W3 |
| mcp-server-filesystem | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-memory | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-sequential-thinking | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-everything | mcp_server | active | soc-foundry | npm global, reference/test server, activated 0.2.3 W1, added to manifest 0.2.8 W7 |
| component-manifest | python_module | active | soc-foundry | added 0.1.15 W1 |

**Total components:** 85
**Status breakdown:** 85 active

---

## Postflight Results

| Gate | Status | Message |
|---|---|---|
| app_build_check | ok | web build present (1502 bytes) |
| artifacts_present | fail | report_artifact missing |
| build_log_complete | ok | no workstreams found in design |
| bundle_completeness | fail | canonical missing: aho-report-0.2.10.md |
| bundle_quality | ok | Bundle valid (591 KB, run_type: single-agent) |
| canonical_artifacts_current | ok | all 10 canonical artifacts at 0.2.10 |
| changelog_current | ok | CHANGELOG.md contains 0.2.10 |
| gemini_compat | ok | Gemini-primary CLI sync verified |
| iteration_complete | fail | Checkpoint: All workstreams reached final state
Build Log: Build log manual ground truth present
Secret Scan: No plaintext secrets found in tracked files
install.fish: install.fish syntax OK
Artifacts: Missing artifacts: report.md |
| manifest_current | ok | all 534 file hashes current |
| mcp_canonical_registry_verify | ok | all 9 MCP packages registry-verified |
| mcp_sources_aligned | ok | MCP sources aligned: 9 entries match |
| pillars_present | fail | 1 errors: Design doc missing §3 (Trident) |
| pipeline_present | ok | SKIP — no pipelines declared in .aho.json |
| readme_current | fail | README.md last modified 2026-04-12T05:45:18.210776+00:00 < iteration start 2026-04-12T07:00:00Z |
| run_complete | deferred | Sign-off incomplete: No Sign-off section found in run report |
| run_quality | fail | 2 quality check failures |
| structural_gates | fail | Structural gates: 0 pass, 3 fail, 1 deferred |

---

## Risk Register

- **2026-04-12T05:42:43.435626+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T05:42:43.452674+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-12T05:42:43.457470+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T05:42:44.832594+00:00** [llm_call] missing credentials
- **2026-04-12T05:43:05.806511+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-12T05:43:05.807152+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-12T05:43:05.816356+00:00** [llm_call] missing credentials
- **2026-04-12T05:43:05.819042+00:00** [llm_call] connection refused

---

## Carryovers

*(no notes from prior iteration)*

---

## Next Iteration Recommendation

- Address failed postflight gates: readme_current, artifacts_present, structural_gates, pillars_present, run_quality, bundle_completeness, iteration_complete
