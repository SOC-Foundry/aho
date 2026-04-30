# aho-plan-0.2.16

**Iteration:** 0.2.16
**Theme:** Claude Code OTEL Integration & 0.2.15 Close-Out
**Phase:** 0 (Clone-to-Deploy)

Execution plan for workstreams defined in `aho-design-0.2.16.md`. Pillars and trident defined in design doc; not repeated here per convention.

---

## Workstream summary

| N | Theme | Gate |
|---|---|---|
| W0 | 0.2.15 close-out + substrate closure + OTEL scaffolding | 0.2.15 closed, install.fish Tier 1 dry-run clean, Qwen Producer emits visible content on cascade prompts, Claude Code metrics + events in Jaeger with correct resource attrs |
| W1 | Pillar 8 cost + token dashboard | Per-workstream cost + token breakdown live, cache read/creation visible, dashboard loads under 2s |
| W2 | Distributed tracing — `TRACEPARENT` propagation | End-to-end Jaeger trace (user prompt → Claude API → tool → dispatcher → Ollama), correct parent-child span relationship |
| W3 | Pillar 11 enforcement + anomaly detection | 5 alert rules live, dedicated Telegram channel verified, synthetic test fires within 60s |
| W4 | Cross-model cascade re-run + close | Paired Auditor comparison on identical Producer output, Pillar 7 verdict with evidence, export pack assembled, iteration bundle and sign-off |

---

## W0 — 0.2.15 close-out + substrate closure + OTEL scaffolding

**Scope:** Three coordinated buckets — Kyle's close-out, substrate debt closure, OTEL environment scaffolding.

### Bucket 1 — 0.2.15 close-out (Kyle-driven)

1. **Sign-off drift repair** — update `sign-off-0.2.15.md`:
   - Line 25 carry-forward count: `21 items` → `27 items` (match `carry-forwards-0.2.15.md` actual footer count after reconciliation)
   - Line 31 bundle section count claim: verify against actual bundle — 0.2.15 bundle has 9 sections (§1–§9), not 8; correct if sign-off claim mismatches
   - `carry-forwards-0.2.15.md` footer: claims 25, actual count is 27 — reconcile (update footer to 27)
2. **Kyle ticks sign-off boxes** on `artifacts/iterations/0.2.15/sign-off-0.2.15.md` after verifying evidence per box
3. **`aho iteration close --confirm`** executed on NZXTcos with `AHO_ITERATION=0.2.15` in env
4. **AHO_ITERATION advanced** to 0.2.16; event logged; checkpoint scaffolding initialized for 0.2.16

### Bucket 2 — substrate closure (Claude Code)

5. **Qwen Producer `num_predict=8000`:**
   - Edit `src/aho/pipeline/dispatcher.py` → `MODEL_FAMILY_CONFIG["qwen"]["options"]["num_predict"] = 8000`
   - Clear `__pycache__` per G070 after edit
   - Probe: run Producer role against the 247K-char NoSQL manual used in 0.2.15 W4 cascade (same input); capture `message.thinking` chars, `message.content` chars, `eval_count`, `done_reason`
   - Record to `artifacts/iterations/0.2.16/qwen-num-predict-probe.json`
   - Expected: `content_chars ≥ 500`, `done_reason != "length"` (or document which next-lever triggers)

6. **Empty-content halt semantics:**
   - Add `EmptyContentError(DispatchError)` to dispatcher typed-exception hierarchy
   - In `src/aho/pipeline/orchestrator.py` cascade step completion, check `result.content == ""` with `result.error is None` — raise `EmptyContentError` with stage context
   - Cascade runner catches `EmptyContentError` and halts the cascade (no silent `[stage X failed: None]` propagation downstream)
   - Unit test: `tests/test_orchestrator_halt.py` covering the halt path

7. **`template_leak_detected` normalization (AF002):**
   - At template-leak detection site in `dispatcher.py`, return `False` when no leak detected (currently `None`)
   - Cascade runner stage JSON builder: write `"template_leak_detected": false` not `null`
   - Update 0.2.16 stage artifacts template to reflect the type
   - Unit test: assert `False` (not `None`) for clean responses

8. **Orchestrator `workstream_id` parameterization (F006):**
   - `src/aho/pipeline/orchestrator.py` — `run_cascade(..., workstream_id="W0")` default
   - Remove hardcoded `"W1"` at lines 148 and 198 (verify line numbers against current file; may have shifted)
   - Unit test: `run_cascade(workstream_id="W4")` emits `pipeline_handoff` events with `workstream_id="W4"` in the log_event payload

9. **`test_workstream_events.py` fixture fix (3rd recurrence):**
   - Create or extend `tests/conftest.py` with autouse fixture patching `aho.events.find_project_root` to return a `tmp_path`
   - Ensure `test_workstream_events.py` tests operate on the tmp directory only, never on real `.aho-checkpoint.json`
   - Verify by running full suite: no checkpoint mutation, no spurious workstream entries

10. **G083 nemoclaw.py narrowing (F003):**
    - `src/aho/agents/nemoclaw.py:77` — dispatch method: narrow `except Exception` to specific error types based on the failure modes actually observed (connection, decode, timeout). Raise or return typed errors.
    - `src/aho/agents/nemoclaw.py:134` — handler dispatch branch: same treatment
    - Unit tests verifying each narrowed exception path behaves correctly

### Bucket 3 — OTEL scaffolding (Claude Code)

11. **`.claude/settings.json` env block:**
    ```
    CLAUDE_CODE_ENABLE_TELEMETRY=1
    OTEL_METRICS_EXPORTER=otlp
    OTEL_LOGS_EXPORTER=otlp
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
    OTEL_EXPORTER_OTLP_PROTOCOL=grpc
    OTEL_LOG_USER_PROMPTS=1
    OTEL_LOG_TOOL_CONTENT=1
    OTEL_RESOURCE_ATTRIBUTES=service.name=claude-code,aho.iteration=${AHO_ITERATION},aho.workstream=${AHO_WORKSTREAM},aho.role=drafter
    ```
12. **`AHO_WORKSTREAM` env variable** — set by aho event helpers at `emit_workstream_start`; Claude Code inherits via shell env at session launch. Document in `CLAUDE.md` reference reading.
13. **Traces explicitly not configured in W0** — `OTEL_TRACES_EXPORTER` unset. W2 flips it on.
14. **Verify signals arrive:**
    - Start a Claude Code session with `CLAUDE_CODE_ENABLE_TELEMETRY=1` and env attrs set
    - Emit a trivial prompt and tool_use
    - Confirm in Jaeger / collector logs: one `claude_code.user_prompt` event, one `claude_code.tool_result` event, one `claude_code.session.count` metric increment, all tagged `aho.iteration=0.2.16`
15. **ADR logged** — number determined by enumerating `artifacts/adrs/` at W0 execution time; do not fabricate. Content: OTEL scaffolding posture decision.

**Deliverables:**
- `install.fish` — finalized Tier 1 section (from existing W0–W3 0.2.15 artifact evidence)
- `src/aho/pipeline/dispatcher.py` — `num_predict=8000`, `template_leak_detected` → `False` default
- `src/aho/pipeline/orchestrator.py` — `EmptyContentError` + halt semantics, `workstream_id` parameterized
- `src/aho/agents/nemoclaw.py` — G083 sites narrowed
- `tests/conftest.py` — `find_project_root` autouse patch (or equivalent)
- `tests/test_orchestrator_halt.py` — new tests for empty-content halt
- `.claude/settings.json` — OTEL env block
- `artifacts/iterations/0.2.16/otel-scaffold-notes.md`
- `artifacts/iterations/0.2.16/qwen-num-predict-probe.json`
- `artifacts/iterations/0.2.16/install-fish-dryrun.md`
- `artifacts/adrs/NNNN-otel-scaffolding-posture.md` (number at execution time)

**Acceptance:**
- 0.2.15 closed via `aho iteration close --confirm` (Kyle-run)
- install.fish Tier 1 dry-run on NZXTcos: clean VRAM detection, correct Arch-family detection, model-pull list matches W0–W3 0.2.15 evidence
- Qwen Producer probe emits ≥500 chars content on 247K-char input, `done_reason != "length"` (or fallback lever engaged and documented)
- Claude Code session produces visible metrics + events in Jaeger with correct `aho.*` resource attrs
- Baseline regression: 10 failed / 374 passed / 1 skipped / 1 deselected (identical to 0.2.15 W4) — **except** `test_workstream_events.py` no longer recurs checkpoint corruption
- Checkpoint at `pending_audit`, W0 acceptance archive written

**Estimated budget:** 4–5 hours Claude session. install.fish finalization is ~1 hour; Qwen probe ~30 min; dispatcher/orchestrator/test fixes ~2 hours; OTEL scaffolding ~30 min; ADR + notes ~30 min.

---

## W1 — Pillar 8 cost + token dashboard

**Scope:** Dashboard surface for per-iteration and per-workstream Claude Code cost + token attribution, consuming OTEL-native metrics set in W0.

1. **Metric ingestion verification:**
   - Confirm otelcol-contrib is exporting metrics to Prometheus (or equivalent) for dashboard consumption. If not, add exporter.
   - Query test: `claude_code_cost_usage` metric visible with `aho_iteration` label = `"0.2.16"`
   - Query test: `claude_code_token_usage` metric visible with `type` label values `input`, `output`, `cacheRead`, `cacheCreation`

2. **Dashboard definition:**
   - File: `artifacts/iterations/0.2.16/dashboards/pillar-8-cost-tokens.json` (Grafana JSON)
   - Panels:
     - **P1** — Total cost by workstream (time series, stacked, grouped by `aho_workstream`)
     - **P2** — Token usage by type (time series, 4 series: input, output, cacheRead, cacheCreation)
     - **P3** — Cost per 1K tokens (gauge, rolling 1-hour window)
     - **P4** — Active time total (single stat, `claude_code.active_time.total`)
     - **P5** — Cost delta from baseline (bar chart, baseline = 0.2.15 W4 average if recoverable, else synthetic probe)
   - Variables: `$iteration`, `$workstream` (dropdown selectors)
   - Refresh: 30s

3. **Attribution logic:**
   - Every metric is tagged with `aho.iteration` and `aho.workstream` via resource attrs from W0
   - Correlation with aho event log via workstream boundaries (start/complete timestamps)
   - Document in `artifacts/iterations/0.2.16/pillar-8-dashboard-notes.md`

4. **Baseline recording:**
   - If 0.2.15 session cost data is recoverable from existing logs (inference log parsing), record as baseline for comparison
   - If not, run a synthetic W1 probe session and record cost figures
   - Baseline file: `artifacts/iterations/0.2.16/cost-baseline.json`

5. **Mercor export copy:**
   - Copy dashboard JSON to `artifacts/iterations/0.2.16/export/claude-otel-reference-pack/dashboards/pillar-8-cost-tokens.json`
   - Strip any aho-specific labels or panel titles that wouldn't transfer

**Deliverables:**
- `artifacts/iterations/0.2.16/dashboards/pillar-8-cost-tokens.json`
- `artifacts/iterations/0.2.16/pillar-8-dashboard-notes.md`
- `artifacts/iterations/0.2.16/cost-baseline.json`
- Export copy under `export/claude-otel-reference-pack/dashboards/`

**Acceptance:**
- All 5 panels render with real data for at least one workstream (W0 telemetry)
- Dashboard loads under 2s on NZXTcos
- Cache breakdown visible as separate series (verifies `type` label attribute from OTEL)
- Export copy is drop-in deployable (no aho hardcodes)

**Estimated budget:** 3–4 hours. Grafana JSON hand-authoring is the wall-clock sink.

---

## W2 — Distributed tracing — `TRACEPARENT` propagation

**Scope:** Enable traces beta, propagate W3C trace context through aho dispatcher and router, produce end-to-end Jaeger trace.

1. **Traces beta enablement:**
   - Add to `.claude/settings.json` env block: `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, `OTEL_TRACES_EXPORTER=otlp`
   - Verify Jaeger receives traces (not just metrics + events)

2. **`TRACEPARENT` propagation in dispatcher:**
   - `src/aho/pipeline/dispatcher.py`: read `TRACEPARENT` env var at entry of `dispatch()`
   - If present: parse W3C trace context, create child span with `trace_id` inherited
   - If absent: create root span (preserves behavior for non-OTEL callers)
   - Span name: `aho.dispatch.{model_family}`
   - Span attributes: `aho.model`, `aho.family`, `aho.stage` (if passed), `dispatch.num_ctx`, `dispatch.num_predict`, `dispatch.duration_ms`, `dispatch.tokens_eval`, `dispatch.tokens_prompt`
   - End span on dispatch completion (success or typed error)

3. **`TRACEPARENT` propagation in router:**
   - `src/aho/pipeline/router.py`: same treatment at `route()` entry
   - Span name: `aho.route.classify`
   - Span attributes: `aho.classifier_model`, `aho.input_excerpt` (truncated), `aho.category`, `aho.duration_ms`

4. **End-to-end trace probe:**
   - Launch a Claude Code session that calls `aho dispatch --stage producer ...` or equivalent via bash wrapper
   - Inspect resulting Jaeger trace: should show Claude Code root span → API request span → tool_use span → bash subprocess span → `aho.dispatch.qwen` child span → Ollama call (if instrumented) or leaf
   - Capture export: `artifacts/iterations/0.2.16/traces/end-to-end-sample.json`

5. **Backward compat verification:**
   - Existing dispatcher tests must continue to pass without `TRACEPARENT` set
   - Unit test: `test_dispatcher_traceparent_absent` — confirms root span created when env var missing
   - Unit test: `test_dispatcher_traceparent_present` — confirms child span created when env var present

6. **OTEL payload truncation:**
   - Observe `OTEL_LOG_TOOL_CONTENT=1` truncation at 60KB — not a failure, confirm documented behavior
   - Record: `artifacts/iterations/0.2.16/trace-integration-notes.md` §Truncation

7. **Gemini CLI asymmetry ADR:**
   - Subject: Gemini has no OTEL equivalent; audits remain invisible at API level
   - Decision: accept asymmetry; harness-watcher event wrappers capture wall-clock only; no timing-wrapper half-measures
   - Rationale: partial observability is worse than clear asymmetry for reference pack consumers
   - Number determined from ADR index at W2 execution time

**Deliverables:**
- `src/aho/pipeline/dispatcher.py` — `TRACEPARENT` read + span creation
- `src/aho/pipeline/router.py` — same
- `tests/test_dispatcher_traceparent.py` — two unit tests
- `tests/test_router_traceparent.py` — two unit tests
- `artifacts/iterations/0.2.16/trace-integration-notes.md`
- `artifacts/iterations/0.2.16/traces/end-to-end-sample.json` — captured Jaeger trace
- `artifacts/adrs/NNNN-gemini-otel-asymmetry.md` (number at execution time)
- Export copy: `.claude-settings-template.json` updated for traces + collector snippet under `export/claude-otel-reference-pack/collector/`

**Acceptance:**
- Single Jaeger trace captured showing parent-child span relationship correctly (aho spans are children of Claude Code spans under same `trace_id`)
- `dispatch.duration_ms` span attribute matches dispatcher's internal timing (no drift)
- Backward compat tests pass
- ADR published with correct index-derived number

**Estimated budget:** 4 hours. Span instrumentation + testing is the bulk.

---

## W3 — Pillar 11 enforcement + anomaly detection

**Scope:** Five alert rules live, dedicated Telegram channel for delivery, synthetic test evidence.

1. **Alert rule files:**
   - `artifacts/iterations/0.2.16/alerts/pillar-11-violations.yaml` — rules 1 and 2
   - `artifacts/iterations/0.2.16/alerts/anomaly-rules.yaml` — rules 3, 4, 5
   - Format: Prometheus Alertmanager syntax (or equivalent for whatever engine is running)

2. **Rule details:**

    | # | Name | Condition | Severity | Window |
    |---|---|---|---|---|
    | 1 | Pillar11CommitViolation | `increase(claude_code_commit_count[1m]) > 0` | critical | 1m |
    | 2 | Pillar11PullRequestViolation | `increase(claude_code_pull_request_count[1m]) > 0` | critical | 1m |
    | 3 | ClaudeAPIErrorSpike | `rate(claude_code_api_error[5m]) > 1` (>5 in 5m) | important | 5m |
    | 4 | ClaudeCostAnomaly | `increase(claude_code_cost_usage[10m]) > 2.0` ($2.00) | important | 10m |
    | 5 | ToolDurationOutlier | `histogram_quantile(0.99, claude_code_tool_result_duration_ms_bucket) > baseline * 3` | info | 5m rolling |

3. **Dedicated Telegram channel:**
   - Kyle creates new Telegram bot (e.g., `@aho_alerts_bot`) and dedicated chat
   - Kyle stores secrets: `ahomw:telegram_alerts_bot_token` and `ahomw:telegram_alerts_chat_id`
   - Verify with `get_secret("ahomw", "telegram_alerts_bot_token")` returns expected value
   - **No agent creates secrets** per Pillar 11

4. **Alert delivery bridge:**
   - `src/aho/alerts/telegram_alerts.py` (new file) — receives webhooks from alert engine, formats alert message, posts to dedicated chat via Telegram API
   - Uses `ahomw:telegram_alerts_*` secrets (not the existing routine-notification `ahomw:telegram_bot_token`)
   - Unit tests with mocked Telegram API
   - Event log side-effect: every alert also appends to `aho_event_log.jsonl` with `event_type=pillar_11_violation` or `event_type=anomaly`

5. **Synthetic test:**
   - Use otelcol-contrib's `telemetrygen` or a hand-rolled probe to emit a synthetic `claude_code.commit.count` increment
   - Verify: rule fires, bridge picks up, Telegram message arrives in dedicated channel within 60s
   - Verify: `aho_event_log.jsonl` contains matching `pillar_11_violation` event
   - Record: `artifacts/iterations/0.2.16/alert-delivery-test.md` with timestamps and screenshots

6. **Baseline calibration for rule 5:**
   - Observe `claude_code.tool_result.duration_ms` p99 over a representative window (W1 + W2 workstream sessions)
   - Set baseline threshold to measured p99, multiplier = 3
   - Document in `pillar-11-monitoring-notes.md`

7. **Mercor export copy:**
   - Copy alert rule files to `export/claude-otel-reference-pack/alerts/`
   - Strip aho-specific labels if any
   - Add `README.md` in `alerts/` explaining each rule

**Deliverables:**
- `artifacts/iterations/0.2.16/alerts/pillar-11-violations.yaml`
- `artifacts/iterations/0.2.16/alerts/anomaly-rules.yaml`
- `src/aho/alerts/telegram_alerts.py` + unit tests
- `artifacts/iterations/0.2.16/pillar-11-monitoring-notes.md`
- `artifacts/iterations/0.2.16/alert-delivery-test.md`
- Export copies under `export/claude-otel-reference-pack/alerts/`

**Acceptance:**
- All 5 rules active in alert engine
- Synthetic Pillar 11 commit event produces alert delivery in dedicated channel within 60s
- aho_event_log.jsonl contains corresponding `pillar_11_violation` event
- Secrets (`telegram_alerts_bot_token`, `telegram_alerts_chat_id`) verified readable via `get_secret("ahomw", ...)`

**Estimated budget:** 4 hours. Bridge code + test + synthetic probe is the bulk.

---

## W4 — Cross-model cascade re-run + close

**Scope:** Clean Pillar 7 paired comparison on identical Producer output. Export pack assembly. Iteration close.

1. **Cascade scenario setup:**
   - Same 247K-char NoSQL manual as 0.2.15 W4 (baseline continuity, no variable change)
   - Producer=Qwen 3.5:9B (with `num_predict=8000` from W0 fix)
   - Indexer-in=Llama 3.2:3B
   - Indexer-out=Llama 3.2:3B
   - Assessor=Qwen 3.5:9B (Nemotron confirmed compromised as Assessor in 0.2.15 W4 F004; do not repeat)

2. **Paired Auditor runs:**
   - **Producer runs once** — produce one canonical Producer output artifact
   - **Auditor Run A** — Qwen-as-Auditor on canonical Producer output
   - **Auditor Run B** — GLM-as-Auditor (`num_gpu=30`) on canonical Producer output
   - Indexer-out and Assessor run once per Auditor (so 2 paired cascade tails)
   - All runs fully traced via W2 OTEL (one trace per run)

3. **Role-compatibility gate (F004 closure):**
   - In `src/aho/pipeline/orchestrator.py` cascade init, read `artifacts/iterations/0.2.15/tier1-roster-validation-0.2.15.json`
   - For each assigned role, assert the model's `operational`/`partial`/`compromised` classification is role-compatible:
     - Producer, Auditor, Assessor roles require `operational` (or `partial` with explicit override)
     - Indexer roles accept `operational` or `partial`
     - `compromised` models cannot be assigned without explicit override flag
   - Unit test: assigning Nemotron to Assessor raises `RoleIncompatibleError` unless override

4. **Pillar 7 verdict:**
   - Compare Auditor outputs from Run A (Qwen) and Run B (GLM) on the same Producer input
   - Dimensions: structural difference (critique categories surfaced), accuracy (do Auditor findings match the Producer artifact), rubber-stamp pattern (does `delta_validations` generic-accept all deltas)
   - Verdict with evidence: quoted excerpts from both Auditors, side-by-side comparison table
   - Record: `artifacts/iterations/0.2.16/cascade-rerun/pillar-7-comparison.md`

5. **Cost attribution:**
   - Both runs' OTEL cost metrics tagged `aho.workstream=W4`
   - Dashboard (W1) should show both runs under W4 attribution
   - Record total cost per run in comparison doc

6. **Export pack assembly:**
   - Assemble `artifacts/iterations/0.2.16/export/claude-otel-reference-pack/` per design spec
   - Copy artifacts from W0–W3 to appropriate subdirs
   - Author `export/claude-otel-reference-pack/README.md` — top-level runbook (what this is, who it's for, deployment steps)
   - Author `export/claude-otel-reference-pack/runbook.md` — step-by-step setup on a fresh machine

7. **Iteration close package:**
   - `retrospective-0.2.16.md` — honest retrospective covering W0–W4, lessons learned on OTEL integration, Pillar 7 verdict
   - `carry-forwards-0.2.16.md` — items not completed, grouped by target iteration with severity
   - `aho-bundle-0.2.16.md` — standard bundle structure (9 sections per 0.2.15 convention)
   - `sign-off-0.2.16.md` — Kyle sign-off sheet with unchecked boxes
   - Verify counts in sign-off match carry-forwards (avoid 0.2.15 AF001 recurrence)

**Deliverables:**
- `artifacts/iterations/0.2.16/cascade-rerun/stage-*.json` (10 stage files for paired runs + 2 trace.json)
- `artifacts/iterations/0.2.16/cascade-rerun/pillar-7-comparison.md`
- `src/aho/pipeline/orchestrator.py` — role-compatibility gate
- `tests/test_orchestrator_role_compat.py` — new unit tests
- `artifacts/iterations/0.2.16/export/claude-otel-reference-pack/` — full assembled pack
- `artifacts/iterations/0.2.16/retrospective-0.2.16.md`
- `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
- `artifacts/iterations/0.2.16/aho-bundle-0.2.16.md`
- `artifacts/iterations/0.2.16/sign-off-0.2.16.md`

**Hard gate blocker:**
- Cross-model cascade paired run completes with real Producer output (not 0-char artifact) — if Producer still emits empty content after W0's `num_predict=8000`, contingency lever (e.g., `/no_think`) must engage before W4 final run
- Both Auditor runs produce >500 chars of substantive critique
- Pillar 7 verdict rendered with evidence (not rhetoric)
- Export pack populated with all four workstream artifact groups + runbook
- Bundle has 9 sections (per 0.2.15 convention)
- Sign-off counts internally consistent
- No agent git operations throughout iteration (Pillar 11)

**Estimated budget:** 5–6 hours. Paired cascade wall-clock ~60–90 min (two Auditor runs); pillar-7 comparison writeup ~1 hour; export pack assembly + runbook ~1–2 hours; retrospective + carry-forwards + bundle ~2 hours.

---

## Cross-iteration carry tracking

Inherited from 0.2.15 (20 items targeted to 0.2.16; 5 items targeted to 0.2.17+):

**Folded into 0.2.16 W0–W4 workstreams above:**
- install.fish Tier 1 section finalization (W0)
- Qwen `num_predict` Producer substrate fix (W0)
- `test_workstream_events.py` fixture fix (W0)
- `template_leak_detected` null → false (W0)
- Orchestrator `workstream_id` parameterization (W0)
- Empty-content halt semantics (W0)
- G083 nemoclaw.py remaining sites (W0)
- Sign-off / carry-forward count drift (W0 Bucket 1)
- Role-compatibility gate in cascade (W4)
- Cross-model cascade re-run (W4)

**Not folded — remain open carry-forwards for 0.2.17+:**
- Auditor role-prompt bifurcation redesign (prompt engineering iteration candidate; 0.2.16 W4 re-run may inform decision)
- `emit_workstream_complete()` side-effect root cause (0.2.14 original; 0.2.15 carry; reactive — if no recurrence, self-resolving)
- Gotcha registry canonical file location (0.2.14 carry; 0.2.15 carry; W0 Bucket 3 may touch but not formally scoped)
- Capability-routed vs role-assigned cascade architectural decision
- Executor-as-outer-loop-judge (Critic/Arbiter)
- OpenClaw disposition
- Baseline contamination protocol formalization
- Thinking field propagation across cascade stages (GLM thinking-field observation from 0.2.15 W4)
- SSH key distribution to remote machines
- WARP/Tailscale coexistence on auraX9cos
- Ollama service layer documentation (may land as part of install.fish in W0)
- Tier 1 hardware requirements documentation (may land as part of install.fish in W0)

**Targeted to 0.2.17+ (unchanged):**
- nomic-embed-text + ChromaDB RAG integration
- Tier 2/3 roster (Gemma 2, DeepSeek-Coder-V2, Mistral-Nemo)
- Fleet bootstrap iteration arc (A8cos minimal, Luke full, P3 production)
- Firestore migration of staging directories

---

## Process discipline

Same as 0.2.15 close. Summary:

- `workstream_start` fires AFTER `AHO_ITERATION=0.2.16` confirmed set (and `AHO_WORKSTREAM` set per W0 Bucket 3)
- `workstream_complete` fires only after audit archive exists with `pass` or `pass_with_findings`, from a fresh Claude session
- Audit archive overwrites forbidden
- Sign-off boxes are Kyle's per Pillar 11
- No git operations by agents
- Raw response is ground truth — every acceptance includes raw-response inspection
- No speed or capability claims without tuned-baseline measurement
- No celebratory framing per G081
- Cross-project contamination vigilance per CLAUDE.md / GEMINI.md
- ADR numbers determined at workstream execution time from `artifacts/adrs/` index — not pre-fabricated

**New for 0.2.16 — OTEL hygiene:**
- Every Claude Code session starts with verification that `aho.iteration`, `aho.workstream`, `aho.role` resource attrs are correctly set (check one emitted event in Jaeger before real work begins)
- Cost attribution per workstream is Pillar 8 ground truth — do not estimate from log parsing after 0.2.16 W1 lands
- `TRACEPARENT` propagation is backward-compatible — callers without trace context still work

---

*Plan doc 0.2.16. Design doc at `artifacts/iterations/0.2.16/aho-design-0.2.16.md` contains pillars, trident, scope, contingencies. This plan expands workstream execution detail. ADR numbers for W0, W2 deliverables determined at workstream execution time from ADR index — not pre-fabricated here.*
