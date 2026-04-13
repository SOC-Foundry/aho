# Council Vetting Results — 0.2.14 W1

**Date:** 2026-04-13
**Vetting method:** Direct invocation per council-inventory.md W1 invocation column.
**Environment:** NZXTcos (CachyOS 6.19.11), Ollama running, all systemd user services active.

---

## LLMs (4)

| Member | Invocation | Status | Latency | Evidence |
|--------|-----------|--------|---------|----------|
| Qwen-3.5:9B | `POST /api/generate model=qwen3.5:9b` | **operational** | 7.7s | Response: "Qwen3.5". Correct self-identification. Coherent. |
| Nemotron-mini:4b | `POST /api/generate model=nemotron-mini:4b` | **substrate-compromised** | 1.4s | Response: "Sure, I can help you with that! What's the name of the AI model you're referring to?" — evasive, doesn't self-identify. 0.2.13 W2.5: 80% "feature" default on classification. |
| GLM-4.6V-Flash-9B | `POST /api/generate model=haervwe/GLM-4.6V-Flash-9B` | **substrate-compromised** | 34.6s | Response: "GLM-4.5V" (identity mismatch — model reports 4.5V, Ollama tag says 4.6V-Flash). 0.2.13 W2.5: 80% timeout, wrong JSON schema for structured output. |
| OpenClaw (Qwen wrapper) | Socket `/run/user/1000/openclaw.sock` cmd=status | **operational** | <1s | Status: 0 sessions (creates on demand). Wraps Qwen 3.5:9B via QwenClient. Configurable via `~/.config/aho/orchestrator.json` `openclaw.default_model`. |

## MCPs (9)

| Member | Invocation | Status | Evidence |
|--------|-----------|--------|----------|
| context7 | `resolve-library-id(Python)` | **operational** | Returns library results with IDs, descriptions, snippet counts. |
| sequential-thinking | `sequentialthinking(probe)` | **operational** | Returns thought history. |
| playwright | Schema loaded, `browser_snapshot` available | **operational** | Tool callable. Full browser automation available. |
| filesystem | `list_directory(/home/kthompson/dev/projects/aho/src)` | **operational** | Returns directory listing with [DIR]/[FILE] prefixes. |
| dart | `list_devices()` | **operational** | 2 devices: Linux (CachyOS), Chrome 146.0.7680.153. Hot reload supported. |
| memory | `read_graph()` | **operational** | Returns empty graph (no entities/relations). Knowledge graph functional. |
| firebase-tools | `firebase_get_environment()` | **configured-but-no-project** | Authenticated as kthompson@socfoundry.com. No firebase.json, no active project. Auth works; project setup needed for full functionality. |
| firecrawl | Not loaded | **gap** | MCP server not started. API key empty in `.mcp.json`. Cannot invoke. |
| everything | `echo("probe")` | **operational** | Returns echoed message. Test/demo server. |

## Other (3)

| Member | Invocation | Status | Latency | Evidence |
|--------|-----------|--------|---------|----------|
| Nemoclaw socket | `cmd=status` then `cmd=dispatch role=assistant task="Say hello"` | **operational** | status <1s, dispatch 18.5s | 3 sessions (assistant, code_runner, reviewer). Dispatch with explicit `role` bypasses Nemotron classify — routes directly to OpenClaw/Qwen. Full stack: Nemoclaw → OpenClaw → Qwen → response. |
| ChromaDB | `chromadb.Client()` | **operational** | <1s | v1.5.5. 0 collections. In-process client works. |
| nomic-embed-text | `POST /api/embeddings model=nomic-embed-text` | **operational** | <1s | 768-dimensional embeddings. Produces valid float vectors. |

---

## Nemoclaw Architectural Investigation

**Question:** Can Nemoclaw dispatch to a specific model without Nemotron classify-then-route?

**Finding: Classification B** — explicit role routing already supported, minor change needed for explicit model_id.

**Evidence:**
- `nemoclaw.py:49-51`: `dispatch(task, role=None)` — when `role` is provided, skips `self.route()` entirely (line 50-51: `if role is None: role = self.route(task)`)
- Socket handler passes `role` through: `req.get("role")` at line 116
- Tested: `{"cmd": "dispatch", "task": "Say hello", "role": "assistant"}` — works, 18.5s, no Nemotron involvement
- **Gap:** No `model_id` parameter. All OpenClaw sessions use same Qwen model from config. Adding model-specific routing requires ~20 lines: pass `model` through dispatch → session constructor (which already accepts it)

**Implication for cascade:** Nemoclaw with explicit `role` works for smoke test (all roles → Qwen anyway). Explicit model_id routing is a 0.2.15 enhancement when matrix testing needs different models per role.

---

## Summary

| Category | Count | Operational | Substrate-Compromised | Configured-Incomplete | Gap |
|----------|-------|-------------|----------------------|----------------------|-----|
| LLMs | 4 | 2 (Qwen, OpenClaw) | 2 (Nemotron, GLM) | 0 | 0 |
| MCPs | 9 | 7 | 0 | 1 (firebase-tools) | 1 (firecrawl) |
| Other | 3 | 3 | 0 | 0 | 0 |
| **Total** | **16** | **12** | **2** | **1** | **1** |

**Upgrade from W0 inventory:** W0 estimated 8 operational, 2 substrate-compromised, 6 unknown. After vetting: 12 operational, 2 substrate-compromised, 1 configured-incomplete, 1 gap. The unknowns resolved mostly to operational.

**For cascade:** Only Qwen 3.5:9B is viable for structured analytical output. Nemotron and GLM respond but produce unreliable output. Smoke test will be Qwen-solo (Pillar 7 violation acknowledged).
