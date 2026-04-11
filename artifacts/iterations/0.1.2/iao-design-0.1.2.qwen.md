# IAO Iteration 0.1.2 Design Document

**Generated:** 2026-04-09T05:28:35Z  
**Iteration:** 0.1.2  
**Project:** iao (code: iaomw)

## Executive Summary
This iteration focuses on hardening the security model, simplifying the installation process, and establishing a self-managing artifact loop. The primary objective is to decouple the project's operational logic from its infrastructure dependencies while significantly elevating the security posture of secret management. By refactoring the core scaffolding and migrating knowledge retrieval systems, we aim to create a more maintainable, secure, and autonomous development environment that junior engineers can onboard into without friction.

## Problem Statement and Constraints
The current architecture suffers from mixed concerns, where secret management is loosely coupled with application code, and the installation script relies on fragile external dependencies. We must solve for security compliance and repository hygiene without breaking backward compatibility for existing users. Constraints include strict adherence to standard OS security practices for key storage and ensuring that the new artifact loop can regenerate its own documentation without external human intervention.

## Workstream Scope and Intent

**W1: Secrets Architecture**  
This workstream replaces plaintext or insecure storage with age encryption paired with the OS keyring. The intent is to ensure that sensitive configuration data is encrypted at rest and accessible only via the operating system's native security mechanisms. This prevents accidental exposure during version control operations.

**W2: New Install.fish**  
We are rewriting the installation script to be more robust and idempotent. The scope includes handling environment detection and dependency resolution within the script itself. This ensures that a user can bootstrap the environment reliably regardless of their initial shell state.

**W3: Kjtcom Strip**  
The goal here is to move iao methodology code out of the external `kjtcom` repository. This reduces coupling and allows the project to own its own logic. We will extract relevant functions and integrate them directly into the main codebase, ensuring the project remains self-contained.

**W4: Local-vs-Global Parameter Model**  
This workstream defines a clear separation between local development overrides and global production parameters. The intent is to prevent configuration drift by enforcing a strict hierarchy where local settings never overwrite global defaults unless explicitly intended.

**W5: RAG Migration**  
We are migrating the Retrieval-Augmented Generation (RAG) pipeline to a more efficient backend. The scope involves updating the vector store and retrieval logic to ensure that documentation queries return accurate results faster, improving the developer experience.

**W6: Qwen-Managed Artifact Loop Scaffolding**  
This establishes the automation framework where Qwen manages the generation of artifacts. The intent is to create a closed loop where the system can document itself and update its own changelogs automatically, reducing manual maintenance overhead.

**W7: Dogfood Test**  
The final workstream involves regenerating the 0.1.2 artifacts via the new loop. This validates that the entire pipeline works end-to-end. If the system cannot generate its own release notes and install scripts, the iteration is not complete.

## Risks and Exit Criteria
**Risks:** The primary risk is keyring compatibility across different Linux distributions, which could hinder W1. Additionally, the new install.fish script (W2) might introduce breaking changes for users with legacy shell configurations.

**Exit Criteria:** The iteration is considered successful only when W7 completes without errors, all W1-W6 workstreams pass internal linting, and the generated artifacts match the design specifications. We will not merge the code until the dogfood test confirms that the new loop can sustain itself.
