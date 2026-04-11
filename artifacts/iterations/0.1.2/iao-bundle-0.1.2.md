# iao 0.1.2 — Bundle Index

**Iteration:** 0.1.2
**Project:** iao (code: iaomw)
**Date:** 2026-04-09
**Author:** Qwen (via W6 loop)

## Purpose
This document serves as the single source of truth for recovering the full context of iao iteration 0.1.2. It is intended for junior engineers joining the project or agents executing future iterations (0.1.3+). It summarizes the architectural shifts, lists the canonical artifacts required to understand the state of the codebase, and outlines the critical decisions made during this phase.

## Canonical Artifacts
The following files constitute the official record of this iteration. All paths are relative to the repository root (`~/dev/projects/iao`).

1.  **Design Document** (`iao-design-0.1.2.md`): Defines the five primary jobs of this iteration, including the establishment of secrets architecture and the scaffolding of the Qwen-managed artifact loop.
2.  **Plan Document** (`iao-plan-0.1.2.md`): Contains the pre-flight checks, launch protocol, and success criteria for each workstream (W1–W7).
3.  **Build Log** (`iao-build-log-0.1.2.md`): Records the chronological execution of workstreams, including timestamps and specific actions taken by W3 (kjtcom strip) and W5 (RAG migration).
4.  **Report** (`iao-report-0.1.2.md`): Provides a graded analysis of what worked, what didn't, and lessons learned regarding the new artifact loop.
5.  **Bundle** (`iao-bundle-0.1.2.md`): This index document, which aggregates the above artifacts for future reference.

## Key Architectural Decisions
This iteration marked a transition from a theoretical scaffold to a functional, self-hosted methodology.

*   **Secrets Management (W1):** We deprecated plaintext secrets in `~/.config/fish/config.fish` in favor of `age` encryption combined with the OS-native keyring. This ensures encryption-at-rest compliance without manual passphrase entry on every login.
*   **Installer Modernization (W2):** The legacy `install.fish` (v10.66) was replaced. The new script handles migration from the old `~/iao-middleware/` directory and performs pre-flight checks before declaring installation complete.
*   **Code Separation (W3):** We audited `kjtcom` and moved generalized iao methodology code (e.g., RAG layer, logger) into the iao authoring location. `kjtcom` remains a reference implementation, while `iao` becomes reusable middleware.
*   **Artifact Loop (W6):** Future iterations (0.1.3+) will generate their own design, plan, and report artifacts using local Qwen via Ollama, reducing latency and cost compared to external models.

## Open Follow-ups
Before proceeding to iteration 0.1.3, the team must address the following:

1.  **Automation:** The secret rotation process in W1 is currently manual. Automation scripts should be written to handle token rotation prior to encryption.
2.  **Validation:** The W6 loop requires stricter JSON schema validation to prevent drift in artifact generation.
3.  **Deployment:** Preparation for Phase 1 is underway, specifically onboarding the second target machine (P3, CachyOS Linux) to validate cross-platform compatibility.

This iteration successfully validated the Qwen-managed loop via dogfood testing (W7), proving the methodology can bootstrap itself.
