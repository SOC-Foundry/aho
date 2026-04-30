# ADR 0003 — OTEL Scaffolding Posture

**Status:** Accepted
**Date:** 2026-04-21
**Iteration of record:** aho 0.2.16 W0
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal — Claude Code OTEL integration;
downstream reference pack inherits these choices with a documented privacy-
profile swap.

---

## Context

Claude Code (the CLI) ships first-class OpenTelemetry instrumentation. As of
2026-04-21 it emits three kinds of signals:

- **Metrics** — `claude_code.session.count`, `claude_code.cost.usage`,
  `claude_code.token.usage` (split by type: input / output / cacheRead /
  cacheCreation), `claude_code.active_time.total`,
  `claude_code.lines_of_code.count`, `claude_code.commit.count`,
  `claude_code.pull_request.count`.
- **Events (logs)** — `claude_code.user_prompt`, `claude_code.api_request`,
  `claude_code.api_error`, `claude_code.api_retries_exhausted`,
  `claude_code.tool_result`, `claude_code.tool_decision`,
  `claude_code.mcp_server_connection`.
- **Traces (beta)** — `claude_code.interaction` as semantic turn root span
  with API and tool spans as children (requires
  `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`).

The aho observability stack already runs two systemd user services:

- `aho-otel-collector.service` — otelcol-contrib listening OTLP gRPC on
  `127.0.0.1:4317` and OTLP HTTP on `127.0.0.1:4318`.
- `aho-jaeger.service` — Jaeger all-in-one (trace store and query UI) at
  `127.0.0.1:14317` (OTLP gRPC) and `127.0.0.1:16686` (UI).

W0 scope is metrics + events only. Traces are W2 (flip
`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` and `OTEL_TRACES_EXPORTER=otlp` when
the W2 trace-integration work lands; also add `TRACEPARENT` propagation in
`src/aho/pipeline/dispatcher.py` and `router.py`).

## Decision

Enable Claude Code telemetry via managed settings in
`.claude/settings.json`. Route everything through the existing collector. Use
the collector's **file exporter** as the verification surface for W0 signals
because Jaeger is a trace store and cannot ingest metrics or logs —
Bucket 3 shipped `file/metrics` and `file/logs` pipeline exporters
explicitly for this purpose.

### Managed env block

```
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_LOG_USER_PROMPTS=1
OTEL_LOG_TOOL_CONTENT=1
OTEL_LOG_TOOL_DETAILS=1
OTEL_LOG_RAW_API_BODIES=file:/home/kthompson/.local/share/aho/api-bodies/
OTEL_METRICS_INCLUDE_SESSION_ID=false
OTEL_RESOURCE_ATTRIBUTES=service.name=claude-code,aho.iteration=0.2.16,aho.workstream=W0,aho.role=drafter
```

`OTEL_TRACES_EXPORTER` is **intentionally unset** in W0. Setting it would
emit traces that Jaeger would accept but that the W2 parent-child spans from
aho dispatcher/router have not been wired for — capturing partial traces
now would produce a record that doesn't match what the trace-integration
workstream is planning. Deferred to W2.

### Resource-attr taxonomy

Three aho-scoped attributes are set on every emitted signal:

- `aho.iteration` — phase.iteration label (`0.2.16`), frozen per iteration.
- `aho.workstream` — `W{N}`, reset at workstream boundary.
- `aho.role` — `drafter` for Claude Code; `auditor` for Gemini CLI when
  Gemini grows OTEL support (currently none — see ADR 0004 asymmetry when
  that ADR lands in W2).

Values are set **literally** in the env block. `${AHO_ITERATION}` / `${AHO_WORKSTREAM}`
shell-expansion style was considered but not adopted for W0 because Claude
Code's settings.json env-value expansion behavior is unverified; literal
values are 100% reliable at the cost of manual update at each
iteration/workstream boundary. Acceptable trade-off for W0; candidate for
automation in a later iteration.

### Capture surface

| Signal class | Examples | Backend in W0 |
|---|---|---|
| Per-session metrics | `session.count`, `cost.usage`, `token.usage` (4-way split), `active_time.total`, `lines_of_code.count`, `commit.count` (Pillar 11), `pull_request.count` (Pillar 11) | Collector file exporter → `~/.local/share/aho/metrics/metrics.jsonl` |
| Per-turn events | `user_prompt` (with `prompt.id` correlation UUID v4), `api_request` per API call, `tool_result`, `tool_decision`, `api_error`, `api_retries_exhausted`, `mcp_server_connection` | Collector file exporter → `~/.local/share/aho/logs/logs.jsonl` |
| Full request + response bodies | N/A — bodies dumped to disk by Claude Code itself | `~/.local/share/aho/api-bodies/` (via `OTEL_LOG_RAW_API_BODIES=file:...`); events link via `body_ref` pointer |
| Traces | Deferred to W2 | (none — `OTEL_TRACES_EXPORTER` unset) |

### Turn reconstruction

**W0 (logs-correlated turn view):** filter `logs.jsonl` by a single `prompt.id`
value to get the user prompt + every API call + every tool invocation +
every tool-use decision + any API error or retry-exhaustion that fired in
that turn.

**W2+ (trace-native turn view):** with traces beta enabled,
`claude_code.interaction` becomes the semantic-turn root span and the API
and tool spans hang off it as children. Filter by `trace_id` in Jaeger.
Prefer the trace view when W2 is live; W0's logs view is the fallback.

### Privacy posture

All `OTEL_LOG_*` flags are enabled for **aho-internal** comprehensive
logging. This is the most permissive capture surface and is appropriate for
a single-operator research harness. The Mercor-exportable reference pack
ships three profiles so external consumers can pick based on data
sensitivity:

- **minimal** — `OTEL_LOG_USER_PROMPTS=0`, `OTEL_LOG_TOOL_CONTENT=0`,
  `OTEL_LOG_TOOL_DETAILS=0`, no `OTEL_LOG_RAW_API_BODIES`. Captures
  metadata-only metrics and event envelopes.
- **standard** — `OTEL_LOG_USER_PROMPTS=1`, `OTEL_LOG_TOOL_DETAILS=1`,
  `OTEL_LOG_TOOL_CONTENT=0`. Enough to reconstruct turns and diagnose
  failures without tool-body payloads.
- **full** — aho's posture. All flags on, raw bodies to disk. Maximum
  diagnostic surface; assumes operator controls the capture path.

The profile selection belongs to the deploying operator, not the harness.

### Cardinality posture

`OTEL_METRICS_INCLUDE_SESSION_ID=false` bounds time-series cardinality on
metrics — per-session IDs would explode the metric label space. Session ID
remains available on **events**, where cardinality bounds do not apply
(events are individual records, not aggregated time series).

### Known limitations

1. **Claude's extended-thinking content is redacted at the Claude Code
   layer before OTEL export**, regardless of any flag. Per documentation,
   the native redaction is unconditional. If aho-internal thinking capture
   becomes a requirement, the correct path is an upstream feature request
   to Anthropic — not a downstream engineering workaround.

2. **Semantic turn structure as a first-class `claude_code.interaction`
   root span exists only in traces (W2).** In W0, turn reconstruction is
   `prompt.id`-correlated across the logs stream. Once W2 lands, the
   trace-native view becomes the canonical turn reconstruction surface.

3. **Gemini CLI has no OTEL equivalent.** Audit cost, tokens, and span
   timings are not captured on the auditor side. Documented as its own
   ADR in W2 (number determined at W2 execution time). Consumers of the
   export pack should expect the asymmetry; half-measure timing wrappers
   are not shipped.

### Carry-forward obligations

- **Log rotation for `~/.local/share/aho/api-bodies/`.** Unbounded file
  growth in a long-running environment. Target: W4 close or 0.2.17
  hygiene workstream. Candidate: `logrotate.d` drop-in file sized at
  daily-rotate / 14-day-retain.

- **Literal resource-attr values need manual bump at iteration / workstream
  boundaries.** Acceptable at W0; candidate for `AHO_ITERATION` /
  `AHO_WORKSTREAM` env-ref expansion in a later iteration once the
  settings.json expansion behavior is empirically verified.

- **Collector OTLP alias deprecation warning.** `"otlp" alias is deprecated;
  use "otlp_grpc" instead` — otelcol-contrib v0.149.0 notice on the
  `otlp/jaeger` exporter. Cosmetic until removal; rename to `otlp_grpc/jaeger`
  at next collector config touch.

## Consequences

### Positive

- W0 emits real signals to the collector with correct `aho.*` resource
  attrs. Downstream workstreams (W1 dashboard, W2 traces, W3 alerts) build
  on a verified capture surface.

- Full per-turn reconstruction is possible from logs alone (W0) and
  improves with traces (W2+).

- Cost attribution per workstream becomes Pillar 8 ground truth —
  estimates from parsed event logs are retired.

- Pillar 11 becomes monitored: `claude_code.commit.count` and
  `claude_code.pull_request.count` feed anomaly rules in W3. The
  convention-is-now-detection posture is measurable.

### Negative

- File growth under `~/.local/share/aho/api-bodies/` — addressed by the
  rotation carry-forward.

- Sensitive prompt / tool-content payloads live on local disk. Access
  control is filesystem-level; any multi-user deployment must revisit.

- Literal resource-attr values in settings.json are maintenance cost.

### Neutral

- The `file` exporter is additive to the existing `otlp/jaeger` exporter on
  the traces pipeline; Jaeger continues to receive traces when W2 ships.

- Metrics and logs pipelines are purely local (file-only in W0); adding a
  Prometheus remote-write or another logs backend is a one-line config
  change in a later iteration.

## Alternatives considered

- **Jaeger as W0 verification surface.** Rejected: Jaeger's OTLP receiver
  accepts traces; it does not ingest metrics or logs. W0 emits only metrics
  and logs (traces deferred to W2), so verifying in Jaeger is physically
  impossible. The plan doc and CLAUDE.md used "Jaeger" as shorthand for
  "the observability stack"; this W0 work makes the distinction explicit
  and updates the language in the carry-to-retro so future iteration docs
  use "collector pipeline output" for W0-scope signals and reserve "Jaeger"
  for W2+ trace verification.

- **Prometheus remote-write for metrics.** Not adopted in W0 because the
  file exporter is sufficient for the dashboard work in W1 (W1 can consume
  the collector's Prometheus exporter if it exists, or the file stream).
  Adding a Prometheus backend is a later decision.

- **Shell-expansion `${AHO_ITERATION}` in settings.json env values.** Not
  adopted: Claude Code's env-expansion behavior in settings.json was
  unverified. Literal values are safer and the maintenance cost is small.

- **Timing-wrapper for Gemini audits.** Rejected per W2-pending ADR.
  Partial observability that looks like coverage it isn't is worse than
  honest asymmetry.

## References

- `.claude/settings.json` — managed env block in effect.
- `~/.config/aho/otel-collector.yaml` — collector pipelines (traces +
  metrics + logs).
- `artifacts/iterations/0.2.16/otel-scaffold-notes.md` — W0 implementation
  notes, substrate state, pipeline verification evidence, deviations from
  plan phrasing, carry-to-retro items.
- `artifacts/iterations/0.2.16/aho-design-0.2.16.md` — iteration scope.
- 0.2.15 W3 ADR 0002 (Nemoclaw decision) — prior aho-internal ADR that
  established the numbering convention.
