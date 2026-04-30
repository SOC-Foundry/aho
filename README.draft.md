# aho

## Origin

TachTech builds data and SIEM migration pipelines for customers — moving customer data out of legacy systems into modern databases and SIEMs. We initially built these pipelines using multi-modal LLMs to handle the messy realities of migration: undocumented schemas to interpret, log formats to normalize, business logic to extract, edge cases to reason through.

Then we observed something. Single-agent Claude or Gemini execution against the same large complex projects — using the same multi-modal models — produced materially worse results than what our pipeline tooling produced. We initially attributed this to the pipelines themselves: the scripts, the structured phases, the project-specific logic. Closer inspection showed the difference was elsewhere. The harness around the pipeline — the gotcha registry, the ADR discipline, the drafter-auditor separation, the sealed acceptance archives, the scope hard-stops, the trace-every-decision posture — was doing the work. The pipeline was useful, but the harness was load-bearing.

aho is the extraction of that harness from pipeline-specific contexts into general-purpose governed agentic engineering infrastructure. The thesis: richer harnesses produce smarter behavior from the same models. Same Claude, same Gemini, materially different output, because the scaffolding around them is structured rather than vibes-based.

## What aho is

aho is governance infrastructure for LLM-driven engineering. The four properties that make it that, rather than another agent framework:

- **Drafter/auditor separation as a structural constraint.** Pattern C: the agent that produces work cannot bless it. The drafter drafts; a separate auditor audits; a human signs.
- **Provable lineage of every dispatch.** W3C TRACEPARENT propagation through the stack means every LLM call is attributable to its workstream, iteration, drafter session, and parent operation. Cost, tokens, errors, decisions all traceable.
- **Monitored invariants enforced as policy.** Pillar 11 (no agent git operations) is the prototype. Future invariants extend the same pattern. Policy as gate, not dashboard.
- **Sealed acceptance and audit archives, immutable event log.** The artifacts are the record. They cannot be retroactively edited. Disputes resolve by reading the archive, not by re-asking the agent.

The combination — and the compliance-shaped framing — is the differentiator. Agent orchestrators (LangChain, AutoGen, CrewAI), observability platforms (LangSmith, Langfuse, Helicone, Phoenix), eval platforms (Braintrust, Promptfoo), and IDE-embedded agents (Cursor, Claude Code) each cover one corner of this surface. None build governance.

## Why aho — cost and token utilization

Token cost matters. Claude and Gemini API spend at scale is the dominant operating cost of LLM-driven engineering, and single-agent execution wastes it in characteristic ways:

- **Cache underutilization.** Single-agent sessions rebuild context each invocation. aho's iteration model — fixed CLAUDE.md system prompt, persistent registries, sealed checkpoints — turns context into a cache asset. The Pillar 8 dashboard tracks this directly: cache:new ratios sustained across workstreams that single-agent execution structurally cannot match.
- **No model-cost gradient.** Single-agent execution sends every decision to the same expensive model. Routing decisions, classification, triage, substantive reasoning, and architectural decisions all priced identically. aho's council pattern routes triage and classification to small local models (Nemotron-class), substantive work to mid-tier (Qwen, GLM), premium dispatches to Claude or Gemini. The cost gradient is visible per-workstream.
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
11. **The human holds the keys.** No agent writes to git or manages secrets.

Each pillar is enforced by tooling, registry entries, or both. Pillar violations are findings; repeated violations are gotcha registry entries with mitigations.

## Architecture — current shape

aho today runs as a single-machine local loop. One human, one workstation, one project at a time.

Components on the workstation:

- **aho harness** — Pattern C state machine, dispatcher (model selection and routing), router (classification), acceptance and audit archive writers. Stateful per active iteration.
- **ollama** — local model runtime. Today: Qwen 3.5:9b for substantive reasoning, GLM-4.6V-Flash-9B for evaluation, Nemotron-mini:4b for triage and classification, nomic-embed-text for retrieval.
- **OTEL collector** — custom aho-otel-collector binary, gRPC ingest on `localhost:4317`, file exporters writing traces, metrics, and logs to `~/.local/share/aho/{traces,metrics,logs}/`.
- **aho-dashboard** — claw3d-fronted Flutter dashboard at `localhost:7800`, served by stdlib `http.server`. Shows component coverage, daemon health, and Pillar 8 cost/token telemetry per workstream.
- **aho-harness-watcher, aho-nemoclaw, aho-openclaw, aho-telegram** — daemon services for harness monitoring, classifier orchestration, dispatcher orchestration, and notification fan-out.
- **age + fernet secret store** — age handles per-machine identity (X25519); fernet handles bulk encrypted secret storage (AES-128). OS keyring caches the passphrase between sessions.

State on disk:

- **`.aho-checkpoint.json`** — Pattern C state machine, single source of truth for iteration progression.
- **`artifacts/iterations/{version}/`** — sealed acceptance archives, audit archives, plan/design docs, bundles, evidence.
- **`artifacts/adrs/`** — versioned architectural decision records, enumerated from disk.
- **`~/.local/share/aho/events/aho_event_log.jsonl`** — immutable append-only event ledger.

Distribution today is fish-shell-driven install scripts. This is a known limitation; see Target shape.

## Architecture — target shape

aho deployment scales across three tiers. The harness lives at the edge with each engineer; the heavy compute lives centrally; the truth layer is managed storage.

### Tier 1: engineer workstation (containerized)

Runs locally on every aho user's machine. Distributed as signed container images.

- **aho-harness** — Pattern C state machine, dispatcher logic, router logic, archive writers. Stateful per active iteration.
- **ollama-edge** — minimal local model runtime for triage, classification, offline work, and fast-iteration scenarios where network round-trip would slow the loop.
- **otel-collector-edge** — local OTEL collector, ships to central observability tier.
- **aho-dashboard-local** — claw3d for this engineer's iterations. Optional; org dashboard exists separately.
- **aho-harness-watcher** — daemon monitoring local harness state, emitting events.
- **engineer-local secret store** — age identity for this engineer, fernet-encrypted local secret bundle.

The engineer container is a workstation tool, not a Kubernetes pod. Stateful per iteration, identity-bound to the engineer, not fungible.

### Tier 2: pod-deployed serving plane (GCP / Kubernetes)

Runs centrally; engineer workstations consume via HTTPS. Pod-based, horizontally scaled with HPA, GPU-aware where applicable.

- **inference-gateway** — the governance load-bearer. Per-tenant routing, Pillar 11 admission gating, TRACEPARENT propagation crossing engineer-to-backend boundary, per-engineer cost attribution stamping, audit log emission for every model call. Tight latency and reliability requirements; multi-zone, PodDisruptionBudget-protected.
- **vllm-{qwen, glm, nemotron, ...}** — high-throughput model serving with continuous batching and PagedAttention. GPU node pools, MIG-partitioned A100s or H100s, HPA on QPS.
- **api-proxy-{anthropic, google, openai}** — egress with per-tenant key vaulting, rate limiting, retry handling.
- **audit-dispatcher** — stateless service handing drafter outputs to the auditor agent.
- **embedding-service** — nomic-embed-text or equivalent containerized for retrieval at scale.
- **batch-worker-pool** — Kubernetes Job objects for council re-vetting and parallel matrix sweeps.
- **registry-api** — Firestore-fronted API for gotcha registry, script registry, ADR index reads and writes.
- **archive-api** — GCS-fronted API for sealed acceptance and audit archive reads and writes.
- **aho-dashboard-org** — team-level org-wide view, separate deployment from engineer-local dashboards.
- **otel-collector-central** — DaemonSet ingestion tier.

### Tier 3: managed storage and state services

Not pods. The truth layer.

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

The harness is the contract between human, drafter agent, and auditor agent. It enforces Pattern C state transitions, validates dispatch parameters, parses TRACEPARENT, creates spans, writes acceptance and audit archives, and refuses operations that violate Pillars (notably 11). The harness is not a library called from agent code; the harness invokes agents.

### The registries

Three registries form the harness's memory:

- **Gotcha registry** — indexed failure modes with mitigations. Each entry is `aho-G###` numbered; entries persist across iterations and projects.
- **Script registry** — sanctioned tool surface per Pillar 4. Every executable invoked from the harness is registered with its arguments, return contract, and side effects.
- **ADR index** — architectural decision records numbered sequentially from disk enumeration, never fabricated.

In current shape, registries are version-controlled files in the repo. In target shape, registries are Firestore-backed APIs with Pub/Sub fan-out for change notification.

### The dispatcher and router

The dispatcher selects a model family (qwen, glm, nemotron, claude, gemini) and routes the dispatch to the appropriate backend. The router classifies inputs to determine routing — typically running a small local model (Nemotron) to triage before deciding whether the work merits a substantive dispatch.

In current shape, dispatcher routes to local Ollama. In target shape, dispatcher routes through the inference-gateway, which bridges to local Ollama for edge work, vLLM pods for substantive council dispatches, or API proxies for premium dispatches.

### Pattern C state machine

Five states per workstream: `not_started`, `in_progress`, `pending_audit`, `audit_complete`, `workstream_complete`. Transitions are durable per Pillar 6 — the checkpoint file is written before any state transition emits its event. The drafter cannot transition past `pending_audit`; only the auditor's archive (read by a fresh drafter session) authorizes the `workstream_complete` transition.

### OTEL telemetry and TRACEPARENT propagation

Every dispatch produces traces, metrics, and logs tagged with iteration, workstream, and role. TRACEPARENT propagates through the dispatch chain so a Claude Code `tool_use` span parents to the `aho.dispatch` span which parents to the inferred-model span. Cost and token attribution is per-span; the Pillar 8 dashboard aggregates by workstream.

### The Pillar 8 cost and token dashboard

claw3d-fronted Flutter dashboard reads from the OTEL aggregator and serves per-workstream and per-iteration cost rollups, token totals, cache:new ratios, turn counts, tool-call counts, MCP event counts, and error counts. The cost gradient is visible directly: substantive dispatches priced higher than triage dispatches, audit dispatches priced separately from drafter dispatches.

### Pattern C drafter and auditor

Drafter is typically Claude Code; auditor is typically Gemini CLI. They run in separate sessions with separate identity. The drafter writes the acceptance archive and stops; a fresh auditor session reads the archive and writes the audit archive; a fresh drafter session reads the audit archive and emits `workstream_complete`. Three sessions, three role boundaries, no agent able to bless its own work.

## Roadmap

aho deployment scales in phases:

- **Phase A (current):** single-machine local loop. Working, refined through 0.2.x iterations.
- **Phase B:** containerized harness on multiple engineer machines. Multi-machine telemetry capture begins. Distribution shifts from install scripts to signed container images. Local-only — no central cloud yet. The data-gathering phase.
- **Phase C:** cloud coordination layer informed by Phase B telemetry. Endpoints for registry sync, harness contribution, shared event log, and central observability backend. Specific shape determined by what Phase B telemetry reveals.
- **Phase D:** customer-facing deployment. Multi-tenant. Compliance-shaped.

Phase A is shipping. Phase B is the next several iterations of architectural work. Phase C and D are not yet designed in detail.

## Repo layout

```
aho/
├── src/aho/                    # Python package (src-layout)
│   ├── pipeline/               # Cascade: dispatcher, router, orchestrator, schemas
│   ├── agents/                 # Drafter/auditor agent integrations (nemoclaw, openclaw)
│   ├── council/                # Local model fleet wiring
│   ├── dashboard/              # Pillar 8 dashboard server + OTEL aggregator
│   ├── harness.py              # Pattern C state machine entry point
│   ├── acceptance.py           # Sealed acceptance archive writer
│   ├── workstream_events.py    # Workstream lifecycle event emitter
│   ├── workstream_gate.py      # State transition gating
│   ├── preflight/              # Pre-launch environment validation
│   ├── postflight/             # Post-execution quality gates
│   ├── registry.py             # Gotcha and script registry access
│   ├── secrets/                # age + fernet secret store wiring
│   ├── telegram/               # Notification fan-out
│   ├── integrations/           # External tool integrations
│   ├── rag/                    # Retrieval (nomic-embed-text, ChromaDB)
│   ├── install/                # Install-time orchestration logic
│   └── components/             # Component coverage tracking
├── bin/                        # CLI entry points and tool wrappers (Pillar 4)
├── artifacts/
│   ├── harness/                # Pillars (base.md), Pattern C protocol, prompt conventions
│   ├── adrs/                   # Architectural Decision Records (sequential)
│   ├── iterations/             # Per-iteration: design, plan, build, acceptance, audit, bundle
│   ├── phase-charters/         # Phase objective contracts
│   ├── roadmap/                # Strategic planning
│   ├── scripts/                # Utility and instrumentation
│   ├── prompts/                # LLM generation templates
│   ├── templates/              # Scaffolding
│   └── tests/                  # Verification suite
├── data/                       # Registries, event log, ChromaDB stores
├── templates/                  # Project bootstrap templates
├── tests/                      # Top-level test suite
├── web/                        # Dashboard web assets
├── app/                        # Consumer application mount (Phase B+)
├── pipeline/                   # Processing pipeline mount (Phase B+)
├── CLAUDE.md                   # Drafter (Claude Code) operating instructions
├── GEMINI.md                   # Auditor (Gemini CLI) operating instructions
├── CHANGELOG.md                # Iteration history
├── COMPATIBILITY.md            # Supported environments
├── MANIFEST.json               # Repo-level manifest
└── install.fish                # 9-step install orchestrator
```

Path-agnostic via `aho.paths.find_project_root()` and the `.aho.json` sentinel.

## Getting started

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

Requirements:

- Arch Linux family (CachyOS tested)
- Python 3.14
- fish shell (primary; non-fish shells are not supported)
- Ollama (installed via upstream script, not pacman)
- 8GB+ VRAM for the local council (Qwen 3.5:9b, GLM-4.6V-Flash-9B, Nemotron-mini:4b, nomic-embed-text)
- systemd user services with linger enabled
- Telegram bot token (optional, for `/ws` streaming)
- Brave Search API token (optional, for search tools)

Distribution today is the fish install script. Container distribution is Phase B; do not assume signed images exist yet.

Configuration:

- **Orchestrator config** at `~/.config/aho/orchestrator.json`: engine, search provider, openclaw/nemoclaw model defaults.
- **MCP servers** wired via per-project `.mcp.json` generated from template at bootstrap. Smoke-tested via `bin/aho-mcp smoke`.
- **Secrets** initialized via `bin/aho-secrets-init`. age keygen per-machine, fernet-encrypted storage, OS keyring caches passphrase.
- **Per-machine systemd user services:** `aho-openclaw`, `aho-nemoclaw`, `aho-telegram`, `aho-harness-watcher`, `aho-otel-collector`, `aho-dashboard`.

## Contributing

Pillar 11 governs: agents do not write to git. All commits are human-authored. PRs are welcome from human contributors. Agent-assisted drafting is expected and encouraged; agent-direct git operations are not.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full iteration history back to 0.1.0-alpha.

## License

License to be determined before v0.6.0 release.
