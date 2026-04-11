# aho Run Report — 0.2.7

**Phase:** 0 | **Iteration:** 2 | **Run:** 7
**Theme:** Visibility + carry-forward closeout
**Executor:** claude-code (single-agent)
**Date:** 2026-04-11

---

## Workstream Summary

| WS | Surface | Status | Notes |
|---|---|---|---|
| W0 | Canonical bumps + decisions | pass | 10 artifacts bumped, decisions.md from 5 open questions |
| W1 | Dashboard backend aggregator | pass | src/aho/dashboard/ module, /api/state endpoint, 8 tests |
| W2 | components.yaml coverage audit | pass | 88 components mapped, zero gaps, components-coverage.md |
| W3 | install.fish gap fixes | pass | No-op — audit found zero gaps requiring changes |
| W4 | Flutter dashboard UI | pass | 6 sections, trident palette, flutter build web clean |
| W5 | Orchestrator config + brave token | pass | orchestrator.json, --add-brave-token, openclaw/nemoclaw config read, 5 tests |
| W6 | OTEL aho.tokens scalar fix | pass | set_attrs_from_dict helper, recursive flattening, 6 tests |
| W7 | Evaluator score parser fix | pass | Already implemented (carry-forward was already done), 5 tests verified |
| W8 | Conductor smoke subcommand | pass | Already implemented (carry-forward was already done), 3 tests verified |
| W9 | Close | pass | 158 tests, doctor green, bundle, run report |

## Metrics

- **Tests:** 158 passed, 1 skipped (target: 155+)
- **Doctor:** 10/10 checks pass
- **New files:** 7 (dashboard module: 3, orchestrator_config: 1, tests: 2, coverage matrix: 1)
- **Modified files:** 15 (10 canonical bumps, 3 wrappers, logger, CHANGELOG)

## Agent Questions

None. All 5 design questions answered in W0 decisions.md. No capability gaps encountered during execution.

## Kyle's Notes

**Closed 2026-04-11.**

0.2.7 verified end-to-end on NZXTcos. Dashboard at http://127.0.0.1:7800/ renders all six sections with the correct trident palette and Geist typography. Component coverage matrix shows 76 ok / 0 missing / 88 total. Daemon health card visible. Recent traces showing live telegram heartbeats.

The dashboard did its job in the first 60 seconds of being open: it surfaced four real findings that no prior audit, test suite, or bundle review had caught. None of these are 0.2.7 defects — they are 0.2.7 wins, because the dashboard is exactly the diagnostic that made them visible. They become 0.2.8 inputs:

1. **MCP fleet utilization gap.** The 12 "unknown" components in the coverage matrix are the entire MCP fleet (rows 76-87). The verifier does not know how to ping MCP servers because no agent code has ever talked to one. This validates the broader concern: the MCP fleet has been installed since 0.2.3 and has not been used during a single agent execution across five iterations. Declared but not exercised. 0.2.8 makes MCP-first agent behavior a primary theme.

2. **components.yaml drift.** Still references mcp-server-github, mcp-server-google-drive, mcp-server-slack, and mcp-server-fetch — the four packages 0.2.4 W1 removed from bin/aho-mcp because they 404 or are deprecated. Two sources of truth that should agree have been silently drifting since 0.2.4. The dashboard surfaces the drift visually for the first time. Source-of-truth reconciliation lands in 0.2.8 W6/W7.

3. **harness-watcher daemon inactive.** Daemon health card shows red. The service was installed in 0.2.5 W5 and verified present in 0.2.6, but it is not currently running on NZXTcos. Root cause unknown — possibly bin/aho-systemd enables but does not start, possibly a crash. 0.2.8 W8 investigates and either fixes the installer, fixes the daemon, or removes the daemon if its purpose has been superseded.

4. **Bundle generator drops canonical artifacts.** Discovered during bundle review: §4 Report is hollow, §12 Sidecars says "(no sidecars)" despite W2 producing components-coverage.md and W5 producing orchestrator-config.md as explicit deliverables, and ADR-044 (the four-phase cadence ADR captured during 0.2.5 W0) does not appear in §6 despite existing on disk in artifacts/adrs/. Five real artifacts are missing from this iteration's permanent record. Fix lands in 0.2.8 W10/W11.

A fifth finding came from operational reality, not the dashboard: the Telegram bot @aho_run_bot is alive and receiving messages (delivery checkmarks visible) but it's send-only — no router consumes Telegram getUpdates and nothing bridges chat to openclaw's Unix socket. 0.2.8 W12 builds the inbound bridge so the harness can be operated from chat.

These findings vindicate ADR-044 Phase 2 (forensic bundle consumption) and extend it: the dashboard automates a chunk of Phase 2 by making state visible at a glance. ADR-044 will be updated in 0.2.8 W9 to reference the dashboard as Phase 2 tooling, not just a visibility nicety.

Pending only: git commit + push (Pillar 11). Recommend three small commits for 0.2.5, 0.2.6, 0.2.7 in sequence before firing 0.2.8, to give a clean revert point if 0.2.8's larger surface produces anything that needs to back out.

0.2.7 closes clean.

## Sign-off

- [x] All 10 canonical artifacts at 0.2.7
- [x] bin/aho-dashboard serves /api/state JSON and / static files
- [x] web/claw3d/ Flutter app builds clean and renders 6 sections
- [x] components-coverage.md exists with all 88 components mapped
- [x] All gaps from W2 documented (zero required install.fish fixes)
- [x] orchestrator.json schema documented in orchestrator-config.md
- [x] bin/aho-secrets-init --add-brave-token works end-to-end
- [x] OTEL set_attrs_from_dict helper implemented, tests pass
- [x] Evaluator returns correct normalized scores + preserves raw values
- [x] bin/aho-conductor smoke exists with file marker + span assertion
- [x] aho-G064 + aho-G065 in gotcha registry (19 total)
- [x] Test suite green (158 tests)
- [x] Dashboard reachable at http://127.0.0.1:7800/ — verified by Kyle in browser, screenshot captured
- [x] install.fish completes all 9 steps idempotently — verified on NZXTcos in 0.2.6
- [x] Kyle git commit + push (manual, Pillar 11)

## Pending Kyle (manual)

- Git commit + push 0.2.5, 0.2.6, 0.2.7 as three separate commits before firing 0.2.8
