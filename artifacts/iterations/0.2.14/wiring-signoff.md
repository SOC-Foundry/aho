# Wiring Sign-off Package — aho 0.2.14

**For:** Kyle — Hard Gate 3 decision
**Date:** 2026-04-13
**Iteration theme:** Council wiring verification + cascade smoke test

---

## 1. Vetting Summary

W1 vetted all 16 declared council members. Results:

| Category | Member | Status | Evidence |
|----------|--------|--------|----------|
| LLM | Qwen-3.5:9B | **operational** | Self-identifies correctly, 7.7s latency, coherent structured output at Q4_K_M |
| LLM | Nemotron-mini:4b | **substrate-compromised** | Evasive self-identification, 80% "feature" default on classification (0.2.13 W2.5) |
| LLM | GLM-4.6V-Flash-9B | **substrate-compromised** | Identity mismatch (reports 4.5V), 80% timeout, wrong JSON schema (0.2.13 W2.5) |
| LLM | OpenClaw (Qwen wrapper) | **operational** | Wraps Qwen 3.5:9B via QwenClient. Cosmetic council member, not distinct capability. |
| MCP | context7 | **operational** | Library resolution works |
| MCP | sequential-thinking | **operational** | Thought history returns |
| MCP | playwright | **operational** | Browser automation callable |
| MCP | filesystem | **operational** | Directory listing works |
| MCP | dart | **operational** | 2 devices detected |
| MCP | memory | **operational** | Knowledge graph functional (empty) |
| MCP | everything | **operational** | Echo returns |
| MCP | firebase-tools | **configured-incomplete** | Authenticated, no project configured |
| MCP | firecrawl | **gap** | Server not started, API key empty |
| Other | Nemoclaw socket | **operational** | Dispatch with explicit role bypasses classify, 18.5s round-trip |
| Other | ChromaDB | **operational** | v1.5.5, in-process client works |
| Other | nomic-embed-text | **operational** | 768-dim embeddings, valid vectors |

**Totals:** 12 operational, 2 substrate-compromised, 1 configured-incomplete, 1 gap.

## 2. Cascade Smoke Test Outcomes

Two runs executed against the same 247K-character NoSQL technical manual (201 pages).

### Run-1 (W1 — dispatcher bugs present)

- **Dispatcher state:** `/api/generate` endpoint, `num_ctx` defaulting to 4096
- **Total wall clock:** 1,885s (31.4 min), 5/5 stages complete, 0 exceptions
- **Total output:** 6,901 chars
- **Findings:** Producer generated 222-char Chinese customer-service persona (total failure). Auditor doubled JSON with template tokens between copies. Indexer_out truncated mid-hallucinated turn. Only assessor produced clean output.
- **Root cause:** Two compounding dispatcher bugs — `num_ctx` truncated 247K document to ~4K tokens; `/api/generate` leaked chat template special tokens (`<|endoftext|>`, `<|im_start|>`) into visible output.

### Run-2 (W1.5 — dispatcher repaired)

- **Dispatcher state:** `/api/chat` endpoint, `num_ctx: 32768`, stop tokens configured
- **Total wall clock:** 1,867s (31.1 min), 5/5 stages complete, 0 exceptions
- **Total output:** 14,725 chars (+113% vs run-1)
- **Hard gates (6/6 pass):**
  1. Zero template tokens across all stages
  2. No multi-turn simulation in any response
  3. Producer on-topic English (3,908 chars substantive NoSQL analysis)
  4. Auditor single coherent JSON block
  5. All 5 stages complete with non-null, non-truncated output
  6. No stage hit 60-min cap (longest: auditor at 9.5 min)

### Run-1 vs Run-2 comparison

| Stage | Run-1 chars | Run-2 chars | Run-1 issue | Run-2 outcome |
|-------|-------------|-------------|-------------|---------------|
| indexer_in | 3,061 | 3,550 | Analyzed only tail 4K of 247K doc | Analyzed Sections 71-100 with 32K context |
| producer | 222 | 3,908 | Chinese customer-service persona | Substantive English scaling analysis |
| auditor | 1,936 | 2,174 | Doubled JSON, template tokens, Chinese | Single coherent JSON, identifies ambiguity |
| indexer_out | 214 | 2,031 | Truncated mid-Chinese hallucination | 3 substantive proposed deltas |
| assessor | 1,468 | 3,062 | Valid logic on limited inputs | Comprehensive meta-assessment, score 92 |

The run-1 to run-2 improvement was purely from dispatcher configuration fixes. No model changes, no prompt changes.

## 3. Role Assignment

**Assignment:** Qwen-solo — `qwen3.5:9b` across all 5 cascade roles (indexer_in, producer, auditor, indexer_out, assessor).

**Pillar 7 violation acknowledged.** Generation and evaluation are not separated — the same model that produced artifacts also audited them. This was the only viable assignment given W1 vetting: Qwen is the sole operational LLM capable of structured analytical output. Nemotron and GLM are substrate-compromised.

Documented in `smoke-test/role-assignment.md` and W1.5 findings.

## 4. Members Ready for 0.2.15 Measurement

| Member | Context | Readiness |
|--------|---------|-----------|
| Qwen-3.5:9B | 32K confirmed working at Q4_K_M on 2080 SUPER (7.2/8.2 GB VRAM) | Ready — primary cascade member, proven in run-2 |
| Llama 3.2 3B | Pulled to NZXTcos (~2GB on disk), not yet integrated | Ready for integration — triage officer candidate, lightweight |

## 5. Members Not Ready

| Member | Issue | Path to Ready |
|--------|-------|---------------|
| Nemotron-mini:4b | Substrate-compromised: 80% "feature" default, evasive self-ID | Re-test on properly configured dispatcher (W1.5 fixes). Matrix data needed. |
| GLM-4.6V-Flash-9B | Substrate-compromised: 80% timeout, wrong JSON schema, identity mismatch | Re-test on `/api/chat` with proper `num_ctx`. Matrix data needed. |
| ChromaDB + nomic-embed-text | Operational but vetting was ping-level, not analytical workload | Include in matrix testing with real embedding/retrieval tasks |
| firebase-tools | Authenticated but no project configured | Configure Firebase project |
| firecrawl | API key empty, server not started | Obtain API key, configure |
| 5 MCPs (dart, memory, everything, sequential-thinking, playwright) | Operational but role in cascade undefined | Define cascade integration points in 0.2.15 |

## 6. Recommended Kyle Decision

**Recommendation: (a) Wiring complete. 0.2.15 proceeds to measurement matrix with expanded roster.**

**Rationale:**

1. **Cascade architecture validated end-to-end.** Five-stage pipeline executed on a 247K-character real-world technical document. Cross-stage coherence confirmed — auditor findings appear in indexer_out's proposed deltas appear in assessor's meta-assessment. This is actual handoff, not parallel hallucination.

2. **Dispatcher honest after W1.5 fix.** The two critical bugs (context truncation + template leakage) are resolved. The dispatcher now uses `/api/chat` with proper `num_ctx` and stop tokens. Run-2 proved the fix.

3. **Substrate quality questions are 0.2.15 matrix concerns, not 0.2.14 wiring concerns.** Whether Nemotron and GLM can produce useful output through the now-honest dispatcher is a measurement question. The wiring to dispatch to them, collect their output, and route it through the cascade is in place.

4. **Expanded roster already pre-positioned.** Llama 3.2 3B on disk. DeepSeek-Coder-V2, Mistral-Nemo, Gemma 2 9B identified as candidates. 0.2.15 matrix testing can begin immediately with Qwen + Llama and expand as models are pulled.

**What (a) does NOT claim:** It does not claim the council is thick or that Pillar 7 is restored. It claims the wiring works and measurement can begin.
