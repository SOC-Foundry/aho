# Investigation 4 — Workstream Audit of 0.1.4

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Summary

0.1.4's run report declared: W0 complete, W1 complete, W2 complete, W3 paused, W4 partial, W5 partial, W6 complete, W7 active (later completed in checkpoint). This investigation verifies each declaration against what is actually on disk.

---

## W0 — Iteration Bookkeeping (Claimed: Complete)

| Deliverable | Evidence | Verdict |
|---|---|---|
| Version bumped to 0.1.4 | `pyproject.toml` version, `./bin/iao --version` returns 0.1.4 | **Shipped** |
| `.iao.json` updated | `current_iteration: "0.1.4"` present, but `last_completed_iteration` still `"0.1.3"` | **Partial** — iteration tracked but never formally closed |
| Checkpoint initialized | `.iao-checkpoint.json` exists with full workstream tracking | **Shipped** |

**Verdict: Shipped (with caveat that formal close never ran)**

---

## W1 — 0.1.3 Cleanup (Claimed: Complete)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| **W1.1** Run report checkpoint-read bug | `src/iao/feedback/run_report.py` lines 26-27: reads checkpoint at render time | **Shipped** |
| **W1.2** Question extraction | `src/iao/feedback/questions.py` has `extract_questions_from_build_log` (line 13) and `extract_questions_from_event_log` (line 26) | **Shipped** |
| **W1.3** Run report quality gate | `src/iao/postflight/run_report_quality.py` exists (2554 bytes) | **Shipped** |
| **W1.4** BUNDLE_SPEC 21 sections | `python3 -c "from iao.bundle import BUNDLE_SPEC; print(len(BUNDLE_SPEC))"` → `21` | **Shipped** |
| **W1.5** `iao doctor` subcommand | `./bin/iao doctor quick` runs cleanly: `Doctor quick: CLEAN` | **Shipped** |
| **W1.6** `iao log workstream-complete` | Help shows 3 positional args: `workstream_id`, `{pass,partial,fail,deferred}`, `summary` | **Shipped** |
| **W1.7** Version regex validator | `validate_iteration_version('0.1.4.0')` raises `ValueError` with correct message about three-octet format | **Shipped** |
| **W1.8** age binary | `which age` → `/usr/bin/age`, `age --version` → `1.3.1` | **Shipped** |

**Verdict: SHIPPED — all 8 sub-deliverables verified**

---

## W2 — Model Fleet Integration (Claimed: Complete)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| `archive.py` with seed/query/list | All 3 functions present (lines 35, 103, 125) | **Shipped** |
| `nemotron_client.py` | Exists (1495 bytes), `classify()` function works | **Shipped** |
| `glm_client.py` | Exists (781 bytes), `generate()` function works | **Shipped** |
| `context.py` | Exists (1061 bytes), RAG enrichment functional | **Shipped** |
| `benchmark_fleet.py` run | Script exists but output doc `model-fleet-benchmark-0.1.4.md` does **not** exist | **Missing** |
| `model-fleet.md` ≥ 1500 words | Exists but only 551 words | **Partial** |
| iaomw-ADR-035 in base.md | Present at line 412 | **Shipped** |
| ChromaDB archives populated | 3 collections: iaomw (17), tripl (144), kjtco (282) | **Shipped** |

**Verdict: Mostly shipped — fleet functional, but benchmark results not captured and model-fleet.md is undersized**

---

## W3 — kjtcom Harness Migration (Claimed: Paused)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| `gotcha_archive.json` entries migrated | 8 entries with `kjtcom_source_id` (G1, G19, G31, G39, G41, G49, G62, G71) out of 13 total | **Partial** |
| `kjtcom-migration-map.md` | Does not exist | **Missing** |
| `/tmp/iao-0.1.4-ambiguous-gotchas.md` written | File not found on disk | **Missing** |
| iaomw-ADR-036 in base.md | Not found | **Missing** |
| `iao iteration resume` CLI command | Not found in `cli.py` | **Missing** |

**Verdict: PARTIAL — migration ran partially (8 entries ported) but pause mechanism never fired. See Investigation 5.**

---

## W4 — Telegram Framework (Claimed: Partial)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| `src/iao/telegram/` subpackage | Exists: `__init__.py` (129B), `notifications.py` (1958B) | **Partial** |
| `TelegramBotFramework` class | Does not exist — only `send_message` and `send_iteration_complete` functions | **Missing** |
| `iao telegram init/test/status` | Only `test` subcommand available | **Partial** |
| Telegram credentials in secrets | `./bin/iao secret list` shows `kjtco:TELEGRAM_BOT_TOKEN` | **Shipped** |
| iaomw-ADR-037 in base.md | Not found | **Missing** |
| python-telegram-bot installed | `import telegram` → version 22.7 | **Shipped** |

**Verdict: PARTIAL — notification plumbing works, but no bot framework, no init/status commands, no ADR**

---

## W5 — OpenClaw + NemoClaw Foundations (Claimed: Partial)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| `src/iao/agents/` subpackage | Exists with `openclaw.py`, `nemoclaw.py`, `roles/` | **Stub only** |
| `OpenClawSession` / `OpenClaw` class | `OpenClaw` exists but `chat()` raises `NotImplementedError` — "open-interpreter failed to install" | **Stub** |
| `NemoClawOrchestrator` class | Exists but delegates to broken `OpenClaw` | **Stub** |
| `open-interpreter` installed | `import interpreter` works but version is "unknown" | **Partial** |
| `scripts/smoke_nemoclaw.py` | Does not exist | **Missing** |
| `docs/harness/agents-architecture.md` | Does not exist | **Missing** |
| iaomw-ADR-038 in base.md | Not found | **Missing** |

**Verdict: STUB — files exist as scaffolding but nothing is functional. open-interpreter's broken install (Python 3.14 / missing Rust for tiktoken) blocked real implementation.**

---

## W6 — Gemini-Primary Sync (Claimed: Complete)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| README.md updated for Gemini-primary | README references "Iteration 0.1.4" and describes current state | **Shipped** |
| CLAUDE.md is short pointer | CLAUDE.md is 7 lines, points to GEMINI.md | **Shipped** |
| `gemini_compat.py` exists | `src/iao/postflight/gemini_compat.py` (1532 bytes) | **Shipped** |
| Telegram notification in `iteration close` | `send_iteration_complete` called in CLI `cmd_iteration` close path | **Shipped** |
| iaomw-ADR-039 in base.md | Present at line 421 | **Shipped** |

**Verdict: SHIPPED**

---

## W7 — Dogfood + Closing Sequence (Claimed: Active → later Complete)

| Sub-deliverable | Evidence | Verdict |
|---|---|---|
| `iao-build-log-0.1.4.md` | Exists, 535 lines, 22.8KB | **Shipped** |
| `iao-report-0.1.4.md` | Exists, 155 lines, 12.1KB | **Shipped** |
| `iao-run-report-0.1.4.md` | Exists, 70 lines, 3.0KB, Kyle signed off all 5 boxes | **Shipped** |
| `iao-bundle-0.1.4.md` | Exists, 5731 lines, 277KB, 39 `## §` headers | **Shipped** |

**Verdict: SHIPPED — all 4 closing artifacts present and substantial**

---

## Summary Table

| Workstream | Claimed | Actual | Delta |
|---|---|---|---|
| W0 | Complete | Shipped (close never finalized) | Minor — `.iao.json` not bumped |
| W1 | Complete | **SHIPPED** (8/8 sub-deliverables) | None |
| W2 | Complete | Mostly shipped (benchmark missing, fleet-doc undersized) | Minor |
| W3 | Paused | Partial (8 entries migrated, pause mechanism never fired) | Significant |
| W4 | Partial | Partial (notifications only, no bot framework) | Matches claim |
| W5 | Partial | **Stubs only** (nothing functional) | Worse than claimed |
| W6 | Complete | **SHIPPED** | None |
| W7 | Active→Complete | **SHIPPED** (checkpoint says complete) | None |

---

## Inherited Debt for 0.1.6

The delta between declared and actual state produces this debt list:

1. **W3 gotcha migration** — 8 of N entries ported, no ambiguous pile review, no migration map, no ADR-036, no resume mechanism
2. **W5 OpenClaw/NemoClaw** — stubs only, blocked by open-interpreter install failure, no architecture doc, no smoke test, no ADR-038
3. **W4 Telegram framework** — notifications work but no bot framework, no init/status commands, no ADR-037
4. **W2 benchmark** — fleet works but benchmark results never captured to docs
5. **W0 iteration close** — `.iao.json` never formally bumped, `completed_at` is null
6. **Missing ADRs** — ADR-036, ADR-037, ADR-038 never written
