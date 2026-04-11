# aho 0.1.14 — Design

**Phase:** 0
**Iteration:** 0.1.14
**Theme:** Terminology sweep, canonical artifact repair, build log stub generator, postflight gate repair, P3 dry-run
**Estimated wall clock:** 5–7 hours
**Primary executor:** Gemini CLI (`gemini --yolo`)
**Closer:** Claude Code (`claude --dangerously-skip-permissions`) for W6

---

## Context

0.1.13 graduated with conditions. Phase 0 realignment landed, folder reorg executed, `/bin` scaffolding in place. W6 caught eight reorg misses that Gemini missed in W3. Four carryovers remain: terminology drift, build log gap on split-agent runs, postflight gate over-fitting, and residual drift in the six canonical harness artifacts.

## Objectives

1. **Terminology sweep.** Rename "Agentic Harness Orchestration" → "Agentic Harness Orchestration" across all active documentation. Rename project code `ahomw` → `ahomw` in ADR prefixes, registries, base.md footer, and every other live reference. Historical iteration artifacts (0.1.2–0.1.12) remain untouched.
2. **Six canonical artifacts repair.** Full audit and rewrite pass on `base.md`, `agents-architecture.md`, `model-fleet.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`. Every ahomw ref, every stale footer, every residual IAO expansion cleared. These six files become the terminology baseline.
3. **Build log stub generator.** Auto-emit `aho-build-{iteration}.md` from `.aho-checkpoint.json` + `data/aho_event_log.jsonl` when no manual build log exists. Split-agent overnight runs get a populated §3 instead of `(missing)`.
4. **Postflight gate repair.** `pillars_present` + `structural_gates` accept W-based workstream layouts as first-class, not just §-based templates. §22 component checklist adds a minimum-by-run-type classification (reorg/docs runs have a different floor than agent execution runs).
5. **Hygiene + reorg cleanup.** Populate `MANIFEST.json`, restore fish marker block in `install.fish`, flatten `artifacts/docs/iterations/0.1.2/` → `artifacts/iterations/0.1.2/`, remove `artifacts/docs/` entirely.
6. **P3 deployment dry-run.** Execute `bin/aho-install` skeleton in a scratch dir on NZXT. Validate XDG path creation, capture any capability-gap interrupts as `artifacts/harness/p3-deployment-runbook.md` updates.

## Non-goals

- Actual P3 clone execution (0.1.15+).
- Touching historical iteration artifacts 0.1.2–0.1.12 (filenames or prose).
- Riverpod, kjtcom, tripledb work.
- Git operations of any kind (Pillar 11).
- Rewriting ADRs that are already clean (only ahomw→ahomw prefix changes, not full rewrites).

## Workstreams

### W0 — Hygiene + reorg cleanup
Bump `.aho.json` and `.aho-checkpoint.json` to 0.1.14. Backup tarball. Populate `MANIFEST.json` with current package manifest (walk `src/aho/`). Restore fish marker block in `install.fish`. Flatten `artifacts/docs/iterations/0.1.2/` → `artifacts/iterations/0.1.2/`. Remove `artifacts/docs/` tree entirely (verify empty after move). `aho doctor` → 6 ok / 0 warn gate.

### W1 — Terminology sweep (iao → aho, ahomw → ahomw, IAO expansion)
Three-pass sweep:

**Pass 1: "Agentic Harness Orchestration" → "Agentic Harness Orchestration"**
- Grep all `.md` under `artifacts/harness/`, `artifacts/adrs/`, `artifacts/roadmap/`, plus `CLAUDE.md`, `GEMINI.md`, `README.md`.
- Update every full expansion. Update every casual use ("the Iterative Agentic..." variants).
- Mermaid trident chart label: `IAO` stays (it's the acronym for the new expansion too — "Agentic Harness Orchestration" abbreviates awkwardly; keep three-letter shaft text as `AHO` and update).

**Pass 2: `ahomw` → `ahomw`**
- `artifacts/harness/base.md` — footer "ahomw - inviolable" → "ahomw - inviolable", and all ADR prefixes `ahomw-ADR-*` → `ahomw-ADR-*` (ADR-003, 005, 007, 009, 012, 014, 015, 017, 021, 027).
- `projects.json` — entry key `ahomw` → `ahomw`.
- Script registry `data/script_registry.json`.
- Gotcha registry `data/gotcha_archive.json` — any `ahomw-*` prefixes.
- `src/aho/registry.py` — hardcoded prefix strings if any.
- Pattern refs in base.md (`aho-Pattern-*` already correct, verify).

**Pass 3: Residual `iao` narrative prose**
- Sweep for any `iao` still surviving in prose (not filenames, not historical iteration dirs).
- Whitelist: `docs/phase-charters/iao-phase-0.md` (historical filename, now at `artifacts/phase-charters/iao-phase-0.md`) — do not rename file, content already historical.
- Whitelist: everything under `artifacts/iterations/0.1.2/` through `artifacts/iterations/0.1.12/`.

**Gate:** `rg -i "iterative agentic-orchestration" artifacts/ CLAUDE.md GEMINI.md README.md` returns zero. `rg "ahomw" artifacts/ src/ data/ projects.json` returns zero outside historical iteration dirs.

### W2 — Six canonical artifacts repair
Full audit + rewrite pass, in order:

1. **`artifacts/harness/base.md`** — footer `ahomw` → `ahomw`, all ADR prefixes, version bump to 0.1.14. Verify Eleven Pillars unchanged.
2. **`artifacts/harness/agents-architecture.md`** — verify 0.1.13 body rewrite held, bump header to 0.1.14, update footer ("Updated by Gemini CLI during aho 0.1.14 W2").
3. **`artifacts/harness/model-fleet.md`** — footer still says "Document updated for aho 0.1.12 W3" — bump to 0.1.14 W2. Verify no ahomw refs.
4. **`CLAUDE.md`** — verify 0.1.13 rewrite held, add "Agentic Harness Orchestration" expansion if any full expansion is used, bump phase rewrite date.
5. **`GEMINI.md`** — same as CLAUDE.md.
6. **`README.md`** — update trident chart label text (`Agentic Harness Orchestration` → `Agentic Harness Orchestration`), update all body references, bump iteration to 0.1.14, update component count if §22 classification ships.

**Gate:** all six files pass `rg -i "iterative agentic"` → zero, `rg "ahomw"` → zero, header versions all 0.1.14.

### W3 — Build log stub generator
New module `src/aho/feedback/build_log_stub.py`. Signature: `generate_stub(iteration: str) -> Path`.

Behavior:
- Read `.aho-checkpoint.json` for workstream statuses, agents, timestamps.
- Tail `data/aho_event_log.jsonl` filtered to current iteration.
- Emit `artifacts/iterations/{iteration}/aho-build-{iteration}.md` with: header, workstream-by-workstream synthesis (agent, status, event count, first/last timestamp per workstream), event log summary (total events, event type histogram), explicit marker "**Auto-generated from checkpoint + event log. No manual build log was authored for this run.**"

Wire into `aho close` sequence: if manual `aho-build-{iteration}.md` absent at close time, call `generate_stub()` before bundle generation. Bundle §3 then embeds the stub, not `(missing)`.

Test: `artifacts/tests/test_build_log_stub.py` with a fixture checkpoint + event log.

**Gate:** stub generation on 0.1.13 fixture data produces a well-formed build log; bundle §3 validation passes on the stub output.

### W4 — Postflight gate repair
Two changes:

1. **`pillars_present.py` + `structural_gates.py`** — detect layout variant (W-based workstream or §-based template) and apply variant-appropriate checks. Add `LayoutVariant` enum. W-based runs check for W0–Wn headers and workstream summary tables; §-based runs check for §1–§22. Both must produce passing gates.

2. **§22 component checklist minimum-by-run-type.** Add `run_type` classification to checkpoint schema: `{"run_type": "agent_execution" | "reorg_docs" | "hygiene" | "mixed"}`. §22 gate applies floor based on run_type — agent_execution expects ≥6, reorg_docs expects ≥2, hygiene expects ≥1. Classification is declared in the design doc (new required field) and read from checkpoint at close.

Update `aho-design-0.1.14.md` to declare `run_type: mixed` for its own run.

**Gate:** replay 0.1.13 bundle through new gates → all green. New tests in `artifacts/tests/test_postflight_layouts.py` and `test_postflight_run_types.py`.

### W5 — P3 deployment dry-run on NZXT
Scratch dir: `/tmp/aho-p3-dryrun/`. Execute `bin/aho-install --dry-run --target /tmp/aho-p3-dryrun` (add `--dry-run` flag if not present).

Validate:
- XDG paths created (`~/.local/bin/`, `~/.config/aho/`, `~/.local/share/aho/` — but scoped under scratch root, not real XDG, to avoid polluting NZXT).
- Wrapper symlinks created.
- Credential template copied.
- Capability-gap interrupt list matches `artifacts/harness/p3-deployment-runbook.md`.

Any surface issues get captured as runbook updates. Do NOT attempt real XDG writes on NZXT — scratch root only.

**Gate:** dry-run completes cleanly, runbook updated with any surfaced gaps.

### W6 — Dogfood + close (Claude Code)
Full test suite (57+ tests). `aho doctor`. Bundle generation using new build log stub generator if manual log absent (it will be absent since Gemini runs overnight again). Bundle §1–§22 validation. Postflight gates with new layout variant + run_type classification. Populate `aho-run-0.1.14.md`. Handoff.

## Risks

- **Terminology sweep hitting code strings.** `iao` is a common substring. Mitigation: scope Pass 1 to prose patterns only ("Iterative Agentic"), Pass 2 to `ahomw` exact matches, Pass 3 uses word-boundary `\biao\b` with historical whitelist.
- **Build log stub quality.** If event log is sparse, stub will be thin. Mitigation: stub explicitly marks itself as auto-generated; §3 quality gate uses lower threshold for stub-sourced logs.
- **Postflight gate repair touching production gate logic.** Mitigation: new tests first, then refactor, then replay 0.1.13 bundle as regression check.
- **W5 scratch dir leakage.** Mitigation: explicit scratch root arg, no real XDG writes, cleanup at end of W5.

## Success criteria

- Zero "Agentic Harness Orchestration" references in active artifacts.
- Zero `ahomw` references outside historical iteration dirs.
- Six canonical artifacts all at 0.1.14 header, all terminology-clean.
- Bundle §3 populated (not `(missing)`) via auto-generated stub.
- Postflight gates green on W-based layout, §22 classified as `mixed` for 0.1.14.
- `bin/aho-install --dry-run` completes on scratch root.
- Sign-off #5 = `[x]`.
