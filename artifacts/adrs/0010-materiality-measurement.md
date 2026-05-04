# ADR 0010 — Materiality Measurement Protocol

**Status:** Accepted (qualified validation; full validation deferred)
**Date:** 2026-05-03
**Iteration of record:** aho 0.2.17 W5 (consolidating 0.2.17 W2/W3/W4 evidence build)
**Decision owner:** Kyle Thompson (signs), Claude web (drafted), Claude Code (executed at W2/W3/W4), llama3.2 + RAG + filter (audits at W5)
**Context surface:** aho project-internal — falsifiability protocol for
the architecture's "harness-as-IQ" claim. Binds 0.2.17 W2 D12 (counter
landing), W3 (RAG enrichment partial closure), W4 D1 (deterministic
post-hoc filter structural closure), 0.3.x materiality validation
runway.

---

## Context

The architecture's load-bearing claim — "the harness produces better
project outcomes than a single-agent executor on the same work" — is
a claim about output quality across iterations. Token-spend reduction
(an early framing hypothesis) is a *downstream artifact* of better
outcomes, not the design driver. A harness that costs more tokens but
produces structurally honest acceptance dispositions, surfaces
defects auditor-side rather than escaping to retrospectives, and
resolves carry-forwards within bounded windows is the harness that
beats the single-agent baseline.

Three forces shape the requirement for falsifiable evidence:

1. **The claim must be falsifiable.** Without a measurement protocol,
   "harness produces better outcomes" is unfalsifiable handwaving. A
   protocol that defines (a) what counts as a defect, (b) where a
   defect was caught, and (c) what the resolution-time distribution
   looks like, gives the architecture a falsifiable surface.

2. **The measurement must run continuously, not just at retrospective
   time.** Counter telemetry recorded per-event during workstream
   execution captures the catch-locus distribution at the moment it
   happens. Retrospective enumeration is necessary but
   reconstructive; the counters are the durable record.

3. **The evidence build must accrue over multiple iterations before
   the threshold is exercised.** N=1 measurement is anecdote. The
   threshold is defined for N≥8; until then, the protocol is
   recording data, not validating the claim.

0.2.17 W2 landed the counter primitive (D12). 0.2.17 W3 wired RAG
enrichment and observed partial false-positive closure. 0.2.17 W4
landed the deterministic post-hoc filter and structurally closed the
fake-ID-on-registered-anchor failure mode. Three iterations of
evidence now span the auditor-seat work, recorded honestly with the
N=4 caveat below.

## Decision

### Four-bucket OTEL counter telemetry

The protocol records four counters over the global OTEL
MeterProvider, with resource attributes `aho.iteration`,
`aho.workstream`, `aho.tier`, `aho.role` and a per-event
`aho.materiality.severity` attribute. Counter names match the
`src/aho/materiality.py` implementation verbatim:

| Bucket | OTEL counter name | Catch locus | Wired by |
|---|---|---|---|
| **caught-by-llama** | `aho.materiality.claim_vs_artifact_mismatches.caught_by_llama` | In-container llama auditor surfaces a claim/artifact mismatch during audit pass. | W2 D12 (real flow inside `aho.council.audit`). |
| **caught-by-drafter** | `aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter` | Drafter (gap-net) flags a defect that auditor dispositioned `clean` on the prior planning turn. | W2 D12 wires placeholder (`gap_carry_forward_writer`); W3 wires real-flow integration. |
| **escaped** | `aho.materiality.claim_vs_artifact_mismatches.escaped` | Defect surfaces retrospectively — neither auditor nor drafter caught it during sealing. | W2 D12 placeholder; W3 wires retrospective-fold-in increment path. |
| **carry-forward resolution rate** | `aho.materiality.carry_forward_resolution_rate` | Carry-forward explicitly closed by reference in a workstream output. | W2 D12 placeholder; W3 wires `carry_forwards_closed` inside acceptance archive emit. |

Counter primitives are created at module-import time in
`src/aho/materiality.py` (W4-close sha
`0ef021e3ee85d5c4390a7d40b19523d874ea84d6bdaeeb56b3f0a31fcac912b8`).
Each counter exposes a record function (`record_caught_by_llama`,
`record_caught_by_drafter`, `record_escaped`,
`record_carry_forward_resolution`) that the consuming primitives call
with severity and an extras dict. The OTEL Counter instruments are
non-functional under `_otel_available=False` (e.g., import failure
or no MeterProvider) — the record functions fail closed (no-op) so
materiality wiring does not block iteration execution under degraded
telemetry.

Baseline extraction lives at `src/aho/materiality_baseline_extract.py`
(W4-close sha
`0fecabc9c73de9148478517e03cc402d8145acd33951a33c7bd654bd76722030`)
and parses the OTEL metrics jsonl stream into per-iteration buckets
for the dashboard surfaces.

### Falsifiability threshold

The falsification surface is exercised when **N ≥ 8 iterations** have
completed under the protocol. Below N=8 the counters record honest
data but the threshold is not yet validated. At N ≥ 8:

1. **≥30% reduction in escaped defects vs the baseline window.** The
   baseline window is the per-iteration mean of the `escaped` bucket
   over the first three iterations under the protocol (0.2.17 W2 →
   the third iteration after the protocol activates). Subsequent
   per-iteration `escaped` counts must average ≥30% lower than the
   baseline window. A higher escape rate falsifies the claim.

2. **Non-zero `caught_by_llama` and `caught_by_drafter` buckets.**
   Both buckets must have non-zero values across the protocol window.
   A protocol that records only `caught_by_llama=0` or
   `caught_by_drafter=0` is not generating evidence about the
   architecture; it is generating evidence about a single seat's
   behavior. Both buckets non-zero means both seats are catching
   defects, which is what the architecture predicts.

3. **Carry-forward resolution rate ≥60% within 2 iterations of
   flagging.** Carry-forwards opened in workstream W{N} must reach a
   `closed` state in the carry-forwards file within iteration W{N+2}
   at a ≥60% rate. Items that persist beyond 2 iterations without
   closure are evidence of unbounded flagging — the carry-forward
   register becomes append-only-with-no-resolution and the protocol
   degrades to a logging surface rather than a feedback surface.

If any of (1), (2), (3) fail at N=8, the architecture's
"harness-as-IQ" claim is falsified at the protocol level and the
ADR is amended (or replaced) with the empirical finding.

### Three-iteration evidence build (qualified validation)

0.2.17 produced three iterations of evidence on the auditor seat's
contribution to the materiality protocol. Recorded honestly, the
build is:

#### W2 (baseline) — auditor without enhancement

W2 deployed the in-container llama3.2:3b auditor for the first time
(D11 self-audit), with counter wiring landing in D12 verification
probe. Self-audit produced a **false positive**: F-0.2.17-W1-003
flagged as "looks placeholder" despite being sealed-real and
registered in the carry-forwards file. The counter
`claim_vs_artifact_mismatches.caught_by_llama` incremented for this
finding — counted in the bucket, but the increment recorded a defect
the model fabricated, not a defect the artifact contained.

W2 acceptance archive sha256:
`4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`.

The materiality protocol was active and recording; the
auditor-as-deployed at W2 had a known capability gap
(F-0.2.17-W2-006 — reference-resolution gap; small-model
pattern-matching on ID syntax without registry access).

#### W3 (partial fix) — RAG enrichment

W3 wired `aho.council.audit_ref_lookup` (W3 D2) and
`aho.council.audit_ref_extract` (W3 D2) into the audit prompt
construction in `aho.council.audit`. The audit primitive now
retrieves "is this ID registered?" via ChromaDB query before flagging
reference-resolution issues, inlining the answer into the prompt's
`## Registered references` section.

W3 D4 RAG-vs-non-RAG comparison closed **1 of 2** demonstrated false
positives:

- W0 replay: F-W0-004 false positive **closed** under RAG
  enrichment (W0 self-audit replay no longer flags the registered
  ID).
- W2 self-audit replay: F-0.2.17-W1-003 false positive
  **persisted** under same prompt rule, same context shape, same
  model. Small-model prompt-following inconsistency at base tier —
  llama3.2:3b honors the registered-references rule on some prompts
  but not others. Mechanism: the rule is paragraph-form text at
  the end of a large system prompt, and the model selectively
  attends.

W3 acceptance archive sha256:
`9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`.

W3 surfaced F-0.2.17-W3-001 (residual prompt-following
inconsistency); F-0.2.17-W2-006 stays open until W4 closes both via
structural fix.

#### W4 (structural closure) — deterministic post-hoc filter

W4 D1 landed `aho.council.audit_finding_filter` — a deterministic
post-pass that drops findings whose anchor IDs are listed
`registered` in the prompt context AND whose description matches the
fake-ID phrase set ('not real', 'looks placeholder', 'matches naming
conventions', etc.). Filter is structural — it does not bet the
architecture on small-model prompt-following.

Filter verified against:

- The exact F-0.2.17-W1-003 false positive that W3 D4 left open
  (D1 acceptance gate 1, W2 self-audit-rag artifact target sha
  `afbc33a3ae68d90f444e5661cf7146180de9798eb2534a1cfd1f004882bfc91a`).
  **Suppressed correctly.**
- The W3 self-audit (D1 gate 2, target sha
  `b3a4e2e6c88244f4b4fcd59f75b56112beed8287600eb2308a7cdb7f4a605efc`,
  three findings remain active). **Did not over-suppress.**
- Synthetic positive and negative tests (D1 gates 3 + 4) for the
  structural-narrowness invariant.

W4 acceptance archive sha256:
`949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`.
W4 audit archive (llama self-audit verbatim disposition
`surface_to_drafter`) sha256:
`9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`.

Both demonstrated false positives (the only two that manifested
across W0/W1/W2 RAG replays) are now structurally addressed.
F-0.2.17-W2-006 and F-0.2.17-W3-001 close at W4 close. The W4 D1
filter does NOT bet the architecture on small-model prompt-following:
the model can ignore the registered-references rule and the failure
mode is still contained because the filter reads the same RAG context
the prompt section was built from and applies the suppression
deterministically.

### N=4 caveat — qualified validation, not full validation

The 0.2.17 evidence build spans **four iterations** (W0 / W1 / W2 /
W3) with the auditor primitive deploying first at W2 and stabilizing
at W4. **N=4 is below the N≥8 threshold.** This ADR's three-iteration
evidence build is **qualified validation, not full validation**:

- The protocol is implemented and recording data correctly (counter
  primitive lands at W2 D12, materiality dashboard surfaces land at
  W4 D5).
- The auditor primitive's known failure modes are progressively
  contained across W2/W3/W4 (baseline → partial → structural).
- Both demonstrated false positives that surfaced across W0/W1/W2
  RAG replays close structurally at W4.

But the falsifiability threshold (≥30% reduction in escaped, non-zero
catch buckets, ≥60% resolution rate) is **not yet exercised** — the
N≥8 window has not closed. 0.3.x continues the evidence build under
partial-tier auditor deployment. Full validation lands when the
falsifiability threshold has been exercised against an N≥8 evidence
window.

The qualified validation status is **deliberately recorded** as part
of this ADR's accepted state. Premature claims of full validation
(at N=4 or below) would be exactly the rubber-stamping the
architecture is designed to surface.

## Rationale

> Token-spend reduction is downstream of better outcomes; outcomes
> are what we measure.

Three forces drive the four-bucket protocol:

1. **Catch-locus is more informative than catch-rate.** A protocol
   that counts "total defects caught" tells you nothing about which
   seat is doing what; the same total can come from a single seat
   doing all the work or from balanced contributions across seats.
   Splitting by catch locus (`caught_by_llama` vs `caught_by_drafter`
   vs `escaped`) makes the architecture's distributed-evaluation
   premise observable.

2. **Resolution rate closes the loop.** Catch-locus alone records
   defect surfacing; the resolution rate counter records what
   happens after surfacing. A high catch rate with a low resolution
   rate is evidence that the protocol is generating noise (or that
   the team can't keep up with the noise). A balanced catch + high
   resolution is evidence the loop is functioning.

3. **The N≥8 threshold prevents premature claims.** Architecture
   claims are easy to make against N=1; they are robust against
   N=8. The N=4 caveat in this ADR makes the qualified state
   explicit so future readers can tell at a glance whether the
   "harness-as-IQ" claim has been exercised against the threshold or
   merely recorded against fewer iterations of evidence.

The three-iteration auditor-seat evidence build (W2 baseline → W3
partial → W4 structural) is itself a sample of the protocol
operating: the auditor surfaced a known failure mode (false
positives on registered IDs); the architecture progressively
contained the failure mode without changing the model; the
containment shipped as repo-resident code. That is the shape the
protocol is designed to surface and reward.

## Consequences

### Positive

- The "harness-as-IQ" claim becomes falsifiable. Future iterations
  either accumulate evidence toward the threshold or flag failures
  against it; either outcome is informative.
- Catch-locus telemetry exposes seat-level contributions. Future
  amendments (adding a partial-tier auditor seat at 0.3.x) get
  observable comparative data, not just total-count drift.
- Carry-forward resolution rate as a counter ties the open-loop
  flagging surface to the closed-loop resolution surface. A protocol
  that opens carry-forwards faster than it closes them surfaces
  inside the same dashboard the auditor seat reports through.
- The three-iteration evidence build (W2 → W4) is recorded with
  sealed shas, so future architectural arguments grounded in
  "0.2.17 demonstrated X" can be cross-referenced to the durable
  artifacts rather than memory.

### Negative

- N=4 is below threshold. The ADR ships in a qualified-validation
  state and stays qualified until N≥8 closes. Premature claims of
  full validation must be guarded against in retrospectives.
- Counter telemetry depends on a functioning OTEL pipeline. Hosts
  without otelcol-contrib reachable on `127.0.0.1:4317` produce
  no-op counter records (fail closed by design). Materiality data
  for those iterations is degraded; the protocol does not break,
  but the evidence build pauses for that iteration.
- The catch-locus distinction depends on auditor confidence-floor
  enforcement (ADR-0007 §Council roles §Anti-rubber-stamp
  hardening). If the auditor rubber-stamps below the floor, the
  `caught_by_llama` bucket undercounts and `escaped` overcounts.
  Mitigation: confidence floor is structural, not advisory;
  rubber-stamping is the failure mode the protocol is designed to
  catch.
- Severity attribution on `caught_by_drafter` requires the drafter
  to assign severity at flag-time. Drafter-side process discipline
  is the load-bearing surface.

### Neutral

- 0.2.17 evidence is recorded in W2/W3/W4 sealed archives plus this
  ADR; future iterations append. The protocol itself is stable
  across iterations — counter names, schema, and threshold
  definition are versioned with this ADR.
- Migration to a partial-tier auditor (qwen3.5:9b at 0.3.x) does
  not change the counter shape; only the model behind the
  `caught_by_llama` bucket changes. The bucket name remains
  `caught_by_llama` for continuity (the architecture-level seat
  name, not the model identity).

## Out of Scope

- **Cost-per-defect calculation.** The four buckets count defects;
  cost-per-defect requires multiplying by token-spend, wall-clock,
  or compute hours. That calculation is downstream of the catch
  buckets and lives in the Pillar 8 dashboard's cost telemetry, not
  in this ADR's protocol.
- **Cross-iteration aggregation logic.** Aggregating the four
  buckets across iterations to compute the threshold metrics (≥30%
  reduction, etc.) is a dashboard-rendering concern; the protocol
  defines the inputs, not the aggregation pipeline.
- **Auditor-as-defect telemetry.** When the auditor itself is the
  defect (false-positive flagging), the protocol does not have a
  bucket for it. The W2 false-positive on F-0.2.17-W1-003 is
  recorded in carry-forwards (F-0.2.17-W2-006) but does not
  decrement `caught_by_llama` retroactively. Sealed archives stay
  sealed.
- **Severity weighting.** The protocol counts defects with
  per-event severity attributes but does not weight the threshold
  by severity. A `cosmetic` defect counts as one increment; a
  `critical` defect counts as one increment. Severity-weighted
  threshold logic is post-0.3.x.

## Alternatives Considered

### Token-spend reduction as the primary metric

Measure orchestrator token-spend per iteration; declare the harness
materially better when token-spend drops.

**Rejected.** Token-spend is downstream of outcomes. A harness that
costs more tokens but produces structurally honest dispositions is
the goal; a harness that costs fewer tokens by skipping audits is
the failure mode. The four-bucket protocol measures outcomes
directly.

### Single defect-rate counter

Count all defects (without splitting by locus); declare improvement
when total count drops.

**Rejected.** Locus-blind counting hides whether improvements are
real or whether defects are escaping rather than being caught. The
catch-locus split is the architecture's load-bearing observation.

### N=3 threshold (faster validation cycle)

Lower the falsification threshold from N≥8 to N≥3 to validate the
architecture faster.

**Rejected.** N=3 is anecdote-adjacent; rejection thresholds at
small N produce false rejections at high rate. N≥8 is the lower
bound at which the threshold metrics are statistically informative
under the iteration-noise distribution. The qualified-validation
caveat exists precisely so the architecture is not over-claimed
during the accumulation window.

### Auditor self-grading

Have the auditor grade its own performance retrospectively, feeding
self-grades into the materiality protocol.

**Rejected.** Pillar 7 ("generation and evaluation are separate
roles") forbids self-grading. The drafter-side gap-net (catch by
drafter on the next planning turn) is the architecturally correct
way to surface what the auditor missed. Self-grading would collapse
the catch-locus distinction.

## Revisit Triggers

This ADR is amended (not necessarily replaced) when any of the
following become true:

1. **N≥8 evidence window closes.** The falsifiability threshold is
   exercised. If passed, the qualified-validation caveat is
   removed; if failed, the architecture's harness-as-IQ claim is
   revised in light of empirical evidence.

2. **A partial-tier auditor seat lands (0.3.x).** The materiality
   protocol's bucket names stay; the model behind `caught_by_llama`
   changes. Amendment captures the seat-promotion event with
   sealed-archive cross-references.

3. **Severity weighting becomes load-bearing.** A future iteration
   surfaces a clear distinction between cosmetic and critical
   defects in catch-locus distribution; severity-weighted threshold
   amendment lands.

4. **A fifth bucket becomes necessary.** If the protocol's four
   buckets undercount a real-world catch locus (e.g., a "caught by
   triage" or "caught by user" surface), the bucket list is
   amended explicitly with the new counter name and wiring.

## References

- `artifacts/adrs/0007-containerization-architecture.md` §Council
  roles — auditor/drafter/triage/retrieval seats; the protocol
  measures their joint output.
- `artifacts/adrs/0009-secrets-broker-boundary.md` — boundary
  between container and host; orthogonal to materiality but cited
  for repo-resident architectural completeness.
- `artifacts/iterations/0.2.17/acceptance/W2.json` (sha256
  `4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`)
  D11 self-audit + D12 counter wiring.
- `artifacts/iterations/0.2.17/acceptance/W3.json` (sha256
  `9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`)
  D4 RAG-vs-non-RAG comparison.
- `artifacts/iterations/0.2.17/acceptance/W4.json` (sha256
  `949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`)
  D1 deterministic post-hoc filter; F-0.2.17-W2-006 +
  F-0.2.17-W3-001 closures.
- `artifacts/iterations/0.2.17/audit/W4.json` (sha256
  `9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`)
  llama self-audit verbatim disposition.
- `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
  F-0.2.17-W2-006, F-0.2.17-W3-001, F-0.2.17-W3-002 — the auditor
  capability-gap evidence chain.
- `src/aho/materiality.py` — counter primitives (W4-close sha
  `0ef021e3ee85d5c4390a7d40b19523d874ea84d6bdaeeb56b3f0a31fcac912b8`).
- `src/aho/materiality_baseline_extract.py` — baseline extraction
  (W4-close sha
  `0fecabc9c73de9148478517e03cc402d8145acd33951a33c7bd654bd76722030`).
- `artifacts/harness/base.md` §Pillar 7 ("generation and evaluation
  are separate roles") — binding constraint on the catch-locus
  distinction.
- `artifacts/harness/base.md` §Pillar 8 ("efficacy is measured in
  cost delta") — adjacent pillar; cost telemetry is separate from
  materiality but feeds the same dashboard surface.
