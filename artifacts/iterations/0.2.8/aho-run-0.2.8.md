# aho Run Report — 0.2.8

**Phase:** 0 | **Iteration:** 2 | **Run:** 8
**Theme:** Discovery + exercise — MCP utilization, source-of-truth reconciliation, harness-watcher diagnosis, bundle completeness, telegram inbound bridge
**Executor:** claude-code (single-agent)
**Date:** 2026-04-11

---

## Workstream Summary

| WS | Surface | Status | Notes |
|---|---|---|---|
| W0 | Bumps + decisions + run report template | pass | 10 artifacts bumped, decisions.md, MCP Tools Invoked section added |
| W1 | D1 diagnosis report | pass | mcp-utilization-gap.md — zero usage confirmed, structural wiring gap found |
| W2 | CLAUDE.md + GEMINI.md MCP-first rules | pass | MCP Toolchain section in both, MUST rules, [INSTALLED-NOT-WIRED] tag, plan doc updated |
| W2.5 | MCP wiring — project .mcp.json | pass | .mcp.json with 9 servers, mcp-wiring.md, verification deferred to session restart |
| W3 | 9 per-server MCP smoke scripts | pass | 9/9 CLI pass, 7/9 protocol pass (firebase+dart need restart), firebase entry point fixed, flutter-mcp replaced with dart mcp-server |
| W4 | bin/aho-mcp smoke aggregator | pass | 9/9 pass, mcp-readiness.md + data/mcp_readiness.json produced |
| W5 | Dashboard MCP verifier | pass | aggregator reads mcp_readiness.json, 7 unknowns → ok, 5 dead stay unknown (W6), verified via Playwright MCP |
| W6 | components.yaml reconciliation | pass | 4 dead removed, flutter→dart replaced, 88→84, doctor+postflight pass, dashboard 84/0/0/84 |
| W7 | mcp_sources_aligned postflight gate | pass | Gate catches server-everything gap on first run, fixed, 9/9 aligned |
| W8 | harness-watcher diagnosis + branch fix | pass | Branch A: installer enable-not-start bug, fixed, daemon running |
| W9 | aho-G066 + G067 + G068 + G069 + ADR-044 update | pass | 4 new gotchas (23 total), ADR-044 Phase 2 dashboard section |
| W10 | Bundle generator sidecars + ADRs fix | pass | §6 includes ADRs (2 found), §12 walks iteration dir (4 sidecars), §4 deferred to close |
| W11 | bundle_completeness postflight gate | pass | Gate works, correctly flags 2 canonical missing (build-log, report — W13 generates) |
| W12 | Telegram inbound bridge to openclaw | pass | inbound.py + openclaw_client.py, daemon extended, 5 commands + free-text, 24 tests pass |
| W13 | Close | pass | 182 tests, doctor 9/10, bundle 610KB, all postflight gates green |

## MCP Tools Invoked

| WS | mcp_used | Justification (if none) |
|---|---|---|
| W0 | none | bump workstream — no technology-specific work requiring MCP |
| W1 | none | servers not wired as MCP connections in Claude Code — structurally unavailable, not a choice |
| W2 | none | instruction workstream — no technology-specific work requiring MCP |
| W2.5 | none | wiring workstream — MCP surface being established, not yet available |
| W3 | mcp__filesystem__list_directory, mcp__memory__read_graph, mcp__everything__echo, mcp__context7__resolve-library-id, mcp__sequential-thinking__sequentialthinking, mcp__playwright__browser_snapshot, mcp__firecrawl__firecrawl_scrape | 7 servers invoked agent-native |
| W4 | none | aggregator workstream — runs fish scripts, no technology-specific MCP domain |
| W5 | mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_evaluate, mcp__playwright__browser_close | Dashboard verification via Playwright MCP — MCP-first dogfood |
| W6 | none | YAML reconciliation — no technology-specific MCP domain |
| W7 | none | postflight gate implementation — no technology-specific MCP domain |
| W8 | none | systemd diagnosis — no technology-specific MCP domain |
| W9 | none | gotcha + ADR text — no technology-specific MCP domain |
| W10 | mcp__filesystem__list_directory (2 calls: iteration dir + adrs dir) | Directory walks for sidecar and ADR discovery |
| W11 | none | postflight gate implementation — no technology-specific MCP domain |
| W12 | mcp__context7__resolve-library-id, mcp__context7__query-docs | Telegram Bot API getUpdates docs via context7-mcp |
| W13 | mcp__playwright__browser_navigate, mcp__playwright__browser_take_screenshot (planned for final dashboard verify) | Close: tests, doctor, build-log, report, bundle, postflight |

## Metrics

- **Tests:** 182 passed, 1 skipped (target: 175+)
- **Doctor:** 9/10 checks pass (dashboard_port warn expected — port in use)
- **Postflight gates:** mcp_sources_aligned ok, bundle_completeness ok
- **New files:** 10 (inbound.py, openclaw_client.py, mcp_sources_aligned.py, bundle_completeness.py, 9 smoke scripts, mcp-wiring.md, .mcp.json)
- **Modified files:** 18 (10 canonical bumps, aggregator.py, doctor.py, mcp_canonical_registry_verify.py, notifications.py, bundle/__init__.py, bin/aho-mcp, bin/aho-systemd, components.yaml)
- **MCP tools invoked:** 14 distinct MCP tool calls across 4 workstreams (W3, W5, W10, W12)

## Agent Questions

None. All 7 design questions answered in W0 decisions.md. No capability gaps encountered that required Kyle input during execution (firecrawl key and flutter-mcp replacement were handled via per-workstream review).

## Kyle's Notes

**Kyle's Notes (closed 2026-04-11):**

0.2.8 is the largest aho iteration to date and the most structurally
consequential. Five real discoveries landed as shipped fixes:

1. MCP utilization gap closed. Zero MCP invocations across iterations
   0.2.3 through 0.2.7; 14 distinct invocations across 4 workstreams
   in 0.2.8 alone (W3, W5, W10, W12). The MCP-first mandate is no
   longer aspirational.

2. Source-of-truth drift resolved. components.yaml and bin/aho-mcp
   agree for the first time since 0.2.4 (9 servers, 8 npm + 1 dart
   SDK-bundled). New postflight gate mcp_sources_aligned prevents
   recurrence.

3. harness-watcher daemon active. Root cause was Branch A installer
   bug — bin/aho-systemd enabled but did not start. One-line fix.

4. Bundle generator fixed. §4 Report no longer hollow, §12 Sidecars
   populated (4 entries), §6 includes iteration-window ADRs. New
   postflight gate bundle_completeness caught both missing files
   on first run and forced W13 to generate them.

5. Telegram inbound bridge live. /status returns live doctor output
   to Kyle's phone. Single-user allow-list, 30s sync wait with async
   ack fallback. First daemon to operate the harness from off-keyboard.

Four new gotchas form a coherent family — a pattern language for
"things that pretend to work but don't":
- aho-G066: declared != exercised
- aho-G067: declared != populated
- aho-G068: installed != wired
- aho-G069: enabled != started

Every Phase 0 graduation criterion can now be checked against this
family. Running through the seven questions (declared? exercised?
populated? installed? wired? enabled? started?) is how P3 clone-to-
deploy validation catches gaps before they ship.

ADR-044 updated with Phase 2 Tooling: Dashboard section using
concrete 0.2.7-0.2.8 examples (12 unknowns flipped, 4 real catches
on first gate runs).

Per-workstream review cadence worked. W1's wiring gap surfaced in 4
minutes. W7's server-everything drift caught on first gate run. Both
would have shipped invisible under per-iteration review. Front-loaded
review intensity (heavy W1-W5, light W6-W13) matched the information
density curve. Worth formalizing as a sub-mode in ADR-045 (scheduled
for 0.2.9 W7).

Openclaw surfaced real stability issues during W12 telegram dispatch
testing: Errno 11 resource unavailable, thinking repetition false
positives, Errno 104 connection reset. These are carried to 0.2.10
as a dedicated iteration theme, not bolted onto 0.2.9.

Firecrawl key resolution used option A (fernet + shell env export)
which turned out cleaner than option B. The server inherits the key
from shell environment regardless of what .mcp.json says. .mcp.json
safely committed with empty string.

0.2.8 closes clean. Next: 0.2.9 workstream streaming + P3 clone
plumbing, 0.2.10 P3 hardening + openclaw reliability, 0.2.11 remote
agent executor + Phase 0 graduation.

## Sign-off

- [x] All 10 canonical artifacts at 0.2.8
- [x] Run report template includes "MCP Tools Invoked" section
- [x] CLAUDE.md and GEMINI.md have MCP-first toolchain section
- [x] 9 MCP smoke test scripts exist; `bin/aho-mcp smoke` works end-to-end (9/9 pass)
- [x] mcp-readiness.md and data/mcp_readiness.json exist
- [x] Dashboard MCP rows show ok instead of unknown (verified via Playwright MCP screenshot)
- [x] components.yaml reconciled: 4 dead removed, flutter→dart replaced, server-everything added (85 total)
- [x] mcp_sources_aligned postflight gate passes (9 entries match)
- [x] harness-watcher diagnosis report exists; Branch A fix landed, daemon running
- [x] Project-level `.mcp.json` exists registering 9 servers (W2.5)
- [x] aho-G066 + G067 + G068 + G069 in gotcha registry (23 total)
- [x] ADR-044 text updated with Phase 2 Tooling: Dashboard section
- [x] Bundle generator includes sidecars from iteration dir (4) + ADRs (2)
- [x] §4 Report is non-hollow in 0.2.8 bundle (14KB from report_builder)
- [x] bundle_completeness postflight gate passes
- [x] Telegram inbound bridge: /start, /help, /status, /iteration, /last, free-text all verified on NZXTcos
- [x] Telegram daemon extended in place (no new systemd unit)
- [x] Test suite green: 182 passed, 1 skipped (target: 175+)
- [x] Bundle validates clean (610KB) and contains every iteration artifact
- [x] Run report MCP Tools Invoked section populated for all 14 workstreams
- [x] Firecrawl API key removed from .mcp.json before git push (pre-push blocker)
- [x] Kyle git commit + push (manual, Pillar 11)
