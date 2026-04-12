# Build Log — aho 0.2.9

**Theme:** Remote operability plumbing + persona 3 discovery
**Executor:** claude-code (single-agent)
**Date:** 2026-04-11
**Type:** Hybrid (feature W0–W7, discovery W8, architecture W8.5) per ADR-045

## W0 — Bumps + decisions + carry-forward capture
12 canonical artifacts bumped 0.2.8 → 0.2.9. decisions.md captured Kyle's 5 pre-iteration answers (MCP portability, Telegram P3, P3 cold state, /ws pause granularity, tonight timing). carry-forwards.md logged 0.2.10/0.2.11/0.4.x+ deferrals. CHANGELOG stub appended. Run report seeded.

## W1 — .mcp.json portability + template mechanism
Created .mcp.json.tpl with {{PROJECT_ROOT}} placeholder. bin/aho-bootstrap extended with step 4: reads template, substitutes via fish `string replace -a`, writes .mcp.json. Idempotent with --force override. .gitignore updated. Bootstrap npm list corrected from stale 11-package to current 8-package (9th is dart SDK-bundled). Step numbering fixed (duplicate step 5 removed). 7 tests.

## W2 — install.fish cross-machine audit
Grepped 5 patterns across bin/, src/, templates/, install.fish. Found 3 stragglers: server-filesystem.fish smoke script (hardcoded path → script-relative resolution), mcp-wiring.md (hardcoded path → {{PROJECT_ROOT}} reference), global-deployment.md (kthompson → $USER). Zero hardcodes remain in executable code. portability-audit.md produced.

## W3 — Workstream event emission
New module src/aho/workstream_events.py with emit_workstream_start() and emit_workstream_complete(). Both emit to aho_event_log.jsonl via log_event(). Idempotent via _scan_events() check. CLI integration: `aho iteration workstream start/complete`. Source agent defaults to AHO_EXECUTOR env var. 9 tests.

## W4 — /ws command family in Telegram inbound
4 new /ws commands in Telegram inbound dispatch: status (reads checkpoint), pause (writes proceed_awaited=true), proceed (clears proceed_awaited), last (reads last workstream_complete from event log). Auto-push subscriber tails aho_event_log.jsonl, sends Telegram notification on new workstream_complete events. Help text updated. Route refactored for multi-part commands. context7-mcp used for Telegram Bot API docs. 20 new tests, 24 existing pass.

## W5 — Checkpoint proceed_awaited handshake
New module src/aho/workstream_gate.py with wait_if_paused(). Polls .aho-checkpoint.json every 5s until proceed_awaited is false. Safe defaults: proceeds if field missing, file missing, or parse error. CLI integration: workstream start calls gate before emit. Timeout=None blocks indefinitely. 9 tests.

## W6 — secrets-architecture.md documentation pass
New file artifacts/harness/secrets-architecture.md. Three-layer model: age key (identity), OS keyring (session cache), Fernet store (encrypted JSON). Sections: overview with diagram, each layer, what never gets committed, first-run workflow, backend architecture, security properties, future plans. ~700 words, junior-dev-readable.

## W7 — ADR-045: discovery iteration formalization
New file artifacts/adrs/ahomw-ADR-045.md. Three-type iteration taxonomy: remediation (narrow, immutable scope), feature (broad, immutable scope), discovery (broad, adaptive within immutable theme). Per-workstream review formalized as SHOULD-default for discovery iterations. ADR-044 cross-reference added. Two Kyle-requested edits applied: reactive workstream count corrected, 0.2.9 hybrid type clarified.

## W8 — Persona 3 validation
Searched all 7 dispatch paths for persona 3 entry point. None found — aho has zero persona 3 implementation surface. OpenClaw's chat (LLM, no files) and execute (files, no LLM) are disconnected. 4 test tasks attempted against /tmp/aho-persona-3-test/: PDF summarize, SOW generation, risk review, email extraction. All 4 failed with "I can't access files." Execute path can read files but provides no LLM reasoning. p3-clone-findings.md documents all 5 findings.

## W8.5 — Install surface architecture decision (discovery insertion)
New file artifacts/iterations/0.2.9/install-surface-architecture.md. 8 sections: three-persona definition, component install taxonomy (project-local vs system-local), 4 Kyle decisions captured verbatim (openclaw Path A, OTEL/Jaeger AUR, aho-run name, working directory/update/install/agent-split), persona 3 dispatch sequence with ASCII diagram, system services inventory, 9 deliverables for 0.2.10, updated roadmap (0.2.10–0.2.13), 4 open questions for 0.2.10 W0.

## W9 — Close
227 tests pass (up from 182, +45 new). Doctor gates checked. Bundle generated. CHANGELOG expanded. Run report finalized.
