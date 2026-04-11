# aho 0.2.2 — Design

**Phase:** 0 | **Iteration:** 2 | **Run:** 2
**Theme:** Global daemons — openclaw, nemoclaw, telegram graduate from stub to active
**Run Type:** mixed | **Wall clock:** ~2-3 hours | **Agent:** Claude Code

## Context

0.2.1 built the global deployment spine: hybrid systemd, native OTEL collector, real installer, model fleet, instrumented stubs. 0.2.2 makes the three named stubs functional. After this run, the deferral debt that's been carried since iao 0.1.4 is fully cleared and aho has real working agents and notifications, not just instrumented placeholders.

## Objectives

1. **Carryover hygiene (W0).** Fix `build_log_complete` design path (second attempt), wall clock per-workstream computation, investigate evaluator warn/reject loop noise, bump components.yaml `next_iteration` fields to 0.2.2.
2. **OpenClaw global daemon (W1).** Real `OpenClawSession` implementation with Ollama dispatch, code execution sandbox, conversation history persistence. Systemd user service `aho-openclaw.service`. Wrapper `bin/aho-openclaw`. Status flips from `stub` to `active` in components.yaml.
3. **NemoClaw global daemon (W2).** Real `NemoClaw` orchestration with Nemotron classification, role routing, OpenClaw session pooling. Systemd user service `aho-nemoclaw.service`. Wrapper `bin/aho-nemoclaw`. Status flips from `stub` to `active`.
4. **Telegram bridge real implementation (W3).** Bot token in age-encrypted secret. Send-only first: capability gap interrupts, close-complete notifications, error alerts. Receive-side waits for 0.2.3+. Systemd user service `aho-telegram.service`. Wrapper `bin/aho-telegram`. Status flips from `stub` to `active`.
5. **Doctor + install integration (W4).** All three new services wired into `aho doctor`, `bin/aho-install`, `bin/aho-uninstall`. P3 deployment runbook updated.
6. **Dogfood + close (W5).** End-to-end smoke: send a real classify task through nemoclaw → openclaw → qwen → telegram notification. Verify trace in Jaeger shows the full chain. Bundle, report, run file, postflight, second commit prep.

## Non-goals

- MCP server fleet (0.2.3)
- P3 clone attempt (0.2.4)
- Telegram receive-side / command handling (0.2.3 or later)
- Frontend wiring (0.3.x)
- Any new postflight gates (0.2.2 is functionality, not gate machinery)

## Workstreams

### W0 — Carryover hygiene
- Bump versions, backup, .aho.json/.aho-checkpoint.json
- Bump 8 canonical artifacts to 0.2.2
- Fix `build_log_complete.py` design path resolution (second attempt — confirm against the new artifacts/iterations layout)
- Fix `report_builder.py` workstream parser to compute wall clock from checkpoint `started_at`/`closed_at` per workstream OR from event log first/last event timestamps when checkpoint lacks per-workstream timing
- Investigate `build_log_synthesis` evaluator warn/reject loop — likely the synthesis evaluator firing repeatedly during close. Add log statement to identify the cause; fix or document as known noise.
- Update `components.yaml`: openclaw, nemoclaw, telegram all bump `next_iteration: "0.2.2"` (in flight) — they'll flip to `active` at end of W1/W2/W3 respectively
- MANIFEST refresh

### W1 — OpenClaw global daemon
**Real implementation:**
- `OpenClawSession.__init__` — generates UUID, creates `/tmp/openclaw-{uuid}/` workspace, initializes conversation history list, opens persistent connection to Ollama via QwenClient
- `OpenClawSession.chat(message)` — appends to history, sends to Qwen with full conversation context, appends response, returns text
- `OpenClawSession.execute_code(code, language)` — writes code to workspace, subprocess.run with timeout=30s, captures stdout/stderr/exit_code, logs OTEL span with attributes
- `OpenClawSession.cleanup()` — removes workspace, closes connection
- All methods continue to emit OTEL spans (instrumentation already landed in 0.2.1 W5)

**Systemd service:**
- `~/.config/systemd/user/aho-openclaw.service`
- ExecStart: `python -m aho.agents.openclaw --serve` (new `--serve` mode that listens on Unix socket at `~/.local/share/aho/openclaw.sock`)
- Auto-restart on failure
- After=network.target ollama.service

**Wrapper:**
- `bin/aho-openclaw` — fish wrapper that connects to the socket and dispatches commands
- `bin/aho-openclaw chat "message"` — single message
- `bin/aho-openclaw execute "code"` — code execution
- `bin/aho-openclaw status` — session count, uptime

**components.yaml:** openclaw status `stub` → `active`, remove `next_iteration`, update notes to "global daemon, systemd user service"

**Tests:** `artifacts/tests/test_openclaw_real.py` — session creation, chat round-trip, code execution, cleanup

### W2 — NemoClaw global daemon
**Real implementation:**
- `NemoClaw.__init__` — initializes Nemotron classifier, opens session pool dict, loads role registry
- `NemoClaw.route(task)` — sends task description to Nemotron with role list, returns classified role
- `NemoClaw.dispatch(task)` — classifies via route(), gets-or-creates OpenClaw session for that role, dispatches via session.chat(), returns response
- `NemoClaw.session_pool` — dict keyed by role name, lazy-instantiated, capped at 5 concurrent sessions
- All methods emit OTEL spans

**Systemd service:**
- `~/.config/systemd/user/aho-nemoclaw.service`
- ExecStart: `python -m aho.agents.nemoclaw --serve` (Unix socket at `~/.local/share/aho/nemoclaw.sock`)
- After=network.target ollama.service aho-openclaw.service

**Wrapper:**
- `bin/aho-nemoclaw dispatch "task description"` — fire-and-forget dispatch
- `bin/aho-nemoclaw status` — pool state, route history

**components.yaml:** nemoclaw status `stub` → `active`

**Tests:** `artifacts/tests/test_nemoclaw_real.py` — routing, dispatch, session reuse

### W3 — Telegram bridge real implementation
**Secrets:**
- New age-encrypted secret `telegram_bot_token` via `aho secret set telegram_bot_token <token>` — capability gap if Kyle hasn't created the bot yet
- New age-encrypted secret `telegram_chat_id` for default destination
- Loaded at daemon startup via existing secrets backend

**Real implementation:**
- `aho.telegram.notifications.send(message, priority="normal", chat_id=None)` — POST to `https://api.telegram.org/bot{token}/sendMessage`, handles 429 rate limiting with backoff, logs OTEL span
- `aho.telegram.notifications.send_capability_gap(gap_description)` — formatted alert with `[CAPABILITY GAP]` prefix
- `aho.telegram.notifications.send_close_complete(iteration, status)` — iteration close notification
- Send-only — no receive loop in this run

**Systemd service:**
- `~/.config/systemd/user/aho-telegram.service`
- ExecStart: `python -m aho.telegram.notifications --serve` (Unix socket for inbound send requests from other daemons)
- After=network.target

**Wrapper:**
- `bin/aho-telegram send "message"` — manual send
- `bin/aho-telegram test` — sends a test message to verify wiring
- `bin/aho-telegram status` — service state, last send timestamp

**Wire into close sequence:** `src/aho/cli.py` close subcommand calls `telegram.send_close_complete()` after checkpoint write (best-effort, never blocks close on telegram failure)

**components.yaml:** telegram status `stub` → `active`

**Tests:** `artifacts/tests/test_telegram_real.py` — mock requests, verify payload shape, verify graceful failure on missing token

**Capability gap expected:** Kyle creates Telegram bot via @BotFather, gets token, runs `aho secret set telegram_bot_token <token>`, runs `aho secret set telegram_chat_id <id>`. Agent halts cleanly if secrets absent.

### W4 — Doctor + install integration
- `src/aho/doctor.py` adds checks: `aho-openclaw.service active`, `aho-nemoclaw.service active`, `aho-telegram.service active`, `telegram_bot_token secret present`
- `bin/aho-install` generates and installs all three new systemd unit files, runs `systemctl --user daemon-reload`, enables --now all three
- `bin/aho-uninstall` stops + disables + removes all three units
- `artifacts/harness/global-deployment.md` updated: 4 user services now (collector + 3 daemons), capability gap inventory updated with telegram bot creation
- `artifacts/harness/p3-deployment-runbook.md` updated with telegram setup steps

### W5 — Dogfood + close
**End-to-end smoke:**
```fish
bin/aho-nemoclaw dispatch "summarize the eleven pillars in 3 sentences"
```
- Nemoclaw classifies → routes to assistant role
- Openclaw session opens → dispatches to Qwen
- Qwen generates response
- Telegram notification fires on completion (best-effort)
- All five steps emit OTEL spans
- Verify trace in Jaeger shows: nemoclaw.dispatch → nemoclaw.route → openclaw.chat → qwen.generate → telegram.send

**Close sequence:**
- 87+ tests green (target: ~95 with new W1-W3 tests)
- `aho doctor` all green including 3 new service checks
- Bundle generation
- Mechanical report builder
- Run file with full component section showing all 3 stubs now `active`
- Postflight gates green
- `.aho.json` updated
- Checkpoint closed
- Print git commit message draft

## Capability gaps expected

- **W3:** Telegram bot creation by Kyle via @BotFather, secret installation. Agent halts cleanly if token absent.
- **W5:** Manual git add/commit/push by Kyle (Pillar 11)

## Success criteria

- openclaw, nemoclaw, telegram all `active` in components.yaml
- Three new systemd user services running and enabled
- End-to-end smoke produces 5-span trace in Jaeger
- Bundle shows §23 with 3 fewer stubs (now 0 stubs, all 72 components active)
- All postflight gates green
- Sign-off #5 = `[x]`
- Second commit pushed to soc-foundry/aho

## After 0.2.2

The deferral debt that's been carried since iao 0.1.4 is fully cleared. aho has real openclaw, real nemoclaw, real telegram. 0.2.3 adds MCP servers as global components. 0.2.4 ships to P3.
