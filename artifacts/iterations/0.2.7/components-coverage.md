# Components Coverage Matrix — 0.2.7 W2

**Iteration:** 0.2.7 | **Date:** 2026-04-11
**Total components:** 88 | **All files verified present**
**Audit result:** No gaps requiring install.fish changes. All components are installed through existing steps.

---

## Summary by kind

| Kind | Count | Install source | Verified |
|---|---|---|---|
| python_module | 59 | Step 3 (pip install aho package) | all ok |
| agent | 10 | Step 3 (pip) + Step 7 (systemd) for daemons | all ok |
| mcp_server | 12 | Step 6 (npm install) | all ok |
| external_service | 4 | Mixed (see detail) | all ok |
| llm | 3 | Step 3 (pip, client code) + Step 4 (model weights) | all ok |

---

## Install path mapping

### Step 1 — pacman (bin/aho-pacman install)
| Component | Kind | Notes |
|---|---|---|
| ollama | external_service | Installed via pacman or upstream script |

### Step 2 — AUR (bin/aho-aur install)
No components exclusively from AUR. age is installed here but is a tool, not a component.

### Step 3 — python (bin/aho-python install)
All 59 python_module entries, all 10 agent entries (source code), all 3 llm client entries, and these external_service entries:

| Component | Notes |
|---|---|
| chromadb | Installed via: pip transitive (chromadb is a dependency of the aho package) |
| opentelemetry | Installed via: pip explicit (opentelemetry-api, opentelemetry-sdk in pyproject.toml) |
| telegram | Source code installed via pip; daemon via Step 7 |

### Step 4 — models (bin/aho-models install)
| Component | Kind | Notes |
|---|---|---|
| qwen-client | llm | Client code via Step 3; model weights (qwen3.5:9b) pulled by ollama |
| nemotron-client | llm | Client code via Step 3; model weights (nemotron-mini:4b) pulled by ollama |
| glm-client | llm | Client code via Step 3; model weights pulled by ollama |

### Step 5 — secrets (bin/aho-secrets-init)
No components directly installed. Secrets infrastructure (age key, fernet store) is tooling, not a component.

### Step 6 — mcp (bin/aho-mcp install)
| Component | Package | Status |
|---|---|---|
| mcp-firebase-tools | firebase-tools | ok |
| mcp-context7 | @upstash/context7-mcp | ok |
| mcp-firecrawl | firecrawl-mcp | ok |
| mcp-playwright | @playwright/mcp | ok |
| mcp-flutter | flutter-mcp | ok |
| mcp-server-filesystem | @modelcontextprotocol/server-filesystem | ok |
| mcp-server-github | @modelcontextprotocol/server-github | ok |
| mcp-server-google-drive | @modelcontextprotocol/server-google-drive | ok |
| mcp-server-slack | @modelcontextprotocol/server-slack | ok |
| mcp-server-fetch | @modelcontextprotocol/server-fetch | ok |
| mcp-server-memory | @modelcontextprotocol/server-memory | ok |
| mcp-server-sequential-thinking | @modelcontextprotocol/server-sequential-thinking | ok |

### Step 7 — systemd (bin/aho-systemd install)
| Component | Service unit | Notes |
|---|---|---|
| openclaw | aho-openclaw.service | Daemon service file |
| nemoclaw | aho-nemoclaw.service | Daemon service file |
| telegram | aho-telegram.service | Daemon service file |
| harness-agent | aho-harness-watcher.service | Daemon service file |

### Step 8 — symlinks
No components. Bin wrapper symlinks only.

### Step 9 — doctor
No components. Verification only.

---

## Documented gaps (not defects)

| Component | Gap description | Resolution |
|---|---|---|
| chromadb | No explicit install.fish step; installed as pip transitive dep | Documented: installed via pip transitive. Fragility: low (chromadb is a direct dependency in pyproject.toml dependencies or transitive) |
| opentelemetry | No separate install step | Documented: explicitly declared in pyproject.toml (opentelemetry-api>=1.25, opentelemetry-sdk>=1.25). Not a gap. |
| brave-integration | Module exists but no API key configured | Addressed by W5 (orchestrator.json + bin/aho-secrets-init --add-brave-token). Not an install.fish gap. |

---

## Component detail table (all 88)

| # | Name | Kind | Path | Install source | Verified |
|---|---|---|---|---|---|
| 1 | openclaw | agent | src/aho/agents/openclaw.py | Step 3 + Step 7 | ok |
| 2 | nemoclaw | agent | src/aho/agents/nemoclaw.py | Step 3 + Step 7 | ok |
| 3 | telegram | external_service | src/aho/telegram/notifications.py | Step 3 + Step 7 | ok |
| 4 | qwen-client | llm | src/aho/artifacts/qwen_client.py | Step 3 + Step 4 | ok |
| 5 | nemotron-client | llm | src/aho/artifacts/nemotron_client.py | Step 3 + Step 4 | ok |
| 6 | glm-client | llm | src/aho/artifacts/glm_client.py | Step 3 + Step 4 | ok |
| 7 | chromadb | external_service | src/aho/rag/archive.py | Step 3 (pip transitive) | ok |
| 8 | ollama | external_service | src/aho/ollama_config.py | Step 1 (pacman) | ok |
| 9 | opentelemetry | external_service | src/aho/logger.py | Step 3 (pip explicit) | ok |
| 10 | assistant-role | agent | src/aho/agents/roles/assistant.py | Step 3 | ok |
| 11 | base-role | agent | src/aho/agents/roles/base_role.py | Step 3 | ok |
| 12 | code-runner-role | agent | src/aho/agents/roles/code_runner.py | Step 3 | ok |
| 13 | reviewer-role | agent | src/aho/agents/roles/reviewer.py | Step 3 | ok |
| 14 | cli | python_module | src/aho/cli.py | Step 3 | ok |
| 15 | config | python_module | src/aho/config.py | Step 3 | ok |
| 16 | doctor | python_module | src/aho/doctor.py | Step 3 | ok |
| 17 | logger | python_module | src/aho/logger.py | Step 3 | ok |
| 18 | paths | python_module | src/aho/paths.py | Step 3 | ok |
| 19 | harness | python_module | src/aho/harness.py | Step 3 | ok |
| 20 | compatibility | python_module | src/aho/compatibility.py | Step 3 | ok |
| 21 | push | python_module | src/aho/push.py | Step 3 | ok |
| 22 | registry | python_module | src/aho/registry.py | Step 3 | ok |
| 23 | ollama-config | python_module | src/aho/ollama_config.py | Step 3 | ok |
| 24 | artifact-loop | python_module | src/aho/artifacts/loop.py | Step 3 | ok |
| 25 | artifact-context | python_module | src/aho/artifacts/context.py | Step 3 | ok |
| 26 | artifact-evaluator | python_module | src/aho/artifacts/evaluator.py | Step 3 | ok |
| 27 | artifact-schemas | python_module | src/aho/artifacts/schemas.py | Step 3 | ok |
| 28 | artifact-templates | python_module | src/aho/artifacts/templates.py | Step 3 | ok |
| 29 | repetition-detector | python_module | src/aho/artifacts/repetition_detector.py | Step 3 | ok |
| 30 | bundle | python_module | src/aho/bundle/__init__.py | Step 3 | ok |
| 31 | components-section | python_module | src/aho/bundle/components_section.py | Step 3 | ok |
| 32 | report-builder | python_module | src/aho/feedback/report_builder.py | Step 3 | ok |
| 33 | feedback-run | python_module | src/aho/feedback/run.py | Step 3 | ok |
| 34 | feedback-prompt | python_module | src/aho/feedback/prompt.py | Step 3 | ok |
| 35 | feedback-questions | python_module | src/aho/feedback/questions.py | Step 3 | ok |
| 36 | feedback-summary | python_module | src/aho/feedback/summary.py | Step 3 | ok |
| 37 | feedback-seed | python_module | src/aho/feedback/seed.py | Step 3 | ok |
| 38 | build-log-stub | python_module | src/aho/feedback/build_log_stub.py | Step 3 | ok |
| 39 | pipeline-scaffold | python_module | src/aho/pipelines/scaffold.py | Step 3 | ok |
| 40 | pipeline-validate | python_module | src/aho/pipelines/validate.py | Step 3 | ok |
| 41 | pipeline-registry | python_module | src/aho/pipelines/registry.py | Step 3 | ok |
| 42 | pipeline-pattern | python_module | src/aho/pipelines/pattern.py | Step 3 | ok |
| 43 | pf-artifacts-present | python_module | src/aho/postflight/artifacts_present.py | Step 3 | ok |
| 44 | pf-build-log-complete | python_module | src/aho/postflight/build_log_complete.py | Step 3 | ok |
| 45 | pf-bundle-quality | python_module | src/aho/postflight/bundle_quality.py | Step 3 | ok |
| 46 | pf-gemini-compat | python_module | src/aho/postflight/gemini_compat.py | Step 3 | ok |
| 47 | pf-iteration-complete | python_module | src/aho/postflight/iteration_complete.py | Step 3 | ok |
| 48 | pf-layout | python_module | src/aho/postflight/layout.py | Step 3 | ok |
| 49 | pf-manifest-current | python_module | src/aho/postflight/manifest_current.py | Step 3 | ok |
| 50 | pf-changelog-current | python_module | src/aho/postflight/changelog_current.py | Step 3 | ok |
| 51 | pf-pillars-present | python_module | src/aho/postflight/pillars_present.py | Step 3 | ok |
| 52 | pf-pipeline-present | python_module | src/aho/postflight/pipeline_present.py | Step 3 | ok |
| 53 | pf-readme-current | python_module | src/aho/postflight/readme_current.py | Step 3 | ok |
| 54 | pf-run-complete | python_module | src/aho/postflight/run_complete.py | Step 3 | ok |
| 55 | pf-run-quality | python_module | src/aho/postflight/run_quality.py | Step 3 | ok |
| 56 | pf-structural-gates | python_module | src/aho/postflight/structural_gates.py | Step 3 | ok |
| 57 | preflight-checks | python_module | src/aho/preflight/checks.py | Step 3 | ok |
| 58 | rag-archive | python_module | src/aho/rag/archive.py | Step 3 | ok |
| 59 | rag-query | python_module | src/aho/rag/query.py | Step 3 | ok |
| 60 | rag-router | python_module | src/aho/rag/router.py | Step 3 | ok |
| 61 | secrets-store | python_module | src/aho/secrets/store.py | Step 3 | ok |
| 62 | secrets-session | python_module | src/aho/secrets/session.py | Step 3 | ok |
| 63 | secrets-cli | python_module | src/aho/secrets/cli.py | Step 3 | ok |
| 64 | secrets-backend-age | python_module | src/aho/secrets/backends/age.py | Step 3 | ok |
| 65 | secrets-backend-base | python_module | src/aho/secrets/backends/base.py | Step 3 | ok |
| 66 | secrets-backend-fernet | python_module | src/aho/secrets/backends/fernet.py | Step 3 | ok |
| 67 | secrets-backend-keyring | python_module | src/aho/secrets/backends/keyring_linux.py | Step 3 | ok |
| 68 | install-migrate-config | python_module | src/aho/install/migrate_config_fish.py | Step 3 | ok |
| 69 | install-secret-patterns | python_module | src/aho/install/secret_patterns.py | Step 3 | ok |
| 70 | brave-integration | python_module | src/aho/integrations/brave.py | Step 3 (code), W5 (config) | ok |
| 71 | firestore | python_module | src/aho/data/firestore.py | Step 3 | ok |
| 72 | workstream-agent | agent | src/aho/agents/roles/workstream_agent.py | Step 3 | ok |
| 73 | evaluator-agent | agent | src/aho/agents/roles/evaluator_agent.py | Step 3 | ok |
| 74 | harness-agent | agent | src/aho/agents/roles/harness_agent.py | Step 3 + Step 7 | ok |
| 75 | conductor | agent | src/aho/agents/conductor.py | Step 3 | ok |
| 76 | mcp-firebase-tools | mcp_server | firebase-tools | Step 6 | ok |
| 77 | mcp-context7 | mcp_server | @upstash/context7-mcp | Step 6 | ok |
| 78 | mcp-firecrawl | mcp_server | firecrawl-mcp | Step 6 | ok |
| 79 | mcp-playwright | mcp_server | @playwright/mcp | Step 6 | ok |
| 80 | mcp-flutter | mcp_server | flutter-mcp | Step 6 | ok |
| 81 | mcp-server-filesystem | mcp_server | @modelcontextprotocol/server-filesystem | Step 6 | ok |
| 82 | mcp-server-github | mcp_server | @modelcontextprotocol/server-github | Step 6 | ok |
| 83 | mcp-server-google-drive | mcp_server | @modelcontextprotocol/server-google-drive | Step 6 | ok |
| 84 | mcp-server-slack | mcp_server | @modelcontextprotocol/server-slack | Step 6 | ok |
| 85 | mcp-server-fetch | mcp_server | @modelcontextprotocol/server-fetch | Step 6 | ok |
| 86 | mcp-server-memory | mcp_server | @modelcontextprotocol/server-memory | Step 6 | ok |
| 87 | mcp-server-sequential-thinking | mcp_server | @modelcontextprotocol/server-sequential-thinking | Step 6 | ok |
| 88 | component-manifest | python_module | src/aho/components/manifest.py | Step 3 | ok |
