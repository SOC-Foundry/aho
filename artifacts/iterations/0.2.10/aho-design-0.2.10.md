# aho Design — 0.2.10

**Phase:** 0 | **Iteration:** 2 | **Run:** 10
**Theme:** Install surface implementation + CLI unification + observability deployment
**Predecessor:** 0.2.9 (hybrid, closed clean)
**Iteration type:** Feature (large, predetermined scope)

## Why this iteration exists

0.2.9 W8.5 produced install-surface-architecture.md as a scope contract. 0.2.10 implements it. Everything in section 6 of that document becomes a workstream here, plus three extensions Kyle surfaced at 0.2.9 close: `aho doctor --deep` with flutter/dart integration, CLI unification under single `aho` binary (decision A), and MANIFEST live-refresh daemon.

This is an overnight iteration. Kyle goes to sleep after W0 fires. Per-workstream review is DISABLED for the mechanical workstreams (W1-W15). Per-workstream review re-enables at the W16 discovery workstream and the W17 close. Kyle wakes, reviews from Telegram via `/ws status` through the night as auto-push notifications arrive.

## Goals

1. **CLI unification.** One `aho` binary. All current top-level `aho-*` wrappers become `aho <subcommand>`. Tab completion. `aho --help` lists everything. Old wrappers stay as implementation, `aho` is the public surface.

2. **Persona 3 entry point.** `aho run "task description"` (subcommand under unified CLI) works from any directory. Reads pwd, connects to openclaw daemon, dispatches task to agent, streams result, writes output to `$CWD/aho-output/run-<ts>.md`.

3. **OpenClaw system-service relocation.** OpenClaw daemon moves from project-scoped pip package to systemd user service. Unix domain socket at `/run/user/$UID/openclaw.sock`. Thin-client invocation from `aho run`.

4. **OpenClaw file bridge.** Connect chat + execute paths. Agent can read files from `$AHO_CWD`, inject into LLM context, write outputs. This is the single biggest persona 3 blocker from W8 findings.

5. **Local install directory.** `~/.local/share/aho/` populated from repo by new `bin/aho-install` wrapper. Layout per W8.5 decision 4c: bin/, harness/, registries/, agents/, secrets/, runtime/. `~/.local/bin/aho` symlink for public PATH access.

6. **Agent instruction split.** CLAUDE-iteration.md + CLAUDE-run.md, GEMINI-iteration.md + GEMINI-run.md. Persona 3 agent instructions cover $AHO_CWD binding, output conventions, no-touch rules on harness/repo dirs.

7. **AUR observability deployment.** otelcol-contrib and jaeger installed via `bin/aho-aur install`. Both deployed as systemd user services. OTEL on 127.0.0.1:4317, Jaeger UI on 127.0.0.1:16686. Existing OTEL emitter from 0.1.15 W2 starts producing traces Jaeger renders.

8. **Dashboard promotion + install section.** Dashboard becomes systemd user service (not ad-hoc `&`). New dashboard section surfacing install completeness: project-local and system-local components, present/missing status, version where applicable.

9. **`aho doctor --deep` with SDK integration.** New doctor mode invoking `flutter doctor -v` and `dart --version`. Output surfaced as structured SDK check section. On-demand, not default.

10. **Components-installed check expansion.** Every component in components.yaml gets a presence check across pacman/aur/python/npm/ollama/sdk/daemon categories. Replaces the current "declared vs running" check with "declared vs actually present on this machine."

11. **MANIFEST live-refresh daemon.** Harness-watcher extended to regenerate MANIFEST.json when files in artifacts/harness/ or data/gotcha_archive.json change. Async, cheap. Dashboard card shows MANIFEST freshness.

12. **0.2.9 residual gate fixes.** Three FAILs from 0.2.9 close: readme_current timezone handling, bundle_quality §22 format, manifest_current self-referential hash loop.

13. **Openclaw stability.** Errno 11 socket timing, repetition detector false positives, Errno 104 connection reset. These were 0.2.9 carry-forwards; the file-bridge + systemd-service work naturally exercises them.

## Non-goals

- Persona 3 end-to-end validation (that's 0.2.11)
- Persona 2 framework-mode validation (0.2.12)
- P3 clone-to-deploy (0.2.13)
- Multi-user anything
- Secrets package extraction (0.4.x+)
- kjtcom work

## Four open questions for Kyle (inherited from 0.2.9 W8.5 §8 + new)

1. **OpenClaw agent routing policy.** Which tasks go to Qwen local vs Claude API vs Gemini CLI? Lean: size-based threshold plus explicit agent-hint flag in `aho run --agent claude "task"`. Default: Qwen local for tasks under 2000 tokens, Claude API above. No Gemini CLI routing for 0.2.10.

2. **Dashboard systemd auto-start.** Auto-start on login or manual start? Lean: auto-start on login via systemd --user, dashboard always up.

3. **OTEL collector config specifics.** Which receivers, exporters, retention? Lean: OTLP gRPC receiver on 4317, file exporter to ~/.local/share/aho/traces/, batch processor, 24h retention. Minimal for local dev. Jaeger consumes from same OTLP receiver.

4. **Fernet store location.** Stay in ~/.config/aho/ (current) or move to ~/.local/share/aho/secrets/ per decision 4c layout? Lean: move to ~/.local/share/aho/secrets/ at install time with migration path for existing NZXTcos state. Migration = copy existing file to new path, update config to read new path, delete old file only after successful read.

**New Q5:** CLI unification transition. Keep old `aho-*` wrappers as shims forwarding to `aho <subcommand>`, or delete them? Lean: keep as shims for one iteration (0.2.10), delete in 0.2.11. Forward-compat cushion for any automation.

## Overnight execution model

Per-workstream review mode: DISABLED for W1-W15 (mechanical). ENABLED for W0, W16, W17 (discovery + close).

Auto-push to Telegram fires on every workstream_complete event. Kyle wakes to a notification stream showing:
- Workstream ID
- Status (pass / fail / partial)
- One-line outcome
- Iteration version

If any workstream fails, checkpoint sets proceed_awaited=true automatically (new behavior for overnight mode). Agent halts at next boundary, waits for Kyle's `/ws proceed` from phone.

Kyle controls via phone:
- `/ws status` — current state
- `/ws pause` — halt at next boundary
- `/ws proceed` — resume
- `/ws last` — last completed handoff

Normal green-path execution: agent works through W1-W15 unattended, halts at W16 for review, Kyle reviews in morning.

## Risk register

- **Overnight agent drift.** Highest risk. Mitigation: auto-halt-on-failure pattern above, conservative MCP-first mandate on every workstream, explicit no-scope-invention reminder in W0 prompt.
- **AUR package unavailability or build failure.** otelcol-contrib and jaeger both exist in AUR but AUR packages can break. Mitigation: capability gap on AUR failure, workstream halts with clear diagnostic, Kyle resolves in morning.
- **OpenClaw socket relocation breaks existing 0.2.9 functionality.** Telegram daemon depends on openclaw. Mitigation: relocation workstream (W5) tests Telegram end-to-end before declaring pass.
- **CLI unification breaks existing wrappers.** W1 maintains shims; W2 adds subcommands; only W17 close decides shim deletion (it does not — deferred to 0.2.11).
- **MANIFEST live-refresh creates storm.** Harness-watcher may trigger on every write. Mitigation: 5-second debounce window, W11 tests no-storm behavior.
- **Openclaw stability issues block persona 3 dispatch.** Mitigation: W13 is dedicated to Errno 11/104 fixes; if those fail, persona 3 dispatch degrades but iteration still closes.
