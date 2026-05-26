# 0.3.1 W2 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `halt`).

W2 acceptance archive sealed at
`artifacts/iterations/0.3.1/acceptance/W2.json`.
W2 audit archive sealed at
`artifacts/iterations/0.3.1/audit/W2.json` with
`disposition: "halt"` (llama self-audit verbatim - driven by two
auditor-machinery findings, both expected manifestations of the
0.3.2 audit-machinery iteration cluster). Drafter (claude-web)
arbitrated both findings and arbitrated disposition to
`pass_with_findings`. One new carry-forward added during D1-D8
execution (F-0.3.1-W2-001 emulator tooling gap; cosmetic). Sealed
shas (verified at close-note authoring time):

- acceptance archive sha256:
  `f213db07c17cca9a9ff565aa066af35813ba7f54ddf7eca2988b0a8a2cc51d34`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `1d98fa0d4d8acbc81a8fc1367aac09bba1aca1baf2e5c2f513a2ad47756e0fd6`

Audit archive (`audit/W2.json`) is UNTOUCHED post-emit. The
disposition field reads `halt`; drafter arbitration is recorded
only in the acceptance archive's D8 `drafter_review_note` block +
`carry_forwards_added` entries, and in this close note's prose.
Per Adversarial Authorship sealed-archive convention, audit
archives are not amended after emit.

## Workstream scope

W2 ran a two-track convergence model: Track A executor-side code
(env-driven from the start) and Track B operator-side substrate
provisioning (Beacon endpoint + token, notjustavar Firestore +
IAM). Eight deliverables per W2-plan-doc-amendment.md (post-W1-close,
post-Beacon-integration-feedback):

- **D1** - env-driven OTLP endpoint configuration (logger.py reads
  `OTEL_EXPORTER_OTLP_ENDPOINT`; stale 0.2.10-era wrappers + templates
  deleted; systemd EnvironmentFile directive; new
  `docs/operations/otel-telemetry.md`).
- **D2** - `~/.config/aho/beacon.env` + fish `conf.d` shim
  (deployment-private; resource attrs populated, endpoint + token
  commented pending Track B).
- **D3** - bidirectional alert bridge (Telegram outbound mirror to
  Beacon webhook + inbound `/beacon` relay to Telegram; backward
  compatible).
- **D4** - tenant-aware Firestore writer module (env-driven routing,
  cross-tenant guard, t_any_* convention, idempotent set; 9
  mock-based unit tests pass).
- **D5** - `aho-firestore-bootstrap` schema seed (1 marker + 5
  schema-definition docs; dry-run + idempotent).
- **D6** - install.fish tier-aware refactor (closes F-0.2.18-W2-002/
  003/004).
- **D7** - substrate-freshness fact #14 (Beacon reachability) +
  F-0.3.1-W0-005 closure (editable re-install).
- **D8** - pacman pin + syncthing v1.30.0 probe + W2 self-audit.

## D8 self-audit findings

Second non-vacuous audit on a populated collection (post-W1 D2
bootstrap). `registered_count=13` of `detected_count=21`;
`filter_eligible: true`; 0 suppressed; `unsupported_halt_downgrade:
false`; structural pre-checks all pass; latency 353285ms (~5.9min).

Two model findings from the in-container llama auditor on a8cos:

- **F0 (model id `D8`, severity info):** "claims to have closed
  F-0.2.18-W0-008 but the artifact does not corroborate." Auditor
  read the explicit "deferred to 0.3.2" mention of F-0.2.18-W0-008 as
  a closure claim. F-0.2.18-W0-008 narrative-lift pattern, already in
  the 0.3.2 audit-machinery iteration cluster. **Drafter arbitration:
  false positive; no new carry-forward.**

- **F1 (model id `F-0.3.1-W0-005`, severity critical):** "carry-forward
  ID unverified and not found in iteration-context collection." Real
  but expected. F-0.3.1-W0-005 was closed in D7 (sys.path editable
  re-install, confirmed by `aho-doctor --workstream W2` returning 8/8).
  The ID is in `carry-forwards-0.2.16.md` (appended during W1 carry-
  forward close) but bare-ID RAG retrieval returns 0 - the
  F-0.2.17-W6-001 cosine-ranking-on-opaque-IDs limitation. NOT a
  W0-005 closure defect; NOT a fake-ID-on-registered pattern (the
  filter correctly did not suppress because RAG classified the ID
  unverified, so it is not a "registered anchor + fake-ID phrase"
  match). Critical severity is auditor-verbatim (correct); operational
  reality is "known limitation manifested as expected."
  **Drafter arbitration: false positive; no new carry-forward.**

W4-of-0.2.17 filter regression check passes. F1's critical finding
correctly did not suppress: it is a real retrieval-ranking gap, not a
fabricated-ID-claimed-registered pattern. Independent verification:
F-0.2.18-W0-008 + F-0.2.18-W2-004 resolve registered with retrievals;
F-0.3.1-W0-005 resolves unverified with 0 retrievals despite being
present in the carry-forwards file.

Both findings join the existing 0.3.2 audit-machinery iteration
cluster (F-0.2.18-W0-008 narrative-lift + F-0.2.17-W6-001 retrieval-
ranking). W2 D8 F1 becomes additional motivating evidence for 0.3.2
scoping: a carry-forward closed and appended in W1 is not surfaceable
by bare-ID RAG query at W2 audit time, strengthening the case for an
ID-keyed metadata field at index time.

## Carry-forwards closed structurally in W2 (verified)

- **F-0.2.18-W2-002** - `bin/aho-models` tier-aware refactor.
  `_tier_name` + `_tier_models` read `~/.config/aho/tier.json` bundle;
  `_check_tier_capacity` gates the GPU requirement by tier (base: no
  GPU; partial: >=12GB; full: >=32GB). Verified: base tier on a8cos
  returns bundle `[llama3.2:3b, nomic-embed-text]`, capacity check
  passes without nvidia.
- **F-0.2.18-W2-003** - first-class `bin/aho-install-tier-manifest` +
  `src/aho/tier_manifest.py` (builds on `aho.tier_detect`). install.fish
  `tier_json_present` step delegates to it.
- **F-0.2.18-W2-004** - `templates/systemd/aho-secrets-broker.service.
  template`; `aho-systemd` daemons list extended with secrets-broker.
- **F-0.3.1-W0-005** - legacy sys.path drift. `pip install -e` on the
  canonical path; `direct_url.json` now points at the canonical repo;
  sys.path legacy entry gone; `import aho` resolves to canonical src;
  `python_sys_path_clean` probe flips fail -> pass;
  `aho-doctor --workstream W2` 8/8.

## Carry-forward code-closed, Track-B-gated for operational closure

- **F-0.3.1-W0-003** - OTLP endpoint to Beacon-aggregator migration.
  Code migration complete: env-driven `logger.py` + `beacon.env` +
  systemd `EnvironmentFile` + fish `conf.d` shim + substrate-freshness
  fact #14 reachability probe. Operational closure (Beacon actually
  reachable) gates on Track B endpoint + token provisioning by davidk.
  Until then aho falls back to the localhost default and fact #14
  reports `unreachable`.

## Carry-forward added in W2

- **F-0.3.1-W2-001 (cosmetic)** - Firestore emulator integration-test
  tooling gap. a8cos has firebase CLI 15.18.0 but no gcloud and no JRE,
  so neither emulator can run. Mock-based unit tests (9, via injected
  fake client) provide logic coverage; the emulator / real-Firestore
  integration test skips on the `FIRESTORE_EMULATOR_HOST_LIVE` gate.
  Target: 0.3.1 W3 / Track B convergence (install a JRE + emulator when
  real-Firestore integration becomes load-bearing) OR 0.3.2.

## Track B convergence table

All Track B gates blocked-not-failed at execution time; surfaced for
operator + davidk:

| Gate | State |
|---|---|
| D1 Beacon endpoint value | blocked - beacon.env endpoint commented; `otel_endpoint_configured` install step reports the gate; aho falls back to localhost default |
| D3 Beacon webhook URL | blocked - `BEACON_WEBHOOK_URL` unset; outbound mirror is a no-op; Telegram-only path unchanged; inbound `/beacon` endpoint live |
| D4 notjustavar + IAM integration | blocked - gcloud/JRE absent; notjustavar not verifiable; 9 mock unit tests pass; integration test skips |
| D5 notjustavar execution | blocked - execute gates on notjustavar live + service-account key in broker; dry-run reports 6 planned writes; execute exits 3 at the gate |

## Substrate state at close

- **Env-driven OTLP throughout:** `logger.py` reads
  `OTEL_EXPORTER_OTLP_ENDPOINT` (TLS auto-detect; localhost fallback);
  4 daemon systemd templates carry `EnvironmentFile=-%h/.config/aho/
  beacon.env`; `beacon.env` + fish `conf.d` shim source the resource
  attrs into interactive + systemd sessions.
- **Stale 0.2.10-era artifacts deleted:** `bin/aho-otel-up`,
  `bin/aho-otel-down`, `templates/otelcol-config.yaml`,
  `templates/systemd/aho-jaeger.service.template`,
  `templates/systemd/aho-otel-collector.service.template`.
- **`aho-doctor --workstream W2`: 8/8 required steps passing**
  (was 7/8 pre-W2; F-0.3.1-W0-005 closure flipped `python_sys_path_clean`).
- **install.fish tier-aware refactor complete;** tier.json schema
  unchanged (backward compat preserved); base-tier bundle correct on
  a8cos.
- **pacman IgnorePkg pin verified** (syncthing already in `[options]`
  on a8cos; `aho-pacman pin` idempotent no-op, no sudo); the privileged
  `pin-apply` half is surfaced to the operator for un-pinned hosts.
- **syncthing v1.30.0 probe live** (`syncthing_version_1_30_0` install
  step; v2.x trips it as a SCoT compliance regression).
- **Substrate-freshness facts expanded 13 -> 14:** fact #14
  `beacon_otlp_reachable` (TCP connect + outcome class ok / unreachable
  / auth_failed). Reports `unreachable` until Track B converges; the
  dashboard brick grid auto-renders 14 facts (panel iterates the
  snapshot).
- **google-cloud-firestore 2.27.0** installed (substrate component for
  the D4 writer).

## Auditor-seat continuation

W2 D8 is the **eighth deployment** of the in-container llama auditor -
**bootstrap test 12** in the architecture progression - and the
**second non-vacuous filter-eligibility check in 0.3.1**:

- **W1 D8 (first non-vacuous):** `registered_count=20` of 28;
  filter_eligible=true; 2 narrative-lift / retrieval-relevance findings.
- **W2 D8 (this one):** `registered_count=13` of 21;
  filter_eligible=true; 2 findings (narrative-lift + retrieval-ranking).
  Collection-warming continues (the registered/detected ratio reflects
  W2's reference mix, which cites more freshly-appended IDs).

The halt-and-surface invariant continues to function correctly. The D8
halt was earned (a real bare-ID RAG-resolution gap on F-0.3.1-W0-005)
but neither finding is a W2 deliverable defect. The W4-of-0.2.17
deterministic post-hoc filter remains structurally correct across eight
deployments: it suppresses the fake-ID-on-registered shape and does not
over-suppress on retrieval-ranking or narrative-lift failure modes
(which need the 0.3.2 structural fixes).

## Forward-looking notes

**For W3 (council-mining retrospective):** Pipeline runs against the
populated ChromaDB collection. Output (augmented gotcha registry with
human-right / council-right / human-wrong / council-wrong quadrants)
lands in notjustavar Firestore via the D4 `firestore_writer` module.
**First substantial Tachtech-tenant data write** - gates on Track B
Firestore + IAM convergence. If Track B is not ready at W3 launch,
drafter may rescope W3 to a deferred-execution shape: the writer +
bootstrap dry-run validates locally and the production write happens at
convergence.

**For W4 (Firestore schema dry-run):** Consumes W3 output, validates the
`t_any_*` indicator field shape against real ingest patterns.

**For W6 (ADR consolidation):** ADR-0013 candidate "Beacon as canonical
OTLP aggregator" - landed at W2, formal ADR captures the decision.
ADR-0014 candidate "aho multi-tenant data architecture" - design-doc
capturing the TTEOS / notjustavar / customer-codename pattern. Pillar 10
+ Pillar 11 amendments + new Pillars 12 + 13 land as a `harness/base.md`
version-bump. W2 D8 F1 (the F-0.2.17-W6-001 retrieval-ranking
manifestation) becomes additional motivating evidence in 0.3.2
audit-machinery iteration scoping at retrospective time.

## State at close

- Acceptance archive sealed:
  `f213db07c17cca9a9ff565aa066af35813ba7f54ddf7eca2988b0a8a2cc51d34`
  (`audit_status: pending_drafter_review`; transitions at operator sign
  + workstream_complete emit).
- Audit archive sealed and UNTOUCHED:
  `1d98fa0d4d8acbc81a8fc1367aac09bba1aca1baf2e5c2f513a2ad47756e0fd6`.
- Carry-forwards file update **pending operator review**: 4 structural
  closures (F-0.2.18-W2-002/003/004, F-0.3.1-W0-005) + 1 code-closed-
  Track-B-gated (F-0.3.1-W0-003) + 1 new entry (F-0.3.1-W2-001), to
  append via `aho.gap_carry_forward_writer.append_to_file` at operator
  discretion.
- W3 launch gate **blocked on operator signature** on W2 + Track B
  convergence (notjustavar Firestore + IAM for the first tenant data
  write).

`workstream_complete` event NOT emitted from this session. Operator
sign-off precedes the emit.
