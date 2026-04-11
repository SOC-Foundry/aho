# Iteration 2 Charter — aho

**Iteration:** 2 (runs 0.2.1–0.2.x)
**Opens:** 2026-04-11
**Phase:** 0

---

## Iteration 2 Objective

Ship aho to soc-foundry/aho and validate clone-to-deploy on ThinkStation P3.

---

## Entry Criteria (from Iteration 1 graduation)

- [x] aho installable as Python package
- [x] Secrets architecture functional
- [x] Folders consolidated to /artifacts/
- [x] /bin wrapper scaffolding established
- [x] Agent instructions written
- [x] Close sequence mechanically correct
- [x] 80+ tests passing
- [x] Component manifest with status tracking

---

## Exit Criteria

- [ ] soc-foundry/aho repository live on GitHub
- [ ] P3 `git clone` + `bin/aho-install` succeeds without manual Python edits
- [ ] `aho doctor full` passes on P3
- [ ] Smoke test (artifact loop end-to-end) passes on P3
- [ ] openclaw status = `active` (not `stub`)
- [ ] nemoclaw status = `active` (not `stub`)
- [ ] telegram bridge status = `active` (not `stub`)

---

## Planned Runs

| Run | Theme |
|---|---|
| 0.2.1 | Cleanup + soc-foundry initial push + openclaw/nemoclaw global wrappers + telegram bridge |
| 0.2.2 | P3 clone attempt + smoke test + capability gap capture |
| 0.2.3+ | Whatever P3 surfaces, fix in tight runs |

---

## Iteration 2 Graduates When

P3 runs an aho iteration end-to-end: `git clone` → `bin/aho-install` → `aho doctor full` green → artifact loop produces a bundle.

---

*Iteration 2 charter — aho Phase 0. Created 2026-04-11 during 0.1.16 W1.*
