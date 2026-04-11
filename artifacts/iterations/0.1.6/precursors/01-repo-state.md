# Investigation 1 — Repo State Snapshot

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Working Tree State

The iao project at `~/dev/projects/iao` is **not a git repository**. There is no `.git` directory. All file state tracking depends on `.iao.json`, `.iao-checkpoint.json`, and file mtimes. This is consistent with Phase 0 (NZXT-only authoring) — git tracking has not yet been initialized for this project.

---

## Iteration Directory Inventory

| Iteration | Files | Notable |
|-----------|-------|---------|
| 0.1.2 | 8 files (design, plan, build-log, bundle, report + .qwen variants + kjtcom-audit) | Complete set. Qwen-generated variants present alongside human-curated ones. |
| 0.1.3 | 6 files (design 53.8KB, plan 51.6KB, build-log 10.9KB, bundle 230KB, report 5.3KB, run-report 824B) | Complete set. Bundle is 230KB — the largest single artifact in the project. |
| 0.1.4 | 6 files (design 63.5KB, plan 59.4KB, build-log 22.8KB, bundle 277KB, report 12.1KB, run-report 3.0KB) | Complete set. All W7 closing artifacts present. |
| 0.1.5 | 2 files (design 34.7KB / 5132 words, plan 26.0KB / 3274 words) | **Incomplete.** Only design and plan exist. No build-log, report, bundle, or run-report. These are Qwen-generated artifacts from a previous session. |
| 0.1.6 | 1 directory (`precursors/`) with the audit prompt file | Empty — this audit is creating the first content. |

---

## Harness Directory

```
docs/harness/
├── base.md        (30,201 bytes) — canonical harness document with ADRs, pillars, trident
└── model-fleet.md (4,180 bytes / 551 words) — model fleet documentation
```

Only 2 files. No `model-fleet-benchmark-0.1.4.md`, no `agents-architecture.md`, no `kjtcom-migration-map.md`. These were planned 0.1.4 deliverables that were never written.

---

## Data Directory

```
data/
└── gotcha_archive.json (6,822 bytes) — 13 entries in a dict with "gotchas" key
```

No `script_registry.json`, no `event_log`, no `iao_event_log.jsonl` in the iao project data directory. However, the kjtcom project has `data/script_registry.json`, `data/iao_event_log.jsonl`, and other registries.

---

## Scripts Directory

```
scripts/
├── benchmark_fleet.py         (1,521 bytes) — model fleet benchmark script
├── build_context_bundle.py    (149 bytes) — stub
├── migrate_kjtcom_harness.py  (3,027 bytes) — kjtcom gotcha migration script
└── query_registry.py          (148 bytes) — stub
```

`build_context_bundle.py` and `query_registry.py` are 148-149 byte stubs. `benchmark_fleet.py` exists but `docs/harness/model-fleet-benchmark-0.1.4.md` (its output) does not — the benchmark was likely never run to completion or its output was not captured. `migrate_kjtcom_harness.py` is the W3 migration script.

---

## Source Package Structure (`src/iao/`)

| Subpackage | Files (excl. `__pycache__`) | Status |
|---|---|---|
| `agents/` | `openclaw.py` (476B stub), `nemoclaw.py` (1033B stub), `roles/assistant.py`, `roles/base_role.py` | **Stubs only.** OpenClaw raises NotImplementedError. NemoClaw delegates to broken OpenClaw. |
| `artifacts/` | `loop.py` (10KB), `qwen_client.py` (2KB), `nemotron_client.py` (1.5KB), `glm_client.py` (781B), `context.py` (1KB), `schemas.py` (1.9KB), `templates.py` (2.3KB) | **Functional.** Core artifact loop and model clients all have real implementations. |
| `data/` | `firestore.py` (7.3KB) | Content — Firestore integration from kjtcom. |
| `feedback/` | `run_report.py` (5.5KB), `questions.py` (2KB), `prompt.py` (996B), `seed.py` (1.4KB), `summary.py` (1.1KB) | **Functional.** Run report reads checkpoint at render time (W1.1 fix landed). |
| `pipelines/` | `pattern.py`, `registry.py`, `scaffold.py`, `validate.py` | Content — pipeline scaffolding. |
| `postflight/` | 12 source files + stale `.pyc` files for `claw3d_version_matches`, `deployed_claw3d_matches`, `deployed_flutter_matches`, `map_tab_renders`, `firestore_baseline` | Mixed. Active checks: `artifacts_present.py`, `build_gatekeeper.py`, `bundle_quality.py`, `gemini_compat.py`, `iteration_complete.py`, `run_report_quality.py`, etc. Stale `.pyc` files for kjtcom-specific checks that have been removed from source but not cleaned from cache. |
| `preflight/` | `checks.py` (3.9KB) | Content — environment validation checks. |
| `rag/` | `archive.py` (4.3KB), `query.py` (4.0KB), `router.py` (4.7KB) | **Functional.** ChromaDB integration works — 3 collections seeded (iaomw: 17, tripl: 144, kjtco: 282). |
| `secrets/` | `cli.py`, `store.py`, `session.py`, `backends/age.py`, `backends/fernet.py`, `backends/keyring_linux.py`, `backends/base.py` | Content — full secrets management with multiple backends. |
| `telegram/` | `__init__.py` (129B), `notifications.py` (1.9KB) | **Minimal.** Only `send_message` and `send_iteration_complete`. No bot framework, no `init`/`status` commands. |

---

## Configuration Files

### `.iao.json`
```json
{
  "iao_version": "0.1",
  "name": "iao",
  "project_code": "iaomw",
  "artifact_prefix": "iao",
  "current_iteration": "0.1.4",
  "phase": 0,
  "mode": "active",
  "created_at": "2026-04-08T12:00:00+00:00",
  "bundle_format": "bundle",
  "last_completed_iteration": "0.1.3"
}
```

**Key finding:** `current_iteration` is still `"0.1.4"` and `last_completed_iteration` is `"0.1.3"`. This means 0.1.4 was never formally closed via `.iao.json` update despite the run report being signed off. The checkpoint says W7 is complete, but `.iao.json` was never bumped.

### `.iao-checkpoint.json`
```json
{
  "iteration": "0.1.4",
  "phase": 0,
  "current_workstream": "review_pending",
  "workstreams": {
    "W0": {"status": "complete"},
    "W1": {"status": "complete"},
    "W2": {"status": "complete"},
    "W3": {"status": "paused", "reason": "ambiguous_review"},
    "W4": {"status": "partial"},
    "W5": {"status": "partial"},
    "W6": {"status": "complete"},
    "W7": {"status": "complete"}
  },
  "completed_at": null,
  "mode": "single-executor"
}
```

**Key finding:** `completed_at` is `null`. The iteration was never formally completed. `current_workstream` is `"review_pending"` which suggests the close sequence ran partway but Kyle's manual sign-off in the run report did not trigger `.iao.json` update.

---

## Backup and Temp Files

- `~/dev/projects/iao.backup-pre-0.1.4` does **not exist**. The plan called for creating it in pre-flight A.1, but it was never created (or was deleted).
- No `/tmp/iao-0.1.4-*` or `/tmp/iao-0.1.5-*` files found.

---

## What This Tells Us

### (a) Workstream deliverables that left actual artifacts on disk

- **W0** (bookkeeping): Version bumped in pyproject.toml, `.iao.json` partially updated (version string present but iteration state inconsistent).
- **W1** (cleanup): Run report checkpoint-read fix landed in `run_report.py`. `questions.py` exists with both extraction functions. `run_report_quality.py` exists. BUNDLE_SPEC has 21 sections. `iao doctor quick` works. `log workstream-complete` takes 3 positional args. Version regex validator works. `age` binary is installed.
- **W2** (model fleet): All 4 models installed in Ollama. `nemotron_client.py`, `glm_client.py`, `context.py` all exist. `archive.py` exists with RAG functions. ChromaDB seeded with 3 archives (443 total documents). `model-fleet.md` exists (551 words). ADR-035 present in base.md.
- **W6** (Gemini-primary): README updated. CLAUDE.md is the short pointer. `gemini_compat.py` exists. ADR-039 present in base.md.
- **W7** (closing): Build log (535 lines), report (155 lines), run-report (70 lines), bundle (5731 lines, 39 `## §` headers) all exist.

### (b) Deliverables that left only partial traces

- **W3** (kjtcom migration): 8 of an unknown total kjtcom gotchas migrated with `kjtcom_source_id` markers. No `kjtcom-migration-map.md`. ADR-036 not found. Ambiguous pile file never written to `/tmp/`. Migration script exists but pause mechanism was never exercised.
- **W4** (Telegram): Only `notifications.py` with `send_message` and `send_iteration_complete`. No bot framework. `iao telegram test` is the only subcommand. Secrets store has `TELEGRAM_BOT_TOKEN` for kjtco. ADR-037 not found.
- **W5** (OpenClaw/NemoClaw): Both files exist but are stubs — `OpenClaw.chat()` raises `NotImplementedError`, `NemoClaw` delegates to broken OpenClaw. No `agents-architecture.md`. No `smoke_nemoclaw.py`. ADR-038 not found. `open-interpreter` imports but version is "unknown". Roles directory has minimal base scaffolding.

### (c) What was in flight when the last agent session ended

The last agent session (Gemini CLI) completed W7 closing artifacts but did not formally close the iteration. `.iao.json` still shows `current_iteration: "0.1.4"` and `completed_at: null`. A subsequent session (likely Gemini or Claude) generated the 0.1.5 design and plan documents via the Qwen artifact loop, but 0.1.5 execution never began — no build log, no checkpoint for 0.1.5, no version bump to 0.1.5 in `.iao.json`.
