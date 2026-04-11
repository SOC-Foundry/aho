# aho 0.2.1 — Design

**Phase:** 0 | **Iteration:** 2 | **Run:** 1 | **Theme:** Global deployment architecture + native OTEL collector + model fleet pre-pull
**Run Type:** mixed | **Wall clock:** ~3-4 hours | **Agent:** Claude Code throughout

## Context

Iteration 1 graduated. Soc-foundry/aho is live. 0.2.1 is the first run of iteration 2 ("Global Deployment + Full Telemetry"). The thesis: every aho component runs globally, every component emits OTEL spans, every component shows up in the upcoming frontend visualization. Half-measures break the visualization story.

## Phase 0 Charter Reference

Phase 0 graduates when soc-foundry/aho can be cloned on P3 and deploy LLMs, MCPs, agents, and OTEL collector via `bin/aho-install` with zero manual Python edits. 0.2.1 builds the install architecture; 0.2.4–0.2.5 validate it on P3.

## Objectives

1. **Hygiene + carryovers (W0).** Fix `build_log_complete` design path lookup, update `agents-architecture.md` body prose, .gitignore improvements (`data/chroma/`, `app/build/`), MANIFEST refresh, version sync to 0.2.1.
2. **Global install architecture (W1).** New `artifacts/harness/global-deployment.md` defining hybrid systemd model, install paths, component lifecycle, capability gap inventory, uninstall safety contract.
3. **Real `bin/aho-install` (W2).** Idempotent installer. Detects platform (Arch + fish required), creates XDG dirs, installs Python package, generates systemd unit files from templates, handles capability gaps cleanly. Companion `bin/aho-uninstall` for clean removal.
4. **Native OTEL collector as systemd user service (W3).** Latest stable opentelemetry-collector-contrib binary at `~/.local/bin/aho-otel-collector`. Config at `~/.config/aho/otel-collector.yaml`. Systemd unit at `~/.config/systemd/user/aho-otel-collector.service`. Logger updated to default to local collector — no more `AHO_OTEL_ENABLED` gating.
5. **Global Ollama + model fleet pre-pull (W4).** Capability gap: sudo install Ollama via official installer if absent. Enable `ollama.service`. Pre-pull qwen3.5:9b, nemotron-mini:4b, GLM-4.6V-Flash-9B, nomic-embed-text. Verify each loads via Ollama API. New `bin/aho-models-status` wrapper.
6. **Component instrumentation pass (W5).** Wire OTEL spans into qwen-client, nemotron-client, glm-client, openclaw, nemoclaw, telegram. Spans include model, latency, token counts, exit codes. Stubs stay stubs in components.yaml — but their attempted calls now show in traces. Visibility deepens before functionality lands.
7. **Dogfood + first end-to-end trace (W6).** Run synthetic iteration smoke test with everything global. Capture OTEL trace in Jaeger. Bundle, report, run file, postflight. Prepare second commit for soc-foundry push.

## Non-goals

- openclaw / nemoclaw real (non-stub) implementations — 0.2.2
- Telegram bridge real implementation — 0.2.3
- MCP server fleet (firebase-tools, context7, firecrawl, playwright, flutter, modelcontextprotocol/server-*) — 0.2.3
- P3 clone attempt — 0.2.4
- Frontend wiring against OTEL data — 0.3.x
- Git operations of any kind (Pillar 11 — Kyle pushes manually)

## Workstreams

### W0 — Hygiene + carryovers
- Bump `.aho.json`, `.aho-checkpoint.json` to 0.2.1
- Backup tarball
- Bump all 7 canonical artifacts to 0.2.1, including `agents-architecture.md` body prose ("Iteration 0.1.13 marks the final realignment" → "Iteration 0.2.1 begins global deployment phase")
- Fix `build_log_complete.py` design doc path lookup (`get_artifacts_root() / "iterations" / iteration / f"aho-design-{iteration}.md"`)
- Add `data/chroma/`, `app/build/`, `__pycache__/`, `*.pyc` to `.gitignore`
- Refresh MANIFEST.json
- `pyproject.toml` version 0.1.16 → 0.2.1
- Verify 0.15.1 directory absent from working tree (cleanup committed)

### W1 — Global install architecture design
New `artifacts/harness/global-deployment.md` with sections:
- **Hybrid systemd model** — Ollama as system service (sudo install), aho daemons as user services (no sudo, lingering enabled)
- **Install paths**:
  - `~/.local/bin/aho*` — wrappers and binaries
  - `~/.config/systemd/user/aho-*.service` — unit files
  - `~/.config/aho/` — collector config, credentials
  - `~/.local/share/aho/` — traces, logs, state
- **Component lifecycle** — install, enable, start, status, stop, restart, uninstall (every component supports all 7)
- **Capability gap inventory** — sudo for Ollama install/service, sudo for `loginctl enable-linger` (already done on NZXT), GitHub auth for soc-foundry pushes (manual per Pillar 11)
- **Uninstall safety contract** — `bin/aho-uninstall` removes installed files but never touches `data/`, `artifacts/`, or git state
- **Idempotency contract** — every install operation safe to re-run, detects existing state and no-ops or upgrades

### W2 — `bin/aho-install` real implementation
Replace existing skeleton with idempotent installer. Fish script. Steps:
1. Platform check: `uname -s` = Linux, fish present, Arch (`/etc/arch-release` exists). Halt with capability gap if not.
2. Create XDG dirs (mkdir -p, idempotent)
3. `pip install -e . --break-system-packages` from project root
4. Generate systemd unit file templates (W3 will populate the OTEL collector one; this step creates the directory structure and template scaffolding)
5. Verify `loginctl show-user kthompson | grep Linger=yes` — capability gap if no
6. Print install summary

Companion `bin/aho-uninstall`:
1. `systemctl --user stop aho-*` (best effort)
2. `systemctl --user disable aho-*` (best effort)
3. `rm ~/.config/systemd/user/aho-*.service`
4. `rm ~/.local/bin/aho-otel-collector` (binary only, not wrappers)
5. `rm -rf ~/.config/aho/`
6. Print "data/ and artifacts/ untouched"

Both wrappers wired into `aho doctor` checks.

### W3 — Native OTEL collector as systemd user service
1. Detect arch (`uname -m` → x86_64) and download latest stable from `https://github.com/open-telemetry/opentelemetry-collector-releases/releases/latest` (otelcol-contrib_*_linux_amd64.tar.gz)
2. Extract `otelcol-contrib` binary, install to `~/.local/bin/aho-otel-collector` (renamed for namespacing)
3. Generate `~/.config/aho/otel-collector.yaml`:
   ```yaml
   receivers:
     otlp:
       protocols:
         grpc:
           endpoint: 127.0.0.1:4317
         http:
           endpoint: 127.0.0.1:4318
   processors:
     batch:
       timeout: 5s
   exporters:
     file:
       path: /home/kthompson/.local/share/aho/traces/traces.jsonl
     otlp/jaeger:
       endpoint: localhost:14317
       tls:
         insecure: true
   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors: [batch]
         exporters: [file, otlp/jaeger]
   ```
4. Generate `~/.config/systemd/user/aho-otel-collector.service`:
   ```ini
   [Unit]
   Description=aho OpenTelemetry Collector
   After=network.target
   [Service]
   Type=simple
   ExecStart=%h/.local/bin/aho-otel-collector --config=%h/.config/aho/otel-collector.yaml
   Restart=on-failure
   RestartSec=5
   [Install]
   WantedBy=default.target
   ```
5. `systemctl --user daemon-reload`
6. `systemctl --user enable --now aho-otel-collector.service`
7. Verify with `systemctl --user status aho-otel-collector` and a smoke OTLP send
8. Update `src/aho/logger.py`: default OTEL endpoint to `127.0.0.1:4317`, remove `AHO_OTEL_ENABLED` gating (always-on by default; opt-out via `AHO_OTEL_DISABLED=1`)
9. New `bin/aho-otel-status` wrapper showing service status, endpoint reachability, last trace timestamp from file exporter

### W4 — Global Ollama + model fleet pre-pull
1. Detect: `which ollama || systemctl status ollama`
2. If absent: capability gap halt — Kyle runs `curl -fsSL https://ollama.com/install.sh | sh` manually, agent resumes
3. Verify `ollama.service` enabled and active
4. For each model (qwen3.5:9b, nemotron-mini:4b, haervwe/GLM-4.6V-Flash-9B, nomic-embed-text):
   - `ollama list | grep <model>` — skip if present
   - `ollama pull <model>` — capability gap if pull fails (likely network or disk)
   - Verify load via `ollama show <model>`
5. New `bin/aho-models-status` querying `http://localhost:11434/api/tags` and rendering a table: name, size, modified, loaded
6. Add to `aho doctor` quick checks
7. Capability gap inventory updated in `global-deployment.md` with the Ollama install command for P3

### W5 — Component instrumentation pass
Wire OTEL spans into every LLM client, agent, and external service:

**`src/aho/artifacts/qwen_client.py`** — wrap each `generate()` call in span with attributes: `model=qwen3.5:9b`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `temperature`, `streaming`, `exit_status`

**`src/aho/artifacts/nemotron_client.py`** — same shape, model=nemotron-mini:4b

**`src/aho/artifacts/glm_client.py`** — same shape, model=haervwe/GLM-4.6V-Flash-9B, plus `image_count` attribute when present

**`src/aho/agents/openclaw.py`** — wrap `dispatch()` and `execute_code()` in spans. Stub status preserved in components.yaml, but instrumented.

**`src/aho/agents/nemoclaw.py`** — wrap `route()` and `dispatch()` in spans. Span name = `nemoclaw.dispatch.<role>`.

**`src/aho/telegram/notifications.py`** — wrap `send()` in span with attributes: `chat_id`, `message_length`, `priority`, `status`. Stub still — span emits even when send is no-op.

Tests in `artifacts/tests/test_otel_instrumentation.py` verify span emission for each component using a mock OTLP receiver.

### W6 — Dogfood + close + first end-to-end trace
1. Full test suite (target ~85 tests with new W3, W5 additions)
2. `aho doctor` — all gates green including new global services
3. Smoke synthetic iteration: trigger qwen-client + nemotron-client + openclaw stub + telegram stub in sequence, verify trace appears in `~/.local/share/aho/traces/traces.jsonl`
4. Optional: `bin/aho-otel-up` (Jaeger), open `localhost:16686`, screenshot the trace for iteration artifacts
5. Bundle generation through corrected close sequence
6. Mechanical report builder produces structured report
7. Run file generated with component section + agent attribution
8. Postflight gates green
9. `.aho.json` updates `last_completed_iteration: 0.2.1`
10. Checkpoint closed
11. Print git commit message draft for Kyle to push manually

## Capability gaps expected

- **W2:** Linger check (already done, should pass)
- **W3:** None (user service, no sudo)
- **W4:** Ollama install if absent (sudo curl pipe), model pulls if disk/network constrained
- **W6:** Manual git commit + push by Kyle after agent close (Pillar 11)

## Success criteria

- `bin/aho-install` runs idempotently on NZXTcos producing identical state on second run
- `bin/aho-uninstall` cleanly removes installed components without touching data
- `aho-otel-collector.service` running and reachable on 4317
- All 4 Ollama models pre-pulled and loaded
- Synthetic smoke test produces traces in file exporter
- Every LLM client + agent + external service emits OTEL spans
- All 7 canonical artifacts at 0.2.1
- Sign-off #5 = `[x]`
- Second commit pushed to soc-foundry/aho
