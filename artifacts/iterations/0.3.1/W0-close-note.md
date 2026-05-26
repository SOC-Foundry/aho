# 0.3.1 W0 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `halt`).

W0 acceptance archive sealed at
`artifacts/iterations/0.3.1/acceptance/W0.json`.
W0 audit archive sealed at
`artifacts/iterations/0.3.1/audit/W0.json` with
`disposition: "halt"` (llama self-audit verbatim — driven by F0
narrative-lift of the resolved D9 chromadb-absent halt + F1
ADR-0011 unverified status echo against an empty RAG collection).
Drafter (claude-web) arbitrated both findings and arbitrated
disposition to `pass_with_findings`. Two new W0 carry-forwards
added (W0-001 drafter substrate-prerequisite gap; W0-002 ChromaDB
collection empty post-install). Sealed shas (verified at
close-note authoring time):

- acceptance archive sha256:
  `ab37497914bb9b194e7434138bd88a9d3a1278185d1cb37dd11836983731a7ff`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `9749cfed8fd5268e0facf36915459f616200e7c43de21ff778f75f9e83115e14`

Audit archive (`audit/W0.json`) is UNTOUCHED post-emit. The
disposition field reads `halt`; drafter arbitration is recorded
only in the acceptance archive's D9 `drafter_review_note` block +
`carry_forwards_added` entries, and in this close note's prose.
Per Adversarial Authorship sealed-archive convention, audit
archives are not amended after emit — corrections and arbitrations
land in acceptance evidence and close-note prose, never in the
audit JSON.

## Workstream scope

W0 is the iteration's documentary substrate: plan-doc placement,
ADR sketches (ADR-0011 substrate-freshness + ADR-0012 chain-of-trust
L5 placement), CLAUDE.md rewrite, carry-forward fold-in inventory,
F-0.2.17-W6-002 closure-status confirmation, carry-forwards-0.2.16.md
initial-state capture, W0 self-audit. Nine deliverables (D1-D9). No
code-change scope; no carry-forward closures within W0 itself.

Eight of nine deliverables (D1-D8) completed cleanly against
operator-pre-placed inputs. D9 produced two halts mid-execution that
were resolved within-session (chromadb absent → drafter Pillar 11
arbitration → executor install; subsequent embed timeout at 120s →
bumped to 600s for CPU-inference latency). Final D9 invocation
emitted at 556316ms latency with the disposition above.

## D9 self-audit findings

Two model findings from the in-container llama auditor on a8cos:

- **F0 (model id `D9`, severity critical):** "The executor invoked
  the audit primitive with RAG enrichment enabled, but the chromadb
  module is absent from the a8cos host Python, causing the audit to
  halt." This is narrative-lift of the resolved D9 chromadb-absent
  halt — the auditor lifted the acceptance archive's documentary
  prose (describing the now-resolved initial halt) as a current
  finding. Same shape as F-0.2.18-W0-008 (small-model
  semantic-discrimination limit, deferred to 0.3.2 audit-machinery
  iteration). **Drafter arbitration: false positive; no new
  carry-forward; pattern already captured.**

- **F1 (model id `ADR-0011`, severity important):** "The artifact
  references ADR-0011 as a registered reference, but its status is
  unverified in the project context." Real substrate-state gap:
  ChromaDB was just-installed during D9 remediation; the project
  collection contains zero documents. RAG enrichment ran structurally
  (`detected_count=26`, `registered_count=0`, `unverified_count=26`)
  but operationally meaningless until the canonical artifact set is
  ingested. **Drafter arbitration: real substrate gap; captured as
  new F-0.3.1-W0-002.**

Neither finding is the fake-ID-on-registered shape. The W4-0.2.17
deterministic post-hoc filter check passes vacuously — filter
eligibility requires `registered_count > 0` and the collection is
empty, so the filter correctly did not fire on the 2 model findings.
No W4-0.2.17 filter regression.

## Carry-forwards added

Two new carry-forwards from W0 (both surfacing the substrate
prerequisite + bootstrap gaps in the W0 sequence, not defects in W0
deliverables themselves):

- **F-0.3.1-W0-001 (important) — Drafter substrate-prerequisite gap.**
  W0 prompt (drafter, claude-web) assumed a8cos had inherited
  NZXTcos's substrate via install.fish but did not include an
  explicit pre-flight substrate-verification step in the W0 sequence.
  Surfaced as chromadb-absent halt at D9 first invocation. During
  arbitration, drafter retracted the W0 prompt's over-broad Pillar 11
  interpretation: Pillar 11 scope is git operations only, plus secret
  decryption, /etc/sudoers modifications, customer-lane crossings,
  hardware procurement, disruptive reboots. Substrate component
  installation is executor scope going forward across 0.3.1. Closure
  mechanism: every future W prompt includes a D0
  substrate-verification deliverable that probes required components
  (chromadb, ollama models present, broker socket, audit dependencies
  importable) before any other work. Drafter chat-side process
  improvement applied retroactively to remaining 0.3.1 workstreams
  (W1-W7) and canonical pattern for 0.3.2+.

- **F-0.3.1-W0-002 (important) — ChromaDB iteration-context collection
  empty post-install.** RAG enrichment returns all-unverified until
  bootstrap. chromadb pip install creates the python module but does
  NOT ingest the canonical artifact set (carry-forwards-0.2.16.md,
  plan-docs, ADRs, close-notes) into the project collection. The
  audit primitive's RAG enrichment queries the empty collection and
  returns 0 hits per reference. Closure mechanism: 0.3.1 W1
  substrate-freshness scope expands to include `aho rag bootstrap`
  (or equivalent) deliverable that ingests the canonical artifact set
  on a fresh chromadb install. Closure verified when W1 self-audit
  RAG enrichment shows `registered_count > 0` for known-registered IDs
  (e.g., F-0.2.17-W1-003). Distinguishable from F-0.2.17-W6-001
  (lookup-ranking-on-opaque-IDs) by: W6-001 returns SOME registered
  refs from a populated collection; W0-002 returns ZERO registered
  refs because the collection itself is empty.

## Carry-forwards closed

None in W0 scope. W0 is documentary placement; closure work is
distributed across W1 (substrate freshness, ChromaDB bootstrap),
W2 (install.fish tier-aware refactor + pacman.conf pin + syncthing
v1.30.0 doctor probe), W6 (ADR amendments), W7 (code-change
closures). Pre-iteration F-0.2.17-W6-002 confirmed already-closed at
D7 via `src/aho/council/embed.py:38` `DEFAULT_TIMEOUT_S = 120` with
explicit docstring attribution; no W7 fold-in needed.

## Substrate state at close

- **Host:** a8cos (GEEKOM A8 MAX, AMD Ryzen 9 8945HS, Radeon 780M iGPU,
  base tier, CachyOS 7.0.9-1).
- **chromadb 1.5.9** installed on a8cos host Python (python3.14) via
  `pip install --user --break-system-packages` — matches existing
  aho==0.2.18 install posture (INSTALLER=pip; `--break-system-packages`
  needed for PEP 668 externally-managed-environment override on Arch-
  derivative). Transitive deps: kubernetes 36.0.0, onnxruntime 1.26.0,
  bcrypt 5.0.0, mmh3 5.2.1, uvicorn 0.47.0, watchfiles 1.2.0,
  websockets 16.0, plus standard build/typer/pydantic-settings stack.
- **ollama models live:** llama3.2:3b (2.0GB Q4_K_M, base-tier auditor
  seat) + nomic-embed-text (274MB F16, council embed seat). Both warm
  in the runner pool (ollama processes 82009 + 82216 active at close).
- **AHO_COUNCIL_EMBED_TIMEOUT_S + AHO_COUNCIL_AUDIT_TIMEOUT_S** bumped
  to 600 during D9 re-invocation. CPU-only Ollama inference on
  Radeon 780M iGPU is the bottleneck. The 600s envelope is comfortable
  for the 27KB acceptance archive at ~556s observed latency; W1-W7
  audits on similarly-sized artifacts should use the same env-var
  posture until GPU acceleration lands (out of 0.3.1 scope).
- **Misplaced ADR duplicates removed** from `artifacts/iterations/0.3.1/`
  (operator pre-placement artifacts at `0011-substrate-freshness.md`
  and `0012-chain-of-trust-l5.md` were stale W0-drafter-outputs staging
  copies). Canonical ADR placements at `artifacts/adrs/0011-substrate-
  freshness.md` and `artifacts/adrs/0012-chain-of-trust-l5.md` verified
  intact.
- **CLAUDE.md.0.2.18-archive** present at repo root, reconstructed from
  git HEAD (sha `43e72947a5f32596eca0360226c89915dac45d575506f33031e4f2335025ce75`,
  170 lines) via read-only `git show HEAD:CLAUDE.md`. Working-tree
  CLAUDE.md is the 0.3.1 rewrite (181 lines, all 11 grep-delta checks
  passing case-insensitive).
- **aho-secrets-broker.service** active (running) on a8cos at close.
- **`~/.config/aho/tier.json`** present with `{host_id: a8cos, tier:
  base, bundle: [llama3.2:3b, nomic-embed-text]}`.

## Auditor-seat continuation

W0 D9 is the sixth deployment of the in-container llama auditor in
the architecture progression — bootstrap test 10 — counting from the
W4-of-0.2.17 stabilization of the post-hoc filter primitive:

- **W4 of 0.2.17 baseline:** deterministic post-hoc filter on the
  finding list. First structural closure of the fake-ID-on-registered
  shape.
- **W5 of 0.2.17 second deployment:** filter eligible (16 registered
  IDs), ran on every model finding, `suppressed_count=0`.
- **W6 of 0.2.17 third deployment:** filter eligible (9 registered
  IDs), ran on every model finding, `suppressed_count=0`. Halt
  disposition driven by F-0.2.17-W4-001 unverified surface; drafter
  arbitration revealed scope distinction → new F-0.2.17-W6-001.
- **W0 of 0.2.18 fourth deployment:** v1/v2/v3 audit cycle closed
  three new structural shapes (F-0.2.18-W0-005 git-op enforcement
  narration / W0-006 RAG status echo / W0-007 unsupported halt
  downgrade). Filter primitive extended with `_GIT_OP_ENFORCEMENT_
  SENTINELS`, `_RAG_STATUS_ECHO_PATTERN`, and `unsupported_halt_
  downgrade` rule. Narrative-lift residual operator-arbitrated as
  F-0.2.18-W0-008.
- **W2 of 0.2.18 fifth deployment:** filter eligible against
  install.fish substrate work; further surfaced F-0.2.18-W2-002
  through W2-009 carry-forwards (closing in 0.3.1 W2 + deferred to
  0.3.2 audit-machinery iteration).
- **W0 of 0.3.1 sixth deployment (this one):** filter eligible
  check returned `filter_eligible=false` due to empty collection
  (`registered_count=0`). Filter correctly did not fire on the 2
  model findings — the regression check passes vacuously because the
  registered-ID-list is empty. The halt disposition was real (auditor
  lifted documentary narrative + surfaced collection-empty state)
  but neither finding is a defect in W0 deliverables; both surface
  substrate gaps in the auditor's RAG dependency chain that 0.3.1 W1
  closes structurally.

The architecture's halt-and-surface invariant continues to function
correctly. The 2 model findings, the empty-collection state, and the
556s latency are all real substrate signals. The drafter arbitration
re-framed both findings within their correct carry-forward categories
without touching the sealed audit archive.

## Forward-looking notes

**For W1 (substrate freshness telemetry + F-0.2.18-W1-004 closure):**

The substrate-freshness scope expands beyond the plan-doc's 10
substrate facts (tailnet domain, OTLP collector bind, image FQDN, SSH
host keys, podman version, broker socket, ChromaDB mount, Ollama
endpoint, 1Password agent socket, CloudflareWARP DNS) to include
**`aho rag bootstrap`** (or equivalent) as a structural deliverable
closing F-0.3.1-W0-002. The deliverable ingests the canonical artifact
set (carry-forwards-0.2.16.md + plan-docs across active iterations +
ADRs at `artifacts/adrs/` + close notes) into the per-project ChromaDB
collection. Closure gate: W1 self-audit on a8cos shows
`rag_enrichment.registered_count > 0` for a known-registered ID
(F-0.2.17-W1-003 is the canonical baseline). Install.fish-as-pre-flight
design incorporates `aho rag bootstrap` as a step alongside
chromadb-importable verification, ollama-models-present verification,
broker-socket verification, and audit-dependencies-importable
verification — closing F-0.3.1-W0-001 structurally via install.fish
`--check` mode rather than via per-W-prompt D0 verification language.

**For W6 (ADR consolidation + harness/base.md amendment):**

Pillar 10 + Pillar 11 amendments + new Pillars 12 + 13 land at W6 as
ADR amendment to `artifacts/harness/base.md` per drafter chat
arbitration this morning. The W0 D9 chromadb halt + drafter Pillar 11
retraction serves as motivating incident in the ADR rationale section.
Specifically: Pillar 11 amendment narrows the executor halt-and-surface
surface to git operations, secret decryption, /etc/sudoers, customer-
lane crossings, hardware procurement, and disruptive reboots — the
five-item canonical list. Substrate component installation moves into
executor scope explicitly. New Pillars 12 + 13 (TBD per drafter
arbitration; scope to be set at W6 prompt-authorship time) sit
alongside the amended 10 + 11 in the new harness/base.md revision.

## State at close

- Acceptance archive sealed: sha
  `ab37497914bb9b194e7434138bd88a9d3a1278185d1cb37dd11836983731a7ff`
  (`audit_status: pending_drafter_review`; transitions to next state
  at operator sign + workstream_complete emit).
- Audit archive sealed and UNTOUCHED: sha
  `9749cfed8fd5268e0facf36915459f616200e7c43de21ff778f75f9e83115e14`.
- Carry-forwards file update **pending operator review** — two new
  entries (F-0.3.1-W0-001 + F-0.3.1-W0-002) to append via
  `aho.gap_carry_forward_writer.append_to_file` at operator
  discretion. Per Pillar 11, executor does not perform the append
  unilaterally; the append touches a tracked file and is part of the
  carry-forward state-machine that the operator owns.
- carry-forward fold-in inventory at
  `artifacts/iterations/0.3.1/carry-forward-fold-in.md` sealed at sha
  `a0137d18731973920c4e9311e28014a742034b8e1ea524439ee3bc978c47cdd6`.
- W1 launch gate **blocked on operator signature** on W0. Drafter
  authors W1 plan-doc refinement + W1 executor prompt after operator
  signs.

`workstream_complete` event NOT emitted from this session. Operator
sign-off precedes the emit.

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-24T12:44:34Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit halt)
Carry-forwards added acknowledged: F-0.3.1-W0-001 (drafter substrate-prerequisite gap), F-0.3.1-W0-002 (ChromaDB collection empty post-install)
Drafter arbitration summary acknowledged: F0 narrative-lift → F-0.2.18-W0-008 pattern (0.3.2-deferred); F1 unverified-status echo → F-0.3.1-W0-002 new substrate gap
Filter-regression check acknowledged: passes vacuously (registered_count=0, filter correctly did not fire)
Pillar 10/11 amendments + new Pillars 12/13 acknowledged for W6 ADR consolidation scope
W1 launch gate: lifted on workstream_complete emit
