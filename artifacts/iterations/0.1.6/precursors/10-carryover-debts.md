# Investigation 10 — Full Carryover and Debts Inventory

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Debts Ranked by Blocking Status, Then Effort

---

### Debt: Stale global `iao` binary shadows pip install
- **Source:** Pre-0.1.4 (legacy iao-middleware)
- **Category:** stale-install
- **Blocking for 0.1.6:** yes — agents and Kyle may invoke the wrong binary
- **Evidence:** Report 02 — global `iao` resolves to `/home/kthompson/iao-middleware/bin/iao` (v0.1.0) instead of the pip-installed v0.1.4
- **Minimum fix:** Remove `~/iao-middleware/bin/` from fish PATH
- **Full fix:** Archive or delete `~/iao-middleware/` entirely, ensure `which iao` resolves to `~/.local/bin/iao`

---

### Debt: `.iao.json` never bumped past 0.1.4, `completed_at` is null
- **Source:** 0.1.4 W0/W7
- **Category:** bug
- **Blocking for 0.1.6:** yes — 0.1.6 cannot begin cleanly until 0.1.4 is formally closed and 0.1.5 is either skipped or closed
- **Evidence:** Report 01 — `current_iteration: "0.1.4"`, `last_completed_iteration: "0.1.3"`, `completed_at: null`
- **Minimum fix:** Manually update `.iao.json` to reflect 0.1.4 closed and skip to 0.1.6
- **Full fix:** Run `iao iteration close --confirm` (via `./bin/iao`) or manually set `last_completed_iteration: "0.1.5"`, `current_iteration: "0.1.6"`

---

### Debt: OpenClaw/NemoClaw are non-functional stubs
- **Source:** 0.1.4 W5
- **Category:** partial-deliverable
- **Blocking for 0.1.6:** depends — if 0.1.6 includes agentic loop work, this blocks it
- **Evidence:** Report 09 — `OpenClaw.chat()` raises NotImplementedError, NemoClaw delegates to broken OpenClaw
- **Minimum fix:** Build OpenClaw as direct Qwen/Ollama wrapper (bypass open-interpreter)
- **Full fix:** Resolve tiktoken/Python 3.14 issue, or implement custom code execution agent using Ollama

---

### Debt: Artifact loop has no progress output
- **Source:** 0.1.4 W7
- **Category:** broken-loop
- **Blocking for 0.1.6:** yes — agents cannot distinguish "generating" from "hung"
- **Evidence:** Report 03 — `stream: false` + `timeout: 1800s` = silent wait up to 30 minutes
- **Minimum fix:** Add heartbeat logging (elapsed time printed every 30s)
- **Full fix:** Switch to streaming mode with token-by-token output, reduce timeout to 600s

---

### Debt: Gotcha registry lacks `project_code` field
- **Source:** 0.1.4 W3
- **Category:** schema-mismatch
- **Blocking for 0.1.6:** depends — blocks cross-project gotcha migration
- **Evidence:** Report 06 — no `project_code` on any of 13 entries; `d.append()` bug due to dict-not-list structure
- **Minimum fix:** Add `project_code` field to existing entries, fix append logic
- **Full fix:** Implement full cross-project query API with project_code ranking

---

### Debt: kjtcom gotcha source data location unclear
- **Source:** 0.1.4 W3
- **Category:** missing-artifact
- **Blocking for 0.1.6:** depends — blocks W3 migration completion
- **Evidence:** Report 05, 06 — `kjtcom/data/gotcha_archive.json` registry is empty; source may be at `template/gotcha/gotcha_registry.json`
- **Minimum fix:** Identify the correct kjtcom gotcha source file
- **Full fix:** Complete migration with Nemotron classification

---

### Debt: Ambiguous pile review never happened
- **Source:** 0.1.4 W3
- **Category:** partial-deliverable
- **Blocking for 0.1.6:** no — can restart migration fresh
- **Evidence:** Report 05 — `/tmp/iao-0.1.4-ambiguous-gotchas.md` never written, `iao iteration resume` never implemented
- **Minimum fix:** Skip pause/resume mechanism; do a fresh classification pass
- **Full fix:** Implement interactive review workflow or batch classification with human approval

---

### Debt: Telegram bot framework not built
- **Source:** 0.1.4 W4
- **Category:** partial-deliverable
- **Blocking for 0.1.6:** no — notifications work; bot framework is nice-to-have
- **Evidence:** Report 09 — only `send_message` and `send_iteration_complete` exist; no bot, no init/status
- **Minimum fix:** Keep notifications-only scope for 0.1.6
- **Full fix:** Build TelegramBotFramework with command handlers and lifecycle management

---

### Debt: Missing ADRs (036, 037, 038)
- **Source:** 0.1.4 W3, W4, W5
- **Category:** missing-artifact
- **Blocking for 0.1.6:** no — ADRs document decisions but don't block code
- **Evidence:** Report 04 — grep of base.md finds ADR-035 and ADR-039 but not 036, 037, 038
- **Minimum fix:** Write 3 ADRs documenting the decisions made (even retroactively)
- **Full fix:** Same — these are documentation artifacts

---

### Debt: `model-fleet.md` undersized (551 words vs. 1500 target)
- **Source:** 0.1.4 W2
- **Category:** partial-deliverable
- **Blocking for 0.1.6:** no
- **Evidence:** Report 04 — `wc -w docs/harness/model-fleet.md` → 551
- **Minimum fix:** Expand with fleet details from Investigation 7
- **Full fix:** Include benchmark results, per-model guidance, context window notes

---

### Debt: Benchmark results not captured
- **Source:** 0.1.4 W2
- **Category:** missing-artifact
- **Blocking for 0.1.6:** no
- **Evidence:** Report 04 — `scripts/benchmark_fleet.py` exists but `docs/harness/model-fleet-benchmark-0.1.4.md` does not
- **Minimum fix:** Run benchmark, capture output
- **Full fix:** Add benchmark to postflight or doctor checks

---

### Debt: Missing architecture docs (`agents-architecture.md`, `kjtcom-migration-map.md`)
- **Source:** 0.1.4 W3, W5
- **Category:** missing-artifact
- **Blocking for 0.1.6:** no — but helpful for onboarding
- **Evidence:** Report 04 — neither file exists
- **Minimum fix:** Write after implementation is done
- **Full fix:** Include as W1 deliverables in 0.1.6

---

### Debt: Claw3D scope confusion
- **Source:** 0.1.4 run report (Kyle's notes)
- **Category:** undefined-concept
- **Blocking for 0.1.6:** depends — if Kyle wants it in scope, definition needed
- **Evidence:** Report 08 — Claw3D is a kjtcom Three.js visualization, not an iao agentic component
- **Minimum fix:** Kyle clarifies whether Claw3D belongs in iao's scope or kjtcom's
- **Full fix:** If in iao scope: build postflight plugin system; if not: remove from iao scope

---

### Debt: Stale `.pyc` files in `src/iao/postflight/__pycache__/`
- **Source:** 0.1.4 sterilization
- **Category:** bug
- **Blocking for 0.1.6:** no — cosmetic
- **Evidence:** Report 08 — `.pyc` files for deleted modules (claw3d_version_matches, deployed_claw3d_matches, deployed_flutter_matches, map_tab_renders, firestore_baseline)
- **Minimum fix:** Delete stale `.pyc` files
- **Full fix:** Add `__pycache__` cleanup to postflight or doctor

---

### Debt: 0.1.5 design/plan exist but 0.1.5 never executed
- **Source:** 0.1.5
- **Category:** partial-deliverable
- **Blocking for 0.1.6:** depends — need to decide whether to skip 0.1.5 or salvage its artifacts
- **Evidence:** Report 01 — `iao-design-0.1.5.md` (5132 words) and `iao-plan-0.1.5.md` (3274 words) exist on disk
- **Minimum fix:** Skip 0.1.5 entirely, bump to 0.1.6
- **Full fix:** Evaluate salvageability of 0.1.5 artifacts for 0.1.6 planning (see Investigation 11)

---

### Debt: `num_ctx` may be too small for long-form Qwen generation
- **Source:** 0.1.4 W7 / artifact loop
- **Category:** broken-loop
- **Blocking for 0.1.6:** no — loop works but may produce truncated output
- **Evidence:** Report 03 — `num_ctx: 8192` with prompts ~920 words + 5000-word target output approaches the limit
- **Minimum fix:** Increase `num_ctx` to 16384
- **Full fix:** Make `num_ctx` configurable per artifact kind

---

## Summary by Priority

### Must fix before 0.1.6 begins
1. Stale global `iao` binary (PATH fix)
2. `.iao.json` iteration state (manual bump to 0.1.6)
3. Artifact loop progress output (heartbeat or streaming)

### Should fix in 0.1.6 (good-to-have)
4. Gotcha registry `project_code` field
5. OpenClaw/NemoClaw beyond stubs
6. kjtcom gotcha source identification
7. Missing ADRs (036, 037, 038)
8. Claw3D scope decision

### Deferred (can wait for 0.1.7+)
9. Telegram bot framework
10. Model fleet benchmark capture
11. Architecture documentation
12. `model-fleet.md` expansion
13. Stale `.pyc` cleanup
14. `num_ctx` tuning
