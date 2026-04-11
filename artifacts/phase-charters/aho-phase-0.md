# Phase 0 Charter — aho

**Phase:** 0 — NZXT-only authoring → clone-to-deploy on P3
**Charter version:** 0.2.4
**Charter date:** 2026-04-11
**Status:** active

---

## Why This Phase Exists

Phase 0 is complete when **soc-foundry/aho can be cloned on a second Arch Linux box (ThinkStation P3) and deploy LLMs, MCPs, and agents via the `/bin` wrapper package with zero manual Python edits.** NZXTcos is the authoring machine. P3 is the UAT target for clone-to-deploy. Phase 0 ends when `git clone` + `bin/aho-install` on P3 produces a working aho environment with local model fleet operational.

## Iteration Boundaries

- **Iteration 1 (0.1.0–0.1.16)** — Build the harness. Graduated 2026-04-11.
- **Iteration 2 (0.2.x)** — Ship to soc-foundry + P3 clone-to-deploy. Active.
- **Iteration 3 (0.3.x)** — Alex demo + claw3d + polish. Planned.

## Phase Objectives

1. **Build the harness (Iteration 1, 0.1.x)** — Secrets, artifact loop, src-layout, terminology, components, OTEL, mechanical reports, postflight gates, close sequence. Graduated 2026-04-11.
2. **Ship to soc-foundry + P3 (Iteration 2, 0.2.x)** — soc-foundry initial push, openclaw/nemoclaw global wrappers, telegram bridge, P3 clone + smoke test.
3. **Polish + claw3d + Alex demo (Iteration 3, 0.3.x)** — Alex SF demo prep, claw3d scaffold, novice operability.
4. **Phase 0 graduates** when P3 + Alex validation lands clean.

## Exit Criteria

- [x] aho installable as Python package on NZXT — achieved 0.1.0
- [x] Secrets architecture (age + OS keyring) functional — achieved 0.1.2
- [x] Qwen artifact loop scaffolded end-to-end — achieved 0.1.2
- [x] Bundle quality gates enforced — achieved 0.1.3
- [x] src-layout with `src/aho/` — achieved 0.1.3
- [x] Human feedback loop with run report + seed mechanism — achieved 0.1.3
- [x] IAO → AHO rename complete — achieved 0.1.9
- [x] Build log split: manual authoritative + Qwen synthesis — achieved 0.1.9
- [x] Iteration artifacts in `artifacts/iterations/<version>/` — achieved 0.1.13
- [x] Component manifest system with `aho components` CLI — 0.1.15
- [ ] Mechanical report builder replaces Qwen-first reports — 0.1.15
- [ ] openclaw/nemoclaw global wrappers installable — 0.1.16
- [ ] telegram bridge real implementation — 0.1.16
- [ ] soc-foundry/aho initial push — 0.1.16
- [ ] P3 clone-to-deploy succeeds — 0.1.16
- [ ] Alex validation / SF demo — 0.1.17
- [ ] Multi-run ship gauntlet clean — 0.18.x
- [ ] Phase 0 graduates to Phase 1

## Iteration Roadmap

| Iteration | Theme | Status |
|---|---|---|
| 1 (0.1.x) | Build the harness | graduated 2026-04-11 |
| 2 (0.2.x) | Ship to soc-foundry + P3 | active |
| 3 (0.3.x) | Alex demo + claw3d + polish | planned |
| Phase 1 | Multi-project, multi-machine | planned |

## Charter Revision History

| Version | Date | Iteration | Change |
|---|---|---|---|
| 0.1 | 2026-04-09 | 0.1.3.1 | Retroactive charter (iao-phase-0.md) |
| 0.1.15 | 2026-04-11 | 0.1.15 | Rewritten to current clone-to-deploy objective, renamed aho-phase-0.md |
| 0.1.16 | 2026-04-11 | 0.1.16 | Iteration 1 graduation, 3-iteration structure, aho.run |
