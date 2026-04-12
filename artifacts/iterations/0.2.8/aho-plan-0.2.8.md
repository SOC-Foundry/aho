# aho Plan — 0.2.8

**Phase:** 0 | **Iteration:** 2 | **Run:** 8
**Theme:** Discovery + exercise (5 discoveries, MCP-first mandate)
**Predecessor:** 0.2.7 (closed clean)
**Design:** `aho-design-0_2_8.md`
**Agent split:** Single-agent Claude Code throughout. **MCP-first execution mandate.** Run report must include "MCP Tools Invoked" per workstream.

## Workstreams

| WS | Surface | Type | Outcome |
|---|---|---|---|
| W0 | Bumps + decisions + run report template | bump | 10 artifacts → 0.2.8, decisions.md, "MCP Tools Invoked" section added |
| W1 | D1 diagnosis report | discovery | mcp-utilization-gap.md, predicted vs actual |
| W2 | CLAUDE.md + GEMINI.md MCP-first rules | code | New "MCP Toolchain" section in both, MUST-strength, [INSTALLED-NOT-WIRED] tag, plan doc W2.5 insert |
| W2.5 | MCP wiring — project .mcp.json | code | Project-level .mcp.json registering 9 servers as MCP connections. Hard prereq for W3 agent-native smoke |
| W3 | 9 per-server MCP smoke scripts (CLI + MCP-protocol) | code | artifacts/scripts/mcp-smoke/*.fish — two categories: CLI health + agent-native invocation |
| W4 | bin/aho-mcp smoke aggregator | code | mcp-readiness.md + data/mcp_readiness.json |
| W5 | Dashboard MCP verifier | code | aggregator.py reads readiness, 12 unknowns flip; verify via @playwright/mcp |
| W6 | components.yaml reconciliation | code | Remove 4 dead entries, update count claims |
| W7 | mcp_sources_aligned postflight gate | code | New gate diffing components.yaml against bin/aho-mcp |
| W8 | harness-watcher diagnosis + branch fix | discovery+code | harness-watcher-diagnosis.md, then Branch A/B/C/D execution |
| W9 | aho-G066 + aho-G067 + aho-G068 + ADR-044 update | bump | Three new gotchas (22 total), ADR text update for dashboard as Phase 2 tooling |
| W10 | Bundle generator sidecars + ADRs fix | code | Walk iterations dir + adrs dir, populate §6 and §12 properly, verify §4 Report generation runs |
| W11 | bundle_completeness postflight gate | code | Assert every iteration .md appears in bundle |
| W12 | Telegram inbound bridge to openclaw | code | inbound.py polls getUpdates, routes commands + free-text, openclaw socket client, formatter, allow-list, tests |
| W13 | Close | bump | Tests, postflight, bundle, run report, build log, changelog |

14 workstreams (W2.5 added post-W1 discovery). Largest aho iteration to date. Risk register names the cut order.

**MCP-first mandate per workstream:**
- W3/W4: by definition uses MCP
- W5: uses @playwright/mcp for dashboard verification (the iteration's first dogfood)
- W8: uses @modelcontextprotocol/server-filesystem for structured file ops where applicable
- W10: uses @modelcontextprotocol/server-filesystem for walking iteration/adr dirs
- W12: uses context7-mcp for Telegram Bot API doc lookups (avoid coding from memory)
- W13: uses @playwright/mcp to verify dashboard still renders after W5/W10 changes

Each workstream's row in the run report includes "mcp_used" listing tools invoked, or explicit "none — bash sufficient" with a one-line justification.

## Workstream details (essential only — design doc has full context)

**W0** — bumps, decisions.md, template change to add MCP Tools Invoked section

**W1** — execute D1 5-step diagnosis, write `mcp-utilization-gap.md`. No code.

**W2** — add "MCP Toolchain" section to CLAUDE.md and GEMINI.md per W0 strength decision (lean MUST). List 9 servers + use cases. Add [INSTALLED-NOT-WIRED] tag convention. Update First Actions Checklist with MCP surface verification step. Update this plan doc to insert W2.5.

**W2.5** — MCP wiring. Produce project-level `.mcp.json` at repo root registering all 9 servers as MCP connections for Claude Code. Hard prerequisite for W3 agent-native smoke tests. ~30 minutes.

**W3** — 9 fish scripts under `artifacts/scripts/mcp-smoke/`. Two test categories: CLI smoke (server health via binary/npx) and MCP-protocol smoke (agent-native invocation via wired surface, depends on W2.5). Each: print test, execute MCP call, assert response, exit 0/1. Servers requiring MCP-protocol stdio (vs CLI invocation) get a tiny Python helper — if more than 3 need it, scope a W3.5 helper module.

**W4** — `bin/aho-mcp smoke` aggregator runs all 9 W3 scripts, produces markdown matrix + JSON sidecar.

**W5** — extend `src/aho/dashboard/aggregator.py` to read `data/mcp_readiness.json` for `mcp_server` kind components. Smoke pass → ok, smoke fail → missing, sidecar absent/stale → unknown. Verify via Playwright MCP: open dashboard, screenshot MCP rows, confirm green.

**W6** — remove 4 dead entries from `components.yaml`. Update component count throughout README, CHANGELOG, harness docs (88 → likely 84).

**W7** — new `src/aho/postflight/mcp_sources_aligned.py`. Parse components.yaml MCP entries, parse bin/aho-mcp packages, assert sets equal. Add to postflight runner.

**W8** — execute D3 5-step diagnosis, write `harness-watcher-diagnosis.md`. Identify Branch A/B/C/D. Execute selected branch in same workstream. 30-minute time box on Branch C; carry to 0.2.9 if rabbit hole.

**W9** — add aho-G066 (declared tools must be exercised) and aho-G067 (declared structures must be populated) to gotcha_archive.json. Update ADR-044 with paragraph under Phase 2 acknowledging dashboard as Phase 2 tooling. Total gotchas: 21.

**W10** — modify bundle generator (likely `src/aho/bundle.py`):
1. §6 ADRs section: walk `artifacts/adrs/`, include any ADR with mtime in iteration window
2. §12 Sidecars section: walk `artifacts/iterations/<version>/`, include every .md not already used as §1-§5 source
3. §4 Report section: verify report_builder.py output exists; if missing, regenerate from event log
4. Audit 0.2.5/0.2.6/0.2.7 bundles for same gaps. Document but do not backfill.

**W11** — new `src/aho/postflight/bundle_completeness.py`. For each .md in `artifacts/iterations/<current>/`, assert it appears in the bundle (sidecar or canonical section). For each ADR with mtime in iteration window, assert it appears in §6.

**W12** — Telegram inbound bridge (full detail in design doc):
1. New `src/aho/telegram/inbound.py` — long-poll getUpdates, dedupe via offset file, chat_id allow-list filter
2. Router with command dispatch dict: /start, /help, /status, /iteration, /last, free-text
3. New `src/aho/telegram/openclaw_client.py` — speaks existing openclaw JSON protocol over Unix socket
4. Response formatter — extract execution/review fields, truncate at 4000 chars
5. Extend existing `aho-telegram.service` daemon process to do inbound polling alongside outbound. No new systemd unit.
6. Sync wait on openclaw with 30s timeout, async ack fallback ("dispatched, will reply when done")
7. Tests: mock getUpdates, mock openclaw socket, assert routing per command class
8. Manual smoke (Kyle): /status, /iteration, free-text dispatch, screenshot for run report

Use context7-mcp for Telegram Bot API documentation lookups during implementation. Do not code from memory.

**W13** — close: full test suite (target 175+), bundle (now with sidecars + ADRs + verified report), all postflight gates green including new bundle_completeness and mcp_sources_aligned, run report with MCP Tools Invoked section populated for all 13 workstreams.

## Definition of done

- [ ] All 10 canonical artifacts at 0.2.8
- [ ] Run report template includes "MCP Tools Invoked" section
- [ ] CLAUDE.md and GEMINI.md have MCP-first toolchain section
- [ ] Project-level `.mcp.json` exists registering 9 servers (W2.5)
- [ ] 9 MCP smoke test scripts exist; `bin/aho-mcp smoke` works end-to-end
- [ ] mcp-readiness.md and data/mcp_readiness.json exist
- [ ] Dashboard MCP rows show ok/missing instead of unknown (verified via Playwright MCP)
- [ ] components.yaml has 4 dead entries removed; component counts updated
- [ ] mcp_sources_aligned postflight gate passes
- [ ] harness-watcher diagnosis report exists; fix landed or daemon removed
- [ ] aho-G066 + aho-G067 + aho-G068 in gotcha registry (22 total)
- [ ] ADR-044 text updated with dashboard reference
- [ ] Bundle generator includes sidecars from iteration dir + ADRs with iteration-window mtime
- [ ] §4 Report is non-hollow in 0.2.8 bundle
- [ ] bundle_completeness postflight gate passes
- [ ] Telegram inbound bridge: /start, /status, /iteration, /last, free-text all work end-to-end on NZXTcos
- [ ] Telegram daemon extended in place (no new systemd unit)
- [ ] Test suite green (175+ tests)
- [ ] Bundle validates clean and contains every iteration artifact
- [ ] Run report MCP Tools Invoked section populated for all 13 workstreams

## Risk register

- **13 workstreams is the largest aho iteration ever.** Cut order if scope pressure forces (first cut first):
  1. W12 telegram inbound — defer to 0.2.9 with daemon left as send-only, explicit carryforward note
  2. W11 bundle_completeness gate — defer to 0.2.9, W10 bundle fix still ships
  3. W8 Branch C if rabbit hole — defer Branch C only, ship Branches A/B/D in scope
- **Floor that must ship for 0.2.8 to be a real iteration:** W0, W1, W2, W3, W4, W5, W6, W7, W9, W10, W13. That's 11 workstreams. W8 must ship at least the diagnosis report. W11 and W12 are the optional cuts.
- **MCP servers requiring stdio protocol:** if more than 3 of the 9 need a Python helper, scope W3.5 explicitly.
- **W8 Branch C rabbit hole:** 30-min time box.
- **W12 telegram polling vs daemon resource use:** long-poll is cheap, but verify daemon memory stays under existing 50MB peak.
- **Discovery iteration variant unproven:** first iteration with diagnosis-only workstreams. Retro in W13 close, decide whether to formalize in ADR-044.

## Out of scope

- Run report digestion over Telegram (separate iteration)
- Multi-user Telegram
- Building useful MCP-driven workflows beyond smoke tests
- Replacement servers for the 4 dead MCP packages
- P3 clone-to-deploy
- Backfilling historical bundles for D4
- kjtcom anything
- Engine-driven behavior in orchestrator.json
