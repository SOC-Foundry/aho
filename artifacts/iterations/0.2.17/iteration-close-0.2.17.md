# 0.2.17 iteration close

**Iteration:** 0.2.17
**Status:** closed
**Authored:** 2026-05-04 (post-W6 workstream_complete + post-W6-003
post-close-discovery append)
**Authoring agent:** claude-code (executor) under drafter (claude-web)
direction
**Crowns but does not duplicate:** seven workstream close notes
(W0–W6) and the canonical retrospective at
`docs/retrospectives/0.2.17.md`

## Summary

0.2.17 shipped the base-tier substrate on NZXTcos: a multistage
container image (`ghcr.io/soc-foundry/aho:0.2.17-rc2`,
manifest digest `sha256:b6dd0596…`) running on Podman, with a
host-mounted unix-socket secrets broker, host-side run-container
wrapper, and the full Adversarial Authorship state machine
operating across four roles — drafter (claude-web), executor
(claude-code on NZXTcos for W0/W2/W3/W4/W5/W6, gemini-cli for
external audit slots), auditor (in-container `llama3.2:3b` with
W3 RAG enrichment + W4 deterministic post-hoc filter), and
operator (Kyle).

Seven workstreams executed sequentially. All seven closed
`pass_with_findings`. All seven workstream close notes
(W0 through W6) operator-signed. Five deployments of the
in-container llama auditor primitive, with progressively-
stabilized infrastructure exercised against substantively
different audit-target shapes (see Materiality data below).
Adversarial-Authorship-at-base-tier is in production.

## Six-workstream summary

| WS | Title | D# | Disposition | acceptance sha256 | audit sha256 | close note sha256 | workstream_complete (UTC) |
|---|---|---|---|---|---|---|---|
| W0 | Substrate carry-forward closure + Podman runtime + hello-world container + Adversarial Authorship harness restart | 4 (+amendment B2.3) | pass_with_findings | `cd4e3f96…` (+ amendment `1be983ea…`) | `1e2b2f49…` | `b458fc4e…` | 2026-05-03T02:35:14 |
| W1 | Base container image build + secrets broker + k8s-readiness | 7 | pass_with_findings | `e4d076ee…` | `8b2771ac…` | `98f897ab…` | 2026-05-03T04:14:39 |
| W2 | Feedback loop wiring + ChromaDB integration + auditor-seat transition | 12 | pass_with_findings | `4a5ab02b…` | `b9c2f1bb…` | `b0fb1ccd…` | 2026-05-03T14:06:19 |
| W3 | Auditor-RAG integration (load-bearing fix from F-0.2.17-W2-006) | 5 | pass_with_findings | `9ed9a88a…` | `b3a4e2e6…` | `3a0c3c08…` | 2026-05-03T15:32:15 |
| W4 | Deterministic post-hoc filter on RAG-aware audit findings + claw3d brick rendering | 7 | pass_with_findings | `949908ff…` | `9d5ab9ec…` | `d7f73e03…` | 2026-05-03T19:55:36 |
| W5 | ADR consolidation + repo-resident component decomposition + repo-resident claw3d brick spec + 0.2.17 retrospective + W5 self-audit | 8 | pass_with_findings | `3ba22601…` | `5bd170e9…` | `1ce28b9a…` | 2026-05-04T03:30:29 |
| W6 | Final code-change closures: F-0.2.17-W1-001 secrets-test hash-fingerprint redesign + F-0.2.17-W4-001 ChromaDB re-index hook + final 0.2.17 self-audit | 3 | pass_with_findings | `b4d6287b…` | `bb7b1d1f…` | `f5b3a781…` | 2026-05-04T05:13:28 |

Per-workstream details, evidence, and findings live in their
respective close notes; this iteration-close note crowns the
chain rather than duplicating it.

## Carry-forwards state at iteration close

### Closed in iteration

- **F-0.2.17-W2-006** — Auditor reference-resolution gap (false
  positives on registered-anchor IDs without RAG context). Closed
  via W4 D1 deterministic post-hoc filter
  (`src/aho/council/audit_finding_filter.py`), which structurally
  drops findings where BOTH a registered anchor appears in the
  description AND a fake-ID phrase matches.

- **F-0.2.17-W3-001** — Small-model prompt-following inconsistency
  (W3 D4 RAG-replay surfaced auditor still flagging registered IDs
  as fake despite RAG enrichment context section in prompt). Closed
  by the same W4 D1 filter — same structural mechanism handles both
  failure modes deterministically.

- **F-0.2.17-W1-001** — `aho secrets-test` test-only subcommand
  printed decrypted secret value to stdout (Pillar 11 friction).
  Closed via W6 D1 hash-fingerprint redesign in `src/aho/cli.py`:
  subcommand now emits `{project, name, fingerprint, length,
  status}` JSON where `fingerprint` is SHA-256 first 8 hex of the
  decrypted value; the value itself never enters agent stdout.
  `aho:0.2.17-rc2` image rebuilt + pushed (manifest digest
  `sha256:b6dd0596…`). Four W1 D3 acceptance gates revalidated
  against rc2.

- **F-0.2.17-W4-001** — ChromaDB iteration-context index did not
  auto-refresh on `carry-forwards-0.2.16.md` updates. Closed AT
  THE DATA LAYER per drafter Option C arbitration in W6 D3 review.
  W6 D2 implementation: `src/aho/gap_carry_forward_writer.append_to_file`
  now calls `aho.rag.index_artifact` post-write; failure path
  emits a stderr warning + increments
  `aho.gap_carry_forward_writer.reindex_failures` OTEL counter,
  but the append still succeeds. Verified across **three
  production-shape dogfooding instances** (W6 close-note appends
  of W6-001 and W6-002 both `reindex_status: ok`; F-0.2.17-W6-003
  post-close append also `reindex_status: ok`). The audit-time
  RAG enrichment lookup-ranking surface that surfaces the file's
  unindexed-by-similarity behavior on opaque-ID queries is a
  separate defect captured below as F-0.2.17-W6-001.

### Carrying to 0.3.x base-tier hardening

- **F-0.2.17-W5-001** — Structural pre-check self-referential
  pattern. Confirmed across four occurrences inside 0.2.17
  (W3 D5 + W4 D7 + W5 D8 + W6 D3). Drafter recommendation: JSON
  path exclusion in pre-check scan (skip fields tagged as
  compliance-evidence prose); explicit and auditable.

- **F-0.2.17-W5-002** — Plan-doc / repo-convention path drift.
  Plan-docs occasionally specified paths (e.g. `docs/adr/`) that
  diverged from existing repo convention (`artifacts/adrs/`).
  Target: drafter chat-side process improvement + 0.3.x plan-doc
  convention notes.

- **F-0.2.17-W6-001** — Audit-time lookup ranking misses opaque-ID
  matches in the carry-forwards file. `audit_ref_lookup` retrieves
  top-24 chunks by cosine similarity then filters to literal-ID-
  containing chunks; opaque alphanumeric IDs (F-0.2.17-WN-NNN
  shape) carry low embedding signal, recency-weighting boosts
  current-iteration chunks over the 0.2.16 carry-forwards file,
  and a 158-chunk corpus has many higher-cosine competitors. The
  chunk containing the literal token IS in chromadb (verified
  twice independently in W6) but does not rank top-24, so
  status surfaces as `unverified`. Drafter-recommended fix:
  ID-keyed metadata field at index time so direct lookup avoids
  cosine entirely.

- **F-0.2.17-W6-002** — Council embed timeout default too tight
  under VRAM contention. Default
  `AHO_COUNCIL_EMBED_TIMEOUT_S=30s` in
  `src/aho/council/embed.py` is too short when nomic-embed-text
  cold-loads after qwen3.5:9b model swap on 8GB VRAM. Substrate
  condition (Ollama state hygiene, not council/embed defect).
  Disposition: bump default to 120s in 0.3.x or earlier.

- **F-0.2.17-W6-003** — Working-state files tracked in git repo
  (gitignore gap). `.aho-checkpoint.json` and
  `.claude/settings.json` were tracked by git despite being
  excluded from container layers via `.dockerignore`. Surfaced
  post-W6-close during iteration-close audit. Disposition:
  `.gitignore` should mirror `.dockerignore` working-state list;
  `git rm --cached` to untrack without local deletion. Not a
  Pillar 11 incident — no credentials or decrypted secrets in
  tracked files. Remediation already executed operator-side
  ahead of the operator's bulk-push at iteration close. Target:
  0.3.1 launch (early base-tier hygiene fix).

### Hard gate before 0.3.1 launch (out of iteration scope)

- **F-0.2.17-W1-003** — `ahomw:telegram_bot_token` rotation. The
  token was exposed to agent stdout during W1 D3 acceptance
  testing (the original incident that motivated W6's
  hash-fingerprint redesign). Rotation is operator-side, post-
  iteration-close, and does NOT block iteration close. The
  rotation is verified using the W6 D1 hash-fingerprint contract:
  pre-rotation fingerprint vs post-rotation fingerprint must
  differ. Surfaced at every workstream close (W1 → W2 → W3 → W4
  → W5 → W6 → this iteration close). Final pre-tsP3 hard gate.

## Materiality data summary

Five deployments of the in-container llama auditor primitive:

- **W2 baseline:** model only, no RAG enrichment. False positives
  on registered-anchor IDs (F-0.2.17-W2-006 surfaced).
- **W3 partial fix:** RAG enrichment via prompt context section.
  Closed 1 of 2 demonstrated false-positive shapes; W3 D4 replay
  surfaced F-0.2.17-W3-001.
- **W4 structural closure:** deterministic post-hoc filter
  (`audit_finding_filter.py`). Both W2-006 and W3-001 failure
  modes now caught.
- **W5 fourth deployment:** filter remains structurally narrow on
  documentation-heavy work (filter_eligible=true,
  registered_id_count=16, suppressed_count=0).
- **W6 fifth deployment:** filter remains structurally narrow on
  final-code-change work (filter_eligible=true,
  registered_id_count=9, suppressed_count=0).

The architecture's **halt-and-surface invariant** functioned
correctly across three distinct halt events inside the iteration:

- **W3 D5 self-audit replay** (filter pre-deployment) — auditor
  surfaced AUDIT-PILLAR11 self-referential structural pre-check
  fire; drafter arbitrated as documentation-prose-attesting-
  compliance, not real Pillar 11 violation.
- **W5 D8 self-audit** — auditor surfaced AUDIT-G081 +
  AUDIT-PILLAR11 (both self-referential structural pre-check
  fires); drafter arbitrated to `pass_with_findings`, captured
  recurring pattern as F-0.2.17-W5-001.
- **W6 D3 self-audit** — auditor surfaced F-0.2.17-W4-001
  unverified + AUDIT-PILLAR11; drafter Option C arbitration
  revealed scope distinction (W4-001 closes at data layer;
  lookup-ranking layer captured separately as F-0.2.17-W6-001).
  This was the iteration's most structurally interesting halt:
  the temporary `audit_status: blocked` window between executor
  halt and drafter arbitration was a real state-machine vertex,
  validating that executor cannot unilaterally advance the state
  machine past a halt condition.

In all three halts, drafter arbitration revealed scope
distinctions (auditor self-referential structural artifacts;
closure-of-different-defect framings) rather than overriding
auditor judgment. The auditor was not wrong in any of the three
cases — it surfaced real structural surfaces that warranted
arbitration. The pattern matters: **earned halts followed by
documented arbitration**, not silent overrides.

Bootstrap tests 1 through 7 all passed structurally (numbering
per W5/W6 close-note convention).

**N=5 below the N≥8 threshold per ADR-0010 — qualified
validation, not full validation.** ADR-0010 §N=4 caveat at W5
extends to §N=5 caveat at W6. Three more iterations of
auditor-seat data are required before the protocol meets the
canonical evidence threshold. Cite
`docs/retrospectives/0.2.17.md` for the complete materiality
narrative; it is the canonical iteration retrospective.

## Architecture artifact final disposition

The chat-side `aho-base-container-architecture.md` artifact
(historical input from pre-0.2.17 design conversations) is
**superseded** by repo-resident artifacts landed in W5:

- `docs/architecture/component-decomposition.md` (W5 D4) —
  per-component contract + tier groupings + host-mounted
  resources + provenance section. Provenance section serves as
  the W5 D7 supersession marker citing the chat-side artifact as
  historical input.
- `docs/architecture/claw3d-brick-spec.md` (W5 D5) — 10
  per-component bricks + red-conditions + materiality dashboard
  surfaces + role-collapse tripwire brick + four-surface
  anti-rubber-stamp dashboard.

Both are in `docs/architecture/` (net-new directory at W5).
ADRs continue to live at `artifacts/adrs/`, with three new/
amended ADRs in W5: `0007-containerization-architecture.md`
(amended with §Council roles), `0009-secrets-broker-boundary.md`
(new), `0010-materiality-measurement.md` (new). The chat-side
architecture artifact is no longer authoritative; the repo-
resident decomposition + brick spec + ADR-0007 amendment are.

## Adversarial Authorship state machine at iteration close

All seven `workstream_complete` events emitted to event log at
`/home/kthompson/.local/share/aho/events/aho_event_log.jsonl`:

- W0 — 2026-05-03T02:35:14
- W1 — 2026-05-03T04:14:39
- W2 — 2026-05-03T14:06:19
- W3 — 2026-05-03T15:32:15
- W4 — 2026-05-03T19:55:36
- W5 — 2026-05-04T03:30:29
- W6 — 2026-05-04T05:13:28

Checkpoint `last_event=W6_workstream_complete`. All seven
sealed acceptance archives + audit archives untouched throughout
iteration after their respective workstream_complete emits.

**Pillar 11 invariant: pass across all seven workstreams,
across all four roles.** Zero git operations by drafter,
executor, or auditor across the entire iteration. All commits,
PRs, and pushes operator-side. Image distribution
(podman push to ghcr.io) was the executor-prompt-authorized
exception — not a source-control git op. Decrypted secret values
never entered agent stdout in 0.2.17 except during the original
W1 D3 incident that motivated F-0.2.17-W1-003 (token rotation)
and F-0.2.17-W1-001 (subcommand redesign closed at W6).

Cross-project contamination vigilance held across the iteration:
zero kjtcom-construct leakage observed (e.g., no "10 IAO Pillars"
or `v10.66`-style version labels), per the discipline established
in 0.2.14 and reinforced by 0.2.15.

## 0.3.1 launch pre-conditions (non-blocking iteration close)

0.2.17 shipped base-tier substrate on NZXTcos (RTX 2080 SUPER
8GB). 0.3.1 deploys partial-tier on tsP3 (ThinkStation P3, RTX
2000 Ada 16GB). The following are operator-side post-iteration
steps; they do NOT block 0.2.17 close:

1. **F-0.2.17-W1-003 — token rotation (HARD GATE).** Rotate
   `ahomw:telegram_bot_token`. Verification path uses W6 D1
   hash-fingerprint contract: pre-rotation fingerprint vs
   post-rotation fingerprint must differ. The contract is in
   place; operator runs the rotation via existing
   `aho secret rotate` flow.

2. **tsP3 bootstrap via `install.fish`.** The `install.fish`
   script in the aho repo (last touched 0.2.6, inherited
   substrate) is the canonical bootstrap for any new Arch box,
   including bare tsP3. It handles podman, nvidia-container-
   toolkit, ollama, aho package install, broker setup,
   CDI config — anything in the substrate-bring-up surface.

3. **Image transfer to tsP3 — two patterns.**
   - **For tsP3 specifically (operator-immediate path):**
     `podman save` on NZXTcos → `scp` tarball over tailnet →
     `podman load` on tsP3. Tailnet bandwidth NZXTcos↔tsP3 is
     high (1.9ms ping); ~340MB transfer is seconds. Avoids
     ghcr.io credential dance on a fresh box.
   - **For future engineer onboarding (canonical pattern):**
     ghcr.io pull from each engineer's box. Per the W6 D1 ops
     gotcha, podman's auth store is independent of gh CLI's
     token store; canonical refresh is
     `gh auth token | podman login ghcr.io -u <user>
     --password-stdin`, then
     `podman pull ghcr.io/soc-foundry/aho:0.2.17-rc2`.
     Generalizes to any internet-connected box.

4. **tsP3 partial-tier model availability.** Post-`install.fish`,
   `ollama pull llama3.2:3b nomic-embed-text:latest` at minimum.
   Optional: `qwen3.5:9b` as a partial-tier auditor candidate
   (16GB Ada VRAM has headroom; NZXTcos 8GB does not — that's
   the architectural reason to move partial-tier work to tsP3).

5. **Smoke test on tsP3.** Post-install + post-image-load:
   `aho host run-container --project ahomw --image
   aho:0.2.17-rc2 -- secrets-test ahomw telegram_bot_token`.
   Expected output: fingerprint JSON of shape `{"project":
   "ahomw", "name": "telegram_bot_token", "fingerprint":
   "<8-hex>", "length": <int>, "status": "ok"}`. No decrypted
   value in stdout (Pillar 11 verified post-rotation).

## Forward-looking note: 0.3.1 launch

Partial-tier deployment on tsP3. Auditor candidate
`qwen3.5:9b` in 16GB Ada VRAM raises the consistency floor over
`llama3.2:3b` base-tier auditing — partial-tier auditor scope is
chat-refinement scope at 0.3.1 launch. Carry-forwards
F-0.2.17-W5-001 / W5-002 / W6-001 / W6-002 / W6-003 fold into
0.3.1 base-tier hardening scope (none are hard gates).

ChromaDB iteration-context collection migration from
`0.2.16`-anchored to `0.3.x`-anchored is a 0.3.1 launch chat
refinement; the carry-forwards file likely splits to
`carry-forwards-0.3.x.md` at 0.3.1 launch with carryover entries
re-anchored. Planning notes only — execution at 0.3.1 launch.

W6's qualified validation status (N=5 below N≥8 ADR-0010
threshold) is the only structural blocker on full-validation
materiality claims. Three more iterations of auditor-seat data
post-0.2.17 reach the threshold; 0.3.1 + 0.3.2 + 0.3.3 are the
likely candidates.

## Sealed-archive inventory

Every artifact below is sealed; modifying any of them at this
point would invalidate the iteration close. Recorded for
auditability:

- `artifacts/iterations/0.2.17/acceptance/W0.json` —
  `cd4e3f96b6d4217f275a946be964d38ff78b8acff7cbd683002f84f4463dfebc`
- `artifacts/iterations/0.2.17/acceptance/W0-amendment-b2-3.json` —
  `1be983eab9895dc19770f950ac7bbf1992da2ae30a74678bdaf56ebb85457c56`
- `artifacts/iterations/0.2.17/audit/W0.json` —
  `1e2b2f496fbf583f9228bdd5658e72ede348bb62809fcaa6704e788ba0067d89`
- `artifacts/iterations/0.2.17/acceptance/W1.json` —
  `e4d076eec6c1e703635e9befb98bc46c7bf171c7fec3a4c3f64161ec60725a6e`
- `artifacts/iterations/0.2.17/audit/W1.json` —
  `8b2771acd0c8cab833ee35f6be957b31f25e6255c9eb40fe055e6f92c75862ab`
- `artifacts/iterations/0.2.17/acceptance/W2.json` —
  `4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`
- `artifacts/iterations/0.2.17/audit/W2.json` —
  `b9c2f1bb5ef4b4af4b0670ef8f84440ccef0a6dbed7be70a160bb031a886ab22`
- `artifacts/iterations/0.2.17/acceptance/W3.json` —
  `9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`
- `artifacts/iterations/0.2.17/audit/W3.json` —
  `b3a4e2e6c88244f4b4fcd59f75b56112beed8287600eb2308a7cdb7f4a605efc`
- `artifacts/iterations/0.2.17/acceptance/W4.json` —
  `949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`
- `artifacts/iterations/0.2.17/audit/W4.json` —
  `9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`
- `artifacts/iterations/0.2.17/acceptance/W5.json` —
  `3ba226016b824641e8c07030cdc5bb74835c8d394228556a58850b1201520b8f`
- `artifacts/iterations/0.2.17/audit/W5.json` —
  `5bd170e930c4b3e26df735651407ba9595e42457754bdd6b0f69838d1bcbe4e6`
- `artifacts/iterations/0.2.17/acceptance/W6.json` —
  `b4d6287bc7e3d8146fc06b7c5870c7e8a9ab6fdf6fd9111768fd0299f0ec5fda`
- `artifacts/iterations/0.2.17/audit/W6.json` —
  `bb7b1d1fcd429bd25730d7bbfcbb82ee30609866692f6bf4f5960b95da51d702`
- `artifacts/iterations/0.2.17/W0-close-note.md` —
  `b458fc4e92042391cf4470fa5480276ceb782cd2b47f0d13cc84d31743326e05`
- `artifacts/iterations/0.2.17/W1-close-note.md` —
  `98f897abcbc6b95c7b3d9934a4bfdbf28a2234ebbc08ac9620fccbcb3cee4eb2`
- `artifacts/iterations/0.2.17/W2-close-note.md` —
  `b0fb1ccd18552a06863cf21c0cd3c3099809773d88f7858db155d0994398c8c3`
- `artifacts/iterations/0.2.17/W3-close-note.md` —
  `3a0c3c08739a2177c6d9a0ab4bfbd8cfc5190e6474018e1e191aa98f37c62fdc`
- `artifacts/iterations/0.2.17/W4-close-note.md` —
  `d7f73e03b1dceb0472ec29ec23a17d16bd05e773bc84fa849bb827718ee60a9c`
- `artifacts/iterations/0.2.17/W5-close-note.md` —
  `1ce28b9a05abada8aa8c4bcbb7dba7924b8b3299690b0af597f0dabb641bea90`
- `artifacts/iterations/0.2.17/W6-close-note.md` —
  `f5b3a781dcf3bb6bd65c511db3c79395a8b4264802be57bb6d1d1d84d6edd140`
- `artifacts/adrs/0007-containerization-architecture.md` (W5 D1
  amended) —
  `ed99e70e8598d516f853abd3719c6a1e9fa8793c2d00ad7fc9f29408bd9fe0ab`
- `artifacts/adrs/0009-secrets-broker-boundary.md` (W5 D2 new) —
  `d2dfed10c9ee6cbd59f5e7094b7705888b9428fdf340c4b4cbc69bab02359e86`
- `artifacts/adrs/0010-materiality-measurement.md` (W5 D3 new) —
  `37b7883021591626e94200df3cf7eb6a439320a40171555e4a7350a84d2ae3d6`
- `docs/architecture/component-decomposition.md` (W5 D4 new) —
  `6418faa3d8a11cc602053cbc1f224134b6c6bef088aa11d8a5e8c6599e9acd42`
- `docs/architecture/claw3d-brick-spec.md` (W5 D5 new) —
  `3af64453a86a197ed8d72bbd2808331ec9143e2057704fc2351ced5930f310b1`
- `docs/retrospectives/0.2.17.md` (W5 D6 new — canonical
  retrospective) —
  `0a98040a932977ca3af7601da1ac2751163ba355907b4656900b3dbe89c4762e`

Mutable per established pattern (carry-forwards file is the
running ledger):

- `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` —
  `5974a691dcc3dba96f8dd8c95f8baeedfb47942cf71f22d6e707a0330eca2b12`
  (post-W6-003 append, 37 strict-regex entries / 43 permissive
  entries at iteration-close authoring time)

## Iteration close attestation

This iteration-close note is a documentation artifact, not a
state-machine event. The canonical state advancement is the
`workstream_complete` event chain (W0 through W6, all emitted
to event log, checkpoint advanced). No additional event-log
event is emitted on iteration close — the chain itself is the
state machine.

### Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-04T13:20:40Z
All seven workstream closes acknowledged: yes
(W0-close-note.md, W1-close-note.md, W2-close-note.md,
W3-close-note.md, W4-close-note.md, W5-close-note.md,
W6-close-note.md, all operator-signed; shas in §Sealed-archive
inventory)
Carry-forwards state acknowledged: yes
(4 closed inside iteration: W2-006, W3-001, W1-001, W4-001;
5 carrying to 0.3.x base-tier hardening: W5-001, W5-002, W6-001,
W6-002, W6-003; 1 hard gate operator-side: W1-003)
Sealed-archive inventory acknowledged: yes
0.3.1 pre-conditions acknowledged: yes
(F-0.2.17-W1-003 token rotation hard gate, tsP3 bootstrap via
install.fish, image transfer pattern, partial-tier model pull,
smoke test contract)
Iteration scope complete: yes
0.2.17 iteration: closed
