# kjtcom Audit & Classification Report

**Iteration:** 0.1.2
**Workstream:** W5
**Date:** 2026-04-08
**Auditor:** Gemini CLI

## Classification Summary

| Classification | Count | Description |
|---|---|---|
| IAO-METHODOLOGY | 28 | Core orchestration, RAG, logging, and metadata |
| KJTCOM-FEATURE | 45+ | Project-specific scrapers, app code, and pipelines |
| AMBIGUOUS | 5 | Files needing further generalization review |

## Detailed Classification Table

| File Path | Classification | Action |
|---|---|---|
| `scripts/query_registry.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `scripts/query_rag.py` | IAO-METHODOLOGY | Migrate to `iao/rag/query.py` |
| `scripts/intent_router.py` | IAO-METHODOLOGY | Migrate to `iao/rag/router.py` |
| `scripts/firestore_query.py` | IAO-METHODOLOGY | Migrate to `iao/data/firestore.py` |
| `scripts/utils/iao_logger.py` | IAO-METHODOLOGY | Reconcile with `iao/logger.py` |
| `scripts/utils/ollama_config.py` | IAO-METHODOLOGY | Migrate to `iao/ollama_config.py` |
| `scripts/brave_search.py` | IAO-METHODOLOGY | Migrate to `iao/integrations/brave.py` |
| `scripts/pre_flight.py` | IAO-METHODOLOGY | Already implemented in `iao/preflight/` |
| `scripts/post_flight.py` | IAO-METHODOLOGY | Already implemented in `iao/postflight/` |
| `scripts/embed_archive.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `scripts/iteration_deltas.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `scripts/utils/ollama_logged.py` | IAO-METHODOLOGY | Migrate to `iao/` |
| `scripts/utils/consolidate_gotchas_v2.py` | IAO-METHODOLOGY | Migrate to `iao/` |
| `scripts/generate_artifacts.py` | IAO-METHODOLOGY | Superseded by W6 Qwen Loop |
| `scripts/check_compatibility.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `scripts/analyze_events.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `scripts/run_evaluator.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `scripts/sync_script_registry.py` | IAO-METHODOLOGY | Migrate & Generalize |
| `kjtcom-telegram-bot.service` | IAO-METHODOLOGY | Migrate as Template |
| `data/script_registry.json` | IAO-METHODOLOGY | (Reference only) |
| `data/gotcha_archive.json` | IAO-METHODOLOGY | (Reference only) |
| `data/iao_event_log.jsonl` | IAO-METHODOLOGY | (Reference only) |
| `scripts/panther_scrape.py` | KJTCOM-FEATURE | Keep in kjtcom |
| `scripts/enrich_counties.py` | KJTCOM-FEATURE | Keep in kjtcom |
| `scripts/telegram_bot.py` | KJTCOM-FEATURE | Keep in kjtcom |
| `pipeline/` | KJTCOM-FEATURE | Keep in kjtcom |
| `app/` | KJTCOM-FEATURE | Keep in kjtcom |
| `functions/` | KJTCOM-FEATURE | Keep in kjtcom |

## Migration Plan

1.  **Phase A (High Priority):** Migrate RAG layer, Firestore helpers, Ollama config, and Logger.
2.  **Phase B (Integration):** Migrate Brave Search and systemd templates.
3.  **Phase C (Maintenance):** Generalize remaining IAO-METHODOLOGY scripts (registry, gotcha consolidation).

kjtcom will retain all original files for steady-state operation. iao will contain the generalized versions.
