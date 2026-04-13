# aho 0.2.14 — Plan Doc

**Theme:** Council wiring verification + cascade smoke test
**Executor:** Claude Code (drafter) | **Auditor:** Gemini CLI | **Sign-off:** Kyle
**Sessions:** 2 | **Workstreams:** 3

---

## W0 — Setup + Hygiene + Model Docs + Council Inventory
**Role:** Setup | **Session:** 1

**Scope:**

1. **Verify 0.2.13 close state.** Checkpoint shows iteration closed. `.aho.json` shows `last_completed_iteration: 0.2.13`. `baseline_regression_check()` clean (13 expected; 14 if close-reconciliation transients remain). Document state, don't block.

2. **Initialize 0.2.14.** Bump VERSION, .aho.json (`current_iteration: 0.2.14`), .aho-checkpoint.json (fresh, `run_type: pattern-c-modified`), MANIFEST.json, pyproject.toml, cli.py VERSION string.

3. **Root directory cleanup PROPOSAL.** Inventory all top-level files. Classify: canonical (keep), scratch-from-iteration (move to `artifacts/iterations/{iter}/scratch/` by mtime), stray (firebase-debug.log → .gitignore). Grep-verify each scratch file for src/ and artifacts/ references. Output `artifacts/iterations/0.2.14/w0-root-cleanup-proposal.md`. **Do NOT execute moves. Kyle approves first.**

4. **README + CHANGELOG narrative append.** Append-only. CHANGELOG entries for 0.2.12 (council activation, G078-G083, strategic rescope at W5) and 0.2.13 (dispatch repair, Pattern C trial, W2.5 substrate findings, rescope at W2.5). README narrative section through 0.2.13 with substrate findings as honest "where we are." No rewrite — extend existing voice.

5. **Pattern C protocol doc patches.** Update `artifacts/harness/pattern-c-protocol.md`:
   - Explicit emitter table (Claude vs Gemini emitters named)
   - `workstream_start` REQUIRED at workstream begin
   - Audit archive overwrites forbidden — re-audits versioned
   - Reference 0.2.13 W0 ambiguity and 0.2.13 reconciliation learnings

6. **`emit_workstream_complete()` side-effect fix.** Locate function, scope side-effect, patch so emit only modifies named workstream's state. Add unit test verifying sibling workstream states preserved across emit calls.

7. **Model documentation review.** Read online docs for: Qwen-3.5:9B, Nemotron-mini:4b, GLM-4.6V-Flash-9B, OpenClaw underlying model (resolve what underpins it; if unclear, document as "unknown — resolve in W1 vetting"). Capture per-model: structured-output support, context window, prompt formatting conventions, quantization options, known limitations. Output `artifacts/council-models-0.2.14.md`.

8. **Council inventory list.** Enumerate every declared council member from existing inventory artifacts and `.mcp.json`. Output `artifacts/iterations/0.2.14/council-inventory.md` listing all members with current claimed status from 0.2.12 inventory:
   - LLMs: Qwen-3.5:9B, Nemotron-mini:4b, GLM-4.6V-Flash-9B, OpenClaw underlying model
   - MCPs (9 declared): context7, sequential-thinking, playwright, filesystem, dart, memory, firebase-tools, firecrawl, everything (or current .mcp.json contents — verify)
   - Other: Nemoclaw socket, ChromaDB, nomic-embed-text
   This list is W1's vetting target.

9. **Stage NoSQL manual.** Source PDF at `artifacts/iterations/0.2.14/matrix-docs/source/NoSQL_DataPipelines_Technical_Manual.pdf` (already uploaded to /mnt/user-data/uploads). Extract full text via `pdftotext -layout`. Output to `artifacts/iterations/0.2.14/matrix-docs/nosql-manual.txt`. Capture page count, file size, extracted line count for record.

**Acceptance:**
- 0.2.13 close state confirmed clean OR discrepancies documented
- 0.2.14 version stamps updated (6 files)
- Root cleanup proposal written (NOT executed)
- README + CHANGELOG appended
- Pattern C protocol doc patched
- `emit_workstream_complete()` patched with passing unit test
- Council models doc complete (4 models)
- Council inventory list complete (all members from sources above)
- NoSQL manual staged + extracted to text
- baseline_regression_check() status recorded
- No git ops (Pillar 11)
- Gotcha registry consulted

**Auditor:** Gemini verifies inventory matches declared sources, model docs cover 4 LLMs, NoSQL extraction succeeded, root cleanup proposal classifications are sound, protocol patches present.

---

## W1 — Council Vet + Cascade Wire + NoSQL Smoke Test
**Role:** Vet + Build + Smoke | **Session:** 1 → 2

**Scope (three sub-phases, two internal hard gates):**

### Sub-phase 1.A — Council vetting (Gate 1)

For every member in `council-inventory.md`, attempt invocation. Record result:

- **LLMs:** invoke via Ollama directly with simple "Hello, identify yourself" prompt. Capture response, latency, errors.
- **MCPs:** invoke each via existing MCP infrastructure with the simplest read operation each supports. Capture response, latency, errors. For MCPs that require setup state (firebase-tools needs auth, slack needs token), note "configured/unconfigured" and skip if unconfigured.
- **Nemoclaw socket:** verify socket exists, attempt classify call.
- **ChromaDB, nomic-embed-text:** invoke if reachable, capture status.

Output: `artifacts/iterations/0.2.14/council-vetting-results.md` with table — member, attempted invocation, result (operational/gap/unknown), evidence (latency, response excerpt, error message). Plus `artifacts/iterations/0.2.14/council-vetting-results.json` machine-readable.

**Hard Gate 1:** Vetting table complete, all members have explicit status. Wiring sub-phase does NOT begin until vetting table exists. If Claude finds itself wiring before vetting completes, halt and finish vetting.

### Sub-phase 1.B — Pipeline schemas + cascade orchestrator (build)

1. **Triple schema** in `src/aho/pipeline/schemas.py`:
   - **Role schema:** `{producer: model_id, indexer_in: model_id, auditor: model_id, indexer_out: model_id, assessor: model_id}`. Validates model_id against verified members from sub-phase 1.A.
   - **Trace schema:** `pipeline_run_id`, `document_id`, `role_assignment`, handoff events with timestamps (indexer_in_complete, producer_complete, auditor_complete, indexer_out_complete, assessor_complete), exceptions, total_wall_clock, total_orchestrator_tokens.
   - **Delta schema:** `{new_gotchas: [...], gotcha_updates: [...], adr_candidates: [...], harness_patches: [...], pattern_candidates: [...]}`. Each item: `proposer_role` (indexer_in or indexer_out), `confidence`, `evidence_citation`, `proposed_text`, `canonical_target_path`.

2. **Cascade orchestrator** in `src/aho/pipeline/orchestrator.py`. Takes document path + role assignment. Executes 5-stage flow: indexer_in → producer → auditor → indexer_out → assessor. Emits trace event per handoff. Handles role-to-model dispatch through Nemoclaw or direct Ollama path per model docs.

3. **Auditor input extension:** receives Producer's work product AND Indexer-in's proposed deltas. Validates both.

4. **Assessor input extension:** receives all prior work products AND Indexer-out's proposed deltas. Validates both.

5. **Validated deltas write to staging:** `artifacts/iterations/0.2.14/deltas/staging/` — one JSON per validated delta. No registry write-back automation.

6. **Integration test on dummy document:** small text file (~500 words), simple role assignment using verified members. Cascade runs end-to-end. Every handoff emits trace event; zero orphaned. Auditor validates at least one dummy delta proposal AND rejects at least one malformed dummy delta.

### Sub-phase 1.C — NoSQL smoke test (Gate 2)

Construct **one role assignment** using verified-operational members from sub-phase 1.A. Strategy:

- If Qwen-3.5:9B is operational and other LLMs are gaps/unknowns, assignment may be Qwen-solo (all 5 roles bound to Qwen). This violates Pillar 7 but is acceptable for smoke — proves cascade works mechanically. Document the Pillar 7 acknowledgment.
- If multiple LLMs are operational, assign per Pillar 7 (drafter ≠ reviewer): e.g., Producer=Qwen, Auditor=GLM, Indexer=Nemotron, Assessor=OpenClaw-or-Qwen.

Run cascade against `artifacts/iterations/0.2.14/matrix-docs/nosql-manual.txt` (full document, no chunking). Per-run cap: 60 minutes per stage (5 stages × 60 min = 5 hours max wall clock, will likely be much less). If any stage hits cap, mark `partial_completion: true` for that stage and continue.

Output: `artifacts/iterations/0.2.14/smoke-test/run-1/` with full trace JSON, role work-product artifacts, delta proposals, delta validations, Assessor final output. Plus a top-level `smoke-test-summary.md` describing what happened.

**Hard Gate 2 (W1 acceptance):**
- Vetting table complete (Gate 1 satisfied)
- Cascade integration test passed on dummy document
- NoSQL smoke test executed (success or partial-completion both acceptable; complete failure is a finding, not a halt)
- All trace events present for completed stages
- Auditor validated at least one delta proposal in either integration test or smoke test
- Assessor produced output (even if partial) on smoke test
- baseline_regression_check() clean
- No G083 sites introduced

**Auditor:** Gemini reviews vetting table independently, runs integration test, reviews smoke test trace + outputs, confirms delta validation behavior.

---

## W2 — Sign-off + Close
**Role:** Close | **Session:** 2

**Scope (six deliverables):**

1. **Council health rerun.** Capture current number for trend record. No decision derives from it.

2. **Wiring sign-off package** (`artifacts/iterations/0.2.14/wiring-signoff.md`). Single document for Kyle decision (Hard Gate 3):
   - Vetting summary table (operational/gap/unknown counts)
   - Cascade smoke test result (passed/partial/failed; per-stage outcomes)
   - Role assignment used for smoke test (with Pillar 7 status — honored or acknowledged-violated)
   - Members ready for 0.2.15 measurement matrix
   - Members not ready (gap/unknown) and what would be needed to make them ready
   - Recommended Kyle decision: (a) wiring complete, 0.2.15 proceeds to measurement, (b) wiring partial, 0.2.15 reshapes, (c) wiring incomplete, 0.2.15 continues vetting

3. **Retrospective** (`retrospective-0.2.14.md`):
   - §1 What was planned
   - §2 What was delivered
   - §3 Vetting findings — substrate truth on member operational status
   - §4 Cascade smoke test — what worked, what didn't, what surprised
   - §5 Pattern C trial assessment (second iteration data)
   - §6 Honest read on whether the council is real

4. **Carry-forwards** (`carry-forwards.md`):
   - 0.2.15 measurement scope (matrix testing, dashboards) — depends on Kyle's wiring decision
   - GLM/Nemotron architecture decisions still deferred (await matrix data)
   - G083 bulk fix continuation
   - Firestore migration of staging (0.2.15+ once measurement substrate settled)
   - OpenClaw deep audit if vetting left it unknown
   - Registry write-back automation
   - Casing-variant Gotcha/gotch policy
   - Council health formula revision

5. **v10.66 bundle** per existing spec (300-500KB target). Sections §1-§11.

6. **Sign-off sheet** (`aho-run-0.2.14.md`) — 3 workstreams delivered (W0, W1, W2). Sign-off boxes for Sessions 1 (W0+W1) and 2 (W2). Kyle's Notes stub focused on 0.2.15 measurement-iteration decisions. Boxes UNCHECKED — Kyle ticks.

**Acceptance:**
- All six deliverables produced
- Sign-off package directly answers Hard Gate 3 question
- Retrospective is honest characterization (no celebratory framing)
- Bundle 300-500KB
- baseline_regression_check() clean
- Sign-off boxes UNCHECKED

**Auditor:** Gemini close-audit — does the retrospective tell the truth about what wiring revealed? Sign-off package directly actionable for Kyle? Substrate findings honest?

---

**Total: 3 workstreams.** W0 setup. W1 vet + wire + smoke (with two internal hard gates). W2 close + sign-off (with Kyle decision gate). 2 sessions.
