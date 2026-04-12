# Council Inventory - 0.2.12 W1

| Name | Kind | Declared Capability | Config Source | Status |
|---|---|---|---|---|
| Qwen-3.5:9B | llm | The primary artifact engine. | artifacts/harness/model-fleet.md | unknown |
| Nemotron-mini:4B | llm | The classification and routing engine. | artifacts/harness/model-fleet.md | unknown |
| GLM-4.6V-Flash-9B | llm | The vision and multimodal reasoning engine. | artifacts/harness/model-fleet.md | unknown |
| ChromaDB | daemon | The vector memory (RAG) backend. | artifacts/harness/model-fleet.md | unknown |
| Nomic-Embed-Text | daemon | The universal embedding model. | artifacts/harness/model-fleet.md | unknown |
| OpenClaw | daemon | Agent daemon running OpenClaw | artifacts/harness/agents-architecture.md | unknown |
| NemoClaw | daemon | Agent daemon running NemoClaw | artifacts/harness/agents-architecture.md | operational |
| mcp-firebase-tools | mcp_server | Firebase/Firestore operations | artifacts/harness/mcp-fleet.md | unknown |
| mcp-context7 | mcp_server | Context-aware documentation lookup | artifacts/harness/mcp-fleet.md | operational |
| mcp-firecrawl | mcp_server | Web scraping and content extraction | artifacts/harness/mcp-fleet.md | unknown |
| mcp-playwright | mcp_server | Browser automation and testing | artifacts/harness/mcp-fleet.md | operational |
| mcp-dart | mcp_server | Flutter/Dart development tooling (official Dart team server) | artifacts/harness/mcp-fleet.md | unknown |
| mcp-server-filesystem | mcp_server | Local filesystem operations | artifacts/harness/mcp-fleet.md | operational |
| mcp-server-memory | mcp_server | Persistent memory store | artifacts/harness/mcp-fleet.md | unknown |
| mcp-server-sequential-thinking | mcp_server | Chain-of-thought reasoning | artifacts/harness/mcp-fleet.md | operational |
| mcp-server-everything | mcp_server | Reference/test server | artifacts/harness/mcp-fleet.md | unknown |
| evaluator-agent | evaluator | Evaluator agent role | src/aho/agents/roles/evaluator_agent.py | gap: parsing logic converts real reviews to rubber stamps |
