# GEMINI-iteration.md — aho Persona 1 (Pipeline Builder)

**Scope:** Agent instructions for Gemini CLI executing aho iterations (persona 1).
**Context:** You are inside a git-cloned aho repo, running an iteration with workstreams, checkpoints, and the full harness contract.
**See also:** GEMINI.md (universal Phase 0 instructions), GEMINI-run.md (persona 3 one-shot work).

---

## When This File Applies

This file applies when you are executing within the iteration/workstream framework:
- `aho iteration` commands
- Workstream-gated work (W0, W1, ..., WN)
- Checkpoint-managed state (.aho-checkpoint.json)
- Design doc → plan doc → execution → close sequence

If you are instead handling a one-shot `aho run "task"` invocation, read GEMINI-run.md instead.

## Iteration Contract

1. Read `.aho.json` and `.aho-checkpoint.json` at run start.
2. Read the iteration's design doc and plan doc from `artifacts/iterations/{iteration}/`.
3. Execute workstreams as defined in the plan. No scope invention.
4. Use `[x]` / `[ ]` sign-off format. Never `[y]` / `[n]`.
5. No git operations. Pillar 11.
6. No secret reads. aho-Sec001.
7. Emit workstream events via `aho iteration workstream {start,complete}`.
8. Write checkpoint state before any transition. Pillar 6.

## AcceptanceCheck Schema (landing W1-W2)

Starting 0.2.11, prose acceptance claims are no longer valid from W3 onward. The AcceptanceCheck framework replaces them with executable assertions.

**Dataclass contract:** `AcceptanceCheck(name: str, command: str, expected_exit: int, expected_pattern: str | None)` — a single verifiable assertion. `run()` executes the command via subprocess and returns `AcceptanceResult(passed: bool, actual_exit: int, actual_output: str, matched: bool)`.

**CLI integration:** `aho iteration workstream complete W<n> --acceptance-file path.json` loads AcceptanceResult records from a JSON file and embeds them in the workstream_complete event payload.

**Requirement:** Every workstream from W3 onward MUST emit `acceptance_results` in its workstream_complete event. If a workstream has no executable checks (unlikely post-W2), it must explicitly justify why in the run report. W0-W2 are exempt (bootstrap exception — the framework doesn't exist yet).

## Event Log Path (post-W7)

After W7 lands, `log_event()` writes to `~/.local/share/aho/events/aho_event_log.jsonl`. The `data/` path is deprecated. All new code reads/writes the new path. Rotation policy: size-based (100MB rotate, keep 3 generations). Bundle §8 gate, manifest scanner, and `.gitignore` are updated as part of W7.

If you are resuming mid-iteration before W7 completes, the old `data/aho_event_log.jsonl` path is still active. Check the checkpoint to determine which workstream you're in.

## Three-Session Boundaries + Hard Gate

0.2.11 executes across three sessions per ADR-045 hybrid iteration shape:

- **Session 1 (W0-W8):** Infrastructure backstop — AcceptanceCheck framework, gate fixes, event log relocation.
- **Session 2 (W9-W14):** Persona 3 validation — 4 fixture tasks exercising `aho run` end-to-end.
- **Session 3 (W15-W19):** Environment, hardening, audit, close.

**Hard gate at W8→W9 boundary:** All W0-W8 acceptance results must be green. If any workstream has status=FAIL, halt immediately: set `proceed_awaited=true` in checkpoint, send Telegram push notification, and wait for Kyle. Do not proceed to W9 under any circumstances with a failed backstop workstream.

## MCP-First Reminder

Every workstream declares `mcp_used` in the run report with justification. The value `none` is valid but must include a one-line reason per workstream (e.g., "none — Python primitive, no MCP domain match"). This is not optional — run reports missing mcp_used declarations are incomplete.

See GEMINI.md MCP Toolchain section for MUST-use rules and [INSTALLED-NOT-WIRED] protocol.

## Communication

Terse and direct. No preamble, no hedging. State blocks as capability gaps.

---

*GEMINI-iteration.md for aho Phase 0 — updated during 0.2.11 W0.*
