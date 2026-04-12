# D1 Diagnosis: MCP Utilization Gap

**Iteration:** 0.2.8 W1
**Date:** 2026-04-11
**Diagnosis type:** Discovery (no code output)

---

## 1. Predicted Finding

Zero MCP server invocations across any prior iteration. All 9 servers installed since 0.2.3; none exercised during agent execution across five iterations (0.2.3 through 0.2.7).

## 2. Actual Finding

**Confirmed.** Zero MCP usage. Evidence:

### 2a. Event log — zero MCP events

`data/aho_event_log.jsonl` contains zero entries with any MCP server name (context7, playwright, firecrawl, flutter-mcp, firebase-tools, server-filesystem, server-memory, server-sequential-thinking, server-everything). Not a single MCP tool call has been logged across the entire project history.

### 2b. Source code — MCP references are declarations, not invocations

MCP server names appear in exactly three source files, all declarative:
- `src/aho/doctor.py:267-272` — hardcoded list for `npm list -g` presence check
- `src/aho/dashboard/aggregator.py:183-191` — hardcoded list for dashboard status display
- `src/aho/postflight/mcp_canonical_registry_verify.py:11-19` — hardcoded list for registry gate

None of these files invoke an MCP server. They verify installation or display status. The servers are verified-present but never called.

### 2c. Iteration artifacts — no MCP tool mentions in any run report

Searched all run reports and bundles in `artifacts/iterations/`. MCP appears only in:
- Infrastructure descriptions ("MCP server fleet installed")
- Component coverage matrices (status: "ok" means npm-installed, not exercised)
- The 0.1.7 run report's prescriptive text about `/bin` wrappers for MCP (aspiration, not execution)
- The 0.1.8/0.1.9/0.1.10/0.1.12 bundle gotcha format note: "Use `-` if no MCP tool was called"

Zero evidence of any MCP tool being called during any workstream execution.

### 2d. Iterations since installation

MCP fleet landed in 0.2.3 W1. Five full iterations have shipped since (0.2.3, 0.2.4, 0.2.5, 0.2.6, 0.2.7). The fleet has been installed, verified, counted, displayed, gated, and dashboard-rendered — but never used.

## 3. Root Cause Analysis

Two distinct root causes, not one:

### Root Cause 1: No agent instructions to use MCP

CLAUDE.md and GEMINI.md contain zero references to MCP servers. The First Actions Checklist does not include MCP. The "What NOT to Do" section does not say "don't ignore MCP tools." No harness file tells agents when or how to invoke MCP servers. The servers exist on disk but are invisible to agent instructions.

**Fix:** W2 adds "MCP Toolchain" section with MUST-strength rules.

### Root Cause 2: MCP servers are not wired into agent tool surfaces

This is the finding W1 itself surfaced: the 9 MCP servers are installed globally via npm (`sudo npm install -g`) but **none are configured as MCP server connections in Claude Code**. Specifically:

- `~/.claude/settings.json` contains only `skipDangerousModePermissionPrompt`. No `mcpServers` key.
- No project-level `.mcp.json` exists in the repo root.
- ToolSearch for `mcp filesystem` and `mcp context7` returns zero matches — these tools are not available to Claude Code.
- The `.mcp.json` files exist in `~/.claude/plugins/marketplaces/` for context7, playwright, and firebase, but none are enabled.

**The MCP-first mandate cannot be honored until the servers are wired as MCP connections.** Installing an npm package puts the binary on PATH. Making it available as an MCP tool requires configuring it in the agent's MCP server list (e.g., Claude Code's `mcpServers` in settings or project `.mcp.json`).

This is a deeper gap than "agents forgot to use MCP." The gap is: **agents literally cannot use MCP because the servers aren't in their tool surface.** The MUST rules in W2 will be aspirational until the wiring exists.

**Fix:** This needs a concrete wiring step — either a project `.mcp.json` or Claude Code settings update — before W3 smoke scripts can test MCP invocation from within Claude Code. W3's fish scripts can invoke MCP servers via CLI (`npx` or direct binary), which tests server health but does not test agent-integrated MCP usage.

## 4. W1 Self-Assessment: MCP-First Compliance

The plan mandated MCP-first execution where applicable. W1 is a diagnosis workstream. Two MCP servers were candidates:

| Server | Potential use in W1 | Could it be used? | Was it used? |
|---|---|---|---|
| @modelcontextprotocol/server-filesystem | grep/glob pass over project files | No — not wired as MCP tool in Claude Code | No |
| @upstash/context7-mcp | reference lookups for MCP protocol docs | No — not wired as MCP tool in Claude Code | No |

**Verdict:** MCP tools were not used in W1 because they are structurally unavailable, not because the agent chose bash over MCP. The diagnosis itself is evidence of the gap it was designed to find. Built-in Claude Code tools (Grep, Glob, Read) were used instead — these are the only search/filesystem tools in the agent's actual tool surface.

This is the first concrete proof that the MCP-first mandate requires a **wiring** step (server configuration), not just an **instruction** step (CLAUDE.md rules). W2's MUST rules are necessary but not sufficient. The wiring gap should be surfaced as a blocker or pre-req for W3.

## 5. Recommendations

1. **W2 proceeds as planned** — MUST rules in CLAUDE.md/GEMINI.md establish the behavioral contract.
2. **Wiring step needed before W3** — configure at least the 9 MCP servers as connections so agents can invoke them natively. Without this, W3 smoke scripts test CLI invocability (server health) but not agent-integrated MCP usage. Both are valuable but they test different things.
3. **W3 scope clarification** — the plan says "fish scripts making MCP calls." If "MCP call" means invoking the server via its MCP protocol (stdio JSON-RPC), a Python helper is needed per server. If it means "verify the server binary runs and responds," CLI invocation suffices. The wiring gap makes agent-native MCP calls impossible for W3 regardless — the smoke scripts will run as shell commands, not as MCP tool invocations from within an agent session.
4. **New gotcha candidate:** aho-G068 — "installed ≠ wired: npm-global MCP packages require explicit agent configuration to appear in tool surfaces." This is distinct from G066 (declared tools must be exercised) because it identifies WHY they weren't exercised.

---

**W3 correction (fleet composition):** The canonical fleet at 0.2.8 close is 9 servers, not 8. `flutter-mcp` (npm wrapper for a nonexistent PyPI package — broken upstream) was replaced with `dart mcp-server` (official Dart team MCP server, bundled with Dart SDK 3.9+). The dart server exposes code analysis, formatting, pub management, test execution, hot reload, and symbol resolution. 8 servers are npm-global packages; 1 (dart) is SDK-bundled. The `mcp_packages` list in `bin/aho-mcp` contains 8 npm entries; the dart server is verified via `dart --version` instead.

---

*mcp-utilization-gap.md — 0.2.8 W1 diagnosis, W3 correction appended.*
