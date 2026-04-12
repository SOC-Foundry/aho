# MCP Wiring — aho

**Version:** 0.2.8
**Date:** 2026-04-11
**Scope:** How MCP servers become agent-reachable tools, not just npm-installed packages

---

## 1. What .mcp.json Does

Claude Code reads `.mcp.json` from the project root at **session start**. Each entry under `mcpServers` launches a subprocess speaking the MCP stdio protocol. The server's tools then appear in the agent's tool surface alongside built-in tools (Read, Edit, Bash, etc.).

Without `.mcp.json`, npm-global MCP packages are installed on the system but invisible to the agent. This is the "installed != wired" gap documented in aho-G068.

`.mcp.json` is **not hot-reloaded**. Changes require restarting the Claude Code session.

## 2. The 9 Servers and Their Wired Commands

| Server Key | npm Package | Command | Args | Env |
|---|---|---|---|---|
| firebase-tools | firebase-tools | `firebase mcp` | — | — |
| context7 | @upstash/context7-mcp | `context7-mcp` | — | — |
| firecrawl | firecrawl-mcp | `firecrawl-mcp` | — | `FIRECRAWL_API_KEY` required |
| playwright | @playwright/mcp | `playwright-mcp` | — | — |
| dart | Dart SDK (bundled) | `dart mcp-server` | — | — |
| filesystem | @modelcontextprotocol/server-filesystem | `mcp-server-filesystem` | `/home/kthompson/dev/projects/aho` | — |
| memory | @modelcontextprotocol/server-memory | `mcp-server-memory` | — | — |
| sequential-thinking | @modelcontextprotocol/server-sequential-thinking | `mcp-server-sequential-thinking` | — | — |
| everything | @modelcontextprotocol/server-everything | `mcp-server-everything` | — | — |

**Notes:**

- `firebase-tools` is invoked via `firebase mcp` subcommand (not `lib/bin/mcp.js`). Requires `firebase login` for full functionality. Fixed in W3.
- `dart` is the official Dart team MCP server bundled with Dart SDK 3.9+. Replaces the broken `flutter-mcp` npm package (upstream PyPI package never published). Invoked via `dart mcp-server`. No additional install required — uses the dart binary from Flutter SDK.
- `firecrawl` requires `FIRECRAWL_API_KEY` env var. Without it, the server starts but fails on any API call.
- `filesystem` is restricted to the aho project directory. On P3, the path will need updating to match that machine's clone location.
- `dart mcp-server` requires stdin to stay open while processing (does not respond if stdin closes immediately after sending the request).

## 3. Verifying Wiring Landed

After restarting Claude Code in the aho project directory:

```fish
# Inside Claude Code, ask the agent to run:
# ToolSearch for "filesystem" — should return mcp-server-filesystem tools
# ToolSearch for "context7" — should return context7-mcp tools
# ToolSearch for "playwright" — should return playwright-mcp tools
```

Or from the CLI, verify the config parses:

```fish
python3 -c "import json; d=json.load(open('.mcp.json')); print(f'{len(d[\"mcpServers\"])} servers wired')"
```

Expected: `9 servers wired`.

**Capability gap:** `.mcp.json` is read at session start, not hot-reloaded. The session that created this file cannot verify wiring in-session. Kyle must restart Claude Code and run ToolSearch to confirm the servers appear as tools.

## 4. User-Level Alternative

For non-project sessions (outside the aho repo), servers can be wired in `~/.claude/settings.json` under the `mcpServers` key using the same format. User-level wiring applies to all Claude Code sessions regardless of working directory.

The aho harness uses project-level `.mcp.json` exclusively because:
- It travels with the repo (`git clone` on P3 gets the wiring for free)
- It does not assume or modify user-level config
- Different projects can wire different server sets

User-level wiring is Kyle's personal config and out of scope for the harness.

## 5. Installed != Wired (aho-G068)

Three distinct states for an MCP server:

| State | What it means | How to detect |
|---|---|---|
| **Installed** | npm package exists globally | `npm list -g <package>` succeeds |
| **Wired** | `.mcp.json` or settings.json entry exists | JSON key present in config |
| **Available** | Server tools appear in agent tool surface | ToolSearch returns tools |

Prior to 0.2.8 W2.5, all 9 servers were **installed** but neither **wired** nor **available**. Dashboard "ok" status checked installation only. The MCP-first mandate requires all three states.

`aho doctor` checks installation. The new `mcp_sources_aligned` gate (W7) will check wiring against `components.yaml`. Agent-side availability depends on session startup successfully launching each server subprocess.

## 6. W3 Startup Fixes

Two servers failed to start after W2.5 wiring. Diagnosed and fixed in W3:

### firebase-tools — wrong entry point

**Symptom:** Server absent from Claude Code tool surface after session restart.
**Root cause:** `.mcp.json` pointed at `node /usr/lib/node_modules/firebase-tools/lib/bin/mcp.js` — this file exists but does not produce MCP stdio output. The correct entry point is the `firebase mcp` subcommand.
**Fix:** Changed `.mcp.json` entry to `"command": "firebase", "args": ["mcp"]`. CLI smoke passes. Protocol smoke deferred to next session restart (hot-reload limitation).

### flutter-mcp — upstream broken, replaced with dart mcp-server

**Symptom:** npm wrapper runs `python3 -m pip install flutter-mcp` on every invocation. Arch Linux PEP 668 rejects system-wide pip installs.
**Root cause:** The `flutter-mcp` npm package is a thin Node.js wrapper around a Python pip package that **does not exist on PyPI**. Both `pipx install flutter-mcp` and `pip install flutter-mcp` fail with "No matching distribution found." The package is broken upstream.
**Fix:** Replaced with the official Dart team MCP server (`dart mcp-server`), bundled with Dart SDK 3.9+. Kyle's Dart SDK is 3.11.4 — well past the minimum. The dart server exposes code analysis, formatting, pub management, test execution, hot reload, and symbol resolution. It is the canonical Flutter/Dart MCP server per https://docs.flutter.dev/ai/mcp-server.
**Status:** Resolved. Fleet remains at 9 servers.

## 7. W3 Protocol Smoke Verification Log (0.2.8)

Agent-native MCP invocations from Claude Code session, one per server:

| Server | Tool called | Result |
|---|---|---|
| filesystem | `mcp__filesystem__list_directory` | Listed 9 files in mcp-smoke/ |
| memory | `mcp__memory__read_graph` | Returned empty knowledge graph |
| everything | `mcp__everything__echo` | Echoed `aho-0.2.8-W3-smoke` |
| context7 | `mcp__context7__resolve-library-id` | Resolved python-telegram-bot (430 snippets) |
| sequential-thinking | `mcp__sequential-thinking__sequentialthinking` | Processed 1-step thought |
| playwright | `mcp__playwright__browser_snapshot` | Snapshot of about:blank |
| firecrawl | `mcp__firecrawl__firecrawl_scrape` | Scraped example.com, returned markdown |
| firebase-tools | — | .mcp.json fix applied in W3; needs session restart to verify |
| dart | — | .mcp.json entry added in W3; needs session restart to verify |

---

*mcp-wiring.md v0.2.8 — aho harness artifact.*
