# aho

Governance infrastructure for LLM-driven engineering. The harness that does the work.

## Origin

aho began as an extraction. SOC-Foundry builds data and SIEM migration pipelines - moving customer data out of legacy systems into modern databases and SIEMs. We initially built these pipelines using multi-modal LLMs to handle the messy realities of migration: undocumented schemas to interpret, log formats to normalize, business logic to extract, edge cases to reason through.

Then we observed something. Single-agent Claude or Gemini execution against the same large complex projects - using the same multi-modal models - produced materially worse results than what our pipeline tooling produced. We initially attributed this to the pipelines themselves: the scripts, the structured phases, the project-specific logic. Closer inspection showed the difference was elsewhere. The harness around the pipeline - the gotcha registry, the ADR discipline, the drafter-auditor separation, the sealed acceptance archives, the scope hard-stops, the trace-every-decision posture - was doing the work. The pipeline was useful, but the harness was load-bearing.

aho is the extraction of that harness from pipeline-specific contexts into general-purpose governed agentic engineering infrastructure. The thesis: richer harnesses produce smarter behavior from the same models. Same Claude, same Gemini, materially different output, because the scaffolding around them is structured rather than vibes-based.

## What aho is

aho is governance infrastructure for LLM-driven engineering. The four properties that make it that, rather than another agent framework:

- **Drafter / executor / auditor / operator separation as a structural constraint.** Adversarial Authorship contract: the agent that drafts cannot execute; the agent that executes cannot bless its own work; a separate auditor adjudicates against sealed evidence; a human signs.
- **Provable lineage of every dispatch.** W3C TRACEPARENT propagation through the stack means every LLM call is attributable to its workstream, iteration, drafter session, and parent operation. Cost, tokens, errors, decisions all traceable.
- **Monitored invariants enforced as policy.** Pillar 11 (no agent git operations) is the prototype. Future invariants extend the same pattern. Policy as gate, not dashboard.
- **Sealed acceptance and audit archives, immutable event log.** The artifacts are the record. They cannot be retroactively edited. Disputes resolve by reading the archive, not by re-asking the agent.

The combination - and the compliance-shaped framing - is the differentiator. Agent orchestrators (LangChain, AutoGen, CrewAI), observability platforms (LangSmith, Langfuse, Helicone, Phoenix), eval platforms (Braintrust, Promptfoo), and IDE-embedded agents (Cursor, Claude Code) each cover one corner of this surface. None build governance.

## Status (0.3.1 in flight)

- **Current iteration:** 0.3.1, seven workstreams. W0 closed (documentary substrate + ADR placements + CLAUDE.md rewrite). W1 closed (substrate freshness, 13-fact telemetry, ChromaDB bootstrap, `bin/aho-doctor`, idempotent `install.fish`). W2–W7 remaining.
- **Latest closed iteration:** 0.2.18 (image rebuild + 0.2.17 carry-forward closures). Container image `ghcr.io/soc-foundry/aho:0.2.18`.
- **Auditor primitive:** in-container `llama3.2:3b` at base tier with W3-0.2.17 RAG enrichment + W4-0.2.17 deterministic post-hoc filter + W0-0.2.18 anti-rubber-stamp extensions. Seven deployments to date; bootstrap test 11 in the architecture progression. **First non-vacuous filter-eligibility check** at 0.3.1 W1 D8 - RAG enrichment `registered_count=20` of 28 detected refs against the populated ChromaDB collection (vs 0/26 at 0.3.1 W0 D9 with empty collection). W4-0.2.17 filter regression check passes non-vacuously.
- **Materiality status:** N=5 below the N≥8 threshold per ADR-0010 - **qualified validation, not full validation**.
- **Partial-tier auditor seat:** `qwen3.5:9b` planned for partial-tier host deployment at 0.3.1 W3.
- **Substrate freshness:** ADR-0011 lightweight tier shipped at W1 of 0.3.1. 13 substrate facts emit `aho.observable.last_verified_age_seconds` OTEL gauge. Dashboard brick grid at `/substrate`.

## Why aho - cost and token utilization

Token cost matters. Claude and Gemini API spend at scale is the dominant operating cost of LLM-driven engineering, and single-agent execution wastes it in characteristic ways:

- **Cache underutilization.** Single-agent sessions rebuild context each invocation. aho's iteration model - fixed CLAUDE.md system prompt, persistent registries, sealed checkpoints - turns context into a cache asset. The Pillar 8 dashboard tracks this directly: cache:new ratios sustained across workstreams that single-agent execution structurally cannot match.
- **No model-cost gradient.** Single-agent execution sends every decision to the same expensive model. Routing, classification, triage, substantive reasoning, and architectural decisions all priced identically. aho's council pattern routes triage and classification to small local models (Nemotron-class), substantive work to mid-tier (Qwen, GLM), audit to a confidence-floor-locked llama seat, premium dispatches to Claude or Gemini. The cost gradient is visible per-workstream.
- **Re-execution waste from undetected drift.** Single-agent failure modes - hallucinated state, stale assumptions, lost context, mid-task looping - are wasted tokens compounded by downstream tokens built on bad foundations. aho's halt-on-fail discipline plus Adversarial Authorship audit catches drift at bucket boundaries, before downstream waste accumulates.
- **Scope creep priced as features.** Single-agent execution under "do this large complex thing" expands scope as it works. aho's no-mid-flight-scope-amendment rule keeps tokens on the requested scope.

These are mechanism claims, not benchmark claims. The mechanisms compound across iterations.

## The Pillars

aho's operating principles. Numbered, named, and binding. Pillars 1–11 from `artifacts/harness/base.md`; Pillars 12 + 13 land formally at W6 of 0.3.1.

1. **Delegate everything delegable.** The paid orchestrator decides; the local free fleet executes.
2. **The harness is the contract.** Agent instructions live in versioned harness files, not model context.
3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out.
4. **Wrappers are the tool surface.** Every tool is invoked through a `/bin` wrapper.
5. **Three octets, three meanings: phase, iteration, run.** Strategic, tactical, and execution scope.
6. **Transitions are durable.** State is written to a durable artifact before any transition.
7. **Generation and evaluation are separate roles.** Drafter and reviewer are different agents.
8. **Efficacy is measured in cost delta.** Wall clock, token cost, and delegate ratio are ground truth.
9. **The gotcha registry is the harness's memory.** Failure modes are indexed with mitigations.
10. **Runs are interrupt-disciplined.** No preference prompts mid-run; only capability gaps halt. _**W6 amendment** clarifies: capability gap = information only the operator can provide. Missing-but-installable substrate components are NOT capability gaps - install and proceed._
11. **The human holds the keys.** No agent writes to git. _**W6 amendment** narrows scope to git operations only, plus a small operator-only host-action list (secret decryption, /etc/sudoers, hardware procurement, disruptive reboots). Substrate component installation is executor scope._
12. **Substrate is probed, never assumed.** Every workstream's first deliverable verifies required substrate components via `install.fish --check` (idempotent end-to-end) or `bin/aho-doctor`. Inheritance of substrate state from prior iterations or sibling hosts is not assumed; it is measured. _New at W6 of 0.3.1._
13. **Hosts are fungible.** The substrate exists to be rebuilt. Artifacts and registries are durable; host machines are not. The harness does not gate on host-preservation concerns; idempotent `install.fish` + sealed archives + gotcha registry persist across host rebuilds. _New at W6 of 0.3.1._

Each pillar is enforced by tooling, registry entries, or both. Pillar violations are findings; repeated violations are gotcha registry entries with mitigations.

### Operating contract: bold-when-clear, escalate-when-ambiguous

Codified as binding operational discipline alongside Pillars 10/11:

- When the path is clear (substrate gap with established remediation, well-defined deliverable, unambiguous arbitration option), executor proceeds with bold judgment
- When the situation is genuinely ambiguous (multiple paths with materially different outcomes, architectural decisions requiring operator input, scope expansions beyond plan-doc), executor halts-and-surfaces
- Reflexive arbitration on clear-path situations is a failure mode that wastes operator tokens and breaks iteration momentum
- Drafter reciprocally commits to not manufacturing ambiguity where execution is obvious

## Architecture - current shape

aho today runs across an engineer fleet over Tailscale, no public-internet exposure. Per-host deployment via `install.fish` (19 steps; check-first / remediate-on-fail / re-check semantics; structured per-step JSON output at `~/.local/share/aho/install-state.jsonl` since 0.3.1 W1).

### Fleet topology

Hosts are typed by capacity tier (base / partial / full per ADR-0007), substrate (consumer-iGPU / consumer-dGPU / workstation-dGPU / datacenter-dGPU; ADR-0007 amendment), and attestation tier (unattested / SEV-SNP-attested; ADR-0012). 0.3.1 deploys to a mix of base-tier and partial-tier hosts across CachyOS x86_64 substrate; all hosts enrolled on the same Tailscale tailnet.

### In-container (`ghcr.io/soc-foundry/aho:0.2.18`)

- **aho harness** - Adversarial Authorship state machine, dispatcher (model selection and routing per `MODEL_FAMILY_CONFIG` longest-prefix match), router (classification primitive at `aho.pipeline.router`), acceptance and audit archive writers. Stateful per active iteration.
- **aho.serve** - `aho serve` entrypoint: ready-and-waiting mode with health endpoints on port 8080.
- **aho.tier_detect** - VRAM probe at startup; classifies host as `base` / `partial` / `full` per ADR-0007 thresholds.
- **aho.secrets_client** - host-broker round-trip via unix socket at `$XDG_RUNTIME_DIR/aho-secrets.sock` (canonical XDG path per ADR-0009 amendment in W6 of 0.3.1). No credential material in image layers.
- **aho.council** - in-container fleet wiring: `audit` (llama3.2:3b auditor at base tier; qwen3.5:9b at partial tier), `triage` (nemotron-mini:4b, classification only), `embed` (nomic-embed-text via Ollama), `audit_ref_extract` + `audit_ref_lookup` (RAG enrichment), `audit_finding_filter` (deterministic post-hoc filter on findings; W0-0.2.18 anti-rubber-stamp extensions).
- **aho.rag** - retrieval primitive against host-mounted ChromaDB volume at `/var/lib/aho/chroma` (fallback `~/.local/share/aho/chroma`); recency-weighted similarity ranking; chunked indexing via `index_artifact` (upsert; idempotent).
- **aho.rag.bootstrap** _(new in 0.3.1 W1)_ - `aho rag bootstrap` ingests the canonical artifact set (carry-forwards files, plan-docs, close notes, iteration-close notes, ADRs, retrospectives) into the per-project iteration-context collection. Subcommands: `--dry-run` / `--rebuild` / `--json` / `--quiet`.
- **aho.gap_carry_forward_writer** - append-to-carry-forwards primitive with auto re-index hook (W6-of-0.2.17 D2 closure of F-0.2.17-W4-001).
- **aho.materiality** - four-bucket OTEL counter primitives per ADR-0010.
- **aho.observability** _(new in 0.3.1 W1)_ - substrate-freshness telemetry API: `record_observable`, `last_verified_age_seconds`, `warning_age_seconds`, `fact_color` (green/yellow/red cascade), `snapshot_all_facts`. Append-only log at `~/.local/share/aho/observables.jsonl`. OTEL gauge `aho.observable.last_verified_age_seconds` with attrs `{fact_id, host, project}`.
- **aho.substrate_probes** _(new in 0.3.1 W1)_ - 13-fact probe registry. Cross-host probes via Tailscale ssh; `host_unreachable` is a distinct outcome class.

### Host-side

- **aho.host.secrets_broker** - long-running unix-socket broker on `$XDG_RUNTIME_DIR/aho-secrets.sock`. SO_PEERCRED authentication; per-UID project-label registration; never returns secret values to unauthorized callers.
- **aho.host.run_container** - wrapper that registers a UID with the broker, runs `podman run` with the broker socket bind-mounted, and unregisters on exit. The canonical entrypoint for engineer-side container invocations.
- **age + fernet secret store** - age handles per-machine identity (X25519); fernet handles bulk encrypted secret storage (AES-128). OS keyring caches the passphrase between sessions.
- **`install.fish`** _(rebuilt at 0.3.1 W1)_ - 19-step idempotent orchestrator. Every step's check-first / remediate-on-fail / re-check / report-final-status sequence. Structured JSON per step to `~/.local/share/aho/install-state.jsonl`. Flags: `--check` (read-only probe of every step, no mutations), `--step <step_id>` (surgical re-run of one step). Backward-compatible with legacy `~/.local/state/aho/install.state` key=value step file.
- **`bin/aho-doctor`** _(new in 0.3.1 W1)_ - per-workstream pre-flight gateway. Invokes `install.fish --check`, parses per-step JSONL, evaluates required-steps list for the calling workstream, exits 0 if all pass / 1 if any fail / 2 if substrate gap upstream / 3 if unknown workstream. `--remediate` cascade.
- **`bin/aho-probe-substrate`** _(new in 0.3.1 W1)_ - fish wrapper invoking the 13-fact probe set; `--fact` / `--host` / `--summary`. Cross-host via Tailscale ssh.
- **`bin/aho-rag-bootstrap`** _(new in 0.3.1 W1)_ - fish wrapper for `aho.rag.bootstrap`.
- **OTEL collector** - local-collector pattern with central aggregation over Tailscale.
- **claw3d dashboard** at `localhost:7800`: components, daemon health, Pillar 8 cost/token telemetry, materiality dashboard, role-collapse tripwire, anti-rubber-stamp dashboard, **substrate-freshness brick grid** at `/substrate` (13-fact green/yellow/red cascade + stale-count summary tile; `/api/substrate` JSON endpoint).
- **`aho-harness-watcher`, `aho-nemoclaw`, `aho-openclaw`, `aho-telegram`, `aho-jaeger`** - daemon services for harness monitoring, classifier orchestration, dispatcher orchestration, notification fan-out (Pillar 11 alert channel separate since 0.2.16 W3), trace viewing.
- **Ollama** - local model runtime serving the in-container fleet via `host.containers.internal:11434` (per ADR-0008 hybrid mode).

### State on disk

- **`.aho-checkpoint.json`** - Adversarial Authorship state machine, single source of truth for iteration progression. Lives at canonical project root; written by `install.fish` step `canonical_checkpoint_present` since 0.3.1 W1.
- **`artifacts/iterations/{version}/`** - sealed acceptance archives, audit archives, plan/design docs, bundles, evidence, close notes.
- **`artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`** - canonical cross-iteration ledger; mutated only via `aho.gap_carry_forward_writer.append_to_file`.
- **`artifacts/adrs/`** - versioned architectural decision records, sequential from disk enumeration. At 0.3.1 W1: ADR-0001 through ADR-0012 (with ADR-0011 substrate freshness + ADR-0012 Chain of Trust L5 added at 0.3.1 W0).
- **`docs/architecture/`, `docs/retrospectives/`** - repo-resident architecture docs and iteration retrospectives.
- **`~/.local/share/aho/events/aho_event_log.jsonl`** - immutable append-only event ledger.
- **`~/.local/share/aho/observables.jsonl`** _(new in 0.3.1 W1)_ - append-only substrate-freshness probe log.
- **`~/.local/share/aho/install-state.jsonl`** _(new in 0.3.1 W1)_ - append-only per-step install.fish structured output.
- **`/var/lib/aho/chroma`** (or `~/.local/share/aho/chroma` fallback) - ChromaDB persistent collection. Populated via `aho rag bootstrap`; queryable via `aho.rag.query` with recency-weighted ranking.

## Architecture - target shape

Three-tier deployment model. The harness lives at the edge with each engineer; heavy compute lives centrally; the truth layer is managed storage.

### Tier 1: engineer workstation (containerized)

Runs locally on every engineer's host. Distributed as signed container images.

- **aho-harness** - Adversarial Authorship state machine, dispatcher, router, archive writers. Stateful per active iteration. **Shipping.**
- **Local OTel collector** - `otel/opentelemetry-collector-contrib` batching, buffering, forwarding to central aggregator over Tailscale. Hub-and-spoke topology (not single canonical aggregator; not full peer mesh) for resilience to central outages and engineer offline scenarios.
- **aho-dashboard-local** - claw3d for this engineer's iterations, port 7800. Includes substrate-freshness brick grid.
- **aho-harness-watcher** - daemon monitoring local harness state, emitting events.
- **Engineer-local secret store** - age identity, fernet-encrypted local secret bundle. Container reads via broker per ADR-0009.

### Tier 2: central serving plane

- **Central OTel aggregator** - self-hosted OpenTelemetry aggregation platform; FastAPI + TimescaleDB; receives from all engineer-local collectors. Standing up during 0.3.1 W2.
- **Central Firestore** - gotcha registry entries, audit dispositions, materiality counter, substrate-freshness telemetry, pipeline outputs, attribution mappings. Multi-tenant data writer ships at 0.3.1 W2; same image runs in any tenant deployment, configuration is the boundary.
- **inference-gateway** _(future, post-0.3.x)_ - per-tenant routing, Pillar 11 admission gating, TRACEPARENT propagation crossing engineer-to-backend boundary, audit log emission for every model call.
- **vllm pods, api-proxy, audit-dispatcher, embedding-service, batch-worker-pool** _(future, post-0.3.x)_ - Kubernetes-with-GPU workload for high-throughput council dispatches.

### Tier 3: per-tenant isolation

aho's multi-tenant model places each tenant's mutable data inside its own GCP project boundary. Shared across tenants (codebase, OCI images, schema conventions, gotcha-registry shape, anonymized cross-engagement learnings). Isolated per tenant (Firestore instance, gotcha registry entries, audit dispositions, materiality counter, substrate-freshness telemetry, pipeline outputs, attribution mappings).

Same image runs in any tenant deployment; tenant scoping is env-var-driven (`AHO_TENANT_ID`, tenant Firestore project, tenant aggregator endpoint). Tenant project boundary is a stronger isolation guarantee than row-level security; tenant audit-of-own-data is uncomplicated; per-tenant aggregator deployment matches the project-codename pattern uniformly.

## Telemetry architecture

### Hub-and-spoke topology

Each engineer's home lab runs a local `otel/opentelemetry-collector-contrib` collector. Local collector batches, buffers, forwards to a central aggregator over Tailscale.

Why hub-and-spoke:

- **Resilience to central outages** - local collector retains telemetry until central is reachable; no data loss when aggregator is down
- **Resilience to engineer offline** - buffered delivery when engineer reconnects
- **Per-engineer debuggability** - engineer queries their own local collector without round-tripping to central
- **Per-tenant isolation** - tenant aggregator deployment matches the project-codename pattern uniformly; cross-tenant data does not co-mingle

### Identity attribution via OTel resource attributes

Added at the local-collector level:

- `service.name`: aho component
- `host.name`: per-host short identifier
- `engineer.id`: per-engineer identifier
- `lab.subnet`: per-engineer subnet (matches subnet plan)
- `deployment.environment`: dev / partial / full
- `tier`: base / partial / full
- `tenant.id`: per-tenant identifier

Central aggregator's TimescaleDB indexes on these attributes. Grafana dashboards filter and aggregate by them.

## Components in detail

### The harness

The harness is the contract between operator, drafter, executor, and auditor. It enforces Adversarial Authorship state transitions, validates dispatch parameters, parses TRACEPARENT, creates spans, writes acceptance and audit archives, and refuses operations that violate Pillars (notably 11). The harness is not a library called from agent code; the harness invokes agents.

### The four roles (Adversarial Authorship)

- **Drafter** - external, persistent across chat sessions. Currently Claude (web project folder). Authors plan-docs, executor prompts, arbitrates auditor disposition pre-sign.
- **Executor** - external, per-iteration. Claude Code or Gemini CLI. Reads the plan-doc, executes the workstream scope, writes the acceptance archive, runs the self-audit probe, halts.
- **Auditor** - in-container, per tier: `llama3.2:3b` at base tier; `qwen3.5:9b` at partial tier (from 0.3.1 W3). RAG enrichment + W4-0.2.17 deterministic post-hoc filter + W0-0.2.18 anti-rubber-stamp extensions.
- **Operator** - human. Signs close notes; rotates secrets; **runs all git operations** (Pillar 11); manages hardware-side actions.

### The registries

- **Gotcha registry** - indexed failure modes with mitigations. Each entry numbered (e.g., `G001`); entries persist across iterations and projects.
- **Script registry** - sanctioned tool surface per Pillar 4.
- **ADR index** - architectural decision records numbered sequentially from disk enumeration. At 0.3.1 W1: ADR-0001 through ADR-0012.

In current shape: version-controlled files in the repo. In target shape: Firestore-backed APIs with Pub/Sub fan-out for change notification.

### The dispatcher and router

The dispatcher (`src/aho/pipeline/dispatcher.py`) selects a model family and routes the dispatch to the appropriate backend. `MODEL_FAMILY_CONFIG` resolves family by longest-prefix match. Ollama state hygiene primitives (`unload_model()`, `list_loaded_models()`, `ensure_model_ready()`) are first-class.

The router (`src/aho/pipeline/router.py`) is the canonical classification primitive.

### Adversarial Authorship state machine

Five states per workstream: `not_started`, `in_progress`, `pending_audit`, `audit_complete`, `workstream_complete`. Plus a transient `blocked` vertex on halt-and-surface conditions. Transitions are durable per Pillar 6 - checkpoint file written before any state transition emits its event. Executor cannot transition past `pending_audit`; only the auditor's archive (read by a fresh drafter session) authorizes `workstream_complete`.

### OTEL telemetry and TRACEPARENT propagation

Every dispatch produces traces, metrics, and logs tagged with iteration, workstream, and role. TRACEPARENT propagates through the dispatch chain. Pillar 8 dashboard aggregates by workstream.

Required env (set by managed `.claude/settings.json`):

```
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_LOG_USER_PROMPTS=1
OTEL_LOG_TOOL_CONTENT=1
OTEL_RESOURCE_ATTRIBUTES=service.name=claude-code,aho.iteration=${AHO_ITERATION},aho.workstream=${AHO_WORKSTREAM},aho.role=drafter
```

### Substrate-freshness telemetry (ADR-0011 lightweight tier, new in 0.3.1 W1)

13 substrate facts emit `aho.observable.last_verified_age_seconds` OTEL gauge with attrs `{fact_id, host, project}`. Per-fact `warning_age_seconds` calibration. Three-color cascade (green if fresh; yellow at 1-3× warning; red at >3× OR never probed). Dashboard brick grid renders the 13 facts + summary tile (stale_count).

| Fact | Default warning | Locality |
|---|---|---|
| `tailnet_domain` | 30 days | per-host |
| `otel_collector_endpoint` | 1 hour | per-host |
| `image_fqdn` | 7 days | per-host |
| `ssh_host_keys` | 90 days | per-host |
| `podman_version` | 14 days | per-host |
| `broker_socket` | 1 hour | per-host |
| `chromadb_mount_path` | 30 days | per-host |
| `ollama_api_endpoint` | 1 hour | per-host |
| `onepassword_agent_socket` | 1 hour | per-host |
| `cloudflarewarp_dns` | 1 hour | per-host |
| `chromadb_doc_count` | 30 minutes | local-only |
| `checkpoint_mtime` | 24 hours | local-only |
| `sys_path_clean` | 1 hour | local-only |

Cross-host probes via Tailscale ssh; `host_unreachable` is a distinct outcome class.

### The Pillar 8 cost and token dashboard

claw3d-fronted Flutter dashboard reads from the OTEL aggregator and serves per-workstream and per-iteration cost rollups, token totals, cache:new ratios, turn counts, tool-call counts, MCP event counts, and error counts. The cost gradient is visible per-dispatch.

### The materiality protocol (ADR-0010)

Four OTEL counters with falsifiable thresholds:

- `aho.materiality.claim_vs_artifact_mismatches.caught_by_llama`
- `aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter`
- `aho.materiality.claim_vs_artifact_mismatches.escaped`
- `aho.materiality.carry_forward_resolution_rate`

ADR-0010 specifies N≥8 iterations, ≥30% reduction in escaped defects vs baseline, non-zero `caught_by_llama` AND non-zero `caught_by_drafter`, carry-forward resolution rate ≥60% within 2 iterations. **At 0.3.1 W1 close: N=5 - qualified validation, not full validation.**

### The anti-rubber-stamp surfaces

Anti-rubber-stamp hardening operates on multiple surfaces, extended in 0.2.18 W0:

1. **`nemotron_raise_on_malformed`** - triage primitive raises rather than silently degrading on malformed model output (G083 discipline).
2. **`llama_confidence_floor_lock`** - auditor `clean` disposition is structurally unreachable below confidence 0.85; locked to `surface_to_drafter` instead.
3. **`role_collapse_tripwire`** - detection of generation/evaluation role collapse across drafter / auditor sessions.
4. **`deterministic_post_hoc_filter`** - W4-of-0.2.17 D1 filter: drops findings only where BOTH a registered anchor appears in the description AND a fake-ID phrase matches. Structurally narrow.
5. **`_GIT_OP_ENFORCEMENT_SENTINELS`** - context-window suppression of git-op false positives on enforcement narration (W0-0.2.18 closure).
6. **`_RAG_STATUS_ECHO_PATTERN`** - RAG status echo suppression (W0-0.2.18 closure).
7. **`unsupported_halt_downgrade`** - halt disposition downgraded to `surface_to_drafter` when all model findings filter-suppressed (W0-0.2.18 closure).

### Secrets broker boundary (ADR-0009)

Three rules verbatim:

1. No credential material in image layers ever.
2. Per-user secret access via host-side broker.
3. No SSH agent socket forwarded.

The broker is the only path from in-container code to host-stored secrets. **W6 of 0.3.1 ADR-0009 amendment** canonicalizes the broker socket path to `$XDG_RUNTIME_DIR/aho-secrets.sock`.

`aho secrets-test` returns SHA-256 fingerprints (first 8 hex + length), never raw values.

### Three-axis tier model (ADR-0007 amendment at W6 of 0.3.1)

Replaces single-axis VRAM-only tier with three orthogonal axes:

1. **Capacity tier** (VRAM-based): base (<12GB) / partial (12-32GB) / full (≥32GB or multi-GPU)
2. **Substrate tier** (inference performance): consumer-iGPU / consumer-dGPU / workstation-dGPU / datacenter-dGPU
3. **Attestation tier** (per ADR-0012): unattested (current) / SEV-SNP-attested (long-arc end state; deferred to 0.4.x+)

Naming the orthogonality prevents conflation. A deployment can move along any axis independently.

## Council architecture

### Per-tier auditor seat

- **Base tier hosts:** `llama3.2:3b` in-container auditor with RAG enrichment + W4-0.2.17 deterministic post-hoc filter + W0-0.2.18 anti-rubber-stamp extensions
- **Partial tier hosts:** `qwen3.5:9b` in-container auditor (deployed at 0.3.1 W3; replaces llama3.2:3b for higher-consistency partial-tier audit)
- **Full tier hosts:** deferred to 0.4.x+

### Council model bundle per tier

| Tier | Auditor seat | Embedding seat | Substantive work | Multimodal |
|---|---|---|---|---|
| **base** | `llama3.2:3b` | `nomic-embed-text` | - | - |
| **partial** | `qwen3.5:9b` | `nomic-embed-text` | `qwen3.5:9b` | `GLM-4.6V-Flash-9B` |
| **full** | TBD | TBD | nemotron-42B candidate | TBD |

## Iteration model

### 0.3.1 (in flight)

Seven workstreams. Focus: substrate freshness telemetry, ChromaDB bootstrap, install.fish idempotency hardening, aho-doctor wrapper, partial-tier deployment, central OTel aggregator integration, ADR consolidation.

- **W0 ✅** documentary substrate (plan-doc + ADR-0011 + ADR-0012 + CLAUDE.md rewrite + carry-forward fold-in)
- **W1 ✅** substrate hardening + bootstrap (install.fish 19-step idempotent; aho-rag-bootstrap; aho-doctor; 13-fact telemetry; dashboard brick grid; tests)
- **W2** install.fish tier-aware refactor + central OTel aggregator integration + multi-tenant Firestore writer
- **W3** council-mining retrospective (classify the artifact corpus into four quadrants, produce augmented gotcha registry)
- **W4** Firestore schema dry-run
- **W5** repo-resident docs reframing (Chain of Trust L5, multi-host deployment, identity discipline)
- **W6** ADR consolidation + Pillar 10/11 amendments + new Pillars 12+13 + harness/base.md version-bump
- **W7** final closures + iteration-final self-audit + iteration-close note

### 0.3.2

Two terminal deliverables:

1. **Central deployment** - populate Firestore with current aho substrate state, write OCI image pointers, stand up central OTel aggregator
2. **Partial container image** - cut from partial-tier host with `qwen3.5:9b` + `nomic-embed-text` + `GLM-4.6V-Flash-9B` baked in; tagged at ghcr.io

### 0.3.3+

First non-internal tenant onboarding. Synthetic-first (internal engineer's home lab as synthetic-isolated tenant) or production-first (first real tenant). Per-engineer onboarding gets a documented runbook: install.fish + tier.json + local collector + per-engineer attribution + identity discipline lane setup.

### 0.4.x+ (charter-level rework, deferred)

- AMD SEV-SNP attestation chain (requires EPYC-class silicon)
- 1Password Connect substrate substitution (gating on SEV-SNP attestation)
- Kyverno admission controllers (requires Kubernetes; full-tier cloud deployment)
- Full L5 hardening invariants (read-only root, cap_drop ALL, SHA256 pinning enforced via Kyverno)
- aho-quantum mid-tier (`aho posture` subcommand, wave-packet visualization for substrate-freshness decoherence)
- aho-quantum full-tier (coherence-driven iteration close)

## Repo layout

```
aho/
├── src/aho/                    # Python package (src-layout)
│   ├── pipeline/               # Cascade: dispatcher, router, orchestrator, schemas
│   ├── council/                # In-container fleet: audit, triage, embed,
│   │                           # audit_finding_filter, audit_ref_extract,
│   │                           # audit_ref_lookup, status, dispatch
│   ├── host/                   # Host-side primitives: secrets_broker, run_container
│   ├── claw3d/                 # Dashboard: server, aggregator, lego bricks,
│   │                           # substrate_panel (new 0.3.1 W1)
│   ├── alerts/                 # Pillar 11 alert fan-out
│   ├── rag/                    # Retrieval (nomic-embed-text, ChromaDB, recency-weighted)
│   │   └── bootstrap.py        # Canonical-artifact-set ingestion (new 0.3.1 W1)
│   ├── secrets/                # Host-side age + fernet store
│   ├── telegram/               # Notification fan-out
│   ├── components/             # Component coverage tracking
│   ├── preflight/, postflight/ # Pre/post-execution gates
│   ├── install/                # Install-time orchestration logic
│   ├── observability.py        # Substrate-freshness telemetry (new 0.3.1 W1)
│   ├── substrate_probes.py     # 13-fact probe registry (new 0.3.1 W1)
│   ├── cli.py, serve.py        # CLI dispatcher + container ready mode
│   ├── tier_detect.py          # VRAM-based tier classification
│   ├── secrets_client.py       # Container-side broker round-trip
│   ├── workstream_events.py    # Workstream lifecycle event emitter
│   ├── workstream_gate.py      # State transition gating
│   ├── audit_disposition_emitter.py
│   ├── gap_carry_forward_writer.py
│   ├── materiality.py          # Four-bucket OTEL counter (ADR-0010)
│   └── ...
├── bin/                        # CLI entry points + tool wrappers (Pillar 4)
│   ├── aho-doctor              # Per-workstream pre-flight gateway (new 0.3.1 W1)
│   ├── aho-rag-bootstrap       # Canonical-artifact bootstrap (new 0.3.1 W1)
│   ├── aho-probe-substrate     # 13-fact probe runner (new 0.3.1 W1)
│   ├── aho-claw3d              # Dashboard server
│   ├── aho-pacman, aho-aur, aho-python, aho-models, aho-secrets-init,
│   │   aho-mcp, aho-systemd    # Install-step wrappers
│   └── ...
├── containers/                 # Container build context
├── Dockerfile                  # Multistage Python 3.14-slim image
├── .dockerignore               # Working-state exclusion list (canonical)
├── artifacts/
│   ├── harness/                # Pillars (base.md), Adversarial Authorship protocol,
│   │                           # prompt conventions
│   ├── adrs/                   # 0001 through 0012 at 0.3.1 W1
│   ├── iterations/             # Per-iteration: plan, acceptance, audit, close note
│   ├── observability/          # Architecture notes
│   ├── phase-charters/, roadmap/, scripts/, prompts/, templates/
│   └── tests/                  # Verification suite
├── docs/                       # Repo-resident documentation
│   ├── architecture/           # component-decomposition.md + claw3d-brick-spec.md
│   └── retrospectives/         # Per-iteration retrospectives
├── data/                       # Registries, event log mirrors
├── tests/                      # Top-level test suite
├── web/                        # Dashboard web assets (claw3d)
├── CLAUDE.md                   # Drafter/executor (Claude Code) operating instructions
├── GEMINI.md                   # External-audit-slot operating instructions
├── CHANGELOG.md                # Iteration history
├── COMPATIBILITY.md            # Supported environments
├── MANIFEST.json               # Repo-level manifest
├── .aho-checkpoint.json        # State machine current state
└── install.fish                # Idempotent 19-step orchestrator (rewritten 0.3.1 W1)
```

Path-agnostic via `aho.paths.find_project_root()` and the `.aho.json` sentinel.

## Getting started

### Fresh-box host bootstrap

```fish
git clone git@github.com:SOC-Foundry/aho.git ~/path/to/aho
cd ~/path/to/aho
./install.fish
```

`install.fish` is idempotent. Re-running on a healthy host completes in seconds with all steps reporting `satisfied`. On drift, it remediates and re-checks. Read-only debugging:

```fish
./install.fish --check                       # probe every step, no mutations
./install.fish --step canonical_checkpoint_present   # surgical re-run of one step
```

Per-workstream pre-flight:

```fish
aho-doctor --workstream W1            # plain output
aho-doctor --workstream W2 --json     # machine-readable
aho-doctor --workstream W2 --remediate   # invoke install.fish --step <id> on failures
```

### Container-side workloads (post-bootstrap)

```fish
# pull the published image
gh auth token | podman login ghcr.io -u <github-username> --password-stdin
podman pull ghcr.io/soc-foundry/aho:0.2.18

# run a workload through the host-side run-container wrapper
# (registers UID with broker, mounts socket, runs command, unregisters on exit)
aho host run-container --image ghcr.io/soc-foundry/aho:0.2.18 \
  -- secrets-test <project> <secret-name>
```

The `gh auth token | podman login` pattern is the canonical credential refresh - podman's auth store at `~/.config/containers/auth.json` is independent of gh CLI's token store.

### Bootstrap the per-project ChromaDB collection

After fresh install, the per-project iteration-context collection starts empty. Bootstrap from the canonical artifact set:

```fish
aho-rag-bootstrap --dry-run        # report planned shape (~50 artifacts, ~270 chunks)
aho-rag-bootstrap                  # execute (~3 min on CPU-only inference)
aho-rag-bootstrap --rebuild        # drop collection + re-ingest (escape hatch)
```

`install.fish` step `chromadb_collection_populated` invokes the bootstrap automatically when the collection is empty.

### Requirements

- Arch Linux family (CachyOS tested)
- Python 3.14
- fish shell (primary; non-fish shells are not supported)
- Ollama (installed via upstream script, not pacman)
- Podman 4.0+ (rootless mode supported; pasta networking with `iif lo` nft rule for in-container→host Ollama traffic)
- chromadb (install via `pip install --user --break-system-packages chromadb` - install.fish step `chromadb_importable` remediates)
- pytest (test runtime; `pip install --user --break-system-packages pytest`)
- 8GB+ VRAM for the local council at base tier:
  - `llama3.2:3b` (auditor, ~2GB)
  - `nomic-embed-text` (retrieval embedding, ~270MB)
- 12-16GB+ VRAM for partial tier:
  - `qwen3.5:9b` (auditor + substantive work, ~6GB)
  - `nomic-embed-text` (retrieval embedding, ~270MB)
  - `GLM-4.6V-Flash-9B` (multimodal, partial-tier candidate)
- systemd user services with linger enabled
- Tailscale tailnet enrollment
- 1Password CLI + `~/.1password/agent.sock` for identity discipline

### Configuration

- **Orchestrator config** at `~/.config/aho/orchestrator.json`
- **Tier manifest** at `~/.config/aho/tier.json`: written by `install.fish` step `tier_json_present`; `{host_id, tier, deployment_mode, families, bundle, rationale, vram_gb}`. W2 of 0.3.1 expands to `aho install tier-manifest` subcommand
- **MCP servers** wired via per-project `.mcp.json` generated from template at bootstrap. Smoke-tested via `bin/aho-mcp smoke`
- **Secrets** initialized via `bin/aho-secrets-init`. age keygen per-machine, fernet-encrypted storage, OS keyring caches passphrase
- **Tenant config** (forward-looking, W2 of 0.3.1): `AHO_TENANT_ID`, `AHO_TENANT_FIRESTORE_PROJECT`, `AHO_TENANT_BEACON_ENDPOINT` - same image runs in any tenant deployment; configuration is the boundary
- **Container env** (set by managed `.claude/settings.json`): see §OTEL telemetry and TRACEPARENT propagation above
- **Substrate-freshness probe** runs via `aho-probe-substrate --summary`; install.fish step `substrate_facts_probed_recently` invokes it when observables.jsonl mtime > 24h

## Contributing

Pillar 11 governs (amended at W6 of 0.3.1, narrowed to git operations only):

- Agents do not write to git, do not push container images without explicit operator authorization, do not run `gh pr create/merge`
- Substrate component installation IS executor scope (corrected from pre-0.3.1 over-broad reading)
- All commits are human-authored
- PRs are welcome from human contributors
- Agent-assisted drafting is expected and encouraged; agent-direct git operations are not

The drafter / executor / auditor / operator separation is structural; contributions that obscure or weaken it are out of scope.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full iteration history back to 0.1.0-alpha.

Per-iteration close notes live alongside the sealed acceptance and audit archives under [`artifacts/iterations/{version}/`](artifacts/iterations/). Canonical iteration retrospectives at [`docs/retrospectives/`](docs/retrospectives/).

## License

License to be determined before v0.6.0 release.
