# Run File — aho 0.2.1

**Generated:** 2026-04-11
**Iteration:** 0.2.1 (Iteration 2, Run 1)
**Phase:** 0
**Status:** Graduated

## Workstream Summary

| WS | Status | Agent | Deliverable |
|---|---|---|---|
| W0 | pass | claude-code | 8 canonical artifacts at 0.2.1, build_log_complete fix, MANIFEST refresh, .gitignore initial pass |
| W1 | pass | claude-code | global-deployment.md (7 sections, hybrid systemd model, 8th canonical artifact) |
| W2 | pass | claude-code | Real bin/aho-install + bin/aho-uninstall, doctor wiring |
| W3 | pass | claude-code | otelcol-contrib v0.149.0 as aho-otel-collector.service, always-on OTEL (opt-out via AHO_OTEL_DISABLED) |
| W4 | pass | claude-code | 4 Ollama models verified (qwen3.5:9b, nemotron-mini:4b, GLM-4.6V-Flash-9B, nomic-embed-text), bin/aho-models-status |
| W5 | pass | claude-code | OTEL spans wired into 6 components (qwen, nemotron, glm, openclaw, nemoclaw, telegram), 7 instrumentation tests |
| W6 | pass | claude-code | 87 tests, bundle 322KB, all postflight gates green |

Wall clock: 14m 22s. Components: 72 (69 active, 3 stub). Bundle: 322KB.

**Soc-foundry/aho second commit pushed:** `9635d5b` — 50 files, +5125/-324, ChromaDB binaries scrubbed from HEAD, 0.2.1 artifacts uploaded.

---

## Agent Questions — Answered

No questions surfaced. Three carryover items identified for 0.2.2 W0 hygiene:

1. **`build_log_complete` still WARN** ("design doc not found, skipping completeness check"). The W0 fix in 0.2.1 didn't fully resolve it. Needs another look at the path resolution in `build_log_complete.py`.
2. **Risk Register shows 20+ evaluator warns/rejects** during 0.2.1 close — all from `build_log_synthesis` evaluator firing repeatedly. Likely the Qwen synthesis loop hitting the rejection threshold but the mechanical builder catching it gracefully. Worth a one-line investigation to confirm it's noise, not a real signal.
3. **Wall clock per-workstream still shows `-`** in run file. Agent attribution landed (`claude-code`), component section embedded, but wall clock from checkpoint timestamps isn't being computed. Small fix in `report_builder.py` workstream parser.

---

## Kyle's Notes

**Iteration 2 has its spine.** 0.2.1 landed everything that needed to land for the global deployment story to be real:

- Hybrid systemd model documented and operational
- Native OTEL collector (otelcol-contrib v0.149.0) running as systemd user service
- Always-on OTEL (no more opt-in gating)
- Real `bin/aho-install` and `bin/aho-uninstall` with idempotency contract
- All 4 Ollama models pre-pulled and verified
- 6 components emitting OTEL spans (qwen, nemotron, glm, openclaw, nemoclaw, telegram)
- 8 canonical artifacts now version-tracked
- soc-foundry/aho second commit live

**The deferral debt is still in components.yaml.** openclaw, nemoclaw, telegram are still `stub` with `next_iteration: 0.1.16` (stale — should have been bumped to 0.2.2 in 0.2.1 but missed). 0.2.2 is the run where they actually graduate from stub to active. The instrumentation pass in 0.2.1 W5 wired spans into them — now 0.2.2 makes them functional.

**Today's status:** ~7:35am PST. Three runs shipped this morning (0.1.15, 0.1.16 iteration 1 graduation, 0.2.1). Family time mid-afternoon. 6-11pm evening block available. P3 ship deadline = end of today. Alex ship deadline = Sunday. Fly Sunday.

**Phase 0 exit roadmap update (3 iterations + ship gauntlet):**
- **0.2.2** — openclaw/nemoclaw global daemons + telegram bridge real implementation + 3 stubs flip to active (today, ~2-3 hours)
- **0.2.3** — MCP server fleet (firebase-tools, context7, firecrawl, playwright, flutter, modelcontextprotocol/server-*) (today evening or tomorrow morning)
- **0.2.4** — P3 clone attempt + smoke test + capability gap capture (tomorrow)
- **0.2.5+** — Whatever P3 surfaces, fix in tight runs
- **Iteration 2 graduates** when P3 runs an aho iteration end-to-end
- **0.3.x** — Alex demo prep, claw3d, novice operability validation (Sunday SF prep)
- **Phase 0 graduates** when iteration 3 closes clean

**Event log audit clean.** The W6 smoke spans contain only `test prompt`, `hello`, `test task`, `print('hello')` — no credentials, no secrets, no API keys. Telemetry design records `input_summary` (truncated/shape) not full prompts, which is the right pattern. Confirmed safe.

**First commit history note.** `data/chroma/` and `data/aho_event_log.jsonl` exist in commit `ac0f66b` history but are gone from HEAD. ChromaDB binaries are noise. Event log is shape-only smoke data. No security action required. Future `git filter-repo` cleanup is a Phase 1 housekeeping item, not a Phase 0 blocker.

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Closed 2026-04-11, W6 by claude-code. Iteration 2 active.*
