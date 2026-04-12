# aho Plan — 0.2.9

**Phase:** 0 | **Iteration:** 2 | **Run:** 9
**Theme:** Remote operability plumbing + P3 clone
**Predecessor:** 0.2.8 (closed clean)
**Design:** `aho-design-0_2_9.md`
**Agent split:** Single-agent Claude Code throughout.
**Review cadence:** Per-workstream Phase 2. After each workstream, agent halts with handoff summary and waits for Kyle review.
**MCP-first mandate:** active per 0.2.8 W2 CLAUDE.md rules.

## Workstreams

| WS | Surface | Type | Outcome |
|---|---|---|---|
| W0 | Canonical bumps + decisions + carry-forward capture | bump | 10 artifacts → 0.2.9, decisions.md from 5 open questions, 0.2.8 carry-forwards logged |
| W1 | .mcp.json portability + template mechanism | code | Template at .mcp.json.tpl, bootstrap generates per-machine .mcp.json from paths resolver |
| W2 | install.fish cross-machine audit | code | NZXTcos hardcodes surfaced and parameterized, all paths via aho_paths.find_project_root() |
| W3 | Workstream event emission | code | workstream_start + workstream_complete events added to aho_event_log.jsonl by CLI entrypoints |
| W4 | /ws command family in Telegram inbound | code | /ws status, /ws pause, /ws proceed, /ws last routing + handlers, auto-push on workstream_complete |
| W5 | Checkpoint proceed_awaited handshake | code | .aho-checkpoint.json gains proceed_awaited field, agent-side polling helper in src/aho/cli.py or similar |
| W6 | secrets-architecture.md documentation pass | code | 30-min write-up under artifacts/harness/, junior-dev-readable, no code extraction |
| W7 | ADR-045: discovery iteration formalization | bump | ADR drafted from 0.2.8 empirical record, reviewed by Kyle, landed in artifacts/adrs/ |
| W8 | P3 clone execution | discovery+code | git clone on P3, bin/aho-bootstrap, install.fish, document every failure, fix-or-carry |
| W9 | Close | bump | tests, bundle, run report, build log, changelog, final sign-off |

9 workstreams as agreed. W8 is the load-bearing one.

## Workstream details

### W0 — Bumps + decisions + carry-forward

- All 10 canonical artifacts → 0.2.9
- `.aho.json` current_iteration → 0.2.9
- `artifacts/iterations/0.2.9/decisions.md` captures Kyle's answers to design open questions 1–5
- Carry-forward section in 0.2.9 design doc references: post-reboot daemon verification, protocol smoke column, openclaw stability → 0.2.10

### W1 — .mcp.json portability

- Create `.mcp.json.tpl` at repo root with placeholder `{{PROJECT_ROOT}}` in filesystem allowed-dirs
- `bin/aho-bootstrap` extended: on first run, reads template, substitutes `{{PROJECT_ROOT}}` with `aho_paths.find_project_root()` output, writes `.mcp.json`
- `.mcp.json` added to `.gitignore`
- `.mcp.json.tpl` committed to repo
- `bin/aho-bootstrap` idempotent: detects existing .mcp.json, skips regeneration unless `--force`
- Test: template substitution produces valid JSON, placeholder fully replaced, idempotency check works

### W2 — install.fish cross-machine audit

- Grep install.fish and all `bin/aho-*` wrappers for any hardcoded `/home/kthompson`, `NZXTcos`, `172.31.255.245`, or similar machine-specific values
- Replace with calls to `aho_paths`, `$USER`, `hostname`, or equivalent resolvers
- Audit `artifacts/harness/pacman-packages.txt` and `model-fleet.txt` for packages known to behave differently on P3 vs NZXTcos (e.g., ollama still needs upstream install per 0.2.6)
- Produce `artifacts/iterations/0.2.9/portability-audit.md` as iteration deliverable
- No install.fish changes unless audit surfaces something — most machine-specific work was already done right in 0.2.5/0.2.6

### W3 — Workstream event emission

- New module `src/aho/workstream_events.py` — emits `workstream_start` and `workstream_complete` events to `data/aho_event_log.jsonl`
- Both events include: iteration, workstream_id, timestamp, source_agent, outcome (for complete), one-line summary
- CLI integration: `aho iteration workstream start W0` and `aho iteration workstream complete W0 --status pass --summary "..."` subcommands
- Tests: event shape, JSONL append-only semantics, idempotent start/complete guards

### W4 — /ws command family

- Extend `src/aho/telegram/inbound.py` command dispatch dict with 4 new entries: `/ws status`, `/ws pause`, `/ws proceed`, `/ws last`
- Handlers:
  - `/ws status` — reads `.aho.json` + `.aho-checkpoint.json`, formats current iteration + WS + proceed_awaited state
  - `/ws pause` — writes proceed_awaited=true to checkpoint, replies "paused at next WS boundary"
  - `/ws proceed` — writes proceed_awaited=false, replies "proceeding"
  - `/ws last` — reads last workstream_complete event from event log, formats one-line summary
- Auto-push subscriber: daemon watches aho_event_log.jsonl for new workstream_complete events, sends summary to configured chat_id
- Use `context7-mcp` for any Telegram Bot API doc lookups during implementation (MCP-first)
- Tests: each command routes correctly, auto-push fires once per event, chat_id filter honored

### W5 — Checkpoint proceed_awaited handshake

- Add `proceed_awaited` field to `.aho-checkpoint.json` schema (default false)
- New helper `src/aho/workstream_gate.py` — `wait_if_paused(timeout_seconds=None)` function that polls checkpoint every 5s until proceed_awaited is false
- Agent-side integration: CLI wrappers call `wait_if_paused()` at each workstream boundary before writing workstream_start event
- Timeout None = block indefinitely. Explicit timeout supported for safety in non-interactive runs
- Tests: helper respects proceed_awaited toggle, timeout path works, no busy-loop (5s poll interval honored)

### W6 — secrets-architecture.md

- New file `artifacts/harness/secrets-architecture.md`
- Covers: age key location + mode, OS keyring role, fernet session cache, Pattern for committing config files with empty secret placeholders + shell env export, what NEVER gets committed (keys, passphrases, tokens, encrypted blobs outside explicit vault paths), junior-dev workflow for first-run
- Target: readable cold by a junior engineer who has never seen aho. ~500-800 words, code examples welcome
- No code extraction — documentation only. Hard extraction target is 0.4.x+

### W7 — ADR-045: Discovery iteration formalization

- New file `artifacts/adrs/ahomw-ADR-045.md`
- Draft from Claude (provided below in the launch prompt block or separately)
- Content: what a discovery iteration is, when to use one, how it differs from remediation iteration (0.2.4) and feature iteration (0.2.7), per-workstream review as sub-mode for high-novelty iterations, 0.2.8 as empirical reference
- Kyle reviews, agent lands file in adrs/ with chosen number
- Update ADR-044 cross-reference to ADR-045 if appropriate

### W8 — P3 clone execution

**Kyle-led, agent supports.** This workstream is manual clone driven by Kyle on P3 directly. Agent's role:
1. Produce a step-by-step runbook document (`artifacts/iterations/0.2.9/p3-clone-runbook.md`) before Kyle executes
2. Be available via chat during Kyle's execution for real-time diagnosis of any failures
3. After Kyle completes, document findings in `artifacts/iterations/0.2.9/p3-clone-findings.md`

**Expected failure categories:**
- Path hardcodes (should be caught by W1/W2 but reality will tell)
- Missing packages on P3 (different pacman state)
- Secret files not populated (expected, capability gaps)
- Ollama models not pulled (expected, fresh install)
- Dashboard port conflicts
- Telegram inbound conflict (decision 2 from W0)

**Success criteria (restated from design):** git clone works, bin/aho-bootstrap halts cleanly on capability gaps, install.fish runs as far as it can, whatever breaks gets a reproduction path documented. Full install success is 0.2.10.

### W9 — Close

- Test suite green (target 190+ tests, up from 182)
- Bundle generation, all postflight gates green (including bundle_completeness and mcp_sources_aligned)
- Run report `aho-run-0_2_9.md` with MCP Tools Invoked table populated for all 9 workstreams
- Build log `aho-build-log-0_2_9.md`
- CHANGELOG entry
- Pending Kyle (manual): any P3 gaps that didn't fix in W8, plus git commit + push for 0.2.5 through 0.2.9 (five iterations pending)

## Definition of done

- [ ] All 10 canonical artifacts at 0.2.9
- [ ] `.mcp.json.tpl` committed, `.mcp.json` gitignored, bootstrap generates per-machine
- [ ] portability-audit.md exists under artifacts/iterations/0.2.9/
- [ ] workstream_events.py emits start + complete events
- [ ] /ws status, /ws pause, /ws proceed, /ws last all work from Kyle's phone
- [ ] Auto-push fires on workstream_complete events
- [ ] .aho-checkpoint.json has proceed_awaited field, wait_if_paused helper works
- [ ] secrets-architecture.md exists and is junior-dev-readable
- [ ] ADR-045 exists in artifacts/adrs/
- [ ] p3-clone-runbook.md exists before Kyle executes P3 clone
- [ ] p3-clone-findings.md exists after Kyle's P3 clone attempt
- [ ] P3 has repo cloned, bin/aho-bootstrap attempted, findings documented
- [ ] Test suite green (190+)
- [ ] Bundle validates clean with all sections populated
- [ ] Run report MCP Tools Invoked section populated for all 9 workstreams

## Risk register

- **Tonight deadline on W8.** W0–W7 must land in time to execute W8 before Kyle's cutoff. If scope pressure arises, cut order: W7 (ADR-045 — can shift to 0.2.10 W0), W6 (secrets-architecture — can shift to 0.2.10), NEVER cut W1/W2/W8.
- **P3 cold state unknown.** If P3 has existing aho state, install.fish idempotency is exercised. If P3 is fully cold, fresh-install path is exercised. Different failure modes. Both informative.
- **Telegram getUpdates race if P3 runs inbound daemon.** W0 decision 2 must land — lean is P3 skips inbound daemon for 0.2.9.
- **Per-workstream cadence on tonight's deadline.** Heavy review early (W1-W5) is the right shape; W6-W7 can be lighter-touch; W8 is all-hands-on-deck regardless.

## Out of scope

- Full remote agent executor (0.2.11)
- Openclaw reliability fixes (0.2.10)
- Multi-user Telegram
- Secrets package extraction
- P3 full production verification
- Phase 0 graduation ceremony
- kjtcom anything
