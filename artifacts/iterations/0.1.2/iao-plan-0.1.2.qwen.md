# iao 0.1.2 — Plan Document

**Iteration:** 0.1.2
**Project:** iao (code: iaomw)
**Phase:** 0 (NZXT-only authoring)
**Status:** Planning
**Generated:** 2026-04-09T05:51:09Z

## Summary

This iteration focuses on maturing the iao toolkit itself. We will secure our secrets infrastructure, replace the legacy installer, clean up the reference implementation (kjtcom), and build the self-generating artifact loop. The work is divided into seven workstreams (W1–W7). Agents Gemini and Claude will collaborate, with Gemini handling infrastructure and migration tasks (W1–W5) before handing off to Claude for the artifact generation loop (W6–W7).

## Workstreams

### W1: Secrets Architecture
*   **Goal:** Eliminate plaintext secrets in `~/.config/fish/config.fish`. Implement encryption-at-rest using `age` for cross-platform compatibility and the OS-native keyring for session unlocking.
*   **Deliverables:** Updated `config.fish` template, `age` key generation script, OS keyring integration tests.
*   **Dependencies:** None.
*   **Agent Owner:** Gemini.
*   **Acceptance Checks:** Secrets decrypt correctly on Linux/macOS/Windows; no plaintext found in git history.

### W2: New Install Script
*   **Goal:** Replace the broken v10.66 `install.fish`. Add logic to handle migration from `~/iao-middleware/` and stale config blocks.
*   **Deliverables:** New `install.fish`, pre-flight check script, migration helper functions.
*   **Dependencies:** W1 (secrets must be ready for config generation).
*   **Agent Owner:** Gemini.
*   **Acceptance Checks:** Standalone unzip installs without errors; legacy config is migrated or flagged.

### W3: kjtcom Strip
*   **Goal:** Audit `~/dev/projects/kjtcom/scripts/` and move all iao methodology code to the iao authoring location.
*   **Deliverables:** Audit report classifying files as "kjtcom-feature" or "iao-methodology", migrated codebase in `iao/`.
*   **Dependencies:** None.
*   **Agent Owner:** Gemini.
*   **Acceptance Checks:** kjtcom runs without iao dependencies; iao repo contains generalized versions of RAG and logger modules.

### W4: Local-vs-Global Parameter Model
*   **Goal:** Define the configuration schema for distinguishing local development parameters from global production settings.
*   **Deliverables:** Updated `iao.json` schema, documentation on parameter precedence.
*   **Dependencies:** W2 (installer must support new config structure).
*   **Agent Owner:** Gemini.
*   **Acceptance Checks:** Config loads correctly in both local and global modes; schema validates JSON inputs.

### W5: RAG Migration
*   **Goal:** Migrate the ChromaDB RAG layer and Firestore helpers from kjtcom to the iao package.
*   **Deliverables:** `query_rag.py`, `intent_router.py` in iao repo, updated Ollama config.
*   **Dependencies:** W3 (code must be moved out of kjtcom first).
*   **Agent Owner:** Gemini.
*   **Acceptance Checks:** RAG queries execute successfully; kjtcom no longer imports iao internal modules.

### Handoff Note
Upon completion of W5, the Gemini agent will pause. The context will be transferred to the Claude agent for the final two workstreams. This split ensures infrastructure stability (Gemini) before shifting to the complex artifact generation logic (Claude).

### W6: Qwen-Managed Artifact Loop
*   **Goal:** Scaffold the Python module that orchestrates Qwen calls, Jinja2 templates, and JSON schemas for artifact generation.
*   **Deliverables:** `iao iteration` CLI subcommand, Python orchestration module, template repository.
*   **Dependencies:** W1–W5 (all infrastructure must be stable).
*   **Agent Owner:** Claude.
*   **Acceptance Checks:** CLI command runs locally; templates render valid JSON artifacts.

### W7: Dogfood Test
*   **Goal:** Regenerate the 0.1.2 artifacts (design, plan, build log, report, bundle) using the new W6 loop.
*   **Deliverables:** Validated bundle for 0.1.2, bug report on loop failures.
*   **Dependencies:** W6 (loop must be functional).
*   **Agent Owner:** Claude.
*   **Acceptance Checks:** Generated artifacts match the design intent; loop completes without external agent intervention.

## Preflight and Postflight

**Preflight:** Ensure `age`, `fish`, and Python environments are installed on NZXT. Verify git history is clean before W3 begins.

**Postflight:** Validate the bundle generated in W7. If the dogfood test fails, iterate on W6 logic before proceeding to 0.1.3. All changes must be committed to the local repository before the iteration closes.
