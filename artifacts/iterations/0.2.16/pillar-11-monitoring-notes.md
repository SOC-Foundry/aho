# Pillar 11 monitoring notes — 0.2.16 W3

Rule rationale, calibration math, deferred verification, and surfaced plan
inconsistencies for the W3 alert rule files.

Companion artifacts:
- `alerts/pillar-11-violations.yaml` — rules 1, 2 (Pillar 11 hard policy)
- `alerts/anomaly-rules.yaml` — rules 3, 4, 5 (anomaly detection)
- `probes/w3_baseline_calibration.py` — re-runnable calibration script
- `src/aho/alerts/telegram_alerts.py` — webhook → dedicated Telegram bridge

## Status banner

W3 ships rule files, bridge code, mocked unit tests, and a calibrated
baseline value. **Live engine evaluation is deferred** — the reduced-scope
Option 4 disposition recorded at the top of this iteration. No alert engine
is yet running on the host and the OTel collector has no exporter path that
could feed one (file + Jaeger only). Standing up Prometheus + Alertmanager
on a workstation as throwaway infrastructure ahead of the future-state
managed-services architecture was deemed out of scope; engine selection is
a non-trivial design decision deferred to 0.2.17 or 0.3 paired with a
dedicated ADR.

## Rule rationale

### Rule 1 — `Pillar11CommitViolation` (severity: critical)

**Expression:** `increase(claude_code_commit_count[1m]) > 0`

**Why:** Pillar 11 forbids agent-side git operations absolutely. The aho
harness has historically treated this as a convention; 0.2.16 makes it a
monitored invariant. Any non-zero increment in the `claude_code.commit.count`
counter over any one-minute window is a violation candidate. The rule fires
immediately (`for: 0m`) — there is no acceptable sustained-volume threshold
because the acceptable volume is zero.

The synthetic test (W3 bucket 5, deferred) was to emit a single counter
increment via probe and verify the rule fires + the bridge delivers within
60 seconds. Without an engine, the test cannot run; the deferral is
documented under §"Deferred verification" below.

### Rule 2 — `Pillar11PullRequestViolation` (severity: critical)

**Expression:** `increase(claude_code_pull_request_count[1m]) > 0`

**Why:** Same Pillar 11 absolute. PR creation is a strictly forbidden agent
operation regardless of whether it is paired with a commit. Rule structure
mirrors rule 1 exactly — one minute of evaluation, immediate firing.

### Rule 3 — `ClaudeAPIErrorSpike` (severity: important)

**Expression:** `rate(claude_code_api_error[5m]) > 1` (sustained for 5m)

**Why:** Sustained API errors are signal of upstream provider instability,
local credential/network failure, or runaway retry storm. Important rather
than critical because the operational response is "investigate within the
hour," not "page someone immediately."

See §"Plan inconsistencies" below for the formal expression vs prose
mismatch and the disposition recommendation.

### Rule 4 — `ClaudeCostAnomaly` (severity: important)

**Expression:** `increase(claude_code_cost_usage[10m]) > 2.0`

**Why:** Pillar 8 cost attribution invariant. The aho-internal cost ceiling
for a single workstream is ~$1.00/iteration in routine operation; $2.00
spent in 10 minutes signals a runaway loop, context-window blowout, or an
unattended automation. Threshold is per-host, not per-tenant — multi-tenant
deployments need additional aho.workstream / tenant labels in the rule
expression.

### Rule 5 — `ToolDurationOutlier` (severity: info)

**Expression:**
`histogram_quantile(0.99, sum by (le) (rate(claude_code_tool_result_duration_ms_bucket[5m]))) > 2411`

**Why:** Tool execution slow-paths are a leading indicator of subprocess
hangs, MCP server failures, network slowness on tool-invoked APIs, or a
misbehaving custom hook. Threshold is `baseline_p99 × 3` per the plan brief.
Severity is info — this is a "look at it eventually" signal, not a page.

See §"Plan inconsistencies" below for the metric-vs-event source caveat.

## Baseline calibration (rule 5)

**Sample window:** logs.jsonl events where `aho.workstream` resource
attribute ∈ {W1, W2}, body string `claude_code.tool_result`, attribute
`duration_ms`.

**Time range surveyed:** 2026-04-30 17:35:14 UTC → 2026-05-01 03:40:07 UTC
(spans the second half of W2 only; W1 absent — see below).

**Sample count:** 21 events. All from W2. **W1 absent from on-disk logs**:
the OTel file exporter wasn't yet writing during W1, so no W1 records exist
in `~/.local/share/aho/logs/logs.jsonl`. The calibration is therefore W2-only
in practice despite the plan-prescribed `W1+W2` window.

**Distribution observed:**

| stat   | duration_ms |
| ------ | ----------- |
| min    | 5           |
| p50    | 25          |
| p95    | 310         |
| **p99** | **804**    |
| p99.9  | 915         |
| max    | 927         |
| mean   | 104         |

**Threshold:** `baseline_p99 × 3 = 804 × 3 = 2411 ms`. Substituted into
`alerts/anomaly-rules.yaml` rule 5 in place of the `TODO_BASELINE_P99_MS`
sentinel.

**Sample-size honesty.** 21 samples is thin for a p99 estimate. The
statistical interpretation: at n=21, the p99 from the empirical CDF is
heavily influenced by the single longest observation (max = 927 ms in this
window). Linear-interpolation p99 between the 20th and 21st samples produced
803.6 ms; the true population p99 could plausibly be anywhere in a wide
range. Treat 2411 ms as a starting threshold, not a final one. Re-running
the calibration probe periodically as the metric corpus grows is the
correct discipline.

**Comparison run (informational, not used).** Re-running the probe with
`--workstreams W1,W2,W3` to include this W3 session's samples (n=93) yielded
p99 = 4748 ms and threshold = 14244 ms. The W3 session had longer-running
tool calls (deeper Read / Bash / find invocations on this large-context
workstream); including W3 biases the baseline toward this session's tool
mix. The W1+W2 canonical value (2411 ms) is what shipped, per the plan
brief's exact instruction. Both runs are reproducible from the probe.

**Probe re-runnability.** `probes/w3_baseline_calibration.py` accepts a
custom logs path, workstream filter, and multiplier:

```sh
python3 artifacts/iterations/0.2.16/probes/w3_baseline_calibration.py \
    --workstreams W1,W2 \
    --multiplier 3.0
```

Output includes time range, sample count, full distribution, and the
substitution value. Same pattern as W2's end-to-end probe — retained for
audit reproducibility.

## Deferred verification

The following W3 deliverables were deferred under Option 4 reduced scope.
Each is registered as a carry-forward in `acceptance/W3.json`. None is a
W3 failure — each is a deliberate decision to avoid silently absorbing
infrastructure scope that belongs in a future iteration.

### B5 — synthetic alert delivery test

The plan's bucket 5 specified a synthetic `claude_code.commit.count`
increment via probe → rule fire → webhook → Telegram delivery, with a
<60-second wall-clock target. None of the chain past "rule fire" can be
demonstrated without a live alert engine. Deferred to the iteration that
stands up the engine. The probe shape is documented in the W3 brief; a
hand-rolled OpenTelemetry-Python emitter targeting `localhost:4317` with
delta-temporality counter is the path of least resistance when the engine
is in place.

### Engine selection

Standing up Prometheus + Alertmanager on a workstation is throwaway work
given the future-state architecture places metrics infrastructure in
Tier 3 managed services. Doing it as part of W3 would commit aho to a
local-stack convention that it does not intend to keep. The engine
selection is a substantive design decision (Prometheus stack vs
VictoriaMetrics vs cloud-managed vs custom evaluator) and warrants a
dedicated ADR. ADR number is **not pre-allocated** — it will be the next
sequential aho-internal number from `artifacts/adrs/` at the time the
iteration owning that work begins (0006 is the next aho-native slot as of
this writing, but pre-allocation is forbidden per CLAUDE.md cross-project
contamination vigilance).

### Bridge live wire-up

`src/aho/alerts/telegram_alerts.py` ships with `BridgeHandler` /
`serve(port=9095)` plumbing but no systemd user unit, no engine receiver
config, and no live secret pair. Once the engine is selected, the
wire-up shape is:

1. Define a webhook receiver in the engine's config pointing at
   `http://127.0.0.1:9095/`.
2. Create a `~/.config/systemd/user/aho-alerts-bridge.service` running
   `python -m aho.alerts.telegram_alerts --serve`.
3. Provision the dedicated Telegram secrets (next item).
4. Trigger a synthetic commit-count increment per B5 above and verify
   end-to-end delivery within the 60-second target.

### Dedicated alerts-channel secrets

`ahomw:telegram_alerts_bot_token` and `ahomw:telegram_alerts_chat_id` are
**Kyle-created, agent-read-only** per Pillar 11. No agent in W3 attempted
to write either secret. The bridge module's `_get_alert_creds()` raises
`AlertSecretMissingError` on absent secrets — the unit tests verify the
fail-loud behavior — so when Kyle eventually provisions the pair against
a dedicated `@aho_alerts_bot`, the bridge picks them up on next request
without code changes.

### Forward pointer to this section

This `pillar-11-monitoring-notes.md` §"Deferred verification" section is
itself a carry-forward item: it is the written record of what was deferred,
why, and what the future-iteration owner needs to do to complete the
deferred work. The acceptance archive references this section directly so
the audit trail is not "the work was deferred" but "the work was deferred
and the disposition is preserved at this exact path."

## Plan inconsistencies surfaced

Two material discrepancies between plan §W3 and the reality of the metrics
emission. Both are documented here for the audit; neither is silently
absorbed into the rule files.

### Inconsistency 1 — Rule 3 expression vs prose

Plan §W3 row 3 specifies:

> `rate(claude_code_api_error[5m]) > 1` (>5 in 5m)

The formal expression `rate > 1` evaluates to "over 1 event per second
sustained over 5 minutes" — roughly 300+ events in a 5-minute window. The
parenthetical "(>5 in 5m)" describes a much tighter threshold:
`increase(claude_code_api_error[5m]) > 5`. The two cannot both be true.

**Disposition:** the W3 brief instructed "match plan table exactly — do
not adjust thresholds for 'feel.'" The shipped rule uses the formal
expression verbatim (`rate > 1`). The parenthetical is preserved in
source comments and in the export-pack README so a downstream reader can
choose the form that matches their operational tolerance. Audit: confirm
which interpretation the plan author intended; correct the plan and
optionally re-evaluate the rule choice.

### Inconsistency 2 — Rule 5 metric does not exist

Plan §W3 row 5 specifies a histogram-quantile expression over the metric
`claude_code_tool_result_duration_ms_bucket`. Survey of all metric names
in `~/.local/share/aho/metrics/metrics.jsonl` (37-line file at calibration
time) produced this complete enumeration:

| count | metric                              |
| ----- | ----------------------------------- |
| 31    | `claude_code.active_time.total`     |
| 23    | `claude_code.cost.usage`            |
| 23    | `claude_code.token.usage`           |
| 10    | `claude_code.session.count`         |
| 7     | `claude_code.lines_of_code.count`   |
| 7     | `claude_code.code_edit_tool.decision` |

There is no `claude_code.tool_result.duration_ms` histogram metric in the
emission. The duration value lives only as a `duration_ms` attribute on
the `claude_code.tool_result` log event in `logs.jsonl`. Rule 5's metric
reference is therefore aspirational against the current Claude Code
version (2.1.123 per resource attrs).

**Disposition:** three options for engine wire-up time, documented in
`alerts/anomaly-rules.yaml` rule-5 comment block:

1. Derive the histogram in the engine via a log-to-metric recording rule
   (Loki + LogQL, VictoriaLogs + vmalert, or equivalent).
2. Convert in the OTel collector via a custom processor.
3. Rewrite the rule against a non-histogram source.

The calibration in §"Baseline calibration" sidesteps the problem by
computing p99 from the event attribute (the truth source) rather than the
non-existent histogram. The substituted threshold value (2411 ms) is
honest. The rule expression itself is not yet falsifiable until a metric
source is supplied.

## Event log integration

Per design doc §W3, alert deliveries also append to the canonical aho
event log. The bridge's `event_log_append()` delegates to
`aho.logger.log_event()` so the schema is identical to all other aho
events:

```json
{
  "timestamp": "...",
  "iteration": "0.2.16",
  "workstream_id": null,
  "event_type": "pillar_11_violation",
  "source_agent": "aho-alerts-bridge",
  "target": "telegram-alerts-channel",
  "action": "alert_delivery",
  "input_summary": "<alertname>",
  "output_summary": "<annotation summary, ≤200 chars>",
  "tokens": null,
  "latency_ms": null,
  "status": "success",
  "error": null,
  "gotcha_triggered": null
}
```

`event_type` is one of two values: `pillar_11_violation` (for
`Pillar11CommitViolation` and `Pillar11PullRequestViolation` alerts) or
`anomaly` (for the three anomaly rules). Classification is via
`aho.alerts.telegram_alerts.classify_event_type()`.

**Fail-loud invariant.** If the event log append fails for any reason
(disk full, parent directory not writable, etc.), the bridge surfaces an
`OSError` to the engine — the engine returns a 500 to the operator. Silent
swallowing is forbidden because alert delivery without an audit-log entry
is invisible to Pillar 11 enforcement. The `webhook_handler` ordering is
deliberate: Telegram first, then log. If Telegram fails, no log is written
and the engine retries; if log fails after Telegram succeeded, the failure
propagates and the operator knows the audit is broken even though the
human got the alert.

## Cross-project contamination check

This document was assembled from aho canonical references only. No
kjtcom or other-project terminology was reached for; "11 Pillars" is
verified against `artifacts/harness/base.md`. ADR numbers are not
pre-allocated — the engine-selection ADR will receive its number from
disk enumeration when it lands.
