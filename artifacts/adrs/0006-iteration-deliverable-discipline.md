# ADR 0006 — Iteration Deliverable + Graduation Criterion Discipline

**Status:** Accepted
**Date:** 2026-05-01
**Iteration of record:** aho 0.2.16 W4
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal — iteration-plan-doc structure;
binds every iteration plan from 0.2.17 onward.

---

## Context

aho's workstreams have crisp deliverables. Every workstream plan section in
`aho-plan-{iter}.md` lists files produced, acceptance gates, and a budget;
every workstream closes against an `acceptance/W{N}.json` archive whose shape
is harness-enforced.

aho's iterations have not. What an iteration delivers — what *exists* at
iteration close that did not exist at iteration start — has been emergent
across 0.2.x. The iteration's *theme* is captured in design and plan docs,
but the binary "did this iteration ship" question has no canonical artifact;
sign-off ticks five workstreams and the close command rolls forward.

Two consequences of that gap surfaced in 0.2.x:

1. **Iteration scope drifted mid-flight without a structural alarm.** 0.2.16
   originally scoped W4 to a Mercor export pack assembly. Mid-iteration the
   scope was deprioritized to ADRs and plan-outline work. That is a
   reasonable scope decision — but at the workstream level a comparable
   mid-flight scope change (a new file added to an in-progress workstream's
   deliverable list, say) would land as a hard meta-rule violation. At the
   iteration level there is no equivalent guardrail because there is no
   crisp iteration-level contract to violate.

2. **The retrospective inherits the emergent shape.** "What did 0.2.16 ship"
   has to be reconstructed by re-reading per-workstream summaries at
   close-out. Future iterations consult that retrospective and inherit a
   pattern of describing iteration deliverables narratively rather than as
   a single-paragraph contract.

This conflicts with aho's own governance thesis. The harness-as-IQ pillar
(2) states that the harness *is* the contract — and aho has applied that
discipline to workstream contracts but not to iteration contracts. Pillar 6
(transitions are durable) and pillar 8 (efficacy is measured in cost delta)
both presuppose that "did this iteration succeed" is a question with a
defined answer. Today the answer is constructed at close-out from
per-workstream evidence rather than asserted at plan time and verified at
close.

The richer-harness, smarter-behavior pattern says: when a meta-rule keeps
producing emergent rather than designed behavior, the fix is to lift the
contract one level. This ADR lifts the deliverable contract from workstream
to iteration.

## Decision

Every `aho-plan-{iter}.md` MUST open with two artifacts before the
workstream summary table:

### (1) Iteration deliverable paragraph

A single plain-language paragraph stating what exists at iteration close
that did not exist at iteration start. The paragraph is written at
plan-doc creation time (before W0), names concrete artifacts (files,
commands, dashboards, alert rules — whatever the iteration produces), and
is the canonical answer to "did this iteration ship."

The paragraph is a contract, not an aspiration. Workstream amendments do
not amend it. The paragraph can only be amended by the same hard meta-rule
exception that governs workstream-scope amendments — kyle-explicit, halt
the iteration, surface the change as a first-class scope decision.

### (2) Graduation criterion

A binary test that must pass for the iteration to be considered shipped.
Forms in order of preference:

1. **Runnable test.** A single command (or short script) that exits 0 when
   the iteration deliverable is met and non-zero otherwise. Preferred form
   when the deliverable is software.

2. **Observable artifact existence + content check.** A list of files that
   must exist and a short content assertion (regex, key presence, count
   range) for each. Acceptable form when the deliverable is documentation
   or design output.

3. **Manual verification checklist with acceptance evidence.** A numbered
   list of human-verifiable conditions, each with a named evidence artifact
   that records the verification. Form of last resort — used only when (1)
   and (2) genuinely do not apply.

The graduation criterion lives at the top of the plan doc immediately
after the deliverable paragraph. At iteration close, the drafter verifies
the criterion and records the verification in the retrospective. If the
criterion fails, the iteration does not close — it stays open until the
criterion passes or until the criterion itself is amended (same hard
meta-rule treatment as above).

### Drafter responsibility at iteration close

Before emitting the final `iteration_complete` event (or its post-ADR-0004
equivalent), the drafter:

1. Re-reads the iteration deliverable paragraph and graduation criterion
   from the plan doc.
2. Asserts each condition of the graduation criterion against current
   repo state.
3. Records the assertion (PASS/FAIL with evidence references) in the
   retrospective under a §Graduation criterion section.
4. If FAIL: halts close, surfaces to Kyle, does not advance.

Sign-off from Kyle remains Pillar 11 work — the drafter validates, Kyle
commits.

## Rationale

> Workstream scope amendments are a hard meta-rule violation. Iteration
> scope amendments — i.e., changing the iteration deliverable mid-iteration
> — are now the same class of violation.

aho's governance signal is consistent across scope levels or it is not
consistent at all. Workstream scope is fixed at workstream-start; that
discipline produced the bucket-by-bucket explicitness that 0.2.16's
workstreams shipped against. The same discipline at iteration boundary
produces an iteration plan doc that asserts what the iteration is *for*
in a single paragraph. Future iteration owners (and future Kyles auditing
in retrospect) read the deliverable paragraph and get the contract; they
do not have to re-derive it from five workstream summaries.

The graduation criterion adds the binary "shipped" question. Today aho's
answer to "did 0.2.16 ship" is "five workstreams have audit_result ∈
{pass, pass_with_findings}". That is a workstream-level success aggregation,
not an iteration-level success assertion. With this ADR, "did 0.2.16
ship" is "the graduation criterion in `aho-plan-0.2.16.md` evaluates true"
— a single question with a single answer.

The runnable-test preference for the criterion mirrors the workstream
acceptance archive's preference for measured evidence over rhetorical
claim. A binary test is harder to fudge than a paragraph of prose. When
the deliverable is software, the test is the contract; when the
deliverable is documentation, the existence-and-content check approximates
the test.

## Consequences

### Positive

- Iterations gain a single-paragraph contract written at plan time, not
  reconstructed at close.
- "Did the iteration ship" becomes a binary question with a defined answer.
- The retrospective has a structurally-required §Graduation criterion
  section, which forces a measurement step that has been emergent in 0.2.x.
- Mid-iteration scope drift surfaces as a deliverable-paragraph amendment,
  which trips the same hard meta-rule that workstream-scope amendments
  trip. Drift becomes detectable at the iteration level.
- The Adversarial Authorship protocol (renamed in 0.2.17 W0 from
  "Pattern C") now has a corresponding pattern at the iteration
  level — drafter writes contract → drafter executes → drafter verifies →
  Kyle signs — paralleling the workstream protocol. Governance signal is
  consistent.
- 0.3.x and onward inherit a uniform iteration-plan-doc opening shape,
  which makes the iteration-bundle archive shape across phases more
  comparable.

### Negative

- Plan-doc creation cost increases. Drafting a deliverable paragraph and a
  graduation criterion at plan time requires more thought than emergent
  scope; the cost shows up at iteration-open rather than iteration-close.
  This is a feature (front-loaded clarity) but an increase nonetheless.
- Some iterations have genuinely exploratory scope where the deliverable
  is hard to specify in advance. The graduation criterion forms (1)–(3)
  cover most cases, but for an iteration whose entire purpose is "decide
  what to do next," the criterion may degrade to (3) and provide weaker
  signal than for an execution-focused iteration. Acceptable; flagged.
- Retroactive application is impossible for closed iterations. 0.2.x prior
  iterations stay narratively-described in their own retrospectives. The
  0.2.16 retrospective applies the discipline retroactively to *itself* —
  the deliverable paragraph and graduation criterion are written at
  retrospective time and the criterion is evaluated against repo state.

### Neutral

- The iteration-plan-doc template grows two top sections. Existing
  workstream summary tables are unchanged.
- The retrospective template grows a §Graduation criterion section. Other
  sections unchanged.
- ADR 0004's `aho iteration close --confirm` redesign is unaffected; the
  archive-reading commit path is the same. A future enhancement could
  surface graduation-criterion verification through the close command, but
  that is out of scope for this ADR.

## Examples

### Example 1 — 0.2.16 (retroactive)

**Iteration deliverable (retroactive):**

> At 0.2.16 close, Claude Code sessions in aho emit cost / token / event /
> trace signals to a managed otelcol-contrib pipeline; Pillar 11
> violations and four anomaly conditions have rule files ready for live
> wire-up; a per-workstream cost-and-token dashboard is rendering;
> distributed traces propagate W3C `TRACEPARENT` from Claude Code through
> `src/aho/pipeline/dispatcher.py` and `router.py` into Ollama leaf calls;
> three new aho-internal ADRs (0006 iteration discipline, 0007
> containerization, 0008 dispatcher missing-model) are recorded; the
> 0.2.17 plan and 0.3 phase plan are seeded.

**Graduation criterion (retroactive — form 2, observable artifact
existence + content check):**

```
1. .claude/settings.json env block contains CLAUDE_CODE_ENABLE_TELEMETRY=1,
   OTEL_METRICS_EXPORTER=otlp, OTEL_LOGS_EXPORTER=otlp, OTEL_TRACES_EXPORTER=otlp,
   CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1, and OTEL_RESOURCE_ATTRIBUTES with
   aho.iteration / aho.workstream / aho.role keys.
2. ~/.local/share/aho/{logs,metrics,traces}/*.jsonl all show non-zero size and
   contain at least one record tagged aho.iteration=0.2.16.
3. artifacts/iterations/0.2.16/dashboards/pillar-8-cost-tokens.json exists
   with five panels (cost-by-workstream, tokens-by-type, cost-per-1K,
   active-time, cost-delta).
4. artifacts/iterations/0.2.16/alerts/{pillar-11-violations,anomaly-rules}.yaml
   both exist with five rules total.
5. src/aho/pipeline/dispatcher.py and src/aho/pipeline/router.py both read
   TRACEPARENT and emit child spans (verified by tests/test_*_traceparent.py
   passing).
6. artifacts/adrs/{0006,0007,0008}-*.md exist.
7. artifacts/iterations/0.2.17/aho-plan-0.2.17.md exists with iteration
   deliverable paragraph + graduation criterion at top.
8. artifacts/iterations/0.3-phase-plan.md (or repo-convention equivalent)
   exists with phase-deliverable paragraph + per-iteration outline.
```

The 0.2.16 retrospective evaluates each numbered condition against current
repo state and records PASS/FAIL.

### Example 2 — 0.2.17 (proposed, drafted in 0.2.16 W4)

**Iteration deliverable (proposed):**

> At 0.2.17 close, aho ships as a base-tier signed container image in a
> registry, pullable and runnable on NZXTcos as a base-tier host.
> install.fish detects GPU capacity and pulls the appropriate model bundle
> at install time. The harness runs end-to-end inside the container — `aho`
> CLI works, telemetry pipelines emit, dashboard renders, dispatcher routes
> correctly per ADR 0008's hybrid-mode dispatch behavior.

**Graduation criterion (proposed — form 1, runnable test):**

```
podman pull <registry>/aho:0.2.17-base \
  && podman run --rm aho:0.2.17-base aho --version \
  && podman run --rm \
       -e AHO_DISPATCH_HYBRID_MODE=1 \
       aho:0.2.17-base aho dispatch --family nemotron --prompt 'hello' \
  && exit 0
```

Exit 0 on a clean working directory on NZXTcos = iteration shipped.

### Example 3 — 0.3.1 (proposed, drafted in 0.2.16 W4)

**Iteration deliverable (proposed):**

> At 0.3.1 close, the partial-tier aho container image exists in the
> registry, pulls cleanly on tsP3 (16GB-class discrete GPU host),
> install.fish detects partial tier and pulls the partial model bundle
> (base + qwen3.5:9b + GLM-4.6V-Flash-9B), and a paired-Auditor cascade
> runs end-to-end inside the container with full Jaeger trace.

**Graduation criterion (proposed — form 1, runnable test):**

```
On tsP3:
podman pull <registry>/aho:0.3.1-partial \
  && podman run --rm aho:0.3.1-partial aho --version \
  && podman run --rm aho:0.3.1-partial \
       aho cascade run --scenario nosql-paired-auditor \
  && exit 0
```

Exit 0 on tsP3 = iteration shipped. Trace artifact is captured by the
cascade command; existence-check is folded into the runner's exit code.

## Out of Scope

- **Specific graduation-criterion templates per iteration class**
  (substrate iteration, design iteration, integration iteration, etc.).
  The three forms above (runnable test / artifact-existence-and-content /
  manual checklist) cover the spectrum; per-class templates are a future
  refinement once 0.2.17 / 0.3.1 generate enough examples to extract a
  pattern. Candidate ADR for late 0.3 or 0.4.

- **Automation of graduation-criterion verification.** Today the drafter
  reads the criterion and asserts it manually at retrospective time. A
  future enhancement is `aho iteration graduate --check` that parses a
  structured graduation block and runs the test. Out of scope for this
  ADR; potentially folds into ADR 0004's close-command redesign as that
  ADR's implementation lands.

- **Integration with `aho iteration` CLI.** ADR 0004 covers the
  close-command redesign; this ADR does not amend it. Once 0004's
  implementation lands, a follow-on ADR can extend the close path to
  read and assert the graduation criterion. Pre-emptive integration here
  would couple two design decisions that should stay independent until
  both have landed in code.

- **Phase-level deliverable paragraphs and graduation criteria.** This
  ADR governs iteration plan docs. Phase plans (e.g., the 0.3 phase plan
  drafted in W4) inherit a similar discipline informally — the 0.3
  phase plan opens with a phase-deliverable paragraph by analogy — but
  this ADR does not formally bind phase plans. Candidate for a separate
  ADR if Phase 0 close (whenever 0.x → 1.0 transitions) reveals the
  same emergent-vs-designed gap at the phase level.

- **Backfilling deliverable paragraphs and criteria onto closed
  iterations.** 0.1.x and 0.2.x prior iterations stay as they are. Their
  retrospectives are durable as written. Backfill would consume drafter
  time on closed work for limited gain; not adopted.

## Alternatives Considered

### Treat workstream acceptance aggregate as the iteration contract

Today's de facto position: an iteration ships when all workstreams have
`audit_result ∈ {pass, pass_with_findings}`.

**Rejected.** Workstream success aggregation is structurally weaker than
iteration deliverable assertion. Five workstreams can each pass against
their individual gates while the iteration as a whole has drifted from
its original purpose; aggregating successes does not detect drift. Also,
"did the iteration ship" should be answerable without reading five
workstream archives.

### Require a deliverable paragraph but not a graduation criterion

Optional graduation criterion would be a softer enforcement.

**Rejected.** Without a binary test, the deliverable paragraph drifts
into aspiration. The graduation criterion is the part that distinguishes
contract from prose. Form (3) (manual checklist) accommodates iterations
where forms (1) and (2) genuinely do not apply, so the requirement is
not infeasibly strict.

### Require the criterion to be runnable (form 1) only

Strictest version: every iteration must have a runnable test.

**Rejected.** Documentation- or design-heavy iterations (this iteration,
arguably) cannot reduce their deliverable to a single runnable test
without contortion. Forcing form 1 in those cases produces synthetic
tests that pass trivially and provide weak signal. Form 2 with explicit
content-check assertions is honestly stronger for those iterations.

### Put the deliverable + criterion in the design doc, not the plan doc

`aho-design-{iter}.md` already opens with §Charter — argued the
deliverable and criterion belong there.

**Rejected.** §Charter is narrative-scoping; the deliverable paragraph
and graduation criterion are contract artifacts. Mixing them with
narrative produces a charter that is half prose and half assertion. The
plan doc is where workstream-level contracts live; the iteration-level
contract belongs alongside, not in the design's narrative section. The
charter can summarize them, but the contract location is the plan doc.

## Revisit Triggers

This ADR is superseded or amended when any of the following become true:

1. **Two iterations in a row produce graduation criteria of form 3
   (manual checklist) without a forcing reason.** Signal that the form-1
   / form-2 framework is too restrictive for aho's actual iteration mix
   and the framework needs revision.

2. **A future ADR extends `aho iteration close --confirm` to verify the
   graduation criterion programmatically.** That ADR likely amends this
   one to formalize the criterion's machine-readable shape.

3. **An iteration is forced open (graduation criterion fails) for more
   than two close-attempts.** Signal that the criterion shape is wrong
   for that iteration class — either it is encoding aspirations the
   iteration cannot deliver, or the iteration is genuinely failing.
   Either way, the experience generates a refinement.

## References

- `artifacts/harness/base.md` §The Eleven Pillars — pillar 2 (harness is
  the contract), pillar 6 (transitions are durable), pillar 8 (efficacy
  in cost delta).
- `artifacts/harness/adversarial-authorship-protocol.md` — workstream-level
  analog of the discipline this ADR lifts to iteration. (Renamed from
  `pattern-c-protocol.md` in 0.2.17 W0.)
- `artifacts/adrs/0004-iteration-close-confirm-redesign.md` — the close
  command redesign that a future ADR may couple with this one.
- `artifacts/iterations/0.2.16/aho-plan-0.2.16.md` — example of an
  iteration plan doc *without* the discipline (pre-this-ADR shape).
- `artifacts/iterations/0.2.17/aho-plan-0.2.17.md` — first iteration
  plan doc *with* the discipline (post-this-ADR shape; drafted in
  0.2.16 W4 alongside this ADR).
- `artifacts/iterations/0.2.16/retrospective-0.2.16.md` §Graduation
  criterion — first retroactive application; drafted in 0.2.16 W4
  alongside this ADR.
