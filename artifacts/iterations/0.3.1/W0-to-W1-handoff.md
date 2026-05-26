# W0 → W1 drafter handoff

**Authored:** 2026-05-25 (W0 close + 1)
**Author:** executor (claude-code on a8cos)
**For:** drafter (claude-web) — W1 plan-doc refinement + executor prompt authoring
**State:** W0 closed (pass_with_findings, workstream_complete emitted). W1
launch gate awaiting operator sign + drafter W1 prompt.

This brief consolidates everything drafter needs to author W1 without
re-investigating the W0 close state. Plan-doc §W1 (substrate freshness
telemetry, F-0.2.18-W1-004 closure) is the baseline scope; this handoff
documents the scope expansions + substrate state W1 must build on.

---

## Scope expansions for W1 (beyond plan-doc §W1 baseline)

### 1. `aho rag bootstrap` deliverable (closes F-0.3.1-W0-002)

W0 D9 surfaced that chromadb pip-install creates the module but does not
ingest the canonical artifact set into the per-project ChromaDB collection.
Result: every detected reference in the W0 acceptance archive returned
`status=unverified` (registered_count=0 / detected_count=26). Captured as
F-0.3.1-W0-002.

W1 deliverable shape (drafter to refine):

- `aho rag bootstrap` subcommand (or `bin/aho-rag-bootstrap`) that ingests
  the canonical artifact set into the per-project ChromaDB collection on
  a fresh chromadb install:
  - `artifacts/iterations/<v>/carry-forwards-<v>.md` for v in active set
  - Plan-docs (`aho-plan-<v>.md`) for v in active set
  - ADRs at `artifacts/adrs/*.md`
  - Close notes at `artifacts/iterations/<v>/W*-close-note.md`
  - Iteration-close notes at `artifacts/iterations/<v>/iteration-close-<v>.md`
- W1 self-audit closure gate: RAG enrichment shows `registered_count > 0`
  for known-registered IDs. Canonical baseline ID: `F-0.2.17-W1-003` (the
  Pillar 11 incident, broadly cited across the 0.2.17-0.2.18 corpus).
- Idempotent: re-running on a populated collection refreshes embeddings,
  doesn't duplicate documents.
- W1 substrate-freshness probe extends to include
  `aho.observable.chromadb_collection_doc_count` per project — surfaces on
  dashboard alongside the 10 plan-doc substrate facts.

### 2. D0 substrate-verification deliverable (closes F-0.3.1-W0-001 partially)

W0 D9 surfaced via drafter arbitration: every future W prompt must include
a D0 substrate-verification step before any other work. F-0.3.1-W0-001
captured the drafter chat-side process improvement.

Structural closure path through W1+W2:

- **W1 contribution:** `bin/aho-doctor` (or extend the existing one) adds
  the substrate-verification probe set: chromadb importable, ollama models
  present per tier.json bundle, broker socket present, audit dependencies
  importable, sys.path has no stale legacy entries.
- **W2 contribution:** `install.fish --check` mode wraps the same probe
  set as a pre-W invocation gate. install.fish becomes the canonical
  pre-flight surface; per-W-prompt D0 language remains as a documentary
  reminder, not a structural enforcement.
- **W1 self-audit gate:** running `bin/aho-doctor` on a8cos returns
  zero substrate-state findings (post-`aho rag bootstrap`).

---

## Substrate observations from W0 close emit (drafter decides whether to capture)

These surfaced during the workstream_complete emit at W0 close. Not
captured as new carry-forwards in W0 — drafter to arbitrate whether
to fold into existing F-0.2.18-W1-004 / W1 scope, capture as new W1
opening carry-forwards, or fold into W2.

### Observation 1: canonical-root `.aho-checkpoint.json` absent on a8cos

`emit_workstream_complete` resolved `find_project_root()` correctly to
`/home/kthompson/Development/Projects/socfoundry/aho` but found no
`.aho-checkpoint.json` at that path. The fail-soft code path skipped the
checkpoint advance silently. Event landed in event log correctly; the
state-machine's per-workstream completion state did not advance.

A stale legacy checkpoint exists at
`/home/kthompson/dev/projects/aho/.aho-checkpoint.json` (mtime
2026-05-16, content: iteration 0.2.16, W2=in_progress). Untouched by
the emit because `find_project_root()` returned the canonical path,
not the legacy.

**Suggested disposition:** W1 scope or W2 scope — either
`aho install` writes an initial `.aho-checkpoint.json` at the canonical
root (W2 install.fish work), OR substrate-freshness probe surfaces
"checkpoint file present at canonical root" as fact #11 (W1 telemetry).
Both work; drafter picks.

### Observation 2: OTEL collector at 127.0.0.1:4317 unreachable from a8cos

W0 close emit's OTLP span export failed with `StatusCode.UNAVAILABLE`
(3 retries). The emit succeeded structurally (event landed in event
log file) but trace telemetry was lost.

Plan-doc §W1 already lists "NZXTcos OTLP collector bind" as substrate
fact #2 to probe. With NZXTcos decommissioned per CLAUDE.md §Deployment
hosts (NZXTcos no longer the OTLP collector substrate host), the
endpoint needs re-binding. Three options:

- A) Stand up an a8cos-local OTEL collector and bind to
  `100.124.234.113:4317` (or localhost). Lowest friction; loses
  cross-host aggregation.
- B) Stand up a p3cos-local OTEL collector and bind to
  `100.84.122.100:4317`. Pairs with W3 partial-tier deployment;
  preserves cross-host aggregation at a single point.
- C) Each base-tier host runs a local collector; p3cos aggregates.
  Most operational; matches the partial-tier-as-aggregator model.

**Suggested disposition:** W1 substrate-freshness fact #2 expands to
include collector-endpoint-reachable probe + drafter+operator pick the
endpoint architecture. Could be a fast W1 deliverable or punt to W3 if
the p3cos-aggregator option wins.

### Observation 3: sys.path includes stale legacy entry

a8cos host Python `sys.path` includes
`/home/kthompson/dev/projects/aho/src` (legacy pre-migration path).
The aho==0.2.18 editable install in
`~/.local/lib/python3.14/site-packages/aho-0.2.18.dist-info/direct_url.json`
points at `file:///home/kthompson/dev/projects/aho` (the legacy path).
Imports still resolve correctly because the executor probe scripts
do `sys.path.insert(0, str(ROOT / "src"))` before importing aho, but
the editable-install metadata is stale.

**Suggested disposition:** W2 install.fish refactor scope —
`pip install --user --break-system-packages -e ~/Development/Projects/socfoundry/aho`
to re-install editable pointing at the canonical path, then verify
`sys.path` no longer includes the legacy entry. Could absorb as a
substrate-hygiene check in `bin/aho-doctor`.

---

## Substrate state at W0 close (for W1 baseline)

W1 inherits this state on a8cos. Drafter does not need to re-verify
in the W1 prompt; the W1 D0 substrate-verification step does the
runtime probe.

| Component | State at W0 close |
|---|---|
| Host | a8cos (GEEKOM A8 MAX, base tier, CachyOS 7.0.9-1) |
| chromadb | 1.5.9 installed in host Python (pip --user --break-system-packages) |
| chromadb collection (per-project) | empty (0 documents) — F-0.3.1-W0-002 W1 closure |
| ollama llama3.2:3b | warm in runner pool |
| ollama nomic-embed-text | warm in runner pool |
| Timeout posture | `AHO_COUNCIL_EMBED_TIMEOUT_S=600` + `AHO_COUNCIL_AUDIT_TIMEOUT_S=600` env-var posture (CPU-only inference on Radeon 780M; ~556s observed latency on 27KB W0 acceptance archive) |
| Broker | `aho-secrets-broker.service` active (running) |
| tier.json | `{host_id: a8cos, tier: base, bundle: [llama3.2:3b, nomic-embed-text]}` |
| OTEL collector endpoint | unreachable at 127.0.0.1:4317 (NZXTcos decommission; per Observation 2) |
| Canonical-root checkpoint | absent (per Observation 1) |
| CLAUDE.md.0.2.18-archive | present at repo root (sha `43e72947…`) |

---

## Carry-forward state at W0 close

- **carry-forwards-0.2.16.md** post-W0 sha:
  `e4c6a1d8e579329e827ee869fdd7bc5623dd494aa006b7c4828d1f5a1a87d7c5`
  (970 → 991 lines; 37 → 39 canonical entries; +2 W0 entries)
- **Two new W0 carry-forwards landed** in two `appended_new_section`
  blocks (writer didn't find existing `## Target: 0.3.1 W1` or
  `## Target: 0.3.1 W1-W7 + 0.3.2+` headings):
  - F-0.3.1-W0-001 (drafter substrate-prerequisite gap; target =
    `0.3.1 W1-W7 + 0.3.2+`)
  - F-0.3.1-W0-002 (ChromaDB collection empty post-install;
    target = `0.3.1 W1`)
- **Reindex hooks fired ok for both appends.** The reindex hook
  indexes the carry-forwards file specifically; collection-level
  bootstrap (per F-0.3.1-W0-002) is still the W1 closure target.

W1 closes F-0.3.1-W0-002 + F-0.2.18-W1-004 + partial F-0.3.1-W0-001
(via `bin/aho-doctor` substrate-verification probe set).

---

## Adversarial Authorship continuity notes

- **Auditor seat for W1 on a8cos:** in-container llama3.2:3b at base
  tier with RAG + filter + anti-rubber-stamp extensions. After
  `aho rag bootstrap` lands, W1 self-audit RAG enrichment should
  show `registered_count > 0` for the first time in 0.3.1 — that's
  the W1 closure gate for F-0.3.1-W0-002.
- **Filter-regression check baseline for W1:**
  - Filter eligibility: `registered_count > 0` ✓ (post-bootstrap)
  - Filter fires correctly on fake-ID-on-registered shapes (no
    regression of the W4-0.2.17 lock-in)
  - Anti-rubber-stamp extensions (`_GIT_OP_ENFORCEMENT_SENTINELS`,
    `_RAG_STATUS_ECHO_PATTERN`, `unsupported_halt_downgrade`) still
    structurally enforced
- **Expected latency on a8cos:** ~9 min per W-level self-audit on
  similarly-sized acceptance archives. Plan W1 wall-time accordingly.
- **F-0.2.18-W0-008 narrative-lift residual:** W1 acceptance archive
  will contain narrative documenting the W0 D9 chromadb-absent halt
  + remediation. Expect the auditor may surface narrative-lift
  findings on that prose. Drafter arbitrates per F-0.2.18-W0-008
  precedent (small-model semantic-discrimination limit; pattern
  captured, deferred to 0.3.2 audit-machinery iteration).

---

## Pillar 11 amended scope (carry forward to W1 prompt)

Per drafter retraction on 2026-05-24 (W0 D9 arbitration), Pillar 11
halt-and-surface scope for executor host actions is now the five-item
canonical list:

1. Git operations (commit / push / merge / rebase / tag / add / gh pr *)
2. Secret decryption (broker contract is the only sanctioned path;
   `aho secrets-test` returns SHA-256 fingerprints, not values)
3. /etc/sudoers modifications
4. Customer-lane crossings (corporate-vs-sovereign-vs-customer
   contamination)
5. Hardware procurement + disruptive reboots

**Substrate component installation is executor scope** — chromadb
1.5.9 install at W0 D9 is the precedent. Future W prompts should
say so explicitly to avoid re-litigating mid-workstream.

Formal Pillar 10 + 11 amendments + new Pillars 12 + 13 land at W6
ADR consolidation per drafter prior arbitration; the W0 D9 chromadb
halt is the motivating incident in the ADR rationale section.

---

## Recommended W1 deliverable list (drafter to refine + reorder)

This is executor-side scoping input; drafter authors authoritative
plan-doc + executor prompt.

- **D0 — Substrate verification.** Run `bin/aho-doctor` (or new
  equivalent) probing the W0-close-substrate-state table above. Halt
  on any missing required component (chromadb, ollama models per
  tier.json bundle, broker socket, audit dependencies).
- **D1 — `aho rag bootstrap` deliverable** (closes F-0.3.1-W0-002).
- **D2 — `src/aho/observability.py` + `record_observable` API** (plan-doc §W1 D1).
- **D3 — OTEL gauge `aho.observable.last_verified_age_seconds`** (plan-doc §W1 D2).
- **D4 — `bin/aho-probe-substrate`** fish wrapper probing the 10 facts +
  observation #2's OTEL-endpoint-reachable probe (plan-doc §W1 D3 +
  Observation 2 expansion).
- **D5 — Dashboard surface** for per-fact ages + chromadb collection
  doc-count + (optionally) checkpoint-file-present (Observation 1)
  (plan-doc §W1 D4 + scope expansions).
- **D6 — install.fish integration** (plan-doc §W1 D5).
- **D7 — Unit tests** at `artifacts/tests/test_observability.py`
  (plan-doc §W1 D6).
- **D8 — W1 self-audit** by base-tier auditor on a8cos. RAG
  enrichment shows `registered_count > 0` on F-0.2.17-W1-003 as the
  F-0.3.1-W0-002 closure gate.

Eight deliverables; W1 plan-doc budget 4-8h overnight per plan-doc
§W1.

---

## Open arbitration points for drafter+operator

1. OTEL collector endpoint architecture post-NZXTcos-decommission
   (W1 vs W3 scope; A/B/C choice from Observation 2).
2. Whether canonical-root checkpoint absence (Observation 1) lands
   in W1 telemetry or W2 install.fish work.
3. Whether the legacy editable-install drift (Observation 3) lands
   in W1 doctor probe or W2 install.fish re-install.
4. Whether to capture Observations 1-3 as new W0-closing carry-forwards
   (F-0.3.1-W0-003 / W0-004 / W0-005) for traceability, or fold into
   W1 deliverable language without new IDs.

---

## Cross-references

- `artifacts/iterations/0.3.1/aho-plan-0.3.1.md` §W1 — baseline scope
- `artifacts/iterations/0.3.1/acceptance/W0.json` — W0 acceptance
  (sha `ab37497914bb9b19…`); deliverables[D9].drafter_review_note has
  per-finding arbitration
- `artifacts/iterations/0.3.1/audit/W0.json` — verbatim llama
  disposition (sha `9749cfed8fd5268e…`, UNTOUCHED)
- `artifacts/iterations/0.3.1/W0-close-note.md` — drafter-arbitrated
  pass_with_findings narrative (sha `569187af00ba5292…`)
- `artifacts/iterations/0.3.1/carry-forward-fold-in.md` — pre-iteration
  carry-forward inventory (sha `a0137d18731973…`)
- `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` — canonical
  carry-forward registry (sha `e4c6a1d8e579329e…`, post-W0 appends)
- `artifacts/adrs/0011-substrate-freshness.md` — lightweight tier ADR
  (W0 placed; W6 finalization scope)
- `artifacts/adrs/0012-chain-of-trust-l5.md` — Chain of Trust L5 ADR
  (W0 placed; W6 finalization scope)
