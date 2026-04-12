# aho 0.2.9 Decisions

**Date:** 2026-04-11
**Source:** Kyle's pre-iteration decisions, captured verbatim in W0.

1. .MCP.JSON PORTABILITY
   Template substitution at bootstrap time. .mcp.json.tpl committed
   to repo with {{PROJECT_ROOT}} placeholder. bin/aho-bootstrap
   generates per-machine .mcp.json from template + aho_paths resolver.
   .mcp.json gitignored. Same pattern as systemd service templates.

2. TELEGRAM BOT ON P3
   P3 skips Telegram inbound daemon entirely for 0.2.9. NZXTcos stays
   the only machine running the inbound bridge. P3 may run outbound-
   only if needed. getUpdates cannot race between two daemons on one
   bot — Telegram locks the stream to one consumer. 0.2.11 solves
   multi-machine properly.

3. P3 COLD STATE
   Assume P3 has existing dev state from Kyle's personal use but no
   prior aho install. install.fish exercises fresh-install path for
   aho-specific components. Pre-existing dev state (Flutter SDK, git,
   python, fish) is expected and welcome.

4. /ws PAUSE GRANULARITY
   Any workstream boundary. Simple model. Users who don't want
   interruptions don't send /ws pause.

5. TONIGHT TIMING
   Run W0–W7 straight through, then W8 P3 clone. Single session,
   per-workstream review continues throughout. If scope pressure
   forces cuts: W7 (ADR-045) and W6 (secrets-architecture) cut
   first. Never cut W1, W2, or W8.
