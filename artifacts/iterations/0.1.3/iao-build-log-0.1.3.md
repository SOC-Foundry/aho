# Build Log — iao 0.1.3.1

**Start:** 2026-04-09T14:00:00Z
**Agent:** claude-code (Claude Opus 4.6)
**Machine:** NZXTcos
**Phase:** 0 (NZXT-only authoring)
**Iteration:** 0.1.3.1
**Theme:** Bundle quality hardening, folder consolidation, src-layout refactor, pipeline scaffolding, human feedback loop

---

## Pre-flight

Pre-flight checks completed with the following state:
- Working directory: `/home/kthompson/dev/projects/iao` — confirmed
- Backup created: `~/dev/projects/iao.backup-pre-0.1.3` (1.2 MB)
- Git state: not a git repository (Phase 0, no remote yet)
- Python: 3.14.3 at `/usr/bin/python3`
- iao package: 0.1.0 installed at `~/.local/bin/iao`
- Ollama: running, qwen3.5:9b and nomic-embed-text present
- Disk: 739G free on `/dev/nvme0n1p2`
- Tools: jq present, age not found (non-blocking)

**Discrepancies encountered:**
- `.iao-checkpoint.json` showed iteration 0.1.2 (not 0.1.3.1) — Gemini CLI W0–W5 had not been executed. The design and plan docs existed at `artifacts/docs/iterations/0.1.3/` in the pre-W1 location, confirming the planning phase completed but execution hadn't started.
- `iao doctor quick` command does not exist in the CLI — the `doctor` subcommand was never added to argparse, though `doctor.py` has `run_all()`. Post-flight and pre-flight work via separate subcommands.
- The `age` binary was not found, though the secrets backend module exists. Non-blocking for this iteration.

**Decision:** Execute all 8 workstreams (W0–W7) as a single-agent run with Claude Code, since Gemini's W0–W5 was not completed. Kyle confirmed this approach.

---

## W0 — Iteration Bookkeeping

**Status:** COMPLETE
**Wall clock:** ~2 min

Actions:
- Updated `.iao.json`: `current_iteration` from `"0.1.3"` to `"0.1.3.1"`, `phase` from `1` to `0`
- Updated `VERSION` from `0.1.0` to `0.1.3`
- Updated `pyproject.toml` version from `0.1.0` to `0.1.3`
- Updated CLI `VERSION` string in `cli.py` from `"iao 0.1.0"` to `"iao 0.1.3"`
- Created new `.iao-checkpoint.json` with W0–W7 workstream tracking
- Verified: `iao --version` returns `iao 0.1.3`

---

## W1 — Folder Consolidation

**Status:** COMPLETE
**Wall clock:** ~10 min

Actions:
- Created `docs/{iterations,phase-charters,archive,drafts}` directories
- Moved `artifacts/docs/iterations/*` → `docs/iterations/` (0.1.2 and 0.1.3 directories)
- Removed empty `artifacts/docs/iterations`, `artifacts/docs`, `artifacts/` via rmdir
- `iao/docs/harness/` not empty (contains `local-global-model.md`) — left intact as package-internal doc
- Updated path references:
  - `iao/artifacts/loop.py`: `_iteration_dir()` now reads from `docs/iterations/`
  - `iao/logger.py`: build log path updated to `docs/iterations/<version>/`
  - `iao/bundle.py`: harness path changed from `iao/docs/harness/` to `docs/harness/`, MANIFEST/install/COMPAT paths changed from `iao/` prefix to project root, `_find_doc()` now searches `docs/iterations/<version>/`, file inventory scans project root
- All 30 tests pass (1 skipped)

---

## W2 — src-layout Refactor

**Status:** COMPLETE
**Wall clock:** ~8 min

Actions:
- Created `src/` directory
- Moved `iao/` (the package) to `src/iao/`
- Old `iao/` directory removed (empty after move)
- Updated `pyproject.toml` with `[tool.setuptools.packages.find] where = ["src"]`
- Removed `iao.egg-info/`, reinstalled via `pip install -e . --break-system-packages`
- Verified: `python3 -c "import iao; print(iao.__file__)"` → `src/iao/__init__.py`
- Added `iaomw-G104` to gotcha registry (flat-layout shadows repo name)
- Updated `COMPATIBILITY.md` with 0.1.3 migration notes
- All 30 tests pass

---

## W3 — Universal Bundle Spec + Quality Gates

**Status:** COMPLETE
**Wall clock:** ~20 min

Actions:
- Appended to `docs/harness/base.md`:
  - `iaomw-Pattern-32`: Existence-Only Success Criteria
  - `iaomw-ADR-028`: Universal Bundle Specification (§1–§20 table)
  - `iaomw-ADR-029`: Bundle Quality Gates (50 KB min, 20 sections, per-section min chars)
  - `iaomw-ADR-012-amendment`: Artifact Immutability extends to iao
- Rewrote `src/iao/bundle.py` with `BundleSection` dataclass, `BUNDLE_SPEC` list of 20 sections, `validate_bundle()` function
- Updated all 5 prompt templates with higher minimum word counts:
  - `design.md.j2`: 5000 words, added `{{ trident_block }}` and `{{ ten_pillars_block }}`
  - `plan.md.j2`: 3000 words
  - `build-log.md.j2`: 2000 words
  - `report.md.j2`: 1500 words, added workstream scores table requirement
- Updated `src/iao/artifacts/schemas.py` ARTIFACTS dict with new minimums
- Created `src/iao/postflight/bundle_quality.py`
- Added `iaomw-G105` to gotcha registry (existence-only acceptance criteria)
- Updated test context in `test_artifacts_loop.py` with trident/pillars variables and higher word counts
- All 30 tests pass

---

## W4 — Universal Pipeline Scaffolding

**Status:** COMPLETE
**Wall clock:** ~15 min

Actions:
- Created `src/iao/pipelines/` subpackage with 4 modules:
  - `pattern.py`: `PipelinePattern` class, 10-phase `PHASE_DESCRIPTIONS` dict
  - `scaffold.py`: `scaffold_pipeline()` creates 10 phase files + checkpoint.json + README
  - `validate.py`: `validate_pipeline()` checks all phases have files with `main()`
  - `registry.py`: `list_pipelines()` and `get_pipeline_status()` from `.iao.json`
- Added `iao pipeline` CLI subparser with `init`, `list`, `validate`, `status` commands
- Created `src/iao/postflight/pipeline_present.py` — returns SKIP for projects without pipelines
- Appended `iaomw-ADR-030` (Universal Pipeline Pattern) to base.md
- Smoke test: `iao pipeline init demo` in `/tmp` → 10 phase files + checkpoint + README, `iao pipeline validate demo` passes
- All 30 tests pass

---

## W5 — Human Feedback Loop + Run Report

**Status:** COMPLETE
**Wall clock:** ~15 min

Actions:
- Created `src/iao/feedback/` subpackage with 4 modules:
  - `run_report.py`: generates run report from checkpoint data with workstream table, agent questions, Kyle's notes, sign-off checkboxes
  - `seed.py`: extracts Kyle's notes section from run report as JSON seed for next iteration
  - `summary.py`: renders workstream summary table from checkpoint
  - `prompt.py`: validates sign-off checkboxes in run report
- Created `prompts/run-report.md.j2` Jinja template
- Added `iao iteration close` (generates run report + bundle + summary) and `iao iteration close --confirm` (validates sign-off) to CLI
- Added `iao iteration seed` command
- Created `src/iao/postflight/run_report_complete.py` — returns DEFERRED until Kyle fills in notes
- Appended `iaomw-ADR-031` (Run Report as Canonical Artifact) and `iaomw-ADR-032` (Human Sign-off Required) to base.md
- Reframed `iaomw-Pillar-10` text in base.md to reference run report feedback loop
- All 30 tests pass

---

## W6 — README Sync + Phase 0 Charter Retrofit + 10 Pillars Enforcement

**Status:** COMPLETE
**Wall clock:** ~20 min

Actions:
- Rewrote `README.md` on kjtcom structure:
  - Hero paragraph, status line, trident mermaid, 10 pillars list
  - Component review (42 components across 4 groups, counted from filesystem)
  - Architecture diagram, active iao projects table, Phase 0 status with exit criteria checklist
  - Roadmap, installation, contributing, license
- Created `docs/phase-charters/iao-phase-0.md` from design doc §1 with updated exit criteria checkboxes
- Created 2 new post-flight checks:
  - `src/iao/postflight/ten_pillars_present.py` — verifies trident + all 10 pillars in design doc and README
  - `src/iao/postflight/readme_current.py` — verifies README mtime > iteration start
- Updated `src/iao/artifacts/templates.py` with `_load_harness_blocks()` to extract trident and pillars from base.md at render time
- Appended to base.md: `iaomw-ADR-033` (README Currency), `iaomw-ADR-034` (Trident/Pillars Verbatim), `iaomw-Pattern-33` (README Drift)
- Added `iaomw-G106` to gotcha registry (README falls behind)
- Both new checks PASS: `ten_pillars_present` ok, `readme_current` ok
- All 30 tests pass

---

## W7 — Qwen Loop Hardening + Dogfood + Closing Sequence

**Status:** COMPLETE
**Wall clock:** ~30 min

Actions:
- Rewrote `src/iao/artifacts/loop.py`:
  - Word count enforcement after each Qwen output
  - 3-retry escalation with expanding guidance (Pillar 7)
  - ADR-012 enforcement: skips design/plan generation when immutable files exist
  - Enriched system prompt with trident, pillars, §1–§20 bundle reference
  - Updated workstream list to reflect actual 0.1.3.1 workstreams (W0–W7)
  - Fixed `_iteration_dir()` to parse version from iteration string
- Updated `src/iao/artifacts/templates.py` with `_load_harness_blocks()` for base.md variable injection
- Dogfood test:
  - Qwen build-log generation: 1684 words on attempt 1, 1690 on attempt 2, exhausted 3 retries at ~1700 words (2000 min). Qwen3.5:9b on CPU cannot reliably hit 2000 words for build-log.
  - Per Pillar 7 escalation and Pillar 6 (pick safest path), build log and report written directly by Claude Code as factual execution records rather than Qwen synthesis.
  - Agent Question for Kyle: "Qwen3.5:9b on CPU exhausts 3 retries for build-log at ~1700 words (2000 min). Consider whether to lower the min_words threshold for build-log, or upgrade to a larger model, or accept Claude-authored build logs as the standard for dogfood iterations."
- Bundle generated mechanically via `iao iteration close` (build_bundle)
- CHANGELOG updated with 0.1.3 entry
- `.iao.json` bumped to `0.1.4.0` draft
- Checkpoint updated: all 8 workstreams complete, current_workstream = "review_pending"

---

## Discrepancies Encountered

1. **Gemini W0–W5 not executed:** The plan specified split-agent execution (Gemini W0–W5, Claude W6–W7). Gemini's workstreams were not completed. Claude Code executed all 8 workstreams as a single-agent run per Kyle's instruction.

2. **`iao doctor` CLI command missing:** CLAUDE.md references `iao doctor quick` and `iao doctor postflight` but the CLI only has `preflight` and `postflight` as top-level subcommands. The `doctor.py` module has `run_all()` but it's not wired to an `iao doctor` argparse entry. Post-flight checks work via the dynamic plugin loader in `_postflight_checks()`.

3. **`iao log workstream-complete` requires 3 positional args:** The CLI expects `workstream_id`, `status` (choices: pass/partial/fail/deferred), and `summary`. The CLAUDE.md examples only pass 2 args. Build log entries written directly instead.

4. **Qwen word count ceiling:** Qwen3.5:9b on CPU consistently maxes out around 1700 words per generation, below the 2000-word minimum for build-log. The retry loop works correctly (attempts 3 times with expanding prompts) but Qwen cannot break the ceiling. This is a model limitation, not a harness failure.

5. **`age` binary not installed:** The secrets backend references age but it's not on PATH. Non-blocking for this iteration since secrets are not exercised in W0–W7.

---

**End:** 2026-04-09T16:00:00Z
