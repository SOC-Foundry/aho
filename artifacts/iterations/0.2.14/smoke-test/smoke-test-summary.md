# Smoke Test Summary — 0.2.14 W1

**Document:** NoSQL_DataPipelines_Technical_Manual.pdf (201 pages, 247,275 chars)
**Assignment:** Qwen-solo (qwen3.5:9b × 5 roles) — Pillar 7 violation acknowledged
**Dispatch:** Direct Ollama HTTP API
**Status:** Complete — all 5 stages finished, 0 exceptions

---

## Per-Stage Results

| Stage | Wall Clock | Output Chars | Notes |
|-------|-----------|-------------|-------|
| indexer_in | 136.4s | 3,061 | Analyzed optimization logic from final sections (pp.194-201). Model saw truncated document (4K context). Substantive analysis within visible window. |
| producer | 348.5s | 222 | Chinese-language customer service response. Off-topic. Model did not follow producer system prompt at Q4_K_M with truncated context. |
| auditor | 527.1s | 1,936 | JSON output with delta_validations. Partially Chinese. Validated deltas from indexer_in. Accepted some, provided reasoning. Handoff mechanism works. |
| indexer_out | 549.2s | 214 | JSON output. Correctly identified "no proposed Deltas" in auditor findings. Empty proposed_deltas array. Honest assessment of input. |
| assessor | 324.1s | 1,468 | JSON assessment. Validated indexer-in optimization logic (MongoDB, Cassandra, Neo4j, Redis). Identified absence of indexer_out deltas. Produced structured final output. |

**Total wall clock:** 1,885.3 seconds (31.4 minutes)
**Exceptions:** 0

## Findings

### Critical: Ollama context_length is 4,096 (not 256K)

Ollama runs Qwen 3.5:9B with `context_length: 4096` by default. The model's 256K context window is not utilized. The 247K-char document is truncated to ~4K tokens by Ollama before the model sees it. This explains why:
- Indexer_in only referenced sections 98-100 (pp.194-201) — the tail of the document visible in 4K context
- Producer generated off-topic Chinese response — insufficient context to understand the task

**Fix for 0.2.15:** Set `num_ctx` in Ollama API call or modelfile. The model supports 256K context natively.

### Model output quality

- **Indexer_in:** Substantive analysis of document tail. Quality is reasonable for what the model could see.
- **Producer:** Off-topic Chinese customer service response. System prompt ineffective at Q4_K_M with truncated context.
- **Auditor:** Delta validation in JSON format. Partially Chinese. The mechanism works — auditor accepted/rejected deltas with reasoning.
- **Indexer_out:** Correctly identified no deltas in auditor output. Honest empty response.
- **Assessor:** Structured JSON assessment. Validated prior work products. Produced final summary with recommendations. The assessor is the strongest output — it received smaller inputs (prior outputs only, not full document) and produced coherent structured analysis.

### Cascade mechanics: proven

The 5-stage handoff architecture works end-to-end:
1. Each stage receives prior outputs and dispatches to Ollama
2. Trace events emitted per handoff (10 total: 5 dispatch + 5 complete)
3. Per-stage JSON artifacts written to run directory (5 files + trace.json)
4. Auditor received and validated indexer_in deltas
5. Assessor received all prior work products and produced meta-assessment
6. Zero unhandled exceptions across all 5 stages
7. No stage hit the 60-minute timeout cap

### Performance

At Q4_K_M on consumer hardware (NZXTcos), per-stage: 136–549s (2.3–9.2 min). Total cascade: 31.4 minutes. Acceptable for batch analysis. Not interactive.

## Gate 2 Assessment

| Criterion | Met? | Notes |
|-----------|------|-------|
| Vetting table complete | Yes | Gate 1 satisfied — 16 members, all with explicit status |
| Cascade integration test on dummy | Yes | 5 stages completed on dummy doc |
| NoSQL smoke test executed | Yes | 5/5 stages complete, 0 exceptions |
| Trace events present | Yes | 10 events (5 dispatch + 5 complete) |
| Auditor validated delta | Yes | Auditor JSON includes delta_validations |
| Assessor produced output | Yes | 1,468 chars structured JSON assessment |
| Baseline clean | Yes | 12 failures, all in baseline. 0 new. |
| No G083 introduced | Yes | No except Exception in new code |

**Gate 2 verdict:** Pass. Cascade proven end-to-end. All 5 stages completed on 201-page NoSQL document. Output quality constrained by 4K context truncation (Ollama default, not model limitation) and Q4_K_M quantization. Cascade mechanics are sound. Output quality is a 0.2.15 configuration + measurement concern.
