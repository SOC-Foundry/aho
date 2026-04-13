# Dispatch Decision — 0.2.14 W1

**Nemoclaw investigation result:** B — explicit role routing supported, model_id routing needs ~20 lines.

## Decision: Direct Ollama dispatch for cascade orchestrator

**Why not Nemoclaw:**
- Nemoclaw supports explicit role bypass but not explicit model_id
- All Nemoclaw sessions route to Qwen 3.5:9B (single model)
- Nemoclaw adds 18.5s latency per call (socket → OpenClaw → Qwen) vs ~8s for direct Ollama
- For smoke test (Qwen-solo), the indirection provides no value
- Adding model_id routing (~20 lines) is deferred to 0.2.15 when matrix testing needs it

**Architecture:**
- `src/aho/pipeline/dispatcher.py` — thin wrapper around Ollama HTTP API
- Orchestrator talks to dispatcher, never to Ollama directly (Pillar 4 honored)
- Dispatcher currently calls Ollama `/api/generate` with configurable model_id per role
- Future: swap dispatcher backend to Nemoclaw once model_id routing is added (0.2.15)

**Implications for 0.2.15+:**
- Nemoclaw ~20 line change lands in 0.2.15 W1
- Dispatcher backend becomes configurable: "ollama" or "nemoclaw"
- Cascade orchestrator unchanged — only dispatcher swaps
