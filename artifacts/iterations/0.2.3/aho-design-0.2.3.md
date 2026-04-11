# aho 0.2.3 — Design

**Phase:** 0 | **Iteration:** 2 | **Run:** 3
**Theme:** Three-agent role split + MCP fleet + dashboard plumbing + localhost arch + bundle expansion
**Run Type:** mixed | **Wall clock target:** 3-4 hours | **Agent:** Claude Code single-agent

## Context

0.2.2 cleared the deferral debt — three named stubs are now real daemons emitting OTEL spans. 0.2.3 builds on that foundation with the next architectural leap: **demoting Claude/Gemini from executor to conductor** and putting the local LLM fleet in charge of the actual workstream execution. This is the run where Pillar 1 ("delegate everything delegable") becomes structurally enforced rather than aspirational.

Simultaneously: ship the MCP server fleet as global components, lay the localhost-by-default plumbing for future dashboard/claw3d, expand bundle inclusions for context completeness, and clean up 0.2.2 hygiene carryovers.

## Objectives

1. **W0 hygiene.** 5 carryovers from 0.2.2: dedupe build log filename, fix MANIFEST version field bumper, broaden version sed patterns to catch freeform lines, document secrets unlock dance for clones, bump 8 canonical artifacts to 0.2.3.
2. **W1 MCP server fleet.** 12 MCP servers as global npm components: firebase-tools, @upstash/context7-mcp, firecrawl-mcp, @playwright/mcp, flutter-mcp, modelcontextprotocol/server-{filesystem,github,google-drive,slack,fetch,memory,sequential-thinking}. `bin/aho-mcp` wrapper, doctor checks, components.yaml entries, install integration.
3. **W2 Three-agent role split.** Add WorkstreamAgent (Qwen), EvaluatorAgent (GLM), HarnessAgent (Nemotron) at `src/aho/agents/roles/`. Each wraps OpenClaw with role-bound LLM. Conductor (Claude/Gemini) dispatches via NemoClaw. HarnessAgent runs as long-lived daemon `aho-harness-watcher.service` subscribing to event log.
4. **W3 Localhost arch + dashboard plumbing.** Add `dashboard_port` field to .aho.json (NZXTcos=7800, P3=7900). Add `aho_role` field ("localhost" default, "public_host" P3-only). Define heartbeat span schema. Add heartbeat emission to all 4 daemons (openclaw, nemoclaw, telegram, harness-watcher). Create `dashboard-contract.md` as 9th canonical artifact. Create `web/claw3d/index.html` placeholder.
5. **W4 Per-clone age key + bundle expansion + doctor.** Add age keygen step to bin/aho-install if no key exists. Add §24-§26 to bundle generator (Infrastructure, Harnesses, Configuration). Doctor checks for new components.
6. **W5 Dogfood + close.** End-to-end via WorkstreamAgent: dispatch a real task through the new role chain (conductor → nemoclaw → workstream-agent → qwen → evaluator-agent → glm → report). Verify trace shows 7+ spans. Bundle, report, run file, postflight, second commit prep.

## Non-goals

- claw3d real implementation (0.2.6 — Alex demo deliverable)
- aho.run public binding, Caddy, TLS, DNS (Phase 1)
- Cross-clone OTEL push (Phase 1)
- P3 clone attempt (0.2.4)
- Telegram receive-side / command handling (later)

## Workstreams

### W0 — Hygiene + carryover cleanup

- Bump 8 canonical artifacts to 0.2.3 (use broadened sed catching `**Version:**`, `Last updated`, freeform `aho 0.2.X` headings)
- MANIFEST.json writer: bump version field on regeneration
- Dedupe build log: `aho-build-log-{iteration}.md` is canonical, remove `aho-build-{iteration}.md` from postflight write list, add removal of orphan from prior runs
- Document secrets unlock dance in `artifacts/harness/global-deployment.md` capability gap inventory
- components.yaml: bump openclaw/nemoclaw/telegram notes to reference 0.2.2 graduation cleanly
- 108+ tests pass

### W1 — MCP server fleet

- 12 MCP servers as components in components.yaml (kind: mcp_server)
- `bin/aho-install` adds global npm install step: `sudo npm install -g <package>` for each (capability gap if not root)
- `bin/aho-mcp list` / `bin/aho-mcp status` / `bin/aho-mcp doctor`
- Doctor: `_check_mcp_fleet()` verifies each package present
- `artifacts/harness/mcp-fleet.md` as canonical artifact #10 (architectural spec, package list, version pins, role of each)
- 12 components added to components.yaml

### W2 — Three-agent role split

- `src/aho/agents/roles/workstream_agent.py` — `WorkstreamAgent(OpenClawSession)`, role="workstream", LLM=qwen3.5:9b, exposes `execute_workstream(ws_id, plan_section) -> dict`
- `src/aho/agents/roles/evaluator_agent.py` — `EvaluatorAgent(OpenClawSession)`, role="evaluator", LLM=GLM-4.6V-Flash-9B, exposes `review(workstream_output, design, plan) -> ReviewResult`
- `src/aho/agents/roles/harness_agent.py` — `HarnessAgent(OpenClawSession)`, role="harness", LLM=nemotron-mini:4b, exposes `propose_gotcha(event)`, `propose_adr(observation)`, `propose_component(detected)`. Long-lived watcher mode `--watch` subscribes to event log tail.
- `src/aho/agents/conductor.py` — new module, `Conductor` class wraps the orchestrator pattern: read plan → for each workstream, dispatch via NemoClaw to workstream agent → evaluator reviews → harness agent observes → next workstream
- Update `src/aho/agents/nemoclaw.py` orchestrator to recognize new roles and route by `kind=workstream|evaluator|harness` field
- `aho-harness-watcher.service` systemd user unit
- 3 new entries in components.yaml: workstream-agent, evaluator-agent, harness-agent (all `kind: agent`, `status: active`)
- Tests: `test_workstream_agent.py`, `test_evaluator_agent.py`, `test_harness_agent.py`, `test_conductor.py`

### W3 — Localhost arch + dashboard plumbing

- `.aho.json` schema additions: `dashboard_port: 7800` (NZXTcos), `aho_role: "localhost"`, `port_range: [7800, 7899]`
- `src/aho/config.py` reads/validates port assignment, refuses bind if collision detected
- `aho.logger.emit_heartbeat(component_name)` helper: emits `heartbeat` span every 30s when component is in `--serve` mode, exits cleanly on SIGTERM
- All 4 daemons (openclaw, nemoclaw, telegram, harness-watcher) emit heartbeat in their serve loops
- Heartbeat span schema: `{name: "heartbeat", attributes: {component, pid, uptime_seconds, role, dashboard_port}}`
- `artifacts/harness/dashboard-contract.md` — 9th canonical artifact: heartbeat schema, component health states (green/yellow/red), polling contract, future cross-clone push contract (deferred to Phase 1)
- `web/claw3d/` directory with placeholder `index.html` containing single `<h1>claw3d coming in 0.2.6</h1>` and a `<script>` reading components.yaml at load time and listing component names — proves the directory exists and the data binding works even before the Three.js scene
- `bin/aho-dashboard` skeleton wrapper (binds to `127.0.0.1:$dashboard_port`, serves placeholder JSON from traces.jsonl tail)

### W4 — Per-clone age + bundle expansion + doctor

- `bin/aho-install` adds: check `age-keygen --output ~/.config/aho/age.key` if file doesn't exist, halt with `[CAPABILITY GAP] age key generated, please backup ~/.config/aho/age.key before continuing` on first run
- `src/aho/bundle/__init__.py` adds §24 Infrastructure (.aho.json, .aho-checkpoint.json, MANIFEST.json, CHANGELOG.md, README.md, CLAUDE.md, GEMINI.md, install.fish), §25 Harnesses (every .md in artifacts/harness/), §26 Configuration (components.yaml, canonical_artifacts.yaml, pyproject.toml, .gitignore, projects.json)
- Bundle size will grow from ~316KB to ~700KB. Acceptable.
- Doctor: `_check_age_key()`, `_check_mcp_fleet()`, `_check_dashboard_port()`, `_check_role_agents()` (verifies workstream/evaluator/harness modules importable)
- `artifacts/harness/canonical_artifacts.yaml` adds entries for `mcp-fleet.md` and `dashboard-contract.md` (#9 and #10)

### W5 — Dogfood + close

**End-to-end role split smoke test:**
```fish
bin/aho-conductor dispatch "explain pillar 1 in two sentences"
sleep 8
wc -l ~/.local/share/aho/traces/traces.jsonl    # before vs after, expect +7
tail -30 ~/.local/share/aho/traces/traces.jsonl | grep -oE '"name":"[^"]+"' | sort -u
# Expected spans:
#   conductor.dispatch
#   nemoclaw.route
#   workstream_agent.execute
#   qwen.generate
#   evaluator_agent.review
#   glm.generate
#   telegram.send
```

If trace shows 7 spans in correct order, the role split is functional. Otherwise debug before close.

**Close sequence:** tests → bundle (now with §24-§26) → report → run file → postflight → .aho.json → checkpoint → telegram close-complete

## Capability gaps expected

- **W1:** sudo npm install for MCP fleet (one-time)
- **W4:** age keygen (only if no key exists, only on first install per clone)
- **W5:** manual git push by Kyle

## Success criteria

- 0 stubs maintained in components.yaml (now ~87 total components, was 72)
- 10 canonical artifacts (added mcp-fleet.md, dashboard-contract.md)
- 4 systemd user services running (openclaw, nemoclaw, telegram, harness-watcher)
- 12 MCP servers installed and verified
- 7-span trace from conductor smoke test
- Bundle ~700KB with §24-§26 populated
- web/claw3d/index.html exists and loads in browser showing component count
- 130+ tests passing (108 + ~25 new)
- All postflight gates green
