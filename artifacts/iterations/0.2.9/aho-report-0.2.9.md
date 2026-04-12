# Report — aho 0.2.9

**Generated:** 2026-04-12T04:43:34Z
**Iteration:** 0.2.9
**Phase:** 0
**Run type:** single-agent
**Status:** active

---

## Executive Summary

This iteration executed 10 workstreams: 10 passed, 0 failed, 0 pending/partial.
47 events logged during execution.
Postflight: 8/18 gates passed, 7 failed.

---

## Workstream Detail

| Workstream | Status | Agent | Events | Wall Clock |
|---|---|---|---|---|
| W0 | pass | claude-code | 1 | - |
| W1 | pass | claude-code | 1 | - |
| W2 | pass | claude-code | 1 | - |
| W3 | pass | claude-code | 1 | - |
| W4 | pass | claude-code | 1 | - |
| W5 | pass | claude-code | 1 | - |
| W6 | pass | claude-code | 1 | - |
| W7 | pass | claude-code | 1 | - |
| W8 | pass | claude-code | 1 | - |
| W8.5 | pass | claude-code | 1 | - |

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
| artifacts_present | fail | report_artifact missing, bundle_artifact missing |
| build_log_complete | ok | no workstreams found in design |
| bundle_completeness | skip | bundle not yet generated for 0.2.9 |
| bundle_quality | warn | Bundle not yet generated: aho-bundle-0.2.9.md |
| canonical_artifacts_current | ok | all 10 canonical artifacts at 0.2.9 |
| changelog_current | ok | CHANGELOG.md contains 0.2.9 |
| gemini_compat | ok | Gemini-primary CLI sync verified |
| iteration_complete | fail | Checkpoint: All workstreams reached final state
Build Log: Build log manual ground truth present
Secret Scan: No plaintext secrets found in tracked files
install.fish: install.fish syntax OK
Artifacts: Missing artifacts: report.md, bundle.md |
| manifest_current | fail | stale hashes: .aho-checkpoint.json, .aho.json, .gitignore |
| mcp_canonical_registry_verify | ok | all 9 MCP packages registry-verified |
| mcp_sources_aligned | ok | MCP sources aligned: 9 entries match |
| pillars_present | fail | 3 errors: Design doc missing Pillar 10; Design doc missing Pillar 11; Design doc missing §3 (Trident) |
| pipeline_present | ok | SKIP — no pipelines declared in .aho.json |
| readme_current | fail | README.md last modified 2026-04-12T04:43:22.776237+00:00 < iteration start 2026-04-12T05:00:00Z |
| run_complete | deferred | Sign-off incomplete: Kyle reviewed and approved |
| run_quality | fail | 1 quality check failures |
| structural_gates | fail | Structural gates: 2 pass, 1 fail, 1 deferred |

---

## Risk Register

- **2026-04-12T04:41:24.171553+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T04:41:24.187744+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-12T04:41:24.192734+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-12T04:41:25.553428+00:00** [llm_call] missing credentials
- **2026-04-12T04:41:45.103824+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-12T04:41:45.104465+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-12T04:41:45.114458+00:00** [llm_call] missing credentials
- **2026-04-12T04:41:45.117240+00:00** [llm_call] connection refused

---

## Carryovers

From 0.2.8 Kyle's Notes:

**Kyle's Notes (closed 2026-04-11):**

0.2.8 is the largest aho iteration to date and the most structurally
consequential. Five real discoveries landed as shipped fixes:

1. MCP utilization gap closed. Zero MCP invocations across iterations
   0.2.3 through 0.2.7; 14 distinct invocations across 4 workstreams
   in 0.2.8 alone (W3, W5, W10, W12). The MCP-first mandate is no
   longer aspirational.

2. Source-of-truth drift resolved. components.yaml and bin/aho-mcp
   agree for the first time since 0.2.4 (9 servers, 8 npm + 1 dart
   SDK-bundled). New postflight gate mcp_sources_aligned prevents
   recurrence.

3. harness-watcher daemon active. Root cause was Branch A installer
   bug — bin/aho-systemd enabled but did not start. One-line fix.

4. Bundle generator fixed. §4 Report no longer hollow, §12 Sidecars
   populated (4 entries), §6 includes iteration-window ADRs. New
   postflight gate bundle_completeness caught both missing files
   on first run and forced W13 to generate them.

5. Telegram inbound bridge live. /status returns live doctor output
   to Kyle's phone. Single-user allow-list, 30s sync wait with async
   ack fallback. First daemon to operate the harness from off-keyboard.

Four new gotchas form a coherent family — a pattern language for
"things that pretend to work but don't":
- aho-G066: declared != exercised
- aho-G067: declared != populated
- aho-G068: installed != wired
- aho-G069: enabled != started

Every Phase 0 graduation criterion can now be checked against this
family. Running through the seven questions (declared? exercised?
populated? installed? wired? enabled? started?) is how P3 clone-to-
deploy validation catches gaps before they ship.

ADR-044 updated with Phase 2 Tooling: Dashboard section using
concrete 0.2.7-0.2.8 examples (12 unknowns flipped, 4 real catches
on first gate runs).

Per-workstream review cadence worked. W1's wiring gap surfaced in 4
minutes. W7's server-everything drift caught on first gate run. Both
would have shipped invisible under per-iteration review. Front-loaded
review intensity (heavy W1-W5, light W6-W13) matched the information
density curve. Worth formalizing as a sub-mode in ADR-045 (scheduled
for 0.2.9 W7).

Openclaw surfaced real stability issues during W12 telegram dispatch
testing: Errno 11 resource unavailable, thinking repetition false
positives, Errno 104 connection reset. These are carried to 0.2.10
as a dedicated iteration theme, not bolted onto 0.2.9.

Firecrawl key resolution used option A (fernet + shell env export)
which turned out cleaner than option B. The server inherits the key
from shell environment regardless of what .mcp.json says. .mcp.json
safely committed with empty string.

0.2.8 closes clean. Next: 0.2.9 workstream streaming + P3 clone
plumbing, 0.2.10 P3 hardening + openclaw reliability, 0.2.11 remote
agent executor + Phase 0 graduation.

---

## Next Iteration Recommendation

- Address failed postflight gates: readme_current, manifest_current, artifacts_present, structural_gates, pillars_present, run_quality, iteration_complete
