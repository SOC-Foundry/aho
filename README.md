# aho

## Origin

TachTech builds data and SIEM migration pipelines for customers — moving customer data out of legacy systems into modern databases and SIEMs. We initially built these pipelines using multi-modal LLMs to handle the messy realities of migration: undocumented schemas to interpret, log formats to normalize, business logic to extract, edge cases to reason through.

Then we observed something. Single-agent Claude or Gemini execution against the same large complex projects — using the same multi-modal models — produced materially worse results than what our pipeline tooling produced. We initially attributed this to the pipelines themselves: the scripts, the structured phases, the project-specific logic. Closer inspection showed the difference was elsewhere. The harness around the pipeline — the gotcha registry, the ADR discipline, the drafter-auditor separation, the sealed acceptance archives, the scope hard-stops, the trace-every-decision posture — was doing the work. The pipeline was useful, but the harness was load-bearing.

aho is the extraction of that harness from pipeline-specific contexts into general-purpose governed agentic engineering infrastructure. The thesis: richer harnesses produce smarter behavior from the same models. Same Claude, same Gemini, materially different output, because the scaffolding around them is structured rather than vibes-based.

## What aho is

aho is governance infrastructure for LLM-driven engineering. The four properties that make it that, rather than another agent framework:

- **Drafter / executor / auditor / operator separation as a structural constraint.** Pattern C, modified: the agent that drafts cannot execute; the agent that executes cannot bless its own work; a separate auditor adjudicates against sealed evidence; a human signs.
- **Provable lineage of every dispatch.** W3C TRACEPARENT propagation through the stack means every LLM call is attributable to its workstream, iteration, drafter session, and parent operation. Cost, tokens, errors, decisions all traceable.
- **Monitored invariants enforced as policy.** Pillar 11 (no agent git operations, no agent secret management) is the prototype. Future invariants extend the same pattern. Policy as gate, not dashboard.
- **Sealed acceptance and audit archives, immutable event log.** The artifacts are the record. They cannot be retroactively edited. Disputes resolve by reading the archive, not by re-asking the agent.

The combination — and the compliance-shaped framing — is the differentiator. Agent orchestrators (LangChain, AutoGen, CrewAI), observability platforms (LangSmith, Langfuse, Helicone, Phoenix), eval platforms (Braintrust, Promptfoo), and IDE-embedded agents (Cursor, Claude Code) each cover one corner of this surface. None build governance.

## Status (as of 0.2.17 close)

- **Latest closed iteration:** 0.2.17 (six workstreams W0–W6, all `pass_with_findings`, all operator-signed). Final close note at [`artifacts/iterations/0.2.17/iteration-close-0.2.17.md`](artifacts/iterations/0.2.17/iteration-close-0.2.17.md). Canonical retrospective at [`docs/retrospectives/0.2.17.md`](docs/retrospectives/0.2.17.md).
- **Container image:** `ghcr.io/soc-foundry/aho:0.2.17-rc2` published (manifest digest `sha256:b6dd0596…`). Multistage Python 3.14-slim build, ~340MB. The `0.2.17` final tag awaits operator-side token rotation (F-0.2.17-W1-003), the only remaining pre-tsP3 hard gate.
- **Auditor primitive:** in-container `llama3.2:3b` with W3 RAG enrichment + W4 deterministic post-hoc filter. Five deployments to date (W2 / W3 / W4 / W5 / W6). Bootstrap tests 1–7 all passed structurally.
- **Materiality status:** N=5 below the N≥8 threshold per ADR-0010 — **qualified validation, not full validation**. Three more iterations of auditor-seat data are required before the protocol meets the canonical evidence threshold.
- **Next:** 0.3.1 launches partial-tier on tsP3 (ThinkStation P3, RTX 2000 Ada 16GB) post-token-rotation. Five carry-forwards fold into 0.3.x base-tier hardening (none are hard gates).

## Why aho — cost and token utilization

Token cost matters. Claude and Gemini API spend at scale is the dominant operating cost of LLM-driven engineering, and single-agent execution wastes it in characteristic ways:

- **Cache underutilization.** Single-agent sessions rebuild context each invocation. aho's iteration model — fixed CLAUDE.md system prompt, persistent registries, sealed checkpoints — turns context into a cache asset. The Pillar 8 dashboard tracks this directly: cache:new ratios sustained across workstreams that single-agent execution structurally cannot match.
- **No model-cost gradient.** Single-agent execution sends every decision to the same expensive model. Routing decisions, classification, triage, substantive reasoning, and architectural decisions all priced identically. aho's council pattern routes triage and classification to small local models (Nemotron-class), substantive work to mid-tier (Qwen, GLM), audit to a confidence-floor-locked llama seat, premium dispatches to Claude or Gemini. The cost gradient is visible per-workstream.
- **Re-execution waste from undetected drift.** Single-agent failure modes — hallucinated state, stale assumptions, lost context, mid-task looping — are wasted tokens compounded by downstream tokens built on bad foundations. aho's halt-on-fail discipline plus Pattern C audit catches drift at bucket boundaries, before downstream waste accumulates. The audit pass costs tokens; the un-audited downstream costs more.
- **Scope creep priced as features.** Single-agent execution under "do this large complex thing" expands scope as it works. aho's no-mid-flight-scope-amendment rule keeps tokens on the requested scope, not on the agent's interpretation of what it should also fix.

These are mechanism claims, not benchmark claims. The mechanisms compound across iterations.

## The 11 Pillars

aho's operating principles. Numbered, named, and binding.

1. **Delegate everything delegable.** The paid orchestrator decides; the local free fleet executes.
2. **The harness is the contract.** Agent instructions live in versioned harness files, not model context.
3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out.
4. **Wrappers are the tool surface.** Every tool is invoked through a `/bin` wrapper.
5. **Three octets, three meanings: phase, iteration, run.** Strategic, tactical, and execution scope.
6. **Transitions are durable.** State is written to a durable artifact before any transition.
7. **Generation and evaluation are separate roles.** Drafter and reviewer are different agents.
8. **Efficacy is measured in cost delta.** Wall clock, token cost, and delegate ratio are ground truth.
9. **The gotcha registry is the harness's memory.** Failure modes are indexed with mitigations.
10. **Runs are interrupt-disciplined.** No preference prompts mid-run; only capability gaps halt.
11. **The human holds the keys.** No agent writes to git or manages secrets. **Monitored invariant since 0.2.16; alert-fanout via dedicated Telegram channel since 0.2.16 W3.**

Each pillar is enforced by tooling, registry entries, or both. Pillar violations are findings; repeated violations are gotcha registry entries with mitigations.

## Architecture — current shape

aho today runs on a single workstation (NZXTcos: RTX 2080 SUPER 8GB) with the harness operating across two surfaces: a host-side broker layer and an in-container engineer-workstation image. 0.2.17 W1 shipped the container image; 0.2.17 W2–W6 stabilized the council seats running inside it.

### In-container (`ghcr.io/soc-foundry/aho:0.2.17-rc2`)

- **aho harness** — Pattern C state machine, dispatcher (model selection and routing per `MODEL_FAMILY_CONFIG` longest-prefix match), router (classification primitive at `aho.pipeline.router`), acceptance and audit archive writers. Stateful per active iteration.
- **aho.serve** — `aho serve` entrypoint: ready-and-waiting mode with health endpoints (`/healthz`, `/readyz`) on port 8080. SIGTERM-disciplined drain with OTEL flush.
- **aho.tier_detect** — VRAM probe at startup; classifies host as `base` / `partial` / `full` per ADR-0007 thresholds. Writes to OTEL resource attribute `aho.tier` and to `/var/run/aho/tier`.
- **aho.secrets_client** — host-broker round-trip via unix socket at `/run/host-services/aho-secrets.sock`. No credential material in image layers; per ADR-0009.
- **aho.council** — in-container fleet wiring: `audit` (llama3.2:3b auditor with confidence-floor lock at 0.85), `triage` (nemotron-mini:4b, classification only), `embed` (nomic-embed-text via Ollama), `audit_ref_extract` + `audit_ref_lookup` (W3 RAG enrichment), `audit_finding_filter` (W4 deterministic post-hoc filter on findings).
- **aho.rag** — retrieval primitive against host-mounted ChromaDB volume at `/var/lib/aho/chroma`; recency-weighted similarity ranking; chunked indexing.
- **aho.gap_carry_forward_writer** — append-to-carry-forwards primitive with auto re-index hook (W6 D2 closure of F-0.2.17-W4-001). Failure path emits warning + OTEL counter; append still succeeds.
- **aho.materiality** — four-bucket OTEL counter primitives per ADR-0010 (`claim_vs_artifact_mismatches.{caught_by_llama, caught_by_drafter, escaped}`, `carry_forward_resolution_rate`).

### Host-side (NZXTcos)

- **aho.host.secrets_broker** — long-running unix-socket broker on `$XDG_RUNTIME_DIR/aho-secrets.sock`. SO_PEERCRED authentication; per-UID project-label registration; never returns secret values to unauthorized callers; logs request shape only, never values.
- **aho.host.run_container** — wrapper that registers a UID with the broker, runs `podman run` with the broker socket bind-mounted, and unregisters on exit. The canonical entrypoint for engineer-side container invocations.
- **age + fernet secret store** — age handles per-machine identity (X25519); fernet handles bulk encrypted secret storage (AES-128). OS keyring caches the passphrase between sessions. Read by the broker only; never by the in-container agent.
- **OTEL collector** — `aho-otel-collector` binary, gRPC ingest on `localhost:4317`, file exporters writing traces, metrics, and logs to `~/.local/share/aho/{traces,metrics,logs}/`.
- **aho-dashboard** — claw3d-fronted Flutter dashboard at `localhost:7800`, served by stdlib `http.server`. Shows component coverage, daemon health, Pillar 8 cost/token telemetry per workstream, materiality dashboard surfaces, role-collapse tripwire, and the four-surface anti-rubber-stamp dashboard (W4 D6 update).
- **aho-harness-watcher, aho-nemoclaw, aho-openclaw, aho-telegram, aho-jaeger** — daemon services for harness monitoring, classifier orchestration, dispatcher orchestration, notification fan-out (with a separate Pillar 11 alert channel since 0.2.16 W3), and trace viewing.
- **Ollama** — local model runtime serving the in-container fleet via `host.containers.internal:11434` (per ADR-0008 hybrid mode).

### State on disk

- **`.aho-checkpoint.json`** — Pattern C state machine, single source of truth for iteration progression.
- **`artifacts/iterations/{version}/`** — sealed acceptance archives, audit archives, plan/design docs, bundles, evidence, close notes.
- **`artifacts/iterations/{prior_version}/carry-forwards-{prior_version}.md`** — running cross-iteration ledger; mutated only via `aho.gap_carry_forward_writer.append_to_file`.
- **`artifacts/adrs/`** — versioned architectural decision records, enumerated from disk (`0001-phase-a-externalization.md` through `0010-materiality-measurement.md` at 0.2.17 close).
- **`docs/architecture/`** — repo-resident component decomposition + claw3d brick spec (W5 D4–D5).
- **`docs/retrospectives/`** — repo-resident iteration retrospectives (W5 D6).
- **`~/.local/share/aho/events/aho_event_log.jsonl`** — immutable append-only event ledger.
- **`/var/lib/aho/chroma`** — host-mounted ChromaDB persistent collection (in-container at the same path; engineer-shared on the host).

Distribution is currently dual-track: `install.fish` for fresh-box host bootstrap (canonical for any new Arch box) plus the `ghcr.io` container image for engineer-side workloads on bootstrapped hosts.

## Architecture — target shape

aho deployment scales across three tiers. The harness lives at the edge with each engineer; the heavy compute lives centrally; the truth layer is managed storage. The 0.2.17 container image is the first concrete step toward Tier 1.

### Tier 1: engineer workstation (containerized)

Runs locally on every aho user's machine. Distributed as signed container images.

- **aho-harness** — Pattern C state machine, dispatcher, router, archive writers. Stateful per active iteration. **Shipping at 0.2.17-rc2.**
- **ollama-edge** — minimal local model runtime for triage, classification, offline work, and fast-iteration scenarios where network round-trip would slow the loop. **Shipping (host-side, hybrid-mode bridged into container).**
- **otel-collector-edge** — local OTEL collector, ships to central observability tier. **Shipping (host-side; central tier still future).**
- **aho-dashboard-local** — claw3d for this engineer's iterations. Optional; org dashboard exists separately. **Shipping (host-side).**
- **aho-harness-watcher** — daemon monitoring local harness state, emitting events. **Shipping (host-side).**
- **engineer-local secret store** — age identity for this engineer, fernet-encrypted local secret bundle. **Shipping (host-side); container reads via broker per ADR-0009.**

The engineer container is a workstation tool, not a Kubernetes pod. Stateful per iteration, identity-bound to the engineer, not fungible.

### Tier 2: pod-deployed serving plane (GCP / Kubernetes)

Runs centrally; engineer workstations consume via HTTPS. Pod-based, horizontally scaled with HPA, GPU-aware where applicable. **Not yet built.**

- **inference-gateway** — the governance load-bearer. Per-tenant routing, Pillar 11 admission gating, TRACEPARENT propagation crossing engineer-to-backend boundary, per-engineer cost attribution stamping, audit log emission for every model call. Tight latency and reliability requirements; multi-zone, PodDisruptionBudget-protected.
- **vllm-{qwen, glm, llama, nemotron, ...}** — high-throughput model serving with continuous batching and PagedAttention. GPU node pools, MIG-partitioned A100s or H100s, HPA on QPS.
- **api-proxy-{anthropic, google, openai}** — egress with per-tenant key vaulting, rate limiting, retry handling.
- **audit-dispatcher** — stateless service handing executor outputs to the auditor agent.
- **embedding-service** — nomic-embed-text or equivalent containerized for retrieval at scale.
- **batch-worker-pool** — Kubernetes Job objects for council re-vetting and parallel matrix sweeps.
- **registry-api** — Firestore-fronted API for gotcha registry, script registry, ADR index reads and writes.
- **archive-api** — GCS-fronted API for sealed acceptance and audit archive reads and writes.
- **aho-dashboard-org** — team-level org-wide view, separate deployment from engineer-local dashboards.
- **otel-collector-central** — DaemonSet ingestion tier.

### Tier 3: managed storage and state services

Not pods. The truth layer. **Not yet built.**

- **Firestore** — checkpoint state, registry contents, gotcha index, ADR index, event log index. Single-collection multi-tenant schema with `t_log_type` discriminator (pattern proven in TachTech's pipeline tooling).
- **GCS** — sealed acceptance archives, sealed audit archives, bundle storage, model weights cache for vLLM.
- **Cloud Trace (or Tempo)** — OTEL trace storage.
- **Cloud Monitoring (or Mimir)** — OTEL metric storage.
- **Cloud Logging (or Loki)** — OTEL log storage.
- **Secret Manager (or Vault)** — per-engineer and per-tenant identity vaulting.
- **Pub/Sub** — event log fan-out for change notification: registry updates published to subscribed harness instances on engineer workstations.
- **Workload Identity** — engineer-container to GCP authentication.

### Why this shape

Three independent scaling axes:

- **Dispatch volume** scales pods in Tier 2 via HPA and cluster autoscaling on GPU node pools. This is the canonical Kubernetes-with-GPU workload.
- **Engineer count and deployment count** scales by deployment multiplication: more engineers means more workstation containers, each producing load on Tier 2 services. Engineer-side does not pod-scale.
- **Storage and archive volume** scales via Tier 3 service capacity, independent of pod count.

Putting the harness or registries in pods would couple these axes and break the independence. The boundary — harness and registries at the edge or behind APIs, model compute in pods, truth in managed services — preserves it.

## Components in detail

### The harness

The harness is the contract between human, drafter agent, executor agent, and auditor agent. It enforces Pattern C state transitions, validates dispatch parameters, parses TRACEPARENT, creates spans, writes acceptance and audit archives, and refuses operations that violate Pillars (notably 11). The harness is not a library called from agent code; the harness invokes agents.

### The four roles (Pattern C, modified)

Per ADR-0007 §Council roles (W5 amendment) and the 0.2.17 protocol:

- **Drafter** — external, persistent across chat sessions. Currently Claude (web project folder). Authors plan-docs, executor prompts, and arbitrates auditor disposition pre-sign.
- **Executor** — external, per-iteration. Claude Code or Gemini CLI. Reads the plan-doc, executes the workstream scope, writes the acceptance archive, runs the self-audit probe, halts.
- **Auditor** — in-container, base tier: `llama3.2:3b` with confidence-floor lock at 0.85 + W3 RAG enrichment + W4 deterministic post-hoc filter. Audits sealed acceptance archives; emits dispositions; never writes its own output past the audit emitter.
- **Operator** — human (Kyle). Signs close notes; rotates secrets; runs git operations; manages physical and credential resources.

### The registries

Three registries form the harness's memory:

- **Gotcha registry** — indexed failure modes with mitigations. Each entry is `aho-G###` numbered; entries persist across iterations and projects.
- **Script registry** — sanctioned tool surface per Pillar 4. Every executable invoked from the harness is registered with its arguments, return contract, and side effects.
- **ADR index** — architectural decision records numbered sequentially from disk enumeration, never fabricated. At 0.2.17 close: ADR-0001 through ADR-0010.

In current shape, registries are version-controlled files in the repo. In target shape, registries are Firestore-backed APIs with Pub/Sub fan-out for change notification.

### The dispatcher and router

The dispatcher (`src/aho/pipeline/dispatcher.py`) selects a model family and routes the dispatch to the appropriate backend. `MODEL_FAMILY_CONFIG` resolves family by longest-prefix match — Qwen, Llama 3.x, GLM, and Nemotron each carry their own stop tokens, `num_predict`, `num_gpu`, and template handling. Ollama state hygiene primitives (`unload_model()`, `list_loaded_models()`, `ensure_model_ready()`) are first-class; cross-model cascades serialize on 8GB VRAM. 52 dispatcher tests (was 6 at 0.2.13).

The router (`src/aho/pipeline/router.py`) is the canonical classification primitive. `NemoClawOrchestrator.route()` uses the router; legacy `nemotron_client.classify` is deprecated since 0.2.16.

In current shape, both dispatcher and router run in-container against the host's Ollama (hybrid mode per ADR-0008). In target shape, they route through the inference-gateway, which bridges to local Ollama for edge work, vLLM pods for substantive council dispatches, or API proxies for premium dispatches.

### Pattern C state machine

Five states per workstream: `not_started`, `in_progress`, `pending_audit`, `audit_complete`, `workstream_complete`. Plus a transient `blocked` vertex on halt-and-surface conditions, first observed at W6 D3 (validates that the executor cannot unilaterally advance the state machine past a halt — drafter arbitration is required).

Transitions are durable per Pillar 6 — the checkpoint file is written before any state transition emits its event. The drafter cannot transition past `pending_audit`; only the auditor's archive (read by a fresh drafter session) authorizes the `workstream_complete` transition.

### OTEL telemetry and TRACEPARENT propagation

Every dispatch produces traces, metrics, and logs tagged with iteration, workstream, and role. TRACEPARENT propagates through the dispatch chain so a Claude Code `tool_use` span parents to the `aho.dispatch` span which parents to the inferred-model span. Cost and token attribution is per-span; the Pillar 8 dashboard aggregates by workstream.

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

### The Pillar 8 cost and token dashboard

claw3d-fronted Flutter dashboard reads from the OTEL aggregator and serves per-workstream and per-iteration cost rollups, token totals, cache:new ratios, turn counts, tool-call counts, MCP event counts, and error counts. The cost gradient is visible directly: substantive dispatches priced higher than triage dispatches, audit dispatches priced separately from drafter dispatches.

### The materiality protocol (ADR-0010)

Four OTEL counters with falsifiable thresholds:

- `aho.materiality.claim_vs_artifact_mismatches.caught_by_llama` — auditor seat catches.
- `aho.materiality.claim_vs_artifact_mismatches.caught_by_drafter` — gap-net catches after auditor pass.
- `aho.materiality.claim_vs_artifact_mismatches.escaped` — mismatches that escape a sealed iteration (surfaced retrospectively).
- `aho.materiality.carry_forward_resolution_rate` — carry-forwards explicitly closed by reference in a workstream output.

ADR-0010 specifies validation thresholds: N≥8 iterations, ≥30% reduction in escaped defects vs baseline window, non-zero `caught_by_llama` AND non-zero `caught_by_drafter` across the protocol window, carry-forward resolution rate ≥60% within 2 iterations of flagging. **As of 0.2.17 close, N=5 — qualified validation, not full validation.**

### The anti-rubber-stamp four-surface dashboard

Anti-rubber-stamp hardening operates on four surfaces (W4 D6 update from prior three-surface version):

1. **`nemotron_raise_on_malformed`** — triage primitive raises rather than silently degrading on malformed model output (G083 discipline).
2. **`llama_confidence_floor_lock`** — auditor `clean` disposition is structurally unreachable below confidence 0.85; locked to `surface_to_drafter` instead.
3. **`role_collapse_tripwire`** — detection of generation/evaluation role collapse across drafter / auditor sessions.
4. **`deterministic_post_hoc_filter`** — W4 D1 filter on RAG-aware findings: drops findings only where BOTH a registered anchor appears in the description AND a fake-ID phrase matches. Structurally narrow.

### Secrets broker boundary (ADR-0009)

Three rules verbatim:

1. No credential material in image layers ever.
2. Per-user secret access via host-side broker.
3. No SSH agent socket forwarded.

The broker is the only path from in-container code to host-stored secrets. The W6 D1 `aho secrets-test` hash-fingerprint redesign closed F-0.2.17-W1-001 (subcommand never returns decrypted value to caller stdout); operator verifies broker round-trip equivalence by computing a host-side fingerprint and comparing.

## Roadmap

aho deployment scales in phases:

- **Phase A (substantially complete through 0.2.17):** single-machine local loop. Working, refined through 0.2.x iterations. Adversarial-Authorship-at-base-tier in production. Materiality protocol in qualified-validation status (N=5 below N≥8 threshold per ADR-0010).
- **Phase B (started at 0.2.17 W1; in progress):** containerized harness on engineer machines. 0.2.17 ships the engineer-workstation container image (`ghcr.io/soc-foundry/aho:0.2.17-rc2`). 0.3.x continues partial-tier and full-tier work on tsP3 and other engineer hardware. Multi-machine telemetry capture begins. Distribution shifts from install scripts alone to install scripts plus signed container images. Local-only — no central cloud yet. The data-gathering phase.
- **Phase C:** cloud coordination layer informed by Phase B telemetry. Endpoints for registry sync, harness contribution, shared event log, and central observability backend. Specific shape determined by what Phase B telemetry reveals.
- **Phase D:** customer-facing deployment. Multi-tenant. Compliance-shaped.

The next iteration (0.3.1) launches partial-tier on tsP3 (ThinkStation P3, RTX 2000 Ada 16GB). The 16GB VRAM headroom enables `qwen3.5:9b` as a partial-tier auditor candidate, raising the consistency floor over `llama3.2:3b` base-tier auditing. Five carry-forwards from 0.2.17 fold into 0.3.1 base-tier hardening (W5-001 structural pre-check scope discrimination, W5-002 plan-doc convention drift, W6-001 lookup-ranking on opaque IDs, W6-002 embed timeout default, W6-003 gitignore gap); none are hard gates. The single hard gate before tsP3 handoff is operator-side: F-0.2.17-W1-003 (`ahomw:telegram_bot_token` rotation), verified via the W6 D1 hash-fingerprint contract.

## Repo layout

```
aho/
├── src/aho/                    # Python package (src-layout)
│   ├── pipeline/               # Cascade: dispatcher, router, orchestrator, schemas
│   ├── council/                # In-container fleet: audit, triage, embed, audit_finding_filter,
│   │                           # audit_ref_extract, audit_ref_lookup, status, dispatch
│   ├── host/                   # Host-side primitives: secrets_broker, run_container
│   ├── dashboard/              # Pillar 8 dashboard server + OTEL aggregator + claw3d bricks
│   ├── alerts/                 # Pillar 11 alert fan-out (Telegram, dedicated channel)
│   ├── rag/                    # Retrieval (nomic-embed-text, ChromaDB, recency-weighted)
│   ├── secrets/                # Host-side age + fernet store; container reads via broker
│   ├── telegram/               # Notification fan-out
│   ├── integrations/           # External tool integrations
│   ├── components/             # Component coverage tracking
│   ├── preflight/              # Pre-launch environment validation
│   ├── postflight/             # Post-execution quality gates
│   ├── install/                # Install-time orchestration logic
│   ├── cli.py                  # `aho` CLI dispatcher
│   ├── serve.py                # Container ready-and-waiting mode (W1)
│   ├── tier_detect.py          # VRAM-based base/partial/full tier classification
│   ├── secrets_client.py       # Container-side broker round-trip client
│   ├── workstream_events.py    # Workstream lifecycle event emitter
│   ├── workstream_gate.py      # State transition gating
│   ├── audit_disposition_emitter.py  # Sealed audit archive writer
│   ├── gap_carry_forward_writer.py   # Carry-forwards append + auto-reindex hook
│   ├── materiality.py          # Four-bucket OTEL counter primitives (ADR-0010)
│   └── ...
├── bin/                        # CLI entry points and tool wrappers (Pillar 4)
├── containers/                 # Container build context (Dockerfile.hello, etc.)
├── Dockerfile                  # Multistage Python 3.14-slim engineer-workstation image
├── .dockerignore               # Working-state exclusion list (canonical)
├── artifacts/
│   ├── harness/                # Pillars (base.md), Adversarial Authorship protocol, prompt conventions
│   ├── adrs/                   # 0001 through 0010 at 0.2.17 close (sequential)
│   ├── iterations/             # Per-iteration: design, plan, build, acceptance, audit, bundle, close note
│   ├── phase-charters/         # Phase objective contracts
│   ├── roadmap/                # Strategic planning
│   ├── scripts/                # Utility and instrumentation
│   ├── prompts/                # LLM generation templates
│   ├── templates/              # Scaffolding
│   └── tests/                  # Verification suite
├── docs/                       # Repo-resident documentation (W5)
│   ├── architecture/           # component-decomposition.md + claw3d-brick-spec.md
│   └── retrospectives/         # 0.2.17.md (canonical iteration retrospective)
├── data/                       # Registries, event log mirrors, ChromaDB stores
├── templates/                  # Project bootstrap templates
├── tests/                      # Top-level test suite
├── web/                        # Dashboard web assets
├── app/                        # Consumer application mount (Phase B+)
├── pipeline/                   # Processing pipeline mount (Phase B+)
├── CLAUDE.md                   # Drafter / executor (Claude Code) operating instructions
├── GEMINI.md                   # Auditor (Gemini CLI) operating instructions for external-audit slots
├── CHANGELOG.md                # Iteration history
├── COMPATIBILITY.md            # Supported environments
├── MANIFEST.json               # Repo-level manifest
└── install.fish                # Multi-step install orchestrator (canonical fresh-box bootstrap)
```

Path-agnostic via `aho.paths.find_project_root()` and the `.aho.json` sentinel.

## Getting started

### Fresh-box host bootstrap (canonical)

```fish
git clone https://github.com/soc-foundry/aho ~/dev/projects/aho
cd ~/dev/projects/aho
./install.fish
aho doctor
```

Optional deeper checks:

```fish
aho doctor --deep        # includes Flutter and dart checks
aho components check     # per-kind component presence verification
```

### Container-side workloads (post-bootstrap)

```fish
# pull the published image
gh auth token | podman login ghcr.io -u <github-username> --password-stdin
podman pull ghcr.io/soc-foundry/aho:0.2.17-rc2

# run a workload through the host-side run-container wrapper
# (registers UID with broker, mounts socket, runs command, unregisters on exit)
aho host run-container --project ahomw --image ghcr.io/soc-foundry/aho:0.2.17-rc2 \
  -- secrets-test ahomw <secret-name>
```

The `gh auth token | podman login` pattern is the canonical credential refresh — podman's auth store at `~/.config/containers/auth.json` is independent of gh CLI's token store, so a valid gh PAT does not automatically authorize podman pulls or pushes (W6 D1 ops gotcha).

The `0.2.17` final tag awaits operator-side token rotation (F-0.2.17-W1-003); the `rc2` tag is the load-bearing tag for engineer-side use through the end of 0.2.17.

### Requirements

- Arch Linux family (CachyOS tested)
- Python 3.14
- fish shell (primary; non-fish shells are not supported)
- Ollama (installed via upstream script, not pacman)
- Podman 4.0+ (rootless mode supported; pasta networking with `iif lo` nft rule for in-container→host Ollama traffic per F-0.2.17-W1-002)
- 8GB+ VRAM for the local council at base tier:
  - `llama3.2:3b` (auditor, ~2GB)
  - `nemotron-mini:4b` (triage, ~3GB)
  - `nomic-embed-text` (retrieval, ~270MB)
  - `qwen3.5:9b` (substantive work; partial-tier candidate, requires 16GB+ VRAM for full-tier role)
  - `glm-4.6V-flash-9b` (partial-tier candidate; removed from base-tier auditor candidacy per ADR-0007 amendment)
- systemd user services with linger enabled
- Telegram bot tokens (optional, for `/ws` streaming and Pillar 11 alert fan-out — separate channels per 0.2.16 W3)
- Brave Search API token (optional, for search tools)

### Configuration

- **Orchestrator config** at `~/.config/aho/orchestrator.json`: engine, search provider, openclaw/nemoclaw model defaults.
- **MCP servers** wired via per-project `.mcp.json` generated from template at bootstrap. Smoke-tested via `bin/aho-mcp smoke`.
- **Secrets** initialized via `bin/aho-secrets-init`. age keygen per-machine, fernet-encrypted storage, OS keyring caches passphrase.
- **Per-machine systemd user services:** `aho-openclaw`, `aho-nemoclaw`, `aho-telegram`, `aho-harness-watcher`, `aho-otel-collector`, `aho-dashboard`, `aho-jaeger`.
- **Container env** (set by managed `.claude/settings.json` and inherited by `aho host run-container`): see §OTEL telemetry and TRACEPARENT propagation above.

## Contributing

Pillar 11 governs: agents do not write to git, do not manage secrets, do not push container images without explicit operator authorization. All commits are human-authored. PRs are welcome from human contributors. Agent-assisted drafting is expected and encouraged; agent-direct git operations are not.

The drafter / executor / auditor / operator separation is structural; contributions that obscure or weaken it are out of scope.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full iteration history back to 0.1.0-alpha.

The canonical 0.2.17 retrospective is at [`docs/retrospectives/0.2.17.md`](docs/retrospectives/0.2.17.md). Per-iteration close notes live alongside the sealed acceptance and audit archives under [`artifacts/iterations/{version}/`](artifacts/iterations/).

## License

License to be determined before v0.6.0 release.
