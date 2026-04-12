# W16 Smoke Validation Findings — 0.2.10

**Date:** 2026-04-12
**Executor:** claude-code

---

## Acceptance Checks

| # | Check | Result | Notes |
|---|---|---|---|
| 1 | `aho run "hello world"` from /tmp/ | PASS | Dispatched to OpenClaw → Qwen, response returned, output written to /tmp/aho-output/run-20260412T054125.md |
| 2 | All 6 systemd services active | PASS | openclaw, telegram, harness-watcher, otel-collector, jaeger, dashboard — all active |
| 3 | OpenClaw socket at /run/user/$UID/ | PASS | srwxr-xr-x at /run/user/1000/openclaw.sock |
| 4 | Jaeger UI at 127.0.0.1:16686 | PASS | Returns HTML, Jaeger v1.62.0 |
| 5 | Dashboard /api/state with install_completeness | PASS | 8/8 dirs present, 10/11 binaries present (otelcol-contrib named differently), CLI symlink present |
| 6 | OTEL→Jaeger connection-refused errors cleared | PASS | 0 connection-refused errors in last 2 minutes after IPv4 fix |
| 7 | `aho doctor --deep` flutter/dart | PASS | flutter doctor 6/6 ok, Dart SDK 3.11.4 |

## Findings

### F1: aho run output quality
The LLM (Qwen) response to "hello world" was contextually confused — it read stale files in /tmp/ from a prior iteration and hallucinated about 0.1.13 workstreams. This is expected behavior for persona 3 with no curated context. The **dispatch pipeline** is validated; LLM response quality is a 0.2.11 persona 3 concern.

### F2: otelcol-contrib binary naming
The installed binary is `aho-otel-collector` (direct download, 361MB) not `otelcol-contrib` (AUR package name). The `_install_completeness()` check in the dashboard aggregator looks for `otelcol-contrib`, which shows "missing". The binary is present and running. AUR path deferred to 0.2.11.

### F3: Jaeger OTLP HTTP port conflict
Jaeger v1.62.0 defaults to binding `:4318` for OTLP HTTP, which conflicts with otelcol-contrib's OTLP HTTP receiver. Fixed by adding `--collector.otlp.http.host-port=localhost:14318` to move Jaeger's HTTP receiver to a non-conflicting port.

### F4: IPv4 vs IPv6 for Jaeger gRPC
otelcol-contrib resolves `localhost:14317` to both IPv4 and IPv6. Jaeger binds only IPv4 (127.0.0.1). This caused intermittent connection-refused errors on the IPv6 path. Fixed by configuring otelcol-contrib to use `127.0.0.1:14317` explicitly.

### F5: Dashboard AHO_PROJECT_ROOT
The dashboard systemd service needs `AHO_PROJECT_ROOT` environment variable set to find the project. Added to the service template. This is a portability concern for P3 clone-to-deploy.

## Overall

7/7 acceptance checks pass. Pipeline validated end-to-end. Findings are non-blocking for 0.2.10 close.
