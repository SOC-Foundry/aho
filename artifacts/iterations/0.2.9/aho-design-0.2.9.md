# aho Design — 0.2.9

**Phase:** 0 | **Iteration:** 2 | **Run:** 9
**Theme:** Remote operability plumbing + P3 clone
**Predecessor:** 0.2.8 (discovery, closed clean)

## Why this iteration exists

Two goals that share one dependency: you need `/ws` streaming working before P3 clone so you can monitor the clone from your phone, AND you need the clone to happen tonight because the calendar is pressing and P3 is the Phase 0 graduation test substrate.

0.2.9 ships the plumbing, clones to P3, documents whatever P3 reveals. Scope is deliberately bounded to plumbing — not the full remote-executor architecture (that crystallizes in 0.2.11 after you've lived with the simpler `/ws` streaming for a while).

## Goals

1. `/ws` command family in Telegram inbound: status, pause, proceed, last. Paired with workstream_start and workstream_complete events auto-pushed to chat.
2. Agent-side handshake via `.aho-checkpoint.json` proceed_awaited field and a small polling helper. Executing agents halt at workstream boundaries, wait for `/ws proceed`, resume.
3. `.mcp.json` and install.fish audited for NZXTcos-specific hardcodes; parameterized where found.
4. Secrets architecture documented (soft action, not extracted as package). Junior devs get a readable-cold explanation of how aho keeps secrets out of the repo.
5. ADR-045: discovery iteration formalization. Lifted from 0.2.8 carry-forward. Claude drafts, Kyle reviews, ships.
6. P3 clone executed. git clone → bin/aho-bootstrap → install.fish on fresh CachyOS box. Whatever fails gets documented in real time. Findings drive 0.2.10 scope.

## Non-goals

- Full Telegram-driven remote agent executor (0.2.11)
- Openclaw reliability fixes (0.2.10)
- Multi-user Telegram
- Extracting secrets as standalone package (0.4.x)
- P3 full production verification (just plumbing in place, not optimized)
- Phase 0 graduation ceremony (0.2.11)
- kjtcom anything

## The /ws streaming feature

**User-facing surface from Telegram chat:**

- `/ws status` — current iteration + current workstream + last event timestamp
- `/ws pause` — sets checkpoint proceed_awaited=true, causes next workstream boundary to halt
- `/ws proceed` — sets checkpoint proceed_awaited=false, releases halted agent
- `/ws last` — last completed workstream summary from event log

**Auto-push:** every `workstream_complete` event in aho_event_log.jsonl triggers a short summary push to the configured chat_id. Format: workstream ID, status, one-line outcome, iteration version. Truncated to fit one Telegram message.

**Agent side:** executing agent (Claude Code, Gemini CLI) writes workstream_start event on entry, workstream_complete on exit. Between workstreams, if proceed_awaited=true in checkpoint, agent polls checkpoint every 5s until false, then proceeds. Simple blocking loop, no complexity.

**Out of scope for 0.2.9:** bidirectional chat (you can send free-text to openclaw today via the W12 bridge, but /ws is specifically for workstream control, not dispatch).

## The P3 clone plan

**Preconditions:**
- P3 is a fresh CachyOS install (or close to fresh — state acceptable if it's already Kyle's dev machine)
- SSH access from NZXTcos to P3 works
- Kyle has GitHub SSH key deployed on P3 (github.com-sockjt host alias per existing conventions)
- /ws streaming is live on NZXTcos so Kyle can watch the clone from phone if needed

**Clone sequence (W8):**
1. `ssh tsP3-cos`
2. `cd ~/Development/Projects/` (P3 path convention per user memory)
3. `git clone git@github.com-sockjt:SOC-Foundry/aho.git`
4. `cd aho`
5. `./bin/aho-bootstrap` — expect capability gaps for age passphrase + telegram token entry
6. `./install.fish` — 9 steps
7. `aho doctor` — full preflight
8. Verify dashboard reachable at http://127.0.0.1:7800/ from P3 browser
9. Verify Telegram `/status` works from P3 (the daemon on P3 should be its own instance, separate from NZXTcos)

**Expected failures:**
- Path hardcodes in .mcp.json (filesystem allowed-dir pointing at NZXTcos path)
- Secret files not populated on P3 (first-run capability gaps)
- Ollama models not present (pulled fresh on first install)
- MCP servers may need npm install on P3 (not just on NZXTcos)
- Telegram bot allow-list conflict if P3 tries to listen with same chat_id
- Dashboard port 7800 may clash with other P3 services

**What counts as success tonight:**
- git clone works
- bin/aho-bootstrap completes or halts cleanly with capability gaps
- install.fish runs as far as it can without NZXTcos-specific failures
- Whatever breaks is documented with a clear reproduction path

**What is NOT a success criterion tonight:**
- All 9 install.fish steps pass on P3
- Dashboard live on P3
- Telegram working from P3

Those are 0.2.10 targets. Tonight is "clone and document reality."

## §3. Trident — Cost Model

aho 0.2.9 is a single-agent Claude Code iteration. No local fleet delegation for workstream execution (Gemini CLI not used). Local fleet (Qwen, Nemotron, GLM) active for daemon services (openclaw, nemoclaw, harness-watcher). Cost model:

- **Orchestrator (Claude Code):** all 10 workstreams, per-workstream review cadence
- **Local fleet:** daemon services only (openclaw chat, nemoclaw routing, harness-watcher events)
- **Delegate ratio:** low (single-agent run), acceptable for install-surface + portability scope

## Pillar Applicability

All eleven pillars apply. Key pillars for 0.2.9:

- Pillar 4 (wrappers are the tool surface): .mcp.json.tpl + bin/aho-bootstrap template generation
- Pillar 6 (transitions are durable): checkpoint proceed_awaited handshake
- Pillar 10 (runs are interrupt-disciplined): /ws pause/proceed gives Kyle interrupt control without breaking execution flow. Capability gaps routed through Telegram.
- Pillar 11 (human holds the keys): no git operations by agent. Kyle commits manually. Per-workstream review ensures Kyle approves each workstream before next begins.

## Open questions for Kyle before W0

1. **P3 clone filesystem allowed-dir in .mcp.json.** Current NZXTcos value is `/home/kthompson/dev/projects/aho`. P3 value per your memory is `/home/kthompson/Development/Projects/aho` (capitalized, different structure). W1 decision: hard-code both paths as allowed-dirs? Template substitution at bootstrap? Detect at runtime? Lean: template substitution driven by `aho_paths.find_project_root()` at bootstrap time, file regenerated per-machine. Same pattern as systemd service templates.

2. **Telegram bot for P3.** Same bot (@aho_run_bot) with chat_id allow-list allowing both daemons to receive, or a second bot for P3? If same bot, getUpdates will race between NZXTcos daemon and P3 daemon — Telegram locks the update stream to one consumer. Must decide. Lean: P3 skips Telegram daemon entirely for 0.2.9; NZXTcos stays the only inbound bridge. P3 runs outbound-only. 0.2.11 solves multi-machine properly.

3. **P3 cold clone vs already-has-state.** Is P3 literally fresh, or does it have some aho state from earlier testing? Affects install.fish idempotency path exercised.

4. **/ws pause granularity.** Pause at *any* workstream boundary, or only at configured halt points? Lean: any boundary. Simple model, easier to reason about. Users who don't want to be interrupted just don't send /ws pause.

5. **P3 timing tonight.** When does the W8 clone happen relative to W0-W7 completion? Run W0-W7 straight through first, then W8 with fresh attention? Or land W1-W7 tonight and W8 tomorrow? Lean: straight through tonight since that's what you said you want. 6-compression option from my last message available if you need it.
