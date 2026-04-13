# Smoke Test Role Assignment — 0.2.14 W1

## Assignment: Qwen-solo

| Role | Model | Rationale |
|------|-------|-----------|
| indexer_in | qwen3.5:9b | Only viable LLM per vetting |
| producer | qwen3.5:9b | Only viable LLM per vetting |
| auditor | qwen3.5:9b | Only viable LLM per vetting |
| indexer_out | qwen3.5:9b | Only viable LLM per vetting |
| assessor | qwen3.5:9b | Only viable LLM per vetting |

## Pillar 7 Violation Acknowledgment

**Pillar 7:** "Generation and evaluation are separate roles. The model that produced an artifact is never the model that grades it."

This smoke test violates Pillar 7: all five roles (including drafter and reviewer) are bound to the same model (Qwen 3.5:9B). This is acknowledged and acceptable for the following reasons:

1. **Vetting outcome:** Only Qwen 3.5:9B is viable for structured output. Nemotron-mini:4b (80% feature-bias) and GLM-4.6V-Flash-9B (80% timeout, wrong JSON schema) cannot produce usable analytical output.
2. **Smoke test purpose:** Proves cascade works mechanically — stages execute, handoffs emit, trace completes. Model quality per role is 0.2.15's matrix-testing concern.
3. **Pillar 7 restoration path:** 0.2.15 matrix testing with heavier quantization (Q8_0), alternative models, or architectural pivot will inform viable multi-model assignment.

## Document

- Source: `artifacts/iterations/0.2.14/matrix-docs/nosql-manual.txt`
- Size: 247,275 characters, 7,091 lines, 201 pages
- Per-stage timeout: 3600 seconds (60 minutes)

## Expected Behavior

Qwen 3.5:9B on this hardware takes ~50s for a short analytical response. On a 247K-char document, first stage (indexer_in) will need to process the full document. Later stages receive prior outputs only (much smaller). Stages may hit the 60-min cap; partial_completion is data, not failure.
