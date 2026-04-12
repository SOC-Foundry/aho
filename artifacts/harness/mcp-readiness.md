# MCP Fleet Readiness — aho

**Generated:** 2026-04-12
**Source:** data/mcp_readiness.json (bin/aho-mcp smoke output)

## Server Status

| Server | cli_smoke | protocol_smoke | Last Successful |
|---|---|---|---|
| context7 | pass | pending | 2026-04-12T02:29:29Z |
| dart | pass | pending | 2026-04-12T02:29:32Z |
| firebase-tools | pass | pending | 2026-04-12T02:29:37Z |
| firecrawl | pass | pending | — |
| filesystem | pass | pending | — |
| memory | pass | pending | — |
| sequential-thinking | pass | pending | — |
| everything | pass | pending | — |
| playwright | pass | pending | — |

## Column Definitions

- **cli_smoke**: `bin/aho-mcp smoke` — verifies server binary exists and responds to basic CLI invocation
- **protocol_smoke**: MCP protocol-level round-trip (tool list request via stdio). Timestamp from `~/.local/share/aho/registries/mcp_smoke_log.jsonl`
- **Last Successful**: ISO 8601 timestamp of most recent successful smoke

## Notes

- 9/9 servers pass CLI smoke as of 0.2.8
- Protocol smoke column added 0.2.11 W8 — timestamps populate as smoke tests execute
- `aho mcp smoke` dispatches to `bin/aho-mcp smoke` which runs per-server CLI scripts
