# OTEL telemetry configuration

aho emits OpenTelemetry traces, metrics, and logs from every process (LLM
dispatches, workstream events, cost/token attributes, substrate-freshness
gauges). Emission is env-driven: the same build emits to a local collector,
a central aggregator, or nowhere, depending on deployment configuration.

## Endpoint configuration

aho reads the OpenTelemetry SDK standard environment variables. The emission
endpoint is `OTEL_EXPORTER_OTLP_ENDPOINT`:

- **Unset** (default): falls back to `http://127.0.0.1:4317` (local gRPC
  collector, single-host behavior). If nothing listens there, emission fails
  silently and the JSONL event log remains the authoritative record.
- **Set to an `https://` endpoint**: TLS transport, auth via
  `OTEL_EXPORTER_OTLP_HEADERS`. This is the central-aggregator deployment.
- **Set to an `http://` endpoint**: insecure transport (local or trusted
  network only).

The endpoint is consumed in `src/aho/logger.py` at tracer-provider setup.
Opt out entirely with `AHO_OTEL_DISABLED=1`.

## Standard env vars

| Variable | Purpose |
|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | gRPC endpoint for OTLP export |
| `OTEL_EXPORTER_OTLP_HEADERS` | auth headers, e.g. `authorization=Bearer <token>` |
| `OTEL_SERVICE_NAME` | service name resource attribute (aho components set `aho`) |
| `OTEL_RESOURCE_ATTRIBUTES` | comma-separated resource attributes (engineer id, tenant id, lab subnet, deployment environment, tier) |
| `AHO_OTEL_DISABLED` | set to `1` to disable OTEL emission entirely |

## Deployment-private env file

Per-deployment endpoint, auth token, and resource attributes live in a
deployment-private env file at `~/.config/aho/beacon.env` (the `~/.config/aho/`
directory is gitignored; the file is never committed). It is consumed by:

- **interactive shells** via a fish `conf.d` shim that parses the file and
  exports each `KEY=value`
- **systemd user units** via the `EnvironmentFile=-%h/.config/aho/beacon.env`
  directive (the leading `-` makes it optional, so units start cleanly even
  when the file is absent)

The auth token is retrieved through the secrets broker (see ADR-0009); it is
never committed in plaintext.

The `install.fish` steps `beacon_env_file_present` and
`otel_endpoint_configured` verify the env file exists and that an active
endpoint line is present. The endpoint value itself is a deployment-time
input (it depends on where the aggregator lives), so `otel_endpoint_configured`
reports a gap until that value is supplied - this is expected on a fresh host
before the aggregator endpoint is provisioned.

## Reachability telemetry

Substrate-freshness fact `beacon_otlp_reachable` (see ADR-0011) probes the
configured endpoint with a TCP connect plus a lightweight OTLP handshake.
Outcomes: `ok` (endpoint responds), `unreachable` (connection fails),
`auth_failed` (connects but token rejected). The dashboard brick grid renders
it alongside the other substrate facts.

## Cross-references

- `src/aho/logger.py` - tracer-provider setup, endpoint resolution
- `artifacts/adrs/0011-substrate-freshness.md` - substrate-freshness telemetry
- `artifacts/adrs/0009-secrets-broker-boundary.md` - broker credential boundary
