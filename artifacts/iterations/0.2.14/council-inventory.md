# Council Inventory — 0.2.14

**Purpose:** W1 vetting target. Every declared council member listed with current claimed status.
**Sources:** 0.2.12 council audits, .mcp.json, carry-forwards, design docs.

---

## LLMs (4)

| Member | Declared Source | Claimed Status (0.2.12) | W1 Invocation Method |
|--------|----------------|------------------------|---------------------|
| Qwen-3.5:9B | artifacts/harness/model-fleet.md, 0.2.12 W1 audit | operational (artifact generation) | `ollama run qwen3.5:9b "Hello, identify yourself"` |
| Nemotron-mini:4b | artifacts/harness/model-fleet.md, 0.2.12 W2 audit, 0.2.13 W2 fix | operational (classification) but substrate-compromised (80% "feature" default) | `ollama run nemotron-mini:4b "Hello, identify yourself"` |
| GLM-4.6V-Flash-9B | artifacts/harness/model-fleet.md, 0.2.12 W3 audit, 0.2.13 W1 fix | operational (evaluation) but substrate-compromised (80% timeout, wrong JSON schema) | `ollama run glm4:9b "Hello, identify yourself"` |
| OpenClaw underlying model | 0.2.12 W5 (deferred), carry-forwards | unknown — never audited. Underlying model not identified. | Resolve model identity via repo inspection, then invoke via OpenClaw socket or direct Ollama. |

## MCPs (9 declared in .mcp.json)

| Member | Declared Source | Claimed Status | W1 Invocation Method |
|--------|----------------|---------------|---------------------|
| context7 | .mcp.json | operational (active in Claude Code sessions) | MCP tool call: `mcp__context7__resolve-library-id` |
| sequential-thinking | .mcp.json | operational (active in Claude Code sessions) | MCP tool call: `mcp__sequential-thinking__sequentialthinking` |
| playwright | .mcp.json | operational (active in Claude Code sessions) | MCP tool call: `mcp__playwright__browser_navigate` |
| filesystem | .mcp.json | operational (active in Claude Code sessions) | MCP tool call: `mcp__filesystem__list_directory` |
| dart | .mcp.json | operational (active in Claude Code sessions) | MCP tool call: `mcp__dart__list_devices` |
| memory | .mcp.json | operational (active in Claude Code sessions) | MCP tool call: `mcp__memory__read_graph` |
| firebase-tools | .mcp.json | unknown (requires auth state) | MCP tool call: `mcp__firebase-tools__firebase_list_projects` |
| firecrawl | .mcp.json | unknown (API key empty in .mcp.json) | MCP tool call — will likely fail without API key |
| everything | .mcp.json | operational (test/demo server) | MCP tool call: `mcp__everything__echo` |

## Other (3)

| Member | Declared Source | Claimed Status | W1 Invocation Method |
|--------|----------------|---------------|---------------------|
| Nemoclaw socket | carry-forwards, ADR-047 | unknown — socket existence unverified since 0.2.10 | Check socket at `/run/user/$UID/openclaw.sock`, attempt classify call |
| ChromaDB | data/chroma/, 0.2.12 inventory | unknown — operational status not verified | Attempt connection to local ChromaDB instance |
| nomic-embed-text | 0.2.12 inventory, embedding model for ChromaDB | unknown — never independently verified | `ollama run nomic-embed-text "test embedding"` |

---

## Summary

| Category | Count | Operational | Substrate-Compromised | Unknown |
|----------|-------|-------------|----------------------|---------|
| LLMs | 4 | 1 (Qwen) | 2 (Nemotron, GLM) | 1 (OpenClaw) |
| MCPs | 9 | 7 | 0 | 2 (firebase-tools, firecrawl) |
| Other | 3 | 0 | 0 | 3 |
| **Total** | **16** | **8** | **2** | **6** |

Note: MCP "operational" status is based on their presence in active Claude Code sessions. W1 vetting will invoke each independently to confirm.
