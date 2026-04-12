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

## MCP-First Mandate

When a workstream's domain matches an available MCP server, use the MCP tool. If no MCP domain matches, justify with one-line in the run report mcp_used column.

## Communication

Terse and direct. No preamble, no hedging. State blocks as capability gaps.
