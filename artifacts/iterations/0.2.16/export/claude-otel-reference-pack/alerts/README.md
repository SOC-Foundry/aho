# Claude Code OTel - example alert rules

Two alert rule files for Prometheus-style alerting on Claude Code
OpenTelemetry metrics.

## Important - these rules are NOT live in this reference pack

The rules in this directory are **expressions only**. They have not been
evaluated against a running engine in the source deployment. To use them
you must:

1. Stand up an Alertmanager-compatible rule engine (Prometheus + Alertmanager,
   VictoriaMetrics' vmalert, Grafana managed alerting, or equivalent).
2. Configure a metric source that exposes the `claude_code.*` metric family -
   typically by adding a `prometheus` exporter to your OpenTelemetry collector
   and pointing your rule engine's scrape config at it.
3. Wire the engine's webhook receiver to your delivery endpoint (Telegram,
   Slack, PagerDuty, etc.). The `telegram_alerts.py` bridge module in the
   source repo demonstrates one such webhook receiver shape.
4. Recalibrate every threshold against your own session distributions - the
   numbers shipped here came from one specific deployment over a small sample
   window and are illustrative, not authoritative.

The source deployment that produced this pack is itself awaiting an engine
selection decision; rule evaluation against a live engine is a deferred
deliverable in that deployment's roadmap and is not represented in this
pack.

## Files

- `pillar-11-violations.yaml` - two rules (`Pillar11CommitViolation`,
  `Pillar11PullRequestViolation`) that fire when an agent-attributable
  `claude_code.commit.count` or `claude_code.pull_request.count` increment
  is observed within a one-minute window. Severity: critical. The "Pillar 11"
  naming is the source deployment's policy convention; rename freely to
  match your organisation's anti-agent-write policy.
- `anomaly-rules.yaml` - three anomaly rules:
  - `ClaudeAPIErrorSpike` - `rate(claude_code_api_error[5m]) > 1`
  - `ClaudeCostAnomaly` - `increase(claude_code_cost_usage[10m]) > 2.0`
  - `ToolDurationOutlier` - `histogram_quantile(0.99, ...bucket) > 2411 ms`

## Calibration

### `ClaudeAPIErrorSpike` threshold

The shipped expression is `rate(claude_code_api_error[5m]) > 1`, which
evaluates to "over 1 event/second sustained for 5 minutes" - roughly 300+
events over a 5-minute window. The originating plan document characterised
the rule as ">5 in 5m" in prose; the formal expression and the prose are
inconsistent. Both are preserved in source comments. Pick the form that
matches your operational tolerance:

- For a tight tolerance (operational paging on any sustained error stream):
  `increase(claude_code_api_error[5m]) > 5`
- For a higher-bar tolerance (only paging on near-outage rates):
  the shipped expression as-is.

### `ClaudeCostAnomaly` threshold

`> 2.0` USD per 10 minutes is appropriate for a single-developer Claude
Code workstation. Multiply by your seat count or scale by your typical
session intensity. Cost attribution is most useful when paired with a
per-session-attribute label that lets you isolate the spending workload.

### `ToolDurationOutlier` threshold

Calibrated baseline_p99 for the source deployment was 804 ms over 21
samples. Multiplied by 3 yields the shipped 2411 ms threshold. **This
sample size is small** - fewer than 100 samples means the p99 estimate
has high variance. Treat the shipped value as a placeholder and run your
own calibration against your own sessions. The calibration script is
at `probes/w3_baseline_calibration.py` in the source repository and is
re-runnable against any `logs.jsonl` produced by an OTel collector
configured per the reference pack.

### `ToolDurationOutlier` metric source

The rule's metric reference `claude_code_tool_result_duration_ms_bucket`
expects a Prometheus-style histogram. **Current Claude Code versions do
not emit this as a histogram metric** - `duration_ms` is recorded only
as an attribute on the `claude_code.tool_result` log event. To use this
rule against current Claude Code emission you must:

1. **Derive the histogram in your engine.** Loki + LogQL, VictoriaLogs +
   vmalert, or any log-to-metric pipeline can synthesise a histogram from
   the event stream's `duration_ms` attribute.
2. **Convert in the OTel collector.** A custom processor (or a future
   contrib processor) can translate the log attribute to a histogram
   metric before export.
3. **Replace the expression.** Substitute a non-histogram source - e.g.,
   a recording rule that tracks max-duration over window via the same
   log-derived series.

This is documented as a known limitation, not a defect of the reference
pack.
