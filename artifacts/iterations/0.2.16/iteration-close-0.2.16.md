# Iteration Close - aho 0.2.16

**Iteration:** 0.2.16
**Closed:** 2026-05-01T23:36:52Z
**Phase:** 0 (Clone-to-Deploy)
**Theme:** Claude Code OTEL Integration & 0.2.15 Close-Out
**Pattern:** C modified (Claude drafts, Gemini audits, Kyle signs)
**Iteration deliverable status:** SHIPPED (against amended Form 2 criterion;
see §Form 2 criterion amendment below - criterion was amended at close
under ADR 0006 hard-meta-rule treatment, not met as originally written).

This is the first iteration close performed under ADR 0006's
iteration-deliverable-discipline convention. ADR 0006 itself landed in
W4 of this iteration; the Form 2 criterion was constructed retroactively
in retrospective §1.2.

---

## Graduation criterion (Form 2: artifact existence + content)

The criterion text below reflects the **amended** §1.2 lines as they
stand after Kyle's authorized amendment at close (see §Form 2 criterion
amendment for what changed and why). Each numbered line corresponds to
retrospective `§1.2` line N.

1. `.claude/settings.json` env block contains the OTEL toggle, exporter
   protocol, endpoint, log toggles, and resource attribute string with
   `service.name=claude-code` and three `aho.*` keys. **(W0)**
2. Pillar 8 cost-and-token telemetry surfaces in the operator-cockpit
   dashboard. Form 2 verification:
   `artifacts/iterations/0.2.16/dashboards/api-otel-sample.json` exists
   and is a valid JSON OTEL response fixture; the Flutter claw3d
   dashboard at `web/claw3d/lib/main.dart` contains a Workstream
   Telemetry section with cost / token / cache-ratio rendering. **(W1,
   amended)**
3. `src/aho/pipeline/dispatcher.py` and `src/aho/pipeline/router.py`
   read `TRACEPARENT` and create child spans; corresponding tests in
   `artifacts/tests/test_dispatcher_traceparent.py` /
   `test_router_traceparent.py` pass. **(W2)**
4. `artifacts/iterations/0.2.16/alerts/pillar-11-violations.yaml` and
   `anomaly-rules.yaml` exist and contain five rules total;
   `src/aho/alerts/telegram_alerts.py` exists with typed-error → HTTP-
   status mapping and `AlertSecretMissingError` path. **(W3)**
5. `artifacts/adrs/0003-otel-scaffolding-posture.md`,
   `0004-iteration-close-confirm-redesign.md`,
   `0005-gemini-otel-asymmetry.md`,
   `0006-iteration-deliverable-discipline.md`,
   `0007-containerization-architecture.md`,
   `0008-dispatcher-missing-model.md` all exist as Accepted (or
   Proposed where explicitly noted). **(W0/W2/W4)**
6. `artifacts/iterations/0.2.16/acceptance/W{0,1,2,3,4}.json` and
   matching `audit/W{0,1,2,3,4}.json` exist with `audit_result` ∈
   `{pass, pass_with_findings}`.

## Verification

Each criterion line was asserted against current repo state at iteration
close. Evidence:

| # | Criterion line | Verified state | Evidence |
|---|---|---|---|
| 1 | settings.json OTEL env block | PASS | `python3 -c "json.load(open('.claude/settings.json'))['env'][...]"` returned all six required keys (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER=otlp`, `OTEL_LOGS_EXPORTER=otlp`, `OTEL_TRACES_EXPORTER=otlp`, `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, `OTEL_RESOURCE_ATTRIBUTES=service.name=claude-code,aho.iteration=0.2.16,aho.workstream=W4,aho.role=drafter`). |
| 2 | claw3d Workstream Telemetry + api-otel-sample.json | PASS (amended) | `api-otel-sample.json` parses as valid JSON, top-level keys include `iteration`, `workstreams`, `iteration_rollup`. `web/claw3d/lib/main.dart` contains literal string `'Workstream Telemetry'` at line 434 and 442; surrounding scope renders cost (`$x.xxxx`), tokens (input/output/cache-read/cache-creation/total), and cache-ratio. |
| 3 | TRACEPARENT in dispatcher + router with tests | PASS | `grep -l TRACEPARENT src/aho/pipeline/dispatcher.py src/aho/pipeline/router.py` matched both. Both test files exist with documented `test_absent` / `test_present` / parent-trace-id-inheritance coverage. |
| 4 | Five alert rules + bridge code | PASS | `pillar-11-violations.yaml` contains `Pillar11CommitViolation` + `Pillar11PullRequestViolation` (2 rules); `anomaly-rules.yaml` contains `ClaudeAPIErrorSpike` + `ClaudeCostAnomaly` + `ToolDurationOutlier` (3 rules). Total 5. `telegram_alerts.py` matches 11 occurrences of typed-error / HTTPStatus / status_code symbols. |
| 5 | ADRs 0003–0008 | PASS | 0003/0005/0006/0007/0008 = `Status: Accepted`; 0004 = `Status: Proposed (design only; implementation deferred to 0.2.16 W4)` - explicitly noted per criterion text. |
| 6 | acceptance + audit archives W0..W4 | PASS | All ten files exist on disk. W0/W3/W4 audits = `pass`; W1/W2 audits = `pass_with_findings`. |

All six criterion lines PASS. Iteration is shipped against the amended
Form 2 criterion.

## Workstreams shipped

All five workstreams reached `workstream_complete` per Pattern C state
machine.

| WN | Theme | Audit | Audited by | Workstream complete event |
|---|---|---|---|---|
| W0 | 0.2.15 close-out + substrate closure + OTEL scaffolding | pass | gemini-cli | `~/.local/share/aho/events/aho_event_log.jsonl` |
| W1 | Pillar 8 cost + token dashboard | pass_with_findings | gemini-cli | (same log) |
| W2 | Distributed tracing - TRACEPARENT propagation | pass_with_findings | gemini-cli | (same log) |
| W3 | Pillar 11 enforcement + anomaly detection | pass_with_findings | gemini-cli | (same log) |
| W4 | ADR-heavy close (re-scoped from cross-model cascade re-run) | pass | gemini-cli | (same log) |

W4 was re-scoped mid-iteration from cross-model cascade re-run + Mercor
reference pack assembly to ADR-heavy close (three ADRs + 0.2.17 plan +
0.3 charter + retrospective + drift sweep). Re-scoping is recorded in
`acceptance/W4.json` → `scope_notes.rescope_disposition`, retrospective
§4.1–4.2, and the W4 launch brief itself. Cascade re-run and Mercor
pack assembly graduate to future iterations.

## AF findings across iteration

11 audit findings across W0–W4 audits. Per-workstream disposition notes
co-located with the sealed acceptance archives at
`acceptance/W{N}-audit-dispositions.md` (W1/W2/W3/W4). High-level summary:

- W0: pass (no AFs surfaced).
- W1: AF003 (baseline failure-count typo, cosmetic), AF004
  (`api_error_count` aliasing, important), AF005
  (`api_retries_exhausted_count` dead field, important).
- W2: AF003 (tests-collected coherence drift 421 vs 427, cosmetic),
  AF004 (`dispatch.duration_ms` error-path measurement gap, info).
- W3: AF001 (Rule 3 expression repair, cosmetic), AF002 (Rule 5
  baseline larger n, info), AF003 (Rule 5 metric-source gap, info).
- W4: AF001 (deviation-count coherence, info - acknowledged, no
  carry-forward), AF002 (CLI gap on `pending_audit` state, info -
  carry-forward to 0.2.x cleanup, future ADR candidate).

Detail and Kyle's verbatim dispositions live in
`carry-forwards-0.2.16.md` and the per-workstream `*-audit-dispositions.md`
files.

## Carry-forwards to future iterations

Canonical list: `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`.
Final count: **24** entries (counted by hand against the file as of
this close, including the new W4-AF002 entry under the "0.2.x cleanup
(future ADR candidate)" target). Targets:

- 0.2.16 close-out drift repair: 2 items (W1-AF003, W2-AF003;
  acceptance-archive-sealed).
- 0.2.16 W3 adjunct OR 0.2.17 harness hygiene: 2 items.
- 0.2.17: 8 items (folded into 0.2.17 W0 per `aho-plan-0.2.17.md`
  §Cross-iteration carry tracking).
- engine-selection ADR + bridge live wire-up (0.2.17 or 0.3): 8 items
  (W3-AF001, W3-AF002, W3-AF003, W3-CF1 through W3-CF5).
- 0.2.x cleanup (future ADR candidate): 1 item (W4-AF002 - `pending_audit`
  CLI gap; pairs with the iteration-level graduation-criterion CLI gap
  surfaced at this close).
- next collector config touch: 1 item (OTLP alias deprecation warning).
- future iteration triggered by external need: 2 items (cross-model
  cascade re-run with paired Auditor comparison; Mercor reference pack
  assembled-as-deployable-unit).

## Form 2 criterion amendment

This is the first iteration close under ADR 0006. At close-time
verification, **retrospective §1.2 line 2 failed against repo state**
as originally written. The original line read:

> `artifacts/iterations/0.2.16/dashboards/pillar-8-cost-tokens.json`
> exists, parses as valid Grafana JSON, references the four expected
> panels (P1–P4 minimum). (W1)

Two failure modes:

1. The file at the named path does not exist. Only `api-otel-sample.json`
   exists in `dashboards/`.
2. The retrospective §3 ship-honest table claimed "Grafana JSON exists
   in the export pack" - but `export/claude-otel-reference-pack/`
   contains only `alerts/`. No Grafana JSON ships in the export pack.

**Rationale for amendment.** The retrospective's Form 2 criterion was
constructed retroactively at W4 close (the convention itself landed in
W4); the line 2 wording was derived from W1 plan-doc language. The W1
plan called for a Grafana JSON dashboard, but mid-W1 the scope was
clarified to extend the existing Flutter claw3d operator cockpit with
a Workstream Telemetry section instead. That redirect was Kyle-approved
and dispositioned at W1 audit time (the W1 acceptance archive ships
the claw3d-extension surface as W1's deliverable). The retroactive
criterion derivation in W4 reverted to the plan-doc wording without
folding the W1 audit-time disposition forward - a derivation error,
not a scope drift.

The criterion-as-written is wrong against W1 ship reality. Amending it
to match what actually shipped is historical correction. The
as-shipped surfaces - Flutter claw3d Workstream Telemetry section +
the on-disk OTEL response fixture - are the artifacts the amended
criterion now names. Both exist; both verify; the iteration ships
against the amended criterion line.

**ADR 0006 hard-meta-rule treatment authorized by Kyle.**
Per ADR 0006 §Decision: "If the criterion fails, the iteration does
not close - it stays open until the criterion passes or until the
criterion itself is amended (same hard meta-rule treatment as above)."
Kyle authorized the amendment explicitly at close-time with the message
text "Option 2 (amend the criterion). Authorizing under ADR 0006
hard-meta-rule treatment." Authorization is recorded here.

**Files changed.** `artifacts/iterations/0.2.16/retrospective-0.2.16.md`
§1.2 line 2 + §3 row 2 amended in place. Sealed acceptance archives
(`acceptance/W{0,1,2,3,4}.json`) untouched. Kyle's signed
`sign-off-0.2.15.md` analog for 0.2.16 (when produced) inherits the
amendment.

**Honest characterization (G081).** The iteration ships against the
amended Form 2 criterion. It does not ship against the criterion as
originally written. The amendment is a first-class scope decision made
at close-time, not a silent fix. ADR 0006's hard-meta-rule treatment
made the amendment a structural artifact rather than retroactive
backfill. This close is the convention's first stress test; the
convention worked - the gap surfaced at the gate, was characterized
honestly, and was dispositioned explicitly.

## Procedural observations for future ADR

Two CLI gaps surfaced through this iteration's close that pair into a
single future-ADR candidate:

1. **Workstream-level `pending_audit` gap.** W4 audit AF002 - Pattern
   C state machine includes `pending_audit` (drafter writes acceptance
   archive; checkpoint advances to that state pending Gemini audit),
   but `aho iteration workstream` exposes only `start` / `complete`.
   Today the state is implied by archive existence; checkpoint
   `last_event` lags by one transition through every workstream's
   audit window.
2. **Iteration-level graduation-criterion verification gap.** ADR 0006
   §Decision step 2 requires the drafter to "Assert each condition of
   the graduation criterion against current repo state" before
   emitting `iteration_complete`. `aho iteration close --confirm`
   exists but does not mechanically read the criterion or assert each
   line - that work is done by hand in this artifact. A pre-confirm
   subcommand that parses a structured graduation block and runs the
   assertions would close the gap. Out of scope for ADR 0006 itself
   (called out in §Out of Scope as the future enhancement that may
   couple with ADR 0004's redesign).

Both gaps belong to the same future-ADR candidate. Recorded in
`carry-forwards-0.2.16.md` under target "0.2.x cleanup (future ADR
candidate)" alongside W4-AF002.

## Editorial note - Pattern C → Adversarial Authorship rename

"Pattern C" terminology used throughout this iteration - including
this artifact, the W4 acceptance archive, the retrospective, and all
sealed audit dispositions - is being renamed to **Adversarial
Authorship** prospectively in 0.2.17 W0. The rename is verbal /
external as of this close (Kyle uses the new term in conversation, IR
materials, README revisions, and external positioning); the
codebase-wide find/replace lands as a planned 0.2.17 W0 deliverable.

Sealed acceptance archives in `artifacts/iterations/0.2.16/acceptance/`
are NOT retroactively edited. They retain "Pattern C" verbatim. Live
governance docs (CLAUDE.md, GEMINI.md, ADR 0006, the iteration plan
template, carry-forwards-0.2.16.md) get the rename in 0.2.17 W0.

The rename rationale: "Pattern C" was an arbitrary label that accreted
load-bearing meaning by repetition. "Adversarial Authorship" describes
the pattern's actual structural property (drafter and auditor are
constitutionally adversarial; human is sole signing authority) and is
externally distinctive. See `artifacts/iterations/0.2.17/aho-plan-0.2.17.md`
W0 for the planned find/replace scope.

## Iteration deliverable status

**SHIPPED** - against the amended Form 2 criterion above. All six
criterion lines verified. Five workstreams reached
`workstream_complete`. Sealed acceptance archives intact. Carry-
forwards routed to future iterations with explicit targets. Pattern C
state machine completed end-to-end for the first iteration ever closed
under ADR 0006's discipline; the convention surfaced one structural
issue (line 2 derivation error) at the gate and resolved it via the
hard-meta-rule amendment path the ADR contemplates.

---

*Iteration close artifact 0.2.16. Companion artifacts:
`retrospective-0.2.16.md` (amended at close - see §1.2 line 2 and §3
row 2 footnotes), `carry-forwards-0.2.16.md`, `acceptance/W{0..4}.json`,
`audit/W{0..4}.json`, `acceptance/W{1,2,3,4}-audit-dispositions.md`,
ADRs 0003 / 0004 / 0005 / 0006 / 0007 / 0008 under `artifacts/adrs/`.*
