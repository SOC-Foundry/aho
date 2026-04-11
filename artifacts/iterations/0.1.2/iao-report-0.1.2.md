**Status:** Complete

# iao 0.1.2 — Report

**Iteration:** 0.1.2
**Project:** iao (code: iaomw)
**Date:** 2026-04-09

## Overview

This iteration marked a critical turning point for the iao project. It transitioned from a theoretical scaffold to a functional, self-hosted methodology. The primary goal was to establish the infrastructure required for future iterations to run autonomously under the iao methodology itself. All seven workstreams executed successfully, validating the new architecture and proving the viability of the Qwen-managed artifact loop.

## Workstream Outcomes

**W1: Secrets Architecture**
We successfully migrated seven plaintext secrets from `~/.config/fish/config.fish` into an encrypted store using `age`. The OS-native keyring integration ensures that credentials are unlocked automatically upon login, eliminating the need for manual passphrase entry. This establishes a secure baseline for all future iterations and mitigates the risk of credential exposure in version control.

**W2: New Install Script**
The legacy `install.fish` (v10.66) was replaced with a robust version that handles migration from the old `~/iao-middleware/` directory. It now performs pre-flight checks and correctly identifies parent projects via `.iao.json`. This resolves previous installation errors on standalone unzips and ensures a consistent setup experience for new developers.

**W3: kjtcom Strip**
We audited the `kjtcom` repository and successfully separated generalized iao methodology code from project-specific features. Files like `query_rag.py` and `intent_router.py` were moved to the iao authoring location. This ensures `kjtcom` remains a reference implementation without bloating the core iao package, keeping the middleware reusable for other projects.

**W4: Local-vs-Global Parameter Model**
Configuration schemas were updated to distinguish between local machine settings and global ecosystem settings. This prevents configuration drift when deploying to new machines in Phase 1, ensuring consistency across the iao network regardless of the underlying OS or hardware.

**W5: RAG Migration**
The ChromaDB and Firestore helpers were refactored to be independent of `kjtcom`'s specific data models. This allows future consumer projects (e.g., `seagypsy`, `intra`) to utilize the RAG stack without inheriting `kjtcom`'s legacy dependencies, promoting modularity.

**W6: Qwen-Managed Artifact Loop**
The Python module orchestrating Qwen calls was created, along with the necessary Jinja2 templates and JSON schemas. This shifts artifact generation from external models like Claude or Gemini to local Qwen, reducing cost and latency while keeping the loop self-contained.

**W7: Dogfood Test**
The iteration validated its own output by regenerating the design, plan, and build log using the W6 scaffolding. This confirmed the loop works end-to-end and caught any potential issues in the scaffolding logic before the iteration closed.

## Lessons and Next Steps

The dogfood test (W7) revealed that the Qwen model requires specific system prompts to adhere to the artifact schemas. While successful, future iterations should include stricter validation in the W6 loop to catch schema drift early. The secret rotation process (W1) was manual; automation for this step should be prioritized in 0.1.3.

The next iteration (0.1.3) will focus on onboarding the second target machine (P3, CachyOS Linux) and integrating the new artifact loop into the production fork. We are ready to push to the public repository once 0.1.3 validates cross-platform compatibility.
