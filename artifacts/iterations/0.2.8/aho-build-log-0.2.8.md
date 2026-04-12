# aho Build Log — 0.2.8

**Date:** 2026-04-11
**Theme:** Discovery + exercise — MCP utilization, source-of-truth reconciliation, harness-watcher diagnosis, bundle completeness, telegram inbound bridge
**Executor:** claude-code (single-agent)

---

## W0 — Canonical bumps + decisions

- 10 canonical artifacts bumped 0.2.7 → 0.2.8
- decisions.md captured verbatim from Kyle's 7-decision block
- Run report template created with new "MCP Tools Invoked" section (per-workstream mcp_used + justification)
- .aho.json current_iteration → 0.2.8, last_completed → 0.2.7

## W1 — MCP utilization gap diagnosis

- D1 5-step diagnosis confirmed: zero MCP server invocations across 0.2.3–0.2.7 (5 iterations, 9 servers)
- Unexpected structural finding: installed ≠ wired. 9 npm packages on disk but none configured as MCP connections in Claude Code
- No mcpServers in ~/.claude/settings.json, no project .mcp.json
- ToolSearch for filesystem and context7 returned zero matches — agents literally cannot use MCP
- W1 self-assessment: attempted MCP tool use, hit structural gap, classified as [INSTALLED-NOT-WIRED]
- Two root causes identified: no agent instructions + no agent wiring

## W2 — CLAUDE.md + GEMINI.md MCP-first rules

- Added "MCP Toolchain" section to both files with MUST-strength rules for 6 server domains
- Added [INSTALLED-NOT-WIRED] tag convention
- Updated First Actions Checklist with step 5 (MCP surface verification)
- 9-server catalog table in both files
- Updated plan doc to insert W2.5 as hard prereq for W3
- aho-G068 (installed ≠ wired) flagged for W9

## W2.5 — MCP wiring

- Produced .mcp.json at repo root with 9 server entries
- Created artifacts/harness/mcp-wiring.md (5-section wiring doc)
- After session restart: 7 of 9 servers live (firebase-tools and flutter-mcp failed to start)
- Capability gap: .mcp.json not hot-reloaded, requires session restart

## W3 — MCP smoke test scripts

- 9 fish scripts under artifacts/scripts/mcp-smoke/
- firebase-tools diagnosis: wrong entry point (lib/bin/mcp.js → firebase mcp subcommand). Fixed .mcp.json
- flutter-mcp diagnosis: npm wrapper tries pip install, PyPI package never published. Broken upstream
- flutter-mcp replaced with official dart mcp-server (Dart SDK 3.9+, Kyle's SDK 3.11.4)
- 9/9 CLI smoke pass, 7/9 protocol smoke pass (firebase + dart need session restart)
- MCP-protocol smoke: 7 MCP tools invoked agent-native — first in aho history
- bin/aho-mcp and bin/aho-bootstrap updated to remove flutter-mcp
- mcp-fleet.md, CLAUDE.md, GEMINI.md, mcp-wiring.md updated for dart

## W4 — bin/aho-mcp smoke aggregator

- Added `smoke` subcommand to bin/aho-mcp
- Runs all scripts in artifacts/scripts/mcp-smoke/, single pass, captures results
- Produces data/mcp_readiness.json (9 entries) and artifacts/iterations/0.2.8/mcp-readiness.md
- 9/9 pass, 0 fail
- bin/aho-mcp version bumped 0.2.4 → 0.2.8

## W5 — Dashboard MCP verifier

- Updated aggregator.py _mcp_state() to read data/mcp_readiness.json
- Updated _verify_component() for mcp_server kind: returns ok/missing from smoke data
- Added dart as SDK-bundled server (checked via dart --version)
- /api/state returns 9 MCP entries, all status=ok
- Dashboard: 83 ok / 0 missing / 5 unknown (dead entries pending W6)
- Playwright MCP verification: navigated to localhost:7800, took screenshot
- 5 Playwright MCP tools invoked — iteration's MCP-first dogfood

## W6 — components.yaml reconciliation

- Removed 4 dead MCP entries: github, google-drive, slack, fetch
- Replaced flutter-mcp with dart mcp-server in components.yaml
- Updated doctor.py: flutter-mcp removed, dart checked via dart --version
- Updated mcp_canonical_registry_verify.py: same treatment
- Dashboard: 84 ok / 0 missing / 0 unknown / 84 total

## W7 — mcp_sources_aligned postflight gate

- New src/aho/postflight/mcp_sources_aligned.py
- Diffs components.yaml mcp_server entries against bin/aho-mcp + SDK servers
- First-run finding: @modelcontextprotocol/server-everything missing from components.yaml since 0.2.4
- Fixed: added entry. Component count 88 → 85
- Gate passes: 9 entries match

## W8 — harness-watcher diagnosis + fix

- 5-step diagnosis in under 5 minutes
- Root cause: Branch A — bin/aho-systemd enables but does not start services
- Fix: added systemctl --user start after enable in bin/aho-systemd
- harness-watcher now active (running) on NZXTcos
- Diagnosis report at artifacts/iterations/0.2.8/harness-watcher-diagnosis.md

## W9 — Gotchas + ADR-044 update

- 4 new gotchas (23 total):
  - G066: declared tools must be exercised
  - G067: declared structures must be populated
  - G068: installed ≠ wired
  - G069: enabled ≠ started
- ADR-044 updated: new "Phase 2 Tooling: Dashboard" section with concrete 0.2.7–0.2.8 examples

## W10 — Bundle generator sidecars + ADRs fix

- §6 Harness: now walks artifacts/adrs/ — 2 ADRs found and included
- §12 Sidecars: now walks artifacts/iterations/<version>/ — 4 sidecars found and included
- §4 Report: correctly deferred to W13 close (report_builder generates it)
- Bundle size 592KB
- Used mcp__filesystem__list_directory for directory walks (MCP-first)

## W11 — bundle_completeness postflight gate

- New src/aho/postflight/bundle_completeness.py
- Three categories: sidecar drift, canonical missing, ADR coverage
- First-run catch: build-log and report flagged as canonical missing (expected pre-close)

## W12 — Telegram inbound bridge

- src/aho/telegram/inbound.py: getUpdates long-poll, offset dedup, chat_id allow-list
- src/aho/telegram/openclaw_client.py: Unix socket client for openclaw
- Daemon extended in-place (serve() starts inbound thread alongside outbound socket)
- 5 commands: /start, /help, /status, /iteration, /last
- Free-text routes to openclaw with 30s sync wait, async ack fallback
- /status and /iteration verified live on Kyle's phone
- Two in-workstream fixes: run_checks → run_all import, Errno 11 socket read
- 24 tests pass
- Used context7-mcp for Telegram Bot API docs

## W13 — Close

- 182 tests pass, 1 skipped
- Doctor: 9/10 checks pass (dashboard_port warn expected)
- Test fix: test_check_mcp_fleet_all_present updated for 8-npm + 1-dart fleet
- Generated aho-report-0.2.8.md (14KB) via report_builder
- Generated aho-build-log-0.2.8.md (this file)
- Bundle regenerated with all canonical sections populated

---

*Build log for aho 0.2.8 — 14 workstreams (W0–W13 + W2.5), largest aho iteration to date.*
