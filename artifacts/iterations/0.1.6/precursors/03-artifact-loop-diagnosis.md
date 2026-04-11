# Investigation 3 — Artifact Loop Diagnosis

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Background

The Qwen artifact loop (`iao iteration design`, `iao iteration plan`, etc.) is suspected broken or extremely slow. A previous Gemini session ran `iao iteration design 0.1.5` and it produced output after ~10 minutes. The same session ran `iao iteration plan 0.1.5` and it hung with no output for an indefinite time. This investigation characterizes the failure mode.

---

## Layer-by-Layer Diagnostic Results

### Layer 1: Ollama Reachable

- **Status:** PASS
- Ollama daemon running at `http://localhost:11434`
- 4 models installed: `nomic-embed-text:latest`, `haervwe/GLM-4.6V-Flash-9B:latest`, `nemotron-mini:4b`, `qwen3.5:9b`
- No models currently loaded in memory (`ollama ps` shows empty table)

### Layer 2: Qwen Tiny Prompt

- **Status:** PASS
- Prompt: "respond with ok"
- Response: "ok"
- Wall clock: **7.1 seconds** (includes model load time)
- This is the cold-start time. Subsequent calls within the keep-alive window would be faster.

### Layer 3: Nemotron Classification

- **Status:** PASS
- Response: "Ok, I'm ready to assist you!"
- Wall clock: **2.1 seconds**

### Layer 4: GLM Generation

- **Status:** PASS
- Response: `<|begin_of_box|>ok<|end_of_box|>` (GLM's special tokens visible)
- Wall clock: **14.7 seconds**

### Layer 5: Nomic Embeddings

- **Status:** PASS
- Output: 768-dimensional embedding vector
- Wall clock: sub-second

### Layer 6: ChromaDB

- **Status:** PASS
- 3 collections: `iaomw_archive` (17 docs), `tripl_archive` (144 docs), `kjtco_archive` (282 docs)
- Database size: 16MB at `~/.local/share/iao/chromadb/`
- Query test ("bundle quality gates" against iaomw_archive, top-3): returned 3 results from 0.1.3 artifacts

### Layer 7: Context Enrichment

- **Status:** PASS
- `build_full_context()` returns plan prompt + RAG enrichment
- Plan prompt: 3,309 chars / 480 words
- Full prompt with RAG: 6,476 chars / 920 words
- System prompt: 2,002 chars / 263 words

### Layer 8: Template Rendering

- **Status:** PASS
- 7 templates present: `design.md.j2`, `plan.md.j2`, `build-log.md.j2`, `report.md.j2`, `bundle.md.j2`, `run-report.md.j2`, `_shared.md.j2`
- Template sizes: 11-38 lines each (very small)
- All templates are structurally correct Jinja2

---

## GPU State

```
GPU: NVIDIA GeForce RTX 2080 (Super variant likely, 8GB VRAM)
Driver: 595.58.03, CUDA: 13.2
Memory: 667 MiB / 8192 MiB used (idle — only KDE processes)
GPU Utilization: 2%
```

Ample GPU memory for any single model. Qwen 9B (6.6GB) fits in VRAM with room for KV cache.

---

## Artifact Loop Code Analysis

### Entry Point (`src/iao/artifacts/loop.py`)

The loop is straightforward:
1. Render Jinja2 template with iteration context
2. Append RAG context from ChromaDB
3. Send to Qwen via `QwenClient.generate()` (which calls Ollama `/api/chat`)
4. Validate response (word count ≥ min_words, required terms present)
5. If validation fails, retry up to 3 times with an escalation prompt
6. Write output to `docs/iterations/{version}/{prefix}-{kind}-{version}.md`

### QwenClient (`src/iao/artifacts/qwen_client.py`)

- Uses `/api/chat` endpoint (not `/api/generate`)
- `stream: false` — waits for complete response before returning
- `timeout: 1800` seconds (30 minutes!) — this is the default
- `temperature: 0.2`, `num_ctx: 8192`
- No progress reporting — the caller gets nothing until Qwen finishes or times out

### Template Prompts

The templates are small and well-structured:
- **design.md.j2** (17 lines): Asks for 5000+ word design document. Includes trident, pillars, workstreams.
- **plan.md.j2** (12 lines): Asks for 3000+ word plan. References workstreams, split-agent handoff.
- **build-log.md.j2** (11 lines): Asks for 2000+ word chronological build log.
- **report.md.j2** (12 lines): Asks for 1500+ word retrospective.
- **bundle.md.j2** (11 lines): Asks for 250+ word bundle index.

### Validation Thresholds (`src/iao/artifacts/schemas.py`)

| Artifact | Min Words | Required Terms |
|---|---|---|
| design | 5,000 | "iteration" |
| plan | 3,000 | "workstream" |
| build-log | 1,500 | "start:" |
| report | 1,200 | "status" |
| bundle | 200 | "iteration" |

### ADR-012 Immutability

Design and plan artifacts are treated as immutable — if they already exist on disk, the loop skips regeneration and returns the existing file. This means the 0.1.5 design (34.7KB) and plan (26.0KB) that exist on disk will NOT be regenerated if the loop runs again for 0.1.5.

---

## Failure Mode Analysis

### Ranked from most to least probable:

**1. (a) Qwen is just slow for long-form generation — MOST PROBABLE**

Evidence:
- Qwen 9B takes 7.1s for a 2-token response (cold start). Generation speed is roughly 15-25 tokens/second on an RTX 2080.
- A 5000-word design document is ~6500 tokens. At 20 tok/s, that's ~325 seconds (~5.4 minutes).
- A 3000-word plan is ~4000 tokens. At 20 tok/s, that's ~200 seconds (~3.3 minutes).
- With the retry mechanism (up to 3 attempts if word count is below threshold), a worst case is 3 × 5.4 minutes = ~16 minutes for a design doc.
- The design doc was generated (~10 minutes reported by Gemini session), which aligns perfectly with this estimate.
- The plan would take similar time. "Hung with no output" likely means the caller was waiting for the synchronous response.

**Why it looks like a hang:** `stream: false` + `timeout: 1800s` means the HTTP request blocks silently for up to 30 minutes. There is no progress output. The caller (CLI or agent) sees nothing until the response arrives or the timeout fires.

**2. (d) The CLI orchestration has no user-visible progress — PROBABLE CONTRIBUTING FACTOR**

Evidence:
- `QwenClient.generate()` does `requests.post(..., timeout=self.timeout)` with `timeout=1800`.
- No streaming, no progress bar, no heartbeat logging.
- The only stderr output is retry messages: `[iao.loop] {artifact} attempt {n}: {words} words < {min} min, retrying...`
- An agent (Gemini or Claude) waiting for stdout/stderr and seeing nothing for 5+ minutes may conclude the process is hung and kill it, or the session may time out.

**3. (b) Prompt asks for impossible length — UNLIKELY**

Evidence:
- The prompts are reasonable. 5000 words for a design doc is ambitious but achievable for Qwen 9B.
- The design doc WAS generated (5132 words) — proving the prompt works.
- The plan doc WAS generated (3274 words, meeting the 3000 min).
- Both documents exist on disk. The loop did work at least once.

**4. (c) RAG context injects garbage — UNLIKELY**

Evidence:
- RAG enrichment adds ~3000 chars of context (snippets from iaomw_archive).
- ChromaDB query returned sensible results (0.1.3 report, run-report, build-log).
- Total prompt with RAG is only 920 words — well within Qwen's 8192 token context window.

**5. (e) Ollama misconfigured or OOM — UNLIKELY**

Evidence:
- Ollama is running and responsive.
- All 4 models are installed.
- GPU has 7.5GB free VRAM — Qwen 9B (6.6GB) fits comfortably.
- All smoke tests passed.

**6. (f) Template rendering broken — RULED OUT**

Evidence:
- Templates render correctly. The computed prompts have correct structure.
- Design and plan artifacts exist on disk — they WERE generated from these templates.

---

## What Actually Happened (Reconstruction)

Based on the evidence, here is the most likely sequence:

1. A Gemini CLI session ran `iao iteration design 0.1.5`. Qwen generated the design doc in ~10 minutes (5132 words, meeting the 5000 minimum). This is consistent with the generation speed estimate.

2. The same session ran `iao iteration plan 0.1.5`. Qwen began generating but the CLI showed no output (stream=false, no progress). After some number of minutes of silence, either:
   - The Gemini session timed out or was killed
   - The operator concluded it was hung and terminated it
   - OR: the plan WAS generated (3274 words exist on disk!) and the hang occurred on a SUBSEQUENT artifact

3. A subsequent Claude Code session picked up the project but focused on cleanup rather than re-attempting the artifact loop, finding the design and plan already on disk.

4. The 0.1.5 plan file exists on disk (25,953 bytes, 3274 words), so the "hang" may have been misdiagnosed — the plan may have completed but a later artifact (build-log or report) hung, or the session ended before the next step.

---

## Recommended Improvements (for 0.1.6 to implement)

1. **Add streaming mode:** Change `QwenClient` to use `stream: true` and print tokens as they arrive, so agents and operators can see progress.
2. **Reduce timeout:** 1800s is excessive. A per-artifact timeout of 600s (10 minutes) with explicit failure would be more debuggable.
3. **Add heartbeat logging:** Print elapsed time every 30-60 seconds during generation.
4. **Consider context window:** With `num_ctx: 8192`, Qwen must fit system prompt + user prompt + generated output. For a 5000-word output (~6500 tokens) plus ~1200 tokens of prompt, the total approaches the 8192 limit. Consider increasing `num_ctx` to 16384 or reducing prompt verbosity.
