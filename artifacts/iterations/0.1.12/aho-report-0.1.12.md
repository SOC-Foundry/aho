# Report

**Run:** 0.1.12
**Phase:** 0
**Status:** Complete

## Summary

Iteration 0.1.12 graduated successfully. This maintenance run targeted four specific conditions carried forward from 0.1.11, focusing on evaluator stability, instrumentation accuracy, and documentation hygiene. The iteration completed within the 2.5-hour wall clock target, demonstrating that the dynamic baseline approach and checkpoint-aware instrumentation are viable without significant performance penalty. Two new failure modes were registered in the gotcha archive (aho-G060, aho-G061), increasing the harness's memory of failure modes. The orchestrator spent its minutes on judgment and scope, delegating execution to the local fleet, adhering to Pillar 1.

## Workstream Scores

| Workstream | Duration | Status | Outcome |
|---|---|---|---|
| W0 — Environment Hygiene | 15 min | Pass | Version bump, backup, install |
| W1 — Evaluator Reload | 60 min | Pass | Baseline reload fix (aho-G060) |
| W2 — Smoke Checkpoint | 30 min | Pass | Iteration stamp fix (aho-G061) |
| W3 — Doc Cleanup | 20 min | Pass | IAO→aho rename, Pillar refs |
| W4 — Dogfood + Close | 45 min | Pass | All 7 verification checks pass |

## Workstream Outcomes

**W0 — Environment Hygiene**
W0 established the baseline state for the iteration. It verified the project root (`~/dev/projects/aho`) and bumped the version to 0.1.12 in `src/aho/cli.py` and `pyproject.toml`. Crucially, it backed up the three files W1-W3 would modify (`evaluator.py`, `smoke_instrumentation.py`, `model-fleet.md`) before making changes. This ensured rollback capability without relying on git history. The manual build log was initialized, satisfying the requirement that every task is artifacts-in to artifacts-out.

**W1 — Evaluator Baseline Reload (aho-G060)**
W1 addressed the critical synthesis rejection loop observed in 0.1.11. The evaluator previously loaded its allowed-files baseline at module init, making it blind to files created mid-run. W1 replaced the global cache with a per-call computation inside `evaluate_text()`. This added ~10ms overhead but restored correctness. A regression test (`tests/test_evaluator_reload.py`) was added to ensure newly created scripts are recognized immediately. The gotcha `aho-G060` was registered in `data/gotcha_archive.json`, documenting the dynamic baseline requirement.

**W2 — Smoke Instrumentation Checkpoint Awareness (aho-G061)**
W2 fixed the iteration-stamp bug in `smoke_instrumentation.py`. Previously, the script read the iteration from an environment variable that did not reflect the latest checkpoint bump. W2 modified the script to read the current iteration directly from `.aho-checkpoint.json` at startup. This ensures event logs always reflect the actual execution context. The smoke test confirmed that events emitted during the run were stamped with `"iteration": "0.1.12"`. The gotcha `aho-G061` was registered to enforce this pattern across all event emitters.

**W3 — Model Fleet Documentation Cleanup**
W3 updated `docs/harness/model-fleet.md` and `docs/harness/agents-architecture.md`. All references to the historical "IAO" identifier were replaced with "aho" to align with the current project name. The version header was updated from 0.1.4 to 0.1.12. References to the retired "Trident" prong were replaced with citations to Pillar 1 (Delegate) and Pillar 8 (Cost Delta). Stale speculation from 0.1.5 was removed from the future extensions section. This work ensures the harness remains a current contract for agents.

**W4 — Dogfood + Close**
W4 executed the verification loop against the modified artifacts. Seven checks were performed: synthesis file non-empty, event log stamps, documentation cleanliness, component count, manual build log presence, run file naming, and test suite health. All checks passed. The iteration was closed, and the bundle was finalized.

## Lessons and Carry-overs

The primary lesson is that correctness in the evaluator outweighs the minor latency cost of reloading the baseline. The 2-hour rejection loop in 0.1.11 was unacceptable, and the ~10ms overhead is a necessary trade-off for stability. The checkpoint-read pattern for instrumentation is now a standard requirement for any script emitting events.

Documentation hygiene (W3) revealed that historical artifacts still contained legacy identifiers. This reinforces the need for regular harness reviews. The gotcha registry now contains two new entries, increasing the compound-interest metric of harness maturity.

For 0.1.13+, the scope will broaden beyond maintenance. The current stability foundation allows for broader feature integration. No new conditions were added; the iteration graduated cleanly. The human holds the keys, and the next iteration will build upon this stable baseline.
