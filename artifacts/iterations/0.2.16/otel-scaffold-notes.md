# OTEL Scaffolding Notes — 0.2.16 W0

**Iteration:** 0.2.16
**Workstream:** W0 (Bucket 3 — OTEL scaffolding)
**Authoritative ADR:** `artifacts/adrs/0003-otel-scaffolding-posture.md`
**Authoritative settings:** `.claude/settings.json` (env block)
**Purpose:** Forensic record of what was found, what was changed, and what verification produced which evidence.

---

## §Substrate State Before W0

Before touching any configuration, the observed state of the aho observability stack on NZXTcos:

### Processes

| Service | Unit | State | Endpoint |
|---|---|---|---|
| otelcol-contrib | `aho-otel-collector.service` | active (running, 2d 5h uptime) | OTLP gRPC `:4317`, HTTP `:4318` |
| Jaeger all-in-one | `aho-jaeger.service` | active (running) | OTLP `:14317`/`:14318`, UI `:16686` |
| NemoClaw daemon | `aho-nemoclaw.service` | active | Unix socket |
| OpenClaw daemon | `aho-openclaw.service` | active | Unix socket |
| Dashboard | `aho-dashboard.service` | active | HTTP `:7800` |
| Telegram bridge | `aho-telegram.service` | active | — |
| Harness watcher | `aho-harness-watcher.service` | **activating (auto-restart)** | — |

### Issue 1 — Collector pipelines were traces-only

`~/.config/aho/otel-collector.yaml` (pre-W0) declared one pipeline: `traces`. Its OTLP receiver on `:4317` accepted all three signal classes, but metrics and logs had no pipeline to route them and were silently dropped. Bucket 3's env block sends `OTEL_METRICS_EXPORTER=otlp` and `OTEL_LOGS_EXPORTER=otlp` — those signals would have been accepted and dropped with no observability if the collector were left unchanged.

**Drift analysis:** this was drift from some earlier iteration. The file exporter under `traces.jsonl` was active (~9KB of historical traces), so the pipeline itself worked — it just never gained metrics + logs siblings when some earlier intent implied them.

### Issue 2 — Jaeger cannot verify W0-scope signals

CLAUDE.md §OTEL Environment and the original brief used "Jaeger" as shorthand for "the observability stack." In W0, `OTEL_TRACES_EXPORTER` is intentionally unset (W2 scope), so Claude Code emits metrics and logs only. Jaeger's OTLP receiver accepts traces but does not ingest metrics or logs — verifying W0 signals "in Jaeger" is physically impossible.

**Resolution:** verify against the collector's file-exporter output (`metrics.jsonl`, `logs.jsonl`). Documented in §Deviations below; carry-to-retro item added to update CLAUDE.md language.

### Issue 3 — `aho-harness-watcher.service` crash-looping

Journal evidence: systemd restart counter at **31,263** at the start of the W0 session. Traceback:

```
File ".../harness_agent.py", line 82, in watch
    proposal = self.propose_gotcha(event)
File ".../harness_agent.py", line 27, in propose_gotcha
    result = classify(...)
File ".../artifacts/nemotron_client.py", line 96, in _classify_impl
    raise NemotronParseError(...)
aho.artifacts.nemotron_client.NemotronParseError: Nemotron response '' does not match any category: ['gotcha', 'noise', 'feature']
```

Every 5–6s the service restarted, ran 1 event through classify, crashed, restarted. Measurable CPU waste over time (~491ms per crash cycle × 31,263 restarts ≈ 4.3 hours of wall CPU over the life of this loop).

Two root causes compound:
1. `harness_agent.py:27` uses the **legacy** `aho.artifacts.nemotron_client.classify` path, which the 0.2.15 W3 migration window deprecates for `aho.pipeline.router.classify_task`. Migration not yet done for harness_agent.
2. The classify call has no exception handling around it — any `NemotronParseError` (Nemotron returning empty content) kills the process. Defensive try/except is absent.

**Resolution (W0):** service **stopped** and **disabled** on Kyle's explicit approval (halts CPU waste); finding **F-W0-001** filed in the acceptance archive. Proper fix (migrate to router + defensive try/except) is out of the W0 item list and deferred.

---

## §What Shipped in W0 Bucket 3

### Collector config extended

`~/.config/aho/otel-collector.yaml` — backup written to `.bak-pre-0.2.16-w0`. New config (see the file; summary here):

- Added `file/metrics` exporter → `~/.local/share/aho/metrics/metrics.jsonl`
- Added `file/logs` exporter → `~/.local/share/aho/logs/logs.jsonl`
- Added `metrics` pipeline routing `otlp` receiver → `batch` processor → `file/metrics`
- Added `logs` pipeline routing `otlp` receiver → `batch` processor → `file/logs`
- Existing `traces` pipeline (→ `file` + `otlp/jaeger`) preserved unchanged

Output directories created: `~/.local/share/aho/metrics/`, `~/.local/share/aho/logs/`, `~/.local/share/aho/api-bodies/`.

Service restarted: `systemctl --user restart aho-otel-collector.service` — came back clean, all three pipelines initialized, receivers bound to `:4317` and `:4318`. One deprecation warning (`"otlp" alias deprecated; use "otlp_grpc"`) carried to retro for cosmetic cleanup.

### `.claude/settings.json` written

New file. Contents match ADR-0003 §Managed env block verbatim. `OTEL_TRACES_EXPORTER` intentionally unset (W2 scope). Literal resource-attr values — `aho.iteration=0.2.16`, `aho.workstream=W0`, `aho.role=drafter`.

### Pipeline verification — synthetic probe

Emitted a synthetic metric (`aho.w0.synthetic_probe_count`) and log (`"aho W0 pipeline verification marker"`) via the Python OTEL SDK (gRPC OTLP to `:4317`) with `aho.iteration=0.2.16`, `aho.workstream=W0`, `aho.role=drafter` resource attrs.

Both landed in their respective jsonl files within the batch timeout (~5s). Resource attrs preserved end-to-end. This proves the pipeline plumbing independently of Claude Code's SDK behavior.

### Pipeline verification — real Claude Code emission

Subsequent to `.claude/settings.json` write, this Claude Code session began emitting real signals to the collector. Sampled records in `metrics.jsonl` and `logs.jsonl`:

- Metrics: `claude_code.session.count`, `claude_code.cost.usage`, `claude_code.token.usage` — all carrying `service.name=claude-code`, `aho.iteration=0.2.16`, `aho.workstream=W0`, `aho.role=drafter`.
- Logs: `claude_code.api_request`, `claude_code.tool_result`, `claude_code.tool_decision`, `claude_code.mcp_server_connection` — same resource attrs.
- Log records carry `prompt.id` (UUID v4) and `session.id` attributes as documented — turn reconstruction via `prompt.id` works.

This is the gate that CLAUDE.md Pattern C step 2 demands: one emitted `claude_code.*` event visible with correct `aho.*` resource attrs before real work. ✓

### Observation — session_id cardinality flag did not suppress as expected

`OTEL_METRICS_INCLUDE_SESSION_ID=false` is set in the env block. `claude_code.cost.usage` and `claude_code.token.usage` data points were observed carrying `session.id` anyway, plus several user identity attributes (`user.email`, `user.id`, `user.account_id`, `user.account_uuid`, `organization.id`).

Possible causes:
- The env var is read at session start; settings.json was written mid-session, so this session's metric emitter may not have picked it up.
- Flag name may be documented differently than I understood.
- Flag may suppress a different attribute than expected.

**Not blocking for W0** — resource-attr verification succeeded. Files as **F-W0-003** (not critical) and carried forward for W1 dashboard to scrub or for flag-behavior diagnosis. The cardinality posture for `claude_code.*` metrics will be revisited in W1.

---

## §Deviations

### Deviation 1 — Verification surface

**Plan/brief text:** "Verify one claude_code.* event lands in Jaeger with aho.iteration=0.2.16 and aho.workstream=W0 resource attrs."

**Actual:** Verified against the collector's file-exporter output (`metrics.jsonl`, `logs.jsonl`), not Jaeger.

**Reason:** Jaeger's OTLP receiver accepts traces; it does not ingest metrics or logs. W0 emits only metrics and logs (traces deferred to W2, `OTEL_TRACES_EXPORTER` unset). Verifying in Jaeger is physically impossible at W0.

**Material impact:** None — the verification substance (one real `claude_code.*` signal with correct `aho.*` resource attrs) is identical; only the backend is different.

### Deviation 2 — Collector config extension

**Plan/brief text:** "Verify otelcol-contrib and jaeger systemd user services are running before writing config."

**Actual:** Services were running, but the collector config was traces-only. Extended the config with metrics and logs pipelines.

**Reason:** Without metrics/logs pipelines, Bucket 3's env-block signals would have had no routing path. Extension is scope-fitting because Bucket 3 has no verification path without it.

**Material impact:** +9 lines of YAML in `otel-collector.yaml`. Backup preserved at `.bak-pre-0.2.16-w0`. Collector restarted cleanly.

### Deviation 3 — Service management

**Plan/brief text:** no service-management action planned.

**Actual:** `aho-harness-watcher.service` stopped and disabled.

**Reason:** Crash-looping with 31,263 accumulated restarts, measurable CPU waste, no-handler on `NemotronParseError`. Kyle approved stop+disable. Masking failed (unit file exists); disable removes the wants-symlink so it will not auto-start on reboot.

**Material impact:** Harness gotcha/adr/feature proposals from the event log are not being generated until this is fixed. F-W0-001 filed with root cause and proposed fix (narrow plus migrate to router).

---

## §Carry to Retro (0.2.16 close)

- **Update CLAUDE.md §OTEL Environment wording** — use "collector pipeline output" (or similar) for W0-scope signal verification. Reserve "Jaeger" specifically for W2+ trace verification. The W0 verification-in-Jaeger wording was a categorical error (Jaeger is a trace store; it does not ingest metrics or logs), caught during W0 execution.
- **OTEL env-var expansion in settings.json.** Literal values used for `aho.iteration` / `aho.workstream` / `aho.role` in W0. Empirically verify whether Claude Code's settings.json env block supports `${VAR}` shell expansion; if yes, switch to dynamic values to eliminate manual iteration/workstream-boundary edits.
- **`"otlp" alias deprecation in otelcol-contrib v0.149.0.** Cosmetic warning — rename `otlp/jaeger` exporter to `otlp_grpc/jaeger` at the next collector-config touch.
- **Logrotate for `~/.local/share/aho/api-bodies/`.** Currently unbounded. Target W4 or 0.2.17 hygiene.
- **session.id cardinality flag behavior.** If `OTEL_METRICS_INCLUDE_SESSION_ID=false` does not suppress as W0 observation suggests, reconcile with Claude Code docs and either fix the env var name or update the ADR.

---

## §References

- `artifacts/adrs/0003-otel-scaffolding-posture.md` — authoritative decision doc.
- `.claude/settings.json` — env block.
- `~/.config/aho/otel-collector.yaml` — pipelines.
- `~/.config/aho/otel-collector.yaml.bak-pre-0.2.16-w0` — pre-W0 backup.
- `~/.local/share/aho/metrics/metrics.jsonl` — metrics evidence file.
- `~/.local/share/aho/logs/logs.jsonl` — logs evidence file.
- `artifacts/iterations/0.2.16/acceptance/W0.json` — W0 acceptance archive (findings, baseline delta, probe results).
