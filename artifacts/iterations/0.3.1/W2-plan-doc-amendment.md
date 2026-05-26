# W2 plan-doc amendment (post-W1-close, post-davidk-Beacon-feedback)

**Iteration:** 0.3.1
**Workstream:** W2
**Status:** plan-doc amendment, supersedes original W2 scope in `aho-plan-0.3.1.md` §W2
**Authored:** 2026-05-26 (post-W1-close, post-davidk-Beacon-integration-feedback)
**Authoring agent:** drafter (claude-web)

## Scope reshape from original W2 plan-doc

Original W2 scope (sealed in `aho-plan-0.3.1.md` §W2): install.fish tier-aware refactor + 0.2.18 W2 carry-forward closures (F-W2-002/003/004) + pacman pin + syncthing v1.30.0 probe. Five deliverables, 4-8h.

Two reshape inputs post-W1-close:

1. **davidk (TachTech-Engineering/Beacon developer) provided Beacon integration guidance.** Key insight: aho's existing OpenTelemetry SDK already handles OTLP emission; only `src/aho/logger.py:33` has a hardcoded endpoint. Making that env-driven gives Beacon every aho span (LLM calls, workstream events, cost/token attributes, substrate-freshness gauges) without code-level extraction work. The "extract beacon's otel/ package as inspired-by adaptation" plan from earlier chat refinement was over-scoped — env-var change is sufficient.
2. **Architectural framework decisions during W1 chat refinement** added tenant-aware Firestore writer + notjustavar schema seed to W2 scope. These remain in scope; davidk's feedback simplifies the OTLP wiring substantially, opening room for the Firestore work without bloating W2.

Result: W2 grows from 5 deliverables to 8, but each is tighter than the originally-scoped Beacon extraction work. Estimated 8-10h overnight, hard ceiling 12h.

## Two-track execution model

W2 runs two parallel tracks that converge at acceptance gates:

**Track A — Executor-side code changes on a8cos.** Claude Code in your session writes:
- Env-driven OTLP endpoint configuration
- Alert bridge expansion (Telegram → Beacon webhook reverse path)
- Tenant-aware Firestore writer module
- install.fish tier-aware refactor closing 0.2.18 W2 carry-forwards
- substrate-freshness fact #14 (Beacon reachability)

**Track B — Operator-side parallel work (Kyle, hands-on).** You provision:
- Firebase configuration for notjustavar Firestore instance in `tteos-497515`
- IAM service account with write access to notjustavar
- Service account key delivered into 1Password broker
- Beacon-side wiring (davidk handles `beacon-492119` configuration, surfaces endpoint + auth token to you)

Track A code is env-var-driven from the start. Real Firestore + real Beacon integration tests gate on Track B substrate-ready. Mock/emulator tests run independently.

## Updated deliverables (8 total)

### D1 — Env-driven OTLP endpoint configuration

**Module:** Modify `src/aho/logger.py:33` to read `OTEL_EXPORTER_OTLP_ENDPOINT` (OpenTelemetry SDK standard env var) with fallback to existing hardcoded value for backward compat during transition. Update stale 0.2.10-era artifacts.

**Specific files (per W2 substrate audit on a8cos, 2026-05-26):**

1. `src/aho/logger.py:33` — replace hardcoded `http://127.0.0.1:4317` with `os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")`. Default-fallback preserves existing behavior on hosts without the env var set.
2. `bin/aho-otel-up` / `bin/aho-otel-down` — 0.2.10-era wrappers reference nonexistent systemd units. **Delete both.** Not deploying local collectors; Beacon receives directly via env-var endpoint.
3. `templates/otelcol-config.yaml` — 0.2.10-era template configures local Jaeger sidecar. **Delete.** No local OTel collector hop needed; aho emits direct to Beacon.
4. Five systemd units (aho-harness-watcher, etc.) — add `Environment=OTEL_EXPORTER_OTLP_ENDPOINT=<beacon-endpoint>` to each `[Service]` section. Endpoint value sourced from `~/.config/aho/beacon.env` (created in D2).
5. `install.fish` — new step `otel_endpoint_configured` verifies `OTEL_EXPORTER_OTLP_ENDPOINT` is set in shell env + canonical config + systemd unit Environment lines. Per W1 idempotency contract: check first, remediate via env-file write, re-check.
6. `bin/aho-claw3d` + other service wrappers — inherit env via systemd unit Environment lines (no change to wrappers themselves; systemd handles propagation).
7. `CLAUDE.md` §OTEL telemetry — update endpoint convention to reflect env-driven config + Beacon target. Note this file is gitignored per F-0.2.17-W6-003; document the canonical convention in commit-tracked `docs/operations/otel-telemetry.md` (new).

**Acceptance gates:**
- `src/aho/logger.py:33` reads env var; behavior preserved if env var unset
- 0.2.10-era stale wrappers/template deleted (verified absent)
- Systemd units have `Environment=OTEL_EXPORTER_OTLP_ENDPOINT=...` lines
- install.fish step `otel_endpoint_configured` passes on a8cos with Beacon endpoint configured
- aho process traces emit to configured endpoint (verified via Beacon-side acknowledgment from davidk, gated on Track B endpoint provisioning)

### D2 — `~/.config/aho/beacon.env` env-file

**Module:** New file `~/.config/aho/beacon.env` (created at install time, not committed to repo). Contains:

```
OTEL_EXPORTER_OTLP_ENDPOINT=https://beacon.tail8492.ts.net:4317
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer <beacon-token>
OTEL_SERVICE_NAME=aho
OTEL_RESOURCE_ATTRIBUTES=engineer.id=kthompson,tenant.id=tachtech,lab.subnet=172.31.255.128/26,deployment.environment=dev,tier=base
```

The `<beacon-token>` is retrieved via aho's broker contract at install time. **Operator provides token to broker via existing 1Password Connect → broker pipeline (Track B work).**

install.fish step `beacon_env_file_present` creates the file if absent, sources it on shell init via `~/.config/fish/conf.d/aho-beacon.fish` (new) for interactive sessions, systemd `EnvironmentFile=` for systemd-managed services.

**Acceptance gates:**
- `~/.config/aho/beacon.env` exists post-install with correct shape
- Shell sessions inherit `OTEL_EXPORTER_OTLP_ENDPOINT` automatically
- systemd services inherit endpoint via `EnvironmentFile=` directive
- Token retrieved via broker contract (never plaintext in env-file checked into version control — `~/.config/aho/` is gitignored)

### D3 — Alert bridge expansion (Telegram → Beacon webhook + reverse)

**Module:** Modify `src/aho/alerts/telegram_alerts.py`. Two changes:

**Outbound (aho → Beacon):** When Alertmanager fires an aho alert, POST to Beacon's generic webhook channel in addition to (or instead of, configurable) Telegram. davidk surfaces Beacon's webhook URL + auth as part of Track B. Config via env var `BEACON_WEBHOOK_URL` + `BEACON_WEBHOOK_TOKEN`.

**Inbound (Beacon → aho):** Add HTTP endpoint to aho's existing alert server that accepts Beacon-shaped webhook payload. Routes the alert to Telegram (existing path). Means Beacon's escalations ("agent host down," "GPU stuck") reach the same Telegram channel where operator already lives.

**Acceptance gates:**
- Outbound test: synthetic Alertmanager fire → arrives at Beacon's webhook (verified via davidk-side acknowledgment)
- Inbound test: synthetic Beacon-shape POST to aho's alert server → arrives in Telegram channel
- Config env-var-driven; backward compat preserved if `BEACON_WEBHOOK_URL` unset (Telegram-only path continues working)

### D4 — Tenant-aware Firestore writer module

**Module:** New `src/aho/firestore_writer/__init__.py` + `src/aho/firestore_writer/client.py`. API:

```python
write_or_update(
    tenant_id: str,           # "tachtech" or future customer codename
    log_type: str,            # t_log_type value: "gotcha", "audit_disposition", "iteration_metadata", "telemetry_summary", etc.
    document_id: str,         # canonical ID like "F-0.3.1-W1-001"
    document_data: dict,      # the data payload
    indicator_fields: dict,   # t_any_* fields per kjtcom schema convention
) -> WriteResult
```

Implementation reads tenant routing from env vars:
- `AHO_TENANT_ID=tachtech`
- `AHO_TENANT_FIRESTORE_PROJECT=tteos-497515`
- `AHO_TENANT_FIRESTORE_DATABASE=notjustavar`
- `AHO_TENANT_FIRESTORE_SERVICE_ACCOUNT_KEY_PATH=<broker-retrieved>`

Idempotent: write-or-update by `document_id`. Pillar 11-compatible: service account key retrieved via broker contract, never plaintext on disk in repo paths.

**Acceptance gates:**
- Unit tests using Firestore emulator pass (`gcloud emulators firestore start` background, point client at emulator endpoint)
- `aho firestore-writer test-write --tenant tachtech --log-type test_marker --document-id W2-D4-acceptance` integration test gates on Track B substrate ready; runs at executor-prompted post-Track-B-confirmation
- Idempotency: re-running test-write produces identical doc state (same fields, no duplicate)
- Pillar 11 check: no service account key visible in repo working tree at any point

### D5 — Initial schema seed in notjustavar (gated on Track B)

**Module:** New `bin/aho-firestore-bootstrap` fish wrapper + Python implementation. Writes initial schema markers to notjustavar:

- Collection: `t_log` (single canonical collection per kjtcom convention)
- Initial document: `{document_id: "_schema_v1", t_log_type: "schema_marker", t_log_source: "aho", t_any_iteration: "0.3.1", t_any_workstream: "W2", t_any_schema_version: "1.0.0", t_any_created_utc: "2026-05-26T..."}` (timestamp at bootstrap execution time)
- One document per anticipated `t_log_type` (minimum viable set): `gotcha`, `audit_disposition`, `iteration_metadata`, `telemetry_summary`, `substrate_observable`. Each is a `schema_definition` doc listing the `t_any_*` fields valid for that type.

**Acceptance gates:**
- `aho-firestore-bootstrap --dry-run` reports planned writes (~6 schema-definition docs + 1 marker doc)
- Default invocation writes successfully (gated on Track B notjustavar provisioning complete)
- Post-bootstrap, query `t_log` collection returns expected doc count + correct shape
- Idempotent: re-running produces no duplicates

### D6 — install.fish tier-aware refactor (closes F-0.2.18-W2-002/003/004)

**Module:** Per original W2 plan-doc §W2 (sealed). Three sub-deliverables coherent with each other:

1. **F-0.2.18-W2-002 closure:** `bin/aho-models` tier-aware refactor. Reads `~/.config/aho/tier.json`, branches on tier, pulls appropriate model bundle.
2. **F-0.2.18-W2-003 closure:** `aho install tier-manifest` subcommand. Detects VRAM, writes tier.json with `{tier, vram_gb, detected_at}`. Already exists per W1 D1 work? Verify and refactor if needed.
3. **F-0.2.18-W2-004 closure:** `templates/systemd/aho-secrets-broker.service.template` (new). `bin/aho-systemd install` installs broker as per-user systemd unit.

**Acceptance gates:**
- `tier.json` on a8cos shows correct base-tier bundle
- Broker service `active (running)` on a8cos
- F-0.2.18-W2-002/003/004 entries in carry-forwards file marked closed structurally

### D7 — Substrate-freshness fact #14 + F-0.3.1-W0-005 closure

**Module:** Extend W1's 13-fact substrate-freshness telemetry to include fact #14: `aho.observable.beacon_otlp_reachable`. Per davidk's bonus item 1.

**Probe shape:** TCP connection attempt to Beacon endpoint + lightweight OTLP gRPC handshake. `probe_outcome: "ok"` if endpoint responds, `"unreachable"` if connection fails, `"auth_failed"` if connection succeeds but token rejected.

**F-0.3.1-W0-005 closure** (legacy sys.path drift): `pip install --user --break-system-packages -e ~/Development/Projects/socfoundry/aho` to re-install editable pointing at canonical path. Verify `sys.path` no longer includes `/home/kthompson/dev/projects/aho/src` legacy entry. install.fish step `python_sys_path_clean` from W1 should transition from "fail" to "pass" post-remediation.

**Acceptance gates:**
- Fact #14 probable, reports correct status against Beacon endpoint
- Dashboard renders fact #14 (extending W1 D5 brick grid from 13 to 14 facts)
- F-0.3.1-W0-003 closure invariant met (Beacon reachable from a8cos)
- F-0.3.1-W0-005 closure invariant met (sys.path clean probe passes)

### D8 — Pacman pin + syncthing v1.30.0 doctor probe + W2 self-audit

**Module:** Per original W2 plan-doc:

1. **`bin/aho-pacman pin syncthing`** subcommand absorbed from 0.3.0 fix script. Idempotent; verifies `IgnorePkg = syncthing` line in `/etc/pacman.conf` `[options]` section.
2. **Syncthing v1.30.0 doctor probe** — `aho doctor` (or new `aho-doctor` from W1) flags any syncthing version != v1.30.0 as SCoT compliance regression.
3. **W2 self-audit** via `aho.council.audit` on W2 acceptance archive. RAG enrichment + filter + anti-rubber-stamp extensions. **Second non-vacuous audit on populated collection** (post-W1 D2 bootstrap).

**Acceptance gates per amendment §D8:** standard self-audit shape. Halt-and-surface after emit regardless of disposition. Drafter reviews pre-sign.

## Carry-forwards expected at W2 close

**Closing structurally in W2:**
- F-0.2.18-W2-002 (tier-aware aho-models via D6)
- F-0.2.18-W2-003 (tier-manifest writer via D6)
- F-0.2.18-W2-004 (broker systemd template via D6)
- F-0.3.1-W0-003 (OTEL endpoint migration to Beacon-aggregator via D1+D2)
- F-0.3.1-W0-005 (legacy sys.path drift via D7 re-install)

**Potentially new from D1-D8 execution surfacing:**
- TBD based on substrate gaps encountered during install.fish refactor, Beacon wiring, or Firestore integration

## Two-track convergence gates

**Track B operator-side dependencies for executor acceptance:**

- D1 acceptance: Beacon endpoint provisioned + token in broker → required before `OTEL_EXPORTER_OTLP_ENDPOINT` value can be written into env-file
- D3 acceptance: Beacon webhook URL surfaced → required before alert bridge outbound test
- D4 acceptance: notjustavar Firestore + IAM service account → required before integration test
- D5 acceptance: depends on D4 substrate ready

If Track B substrate not ready when executor reaches gate, executor halts-and-surfaces "blocked on Track B"; operator confirms substrate state; executor resumes. Per W1's bold-when-clear/escalate-when-ambiguous contract: substrate-not-ready is genuinely ambiguous (substrate exists or not is operator-knowledge), warrants halt.

## Halt-and-surface conditions

- Wall-time > 10h soft / 12h hard
- D1 changes break existing OTLP emission on hosts without Beacon endpoint set (backward compat regression)
- D3 alert bridge changes break existing Telegram path
- D4 Firestore writer fails idempotency property
- D6 install.fish refactor breaks existing tier.json structure (backward incompat)
- D8 self-audit fake-ID-on-registered finding (W4-0.2.17 filter regression)
- Track B substrate not ready at convergence gate (halt + surface, not failure)

## Cross-references

- `artifacts/iterations/0.3.1/W1-close-note.md` — predecessor workstream close
- `artifacts/iterations/0.3.1/tteos-architectural-framework-report-2026-05-25.md` — architectural baseline including tenant-aware framing
- `artifacts/observability/260524-beacon-overview.md` — Beacon architecture reference
- davidk's Beacon-wiring feedback (2026-05-26) — informs D1+D3+D7 scope; not yet archived
- `artifacts/adrs/0011-substrate-freshness.md` — substrate freshness ADR (D7 extends fact set 13 → 14)
- `artifacts/adrs/0012-chain-of-trust-l5.md` — Chain of Trust L5 placement (W2 ships first cross-tenant-relevant integration)

## Forward-looking notes

**W3 (council-mining retrospective):** Pipeline runs against populated ChromaDB collection from W1 D2. Output (augmented gotcha registry with human-right / council-right / human-wrong / council-wrong quadrants) lands in notjustavar Firestore via W2's `firestore_writer` module. First substantial Tachtech-tenant data write.

**W4 (Firestore schema dry-run):** Validates `t_any_*` indicator field shape against ingest patterns. Uses notjustavar or test database within `tteos-497515`.

**W6 (ADR consolidation):** ADR-0013 candidate "Beacon as canonical OTLP aggregator" — landed W2, formal ADR captures decision. ADR-0014 candidate "aho multi-tenant data architecture" — design-doc capturing TTEOS / notjustavar / customer-codename pattern for future-state consideration.

**0.3.2 (TTEOS production deployment):** OCI image (base + partial) ships with W2's env-var-driven OTLP wiring + Firestore writer baked in. Tenant configuration injected at deploy-time per architectural framework report §4.4.
