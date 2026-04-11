# aho 0.1.13 — Design

**Phase:** 0
**Iteration:** 0.1.13
**Theme:** Phase 0 realignment, folder reorg, `/bin` wrapper scaffolding, global deployment prep
**Estimated wall clock:** 10–14 hours (overnight Gemini run, W0–W5; Claude Code W6)
**Primary executor:** Gemini CLI (`gemini --yolo`)
**Closer:** Claude Code (`claude --dangerously-skip-permissions`) for W6 if needed

---

## Phase 0 Objective (Reframed)

**Phase 0 is complete when soc-foundry/aho can be cloned on a second Arch Linux box (ThinkStation P3) and deploy LLMs, MCPs, and agents via the `/bin` wrapper package with zero manual Python edits.** NZXTcos remains the authoring machine; P3 is the UAT target for clone-to-deploy. This supersedes the prior "NZXT-only authoring" framing.

## Objectives

1. Rewrite CLAUDE.md and GEMINI.md as universal Phase 0 agent instructions reflecting the clone-to-deploy objective. Purge all legacy iao prose. These are per-phase files and get rewritten once here.
2. Sweep harness and ADR documentation prose for stale iao references. `agents-architecture.md` body, `0001-phase-a-externalization.md`, and any other `.md` under current `docs/` with narrative drift.
3. Consolidate folder layout. Collapse `docs/`, `scripts/`, `templates/`, `prompts/`, `tests/` into `/artifacts/*`. Establish `/src`, `/bin`, `/artifacts`, `/data`, `/app`, `/pipeline` as the canonical top-level roots.
4. Build `/bin` wrapper scaffolding. Pattern doc, template, one reference wrapper (openclaw) showing instrumentation, event log, replay contract.
5. Prep global deployment. XDG paths, install script skeleton, credential templates, capability-gap interrupt docs for sudo operations.
6. Dogfood end-to-end on NZXTcos; capture any P3-specific gotchas as deferred items for 0.1.14.

## Non-goals

- Actual P3 deployment execution (that's 0.1.14+).
- Riverpod or kjtcom work.
- Git operations of any kind (Pillar 11).
- Rewriting historical iteration artifacts (0.1.2–0.1.8 keep iao-prefixed filenames as historical record).
- Touching `docs/phase-charters/iao-phase-0.md` beyond moving it to `/artifacts/phase-charters/`.

## Workstreams

### W0 — Environment hygiene + backup
Bump `.aho.json` and `.aho-checkpoint.json` to 0.1.13. Tarball current repo state to `~/dev/backups/aho-pre-0.1.13.tar.gz`. Mask sleep/suspend. Verify Ollama models loaded. Verify ChromaDB `aho_archive` collection intact.

### W1 — Phase 0 rewrite (CLAUDE.md + GEMINI.md + README)
Rewrite `CLAUDE.md` and `GEMINI.md` from scratch as universal Phase 0 agent instructions. New objective (clone-to-deploy on P3). Eleven Pillars verbatim from `base.md`. Split-agent model documented. Gotcha registry query-first enforced. Purge every iao reference. Sync README Phase 0 section and exit criteria to match new objective. README stays at repo root.

### W2 — Harness + ADR prose sweep
Grep sweep across current `docs/**/*.md` for stale iao narrative (case-insensitive, prose not code). Surgical rewrites on `agents-architecture.md` body (opening paragraph, P3 Diligence section, footer), `adrs/0001-phase-a-externalization.md` (full rewrite, status stays Accepted), plus any other hits. Headers and version labels bump to 0.1.13. Do not touch historical iteration artifacts 0.1.2–0.1.8.

### W3 — Folder reorg (execution)
Execute the collapse. New layout:

```
~/dev/projects/aho/
├── src/aho/              (unchanged)
├── bin/                  (CLI + wrappers, expanded in W4)
├── artifacts/
│   ├── harness/          (from docs/harness/)
│   ├── adrs/             (from docs/adrs/)
│   ├── iterations/       (from docs/iterations/)
│   ├── phase-charters/   (from docs/phase-charters/)
│   ├── roadmap/          (from docs/roadmap/)
│   ├── scripts/          (from scripts/)
│   ├── templates/        (from templates/)
│   ├── prompts/          (from prompts/)
│   └── tests/            (from tests/)
├── data/                 (unchanged)
├── app/                  (new, scaffold + README)
├── pipeline/             (new, scaffold + README)
├── .aho.json
├── .aho-checkpoint.json
├── pyproject.toml
├── install.fish
├── CLAUDE.md
├── GEMINI.md
└── README.md
```

Update `src/aho/paths.py` (or equivalent resolver) to use new artifact roots. Update every Python import referencing `scripts/`, `templates/`, `prompts/`, `tests/`. Update `pyproject.toml` test paths. Update `install.fish`. Update every doc cross-reference. Run full test suite after moves; zero regressions gate.

### W4 — `/bin` wrapper scaffolding
Write `artifacts/harness/bin-wrapper-pattern.md`: what a wrapper is (Pillar 4), required instrumentation hooks (event log call, input capture for replay, exit code propagation), fish syntax constraints, capability-gap interrupt contract. Produce `bin/wrapper-template.fish`. Produce reference implementation `bin/openclaw` showing the full shape. Wrapper surfaces must never expose `git commit` or `git push` (Pillar 11).

### W5 — Global deployment prep
Design XDG layout: `~/.local/bin/aho-*` (wrapper symlinks), `~/.config/aho/` (credentials, model fleet config), `~/.local/share/aho/` (event log, ChromaDB on deployed hosts). Write `bin/aho-install` skeleton — idempotent fish installer that clones/updates, creates XDG dirs, symlinks wrappers, runs `iao doctor` equivalent. Credential template in `artifacts/templates/credentials.example.fish`. Document capability-gap interrupts Kyle will need to handle manually on P3 (sudo package installs, Ollama service enable, ChromaDB init). Do NOT attempt any sudo operations on NZXTcos during this run — design only.

### W6 — Dogfood + close
Full test suite. `aho doctor`. Regenerate bundle. Verify §1–§21 spec. Verify §22 component checklist unchanged at 6. Run postflight gates. Populate run file. Hand off to Kyle.

## Risks

- **Folder reorg surface area.** Touches every import and every doc cross-reference. Mitigation: W0 backup, test suite as regression gate, `rg` sweep post-move for missed references.
- **Prose sweep false negatives.** `rg -i "iao"` will hit code strings and historical filenames. Mitigation: scope to narrative prose only, whitelist 0.1.2–0.1.8 iteration dirs, whitelist code identifiers.
- **Qwen synthesis budget.** 6-workstream run with heavy doc generation. Mitigation: manual build log is authoritative (ADR-042), synthesis is optional commentary.
- **CLAUDE.md / GEMINI.md rewrite getting bundled into per-run artifacts.** Mitigation: explicit note in W1 — these files are per-phase, Kyle has overruled the per-run restriction for this specific run only.

## Success criteria

- CLAUDE.md and GEMINI.md contain zero `iao` references (except historical notes).
- `rg -i "iao"` across `artifacts/harness/` and `artifacts/adrs/` returns only whitelisted historical references.
- New folder layout matches spec; zero broken imports; full test suite passes.
- `bin/openclaw` wrapper executes end-to-end on NZXTcos.
- `bin/aho-install` skeleton exists with complete capability-gap interrupt documentation.
- Bundle §1–§22 pass. Sign-off #5 = `[x]`.
