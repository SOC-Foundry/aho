# ADR 0005 — Gemini CLI OTEL Asymmetry

**Status:** Accepted
**Date:** 2026-04-23
**Iteration of record:** aho 0.2.16 W2
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal — distributed tracing posture;
downstream reference pack consumers inherit the same asymmetry and should
plan around it.

---

## Context

W2 wires `TRACEPARENT` propagation through `src/aho/pipeline/dispatcher.py`
and `src/aho/pipeline/router.py` so that Claude Code (drafter) sessions
produce end-to-end traces: Claude Code session → tool span → bash
subprocess → `aho.dispatch.{family}` span → `aho.route.classify` span →
(Ollama, uninstrumented leaf).

Under Pattern C (modified), Gemini CLI is the **auditor** role. For every
workstream, Claude drafts, then Gemini audits, then Kyle signs. The audit
run is a substantive slice of the total iteration cost and latency.

As of 2026-04-23, **Gemini CLI has no first-class OpenTelemetry support.**
Specifically:

- No equivalent of `CLAUDE_CODE_ENABLE_TELEMETRY=1`. No `OTEL_*` env
  contract. No OTLP exporter.
- No documented span emission. No documented event log. No documented
  metric stream.
- No `TRACEPARENT` propagation from the parent process. A bash subprocess
  that runs `gemini` carries `TRACEPARENT` in the env but nothing in the
  Gemini process consumes it.
- No public Anthropic-style cost/token metric schema. Cost is reported at
  the end of a session in the CLI's own summary format, not as OTLP
  metrics.

Harness-watcher wraps Gemini invocations today and records wall-clock
start/end into `aho_event_log.jsonl` with `source_agent=gemini-cli`. That
captures *when* the audit ran and *how long* — nothing about model-level
cost, token count, or trace context.

## Decision

**Accept the asymmetry.** Document it explicitly. Ship no timing-wrapper
half-measures.

Specifically:

1. **No instrumentation shims.** The aho harness does **not** wrap the
   Gemini CLI invocation in a local OTEL span that synthesizes tokens,
   cost, or trace linkage that Gemini did not emit.

2. **Harness-watcher event wrappers capture wall-clock only.** Existing
   `gemini_invocation_start` / `gemini_invocation_end` events in
   `aho_event_log.jsonl` stay as they are — a durable record of audit
   latency, nothing more. No synthetic span emission to OTLP on Gemini's
   behalf.

3. **Audit cost attribution remains drafter-only in the Pillar 8
   dashboard.** The dashboard panel for per-workstream cost reports what
   Claude Code spent drafting. Gemini audit cost is not represented. A
   separate static cost-per-audit estimate is documented in the
   retrospective, not plotted in the dashboard.

4. **Audit spans do not appear in Jaeger.** A workstream's Jaeger trace
   will show Claude's drafting work fully instrumented (session → tool →
   dispatch → route → ollama), and a separate *non-traced* Gemini audit
   step recorded only in the event log.

## Rationale

> Partial observability that looks like coverage it isn't is worse than
> clear documented asymmetry.

Concretely:

- A synthetic "gemini-invocation" span with wall-clock start/end and no
  token/cost attributes would appear in Jaeger alongside real aho spans
  and visually suggest a parity that doesn't exist. Dashboard panels that
  aggregate `aho.*` span durations would silently fold in Gemini's
  wall-clock without the cost context. Reference pack consumers
  inheriting the pattern would get shipped a lie.

- A half-measure "fake token count based on prompt length" or "cost
  estimate based on input bytes" compounds the same problem with
  fabricated numeric precision. A future reader would not be able to tell
  which metric points are measured versus estimated without reading the
  shim code.

- The reference pack audience (Mercor engagement and beyond) is explicitly
  evaluating Claude Code's OTEL story for production deployment.
  Pretending the end-to-end picture is symmetric when it isn't
  mis-represents the current state of the ecosystem and invites the same
  mistake downstream.

The aho pattern is: **measure ground truth or flag the gap.** This ADR
flags the gap.

## Consequences

### Positive

- Trace and metric consumers know exactly what's instrumented. No
  reasoning about whether a measurement is real or synthetic.

- The moment Google ships OTEL support in Gemini CLI (or an equivalent
  cost/event surface), this ADR is superseded by a new decision — not by
  retrofit of the harness output to match real data.

- The reference pack documents the boundary: `drafter=claude-code`
  attributes flow through the full OTLP stack; `auditor=gemini-cli`
  attributes are visible only in `aho_event_log.jsonl`. Downstream
  consumers decide what to do about the auditor side based on their own
  vendor.

### Negative

- **Pillar 8 cost attribution is incomplete** for Pattern C iterations.
  Audit cost is real money; not plotting it hides a real line item.
  Mitigation: retrospective ships a static per-iteration estimate
  (audit cost ≈ N × static-per-audit-usd); the W1 dashboard panel labels
  its scope as "drafter only" so the omission is explicit.

- **No audit latency visible in Jaeger.** An operator debugging "why did
  this workstream take 2 hours" will see Claude drafting for 45 minutes
  and a gap. They'll need to consult `aho_event_log.jsonl` to see the
  audit block. Annoying but explicit — no phantom span to mislead.

- **No `TRACEPARENT` continuity across the audit boundary.** If a future
  workstream involves an audit-triggered re-draft (drafter → audit →
  drafter), the two drafter spans will belong to separate traces because
  nothing is propagating trace context through the audit gap.

### Neutral

- The asymmetry is an ecosystem state, not a design flaw. aho's response
  is to surface it; vendor parity is not aho's job.

- Resource attribute `aho.role=auditor` is reserved in the schema but
  unused in emission. When Gemini ships OTEL, the attribute value waits
  for it. No schema change required.

## Alternatives Considered

### Wall-clock span wrapper

Wrap every Gemini invocation in a local Python-side OTEL span that records
start, end, wall-clock-duration. Attribute `aho.role=auditor`,
`aho.tool=gemini-cli`, no token/cost attrs.

**Rejected.** The span would appear in Jaeger under a real aho trace and
visually suggest parity with Claude's instrumented spans. A dashboard
panel querying `aho.duration_ms` across all aho-scope spans would silently
include Gemini's wall-clock, corrupting per-stage latency statistics.
Fixing that by filtering on the role attribute is fragile and relies on
every dashboard author remembering the filter. The non-emission version
of this decision is strictly safer.

### Prompt-length-based token estimate

Fabricate a `tokens_approximate = len(prompt) / 4` attribute on a wrapper
span and feed it into the Pillar 8 dashboard so audit cost is plotted.

**Rejected.** Fabricated numeric precision is worse than missing data. A
metric dashboard that says "audit cost was $0.23" when the number was
invented produces false confidence. Pillar 8's ground-truth contract
(`claude_code.cost.usage` is real, sourced from Anthropic's billed API
response) would be contaminated by values with an invisible
synthetic-vs-measured distinction.

### Stream Gemini CLI's own stderr/stdout to OTEL

Capture Gemini's end-of-session cost summary (which it does print) and
parse it into an OTEL event.

**Rejected for now.** Parsing a CLI's human-readable summary is a fragile
contract — Google can change the format at any time without breaking
their users and we'd silently lose the metric. If this becomes necessary,
the correct design is a pinned wrapper script with explicit format
version pinning and a failure mode when the format changes. Out of scope
for W2; candidate for a dedicated workstream if audit cost attribution
becomes load-bearing.

### File a vendor feature request

Not an alternative to *this* ADR — it's complementary. An upstream
feature request to Google for OTEL support in Gemini CLI is the right
escalation path. That action is operator-driven and not captured in code;
this ADR does not block on it.

## Revisit Triggers

This ADR is superseded when any of the following become true:

1. **Gemini CLI ships OTEL metrics/events/traces.** The new decision:
   enable `GEMINI_CLI_OTEL_EQUIVALENT=1` (or whatever the contract
   becomes), add collector pipeline for the new signals, remove the
   "audit = wall-clock only" language from the reference pack, and
   populate `aho.role=auditor` on real emitted signals.

2. **The auditor role migrates to a different tool that does speak
   OTEL.** Drop the Gemini-specific language; the asymmetry resolves.

3. **A second workstream adds OTEL-instrumented synthetic-auditor
   tooling where the audit is structurally not a vendor-CLI call.** New
   ADR covering that posture; this ADR stays valid for the legacy audit
   path.

## References

- `artifacts/iterations/0.2.16/aho-plan-0.2.16.md` §W2.7 — ADR task.
- `artifacts/iterations/0.2.16/aho-design-0.2.16.md` §W2 — design-level
  context for the asymmetry.
- `artifacts/iterations/0.2.16/trace-integration-notes.md` — W2
  implementation notes referencing this ADR from the Gemini asymmetry
  section.
- `artifacts/adrs/0003-otel-scaffolding-posture.md` §Known limitations
  (3) — W0 anticipated this ADR and pointed forward to W2.
- `.claude/settings.json` — drafter managed-settings env block (no
  parallel exists for auditor).
- `~/.local/share/aho/events/aho_event_log.jsonl` — durable audit wall-
  clock record; current ground truth for Gemini invocation timing.
