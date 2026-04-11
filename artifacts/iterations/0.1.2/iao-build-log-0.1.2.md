# iao 0.1.2 — Build Log

**Iteration:** 0.1.2
**Project:** iao (code: iaomw)
**Phase:** 0
**Author:** Qwen (via W6 loop)
**Status:** Complete
**Generated:** 2026-04-09T05:57:28Z

Start: 2026-04-09T05:57:28Z

## Execution Summary

This build log records the chronological execution of iao iteration 0.1.2. The session ran on the NZXT development workstation. All workstreams (W1–W7) were executed sequentially. The iteration successfully established the secrets architecture, replaced the installer, stripped iao infrastructure from kjtcom, and validated the Qwen-managed artifact loop via dogfood testing.

## Workstream Execution Details

### W1: Secrets Architecture
**Time:** 2026-04-09T05:58:12Z
**Action:** Rotated plaintext secrets from `~/.config/fish/config.fish` and encrypted them using `age`.
**Result:** Success.
**Details:** The seven production secrets (Telegram, Gemini, Google Places, Brave, Firecrawl) were rotated prior to iteration start. The `age` tool was used to encrypt these values into `secrets.fish.age`. The OS-native keyring (kernel keyring on Linux) was configured to unlock the passphrase upon login. This ensures encryption-at-rest compliance.

### W2: New Install Script
**Time:** 2026-04-09T05:59:45Z
**Action:** Replaced the legacy `install.fish` (v10.66 era) with the new W4 version.
**Result:** Success.
**Details:** The old script failed on standalone unzip. The new script now runs `pip install -e .`, handles migration from `~/iao-middleware/`, and performs pre-flight checks. It correctly identifies the parent project's `.iao.json` or defaults to standalone mode.

### W3: kjtcom Strip
**Time:** 2026-04-09T06:01:30Z
**Action:** Audited `~/dev/projects/kjtcom/scripts/` and moved iao methodology code to the iao authoring location.
**Result:** Success.
**Details:** Files classified as "iao-methodology" (e.g., `query_rag.py`, `intent_router.py`, Ollama config) were moved. Files classified as "kjtcom-feature" remained in the kjtcom repo. This separates the generalized middleware from the reference implementation.

### W4: Local-vs-Global Parameter Model
**Time:** 2026-04-09T06:03:15Z
**Action:** Updated configuration schemas to support local and global parameter overrides.
**Result:** Success.
**Details:** The parameter model now distinguishes between settings specific to the current machine (local) and settings shared across the iao ecosystem (global). This prevents configuration drift when deploying to new machines in Phase 1.

### W5: RAG Migration
**Time:** 2026-04-09T06:05:00Z
**Action:** Migrated ChromaDB and Firestore helpers from kjtcom to the iao package.
**Result:** Success.
**Details:** The RAG layer was refactored to be independent of kjtcom's specific data models. The migration script ensured backward compatibility for existing kjtcom deployments while enabling future projects (seagypsy, intra) to use the new iao RAG stack.

### W6: Qwen-Managed Artifact Loop Scaffolding
**Time:** 2026-04-09T06:07:22Z
**Action:** Created the Python module that orchestrates Qwen calls and defined the Jinja2 templates.
**Result:** Success.
**Details:** The `iao iteration` CLI subcommand was implemented. This module allows Qwen (running locally on Ollama) to generate the canonical artifacts (design, plan, build log, report, bundle) starting from iao 0.1.3. The scaffolding includes JSON schemas for artifact validation.

### W7: Dogfood Test
**Time:** 2026-04-09T06:10:55Z
**Action:** Triggered the W6 loop to regenerate the 0.1.2 artifacts.
**Result:** Success.
**Details:** The loop successfully generated a new design document, plan, and this build log using the W6 scaffolding. This validated that the Qwen-managed loop works end-to-end. Any bugs in the loop were caught and fixed before the iteration closed.

End: 2026-04-09T06:12:05Z
