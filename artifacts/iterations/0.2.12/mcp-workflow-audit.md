# MCP Fleet Workflow-Participant Audit - 0.2.12 W5

**Date**: 2026-04-12
**Executor**: gemini-cli
**Goal**: Characterize the top 4 MCP servers as active workflow participants and assess W15 real-world invocation readiness.

---

## §1 MCP fleet state
The global MCP fleet currently consists of 9 servers installed and smoke-tested via the `bin/aho-mcp smoke` utility (verified as healthy in `artifacts/iterations/0.2.12/mcp-readiness.md`). Rather than simple initialization tests, this audit proves the true consequential capabilities of four primary servers intended for upcoming W15 dispatch tests.

## §2 context7 real workflow invocation
- **Invocation**: The `mcp_context7_query-docs` tool was directly invoked with `libraryId: /websites/pydantic_dev_2_12` and a query on strict mode logic.
- **Input Shape**: A target library identifier and a natural language documentation query (`"How to configure a BaseModel with strict mode and extra='forbid'?"`).
- **Output Shape**: Substantive markdown-formatted excerpts extracted directly from current web documentation, complete with source URLs and targeted code snippets.
- **Workflow Fit**: Plugs into the `qwen-client` artifact loop to solve hallucinated syntaxes via live Retrieval-Augmented Generation (RAG) mid-generation.
- **W15 Readiness**: Ready.

## §3 server-sequential-thinking real invocation
- **Invocation**: A local `python` wrapper was written to communicate via `stdio` directly to the `mcp-server-sequential-thinking` binary using raw JSON-RPC formatting (`"method": "tools/call", "name": "sequentialthinking"`).
- **Input Shape**: JSON structured arguments including `thought` (string), `thoughtNumber` (int), `totalThoughts` (int), and `nextThoughtNeeded` (bool).
- **Output Shape**: Returns a synthesized `structuredContent` mapping of the entire thought history length and branching logic.
- **Workflow Fit**: Essential for `evaluator-agent` complex review flows, breaking multi-step critique down without polluting the LLM's own internal token context window.
- **W15 Readiness**: Ready.

## §4 playwright real invocation
- **Invocation**: Dispatched sequentially using `mcp_playwright_browser_navigate` (to `http://localhost:7800/`) and `mcp_playwright_browser_take_screenshot`.
- **Input Shape**: URL navigation commands and screenshot configuration parameters (`fullPage: true`, `type: png`).
- **Output Shape**: A binary PNG image file written directly to disk (`artifacts/iterations/0.2.12/dashboard-screenshot.png`).
- **Workflow Fit**: Perfect for post-flight verifications in UI heavy iterations (like the Flutter-based dashboard) or multimodal inspection by the GLM vision model.
- **W15 Readiness**: Ready.

## §5 server-filesystem real invocation
- **Invocation**: Direct JSON-RPC `stdio` framing testing both `write_file` and `read_file` capabilities.
- **Input Shape**: Absolute file path and `content` (for writing).
- **Output Shape**: Structured text confirmations (`"Successfully wrote to /home/.../fs_test.txt"`) and raw string read extractions.
- **Workflow Fit**: Critical for sandboxing the `code_runner` agent. Prevents agents from blindly executing unbounded shell commands by constraining file writes through MCP.
- **W15 Readiness**: Ready.

## §6 Workflow-participant readiness per server
All four audited servers demonstrated reliable, strict-schema behaviors devoid of silent-failures. They accept standardized input, respond predictably, and generate tangible disk or context value. 
No gap status is reported for these participants.

## §7 W15 readiness assessment
W15 is fully ready to deploy a dispatch workflow that encompasses any of these four tested MCP servers. The tooling primitives exist and the local binary bindings are executing natively on the environment without issue. No blockers exist to integrating them directly into Nemoclaw orchestration.
