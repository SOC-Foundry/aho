# aho Design — 0.2.8

**Phase:** 0 | **Iteration:** 2 | **Run:** 8
**Theme:** Discovery + exercise — MCP utilization, source-of-truth reconciliation, harness-watcher diagnosis, bundle completeness, telegram inbound bridge
**Predecessor:** 0.2.7 (visibility iteration, closed clean)

## Why this iteration exists

0.2.7 shipped a working dashboard. Five real findings surfaced from operational reality, all sharing one root cause: **aho has been building infrastructure faster than it has been exercising or validating that infrastructure.**

1. **MCP fleet has 12 unknowns in the dashboard.** All 12 are MCP servers. Installed since 0.2.3 W1, never used during agent execution across five iterations.
2. **components.yaml drift.** Still references the four MCP packages 0.2.4 W1 removed (github, google-drive, slack, fetch). Two sources of truth silently drifting for four iterations.
3. **harness-watcher daemon inactive.** Installed in 0.2.5 W5, verified present in 0.2.6, currently not running. Root cause unknown.
4. **Bundle generator drops canonical artifacts.** 0.2.7 bundle has hollow §4 Report, "(no sidecars)" in §12 despite W2/W5 producing real sidecar artifacts, no ADR-044 in §6 despite the file existing on disk. Five real artifacts missing from the iteration's permanent record.
5. **Telegram bot is send-only.** Inbound messages reach Telegram (delivery checkmarks visible) but die there. openclaw is alive on its Unix socket but no bridge connects chat to it. Kyle wants to operate the harness from his phone.

This is a discovery iteration. Some workstreams produce diagnoses rather than code. Some produce code that exercises existing infrastructure. The only genuinely new thing built is the Telegram inbound bridge, which wires existing daemons together rather than introducing new infrastructure.

## Goals

1. MCP-first becomes a first-class agent behavior. CLAUDE.md and GEMINI.md gain explicit instructions. Run report template gains mandatory "MCP Tools Invoked" section.
2. Each of the 9 MCP packages gets a one-call smoke test. Dashboard's 12 unknowns flip.
3. components.yaml and bin/aho-mcp reconciled. New `mcp_sources_aligned` postflight gate.
4. harness-watcher diagnosed. Fixed, removed, or carried with explicit reason.
5. Bundle generator captures sidecars from `artifacts/iterations/<version>/`, ADRs with mtime in iteration window, and verifies §4 Report exists. New `bundle_completeness` postflight gate.
6. Telegram inbound bridge: messages to @aho_run_bot route to openclaw via Unix socket. Round-trip works for `/start`, `/help`, `/status`, `/iteration`, free-text dispatch. Single-user (chat_id allow-list).
7. New gotchas: aho-G066 (declared tools must be exercised), aho-G067 (declared structures must be populated).
8. ADR-044 textual update: dashboard is now part of Phase 2 tooling.

## Non-goals

- Run report digestion workflow over Telegram (pipe ships now, digestion ships in 0.2.9 or later)
- Multi-user Telegram
- New harness infrastructure beyond the inbound bridge
- Useful MCP-driven workflows beyond smoke tests
- Replacement servers for the four dead MCP packages
- P3 clone-to-deploy
- Backfilling historical bundles for Discovery 4 — enforce going forward only

## Discovery details (compressed)

**D1 MCP utilization gap.** Diagnosis confirms zero usage. Fix: W2 instructions, W3 smoke scripts, W4 aggregator, W5 dashboard verifier wiring.

**D2 Source-of-truth drift.** W6 removes 4 dead components.yaml entries. W7 adds postflight gate.

**D3 harness-watcher.** W8 diagnoses (5-step systemctl + journalctl + service file + installer + daemon source review), then executes Branch A/B/C/D fix in same workstream.

**D4 Bundle generator.** W10 fixes generator to walk `artifacts/iterations/<version>/` for sidecars and `artifacts/adrs/` for iteration-window ADRs. Verify §4 Report generation runs in close sequence. W11 adds `bundle_completeness` postflight gate.

**D5 Telegram inbound.** W12 builds inbound bridge.

## Telegram inbound bridge (W12 architecture)

```
Telegram getUpdates long-poll
  └→ filter by chat_id allow-list (Kyle only)
     └→ route by command:
        ├─ /start, /help     → static reply (no openclaw)
        ├─ /status           → call doctor preflight, format, reply
        ├─ /iteration, /last → read .aho.json + checkpoint, format, reply
        └─ any other text    → openclaw socket dispatch → format → reply
```

Implementation: new `src/aho/telegram/inbound.py` long-polls getUpdates, dedupes by `update_id` persisted to `~/.local/state/aho/telegram_offset`, filters by chat_id from secrets store. Router matches command prefixes; free-text routes through new openclaw socket client speaking the existing JSON protocol (no new openclaw surface). Response formatter extracts execution status / deliverables / score / recommendation, truncates at 4000 chars. Daemon: extend existing `aho-telegram.service`, no new systemd unit. Sync wait on openclaw responses with 30s timeout, fall back to async ack ("dispatched, will reply when done") on timeout. Tests: mock getUpdates, mock openclaw socket, assert routing per command class.

Out of scope for W12: run report digestion, multi-user, inline keyboards, media handling, group chats.

## Open questions for Kyle

1. MCP smoke depth: 1 call per server vs 3? Lean: 1.
2. Drift gate scope: mcp-only vs general canonical-sources? Lean: mcp-only in 0.2.8.
3. harness-watcher Branch D (remove if superseded) acceptable? Lean: yes.
4. MCP-first strength: preferred or MUST? Lean: MUST.
5. Discovery iteration formalization in ADR-044? Lean: yes, after 0.2.8 closes.
6. Telegram daemon fold-in vs new service? Lean: fold into existing aho-telegram.service.
7. Telegram openclaw response: sync wait or async ack? Lean: sync 30s timeout, async fallback.
