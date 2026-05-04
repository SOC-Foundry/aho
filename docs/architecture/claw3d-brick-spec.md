# claw3d brick spec

**Status:** Repo-resident authoritative spec (W5 D5 deliverable).
**Iteration of record:** aho 0.2.17 W5, consolidating 0.2.17 W4 D2/D3/D4/D5/D6 brick implementations.
**Source paths:** all relative to repo root.
**Supersedes:** chat-side architecture artifact `aho-base-container-architecture.md` §claw3d coverage.

---

## What claw3d is

claw3d is aho's per-component dashboard surface. Each component renders as a single brick — green when healthy, red when a fault predicate matches, unknown when the component has no signal in the observation window. The brick layer reads aggregated OTEL state via `aho.dashboard.otel_aggregator`; no brick polls Ollama, ChromaDB, systemd, or any external surface directly.

Brick predicates are pure functions over a `signal_state: dict` shape (`{counters, presence, flags}`). Predicates are deliberately small — anything fancier moves into the aggregator so brick logic stays inspectable. The canonical synthetic state fixture (`bricks.synthetic_signal_state(healthy=...)`) drives tests, probes, and dashboard demonstrations without requiring a live OTEL collector.

The W4 D2 plan-doc fixed coverage at ten components. Three additional surfaces sit alongside the per-component grid:

- **Materiality dashboard surfaces** (W4 D3) — four-bucket render of the ADR-0010 protocol counters.
- **Materiality comparison surface** (W4 D5) — iteration-over-iteration comparison of the same four buckets.
- **Role-collapse trip-wire brick** (W4 D4) — single dedicated brick rendering the Pillar 7 invariant, parallel to the per-component grid's `aho.adversarial` brick.
- **Anti-rubber-stamp dashboard** (W4 D6) — four-surface verification dashboard.

---

## Per-component bricks (10)

Source: `src/aho/dashboard/lego/bricks.py` (W4-close sha256 `35cbb6c1a7ba24762e857e750f98253eac21066be3641d3efd021ed5e5e96fd4`).

Color rule (canonical): **red wins over green; if neither predicate matches, brick is unknown.** A brick that cannot decide is not green.

### 1. `aho.dispatcher` — pipeline dispatcher

Local model dispatch wrapper. Reads OTEL counters emitted by `src/aho/pipeline/dispatcher.py`.

| Field | Value |
|---|---|
| Signal keys | `aho.pipeline.dispatcher.invocation_count`, `aho.pipeline.dispatcher.error_count` |
| Red predicate | `error_count > 0` |
| Green predicate | `invocation_count > 0 AND error_count == 0` |
| Unknown | no dispatcher activity in window |

### 2. `aho.adversarial` — Adversarial Authorship dispatch (role-collapse trip-wire)

The role-collapse trip-wire surface. Same signal source as the dedicated W4 D4 trip-wire brick; this one wraps it for the per-component grid view.

| Field | Value |
|---|---|
| Signal keys | `aho.council.dispatch.role_collapse_tripwire_fired`, `aho.council.dispatch.invocation_count` |
| Red predicate | `role_collapse_tripwire_fired > 0` |
| Green predicate | `invocation_count > 0 AND role_collapse_tripwire_fired == 0` |
| Unknown | no dispatch activity in window — invariant inactive, not violated |

### 3. `aho.workstream` — workstream events / checkpoint emit

Reads counters emitted by `src/aho/workstream_events.py` for state-machine event emission and checkpoint-write health.

| Field | Value |
|---|---|
| Signal keys | `aho.workstream.event_count`, `aho.workstream.checkpoint_write_error_count` |
| Red predicate | `checkpoint_write_error_count > 0` |
| Green predicate | `event_count > 0 AND checkpoint_write_error_count == 0` |
| Unknown | no workstream events in window |

### 4. `aho.secrets_client` — read-only host ↔ container bridge

Read-only counters from `src/aho/secrets_client.py`. The broker boundary's container-side liveness surface per ADR-0009.

| Field | Value |
|---|---|
| Signal keys | `aho.secrets_client.read_count`, `aho.secrets_client.error_count` |
| Red predicate | `error_count > 0` |
| Green predicate | `read_count > 0 AND error_count == 0` |
| Unknown | no broker reads in window |

### 5. `aho.otel` — OTEL exporter liveness

Reads health of the OTEL pipeline itself: did `logs.jsonl` and `metrics.jsonl` get emit signals.

| Field | Value |
|---|---|
| Signal keys | `aho.otel.logs_emitted_count`, `aho.otel.metrics_emitted_count`, `aho.otel.exporter_error_count` |
| Red predicate | `exporter_error_count > 0` |
| Green predicate | `logs_emitted_count > 0 AND metrics_emitted_count > 0` |
| Unknown | OTEL pipeline silent (collector not started, host degraded) |

### 6. `aho.health` — periodic /healthz + /readyz probes

Container-side health primitive (`src/aho/health.py`). Emits success / failure counts as the readiness probe stack runs.

| Field | Value |
|---|---|
| Signal keys | `aho.health.probe_success_count`, `aho.health.probe_failure_count` |
| Red predicate | `probe_failure_count > 0` |
| Green predicate | `probe_success_count > 0 AND probe_failure_count == 0` |
| Unknown | no health activity in window |

### 7. `aho.signal` — telegram + halt-and-surface

Signal / alert subsystem (`src/aho/signal.py`). Tracks alert emission and error count.

| Field | Value |
|---|---|
| Signal keys | `aho.signal.emit_count`, `aho.signal.error_count` |
| Red predicate | `error_count > 0` |
| Green predicate | `emit_count > 0 AND error_count == 0` |
| Unknown | no signal activity in window |

### 8. `aho.council.audit` — auditor seat (llama3.2 + RAG + post-hoc filter)

The auditor seat's per-component brick. The W4 update extends the brick with a filter-activity drill-down (`extra_render`) that exposes the deterministic post-hoc filter's eligibility and suppression counts alongside the brick color.

| Field | Value |
|---|---|
| Signal keys | `aho.council.audit.invocation_count`, `aho.council.audit.error_count`, `aho.council.audit.finding_filter.eligible_count`, `aho.council.audit.finding_filter.suppressed_count` |
| Red predicate | `error_count > 0` |
| Green predicate | `invocation_count > 0 AND error_count == 0` |
| Extra render | `filter_eligible_count`, `filter_suppressed_count`, `audit_count`, `audit_error_count` |
| Unknown | no audit activity in window |

### 9. `aho.council.triage` — triage seat (nemotron-mini)

Triage seat's classification health. Red on malformed-output count (G083 hardening fired), which is the architecturally-load-bearing failure mode for triage.

| Field | Value |
|---|---|
| Signal keys | `aho.council.triage.invocation_count`, `aho.council.triage.malformed_count` |
| Red predicate | `malformed_count > 0` |
| Green predicate | `invocation_count > 0 AND malformed_count == 0` |
| Unknown | no triage activity in window |

### 10. `aho.council.embed+aho.rag` — embed + RAG retrieval (combined)

Combined brick covering the embed seat (`aho.council.embed`) and the RAG layer (`aho.rag`). They share a contract: retrieve into the audit-prompt's `## Registered references` section and provide query liveness for triage.

| Field | Value |
|---|---|
| Signal keys | `aho.council.embed.invocation_count`, `aho.rag.query_count`, `aho.rag.error_count` |
| Red predicate | `aho.rag.error_count > 0` |
| Green predicate | `aho.rag.query_count > 0 AND aho.rag.error_count == 0` |
| Unknown | no retrieval activity in window |

---

## Materiality dashboard surfaces

Source: `src/aho/dashboard/lego/materiality_surfaces.py` (W4-close sha256 `9e6b97399c91354c18bc5dfaedc7134f2da607b4340d2e14653a58614fddbd8c`).

Four bucket surfaces, plus an overview surface that combines all four into a single header rendering. Each per-bucket surface exposes:

- The running total count.
- Per-severity breakdown (`info`, `important`, `critical`).
- Last-update timestamp (from the aggregator's window).

The four buckets correspond directly to the [ADR-0010](../../artifacts/adrs/0010-materiality-measurement.md) counter names:

| Bucket id | OTEL counter source | Description |
|---|---|---|
| `caught_by_llama` | `aho.materiality.claim_vs_artifact_mismatches.caught_by_llama` | Claim/artifact mismatches surfaced by the llama auditor seat. |
| `caught_by_drafter` | `aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter` | Mismatches surfaced by the drafter (gap-net) after auditor passed the artifact. |
| `escaped` | `aho.materiality.claim_vs_artifact_mismatches.escaped` | Mismatches surfaced retrospectively — escaped a sealed iteration. |
| `carry_forward_resolution` | `aho.materiality.carry_forward_resolution_rate` | Carry-forwards explicitly closed by reference in a workstream output. |

Overview surface composition: `OverviewSurface.catch_rate_components` carries the three catch-rate buckets (`caught_by_llama`, `caught_by_drafter`, `escaped`) so the dashboard can render the at-a-glance "is the auditor doing useful work?" view that the protocol is designed to surface. `carry_forward_resolution_count` renders separately as the loop-closure metric.

State normalization helper: `materiality_surfaces.materiality_state_from_otel_counters(counters)` converts the raw `aho.materiality.*` counter dict into the per-bucket dashboard shape.

---

## Materiality comparison surface

Source: `src/aho/dashboard/lego/materiality_comparison.py` (W4-close sha256 `9038f83119249bbdef14feea10aa5f54efbaf4b5d7b99d68f668bce362f4177b`).

Iteration-over-iteration comparison of the four materiality buckets. Each row in the comparison table renders one bucket across N iterations, visualizing the catch-rate distribution as the protocol's evidence accumulates.

Per ADR-0010, the falsifiability threshold is exercised at N≥8 iterations:

- ≥30% reduction in `escaped` vs the baseline window (first three iterations under the protocol).
- Non-zero `caught_by_llama` and `caught_by_drafter` across the protocol window.
- Carry-forward resolution rate ≥60% within 2 iterations of flagging.

The comparison surface is the dashboard rendering of the threshold's exercise — at 0.2.17 close, with N=4, the comparison surface renders qualified-validation state, not full validation. Comparison rows are tagged with the iteration label and acceptance-archive sha for cross-reference to the sealed evidence.

---

## Role-collapse trip-wire brick

Source: `src/aho/dashboard/lego/role_collapse_brick.py` (W4-close sha256 `e7b836217e64bf25393214b820ce04422f42924491b4e28971083f7f8f4e7272`).

A single dedicated brick rendering the Pillar 7 invariant: in any single iteration, drafter and auditor must not collapse onto the same model family. `aho.council.dispatch.record_role_family` raises `CouncilRoleCollapseError` when the invariant is violated; this brick surfaces whether that has fired.

Distinct from the per-component grid's `aho.adversarial` brick: D2's `aho.adversarial` sits in the per-component grid alongside other components for at-a-glance health review; this dedicated brick is a focused one-brick surface dedicated to the invariant. Both read the same signal source so they cannot disagree.

| Field | Value |
|---|---|
| Component id (when promoted to BrickState) | `aho.adversarial.role_collapse_tripwire` |
| Signal keys | `aho.council.dispatch.role_collapse_tripwire_fired`, `aho.council.dispatch.invocation_count` |
| Red predicate | `tripwire_fired_count > 0` |
| Green predicate | `dispatch_invocation_count > 0 AND tripwire_fired_count == 0` |
| Unknown | no dispatch activity in window — invariant inactive, not violated |
| Drill-down | `role_pair_snapshot` from `flags` — captures which (drafter, auditor) family pair would have collapsed when the trip-wire fires |

Pillar 7 falsifiability surface: a green brick is positive evidence the invariant held; a red brick is positive evidence of a violation; an unknown brick is positive evidence of no exercise (which is honest — the invariant is only meaningful when dispatch ran).

---

## Anti-rubber-stamp dashboard (four surfaces)

Source: `src/aho/dashboard/lego/anti_rubber_stamp_dashboard.py` (W4-close sha256 `04748ce6fac719c776d6a2b66d66db534d025ac3a7aba415ff37044e70e3774c`).

**Four-surface version (W4 D6 update — was three-surface pre-W4).** The fourth surface is the deterministic post-hoc filter, added when W4 D1 closed the fake-ID-on-registered-anchor failure mode structurally.

Surface ids:

```
SURFACE_IDS = (
    "nemotron_raise_on_malformed",
    "llama_confidence_floor_lock",
    "role_collapse_tripwire",
    "deterministic_post_hoc_filter",
)
```

### Surface 1 — `nemotron_raise_on_malformed`

Nemotron triage out-of-rubric protection (G083). Hardening raises `CouncilTriageMalformedError`; this surface counts how often the hardening fired vs how many triage invocations succeeded.

| Field | Value |
|---|---|
| Signal keys | `aho.council.triage.invocation_count`, `aho.council.triage.malformed_count` |
| Red | `malformed_count > 0` (hardening fired — out-of-rubric output emitted) |
| Green | `invocation_count > 0 AND malformed_count == 0` |
| Unknown | no triage activity in window |

### Surface 2 — `llama_confidence_floor_lock`

Llama audit confidence-floor lock. Hardening rewrites `clean+low-confidence` dispositions to `surface_to_drafter`; this surface counts lock firings.

| Field | Value |
|---|---|
| Signal keys | `aho.council.audit.invocation_count`, `aho.council.audit.confidence_floor_lock_count` |
| Red | `confidence_floor_lock_count > 0` (lock fired — would-be `clean` rewritten to `surface_to_drafter`) |
| Green | `invocation_count > 0 AND confidence_floor_lock_count == 0` |
| Unknown | no audit activity in window |

### Surface 3 — `role_collapse_tripwire`

Drafter/auditor role-collapse trip-wire. Same signal as the dedicated W4 D4 brick; rendered here as part of the anti-rubber-stamp posture for at-a-glance verification across all four hardenings.

| Field | Value |
|---|---|
| Signal keys | `aho.council.dispatch.role_collapse_tripwire_fired`, `aho.council.dispatch.invocation_count` |
| Red | `role_collapse_tripwire_fired > 0` |
| Green | `invocation_count > 0 AND role_collapse_tripwire_fired == 0` |
| Unknown | no dispatch activity |

### Surface 4 — `deterministic_post_hoc_filter` (W4 D6 addition)

W4 D1 deterministic post-hoc filter on RAG-aware audit findings. Suppresses findings where BOTH a registered anchor AND a fake-ID phrase appear in the description. Suppressed findings are recorded structurally for drafter / operator inspection (not silently dropped).

| Field | Value |
|---|---|
| Signal keys | `aho.council.audit.finding_filter.eligible_count`, `aho.council.audit.finding_filter.suppressed_count`, `aho.council.audit.finding_filter.over_suppression_invariant_failures` |
| Red | `over_suppression_invariant_failures > 0` (filter over-suppressed — narrowness invariant broken) |
| Green | `eligible_count > 0 AND no over-suppression failures` |
| Unknown | filter not eligible (no registered anchors in prompt context) |

The drill-down detail records the per-suppression record so drafters can inspect what the filter caught and verify the suppression was structurally narrow.

### Overview surface

`evaluate_overview(surfaces)` produces a single SurfaceState rendering the worst-color across the four surfaces — red if any red, green if all green, unknown if all unknown. The overview is the at-a-glance answer to "is the anti-rubber-stamp posture intact this iteration?"

---

## Synthetic load test fixture

`bricks.synthetic_signal_state(healthy=...)` produces a counter dict consistent with a 5-minute synthetic load test:

- `healthy=True` — every brick evaluates green. Every counter has positive activity, every error counter is zero.
- `healthy=False` — one fault per component so every brick evaluates red. The fixture is exhaustive: one demonstrable red predicate match per brick, plus a role-collapse trip-wire fire, plus an OTEL exporter error.

Tests at `artifacts/tests/test_lego_bricks.py` and `test_role_collapse_brick.py` exercise both fixtures end-to-end and assert color outcomes.

The fixture exists explicitly so dashboards rendering claw3d on a host with no live OTEL collector — operator reviewing artifact archives offline, drafter inspecting brick rendering during plan-doc authoring — get a faithful preview of brick semantics without needing live signal.

---

## Color rules — canonical

These rules apply uniformly across all per-component bricks, the role-collapse trip-wire brick, the materiality bucket surfaces, and the four anti-rubber-stamp surfaces:

1. **Red wins over green.** A red predicate match always overrides a green predicate match. The fault has fired; the brick reds.
2. **Unknown is honest.** A brick that cannot decide between red and green is not green. Insufficient signal in the observation window produces `unknown` — the dashboard does not paint optimistic green over silence.
3. **Predicates are pure functions.** Same input → same output. No I/O, no time-based heuristics, no clock skew dependencies. The aggregator is the only path that touches I/O.
4. **Suppressed findings are recorded structurally.** The deterministic post-hoc filter does not silently drop findings; suppressions are emitted as structured records so drafters can inspect what was suppressed.

---

## Relationship to ADRs

| ADR / spec | This doc's surface |
|---|---|
| [ADR-0007 §Council roles](../../artifacts/adrs/0007-containerization-architecture.md) | Council seats consumed by bricks 8–10 + role-collapse trip-wire brick. |
| [ADR-0009](../../artifacts/adrs/0009-secrets-broker-boundary.md) | Brick 4 (`aho.secrets_client`) renders broker liveness; brick 7 (`aho.signal`) renders alerts including any broker auth failure. |
| [ADR-0010](../../artifacts/adrs/0010-materiality-measurement.md) | Materiality dashboard surfaces (4 buckets) + materiality comparison surface render the protocol's catch-rate evidence. |
| [Component decomposition](component-decomposition.md) | Each brick maps to one or two components in the decomposition; this doc's color rules govern how those components render. |

---

## Coverage summary

10 per-component bricks + 4 materiality bucket surfaces + 1 materiality overview surface + 1 materiality comparison surface + 1 role-collapse trip-wire brick + 4 anti-rubber-stamp surfaces + 1 anti-rubber-stamp overview = **22 distinct claw3d surfaces** at base tier.

The W4 D6 update from three-surface to four-surface anti-rubber-stamp dashboard is the load-bearing iteration delta that this doc captures. Pre-W4 anti-rubber-stamp had three surfaces (nemotron, llama, role-collapse); W4 D6 added the deterministic post-hoc filter as the fourth, explicitly because W4 D1 closed the fake-ID-on-registered-anchor failure mode structurally and the dashboard surface needed to reflect the new layer.
