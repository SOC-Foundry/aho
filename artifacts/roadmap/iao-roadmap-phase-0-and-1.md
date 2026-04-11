# aho Roadmap — Phase 0 and Phase 1

**Status:** Living document, updated each iteration
**Bootstrap:** Created 2026-04-08 by Claude web during aho 0.1.2 design conversation
**Audience:** Anyone reading aho for the first time, junior engineers being onboarded, future contributors deciding where to focus, and forensic reviewers trying to understand aho's history.

---

## What this document is

This is the **canonical roadmap** for aho. It explains where aho is going, in what order, and why. Every aho iteration design doc references this roadmap to anchor itself in the larger sequence. Every novice user reading aho for the first time should start here.

---

## What aho is, in one paragraph

aho is an Agentic Harness Orchestration methodology and toolkit. It formalizes how engineering work happens with AI agents (Claude Code, Gemini CLI, local LLMs via Ollama) by structuring every unit of work as a small focused **iteration** with five canonical artifacts: design, plan, build log, report, bundle. aho was extracted from a real production project called **kjtcom** over Phases 1-10 of intensive AI-agent-driven development. kjtcom remains the **reference implementation** of aho methodology. aho itself is the generalized middleware that lets the methodology be reused across many projects.

---

## The phase model

aho is being built across two phases that span roughly a year of focused work:

**Phase 0 — Authoring on NZXT** (current phase, 0.1.2 through 0.6.x)
**Phase 1 — Cross-machine and cross-platform validation** (1.0.x through 1.5.x)

Between Phase 0 and Phase 1, two transition iterations create the public repository (0.6.x) and the production fork (0.7.x). After Phase 1, aho is presumed mature enough to be used by TachTech engineers in production work without active development support.

The full sequence:

```
0.1.2 ──┐
0.1.3 ──┤
0.1.13 ─┼─ Phase 0: Authoring on NZXT + Clone-to-Deploy realignment
0.2.x ──┤
...
0.6.x ── Repository creation
0.7.x ── Production fork creation
1.0.x ──┐
...
1.5.x ──┘
```

Each iteration is a complete AHO cycle (design → plan → build → report → bundle) with its own focused scope.

---

## Phase 0 — Authoring on NZXT

**Where it happens:** Entirely on NZXT, the development workstation.

**Phase 0 Objective (Realignment 0.1.13):** Phase 0 is complete when **soc-foundry/aho can be cloned on a second Arch Linux box (ThinkStation P3) and deploy LLMs, MCPs, and agents via the `/bin` wrapper package with zero manual Python edits.**

---

## After Phase 1

Phase 1 ends with aho validated across multiple machines and operating systems. At that point:

- **TachTech engineering team can adopt aho** as a methodology for AI-agent-driven engineering work.
- **soc-foundry/aho continues as the upstream lab** where Kyle experiments with new features.
- **tachtech-engineering/aho is the production fork** where TachTech engineers consume releases.

---

## Sign-off

This roadmap was bootstrapped by Claude web on 2026-04-08. From 0.1.3 onward, updates happen via the local fleet. Updated in 0.1.13 W2 to reflect the transition to `aho` and the clone-to-deploy objective.
