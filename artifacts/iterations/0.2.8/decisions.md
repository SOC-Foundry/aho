# aho 0.2.8 Decisions

**Date:** 2026-04-11
**Source:** Kyle's pre-iteration decisions block, captured verbatim in W0.

---

## 1. MCP SMOKE TEST DEPTH

One call per server. Lean confirmed.

W3 produces 9 fish scripts, each making a single known-good call to its
target MCP server, asserting a known-good response shape, exiting 0/1.
Deeper exercise (multi-call, error handling, real workflow) waits until
there is a real workflow to drive it — likely 0.3.x.

Rationale: 0.2.8 is about establishing the habit of using MCP at all.
Smoke proves invokability. Utility proves itself later.


## 2. DRIFT GATE SCOPE

mcp_sources_aligned only. Lean confirmed.

W7 builds the specific gate. Generalization to canonical_sources_aligned
(covering MCP, models, pacman, systemd templates) waits until 0.3.x once
the pattern is clear from at least two concrete instances.

Rationale: don't over-engineer the abstraction before the second use case
exists.


## 3. HARNESS-WATCHER BRANCH D

Acceptable. Lean confirmed.

If W8 diagnosis determines harness-watcher's purpose is superseded by
other daemons or by dashboard polling, remove the service entirely:
- Delete the systemd template
- Remove from bin/aho-systemd install list
- Remove from components.yaml
- CHANGELOG entry explains the removal
- Update component count claims downstream

Dead code in components.yaml is the exact problem 0.2.8 is fixing.
Removal is the principled answer.

If diagnosis determines the daemon is needed but broken, execute Branch
A (installer fix), B (service file fix), or C (runtime fix) per the
30-minute time box.


## 4. MCP-FIRST INSTRUCTION STRENGTH

MUST. Lean confirmed.

CLAUDE.md and GEMINI.md "MCP Toolchain" section uses MUST language for
technology-specific work where an MCP tool exists:

- Flutter code -> MUST consult flutter-mcp before writing from memory
- Web UI verification -> MUST use @playwright/mcp before declaring done
- Library docs -> MUST use context7-mcp for Telegram Bot API, Firebase
  SDK, etc., not training-data recall
- Filesystem walks -> MUST use @modelcontextprotocol/server-filesystem
  for structured operations where applicable
- Web fetching -> MUST use firecrawl-mcp for retrieving external
  references during planning

Bash fallback is permitted but every workstream that takes the bash path
on a domain where an MCP tool exists must include a one-line
justification in the run report's MCP Tools Invoked section. Format:
"none -- bash sufficient because <reason>".

The weaker "preferred" version is what produced 0.2.7 W4 building Flutter
from memory. Strong version forces the question into every workstream.


## 5. DISCOVERY ITERATION FORMALIZATION

Yes, formalize after 0.2.8 closes. Lean confirmed.

W9 ADR-044 update is text-only for the dashboard reference (Phase 2
tooling acknowledgment). The discovery iteration variant gets its own
ADR amendment as a follow-on after 0.2.8 ships and we can write from
experience rather than prediction.

Capture target: ADR-044 amendment or ADR-045 (new) lands in 0.2.9 W0,
documenting:
- What a discovery iteration is (some workstreams produce diagnoses
  rather than code)
- When to use one (when accumulated declared-but-unvalidated debt
  exceeds capacity for forward feature work)
- How it differs from a remediation iteration like 0.2.4
- The 0.2.8 close serves as the empirical reference

Do not modify ADR-044 to formalize discovery iterations during 0.2.8
itself. That would be premature.


## 6. TELEGRAM DAEMON FOLD-IN VS NEW SERVICE

Fold into existing aho-telegram.service. Lean confirmed.

W12 extends the existing daemon process at src/aho/telegram/notifications.py
(or wherever the send-only daemon currently lives) to do inbound polling
in the same process. Single bot token, single rate limit, single Unix
process, dual purpose.

Rationale:
- Send and receive share the same bot identity, same secrets, same rate
  limit budget. Splitting them across processes creates two places to
  manage one set of credentials.
- Telegram's getUpdates and sendMessage cannot be used simultaneously
  from two processes against the same bot -- getUpdates locks the update
  stream. Single-process is the only correct architecture.
- Existing systemd unit aho-telegram.service is already enabled and
  running. Extending it requires zero install.fish changes.

Implementation: add an asyncio task or thread inside the existing daemon
that runs the long-poll loop alongside the existing send queue. The
inbound module (src/aho/telegram/inbound.py) is imported and started
from the existing daemon entrypoint.


## 7. TELEGRAM OPENCLAW RESPONSE -- SYNC WAIT OR ASYNC ACK

Sync wait with 30-second timeout, async ack fallback. Lean confirmed.

Flow:
1. Inbound message classified as free-text or unknown command
2. Send to openclaw via Unix socket
3. Wait synchronously for response, up to 30 seconds
4. If response arrives within 30s: format and reply with full result
5. If timeout: reply immediately with "dispatched, will reply when done"
   AND register an async callback that sends the result to the same chat
   when it eventually arrives

The 30-second value is provisional. Most openclaw round-trips Kyle has
seen are 5-15 seconds (qwen3.5:9b generation speed on the 2080 SUPER).
30s gives generous headroom for cold-cache calls without making the user
wait too long for the timeout fallback to fire.

Tunable via orchestrator.json under a new key:
  "telegram": {
    "openclaw_sync_timeout_seconds": 30
  }

Default 30, no behavior change in 0.2.8 if absent.

The async callback path uses the same Telegram sendMessage that the
existing outbound daemon uses. Bridge the inbound thread -> outbound queue
via the existing daemon's internal API; do not open a second Telegram
connection.


## GO/NO-GO

W0 unblocked. Proceed with W0 canonical bumps and decisions.md capture
using this block verbatim, then W1 through W13 per plan doc. Single-agent
Claude Code throughout with MCP-first execution mandate.

Reminders:
- W3 may need a Python helper for MCP servers that only speak stdio. If
  more than 3 of the 9 need it, scope a W3.5 helper module explicitly.
  Do not let helper scope absorb invisibly into W3.
- W5 verification of MCP rows in dashboard MUST use @playwright/mcp.
  This is the iteration's first dogfood of MCP-first.
- W8 Branch C is time-boxed to 30 minutes of diagnosis. Carry to 0.2.9
  if not resolved in that window.
- W12 implementation MUST use context7-mcp for Telegram Bot API doc
  lookups. Do not write Bot API code from memory.
- Risk register cut order if scope pressure forces: W12 first, W11
  second, W8 Branch C third. Floor for real 0.2.8 ship is 11 workstreams.

Brave API key already entered in 0.2.7 W5. Do not request it again.
Telegram bot @aho_run_bot already exists and the daemon is running. Do
not create a new bot or new systemd unit. W12 extends what exists.
