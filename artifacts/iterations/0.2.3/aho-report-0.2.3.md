# Report — aho 0.2.3

**Generated:** 2026-04-11T16:53:47Z
**Iteration:** 0.2.3
**Phase:** 0
**Run type:** mixed
**Status:** active

---

## Executive Summary

This iteration executed 6 workstreams: 5 passed, 0 failed, 1 pending/partial.
375 events logged during execution.
Postflight: 9/15 gates passed, 4 failed.

---

## Workstream Detail

| Workstream | Status | Agent | Events | Wall Clock |
|---|---|---|---|---|
| W0 | pass | claude-code | 0 | - |
| W1 | pass | claude-code | 0 | - |
| W2 | pass | claude-code | 0 | - |
| W3 | pass | claude-code | 0 | - |
| W4 | pass | claude-code | 0 | - |
| W5 | pending | claude-code | 0 | - |

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
| mcp-flutter | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-filesystem | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-github | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-google-drive | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-slack | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-fetch | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-memory | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| mcp-server-sequential-thinking | mcp_server | active | soc-foundry | npm global, activated 0.2.3 W1 |
| component-manifest | python_module | active | soc-foundry | added 0.1.15 W1 |

**Total components:** 88
**Status breakdown:** 88 active

---

## Postflight Results

| Gate | Status | Message |
|---|---|---|
| app_build_check | ok | web build present (1502 bytes) |
| artifacts_present | fail | report_artifact missing |
| build_log_complete | ok | all 6 workstreams logged in manual file |
| bundle_quality | ok | Bundle valid (392 KB, run_type: mixed) |
| canonical_artifacts_current | ok | all 10 canonical artifacts at 0.2.3 |
| changelog_current | ok | CHANGELOG.md contains 0.2.3 |
| gemini_compat | ok | Gemini-primary CLI sync verified |
| iteration_complete | fail | Checkpoint: Incomplete workstreams: W5(pending)
Build Log: Build log manual ground truth present
Secret Scan: No plaintext secrets found in tracked files
install.fish: install.fish syntax OK
Artifacts: Missing artifacts: report.md |
| manifest_current | fail | stale hashes: .aho-checkpoint.json, .aho.json, .gitignore |
| pillars_present | ok | Eleven pillars present in design and README |
| pipeline_present | ok | SKIP — no pipelines declared in .aho.json |
| readme_current | fail | README.md last modified 2026-04-11T16:36:30.733527+00:00 < iteration start 2026-04-11T17:00:00Z |
| run_complete | deferred | Sign-off incomplete: Manual conductor smoke test (7-span trace), Kyle git commit + push |
| run_quality | ok | Run file passes quality gate |
| structural_gates | pass | Structural gates: 3 pass, 0 fail, 1 deferred |

---

## Risk Register

- **2026-04-11T16:36:59.376328+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:36:59.391656+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T16:36:59.396445+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:37:00.801595+00:00** [llm_call] missing credentials
- **2026-04-11T16:37:02.687003+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T16:37:02.687602+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T16:37:02.690204+00:00** [llm_call] missing credentials
- **2026-04-11T16:37:02.693258+00:00** [llm_call] connection refused
- **2026-04-11T16:39:06.346633+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:39:06.362204+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T16:39:06.366930+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:39:07.757285+00:00** [llm_call] missing credentials
- **2026-04-11T16:39:09.592715+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T16:39:09.593299+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T16:39:09.595832+00:00** [llm_call] missing credentials
- **2026-04-11T16:39:09.598466+00:00** [llm_call] connection refused
- **2026-04-11T16:42:21.646300+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:42:21.667635+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T16:42:21.672633+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:42:42.411721+00:00** [evaluator_run] severity=warn errors=2

---

## Carryovers

From 0.2.2 Kyle's Notes:

Deferral debt cleared. 0 stubs. Iteration 2 mid-flight.

Locked decisions for 0.2.3+:
- 3-agent role split: Qwen=workstream, GLM=evaluator, Nemotron=harness watcher. Claude/Gemini demoted to conductor.
- Harness-as-IQ thesis confirmed: bigger harness = smarter local components.
- Localhost-by-default: NZXTcos=7800, P3=7900, never bind 0.0.0.0 in Phase 0.
- Per-clone age keys (regenerated per machine, never transferred).
- claw3d = LEGO bricks in virtual office, Three.js, deferred to 0.2.6 for Alex demo.
- Bundle §24-§26 expansion (Infrastructure, Harnesses, Configuration).
- Public host on aho.run via Caddy = Phase 1 only.

Phase 0 exit: 0.2.3 (role split + MCP + plumbing) → 0.2.4 (P3 clone) → 0.2.5 (P3 fixes) → 0.2.6 (claw3d for Alex) → graduate.

5 hygiene carryovers folded into 0.2.3 W0.

Sign-off: [x] all five.


---

---

## Next Iteration Recommendation

- Address failed postflight gates: readme_current, manifest_current, artifacts_present, iteration_complete
