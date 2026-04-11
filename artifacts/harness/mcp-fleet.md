# aho MCP Fleet — Architectural Specification

**Version:** 0.2.3
**Date:** 2026-04-11
**Scope:** Global MCP server fleet for aho agent orchestration

---

## 1. Overview

The MCP (Model Context Protocol) fleet provides standardized tool access for aho agents. All servers are installed globally via npm and managed through `bin/aho-mcp`. Each server exposes capabilities that agents can invoke through the wrapper surface (Pillar 4).

## 2. Server Catalog

| # | Package | Component Name | Role |
|---|---|---|---|
| 1 | firebase-tools | mcp-firebase-tools | Firebase/Firestore operations |
| 2 | @upstash/context7-mcp | mcp-context7 | Context-aware documentation lookup |
| 3 | firecrawl-mcp | mcp-firecrawl | Web scraping and content extraction |
| 4 | @playwright/mcp | mcp-playwright | Browser automation and testing |
| 5 | flutter-mcp | mcp-flutter | Flutter app development tooling |
| 6 | @modelcontextprotocol/server-filesystem | mcp-server-filesystem | Local filesystem operations |
| 7 | @modelcontextprotocol/server-github | mcp-server-github | GitHub API operations |
| 8 | @modelcontextprotocol/server-google-drive | mcp-server-google-drive | Google Drive file access |
| 9 | @modelcontextprotocol/server-slack | mcp-server-slack | Slack messaging integration |
| 10 | @modelcontextprotocol/server-fetch | mcp-server-fetch | HTTP fetch operations |
| 11 | @modelcontextprotocol/server-memory | mcp-server-memory | Persistent memory store |
| 12 | @modelcontextprotocol/server-sequential-thinking | mcp-server-sequential-thinking | Chain-of-thought reasoning |

## 3. Installation

```fish
# Install all MCP servers
bin/aho-mcp install

# Verify installation
bin/aho-mcp doctor
```

All packages install globally via `sudo npm install -g`. This is a one-time capability gap per clone.

## 4. Per-Server Role

- **firebase-tools**: Firestore CRUD for TripleDB and project state persistence.
- **context7**: Documentation RAG — fetches library docs on demand for agent context.
- **firecrawl**: Structured web extraction for research tasks.
- **playwright**: End-to-end browser testing for app/ builds.
- **flutter**: Flutter widget scaffolding and build tooling.
- **server-filesystem**: Safe, sandboxed file I/O for agent workdirs.
- **server-github**: PR creation, issue management, repo queries.
- **server-google-drive**: Document retrieval from shared drives.
- **server-slack**: Notification delivery to team channels.
- **server-fetch**: Generic HTTP client for API integrations.
- **server-memory**: Cross-session persistent key-value store.
- **server-sequential-thinking**: Structured reasoning for complex multi-step tasks.

## 5. Doctor Checks

`aho doctor` includes `_check_mcp_fleet()` which verifies all 12 packages are present via `npm list -g --depth=0`. Missing packages are reported individually.

`bin/aho-mcp doctor` provides the same check as a standalone command.

## 6. Future Extensions

- Version pinning per server (Phase 1)
- Per-agent MCP access control (which agents can use which servers)
- MCP server health monitoring via heartbeat spans
- Cross-clone MCP fleet sync via aho.run

---

*MCP fleet specification for aho Phase 0 — authored during 0.2.3 W1.*
