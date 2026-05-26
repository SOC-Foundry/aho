# 0.3.1 W1 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `halt`).

W1 acceptance archive sealed at
`artifacts/iterations/0.3.1/acceptance/W1.json`.
W1 audit archive sealed at
`artifacts/iterations/0.3.1/audit/W1.json` with
`disposition: "halt"` (llama self-audit verbatim — driven by F0 D2
retrieval-relevance failure + F1 F-0.2.17-W5-001 narrative-lift on
deferred-carry-forward listing). Drafter (claude-web) arbitrated
both findings and arbitrated disposition to `pass_with_findings`.
One new carry-forward added during D1-D7 execution (F-0.3.1-W1-001
nomic-embed chunk-size cap; cosmetic). Sealed shas (verified at
close-note authoring time):

- acceptance archive sha256:
  `76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d`

Audit archive (`audit/W1.json`) is UNTOUCHED post-emit. The
disposition field reads `halt`; drafter arbitration is recorded
only in the acceptance archive's D8 `drafter_review_note` block +
`carry_forwards_added` entries, and in this close note's prose.
Per Adversarial Authorship sealed-archive convention, audit
archives are not amended after emit — corrections and arbitrations
land in acceptance evidence and close-note prose, never in the
audit JSON.

## Workstream scope

W1 was the first substantive code-change workstream of 0.3.1.
Eight deliverables per W1-plan-doc-amendment.md (post-W0-close
amendment that superseded the original plan-doc §W1 scope):

- **D1** — install.fish idempotency hardening + structured per-step
  JSON output (12-field schema, --check + --step flags, 19 steps).
- **D2** — `aho rag bootstrap` (closes F-0.3.1-W0-002 structurally).
- **D3** — `bin/aho-doctor` wrapper (closes F-0.3.1-W0-001
  structurally).
- **D4** — Substrate freshness telemetry, 13 facts, per-fact warning
  thresholds, cross-host probes, OTEL gauge.
- **D5** — Dashboard surface: `/api/substrate` + `/substrate` HTML
  brick grid.
- **D6** — install.fish integration completeness; <60s full run.
- **D7** — Four test files; 27 passed + 1 intentional skip.
- **D8** — W1 self-audit on populated collection; first non-vacuous
  filter-eligibility check in 0.3.1.

## D8 self-audit findings

Two model findings from the in-container llama auditor on a8cos:

- **F0 (model id `D2`, severity important):** "The artifact claims
  that the carry-forward F-0.3.1-W0-002 is closed structurally, but
  the evidence snippet shows that it is not." This is an
  auditor retrieval-relevance failure. The W0-002 closure invariant
  is met operationally: RAG enrichment registered_count=20 (up from
  0 at W0 D9), F-0.2.17-W1-003 + F-0.2.18-W2-004 + F-0.3.1-W0-002 +
  F-0.3.1-W0-001 all resolve as registered with non-null
  top_source_artifact_path. ChromaDB collection is populated.
  Bootstrap worked. The auditor's evidence-snippet retrieval matched
  on unrelated content (W3-of-0.2.17 D1/D2 spurious-ID pattern, not
  the W0-002 closure mechanism). Same retrieval-relevance failure
  shape as F-0.2.17-W6-001 (deferred to 0.3.2 audit-machinery
  iteration). **Drafter arbitration: false positive; no new
  carry-forward; pattern in existing 0.3.2 cluster.**

- **F1 (model id `F-0.2.17-W5-001`, severity important):** "The
  artifact claims that the audit-time structural pre-check
  self-referential pattern is present, but the evidence snippet
  does not show this." The acceptance archive references
  F-0.2.17-W5-001 as a deferred carry-forward (to 0.3.2
  audit-machinery iteration), NOT as an active claim that the
  pattern is present in W1. Auditor conflated 'mentions in
  deferral context' with 'claims as active.' Same narrative-lift
  shape as F-0.2.18-W0-008. **Drafter arbitration: false positive;
  no new carry-forward; pattern in existing 0.3.2 cluster.**

Neither finding is fake-ID-on-registered. Both IDs are registered
references (D2 is a W1 deliverable ID in this acceptance archive;
F-0.2.17-W5-001 is a registered carry-forward ID resolved in the
RAG enrichment). The filter correctly did not suppress because
neither finding matches the fake-ID-on-registered shape that the
W4-of-0.2.17 deterministic post-hoc filter is structurally narrow
to. Both findings express auditor retrieval-relevance /
narrative-lift failures — distinct categories within the existing
0.3.2 audit-machinery iteration cluster.

W4-of-0.2.17 filter regression check passes non-vacuously
(`filter_eligible: true`; filter ran on the 2 model findings;
suppressed 0; did not silently substitute degraded findings; did
not fire incorrectly on registered IDs). This is the first
operationally meaningful filter-eligibility check in 0.3.1 — at
W0 D9 the collection was empty, registered_count=0, and
filter_eligible was vacuously false.

## Carry-forwards closed in W1

**Structural closures (verified by D8 RAG enrichment + W1
deliverable acceptance):**

- **F-0.2.18-W1-004** (substrate decoherence; original W1 closure
  target via D4 telemetry implementation). Closed by D4: 13-fact
  probe set + OTEL gauge + observables.jsonl append-only log per
  ADR-0011 lightweight tier. Tailnet-FQDN closure invariant verified
  on a8cos with `last_verified_age_seconds < 1h` after fresh probe
  (`tail8492.ts.net`, the post-incident tailnet domain).

- **F-0.3.1-W0-001** (drafter substrate-prerequisite gap; W0 D9
  surfaced via chromadb-absent halt). Closed structurally by D3
  `bin/aho-doctor` wrapper: forward-deployable per-workstream
  pre-flight gateway invokable from any W's D0. W2-first-dogfood
  pattern documented; install.fish `--check` mode is the
  structural pre-flight surface.

- **F-0.3.1-W0-002** (ChromaDB collection empty post-install; W0 D9
  surfaced via auditor's all-unverified RAG enrichment). Closed
  structurally by D2 `aho rag bootstrap` (52 of 53 canonical
  artifacts ingested → 263 chunks; idempotent re-run). Closure
  **VERIFIED operationally** by D8 RAG enrichment
  `registered_count=20` (vs 0 at W0 D9 with the same audit
  primitive). install.fish step `chromadb_collection_populated`
  invokes the bootstrap as remediation on detected empty collection.

- **F-0.3.1-W0-004** (canonical-root .aho-checkpoint.json absent on
  a8cos; W0 emit surfaced via no-op checkpoint advance). Closed
  structurally by D1 install.fish step `canonical_checkpoint_present`
  with checkpoint writer remediation. .aho-checkpoint.json now
  present at `~/Development/Projects/socfoundry/aho/.aho-checkpoint.json`
  with current_iteration / current_workstream / status fields.

## Carry-forwards partially closed in W1 (W2 completes)

- **F-0.3.1-W0-003** (OTEL collector endpoint post-NZXTcos-decommission).
  W1 ships an a8cos-local probe in the D4 13-fact set
  (fact `otel_collector_endpoint`, warning_age_seconds=3600). The
  probe currently reports `fail` because no a8cos-local collector
  is running yet. W2 closure: migrate to Beacon-as-aggregator per
  the W2 plan-doc-amendment scope expansion (extract
  `beacon/otel/config.py + exporter.py + buffer.py`, copy into
  `src/aho/observability/otlp_exporter.py`, wire metrics + audit
  dispositions to beacon's gRPC endpoint over Tailscale).

- **F-0.3.1-W0-005** (legacy `/home/kthompson/dev/projects/aho/src`
  in `sys.path` from stale editable-install metadata). W1 probes
  via D4 fact `sys_path_clean` (warning_age_seconds=3600) and
  reports drift. W2 closure: `pip install --user
  --break-system-packages -e ~/Development/Projects/socfoundry/aho`
  re-installs editable pointing at canonical path; verify
  post-install sys.path drift resolved.

## New carry-forward from W1 execution

- **F-0.3.1-W1-001 (cosmetic)** — D2 ingestion skip: single
  artifact chunk exceeded nomic-embed-text size cap. 52 of 53
  artifacts indexed; `artifacts/iterations/0.2.17/iteration-close-
  0.2.17.md` chunk-5 (out of 6 chunks) failed embed with HTTP 400
  Bad Request. Other 5 chunks of the same file indexed
  successfully — content is partially queryable. Closure target:
  0.3.2 (peer to F-0.2.17-W6-001 retrieval-quality work) OR W2 if
  chunking refinement is in scope. Recorded for visibility; not a
  structural defect in W1.

## Substrate state at close

- **install.fish idempotency + structured output:** 19 steps;
  check-first / remediate-on-fail / re-check / report-final-status
  semantics on every step. JSONL per-step output to
  `~/.local/share/aho/install-state.jsonl` with documented 12-field
  schema. `--check` (read-only) and `--step <id>` (surgical re-run)
  modes available. Full `--check` run on a8cos: 14s. Full mode run:
  16s. Idempotency property verified across two consecutive full
  runs.
- **`bin/aho-doctor` wrapper available** for W2+ executor prompts.
  Signature: `aho-doctor [--workstream W1|W2|W3] [--required-steps
  id_list] [--remediate] [--json]`. Exit codes 0/1/2/3 per amendment.
  W2 D0 invocation pattern: `aho-doctor --workstream W2` →
  non-zero exits gate the W2 prompt's substantive deliverables.
- **ChromaDB collection populated:** `ahomw` collection has 263
  documents (52 canonical artifacts × ~5 chunks each). D8 RAG
  enrichment confirms 20 of 28 detected references resolve to
  `status=registered` with non-null `top_source_artifact_path`.
  Bootstrap is idempotent (re-run produces same 263-count).
- **13-fact substrate-freshness telemetry live with local-only
  OTLP emission.** `src/aho/observability.py` API
  (`record_observable` / `last_verified_age_seconds` /
  `snapshot_all_facts` / `stale_count`). `bin/aho-probe-substrate`
  exercise the probe set across a8cos + p3cos + x9cos via Tailscale
  ssh. `host_unreachable` is a distinct outcome class.
- **Dashboard surface rendering substrate-freshness brick grid.**
  GET `http://127.0.0.1:7800/api/substrate` returns 13-fact JSON.
  GET `http://127.0.0.1:7800/substrate` returns HTML brick grid
  with color cascade (green / yellow / red per per-fact warning
  thresholds) + summary tile (stale count). Current substrate state
  on a8cos: 11 green / 0 yellow / 2 red (both reds map to W2-scope
  substrate gaps — OTEL collector + sys.path).
- **Auditor seat:** llama3.2:3b in-container at base tier on a8cos.
  RAG enrichment now populated (vs empty at W0 D9). `AHO_COUNCIL_
  EMBED_TIMEOUT_S=900` + `AHO_COUNCIL_AUDIT_TIMEOUT_S=900`
  env-var posture confirmed for CPU-only Ollama inference on the
  Radeon 780M iGPU substrate.
- **Misc executor-session substrate state:** pytest 9.0.3 installed
  (test runtime); .aho-checkpoint.json present at canonical project
  root; tier.json present and base-tier.

## Auditor-seat continuation

W1 D8 is the **seventh deployment** of the in-container llama
auditor — **bootstrap test 11** in the architecture progression —
counting from the W4-of-0.2.17 stabilization of the post-hoc filter
primitive:

- **W4 / W5 / W6 of 0.2.17:** filter primitive stabilization across
  three workstreams (3 deployments).
- **W0 / W1 / W2 of 0.2.18:** filter extensions
  (`_GIT_OP_ENFORCEMENT_SENTINELS`, `_RAG_STATUS_ECHO_PATTERN`,
  `unsupported_halt_downgrade`) per W0 v1/v2/v3 audit cycle (3
  deployments).
- **W0 of 0.3.1:** first audit on chromadb-just-installed substrate
  with empty collection; filter_eligible=false (vacuous; 1
  deployment).
- **W1 of 0.3.1 (this one):** first audit on populated collection
  in 0.3.1. **First non-vacuous filter-eligibility check in 0.3.1**
  — `registered_count=20` (vs 0 at W0 D9). Filter ran
  operationally on 2 model findings; suppressed 0; W4-of-0.2.17
  lock-in confirmed not regressed (1 deployment).

Cumulative: 7 deployments / 11th bootstrap-test in the
architecture progression. The halt-and-surface invariant continues
to function correctly. D8 halt was earned (real model findings
expressing real auditor retrieval-relevance / narrative-lift
failures) — drafter arbitration revealed both findings as
auditor-machinery limitations (not W1 deliverable defects) in the
existing 0.3.2 cluster.

The W4-of-0.2.17 deterministic post-hoc filter remains structurally
narrow across seven deployments. It catches `registered anchor +
fake-ID phrase` combinations specifically and does not silently
drop on retrieval-relevance or narrative-lift failure modes (which
is correct — those modes need different structural fixes per the
0.3.2 cluster).

## Forward-looking notes

**For W2 (install.fish tier-aware refactor + Beacon integration +
notjustavar Firestore writer module):**

W2 scope expands beyond original plan-doc §W2 (tier-aware
aho-models / tier-manifest writer / broker systemd template) per
arbitration this iteration. Five tracks:

- **Track 1 — 0.2.18 W2 carry-forwards (originally scoped):**
  F-0.2.18-W2-002 (bin/aho-models tier-aware), F-0.2.18-W2-003
  (`aho install tier-manifest`), F-0.2.18-W2-004 (broker systemd
  template). Plus pacman.conf `IgnorePkg = syncthing` pin +
  syncthing v1.30.0 doctor probe from 0.3.0 pre-flight.
- **Track 2 — Beacon integration:** Extract beacon's `otel/config.py
  + exporter.py + buffer.py` pattern; copy into
  `src/aho/observability/otlp_exporter.py`. Configure OTLPSettings
  via `OTLP_*` env-prefixed pydantic settings. Wire aho metrics
  (audit dispositions, substrate freshness, council invocations) to
  beacon's gRPC endpoint over Tailscale. Per beacon §11 takeaways:
  cloud-provider detection auto-degrades on bare-metal; copying the
  package is the documented extraction path.
- **Track 3 — F-0.3.1-W0-003 closure:** Migrate OTEL endpoint from
  a8cos-local to Beacon-as-aggregator. Reconfigure
  `OTEL_EXPORTER_OTLP_ENDPOINT` (or whatever beacon's canonical
  env-var key resolves to) to beacon's gRPC receiver address.
  Substrate fact #2 (`otel_collector_endpoint`) reachability flips
  from `fail` to `ok` post-migration.
- **Track 4 — F-0.3.1-W0-005 closure:** `pip install --user
  --break-system-packages -e ~/Development/Projects/socfoundry/aho`
  re-installs editable pointing at canonical path. Verify
  post-install: `sys.path` no longer includes
  `/home/kthompson/dev/projects/aho/src`. Substrate fact #13
  (`sys_path_clean`) probe flips from `fail` to `ok`.
- **Track 5 — Tachtech-tenant Firestore writer module (notjustavar
  codename):** `t_any_*` indicator field convention; env-var-driven
  tenant config (`AHO_TENANT_ID` / `AHO_TENANT_FIRESTORE_PROJECT` /
  `AHO_TENANT_BEACON_ENDPOINT`). Beacon API key secret as a new
  fernet-broker entry `beacon_otlp_api_key`; aho's OTLP exporter
  retrieves at startup. ADR-0009 contract path (broker fetch, never
  plaintext at rest).

W2 D0: `aho-doctor --workstream W2`. W2 required-step list per
amendment §D3 includes all W1 required steps + `tier_json_present`
+ W2-new steps (`broker_service_template_installed`,
`pacman_ignorepkg_syncthing`, `syncthing_version_1_30_0`).

**For W3 (council-mining retrospective + first Tachtech-tenant
data write):**

Pipeline runs against the ~200 artifacts in the populated ChromaDB
collection from D2 (currently 263 chunks across 52 artifacts; W2
may grow this to ~70-80 artifacts after Beacon docs + retros land
post-bootstrap). Output: augmented gotcha registry with
human-right / council-right / human-wrong / council-wrong
quadrants. The output lands in notjustavar Firestore as the **first
substantial Tachtech-tenant data write** via W2's Firestore writer
module — operationally validates the multi-tenant data path before
0.3.2 broader-scope work.

**For W4 (Firestore schema dry-run):**

Uses notjustavar test collection or test database within
notjustavar (operator decides which at W4 prompt-authoring time).
Validates `t_any_*` indicator field shape against ingest patterns.
Substrate-fact-probe-set extends to include Firestore reachability
+ schema-version probe.

**For W6 (ADR consolidation + harness/base.md amendment):**

- ADR-0011 finalization: substrate freshness lightweight tier ships
  W1+W2; mid-tier (`aho posture` subcommand + dashboard wave-packet
  visualization per aho-quantum.md) defers to 0.3.3+ candidate.
- ADR-0012 finalization: Chain of Trust L5 placement.
- ADR-0007 amendment: three-axis tier model (VRAM × attestation ×
  tenant-data-locus).
- ADR-0009 amendment: XDG broker socket canonical path
  (F-0.2.18-W2-005 closure).
- Pillar 10 + Pillar 11 amendments + new Pillars 12 + 13 land as
  `harness/base.md` version-bump. The W0 D9 chromadb halt + the
  drafter retraction of over-broad Pillar 11 scope is the
  motivating incident in the Pillar 11 amendment rationale.
- **Candidate ADR-0013:** "Beacon as canonical OTLP aggregator."
  Decides between (a) leaving beacon integration as install.fish
  env-var configuration without ADR (operational decision) or (b)
  elevating to ADR for the architectural decision that Tachtech's
  operational telemetry plane is beacon-centric across all
  projects. Drafter recommends (b) — beacon-as-aggregator becomes
  load-bearing for TTEOS and customer engagements; ADR makes it
  discoverable.
- **Candidate ADR-0014:** "aho multi-tenant data architecture."
  Captures TTEOS / notjustavar / customer-codename /
  downstream-routing-from-pipeline / obfuscation-at-downstream-emit
  pattern as architectural decision for future-state consideration.
  **NOT current 0.3.1 deliverable scope** — design-doc-shape rather
  than implementation. Documented at W6 to discover at 0.4.x+
  charter time.

## State at close

- Acceptance archive sealed:
  `76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba`
  (`audit_status: pending_drafter_review`; transitions at operator
  sign + workstream_complete emit).
- Audit archive sealed and UNTOUCHED:
  `3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d`.
- Carry-forwards file update **pending operator review**. Six
  closures + one new entry to append via
  `aho.gap_carry_forward_writer.append_to_file` at operator
  discretion. The append touches a tracked file and is part of the
  carry-forward state-machine that the operator owns (Pillar 11).
- W1 deliverables shipped on a8cos: install.fish + 5 new bin
  wrappers (aho-rag-bootstrap, aho-doctor, _aho_doctor_eval.py,
  aho-probe-substrate, aho-claw3d updated) + 3 new src modules
  (rag/bootstrap.py, observability.py, substrate_probes.py) + 1 new
  claw3d panel (substrate_panel.py) + 4 new test files + 1 modified
  src/aho/claw3d/server.py route addition.
- W2 launch gate **blocked on operator signature** on W1. Drafter
  authors W2 plan-doc-amendment + W2 executor prompt after operator
  signs.

`workstream_complete` event NOT emitted from this session. Operator
sign-off precedes the emit.

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-25T15:23:09Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit halt)
Structural closures acknowledged: F-0.2.18-W1-004, F-0.3.1-W0-001, F-0.3.1-W0-002 (D8-verified registered_count=20), F-0.3.1-W0-004
Partial closures acknowledged: F-0.3.1-W0-003 (OTEL local; W2 Beacon migration completes), F-0.3.1-W0-005 (sys.path probe; W2 pip install -e completes)
New carry-forward acknowledged: F-0.3.1-W1-001 (cosmetic; nomic-embed chunk-size cap on 1 of 53 artifacts; W2 or 0.3.2 chunking refinement)
Drafter arbitration acknowledged: F0 (D2) F-0.2.17-W6-001-style retrieval-relevance failure; F1 (F-0.2.17-W5-001) F-0.2.18-W0-008 narrative-lift shape; both join 0.3.2 audit-machinery cluster
Auditor architecture progression acknowledged: bootstrap test 11; first non-vacuous filter-eligibility check in 0.3.1; no W4-0.2.17 filter regression
W2 launch gate: lifted on workstream_complete emit
