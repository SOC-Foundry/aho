# aho Run Report — 0.2.9

**Phase:** 0 | **Iteration:** 2 | **Run:** 9
**Theme:** Remote operability plumbing + persona 3 discovery + install surface architecture
**Executor:** claude-code (single-agent)
**Date:** 2026-04-11

---

## Workstream Summary

| WS | Surface | Status | Notes |
|---|---|---|---|
| W0 | Bumps + decisions + carry-forward capture | pass | 12 artifacts bumped, decisions.md, carry-forwards.md |
| W1 | .mcp.json portability + template mechanism | pass | .mcp.json.tpl with {{PROJECT_ROOT}}, bootstrap step 4 generates per-machine, .gitignore updated, MCP npm list corrected to 8 (9th is dart SDK), 7 tests |
| W2 | install.fish cross-machine audit | pass | 3 hardcodes fixed (smoke script, mcp-wiring.md, global-deployment.md), portability-audit.md produced |
| W3 | Workstream event emission | pass | workstream_events.py, CLI `aho iteration workstream start/complete`, idempotent guards, 9 tests |
| W4 | /ws command family in Telegram inbound | pass | /ws status/pause/proceed/last + auto-push on workstream_complete, 20 new tests, 24 existing pass |
| W5 | Checkpoint proceed_awaited handshake | pass | workstream_gate.py with wait_if_paused(), CLI wired at workstream start, 9 tests |
| W6 | secrets-architecture.md documentation pass | pass | Three-layer model documented, first-run workflow, backend tree, security properties |
| W7 | ADR-045: discovery iteration formalization | pass | Three-type taxonomy (remediation/feature/discovery), per-workstream review sub-mode, ADR-044 cross-ref |
| W8 | Persona 3 validation | pass | No entry point exists. Chat has no file access. Execute has no LLM. 4/4 tasks failed. Findings documented. |
| W8.5 | Install surface architecture decision | pass | Three-persona taxonomy, 4 Kyle decisions, aho-run dispatch spec, 0.2.10 scope contract |
| W9 | Close | pass | 227 tests, doctor gates, bundle 636KB, CHANGELOG expanded, run report finalized |

## MCP Tools Invoked

| WS | mcp_used | Justification (if none) |
|---|---|---|
| W0 | none | bump workstream — no technology-specific work requiring MCP |
| W1 | none | template substitution + fish scripting — no technology-specific MCP domain |
| W2 | none | grep/audit workstream — no technology-specific MCP domain |
| W3 | none | Python event module + CLI wiring — no technology-specific MCP domain |
| W4 | mcp__context7__resolve-library-id, mcp__context7__query-docs | Telegram Bot API sendMessage docs via context7-mcp |
| W5 | none | Python polling helper + CLI wiring — no technology-specific MCP domain |
| W6 | none | documentation pass — no technology-specific MCP domain |
| W7 | none | ADR drafting — no technology-specific MCP domain |
| W8 | none | persona validation — openclaw chat/execute are existing tools, no MCP domain |
| W8.5 | none | architecture documentation — no technology-specific MCP domain |
| W9 | none | close workstream — tests, doctor, bundle generation, no technology-specific MCP domain |

## Metrics

- **Tests:** 227 passed, 1 skipped (target: 190+, actual: +45 new)
- **Doctor:** 33 checks (see close run for final state)
- **Bundle:** 636KB
- **New files:** 8 (workstream_events.py, workstream_gate.py, secrets-architecture.md, ADR-045, .mcp.json.tpl, test_mcp_template.py, test_workstream_events.py, test_workstream_gate.py, test_telegram_ws_commands.py)
- **Modified files:** 16 (12 canonical bumps, inbound.py, cli.py, bootstrap, .gitignore)
- **Iteration deliverables:** decisions.md, carry-forwards.md, portability-audit.md, p3-clone-runbook.md, p3-clone-findings.md, install-surface-architecture.md
- **MCP tools invoked:** 2 distinct (context7 resolve-library-id + query-docs in W4)
- **Workstreams:** 10 (W8.5 inserted per ADR-045 discovery pattern)
- **Iteration type:** Hybrid (feature W0–W7, discovery W8, architecture W8.5) per ADR-045

## Agent Questions

None. All 5 design questions answered in W0 decisions.md. W8 scope revision handled via per-workstream review (Kyle redirected P3 clone → persona 3 validation mid-iteration). W8.5 inserted cleanly as discovery workstream.

**Kyle's Notes (closed 2026-04-11):**

0.2.9 was scoped as remote operability plumbing + P3 clone. It
closed as hybrid: feature W0-W7 landed /ws streaming cleanly, then
W8 discovery found zero persona 3 surface, then W8.5 architecture
inserted to crystallize the install-surface decisions before any
more implementation work.

Highest-value deliverable: install-surface-architecture.md. Names
three aho personas (pipeline / framework / impromptu), classifies
every component as project-local vs system-local, captures four
Kyle decisions verbatim, specs persona 3 dispatch sequence. This
document is the scope contract for 0.2.10 through 0.2.13.

Persona 3 discovery was the kind of catch ADR-045 describes. If
W8 had been the P3 clone, 0.2.9 would have shipped an install that
fundamentally couldn't do the most common use case. The redirect
cost one workstream slot (W8.5) and delayed P3 clone by two
iterations. Cheap trade.

/ws Telegram streaming works end-to-end from phone. Kyle tested
/ws pause mid-W4 by accident, confirmed round-trip. W3+W4+W5
decomposition into three small workstreams was the right call —
each earned its place and the composition produced better
behavior than a monolith would have.

context7 MCP adoption crossed from "mandated" to "learned" in
this iteration. W4 agent invoked it proactively before writing
Telegram Bot API code, without prompt-level requirement. MCP-first
is becoming habit.

Three residual postflight FAILs at close are pre-existing
infrastructure debt, not 0.2.9 content:
- readme_current: timezone/clock skew between checkpoint and
  system time
- bundle_quality: §22 component count format in bundle generator
- manifest_current: self-referential hash loop (MANIFEST writes
  itself, then its hash changes)

All three move to 0.2.10 W15 as dedicated fixes.

Roadmap reshaped by W8.5:
- 0.2.10: install surface implementation + CLI unification + AUR
  observability (overnight execution, bold scope)
- 0.2.11: persona 3 validation on NZXTcos against installed surface
- 0.2.12: persona 2 framework-mode validation
- 0.2.13: P3 clone-to-deploy as Phase 0 graduation test

Phase 0 graduation criteria updated: not "clone to P3 succeeds"
but "three personas validated on two machines." Better bar.

0.2.9 closes clean. Five unpushed iterations (0.2.5-0.2.9) pending
Kyle git commit + push.

## Sign-off

- [x] Kyle reviewed and approved
