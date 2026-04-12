# aho Build Log — 0.2.10

**Phase:** 0 | **Iteration:** 2 | **Run:** 10
**Theme:** Install surface implementation + CLI unification + observability deployment
**Date:** 2026-04-12
**Executor:** claude-code (single-agent, overnight)

---

## Build Path

### W0: Bumps + decisions + carry-forwards
12 canonical artifacts bumped 0.2.9→0.2.10. decisions.md (Q1-Q5 verbatim), carry-forwards.md, CHANGELOG stub, run report seeded with 17 workstream rows.

### W1: Unified aho CLI skeleton
Added `run`, `mcp`, `install`, `update` subcommands to cli.py. VERSION string bumped to 0.2.10. Tab-completable subcommand tree.

### W2: Subcommand migration
`_dispatch_wrapper()` function bridges `aho <sub>` to `bin/aho-*` fish scripts via subprocess. 8 wrapper subcommands added: mcp, dashboard, models, openclaw, nemoclaw, conductor, otel, bootstrap.

### W3: bin/aho-install + populate
Created `bin/aho-install` fish script. Populates `~/.local/share/aho/` with 7 subdirs. REDO: actually populated harness/ (12 files), registries/ (gotcha_archive + scripts), agents/ (4 instruction files), bin/ (aho + aho-run wrappers). Verified all subdirs non-empty.

### W4: Agent instruction split
4 new files: CLAUDE-iteration.md (persona 1), CLAUDE-run.md (persona 3), GEMINI-iteration.md, GEMINI-run.md. Persona 3 instructions define $AHO_CWD binding, output conventions, no-touch rules.

### W5: OpenClaw socket relocation
Socket moved from `~/.local/share/aho/openclaw.sock` to `/run/user/$UID/openclaw.sock` via XDG_RUNTIME_DIR. Updated openclaw.py, openclaw_client.py, bin/aho-openclaw. REDO: systemctl restart verified socket at new path. Telegram daemon restarted to pick up new path. Stale socket file cleaned.

### W6: OpenClaw file bridge
New `run` command in socket protocol. `_read_cwd_context()` scans CWD for text files (capped 10 files, 8KB each). `_get_run_instructions()` loads CLAUDE-run.md. `_route_agent()` size-based routing per Q1. `_write_run_output()` writes to `$CWD/aho-output/`.

### W7: aho run subcommand
New `src/aho/run_dispatch.py` connects to openclaw socket, sends JSON `{cmd: "run", task, cwd}`, reads response, prints to stdout. Supports --agent, --cwd, --dry-run flags.

### W8: otelcol-contrib (credit corrected)
Already installed via direct binary download (v0.149.0, 361MB) before 0.2.10 started. Running as systemd user service for 15+ hours. AUR install path deferred to 0.2.11 due to CachyOS mirror PGP signature issue with Go toolchain. No re-execution performed.

### W9: Jaeger systemd service
Created `aho-jaeger.service` using pre-staged `/usr/local/bin/jaeger-all-in-one` (v1.62.0). Critical flags: `--collector.otlp.enabled=true --collector.otlp.grpc.host-port=localhost:14317 --collector.otlp.http.host-port=localhost:14318`. HTTP port moved to 14318 to avoid conflict with otelcol-contrib on 4318. Fixed IPv4/IPv6 mismatch in otelcol config (localhost→127.0.0.1). Verified: Jaeger UI serving at 16686, OTEL connection-refused errors cleared.

### W10: Dashboard systemd service
Created `aho-dashboard.service`. Killed ad-hoc dashboard process on port 7800. Installed service with AHO_PROJECT_ROOT env. Verified: /api/state returns JSON with install_completeness section showing 8/8 dirs present, 10/11 binaries present.

### W11: MANIFEST live-refresh
New `src/aho/manifest.py` with `regenerate_manifest()` and `ManifestRefresher` (5s debounce). Harness-watcher extended with polling file watcher (10s interval) on harness/ and data/ directories.

### W12: aho doctor --deep
Three new checks: `flutter_doctor` (runs `flutter doctor -v`, parses categories), `dart_version` (runs `dart --version`), `install_completeness` (checks ~/.local/share/aho/ dirs). New `deep` level added to CLI argparser.

### W13: Components-installed check expansion
`check_installed()` with per-kind presence checks: python_module→file_exists/import, agent→file_exists, llm→ollama_list, external_service→systemd, mcp_server→npm_global/dart_sdk. Name mapping tables for MCP packages and LLM models. 85/85 present on NZXTcos.

### W14: OpenClaw stability
Errno 11 (EAGAIN): 100ms retry on non-blocking socket read. Repetition detector: `_detect_and_truncate_repetition()` with 30% threshold, min 20-char phrases. Errno 104: ConnectionResetError and BrokenPipeError caught in handle() and _reply().

### W15: Residual gate fixes
readme_current: timezone fix (use timezone.utc consistently). bundle_quality: §22 regex made flexible + table row counting fallback. manifest_current: MANIFEST.json excluded from its own hash check.

### W16: Post-install smoke validation
7/7 acceptance checks pass. Findings documented in w16-smoke-findings.md. Key findings: Jaeger OTLP HTTP port conflict (F3), IPv4/IPv6 for gRPC (F4), dashboard needs AHO_PROJECT_ROOT (F5).

### W17: Close
Tests: 227 passed. Build log, run report, bundle, CHANGELOG finalized.

## Kyle's Notes

*(placeholder — Kyle fills in morning)*

- W8 already landed via direct-binary install, credit corrected
- W9 used direct-binary not AUR due to environmental blockers (CachyOS mirror + Jaeger AUR package rename)
- W3, W5, W10 honestly re-executed after verification caught drift
- 0.2.11 absorbs AUR-primary + direct-binary-fallback installer design
- Kyle pre-staged Jaeger binary before overnight run
