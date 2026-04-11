# Phase 0 Charter — iao

**Phase:** 0 — NZXT-only authoring
**Charter author:** iao planning chat (retroactive)
**Charter version:** 0.1
**Charter date:** 2026-04-09
**Iteration where chartered:** 0.1.3.1
**Status:** active

---

## Why This Phase Exists

iao was extracted from kjtcom during kjtcom Phase 10. Before iao can be delivered to other engineers and other machines, it has to mature on a single workstation under a single author. Phase 0 is that maturation period. It exists so that the methodology can dogfood itself, surface its own failure modes, and harden its harness against those failures *before* anyone else has to install it. Phase 0 ends when iao is publishable to the public soc-foundry/iao GitHub organization at 0.6.x — a state where a fresh machine can `git clone`, run `install.fish`, and have a working iao environment without the original author intervening.

## Phase Objectives

1. Establish secrets architecture (achieved 0.1.2)
2. Establish artifact loop with Qwen as primary author (scaffolded 0.1.2, hardened 0.1.3)
3. Establish folder layout, naming, and harness conventions (0.1.3)
4. Establish pipeline scaffolding pattern reusable by consumer projects (0.1.3)
5. Establish human feedback mechanism that seeds the next iteration from the previous run's notes (0.1.3)
6. Establish bundle quality gates that prevent existence-only success (0.1.3)
7. Establish telegram framework, global MCP install, ambient agent briefings (0.1.4)
8. Establish cross-platform installer for fish/bash/PowerShell/macOS (0.1.4)
9. Validate iao can produce production-quality artifacts via Qwen loop without chat-authored bootstrap (0.1.5)
10. Reach a state where iao is publishable to soc-foundry/iao (0.6.x — phase exit)

## Phase Entry Criteria (where Phase 0 began)

- iao extracted from kjtcom via kjtcom Phase 10 (achieved kjtcom 10.69.1)
- iao package installable via `pip install -e iao/` (achieved kjtcom 10.66)
- iao authoring environment exists at `~/dev/projects/iao` (achieved kjtcom 10.69.1 W6)
- Pattern-31 (formal phase chartering) added to base.md (achieved kjtcom 10.69.1 W4)
- iao 0.1.0 shipped as broken rc1 to surface 12 findings against a real install
- iao 0.1.2 shipped with secrets + kjtcom strip + Qwen loop scaffolding (graduated with conditions)

## Phase Exit Criteria (Graduation Conditions)

- [x] iao installable as Python package on NZXT — achieved 0.1.0
- [x] Secrets architecture (age + OS keyring) functional — achieved 0.1.2 W1
- [x] kjtcom methodology code migrated into iao authoring location — achieved 0.1.2 W5
- [x] Qwen artifact loop scaffolded end-to-end — achieved 0.1.2 W6
- [x] Bundle quality gates enforced (size + section completeness + content checks) — achieved 0.1.3 W3
- [x] Folder layout consolidated to single `docs/` root — achieved 0.1.3 W1
- [x] Python package on src-layout (`src/iao/`) — achieved 0.1.3 W2
- [x] Universal pipeline scaffolding with `iao pipeline init` CLI — achieved 0.1.3 W4
- [x] Human feedback loop with run report + Kyle's notes seed mechanism — achieved 0.1.3 W5
- [x] README on kjtcom structure with all 10 pillars + trident — achieved 0.1.3 W6
- [x] Phase 0 charter committed to design history — achieved 0.1.3 W6
- [ ] Qwen loop produces production-weight artifacts — 0.1.3 W7
- [ ] Telegram framework + global MCP install + ambient agent briefings — 0.1.4
- [ ] Cross-platform installer (fish/bash/zsh/PowerShell) — 0.1.4
- [ ] Novice operability validation — 0.1.5
- [ ] Buffer iterations 0.2.x–0.5.x consumed if needed
- [ ] iao 0.6.x ships to soc-foundry/iao public repo — Phase 0 graduates

## Iterations Planned in Phase 0

| Iteration | Scope | Status |
|---|---|---|
| 0.1.0 | broken rc1, surfaced 12 findings | shipped |
| 0.1.2 | secrets, kjtcom strip, RAG migration, Qwen loop scaffold | graduated |
| 0.1.3 | bundle quality, folder consolidation, src-layout, pipelines, feedback | **executing** |
| 0.1.4 | telegram framework, MCP global install, cross-platform installer | planned |
| 0.1.5 | integration polish, novice operability validation | planned |
| 0.2.x–0.5.x | buffer iterations | reserved |
| 0.6.x | soc-foundry/iao first push | planned (Phase 0 exit) |
| 0.7.x | tachtech-engineering/iao production fork | planned (Phase 1) |

## Phase Charter Revision History

| Version | Date | Iteration | Change |
|---|---|---|---|
| 0.1 | 2026-04-09 | 0.1.3.1 | Retroactive charter for Phase 0 (W6 deliverable) |
