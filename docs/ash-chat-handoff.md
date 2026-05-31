# Ash (formerly Aho) Project Chat Handoff

**Date:** 2026-05-30  
**Participants:** Kyle Thompson + Grok

## Project Overview
**Ash** (Agentic System Harness, previously named Aho) is Kyle's long-term project to build serious governance infrastructure for LLM-driven engineering work. It originated as internal middleware tooling at Tachtech to make large, expensive data/SIEM migration pipelines more reliable and cost-effective when using frontier models.

Core thesis: Richer, more disciplined harnesses produce materially better results from the same models.

## User's Professional Context
- VP of Engineering at Tachtech (cybersecurity firm in San Francisco).
- Focus areas:
  - Advanced SIEM correlation development (multi-log source table joins for adversary detection).
  - Helping enterprises build **secure agentic developer workflows** to prevent supply chain breaches.
- Notable clients include OpenAI, Uber, PayPal, McDonald’s, and others (some engaged post-breach, e.g. Mercor).
- Primary observed threat model with AI coding tools: Junior developers using Claude Code blindly accepting malicious npm package suggestions that exfiltrate GitHub keys.
- Sales mix with clients: ~65% process/hygiene, ~35% tooling.

## Key Assets & Philosophy (What to Preserve)
User has explicitly stated willingness to burn down most of the current codebase. The real value lies in:

- **The 11 Pillars** — Core operating principles (especially Pillar 8: efficacy measured in cost delta, Pillar 11: human holds the keys / no agent git operations).
- **Gotcha Registries** — Institutional memory of failure modes and mitigations.
- **Harnesses** — Defined by Kyle as: a set of role-specific agent and multi-modal instructions assigned to different models based on their strengths (e.g. qwen as auditor, llama 3.2 as regulator, GLM as executor) to produce consistent, reliable results.
- **Historical record** in `/artifacts/iterations/` — This is considered the highest-value artifact from all prior work with Claude.
- **3-octet (a.b.c) iteration system** — Used for historical traceability. Willing to adjust to 2 or 4 octets but needs strong justification to move to a single-octet system.

## Current Assessment of Existing Codebase
- User is willing to **burn most of it down** and start fresh.
- The current implementation (complex council, state machine, workstream orchestration, etc.) has limited retained value.
- Major problems experienced with Claude during development:
  - Difficulty staying within the a.b.c structure.
  - Getting stuck in workstreams, taking detours, losing focus.
  - Poor ability to pivot when needed.
  - Misinterpreting hard rules (e.g. Pillar 11 interpreted as "I cannot make system changes").
  - Perceived lack of investment in outcomes that reduce the centrality of single frontier agents.

## Recent Developments
- Corporate decision at Tachtech to rebrand from **Aho** to **Ash**.
- Repo has been forked to a corporate account (`tachtech-engineering`).
- Development will continue primarily in the personal `socfoundry/aho` repo.
- Stable versions will be forked back to the corporate repo at milestones.
- As of this chat, Ash is still **pre-production** internally at Tachtech.

## User's Assessment of AI Collaboration
- Views Claude as effective for junior developers but less suitable as a "veteran developer tool."
- Explicitly stated that Grok appears to be a better fit for his development needs on this project.
- Expressed interest in continuing development with Grok's assistance.

## Open Topics for Future Work
- Whether to retain or significantly modify **Adversarial Authorship** (currently open for discussion).
- Redefining the harness around role-specialized instructions + model routing based on capability.
- Potential simplification or restructuring of the iteration system (a.b.c).
- Practical path to making Ash production-ready for Tachtech's internal use and client work.

## Recommended Approach Going Forward
- Treat the current source code as largely disposable.
- Anchor new work in the preserved concepts (Pillars, Gotcha, Harness-as-role-instruction-layer, a.b.c traceability).
- Focus on building something that produces consistent, reliable results for experienced engineers rather than maximizing volume for juniors.
- Maintain high discipline around artifacts and historical traceability.

---

*This document was created to allow clean context transfer to a new session.*