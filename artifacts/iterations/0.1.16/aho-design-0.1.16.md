# aho 0.1.16 — Design

**Phase:** 0 | **Iteration:** 0.1.16 | **Theme:** Close sequence repair + iteration 1 graduation
**Agent:** Claude Code single-agent throughout

## The Eleven Pillars

1. Delegate everything delegable. 2. The harness is the contract. 3. Everything is artifacts. 4. Wrappers are the tool surface. 5. Three octets, three meanings. 6. Transitions are durable. 7. Generation and evaluation are separate roles. 8. Efficacy is measured in cost delta. 9. The gotcha registry is the harness's memory. 10. Runs are interrupt-disciplined. 11. The human holds the keys.

## Objective

Fix the close sequence ordering bug surfaced in 0.1.15 (postflight ran before artifact generation), add canonical artifacts discipline, wire run file through report builder, and graduate iteration 1.

## Workstreams

### W0 — Close sequence repair + canonical artifacts + hygiene

Refactored close sequence into explicit ordered steps. Created canonical_artifacts_current.py postflight gate and canonical_artifacts.yaml. Wired run file through report_builder. Version bumps, README fixes, pyproject URLs, aho_json.py helper.

### W1 — Iteration 1 graduation ceremony

Created iteration-1-close.md, iteration-2-charter.md, updated phase-0 charter with iteration boundaries, added README iteration roadmap.

### W2 — Dogfood close sequence

Run corrected close on 0.1.16, verify zero false positives, validate run file attribution.

## Success criteria

- Close sequence runs in correct order: tests → bundle → report → run file → postflight → .aho.json → checkpoint
- All 7 canonical artifacts at 0.1.16
- Run file shows real agent attribution (claude-code, not unknown)
- Zero false-positive postflight failures
- Iteration 1 close artifact and iteration 2 charter exist
