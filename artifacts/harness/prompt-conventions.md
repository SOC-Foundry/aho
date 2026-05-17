## Prompt Conventions

This document serves as the living playbook for prompt writers instructing aho agents (e.g., Claude Code, Gemini CLI, Qwen). It institutionalizes the learnings and tacit knowledge acquired through iterations to prevent drift and ensure clean, objective handoffs.

## 1. Canonical Command References
- **Let configuration own paths:** Always use generic tool invocations like `pytest` instead of path-specific overrides like `pytest tests/`. 
- Trust that `pyproject.toml` or other project configuration will resolve `testpaths`. Hardcoding specific directories in prompts often bypasses important tests or forces the executor to create dummy files to satisfy a malformed prompt instruction (see aho-G079).

## 2. Acceptance Principles
- **Behavior over Numbers:** Prefer behavioral assertions (e.g., "no new failures beyond baseline") over rigid numeric counts (e.g., "N+ passed"). Numeric counts invite gamified behavior such as inflating test outputs with empty dummy cases.
- **Semantic over Exact Match:** Instead of expecting exact string matches, prefer semantic patterns or specific error indicators that are robust across different terminal environments, test runner versions, and executors.

## 3. Context Over Rules
- **Reference, Don't Restate:** Prompts should cite relevant prior iterations, gotchas, and pattern references as required reading material rather than restating them as explicit rules in the prompt body. This maintains the harness as the single source of truth (Pillar 2).

## 4. Celebration Discipline
- **Report Neutrally:** Present outcomes objectively. Let the facts be celebratory if they genuinely are. 
- Avoid phrases like "clean close", "landed beautifully", or "all green" when underlying metrics indicate mixed realities, regressions, or unresolved edge cases (see aho-G081). 

## 5. Anti-Gaming
- **Flag, Don't Comply:** If an acceptance specification rigidly forces the executor into manufacturing compliance (such as outputting false counts or creating dummy files), the executor should flag this instruction to the planner rather than silently contorting the codebase to meet the broken specification.

## 6. Tacit Knowledge Documentation
- **Whiteboard the Plays:** Any operational convention that emerges through repeated successful usage (e.g., test path routing, standard command flags) must be documented here. Future executors entering the harness must not rely on the tacit knowledge acquired by prior executors (see aho-G080).

## 7. Canonical Repo Paths
- **ADRs live in `artifacts/adrs/`**, not `docs/adr/`. Plan-doc and design-doc references must use the canonical path; do not invent `docs/adr/` paths during drafting (this drift recurred across 0.2.17 — see F-0.2.17-W5-002, closed at the convention layer in 0.2.18 W0).
- **Iteration artifacts live in `artifacts/iterations/<version>/`**, not `docs/iterations/`. Plan, design, build-log, retrospective, acceptance, audit, probes, and bundle artifacts all live under that root.
- **Retrospectives live at `docs/retrospectives/<version>.md`** — the one legitimate `docs/` path in the iteration loop. Do not extend the `docs/` convention to other artifact classes.
- **Harness contracts live in `artifacts/harness/`**: `base.md`, `adversarial-authorship-protocol.md`, `prompt-conventions.md` (this file), `test-baseline.json`. CLAUDE.md and GEMINI.md live at the repo root and reference these.
- Verify against this section before quoting any structural path in a plan-doc or design-doc. Fabricated paths fail at executor-side acceptance; the cost is paid in a re-draft cycle.
