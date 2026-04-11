# Run File — aho 0.1.12

**Generated:** 2026-04-11T03:37:40Z
**Iteration:** 0.1.12
**Phase:** 0
**Status:** Graduated clean

## About this Report

This run file is a canonical iteration artifact produced during the `iteration close` sequence. It serves as the primary feedback interface between the autonomous agent and the human supervisor. Unlike the Qwen-generated synthesis report, this document is mechanically assembled from the iteration's ground truth: the execution checkpoint and the extracted agent questions.

---

## Workstream Summary

| Workstream | Status | Agent | Wall Clock |
|---|---|---|---|
| W0 | pass | Claude Code | - |
| W1 | pass | Claude Code | - |
| W2 | pass | Claude Code | - |
| W3 | pass | Claude Code | - |

---

## Agent Questions for Kyle

(none — no questions surfaced during execution)

---

## Kyle's Notes for Next Iteration

0.1.12 graduated clean — first clean close since 0.1.10. Two gotchas fixed (aho-G060 evaluator baseline reload, aho-G061 smoke instrumentation iteration read), model-fleet.md and agents-architecture.md headers bumped to 0.1.12. Four conditions carry into 0.1.13:

1. **Harness prose drift.** `docs/harness/agents-architecture.md` body still says "Iteration 0.1.7 introduces a complete rebuild of the iao agentic foundations" and references `iao.logger.log_event`. Footer credits "iao 0.1.7 W8". Only the header was sed'd in 0.1.12 W3. Rename sweeps keep missing doc prose because `rg`+`sed` target imports, not narrative text. 0.1.13 W2 fixes this surgically.

2. **ADR-0001 entirely stale.** `docs/adrs/0001-phase-a-externalization.md` still uses "IAO (Iterative Agentic Orchestration)" and references `iao` CLI, `from iao import ...`, pip install of `iao`. Status is Accepted so it's active, not historical. 0.1.13 W2 rewrites.

3. **Folder reorg is go.** Deferred through every run since 0.1.8. 0.1.13 W3 executes: `docs/`, `scripts/`, `templates/`, `prompts/`, `tests/` all collapse under `/artifacts/*`. New root is `/src`, `/bin`, `/artifacts`, `/data`, `/app`, `/pipeline`. `/app` and `/pipeline` land as scaffolds with READMEs.

4. **Phase 0 objective reframed.** Phase 0 is no longer "NZXT-only authoring" — it's **"clone soc-foundry/aho on a second Arch box (P3) and deploy LLMs + MCPs + agents via the `/bin` wrapper package."** CLAUDE.md and GEMINI.md both get rewritten once in 0.1.13 W1 as universal Phase 0 files reflecting this objective. Legacy iao prose in both files is cleared. Per-phase universal rule still holds after 0.1.13 — they don't get touched again until Phase 1.

0.1.13 is designed long and ambitious — W0–W6 in a single overnight Gemini run. Split-agent model: Gemini rips W0–W5, Claude Code handles W6 dogfood + close if needed. Capability-gap interrupts expected in W5 for any sudo-adjacent install operations.

---

## Reference: The Eleven Pillars

1. **Delegate everything delegable.** The paid orchestrator decides; the local free fleet executes.
2. **The harness is the contract.** Instructions live in versioned harness files, not model context.
3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out.
4. **Wrappers are the tool surface.** Every tool is invoked through a `/bin` wrapper.
5. **Three octets, three meanings: phase, iteration, run.**
6. **Transitions are durable.** State written before any transition.
7. **Generation and evaluation are separate roles.** Drafter and reviewer are different agents.
8. **Efficacy is measured in cost delta.** Wall clock, token cost, delegate ratio are ground truth.
9. **The gotcha registry is the harness's memory.**
10. **Runs are interrupt-disciplined, not interrupt-free.** Only capability gaps halt.
11. **The human holds the keys.** No agent writes to git or manages secrets.

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Run report generated 2026-04-11T03:37:40Z, closed 2026-04-11*
