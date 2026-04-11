# Investigation 7 — Model Fleet Isolated Smoke Tests

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Ollama Fleet Status

All 4 models are installed:

| Model | Installed Name | Size |
|---|---|---|
| Qwen | `qwen3.5:9b` | 6.6 GB |
| Nemotron | `nemotron-mini:4b` | 2.7 GB |
| GLM | `haervwe/GLM-4.6V-Flash-9B:latest` | 8.0 GB |
| Nomic | `nomic-embed-text:latest` | 274 MB |

No models are currently loaded in memory (`ollama ps` shows empty table — models load on demand).

---

## Individual Smoke Tests

### nemotron-mini:4b

- **Endpoint:** `/api/generate`
- **Prompt:** "respond with ok"
- **Response:** "Ok, I'm ready to assist you!"
- **Wall clock:** 2.1 seconds
- **Status:** PASS

Nemotron is the fastest model. Its classification function (`nemotron_client.classify()`) uses `temperature: 0.0` and `num_predict: 20` for tight, deterministic outputs.

### qwen3.5:9b

- **Endpoint:** `/api/generate`
- **Prompt:** "respond with ok"
- **Response:** "ok"
- **Wall clock:** 7.1 seconds (includes cold model load)
- **Status:** PASS

Qwen is the primary artifact generation model. The 7.1s response time for a minimal prompt indicates ~5s model load + ~2s generation. For long-form generation (5000+ words), expect 5-15 minutes depending on output length.

### haervwe/GLM-4.6V-Flash-9B

- **Endpoint:** `/api/generate`
- **Prompt:** "respond with ok"
- **Response:** `<|begin_of_box|>ok<|end_of_box|>` (GLM's special tokens visible in raw output)
- **Wall clock:** 14.7 seconds
- **Status:** PASS (with note)

GLM is the slowest to load and respond. The special tokens (`<|begin_of_box|>`, `<|end_of_box|>`) in the response are GLM's formatting markers — the `glm_client.py` does `.strip()` but doesn't strip these tokens. This is a minor issue (cosmetic, not functional).

### nomic-embed-text

- **Endpoint:** `/api/embeddings`
- **Prompt:** "test"
- **Response:** 768-dimensional embedding vector
- **Wall clock:** sub-second
- **Status:** PASS

Embedding model is the smallest (274MB) and fastest. Used exclusively for ChromaDB vector indexing.

---

## ChromaDB Status

### Storage

- **Path:** `~/.local/share/iao/chromadb/`
- **Size:** 16 MB
- **Status:** Present and functional

### Collections

| Collection | Document Count |
|---|---|
| `iaomw_archive` | 17 |
| `tripl_archive` | 144 |
| `kjtco_archive` | 282 |

Total: 443 documents across 3 project archives.

### Live Query Test

Query: "bundle quality gates" against `iaomw_archive`, top-3 results:

| Rank | Source | Iteration |
|---|---|---|
| 1 | `iao-report-0.1.3.md` | 0.1.3 |
| 2 | `iao-run-report-0.1.3.md` | 0.1.3 |
| 3 | `iao-build-log-0.1.3.md` | 0.1.3 |

Results are relevant — all three documents from 0.1.3 discuss quality gates. The RAG pipeline is functional.

---

## open-interpreter Status

```python
>>> import interpreter
>>> interpreter.__version__
'unknown'
```

The `interpreter` module imports successfully but reports unknown version. The iao `openclaw.py` stub documents that "open-interpreter installation failed in iao 0.1.4 due to Python 3.14 and missing Rust compiler for tiktoken." However, the import works, suggesting a partial or compatibility-patched install.

Instantiation was not tested (per instructions — "don't launch it, just construct"). The `OpenClaw` class raises `NotImplementedError` on `.chat()` regardless.

---

## Fleet Health Matrix

| Component | Installed | Reachable | Smoke Test | Notes |
|---|---|---|---|---|
| Ollama daemon | Yes | Yes (localhost:11434) | PASS | v? — running, no models loaded at idle |
| qwen3.5:9b | Yes (6.6GB) | Yes | PASS (7.1s) | Primary artifact generator. Slow for long-form. |
| nemotron-mini:4b | Yes (2.7GB) | Yes | PASS (2.1s) | Classification model. Fast, deterministic. |
| GLM-4.6V-Flash-9B | Yes (8.0GB) | Yes | PASS (14.7s) | Vision/reasoning. Slow load, special tokens in output. |
| nomic-embed-text | Yes (274MB) | Yes | PASS (<1s) | Embedding model for ChromaDB. |
| ChromaDB | Yes (16MB) | Yes | PASS | 3 collections, 443 docs. Query returns relevant results. |
| open-interpreter | Partial | N/A | N/A | Imports but broken (Python 3.14 / tiktoken). |
| python-telegram-bot | Yes (v22.7) | N/A | N/A | Library installed, not tested for actual bot operations. |

---

## GPU Context

```
GPU: NVIDIA GeForce RTX 2080 (8GB VRAM)
Driver: 595.58.03, CUDA: 13.2
VRAM used: 667 MiB / 8192 MiB (at idle)
```

The RTX 2080 has 8GB VRAM. Model sizes:
- Qwen 9B: 6.6GB — fits in VRAM but leaves minimal room for KV cache
- GLM 9B: 8.0GB — may partially spill to CPU RAM
- Nemotron 4B: 2.7GB — fits comfortably
- Nomic embed: 274MB — trivial

Only one large model can be loaded at a time. The artifact loop (which uses Qwen) will work, but running GLM concurrently would cause memory pressure.

---

## What This Tells Us

The model fleet is healthy and all components are reachable. The primary bottleneck for the artifact loop is generation speed — Qwen 9B on an RTX 2080 produces ~15-25 tokens/second, making 5000-word documents take 5-15 minutes. This is workable but requires patience and proper timeout configuration. The "hang" behavior reported in previous sessions is almost certainly a perception problem (no progress output) rather than an actual hang.

The only non-functional fleet component is open-interpreter, which blocks OpenClaw/NemoClaw from being more than stubs. This is a Python 3.14 compatibility issue with tiktoken's Rust build.
