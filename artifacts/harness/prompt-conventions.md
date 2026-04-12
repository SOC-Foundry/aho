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
