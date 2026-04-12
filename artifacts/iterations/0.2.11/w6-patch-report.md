# W6 Forensic Patch Report — 0.2.11

**Date:** 2026-04-12
**Trigger:** Kyle post-W6 review — design doc drift uncorrected, gate relaxation was wrong fix
**Scope:** 4 corrective items. No version bump. No postflight re-run.
**Precedent:** 0.2.10 forensic-patch-report.md

---

## Item 1: Design Doc §5 — Canonical 11 Pillars

**Before:**
```
## §5 Ten IAO Pillars

1. **Explicit state** — .aho.json + .aho-checkpoint.json + workstream_events drive all transitions
2. **Verifiable acceptance** — W1-W2 replace prose claims with executable AcceptanceCheck primitives
3. **Per-workstream review** — ON throughout per ADR-044/045; backstop until W2 framework matures
4. **Hybrid iteration shape** — ADR-045 three-type taxonomy: infrastructure + validation + environment/audit
5. **MCP-first** — every workstream declares mcp_used with justification
6. **Install surface canonicity** — `~/.local/share/aho/` as single source of runtime state
7. **Three-persona taxonomy** — W9-W14 validates persona 3; persona 2/1 deferred
8. **Observability live** — OTEL→Jaeger pipeline consumes workstream events + persona 3 runs
9. **Gotcha registry as middleware** — aho-G048 keyring resilience class formalized W15
10. **Chat-first, artifact-second** — this design refined in chat before artifact production
```

**After:**
```
## §5 The Eleven Pillars of AHO

1. **Delegate everything delegable.** The paid orchestrator decides; the local free fleet executes.
2. **The harness is the contract.** Agent instructions live in versioned harness files, not model context.
3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out.
4. **Wrappers are the tool surface.** Every tool is invoked through a `/bin` wrapper.
5. **Three octets, three meanings: phase, iteration, run.** Strategic, tactical, and execution scope.
6. **Transitions are durable.** State is written to a durable artifact before any transition.
7. **Generation and evaluation are separate roles.** Drafter and reviewer are different agents.
8. **Efficacy is measured in cost delta.** Wall clock, token cost, and delegate ratio are ground truth.
9. **The gotcha registry is the harness's memory.** Failure modes are indexed with mitigations.
10. **Runs are interrupt-disciplined.** No preference prompts mid-run; only capability gaps halt.
11. **The human holds the keys.** No agent writes to git or manages secrets.
```

**Root cause:** Planner (Claude chat) produced §5 from memory with fabricated iteration-specific pillar names. Canonical source (README) never read. All 10 "pillars" were invented — none matched the actual 11.

---

## Item 2: Plan Doc §5 Pointer

**Before:**
```
## Ten IAO Pillars
(See design §5 — all 10 inherited verbatim.)
```

**After:**
```
## The Eleven Pillars of AHO
(See design §5 — all 11 inherited verbatim.)
```

**Root cause:** Plan doc inherited the fabricated name and count from the design doc.

---

## Item 3: pillars_present Gate Tightened

**Before:** `pillar_count >= 10` — relaxed in W6 to accommodate the fabricated 10-pillar design.

**After:** `pillar_count == 11` — exact match required, matching README canonical count.

**Root cause:** W6 treated the symptom (gate rejects design with 10 pillars) by relaxing the gate, instead of fixing the source (design doc should have 11 pillars). The relaxation was the wrong fix — it would have allowed any future design with only 10 pillars to pass silently.

**Verification:**
```
$ python -m aho.postflight.pillars_present --iteration 0.2.11
ok: Trident + pillars present in design and README
  ok       design_pillars: All 11 pillars enumerated in design doc
  ok       readme_pillars: All 11 pillars present in README
```

---

## Item 4: Gotcha aho-G073 Registered

**New entry:** `aho-G073 — agent-guidance-can-introduce-canonical-drift`

- **Symptom:** Planner-produced artifacts reference fabricated canonical content
- **Cause:** Planner produces content from memory without ground-truth read of canonical sources
- **Fix:** Read canonical source before producing artifacts. Quote verbatim into decisions.md at W0. Count-based gates catch drift at postflight.
- **Example:** 0.2.11 W6 — planner produced 10 fabricated pillars; canonical is 11

Registered in both `~/.local/share/aho/registries/gotcha_archive.json` and `data/gotcha_archive.json` (27 gotchas total).

---

## Acceptance Results

6/6 checks pass — archived at `acceptance/W6-patch.json`.

| Check | Status |
|---|---|
| design_doc_has_11_pillars | PASS |
| design_doc_contains_canonical_pillars | PASS |
| plan_doc_references_eleven | PASS |
| gate_requires_exactly_11 | PASS |
| gotcha_g073_registered | PASS |
| no_regression (45 tests) | PASS |

## Files Modified

| File | Change |
|---|---|
| `artifacts/iterations/0.2.11/aho-design-0.2.11.md` | §5 replaced with canonical 11 pillars verbatim from README |
| `artifacts/iterations/0.2.11/aho-plan-0.2.11.md` | §5 pointer updated: "Ten IAO" → "Eleven Pillars of AHO", 10 → 11 |
| `src/aho/postflight/pillars_present.py` | Pillar count tightened from >= 10 to == 11 |
| `~/.local/share/aho/registries/gotcha_archive.json` | aho-G073 added |
| `data/gotcha_archive.json` | Synced from installed copy |

## Scope Assessment

Corrective patch on closed workstream W6. No re-open, no version bump, no postflight re-run. All changes are within the 4 items specified. No scope creep. 45 tests pass with zero regressions.

The failure mode (G073) is structural: planner memory produces plausible-but-fabricated canonical content. The gate caught it after the fact; the prevention fix is at W0 (read-then-quote canonical sources into decisions.md).
