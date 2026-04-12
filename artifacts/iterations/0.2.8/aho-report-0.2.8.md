# Report — aho 0.2.8

**Generated:** 2026-04-12T00:01:37Z
**Iteration:** 0.2.8
**Phase:** 0
**Run type:** single-agent
**Status:** active

---

## Executive Summary

This iteration executed 14 workstreams: 14 passed, 0 failed, 0 pending/partial.
23160 events logged during execution.
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
| W2 | pass | claude-code | 1 | - |
| W2.5 | pass | claude-code | 1 | - |
| W3 | pass | claude-code | 2 | 9m 21s |
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
| artifacts_present | fail | build_artifact missing, report_artifact missing |
| build_log_complete | ok | no workstreams found in design |
| bundle_completeness | fail | canonical missing: aho-build-log-0.2.8.md, aho-report-0.2.8.md |
| bundle_quality | ok | Bundle valid (578 KB, run_type: single-agent) |
| canonical_artifacts_current | ok | all 10 canonical artifacts at 0.2.8 |
| changelog_current | ok | CHANGELOG.md contains 0.2.8 |
| gemini_compat | ok | Gemini-primary CLI sync verified |
| iteration_complete | fail | Checkpoint: All workstreams reached final state
Build Log: Manual build log missing at artifacts/iterations/0.2.8/aho-build-log-0.2.8.md
Secret Scan: No plaintext secrets found in tracked files
install.fish: install.fish syntax OK
Artifacts: Missing artifacts: report.md |
| manifest_current | fail | stale hashes: .aho-checkpoint.json, .aho.json, .gitignore |
| mcp_canonical_registry_verify | ok | all 9 MCP packages registry-verified |
| mcp_sources_aligned | ok | MCP sources aligned: 9 entries match |
| pillars_present | fail | 4 errors: Design doc missing Pillar 9; Design doc missing Pillar 10; Design doc missing Pillar 11 |
| pipeline_present | ok | SKIP — no pipelines declared in .aho.json |
| readme_current | fail | README.md last modified 2026-04-11T21:49:23.840484+00:00 < iteration start 2026-04-11T23:00:00Z |
| run_complete | deferred | Sign-off incomplete: All 10 canonical artifacts at 0.2.8, Run report template includes "MCP Tools Invoked" section |
| run_quality | ok | Run file passes quality gate |
| structural_gates | fail | Structural gates: 0 pass, 2 fail, 2 deferred |

---

## Risk Register

- **2026-04-11T23:50:57.799741+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:51:41.056057+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:52:11.086981+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:52:41.093207+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:53:11.107377+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:53:41.139682+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:54:11.156876+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-11T23:54:41.189112+00:00** [llm_call] HTTPConnectionPool(host='localhost', port=11434): Read timed out. (read timeout=30)
- **2026-04-12T00:00:16.264757+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T00:00:16.281308+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-12T00:00:16.286184+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T00:00:17.665547+00:00** [llm_call] missing credentials
- **2026-04-12T00:00:34.236064+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-12T00:00:34.236749+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-12T00:00:34.246643+00:00** [llm_call] missing credentials
- **2026-04-12T00:00:34.250588+00:00** [llm_call] connection refused
- **2026-04-12T00:01:01.509354+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T00:01:01.526564+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-12T00:01:01.531447+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T00:01:02.887682+00:00** [llm_call] missing credentials

---

## Carryovers

From 0.2.7 Kyle's Notes:

**Closed 2026-04-11.**

0.2.7 verified end-to-end on NZXTcos. Dashboard at http://127.0.0.1:7800/ renders all six sections with the correct trident palette and Geist typography. Component coverage matrix shows 76 ok / 0 missing / 88 total. Daemon health card visible. Recent traces showing live telegram heartbeats.

The dashboard did its job in the first 60 seconds of being open: it surfaced four real findings that no prior audit, test suite, or bundle review had caught. None of these are 0.2.7 defects — they are 0.2.7 wins, because the dashboard is exactly the diagnostic that made them visible. They become 0.2.8 inputs:

1. **MCP fleet utilization gap.** The 12 "unknown" components in the coverage matrix are the entire MCP fleet (rows 76-87). The verifier does not know how to ping MCP servers because no agent code has ever talked to one. This validates the broader concern: the MCP fleet has been installed since 0.2.3 and has not been used during a single agent execution across five iterations. Declared but not exercised. 0.2.8 makes MCP-first agent behavior a primary theme.

2. **components.yaml drift.** Still references mcp-server-github, mcp-server-google-drive, mcp-server-slack, and mcp-server-fetch — the four packages 0.2.4 W1 removed from bin/aho-mcp because they 404 or are deprecated. Two sources of truth that should agree have been silently drifting since 0.2.4. The dashboard surfaces the drift visually for the first time. Source-of-truth reconciliation lands in 0.2.8 W6/W7.

3. **harness-watcher daemon inactive.** Daemon health card shows red. The service was installed in 0.2.5 W5 and verified present in 0.2.6, but it is not currently running on NZXTcos. Root cause unknown — possibly bin/aho-systemd enables but does not start, possibly a crash. 0.2.8 W8 investigates and either fixes the installer, fixes the daemon, or removes the daemon if its purpose has been superseded.

4. **Bundle generator drops canonical artifacts.** Discovered during bundle review: §4 Report is hollow, §12 Sidecars says "(no sidecars)" despite W2 producing components-coverage.md and W5 producing orchestrator-config.md as explicit deliverables, and ADR-044 (the four-phase cadence ADR captured during 0.2.5 W0) does not appear in §6 despite existing on disk in artifacts/adrs/. Five real artifacts are missing from this iteration's permanent record. Fix lands in 0.2.8 W10/W11.

A fifth finding came from operational reality, not the dashboard: the Telegram bot @aho_run_bot is alive and receiving messages (delivery checkmarks visible) but it's send-only — no router consumes Telegram getUpdates and nothing bridges chat to openclaw's Unix socket. 0.2.8 W12 builds the inbound bridge so the harness can be operated from chat.

These findings vindicate ADR-044 Phase 2 (forensic bundle consumption) and extend it: the dashboard automates a chunk of Phase 2 by making state visible at a glance. ADR-044 will be updated in 0.2.8 W9 to reference the dashboard as Phase 2 tooling, not just a visibility nicety.

Pending only: git commit + push (Pillar 11). Recommend three small commits for 0.2.5, 0.2.6, 0.2.7 in sequence before firing 0.2.8, to give a clean revert point if 0.2.8's larger surface produces anything that needs to back out.

0.2.7 closes clean.

---

## Next Iteration Recommendation

- Address failed postflight gates: readme_current, manifest_current, artifacts_present, structural_gates, pillars_present, bundle_completeness, iteration_complete
