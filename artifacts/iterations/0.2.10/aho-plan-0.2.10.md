# aho Plan — 0.2.10

**Phase:** 0 | **Iteration:** 2 | **Run:** 10
**Theme:** Install surface implementation + CLI unification + observability deployment
**Iteration type:** Feature (large, predetermined scope)
**Agent split:** Single-agent Claude Code overnight.
**Review cadence:** Per-workstream review DISABLED for W1-W15. ENABLED for W0, W16, W17.
**MCP-first mandate:** active.
**Overnight mode:** auto-halt-on-failure via proceed_awaited=true on any workstream failure.

## Workstreams

| WS | Surface | Type | Review | Outcome |
|---|---|---|---|---|
| W0 | Bumps + Kyle decisions + carry-forwards | bump | yes | 12 artifacts → 0.2.10, decisions.md with Q1-Q5, carry-forwards refresh |
| W1 | Unified `aho` CLI skeleton | code | no | Python CLI under src/aho/cli.py with subcommand tree: run, doctor, iteration, secret, mcp, update, install |
| W2 | Subcommand migration of existing wrappers | code | no | bin/aho-* wrappers become `aho <sub>` subcommands; shims preserved as thin forwarders |
| W3 | `bin/aho-install` — local install directory populator | code | no | Creates ~/.local/share/aho/ layout, populates from repo, symlinks ~/.local/bin/aho |
| W4 | Agent instruction split | code | no | CLAUDE-iteration.md + CLAUDE-run.md, GEMINI variants; persona 3 content per W8.5 §3 decision 4d |
| W5 | OpenClaw → systemd user service + socket relocation | code | no | aho-openclaw.service unit file, socket at /run/user/$UID/openclaw.sock, Telegram daemon updated, end-to-end verified |
| W6 | OpenClaw file bridge (chat + execute paths unified) | code | no | Agent can read files from $AHO_CWD and inject into LLM context. Core persona 3 blocker. Most complex workstream. |
| W7 | `aho run` subcommand implementation | code | no | Fish wrapper reads pwd, connects to openclaw socket, dispatches task, streams result, writes to $CWD/aho-output/run-<ts>.md |
| W8 | AUR install: otelcol-contrib | code | no | bin/aho-aur extended, aho-otel-collector.service, OTLP gRPC listener on 127.0.0.1:4317 |
| W9 | AUR install: jaeger | code | no | aho-jaeger.service, UI on 127.0.0.1:16686, consumes from OTEL collector |
| W10 | Dashboard as systemd service + install completeness section | code | no | aho-dashboard.service auto-starts, new dashboard card surfaces every components.yaml entry with present/missing status |
| W11 | MANIFEST live-refresh daemon | code | no | Harness-watcher handler regenerates MANIFEST.json on harness/registry writes, 5s debounce |
| W12 | `aho doctor --deep` with flutter/dart integration | code | no | Invokes flutter doctor -v + dart --version, structured output as SDK section |
| W13 | Components-installed check expansion | code | no | Every components.yaml entry gets category-appropriate presence check (pacman/aur/python/npm/ollama/sdk/daemon) |
| W14 | Openclaw stability: Errno 11, repetition detector, Errno 104 | code | no | Socket timing fix, repetition detector threshold tuning on qwen, connection reset handling |
| W15 | 0.2.9 residual gate fixes | code | no | readme_current timezone, bundle_quality §22 format, manifest_current self-referential hash loop |
| W16 | Post-install smoke validation | discovery | yes | End-to-end check: fresh `aho run "hello world"` from /tmp/ succeeds, dashboard shows green, Jaeger has traces. Kyle reviews. |
| W17 | Close | bump | yes | Tests, bundle, run report, build log, CHANGELOG, Kyle's Notes. |

17 workstreams. Largest iteration ever. Most are mechanical; the nonlinear ones are W5 (socket relocation), W6 (file bridge), W13 (components check expansion), and W16 (discovery).

## Overnight halt behavior

New behavior for 0.2.10: if any workstream fails, the agent writes `proceed_awaited: true` to the checkpoint before emitting workstream_complete with status=fail. Agent halts at next boundary via wait_if_paused(). Telegram auto-push delivers failure summary to Kyle's phone. Kyle wakes, reviews via `/ws last`, decides whether to `/ws proceed` (skip and continue) or leave paused for morning debug.

If agent hits a capability gap (missing package, sudo required, etc.), same halt-on-gap behavior as normal interrupt-disciplined runs. Treat capability gap as implicit pause.

## Definition of done

- [ ] All 12 canonical artifacts at 0.2.10
- [ ] `aho` unified CLI with all subcommands wired
- [ ] `aho run "task"` works from any directory
- [ ] ~/.local/share/aho/ populated, ~/.local/bin/aho symlinked
- [ ] CLAUDE-run.md and GEMINI-run.md exist and readable
- [ ] OpenClaw systemd service running, socket at /run/user/$UID/openclaw.sock
- [ ] OpenClaw file bridge: agents can read files from $AHO_CWD
- [ ] otelcol-contrib installed from AUR, systemd service up, 4317 listening
- [ ] jaeger installed from AUR, systemd service up, 16686 serving UI
- [ ] Dashboard auto-starts as systemd service, install completeness section live
- [ ] MANIFEST live-refreshes on harness/registry writes
- [ ] `aho doctor --deep` invokes flutter + dart checks
- [ ] Every components.yaml entry gets category-appropriate presence check
- [ ] Openclaw Errno 11/104 + repetition detector fixes verified
- [ ] 0.2.9 residual gates all ok (or documented as intentionally deferred)
- [ ] Test suite green (target 250+)
- [ ] Bundle validates clean with all sections populated
- [ ] Post-install smoke: `aho run "hello world"` from /tmp/ succeeds end-to-end

## Out of scope

- Persona 3 validation with real tasks (0.2.11 — now that entry point exists)
- Persona 2 framework-mode (0.2.12)
- P3 clone-to-deploy (0.2.13)
- Remote agent executor (future)
- Multi-user telegram
- Secrets package extraction
- kjtcom
