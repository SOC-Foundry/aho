# aho changelog

## [0.2.10] — 2026-04-12

**Theme:** Install surface implementation + CLI unification + observability deployment

- Unified `aho` CLI: run, mcp, install, update, dashboard, models, openclaw, otel, bootstrap subcommands
- `_dispatch_wrapper()` bridges `aho <sub>` → `bin/aho-*` fish scripts; old wrappers kept as implementations
- `bin/aho-install` populates `~/.local/share/aho/` with harness, registries, agents, bin, secrets, runtime
- Agent instruction split: CLAUDE-iteration.md + CLAUDE-run.md, GEMINI-iteration.md + GEMINI-run.md (persona 1 vs persona 3)
- OpenClaw socket relocated from `~/.local/share/aho/` to `/run/user/$UID/openclaw.sock` (XDG_RUNTIME_DIR)
- OpenClaw file bridge: `run` command reads CWD files, routes to model per Q1 decision, writes output to `$CWD/aho-output/`
- `aho run "task"` end-to-end: dispatch to OpenClaw socket, persona 3 agent instructions, structured output
- otelcol-contrib v0.149.0 (direct binary, predates 0.2.10) + Jaeger v1.62.0 (direct binary) as systemd user services
- Dashboard promoted from ad-hoc to systemd user service, install completeness section in /api/state
- MANIFEST live-refresh daemon: 5s debounced regeneration on harness/registry changes
- `aho doctor --deep`: flutter doctor -v + dart --version SDK integration checks
- `aho components check`: per-kind presence verification (85/85 on NZXTcos)
- OpenClaw stability: Errno 11 retry, repetition detector (30% threshold), Errno 104 catch
- Postflight gate fixes: readme_current timezone, bundle_quality §22 flexible format, manifest_current self-referential skip
- 6 systemd user services active: openclaw, telegram, harness-watcher, otel-collector, jaeger, dashboard
- AUR install path deferred to 0.2.11 (CachyOS mirror PGP issue + Jaeger-bin AUR rename)
- 227 tests (maintained from 0.2.9), 17 workstreams, W3/W5/W9/W10 re-executed after drift verification

## [0.2.9] — 2026-04-11

**Theme:** Remote operability plumbing + persona 3 discovery + install surface architecture

- `.mcp.json.tpl` template with `{{PROJECT_ROOT}}` placeholder; `bin/aho-bootstrap` generates per-machine `.mcp.json` at step 4
- `.mcp.json` gitignored (machine-specific generated artifact)
- Bootstrap npm list corrected from stale 11-package to current 8-package (9th is dart SDK-bundled)
- Portability audit: 3 hardcoded paths fixed (smoke script, mcp-wiring.md, global-deployment.md), zero hardcodes remain in executable code
- `src/aho/workstream_events.py` — `emit_workstream_start()` / `emit_workstream_complete()` with idempotent guards
- CLI: `aho iteration workstream {start,complete}` subcommands
- Telegram `/ws` command family: `/ws status`, `/ws pause`, `/ws proceed`, `/ws last`
- Auto-push subscriber: tails event log, sends Telegram notification on `workstream_complete`
- `src/aho/workstream_gate.py` — `wait_if_paused()` polls checkpoint for `proceed_awaited` flag at workstream boundaries
- `artifacts/harness/secrets-architecture.md` — three-layer model (age + keyring + fernet), junior-dev-readable
- ADR-045: Discovery iteration formalization — three-type taxonomy (remediation/feature/discovery), per-workstream review sub-mode
- Persona 3 validation: no entry point exists, chat/execute disconnected, 4/4 test tasks failed — structural gap documented
- `artifacts/iterations/0.2.9/install-surface-architecture.md` — three-persona taxonomy, aho-run dispatch spec, 4 Kyle decisions, 0.2.10 scope contract
- Updated roadmap: 0.2.10 install surface → 0.2.11 persona 3 validation → 0.2.12 persona 2 → 0.2.13 P3 clone graduation
- 227 tests (up from 182), 10 workstreams (W8.5 inserted per ADR-045 discovery pattern)

## [0.2.8] — 2026-04-11

**Theme:** Discovery + exercise — MCP utilization, source-of-truth reconciliation, harness-watcher diagnosis, bundle completeness, telegram inbound bridge

- MCP-first mandate: CLAUDE.md + GEMINI.md gain MUST-strength MCP Toolchain section, [INSTALLED-NOT-WIRED] tag convention
- Project `.mcp.json` wires 9 MCP servers as Claude Code tool connections (8 npm + 1 SDK-bundled dart)
- `bin/aho-mcp smoke` — 9 per-server CLI smoke scripts + aggregator producing `data/mcp_readiness.json`
- Dashboard MCP verifier: aggregator reads smoke results, 85 ok / 0 missing / 0 unknown (zero unknowns for first time)
- components.yaml reconciled: 4 dead entries removed, flutter-mcp replaced with dart mcp-server, server-everything added. 88 → 85 components
- `mcp_sources_aligned` postflight gate: diffs components.yaml against bin/aho-mcp, caught server-everything gap on first run
- `bundle_completeness` postflight gate: three-category check (sidecar drift, canonical missing, ADR coverage)
- harness-watcher diagnosis: Branch A (enable-not-start), fixed in bin/aho-systemd, daemon running
- 4 new gotchas: G066 (declared ≠ exercised), G067 (declared ≠ populated), G068 (installed ≠ wired), G069 (enabled ≠ started)
- ADR-044 updated: Phase 2 Tooling section with dashboard as forensic consumption accelerator
- Bundle generator: §6 walks artifacts/adrs/, §12 walks iteration dir for sidecars
- Telegram inbound bridge: getUpdates polling, /status /iteration /last + free-text→openclaw, verified live on phone
- 182 tests (up from 158), 14 workstreams (largest iteration), MCP fleet smoke 9/9 pass

## [0.2.7] — 2026-04-11

**Theme:** Visibility + carry-forward closeout — dashboard, coverage audit, orchestrator config

- `src/aho/dashboard/` — new Python module: aggregator + HTTP server for localhost dashboard
- `bin/aho-dashboard` rewritten to serve `/api/state` (aggregated JSON) and `/` (Flutter app)
- `/api/state` endpoint aggregates system, component, daemon, trace, MCP, and model state with 2s cache
- Flutter Web dashboard at `web/claw3d/` — 6 sections: banner, component matrix, daemon health, traces, MCP fleet, model fleet
- Trident palette (#0D9488 shaft, #161B22 background, #4ADE80 accent), monospace typography, 5s polling
- `components-coverage.md` — 88 components audited, all mapped to install.fish steps, zero gaps
- `~/.config/aho/orchestrator.json` — engine (reserved), search provider, openclaw/nemoclaw model config
- `bin/aho-secrets-init --add-brave-token` — interactive prompt, fernet-encrypted storage
- openclaw and nemoclaw read model defaults from orchestrator.json, fallback to hardcoded
- `set_attrs_from_dict()` helper in logger.py — recursive OTEL span attribute flattening (aho-G064 final fix)
- 158 tests passing (up from 143)

## [0.2.6] — 2026-04-11

**Theme:** install.fish live-fire hardening — pacman, secrets, telegram doctor

- Removed ollama from `pacman-packages.txt` — installed via upstream script, CachyOS pacman package corrupt + conflicts with `/usr/share/ollama`
- `bin/aho-pacman`: added `_pkg_present` fallback that checks `command -q` for upstream-installed packages
- `bin/aho-secrets-init`: rewritten to check fernet secrets store + telegram daemon instead of bogus `.age` file scaffold
- `aho doctor preflight`: telegram check now shows `@aho_run_bot` via cached `getMe` API response
- Telegram daemon writes bot identity to `~/.local/state/aho/telegram_bot.json` on startup
- install.fish completes all 9 steps clean on NZXTcos, second run fully idempotent

## [0.2.5] — 2026-04-11

**Theme:** Clone-to-deploy install.fish + 0.2.3 carry-forward hardening

- `install.fish` rewritten as thin 9-step orchestrator with resume support via `install.state`
- 6 new bin wrappers: `aho-pacman`, `aho-aur`, `aho-models`, `aho-secrets-init`, `aho-systemd`, `aho-python`
- 3 declarative lists: `pacman-packages.txt` (15 packages), `aur-packages.txt` (empty), `model-fleet.txt` (4 models)
- `bin/aho-install` renamed to `bin/aho-bootstrap` — install.fish is now the top-level entry point
- `bin/aho-secrets-init`: age keygen + keyring bootstrap + telegram scaffold with capability gap halt
- `bin/aho-systemd install` deploys all 4 user daemons including `aho-harness-watcher.service` (0.2.3 W3 fix)
- OTEL `aho.tokens` dict→scalar flatten — no more `Invalid type dict` errors (aho-G064)
- Evaluator score parser: scale detection (0-1 → 0-10), preserves `raw_score` and `raw_recommendation`
- `bin/aho-conductor smoke`: verifiable smoke test with file marker + event log span assertion (aho-G065)
- 2 new gotchas: aho-G064, aho-G065. Registry at 19 entries
- 143 tests pass (was 137)

## [0.2.4] — 2026-04-11

**Theme:** W1 remediation — canonical MCP list correction + verification harness

- MCP fleet corrected from 12 to 9 registry-verified packages
- Removed: server-github (moved to Go binary), server-google-drive (archived), server-slack (deprecated), server-fetch (Python-only)
- Added: server-everything (reference/test server)
- `bin/aho-mcp` fish scoping fix: `set -l` → `set -g` for script-level constants (aho-G062)
- `bin/aho-mcp doctor` gains registry verification pass via `npm view`
- New postflight gate: `mcp_canonical_registry_verify` — fails on 404 or deprecation
- New e2e CLI test: `tests/integration/test_aho_mcp_cli_e2e.fish`
- 2 new gotchas: aho-G062 (fish set -l scoping), aho-G063 (canonical list registry verification)
- Gotcha registry at 17 entries
- `mcp-fleet.md` updated to 9-server catalog with removal rationale
- 10 canonical artifacts at 0.2.4
- 137 tests passing

## [0.2.3] — 2026-04-11

**Theme:** Three-agent role split + MCP fleet + dashboard plumbing

- Three-agent role split: WorkstreamAgent (Qwen), EvaluatorAgent (GLM), HarnessAgent (Nemotron) at `src/aho/agents/roles/`
- Conductor orchestrator: dispatch → nemoclaw.route → workstream → evaluator → telegram
- 12 MCP servers as global npm components with `bin/aho-mcp` manager (list/status/doctor/install)
- `aho-harness-watcher.service` — 4th systemd user daemon, long-lived event log watcher
- Localhost dashboard plumbing: dashboard_port=7800, aho_role field, heartbeat emission (30s intervals)
- `artifacts/harness/dashboard-contract.md` — canonical artifact #9 (heartbeat schema, health states)
- `artifacts/harness/mcp-fleet.md` — canonical artifact #10 (12-server fleet spec)
- `web/claw3d/index.html` placeholder (real implementation in 0.2.6)
- `bin/aho-dashboard` skeleton (127.0.0.1:7800, traces.jsonl tail as JSON)
- Bundle expanded with §24 Infrastructure, §25 Harnesses, §26 Configuration
- Per-clone age keygen in `bin/aho-install` with [CAPABILITY GAP] halt
- Doctor: `_check_age_key()`, `_check_dashboard_port()`, `_check_role_agents()`, `_check_mcp_fleet()`
- `src/aho/config.py`: get_dashboard_port(), get_aho_role(), check_port_available()
- 88 components (12 MCP servers, 4 new agents), 0 stubs
- 10 canonical artifacts at 0.2.3
- 137 tests passing (29 new)

## [0.2.2] — 2026-04-11

**Theme:** Global daemons — openclaw, nemoclaw, telegram graduate from stub to active

- OpenClaw global daemon: `--serve` mode with Unix socket, session pool (5 max), JSON protocol, systemd user service `aho-openclaw.service`, `bin/aho-openclaw` wrapper
- NemoClaw global daemon: `--serve` mode with Unix socket, Nemotron routing + OpenClaw session pool, systemd user service `aho-nemoclaw.service`, `bin/aho-nemoclaw` wrapper
- Telegram bridge: real send-only implementation with project-scoped age-encrypted secrets, 429 retry, capability gap/close-complete notifications, systemd user service `aho-telegram.service`, `bin/aho-telegram` wrapper
- Doctor: 3 new daemon health checks (aho-openclaw, aho-nemoclaw, aho-telegram)
- `bin/aho-install`: auto-installs systemd unit files from templates/systemd/
- End-to-end trace: nemoclaw.dispatch → nemoclaw.route → openclaw.chat → qwen.generate → telegram.send
- 0 stubs remaining in components.yaml (was 3). Deferral debt cleared since iao 0.1.4.
- `report_builder.py`: wall clock per-workstream from event log timestamps
- `build_log_complete.py`: multi-candidate design path resolution
- `evaluator.py`: AHO_EVAL_DEBUG logging for warn/reject loop investigation
- 108 tests passing (21 new: 7 openclaw, 6 nemoclaw, 8 telegram)

## [0.2.1] — 2026-04-11

**Theme:** Global deployment architecture + native OTEL collector + model fleet pre-pull

- Global deployment architecture (`global-deployment.md`) — hybrid systemd model, install paths, lifecycle, capability gaps, uninstall contract, idempotency contract
- Real `bin/aho-install` — idempotent fish installer with platform check, XDG dirs, pip install, linger verification
- `bin/aho-uninstall` — clean removal with safety contract (never touches data/artifacts/git)
- Native OTEL collector as systemd user service (`aho-otel-collector.service`, otelcol-contrib v0.149.0)
- OTEL always-on by default — opt-out via `AHO_OTEL_DISABLED=1` (was opt-in `AHO_OTEL_ENABLED=1`)
- OTEL spans in 6 components: qwen-client, nemotron-client, glm-client, openclaw, nemoclaw, telegram
- `bin/aho-models-status` — Ollama fleet status wrapper
- `bin/aho-otel-status` — collector service + trace status
- Doctor: install_scripts, linger, model_fleet (4 models), otel_collector checks added
- `build_log_complete.py` design path fix using `get_artifacts_root()`
- 8 canonical artifacts (added global-deployment.md)
- 87 tests passing (7 new OTEL instrumentation tests)

## [0.1.16] — 2026-04-11

**Theme:** Close sequence repair + iteration 1 graduation

- Close sequence refactored: tests → bundle → report → run file → postflight → .aho.json → checkpoint
- Canonical artifacts gate (`canonical_artifacts_current.py`) — 7 versioned artifacts checked at close
- Run file wired through report_builder for agent attribution and component activity section
- `aho_json.py` helper for `last_completed_iteration` auto-update
- Iteration 1 graduation ceremony: close artifact, iteration 2 charter, phase 0 charter update
- Legacy SHA256 manifest check removed from doctor quick checks (blake2b `manifest_current` is authoritative)
- All 7 canonical artifacts bumped to 0.1.16
- README: aho.run domain, iteration roadmap, link fixes
- pyproject.toml: version 0.1.16, project URLs added
- `_iao_data()` bug fixed in components attribution CLI

## [0.1.15] — 2026-04-11

**Theme:** Foundation for Phase 0 exit

- Mechanical report builder (`report_builder.py`) — ground-truth-driven, Qwen as commentary only
- Component manifest system (`components.yaml`, `aho components` CLI, §23 bundle section)
- OpenTelemetry dual emitter in `logger.py` (JSONL authoritative, OTEL additive)
- Flutter `/app` scaffold with 5 placeholder pages
- Phase 0 charter rewrite to current clone-to-deploy objective
- New postflight gates: `manifest_current`, `changelog_current`, `app_build_check`
- MANIFEST.json refresh with blake2b hashes
- CHANGELOG.md restored with full iteration history

## [0.1.14] — 2026-04-11

**Theme:** Evaluator hardening + Qwen loop reliability

- Evaluator baseline reload per call (aho-G060 fix)
- Smoke instrumentation reads iteration from checkpoint at script start (aho-G061)
- Build log stub generator for iterations without manual build logs
- Seed extraction CLI (`aho iteration seed`)
- Two-pass artifact generation for design and plan docs

## [0.1.13] — 2026-04-10

**Theme:** Folder consolidation + build log split

- Iteration artifacts moved to `artifacts/iterations/<version>/`
- Build log split: manual (authoritative) + Qwen synthesis (ADR-042)
- `aho iteration close` sequence with bundle + run report + telegram
- Graduation analysis via `aho iteration graduate`
- Event log JSONL structured logging

## [0.1.12] — 2026-04-10

**Theme:** RAG archive + ChromaDB integration

- ChromaDB-backed RAG archive (`aho rag query`)
- Repetition detector for Qwen output
- GLM client integration alongside Qwen and Nemotron
- Evaluator baseline reload fix (aho-G060)

## [0.1.11] — 2026-04-10

**Theme:** Agent roles + secret rotation

- Agent role system (`base_role`, `assistant`, `reviewer`, `code_runner`)
- Secret rotation via `aho secret rotate`
- Age + OS keyring secret backends
- Pipeline validation improvements

## [0.1.10] — 2026-04-09

**Theme:** Pipeline scaffolding + doctor levels

- Doctor command with quick/preflight/postflight/full levels
- Pipeline scaffold, validate, and status CLI
- Postflight plugin system with dynamic module loading
- Disk space and dependency checks

## [0.1.9] — 2026-04-09

**Theme:** IAO → AHO rename

- Renamed Python package iao → aho
- Renamed CLI bin/iao → bin/aho
- Renamed state files .iao.json → .aho.json, .iao-checkpoint.json → .aho-checkpoint.json
- Renamed ChromaDB collection ahomw_archive → aho_archive
- Renamed gotcha code prefix ahomw-G* → aho-G*
- Build log filename split: manual authoritative, Qwen synthesis to -synthesis suffix (ADR-042)

## [0.1.0-alpha] — 2026-04-08

First versioned release. Extracted from kjtcom POC project as iaomw (later renamed iao, then aho).

- iaomw.paths — path-agnostic project root resolution
- iaomw.registry — script and gotcha registry queries
- iaomw.bundle — bundle generator with 10-item minimum spec
- iaomw.compatibility — data-driven compatibility checker
- iaomw.doctor — shared pre/post-flight health check module
- iaomw.cli — CLI with project, init, status, check, push subcommands
- iaomw.harness — two-harness alignment tool
- pyproject.toml — pip-installable package
- Linux + fish + Python 3.11+ targeted
