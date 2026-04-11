# Report — aho 0.2.2

**Generated:** 2026-04-11T16:09:57Z
**Iteration:** 0.2.2
**Phase:** 0
**Run type:** mixed
**Status:** unknown

---

## Executive Summary

This iteration executed 6 workstreams: 6 passed, 0 failed, 0 pending/partial.
582 events logged during execution.
Postflight: 13/15 gates passed, 0 failed.

---

## Workstream Detail

| Workstream | Status | Agent | Events | Wall Clock |
|---|---|---|---|---|
| W0 | pass | claude-code | 0 | - |
| W1 | pass | claude-code | 0 | - |
| W2 | pass | claude-code | 0 | - |
| W3 | pass | claude-code | 0 | - |
| W4 | pass | claude-code | 0 | - |
| W5 | pass | claude-code | 0 | - |

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
| component-manifest | python_module | active | soc-foundry | added 0.1.15 W1 |

**Total components:** 72
**Status breakdown:** 72 active

---

## Postflight Results

| Gate | Status | Message |
|---|---|---|
| app_build_check | ok | web build present (1502 bytes) |
| artifacts_present | ok | all 3 artifacts present (aho) |
| build_log_complete | ok | all 6 workstreams logged in manual file |
| bundle_quality | ok | Bundle valid (316 KB, run_type: mixed) |
| canonical_artifacts_current | ok | all 8 canonical artifacts at 0.2.2 |
| changelog_current | ok | CHANGELOG.md contains 0.2.2 |
| gemini_compat | ok | Gemini-primary CLI sync verified |
| iteration_complete | ok | Checkpoint: All workstreams reached final state
Build Log: Build log manual ground truth present
Secret Scan: No plaintext secrets found in tracked files
install.fish: install.fish syntax OK
Artifacts: All Qwen-generated artifacts present |
| manifest_current | ok | all 71 file hashes current |
| pillars_present | ok | Eleven pillars present in design and README |
| pipeline_present | ok | SKIP — no pipelines declared in .aho.json |
| readme_current | ok | README updated during this iteration (mtime: 2026-04-11T15:14:16.435041+00:00) |
| run_complete | deferred | Kyle's notes section not yet filled in |
| run_quality | ok | Run file passes quality gate |
| structural_gates | pass | Structural gates: 4 pass, 0 fail, 0 deferred |

---

## Risk Register

- **2026-04-11T15:15:56.399327+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T15:15:56.414926+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T15:15:56.419667+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T15:15:58.291968+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T15:15:58.292589+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T16:01:31.602093+00:00** [llm_call] missing credentials
- **2026-04-11T16:01:31.604963+00:00** [llm_call] connection refused
- **2026-04-11T16:05:04.207570+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:05:04.225587+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T16:05:04.231794+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:05:05.609563+00:00** [llm_call] missing credentials
- **2026-04-11T16:05:07.866606+00:00** [evaluator_run] severity=reject errors=1
- **2026-04-11T16:05:07.868094+00:00** [evaluator_run] severity=warn errors=1
- **2026-04-11T16:05:07.873591+00:00** [llm_call] missing credentials
- **2026-04-11T16:05:07.878683+00:00** [llm_call] connection refused
- **2026-04-11T16:05:56.999365+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:05:57.017280+00:00** [evaluator_run] severity=reject errors=40
- **2026-04-11T16:05:57.027622+00:00** [evaluator_run] severity=warn errors=2
- **2026-04-11T16:05:58.401683+00:00** [llm_call] missing credentials
- **2026-04-11T16:06:00.639052+00:00** [evaluator_run] severity=reject errors=1

---

## Carryovers

From 0.2.1 Kyle's Notes:

**Iteration 2 has its spine.** 0.2.1 landed everything that needed to land for the global deployment story to be real:

- Hybrid systemd model documented and operational
- Native OTEL collector (otelcol-contrib v0.149.0) running as systemd user service
- Always-on OTEL (no more opt-in gating)
- Real `bin/aho-install` and `bin/aho-uninstall` with idempotency contract
- All 4 Ollama models pre-pulled and verified
- 6 components emitting OTEL spans (qwen, nemotron, glm, openclaw, nemoclaw, telegram)
- 8 canonical artifacts now version-tracked
- soc-foundry/aho second commit live

**The deferral debt is still in components.yaml.** openclaw, nemoclaw, telegram are still `stub` with `next_iteration: 0.1.16` (stale — should have been bumped to 0.2.2 in 0.2.1 but missed). 0.2.2 is the run where they actually graduate from stub to active. The instrumentation pass in 0.2.1 W5 wired spans into them — now 0.2.2 makes them functional.

**Today's status:** ~7:35am PST. Three runs shipped this morning (0.1.15, 0.1.16 iteration 1 graduation, 0.2.1). Family time mid-afternoon. 6-11pm evening block available. P3 ship deadline = end of today. Alex ship deadline = Sunday. Fly Sunday.

**Phase 0 exit roadmap update (3 iterations + ship gauntlet):**
- **0.2.2** — openclaw/nemoclaw global daemons + telegram bridge real implementation + 3 stubs flip to active (today, ~2-3 hours)
- **0.2.3** — MCP server fleet (firebase-tools, context7, firecrawl, playwright, flutter, modelcontextprotocol/server-*) (today evening or tomorrow morning)
- **0.2.4** — P3 clone attempt + smoke test + capability gap capture (tomorrow)
- **0.2.5+** — Whatever P3 surfaces, fix in tight runs
- **Iteration 2 graduates** when P3 runs an aho iteration end-to-end
- **0.3.x** — Alex demo prep, claw3d, novice operability validation (Sunday SF prep)
- **Phase 0 graduates** when iteration 3 closes clean

**Event log audit clean.** The W6 smoke spans contain only `test prompt`, `hello`, `test task`, `print('hello')` — no credentials, no secrets, no API keys. Telemetry design records `input_summary` (truncated/shape) not full prompts, which is the right pattern. Confirmed safe.

**First commit history note.** `data/chroma/` and `data/aho_event_log.jsonl` exist in commit `ac0f66b` history but are gone from HEAD. ChromaDB binaries are noise. Event log is shape-only smoke data. No security action required. Future `git filter-repo` cleanup is a Phase 1 housekeeping item, not a Phase 0 blocker.

---

---

## Next Iteration Recommendation

- All workstreams passed and postflight gates green. Proceed to next iteration.
