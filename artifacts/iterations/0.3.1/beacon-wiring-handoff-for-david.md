# Beacon wiring handoff (for david) - 0.3.1 W2 Track B

**Audience:** david (Beacon developer)
**From:** aho executor (claude-code on a8cos) + operator (Kyle)
**Date:** 2026-05-26
**Status:** Track A (aho-side code) complete and verified. This doc lists
every value + service you need to provide or build to get aho emitting to
Beacon. Closes F-0.3.1-W0-003 operationally once converged.

> This file lives under `artifacts/iterations/0.3.1/` which is gitignored
> (deployment-private). Real host/tenant/project identifiers appear here; this
> doc is never committed to the public repo.

---

## TL;DR - what we need from you

| # | Ask | Used for |
|---|---|---|
| 1 | Beacon OTLP **gRPC endpoint URL** (host:port, and whether `https`/TLS or `http`/insecure) | aho exporter target |
| 2 | Beacon **OTLP ingest auth token** (Bearer) + how it should be minted (per-engineer vs shared) | `OTEL_EXPORTER_OTLP_HEADERS` |
| 3 | Confirm Beacon's **OTLP gRPC receiver is enabled** on the endpoint (your `OTLP_*` settings) | accept aho's pushes |
| 4 | Beacon **webhook URL + token** for the alert bridge (outbound aho -> Beacon) | `BEACON_WEBHOOK_URL` / `BEACON_WEBHOOK_TOKEN` |
| 5 | Beacon **inbound webhook payload schema** (what Beacon POSTs to aho's `/beacon` endpoint) | aho inbound relay parsing |
| 6 | Confirm the **resource-attribute keys** Beacon's TimescaleDB indexes on | dashboard filtering |
| 7 | Confirm **Tailscale ACL** allows a8cos (and the container) -> Beacon host on the OTLP port | network path |

Everything aho-side is already plumbed and env-driven. The moment items 1-2
land, host emission starts with one env-file edit + a service restart.

---

## Namespace gotcha (read first)

There are two OTLP env-var namespaces in play. Do not conflate them:

- **aho EMITS** using the OpenTelemetry SDK standard vars:
  `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`,
  `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_RESOURCE_ATTRIBUTES`,
  `OTEL_SERVICE_NAME`. (Prefix: `OTEL_EXPORTER_OTLP_`.)
- **Beacon CONFIGURES** its own receiver/exporter using its pydantic settings
  with prefix `OTLP_` (`OTLP_ENABLED`, `OTLP_ENDPOINT`, `OTLP_PROTOCOL`,
  `OTLP_INSECURE`, ...), per `artifacts/observability/260524-beacon-overview.md`.

So: you set `OTLP_*` on the Beacon side to turn the receiver on; aho sets
`OTEL_EXPORTER_OTLP_*` to point at you. The endpoint must agree; the prefixes
will not.

---

## Current state (verified on a8cos 2026-05-26)

- `OTEL_EXPORTER_OTLP_ENDPOINT` resolves to **empty** in a fresh login shell.
  `~/.config/aho/beacon.env` has the endpoint + token lines commented (Track B
  placeholders). `OTEL_SERVICE_NAME=aho` + resource attrs DO populate (the env
  shim works; only the endpoint is pending).
- With the endpoint unset, aho's `logger.py` falls back to
  `http://127.0.0.1:4317`. Nothing listens there (we deleted the 0.2.10-era
  local collector; aho emits direct to Beacon by design). So every aho OTLP
  span is currently **dropped silently** (logger swallows the connection
  failure; the JSONL event log stays authoritative).
- Substrate-freshness fact #14 `beacon_otlp_reachable` reports **unreachable**.
- **Net: aho emits nothing to Beacon yet.** The pipe is built end-to-end and
  flowing nowhere, pending items 1-2 above.

---

## What aho already provides (Track A, done)

- **Env-driven exporter.** `src/aho/logger.py` reads
  `OTEL_EXPORTER_OTLP_ENDPOINT` (default `http://127.0.0.1:4317`). TLS is
  auto-selected: `https://` -> secure channel, `http://` -> insecure. The SDK
  reads `OTEL_EXPORTER_OTLP_HEADERS` for auth on its own.
- **gRPC protocol.** aho uses the OTLP/gRPC span exporter (port 4317
  convention). `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`.
- **Deployment-private env file.** `~/.config/aho/beacon.env` (gitignored).
  Consumed by interactive fish via `~/.config/fish/conf.d/aho-beacon.fish` and
  by systemd user units via `EnvironmentFile=-%h/.config/aho/beacon.env`.
- **Resource attributes** (already populated in beacon.env):
  `OTEL_RESOURCE_ATTRIBUTES=engineer.id=kthompson,tenant.id=tachtech,lab.subnet=172.31.255.128/26,deployment.environment=dev,tier=base`
  plus `OTEL_SERVICE_NAME=aho`. aho also stamps `host.name` per host.
- **Reachability telemetry.** Fact #14 `beacon_otlp_reachable` TCP-probes the
  configured endpoint (outcomes: `ok` / `unreachable` / `auth_failed`) and
  renders on the dashboard brick grid.
- **Alert bridge (bidirectional).** `src/aho/alerts/telegram_alerts.py`:
  - outbound `beacon_post()` mirrors each alert to `BEACON_WEBHOOK_URL`
    (Bearer `BEACON_WEBHOOK_TOKEN`); no-op + Telegram-only if unset
  - inbound `/beacon` HTTP route relays Beacon-shaped payloads to the Telegram
    channel the operator watches

---

## What you provide (detail)

### 1. OTLP gRPC endpoint
- Format: `<scheme>://<beacon-host>.<tailnet>.ts.net:<port>` (gRPC, typically
  4317). Example shape: `https://beacon.tail8492.ts.net:4317`.
- Tell us scheme: **TLS (`https`)** or **insecure (`http`)**. If TLS with a
  self-signed cert, say so - aho's exporter uses a secure channel for `https`
  and we may need to point it at your CA bundle.
- Beacon project context: `beacon-492119`. aho fleet host emitting first:
  a8cos on tailnet `tail8492.ts.net`.

### 2. OTLP ingest auth token
- aho sends it as `OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer <token>`.
- Decide: **per-engineer token** (preferred for attribution + revocation) or
  **shared fleet token**. If per-engineer, a8cos/kthompson needs its own.
- Delivery: hand the token to the operator for the **1Password Connect -> aho
  secrets broker** pipeline (ADR-0009). aho never stores it plaintext in the
  repo; it lands in the gitignored `beacon.env` on-host, or the broker injects
  it at service start. The token is NOT something aho mints - you/operator do.

### 3. Receiver enabled
- Confirm Beacon's `OTLP_*` config has the gRPC receiver up on the endpoint:
  `OTLPGrpcServer` on 4317 (per beacon-overview `otlp_receiver.grpc_enabled`).
- Confirm it accepts **traces** (aho's primary signal is spans: LLM dispatches,
  workstream events, cost/token attrs) in addition to metrics/logs. The beacon
  overview describes metrics + logs receivers explicitly; we need traces too,
  or guidance on whether aho should emit metrics instead of/in addition to
  spans.

### 4. Webhook URL + token (alert bridge outbound)
- `BEACON_WEBHOOK_URL` - the Beacon generic-webhook ingest URL aho POSTs alerts
  to.
- `BEACON_WEBHOOK_TOKEN` - Bearer token for that POST.
- Both go in `beacon.env` (or broker). Unset = aho stays Telegram-only (no
  regression).

### 5. Inbound webhook schema (Beacon -> aho)
- aho's `/beacon` endpoint currently parses a tolerant generic shape: it looks
  for `title` / `alertname` / `summary`, `severity`, and `message` /
  `description`, and accepts either a single object or an `{"alerts": [...]}`
  list. **Send us your actual escalation payload schema** so we can tighten the
  parser. If it already matches the generic shape, no change needed.

### 6. Resource-attribute schema
- Confirm Beacon's TimescaleDB indexes on the attribute keys aho sends:
  `service.name`, `host.name`, `engineer.id`, `tenant.id`, `lab.subnet`,
  `deployment.environment`, `tier`. If you expect different key names, tell us
  and we'll align `OTEL_RESOURCE_ATTRIBUTES`.

### 7. Tailscale ACL
- Confirm the tailnet ACL permits a8cos (`tag:engineer-host` or equivalent) to
  reach the Beacon host on the OTLP port. Same question for the container's
  egress path (see container section).

---

## Host wiring (a8cos)

Once items 1-2 land, the operator does (no aho code change):

1. Uncomment + fill the two lines in `~/.config/aho/beacon.env`:
   - `OTEL_EXPORTER_OTLP_ENDPOINT=<your endpoint from item 1>`
   - `OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer <token from item 2>`
2. Restart the aho user services so they re-source the env file:
   `systemctl --user restart aho-openclaw aho-nemoclaw aho-telegram aho-harness-watcher`
   (the broker can stay up; it does not emit telemetry).
3. New interactive shells pick up the endpoint automatically (fish `conf.d`
   shim). Existing shells need a re-source or new login.
4. Verify: `aho-probe-substrate --fact beacon_otlp_reachable --summary` should
   flip from `unreachable` to `ok`.

**Host-level system metrics (optional, your call):** the architectural
framework describes a per-engineer local `otel/opentelemetry-collector-contrib`
that forwards host CPU/mem/disk/net to central Beacon (hub-and-spoke). aho does
NOT ship that collector today (we removed the 0.2.10 local-collector). If you
want host-level system metrics (not just aho-app spans), tell us whether to:
- (a) stand up a local `otelcol-contrib` on a8cos forwarding to Beacon, or
- (b) have aho emit host metrics directly via its SDK, or
- (c) skip host-level metrics for now (aho-app spans only).

---

## Container wiring (aho OCI image)

The aho container (`ghcr.io/soc-foundry/aho:0.2.18`) runs the same
`logger.py`, so it emits via the same `OTEL_EXPORTER_OTLP_*` vars. Two gaps:

1. **STALE baked default.** The image's Dockerfile bakes
   `OTEL_EXPORTER_OTLP_ENDPOINT=http://nzxtcos.tail8492.ts.net:4317` - pointing
   at the **decommissioned NZXTcos host**. Until the image is rebuilt (0.3.2),
   the container must have the endpoint **overridden at runtime**. Options:
   - pass `-e OTEL_EXPORTER_OTLP_ENDPOINT=<beacon> -e OTEL_EXPORTER_OTLP_HEADERS=...`
     on `podman run` (via the `aho host run-container` wrapper's extra-flag
     passthrough), or
   - bind-mount / inject `beacon.env` and source it in the container entrypoint.
   - **0.3.2 fix:** rebuild base + partial images with the Beacon endpoint as
     the env-var default (or no default + require runtime injection).
2. **Container -> Beacon network path.** Decide how the container egresses:
   - if Beacon is reachable on the tailnet and the container has tailnet access
     (tailscale0), it can hit the Beacon FQDN directly;
   - otherwise it routes through the host (`host.containers.internal`) to a
     host-local collector that forwards to Beacon.
   The L5 "Tailscale0 binding" hardening invariant is NOT enforced yet (carry-
   forward), so confirm the container's actual egress with the operator.

**What we need from you for the container:** same endpoint + token as the host
(or a container-scoped token if you prefer per-workload attribution), plus
confirmation of the egress path so we wire the `run_container` env passthrough
correctly.

---

## Tokens / service accounts to build

| Item | Who builds | Where it lands | Notes |
|---|---|---|---|
| Beacon OTLP ingest token (host) | david / operator | aho secrets broker -> beacon.env | per-engineer preferred |
| Beacon OTLP ingest token (container) | david / operator | runtime `-e` or broker | same or container-scoped |
| Beacon webhook token (outbound alerts) | david / operator | beacon.env (`BEACON_WEBHOOK_TOKEN`) | for the alert bridge |
| Tailscale ACL grant (a8cos + container -> Beacon:4317) | operator (tailnet admin) | tailnet policy | network path |

aho does not mint any of these - they are Beacon-side / operator-side. aho's
broker (ADR-0009) is the on-host storage boundary; tokens reach it via the
1Password Connect pipeline, never plaintext in the repo.

> Note (not your scope, FYI): a separate Track B item is the **notjustavar
> Firestore + IAM service account** (`tteos-497515` / database `notjustavar`)
> for aho's tenant data writer. That is unrelated to Beacon OTLP wiring; it
> gates W3's first tenant data write, not telemetry emission. Flagged so the
> two Track B streams are not confused.

---

## Verification (once converged)

1. `aho-probe-substrate --fact beacon_otlp_reachable --summary` -> `ok`.
2. Trigger an aho dispatch (any council call or workstream event) and confirm
   the span lands in Beacon's TimescaleDB filtered by
   `service.name=aho, host.name=a8cos`.
3. Outbound alert: synthetic Alertmanager fire -> confirm it arrives at the
   Beacon webhook (your side).
4. Inbound alert: POST a Beacon-shape payload to aho's `/beacon` endpoint ->
   confirm it arrives in the operator's Telegram channel.
5. Container: run a workload via `aho host run-container` with the endpoint
   override and confirm container spans arrive tagged with the container's
   `host.name` / `deployment.environment`.

---

## Open questions / decisions for david + operator

1. Per-engineer vs shared OTLP ingest token? (attribution + revocation)
2. TLS posture on the Beacon endpoint (real cert / self-signed / insecure)?
3. Does Beacon's gRPC receiver accept **traces**, or should aho emit metrics?
4. Beacon inbound webhook payload schema (to tighten aho's `/beacon` parser).
5. Host-level system metrics: local `otelcol-contrib` hop, direct SDK emit, or
   skip for now?
6. Container egress path to Beacon: direct tailnet vs host-routed?
7. Timing: is the Beacon endpoint live now (so we can converge W2 / F-0.3.1-W0-003),
   or should W3 launch in deferred-execution shape?

---

## Cross-references

- `docs/operations/otel-telemetry.md` - aho's env-driven OTEL convention (public)
- `artifacts/observability/260524-beacon-overview.md` - Beacon architecture
- `artifacts/iterations/0.3.1/W2-close-note.md` - W2 close (F-0.3.1-W0-003 code-closed, Track-B-gated)
- `artifacts/adrs/0009-secrets-broker-boundary.md` - broker credential boundary
- `src/aho/logger.py` - exporter setup (env-driven endpoint)
- `~/.config/aho/beacon.env` - the env file to populate (on-host, gitignored)
