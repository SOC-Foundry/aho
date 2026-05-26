# aho Component Decomposition (base tier)

**Status:** Repo-resident authoritative spec (W5 D4 deliverable).
**Iteration of record:** aho 0.2.17 W5 (consolidating 0.2.17 W0–W4 implementation work).
**Source paths:** All source paths relative to repo root; `sha256` columns recorded at W4 close (2026-05-03).
**Supersedes:** chat-side architecture artifact `aho-base-container-architecture.md` §Component decomposition (see [Provenance](#provenance) below).

---

## Tier model

aho's runtime decomposes into three tiers, two delivery surfaces, and a host-side support surface:

- **Process tier.** The CLI and process-control surfaces - workstream launch, dispatch routing, secrets-client, artifact emission. Runs in-container at base tier; orchestrates the council seats.
- **Council tier.** The five-seat agent fleet at base tier - drafter (external), executor (external), auditor (in-container llama3.2), triage (in-container nemotron-mini), retrieval (in-container nomic-embed-text + ChromaDB).
- **Observation tier.** Telemetry, health endpoints, signal aggregation, audit-disposition emission, materiality counters.

Two delivery surfaces:

- **In-image.** Code, Python virtualenv, ollama binary, harness reference materials. Bit-identical across operators per [ADR-0009](../../artifacts/adrs/0009-secrets-broker-boundary.md) Rule 1.
- **Host-mounted.** ChromaDB volume, iteration state volume, tier config, secrets broker socket. Per-host content; never in image layers.

One host-side support surface:

- **Host-side broker.** `aho.host.secrets_broker` runs on the host (not in container) per [ADR-0009](../../artifacts/adrs/0009-secrets-broker-boundary.md). Accessed by the in-container client via bind-mounted unix socket.

Out-of-process model layer:

- **Hybrid mode (development affordance).** Per [ADR-0008](../../artifacts/adrs/0008-dispatcher-missing-model.md): partial-tier dispatches escape the container via `host.containers.internal:11434` to the host's native Ollama. Production deferred to 0.3.x.

---

## Process tier

| Component | Source path | W4-close sha256 | Contract surface |
|---|---|---|---|
| CLI entrypoint | `src/aho/cli.py` | `65b5efcf7994b03c4da8dae6b2de832abc51a6a6c6aec2f32004b42ee7688e76` | argparse-driven user-facing commands. Hosts `aho host install`, `aho host run-container`, `aho iteration ...`, `aho workstream ...`, `aho secrets-test` (W6-removable per F-0.2.17-W1-001). |
| Dispatch (pipeline) | `src/aho/pipeline/dispatcher.py` | `152bb17aea363fbdd5d3f3f204c2b70f0923dee6dd061de34aeff5fc4832ca4d` | Multi-model dispatcher with `MODEL_FAMILY_CONFIG` longest-prefix family resolution. Hybrid-mode env gate per ADR-0008. Reads `TRACEPARENT` from subprocess env for OTEL trace propagation. |
| Pipeline router | `src/aho/pipeline/router.py` | `7b0daa424bcdd3166cfc1f80e8633167e06217f1ba9e75ce7a6b39477acef394` | Canonical classification primitive. `NemoClawOrchestrator.route()` consumes; legacy `nemotron_client.classify` is deprecated. |
| Workstream events | `src/aho/workstream_events.py` | `5123f892cfd54a764468c2810a5e8348413f9809f92840854eb19f83c993cbfc` | Emits `workstream_start`, `pending_audit`, `workstream_complete`, `audit_complete` events. State-machine source of truth for Adversarial Authorship transitions. |
| Workstream init | `src/aho/workstream_init.py` | `56462be9a5ccdb0b81d2e4caf87c5173e1b592fcd9617431d1d0336f8329f3f4` | Bin-wrapper for `aho workstream init W{N}` per F-W1-001 carry-forward - writes literal env values into `.claude/settings.json` at workstream boundary (Pillar 4 surface). |
| Workstream gate | `src/aho/workstream_gate.py` | `7a3fb60b880b6c96695370f34050f2ab2a362afb6964637b32e434b371553fd1` | State-machine gate enforcement (`pending_audit` → `audit_complete` → `workstream_complete`). |
| Secrets client (container-side) | `src/aho/secrets_client.py` | `e9b305f7db831a267fd8a013185ae2549a1b6cc88cdd6b4fe0f5327043f5a04e` | Connects to bind-mounted broker socket (`AHO_SECRETS_SOCKET`, default `/run/host-services/aho-secrets.sock`). JSON line request/response. No caching across container restarts. Implements [ADR-0009](../../artifacts/adrs/0009-secrets-broker-boundary.md) Rule 2. |
| Audit-disposition emitter | `src/aho/audit_disposition_emitter.py` | `a3e6df0469fe5183c7ddb7caf410ddf61adec20c5273450b7764cddb3703b2fa` | Emits audit dispositions to `audit/W{N}.json` archives. W4 update: surfaces `suppressed_findings` and `finding_filter` in emitted JSON for filter transparency. |
| Gap / carry-forward writer | `src/aho/gap_carry_forward_writer.py` | `d0799c8194fa40febb9e873ab87839632fada814727c9b43f535fcf7368bf248` | `append_to_file` writes new carry-forward entries under target headings in `carry-forwards-{iteration}.md`. Strict-regex entry counting; permissive cross-iteration counter is callsite-side. ChromaDB re-index hook is W6 scope (F-0.2.17-W4-001). |
| Tier detect | `src/aho/tier_detect.py` | `71fd9785def9af04009be7ce2cdf5982675dab00c4522e1521dc45e428ad1b5c` | NVIDIA-driver-aware tier classification. AHO_TIER env override path. Persists tier to `/var/run/aho/tier`. |
| Logger / OTEL init | `src/aho/logger.py` | `3c6b1b1bb06498626fdad29263f0f6e3b842d697e1325111df9acfb9b5c1158e` | TracerProvider + LoggerProvider + MeterProvider initialization. Reads `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_RESOURCE_ATTRIBUTES`. Module-import-time init - daemons cache `_ITERATION` here (F-0.2.17-W0-002 carry-forward). |

The process tier owns no model state. All model invocations are routed through the council tier or the dispatcher. The workstream-events module is the durable record of state transitions; checkpoint advancement is gated on event emission.

---

## Council tier

The council is five seats. Two are **external** (drafter, executor) - they run on operator chat / CLI, not in the container, and have no module surface. Three are **in-container**.

### External seats (no container module)

| Seat | Where it runs | Contract |
|---|---|---|
| Drafter | Claude web (chat-resident) | Plan-doc authoring; drafter arbitration of audit findings; gap-net for what auditor cannot catch by design. |
| Executor | Claude Code (or Gemini CLI) on operator workstation | Per-iteration; codified per-iteration in plan-doc. Implements deliverables; emits acceptance archive; emits OTEL telemetry; never invokes git. |

### In-container seats

| Seat | Module | Source path | W4-close sha256 | Base-tier model | Contract surface |
|---|---|---|---|---|---|
| Council dispatcher (seat router) | `aho.council.dispatch` | `src/aho/council/dispatch.py` | `7d67e03ea0bb3ddc19b3d5a00f786d7a678ef0c5c6c7482da4c6abeaca376257` | n/a | Routes work to the right seat. Stub at W1; real wiring at W2+. |
| Triage seat | `aho.council.triage` | `src/aho/council/triage.py` | `f17ac667119e35717d9b4988a7aaed9652c6018d896eb391c982aca40cf55a73` | `nemotron-mini:4b` | Classification only. Raise-on-malformed (G083). No `categories[-1]` fallback. |
| Auditor seat | `aho.council.audit` | `src/aho/council/audit.py` | `12f2cabcb6d2449d2e547912862252c3f49d9fa9663cda871305641d092dd35c` | `llama3.2:3b` | Structural spot-check: claim-vs-artifact, contract-shape, invariant resolution. Confidence floor 0.85 structural. RAG enrichment via `audit_ref_lookup` (W3 D2). Post-hoc filter via `audit_finding_filter` (W4 D1). Disposition shape `clean | halt | surface_to_drafter` with `clean` unreachable below floor. SEVERITY_SYNONYMS table absorbs source-artifact severity vocabulary mimicry per F-0.2.17-W2-003. |
| Embedder | `aho.council.embed` | `src/aho/council/embed.py` | `5ac9bf3f148caa0f387290f3149ba9afb88aee30d576bbb18441ef4fb68b2fb6` | `nomic-embed-text` | Sole embedding surface for retrieval. 768-dim vectors. Chunking at 4000 chars with 500-char overlap (per F-0.2.17-W2-002 - nomic-embed-text 7000-char/5000-char context-length cap). |
| Council client | `aho.council._client` | `src/aho/council/_client.py` | `31bbec0a315257e7470ac4600d2fa9cdf9452055b82c3de745892c246eb929f3` | n/a | Internal HTTP client to host or in-container Ollama. Used by triage/audit/embed seats. |

### Council audit extensions (W3 + W4 additions)

These are auditor-seat support modules that landed across W3 and W4 to close the small-model reference-resolution gap (F-0.2.17-W2-006 / F-0.2.17-W3-001):

| Module | Source path | W4-close sha256 | Wired by | Contract surface |
|---|---|---|---|---|
| Audit reference extractor | `aho.council.audit_ref_extract` | `src/aho/council/audit_ref_extract.py` | `35bdf5fbe74c37ae90b0e3cb94690739346338ae8d2cba34a19e90d85c3cd116` | W3 D2 | Walks the audit-target artifact and extracts every reference ID matching the carry-forward / ADR / gotcha syntax (`F-N.N.N-W*-NNN`, `ADR-NNNN`, `G\d+`, etc.). Feeds the lookup module. |
| Audit reference lookup | `aho.council.audit_ref_lookup` | `src/aho/council/audit_ref_lookup.py` | `995e43a26b182699967cfc7414df175c7a627dd47ca5b771eebebc27d041d1d3` | W3 D2 | Queries ChromaDB for each extracted ID. Returns `registered` / `unverified` status + `top_source_artifact_path`. Inlined into the audit prompt's `## Registered references` section. |
| Audit finding filter | `aho.council.audit_finding_filter` | `src/aho/council/audit_finding_filter.py` | `67ba8796241ca7ba743bb10e6ac91b79408beb82fb8e70168ca628ab22bcd345` | W4 D1 | Deterministic post-hoc filter. Drops findings whose anchor IDs are listed `registered` AND whose description matches the fake-ID phrase set ('not real', 'looks placeholder', 'matches naming conventions', etc.). Suppresses **only** when both match - does not over-suppress. Filter is structural; does not depend on small-model prompt-following. |

---

## Observation tier

| Module | Source path | W4-close sha256 | Contract surface |
|---|---|---|---|
| OTEL stub helper | `aho._otel_stub` | `src/aho/_otel_stub.py` | `3c1999571aa39614249ebca2aeb45613798742483077cc0ff1ad2e687d7ce334` | Fallback no-op TracerProvider/MeterProvider when otel-sdk imports fail. Allows tests + minimal-deps environments to exercise telemetry call sites without breaking. |
| OTEL aggregator (dashboard side) | `aho.dashboard.otel_aggregator` | `src/aho/dashboard/otel_aggregator.py` | `bd6c06c9cd11701f30412487beccb33d6a4e1a591502a22de69e9f0b7f69bf50` | Reads OTEL metrics jsonl + log streams. Surfaces `/api/otel` for dashboard. AF004/AF005 (api_error_count alias / api_retries_exhausted_count dead field) carry forward. |
| Health server | `aho.health` | `src/aho/health.py` | `119f47d78c42368e3beff774f0e0af16415e4f616e85f97c7ce6392e186e7a42` | k8s-readiness `GET /healthz` (liveness) + `GET /readyz` (tier+secrets+council_imports probes). Default port 8080, env-configurable. |
| Serve entrypoint | `aho.serve` | `src/aho/serve.py` | `ab509b41a21de7067b71e039c0f6fe5d3c8248eeceb7653e14d92e8b23d43067` | Container entrypoint. Tier-detect, council-imports probe, secrets-broker probe, SIGTERM drain. |
| Signal aggregation | `aho.signal` | `src/aho/signal.py` | `94b684271379c5baf1a36b085ada73b2abfca669705df46f3ed9b649697e5ec4` | OTEL signal aggregation surface for dashboard. |
| Audit-disposition emitter | `aho.audit_disposition_emitter` | `src/aho/audit_disposition_emitter.py` | `a3e6df0469fe5183c7ddb7caf410ddf61adec20c5273450b7764cddb3703b2fa` | Same module as process-tier entry; observation-tier role is emitting structured audit dispositions to JSON archive. |
| Gap / carry-forward writer | `aho.gap_carry_forward_writer` | `src/aho/gap_carry_forward_writer.py` | `d0799c8194fa40febb9e873ab87839632fada814727c9b43f535fcf7368bf248` | Same module as process-tier entry; observation-tier role is the durable record of catch-locus events for the materiality protocol. |

### Materiality (W2+)

| Module | Source path | W4-close sha256 | Wired by | Contract surface |
|---|---|---|---|---|
| Materiality counters | `aho.materiality` | `src/aho/materiality.py` | `0ef021e3ee85d5c4390a7d40b19523d874ea84d6bdaeeb56b3f0a31fcac912b8` | W2 D12 | Four-bucket OTEL counter primitive per [ADR-0010](../../artifacts/adrs/0010-materiality-measurement.md). Counter names: `aho.materiality.claim_vs_artifact_mismatches.{caught_by_llama,caught_by_drafter,escaped}`, `aho.materiality.carry_forward_resolution_rate`. |
| Materiality baseline extract | `aho.materiality_baseline_extract` | `src/aho/materiality_baseline_extract.py` | `0fecabc9c73de9148478517e03cc402d8145acd33951a33c7bd654bd76722030` | W2 D12 | Parses OTEL metrics jsonl → per-iteration buckets for dashboard rendering. |

### Retrieval (W2+)

| Module | Source path | W4-close sha256 | Contract surface |
|---|---|---|---|
| RAG entrypoint | `aho.rag` | `src/aho/rag/__init__.py` | `85c1131dad062fb2f22d4d296e44d0b98ad017e44283a494d693bd6d632da401` | RAG layer module surface. ChromaDB persistent client at `AHO_CHROMA_DIR` (default `/var/lib/aho/chroma`; falls back to `~/.local/share/aho/chroma` per F-0.2.17-W2-001). |
| RAG query | `aho.rag.query` | `src/aho/rag/query.py` | `618dee1209871cbd283fb9f4fe79e23a80b036a54fda21c02a78ec55f333e684` | Recency-weighted query API. Sole retrieval surface for triage and audit. |
| RAG archive | `aho.rag.archive` | `src/aho/rag/archive.py` | `b832785b1f158d3a6f7fe247637a9c9651c1b6e4cb355eae4744d9a1e87a37b6` | Index-build path. ChromaDB re-index hook is W6 scope (F-0.2.17-W4-001). |
| RAG router | `aho.rag.router` | `src/aho/rag/router.py` | `04fb0a9c4639ee7822d29d58ae00f5dd23d4213a7272f7d7d8ddc75561005539` | Routes ingest paths into the right collection (iteration-context, harness-base, etc.). |

### Lego brick rendering (claw3d)

| Module | Source path | W4-close sha256 | Contract surface |
|---|---|---|---|
| Brick definitions | `aho.dashboard.lego.bricks` | `src/aho/dashboard/lego/bricks.py` | `35cbb6c1a7ba24762e857e750f98253eac21066be3641d3efd021ed5e5e96fd4` | Per-component brick registry. 10 base-tier bricks per the [claw3d brick spec](claw3d-brick-spec.md). |
| Materiality dashboard surfaces | `aho.dashboard.lego.materiality_surfaces` | `src/aho/dashboard/lego/materiality_surfaces.py` | `9e6b97399c91354c18bc5dfaedc7134f2da607b4340d2e14653a58614fddbd8c` | Four-bucket render surface for the materiality counters. |
| Materiality comparison | `aho.dashboard.lego.materiality_comparison` | `src/aho/dashboard/lego/materiality_comparison.py` | `9038f83119249bbdef14feea10aa5f54efbaf4b5d7b99d68f668bce362f4177b` | Iteration-over-iteration comparison surface for the materiality buckets. |
| Role-collapse trip-wire | `aho.dashboard.lego.role_collapse_brick` | `src/aho/dashboard/lego/role_collapse_brick.py` | `e7b836217e64bf25393214b820ce04422f42924491b4e28971083f7f8f4e7272` | OTEL invariant: `executor_model_family ≠ auditor_model_family`. Brick turns red if collapsed. Pillar 7 falsifiability surface. |
| Anti-rubber-stamp dashboard | `aho.dashboard.lego.anti_rubber_stamp_dashboard` | `src/aho/dashboard/lego/anti_rubber_stamp_dashboard.py` | `04748ce6fac719c776d6a2b66d66db534d025ac3a7aba415ff37044e70e3774c` | Four-surface verification dashboard (W4 D6 update - was three-surface pre-W4). |
| Lego layout | `aho.dashboard.lego.layout` | `src/aho/dashboard/lego/layout.py` | `eee9d5a74c4111cfe172afa24806f7c0efcd8ee4473f4c9d781af11b189e5d50` | Brick layout primitive. |
| Lego renderer | `aho.dashboard.lego.renderer` | `src/aho/dashboard/lego/renderer.py` | `15a06d4de6b8b2abc1743f478c5045e0d809b460339cb129cf42ad200a03cb70` | Brick rendering primitive. |

---

## Host-mounted (not in image)

These resources live on the host filesystem and are bind-mounted into the container at run time. They are not part of the image:

| Resource | Host path (default) | Container mount | Owner |
|---|---|---|---|
| ChromaDB volume | `/var/lib/aho/chroma` (fallback `~/.local/share/aho/chroma`) | `/var/lib/aho/chroma` | Operator. Persists across container restarts. |
| Iteration state volume | `~/.local/share/aho/iteration-state` | `/var/lib/aho/iteration-state` | Operator. Holds checkpoint, recent acceptance archives. |
| Tier config | `/var/run/aho/tier` (per-host, written by tier-detect) | `/var/run/aho/tier` | aho.tier_detect at install or container start. |
| Secrets broker socket | `${XDG_RUNTIME_DIR}/aho-secrets.sock` | `/run/host-services/aho-secrets.sock` (read-only) | Operator's broker process per [ADR-0009](../../artifacts/adrs/0009-secrets-broker-boundary.md). |
| Models bundle | `~/.local/share/aho/models/` | (Ollama model dir bind-mount) | Operator (install.fish does the pull). |

---

## Host-side (not in container)

The host-side broker is a standalone process running on the operator's workstation. Not in the image:

| Module | Source path | W4-close sha256 | Contract surface |
|---|---|---|---|
| Host broker | `aho.host.secrets_broker` | `src/aho/host/secrets_broker.py` | `4cff78274f587e4781663f0755407a4eb8b4a96d839c8a481bdc5273d6171019` | Unix-socket service at `${XDG_RUNTIME_DIR}/aho-secrets.sock` (mode 0600). SO_PEERCRED-authenticated. Single decrypted value per request. JSON line request/response. Logs request shape, never values. Per [ADR-0009](../../artifacts/adrs/0009-secrets-broker-boundary.md). |
| Run-container wrapper | `aho.host.run_container` | `src/aho/host/run_container.py` | `036a267f43772f2da2c5995b0d5c233d8af319fca90505ae254b9963b6856bfd` | `aho host run-container --project P --image I -- <cmd>`. Registers calling UID with broker before `podman run`, mounts broker socket read-only, unregisters on exit. Canonical surface for container invocation; raw `podman run` bypasses registration and broker rejects via SO_PEERCRED. |

---

## Out-of-process model layer

Per [ADR-0008](../../artifacts/adrs/0008-dispatcher-missing-model.md):

- **Hybrid mode (development affordance).** `AHO_DISPATCH_HYBRID_MODE=1` enables container → `host.containers.internal:11434` for partial-tier dispatches. Host's native Ollama serves; container's bundled Ollama untouched. NZXTcos uses this for partial-tier development work during 0.2.17.
- **Production deployment.** `AHO_DISPATCH_HYBRID_MODE` unset. Container's bundled Ollama serves all dispatches at the host's tier bundle. Missing-model requests hard-error with `ModelNotAvailableError`.
- **Cloud serving plane (full tier).** Deferred to 0.3.x. Container's bundled Ollama still serves locally; cloud-tier full bundle pulls from a different model surface. Phase C selection of cloud registry is open.

---

## Cross-reference index

| Concern | ADR / doc |
|---|---|
| Image shape, tier classification, secrets posture, GPU passthrough deferral, council roles | [ADR-0007 - Containerization architecture](../../artifacts/adrs/0007-containerization-architecture.md) |
| Dispatcher behavior on missing model family | [ADR-0008 - Dispatcher behavior on missing model family](../../artifacts/adrs/0008-dispatcher-missing-model.md) |
| Secrets broker boundary (three rules + per-engineer onboarding) | [ADR-0009 - Secrets broker boundary](../../artifacts/adrs/0009-secrets-broker-boundary.md) |
| Materiality measurement protocol (four-bucket + falsifiability threshold) | [ADR-0010 - Materiality measurement protocol](../../artifacts/adrs/0010-materiality-measurement.md) |
| Per-component brick definitions (red conditions, materiality surfaces, role-collapse trip-wire, anti-rubber-stamp dashboard) | [claw3d brick spec](claw3d-brick-spec.md) |
| Eleven Pillars (canonical) | `artifacts/harness/base.md` §The Eleven Pillars |

---

## Provenance

This document is the repo-resident authoritative spec for aho's component decomposition at base tier. It supersedes the chat-side architecture artifact `aho-base-container-architecture.md` §Component decomposition section, which was the working draft that informed 0.2.17 W0–W4 implementation.

The chat-side artifact is **not present in the repository** - it lived as an uploaded-files reference in operator chat sessions during 0.2.17 W0–W4. This doc carries the decomposition forward as the canonical, repo-resident, version-controlled spec.

W5 D7 supersession marker: per the W5 plan-doc, when the chat-side artifact is not in the repo, this Provenance section serves as the supersession path. Future amendments to component decomposition land in this document, not in the chat-side artifact.

Sealed-archive cross-references for verification:

- W0 acceptance archive: sha256 `cd4e3f96b6d4217f275a946be964d38ff78b8acff7cbd683002f84f4463dfebc`.
- W0 amendment B2.3: sha256 `1be983eab9895dc19770f950ac7bbf1992da2ae30a74678bdaf56ebb85457c56`.
- W1 acceptance archive: sha256 `e4d076eec6c1e703635e9befb98bc46c7bf171c7fec3a4c3f64161ec60725a6e`.
- W2 acceptance archive: sha256 `4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`.
- W3 acceptance archive: sha256 `9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`.
- W4 acceptance archive: sha256 `949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`.
- W4 audit archive: sha256 `9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`.
- carry-forwards-0.2.16.md (post-W4-001 append): sha256 `c75e6de5e5ba9ecb860e5313c09a8d81976c185773c8c50ae2e57efdec1cc7ee`.
