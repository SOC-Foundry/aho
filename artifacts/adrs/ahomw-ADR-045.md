# ADR-045: Discovery Iteration Formalization

**Status:** Accepted
**Date:** 2026-04-11
**Iteration of record:** 0.2.9 (W7 capture, 0.2.8 as empirical reference)
**Author:** Kyle Thompson (decisions), Claude Code (draft)
**Context surface:** aho methodology — iteration type taxonomy

---

## Context

aho iterations vary in shape. Some are remediation (0.2.4: fix the MCP fleet list, add verification harness). Some are feature (0.2.7: dashboard, coverage audit, orchestrator config). Some are discovery — the iteration's primary output is *finding out what's broken* rather than shipping a predetermined scope.

0.2.8 was the first iteration that ran explicitly as a discovery iteration: 14 workstreams (largest to date), theme "Discovery + exercise," and a scope that could not have been fully specified at W0 because the findings of each workstream informed the next. The design doc listed 7 open questions — more than any prior iteration — and the workstream count grew from 10 planned to 14 shipped because W1 (MCP utilization gap diagnosis) surfaced structural issues that spawned W2.5, W7, and W10 as reactive workstreams.

This pattern — "the iteration discovers the work as it goes" — is now common enough to formalize. Without formalization, discovery iterations look like scope drift or poor planning. With formalization, they are a recognized iteration type with their own constraints and success criteria.

---

## Decision

aho recognizes three iteration types. The type is declared in the design doc and determines the scope contract:

### 1. Remediation iteration

- **Shape:** narrow, predetermined scope. Every workstream is known at W0.
- **Success criteria:** all targeted defects fixed, regression tests added.
- **Scope contract:** immutable. Workstreams do not spawn mid-iteration.
- **Example:** 0.2.4 — MCP fleet corrected from 12 to 9, registry verification gate added.

### 2. Feature iteration

- **Shape:** broad but predetermined. Workstreams are known at W0; each delivers a planned capability.
- **Success criteria:** all planned capabilities shipped with tests and documentation.
- **Scope contract:** immutable. Mid-iteration findings become carry-forwards, not new workstreams.
- **Example:** 0.2.7 — dashboard, coverage audit, orchestrator config. All planned at W0, all shipped as designed.

### 3. Discovery iteration

- **Shape:** broad and adaptive. W0 establishes a direction and initial workstreams. Subsequent workstreams may spawn from findings.
- **Success criteria:** discoveries documented with reproduction paths, fixes shipped where feasible, carry-forwards captured for what requires a follow-up iteration.
- **Scope contract:** mutable within the iteration's theme. New workstreams are permitted if they arise from findings within the theme. The theme itself is immutable.
- **Example:** 0.2.8 — theme "MCP utilization, source-of-truth reconciliation, harness-watcher diagnosis." W1 found the MCP gap; W2.5 wired the servers; W7 built a postflight gate. None of W2.5, W7, or W10 existed in the original plan. All arose from the theme.

### When to use each type

| Signal | Type |
|---|---|
| Known bugs with reproduction paths | Remediation |
| Feature requests with clear acceptance criteria | Feature |
| "Something is wrong but we don't know what" | Discovery |
| Post-install on a new machine (unknown failure modes) | Discovery |
| Carry-forward list longer than 5 items across 2+ domains | Discovery |

---

## Per-workstream review as a sub-mode

Discovery iterations SHOULD use per-workstream review cadence (ADR-044 Phase 2 applied at workstream granularity, not only at iteration close). This means:

1. Agent completes a workstream and halts with a handoff summary.
2. Kyle reviews findings before the next workstream starts.
3. Kyle may amend scope for subsequent workstreams based on findings.
4. The theme remains fixed; the workstream plan adapts.

Per-workstream review is optional for remediation and feature iterations (where the scope is known and stable) but SHOULD be default for discovery iterations. The cost is higher wall-clock time per iteration. The benefit is that discoveries compound — W1 findings inform W2 scope, which informs W3 scope — and this compounding is lost if all workstreams run unreviewed.

0.2.8 ran per-workstream review and inserted one reactive workstream (W2.5, MCP wiring) that did not exist in the original plan. Several planned workstreams (W7, W10, W11) also produced first-run catches, but these were planned workstreams with unexpected findings — not scope insertions. 0.2.9 continued per-workstream review for all 9 workstreams as a hybrid iteration (W0–W7 feature-shaped, W8–W9 discovery-shaped due to P3 clone's unknown failure modes). Kyle chose this deliberately: per-workstream review is the more conservative default, and the hybrid shape made it load-bearing.

---

## Relationship to ADR-044

ADR-044 describes the four-phase loop between iterations. ADR-045 describes iteration *types* that determine the scope contract within Phase 4 (W0 contract):

- **Remediation/Feature:** Phase 4 contract is immutable. Agent executes exactly what was planned.
- **Discovery:** Phase 4 contract establishes the theme and initial workstreams. The theme is immutable; the workstream plan is adaptive. Per-workstream review (Phase 2 applied intra-iteration) gates each adaptation.

ADR-045 does not modify ADR-044. It refines the scope contract semantics within Phase 4.

---

## Consequences

**Positive:**

- Discovery iterations no longer look like planning failures. They are a recognized pattern with explicit rules.
- The mutable-scope rule is bounded by the immutable-theme constraint, preventing true scope drift.
- Per-workstream review makes discovery iterations legible in real time — Kyle sees findings as they emerge, not only at close.
- The taxonomy is teachable: a new collaborator can be told "this is a discovery iteration, workstreams may spawn from findings, the theme is fixed" and operate correctly.

**Negative:**

- Discovery iterations are slower than feature iterations at the same workstream count because of per-workstream review overhead.
- The three-type taxonomy may be insufficient. Hybrid iterations (partly remediation, partly feature) are not explicitly addressed — they should use whichever type's scope contract is more conservative.
- Declaring the wrong type at W0 (e.g., calling a discovery a feature) produces either artificial carry-forwards (findings that should have been workstreams) or scope drift (reactive workstreams in a supposedly immutable plan).

**Mitigations:**

- The type is declared in the design doc header and visible to all agents. Incorrect typing surfaces during Phase 2 forensic review.
- Hybrid iterations default to the more conservative scope contract (feature → immutable workstream plan; if findings force scope change, Kyle explicitly re-declares as discovery).

---

## References

- ADR-044: Four-Phase Question-Driven Iteration Cadence — `artifacts/adrs/ahomw-ADR-044.md`
- 0.2.4 (remediation example) — `artifacts/iterations/0.2.4/`
- 0.2.7 (feature example) — `artifacts/iterations/0.2.7/`
- 0.2.8 (discovery example, 14 workstreams) — `artifacts/iterations/0.2.8/`
- 0.2.9 (hybrid example: feature W0–W7 + discovery W8–W9) — `artifacts/iterations/0.2.9/`
- Pillars 6, 10 — `artifacts/harness/base.md`

---

*ADR-045 — drafted during 0.2.9 W7 from the empirical record of 0.2.8 (first explicit discovery iteration). The three-type taxonomy existed in Kyle's working memory; this ADR makes it transmissible.*
