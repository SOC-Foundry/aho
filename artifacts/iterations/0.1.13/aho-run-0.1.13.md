# Run File — aho 0.1.13

**Generated:** 2026-04-10
**Iteration:** 0.1.13
**Phase:** 0
**Status:** Graduated with conditions

## About this Report

W6 close by Claude Code after Gemini CLI executed W0–W5 overnight. Split-agent model: Gemini bulk, Claude Code dogfood + close + path migration fixes.

---

## Workstream Summary

| Workstream | Status | Agent | Summary |
|---|---|---|---|
| W0 | pass | gemini-cli | Environment hygiene, backup, version bump, fleet verified |
| W1 | pass | gemini-cli | CLAUDE.md, GEMINI.md, README.md rewritten; iao prose purged |
| W2 | pass | gemini-cli | agents-architecture.md body + ADR-0001 rewritten; headers bumped |
| W3 | pass | gemini-cli | Folder reorg to `artifacts/*`; paths.py updated; tests green |
| W4 | pass | gemini-cli | `aho doctor` unified; project switch syncs `.aho.json` |
| W5 | pass | gemini-cli | `bin/aho` dispatcher, `bin/aho-install`, `bin/aho-mcp` scaffolded |
| W6 | pass | claude-code | Dogfood, 8 reorg-miss fixes, bundle 123KB §1–§22, close |

---

## W6 Dogfood Findings (carried into 0.1.13 bundle)

Claude Code discovered and fixed stale `docs/` path references W3 missed:

1. `artifacts/tests/test_doctor.py` — asserted `iao_json` key, updated to `aho_json`.
2. `src/aho/bundle/__init__.py` — `DOCS_DIR` pointed to `PROJECT_DIR / "docs"`, updated to use `get_artifacts_root()`.
3. Six postflight modules (`run_complete.py`, `bundle_quality.py`, `run_quality.py`, `pillars_present.py`, `build_log_complete.py`, `iteration_complete.py`) — hardcoded `root / "docs" / "iterations"`, updated to `root / "artifacts" / "iterations"`.

Tests: 57/57 green. Bundle: 123KB, §1–§22 present, validation PASS. Doctor: 4 ok / 2 warn (pre-existing: empty MANIFEST.json, missing fish marker).

**Postflight false positives:** `pillars_present` + `structural_gates` failed because 0.1.13 design uses W-based workstream layout, not §-based template the gate expects. Carried to 0.1.14 as gate repair.

**§22 component count:** 4, down from 6 in 0.1.12. Expected — 0.1.13 was a reorg/docs run, not an agent execution run. `openclaw` and `qwen-client` were never invoked. §22 is a per-run manifest, not a target count.

---

## Agent Questions — Answered

1. **Missing manual build log for 0.1.13.** *Accepted.* Split-agent overnight runs without Claude Code pair-proving will not have manual build logs. Checkpoint + event log + W6 run report are sufficient ground truth for ADR-042 for this run only. **This does not happen again.** 0.1.14 W3 builds an auto-generated build log stub generator that runs from checkpoint + event log so the `(missing)` state is impossible on future split-agent runs.

2. **Pre-existing doctor warns (empty MANIFEST.json, missing fish marker).** Fold into 0.1.14 W0 hygiene.

3. **`docs/iterations/0.1.2/` stub.** Fixed manually — `docs/` moved into `artifacts/docs/`. 0.1.14 W2 flattens option A: `artifacts/docs/iterations/0.1.2/` → `artifacts/iterations/0.1.2/`, then remove `artifacts/docs/` entirely. Historical 0.1.2 lives alongside all other iterations; iao-prefixed filenames inside remain as sufficient historical markers.

---

## Kyle's Notes for Next Iteration

0.1.13 landed big — Phase 0 realignment, folder reorg, `/bin` scaffolding, CLAUDE.md/GEMINI.md as universal Phase 0 files. Gemini ran W0–W5 clean overnight. Claude Code caught the W3 reorg misses (8 files) during W6 dogfood — that's exactly why split-agent close exists.

Four carryovers into 0.1.14:

1. **Terminology + code sweep (biggest).** "Agentic Harness Orchestration" → **"Agentic Harness Orchestration"** everywhere. Project code `ahomw` → `ahomw` in ADR prefixes (`ahomw-ADR-*` → `ahomw-ADR-*`), `projects.json`, `base.md`, gotcha registry, script registry, and anywhere else the 5-char code appears. The six canonical harness artifacts (`base.md`, `agents-architecture.md`, `model-fleet.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`) still have residual drift — `ahomw-ADR-*` refs in base.md, "Agentic Harness Orchestration" in README expansion, "ahomw - inviolable" footer in base.md, 0.1.12 footer timestamp in model-fleet.md. Fix all six moving forward.

2. **Build log stub generator.** Split-agent runs must auto-emit a build log from checkpoint + event log. No more `(missing)` for §3.

3. **Postflight gate repair.** `pillars_present` + `structural_gates` over-fit to §-based template. Accept W-based workstream layout as a first-class variant. §22 minimum-by-run-type classification so reorg/docs runs don't falsely trip count gates.

4. **P3 deployment dry-run.** Execute `bin/aho-install` skeleton in a scratch dir on NZXT. Validate XDG path creation, surface capability-gap interrupts as docs updates. Sets up 0.1.15 for actual P3 clone.

Plus hygiene (W0: MANIFEST.json populate, fish marker restore) and reorg cleanup (W2: flatten `artifacts/docs/`).

---

## Reference: The Eleven Pillars

1. Delegate everything delegable.
2. The harness is the contract.
3. Everything is artifacts.
4. Wrappers are the tool surface.
5. Three octets, three meanings: phase, iteration, run.
6. Transitions are durable.
7. Generation and evaluation are separate roles.
8. Efficacy is measured in cost delta.
9. The gotcha registry is the harness's memory.
10. Runs are interrupt-disciplined, not interrupt-free.
11. The human holds the keys.

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Run report closed 2026-04-11, W6 by claude-code*
