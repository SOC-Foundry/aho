# 0.2.17 W6 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `halt`).

W6 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W6.json`.
W6 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W6.json` with
`disposition: "halt"` (llama self-audit verbatim - driven by
F-0.2.17-W4-001 unverified status surfacing in RAG enrichment +
self-referential AUDIT-PILLAR11 structural pre-check). Drafter
(claude-web) arbitrated all three findings under Option C -
partial closure framing - and arbitrated disposition to
`pass_with_findings`. Two new W6 carry-forwards added (W6-001
audit-time lookup ranking; W6-002 council embed timeout default).
Sealed shas (verified at close-note authoring time):

- acceptance archive sha256:
  `b4d6287bc7e3d8146fc06b7c5870c7e8a9ab6fdf6fd9111768fd0299f0ec5fda`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `bb7b1d1fcd429bd25730d7bbfcbb82ee30609866692f6bf4f5960b95da51d702`
  (target_artifact_sha256 inside the audit document:
  `f105f65c2d9e029a12b63e567b97e196e88f1ce69d337f4a2ab22e089690e867`,
  reflecting the pre-edit acceptance archive content the audit ran
  against - drafter arbitration occurs in the acceptance archive
  only, not the audit JSON)
- carry-forwards file sha256 (post-W6-001 + W6-002 append):
  `cd9f2726ee75a54c447dc6bf2a20275887d3fad563f3b68487d151019d83119b`

Audit archive (`audit/W6.json`) is UNTOUCHED post-emit. The
disposition field reads `halt`; drafter arbitration is recorded
only in the acceptance archive's D3 `drafter_review_note` block
+ `carry_forwards_added` entries, and in this close note's prose.
Per Adversarial Authorship sealed-archive convention, audit
archives are not amended after emit - corrections and arbitrations
land in acceptance evidence and close-note prose, never in the
audit JSON.

## Materiality status

W6 lands the residual code-change closures: F-0.2.17-W1-001
secrets-test hash-fingerprint redesign + F-0.2.17-W4-001 ChromaDB
re-index hook. With W6 D3 emit complete, the 0.2.17 evidence build
is complete: five iterations of in-container llama auditor data
across W2 / W3 / W4 / W5 / W6, with progressively-stabilized
auditor infrastructure exercised against substantively different
audit-target shapes:

- **W2 baseline:** in-container llama auditor with no RAG
  enrichment. False positives on registered-anchor IDs surfaced
  systematically (F-0.2.17-W2-006).
- **W3 partial fix:** RAG enrichment via `aho.council.audit`'s
  pre-prompt context section. Closed 1 of 2 demonstrated false
  positives.
- **W4 structural closure:** deterministic post-hoc filter on the
  finding list. Both demonstrated false positives now caught.
- **W5 fourth deployment:** filter remains structurally narrow on
  documentation-heavy work. Filter eligible (16 registered IDs),
  ran on every model finding, suppressed_count=0.
- **W6 fifth deployment:** filter remains structurally narrow on
  final-code-change work. Filter eligible (9 registered IDs),
  ran on every model finding, suppressed_count=0. The halt
  disposition was driven by a real surface (F-0.2.17-W4-001
  unverified in RAG enrichment) that drafter arbitration revealed
  as closure-of-different-defect - F-0.2.17-W4-001 itself closes
  at the data layer; the lookup-ranking surface is captured as new
  F-0.2.17-W6-001.

The architecture's halt-and-surface invariant continues to function
correctly. D3 halt was earned (real surface in lookup primitive on
opaque-ID queries against a 158-chunk corpus). Drafter arbitration
revealed scope distinction: W4-001 closes at the data layer;
W6-001 captures the lookup-ranking layer as a separate carry-
forward. The W4 D1 deterministic post-hoc filter remains
structurally narrow across five deployments - code-heavy (W4 and
W6) and documentation-heavy (W5) work both produce the same
filter behavior because the filter inspects literal description
text, not domain context.

N=5 below the N≥8 threshold per ADR-0010. Qualified validation
unchanged (status: qualified-validation, not full-validation, per
ADR-0010 §N=4 caveat now extended to §N=5 caveat).

## D3 self-audit findings section

W6 D3 self-audit ran `aho.council.audit(artifact=W6_acceptance_archive,
rag_enrichment=True)` against the W6 acceptance archive at the
moment of seal-1 (pre-edit, target sha
`f105f65c2d9e029a12b63e567b97e196e88f1ce69d337f4a2ab22e089690e867`).
Llama returned disposition `halt` at confidence 0.95 with 3
findings (2 model + 1 structural pre-check). Drafter
(claude-web) arbitrated all 3 to `pass_with_findings` under
Option C - partial closure framing:

- **D1 (important).** Auditor text: *"The carry-forward_full ID
  F-0.2.17-W1-001 is registered, but its source is not found in
  the iteration-context."* This is a small-model self-contradiction
  artifact. F-0.2.17-W1-001 IS in fact registered, and the RAG
  enrichment shows it as registered with `top_source_artifact_path`
  pointing to `W1-close-note.md`. The auditor's text "but its
  source is not found" contradicts its own RAG context section.
  The W4 D1 filter correctly did not suppress this finding because
  the description has no fake-ID phrase - the filter's structural
  narrowness is intentional and preserved. Drafter arbitration:
  no action; auditor self-contradiction artifact, not a real
  finding.

- **F-0.2.17-W4-001 (info).** Auditor text: *"The carry-forward_full
  ID F-0.2.17-W4-001 is unverified."* Real surface - but reflects
  closure-of-different-defect, not regression on D2. F-0.2.17-W4-001
  itself closes AT THE DATA LEVEL: D2's append-triggered reindex
  landed; chunk015 of carry-forwards-workstream chunks contains
  literal F-0.2.17-W4-001 token (verified twice independently in
  W6 D2 live probe + W6 D3 halt-investigation). The unverified
  surface comes from the audit-time lookup primitive
  (`audit_ref_lookup.py` top-24 cosine-similarity retrieval) not
  ranking the carry-forwards chunk in top-24 against the opaque-
  ID query "F-0.2.17-W4-001" in a 158-chunk corpus. **Captured as
  new carry-forward F-0.2.17-W6-001.** Drafter arbitration:
  F-0.2.17-W4-001 closes at data layer; F-0.2.17-W6-001 captures
  the lookup-ranking layer as a separate defect (drafter-recommended
  structural fix: ID-keyed metadata field at index time, 0.3.x
  base-tier hardening target).

- **AUDIT-PILLAR11 (critical, structural pre-check).** Git-op
  tokens (`git-add`, `git-commit`, `git-push`, `gh pr create`)
  matched literal text inside `pillar_11_invariant_check.evidence.files_written`
  prose attesting that the executor did NOT invoke these
  primitives. Same shape as W3 D5 + W4 D7 + W5 D8 (now confirmed
  across four audits within the 0.2.17 iteration). Pillar 11
  invariant in fact respected; prose attests compliance.
  F-0.2.17-W5-001 already captures the recurring pattern (drafter
  recommendation: structural pre-check scope discrimination via
  JSON path exclusion; 0.3.x base-tier hardening target). No new
  carry-forward needed.

**Drafter-arbitrated disposition: `pass_with_findings` under
Option C (partial closure framing).** Three findings: one is
auditor self-contradiction artifact; one is real surface
captured as separate carry-forward (W4-001 closes at data layer,
W6-001 captures lookup-ranking layer); one is fourth occurrence
of a pattern already captured at W5-001.

The D3 hard-fail condition - "self-audit produces fake-ID-on-
registered-anchor false positives that the filter should have
caught (W4 D1 hardening regression)" - **did not trigger.** No
finding has the failure shape. Filter was active and eligible
(filter_eligible=true, registered_id_count=9, model_findings=2,
suppressed=0). The F-0.2.17-W4-001 finding's description ("is
unverified") has no fake-ID phrase from FAKE_ID_PHRASES set; the
filter correctly preserved it as an active finding for drafter
review. **Bootstrap test 7 (loop closure on final code-change
workstream) passes structurally** - the halt-and-surface
mechanism functioned correctly: auditor surfaced a real lookup-
ranking concern that drafter arbitration revealed as closure-of-
different-defect.

## Carry-forwards CLOSED

Two carry-forwards closed in W6:

- **F-0.2.17-W1-001 - `aho secrets-test` test-only subcommand
  left in 0.2.17-rc1 image.** Closure mechanism: D1 hash-
  fingerprint redesign (Path A) in `src/aho/cli.py`. Subcommand
  still present in rc2 image (per drafter recommendation -
  preserves verification capability), but no longer prints
  decrypted value - emits SHA-256 first 8 hex + length JSON
  instead. Pillar 11 invariant: agent stdout never contains the
  decrypted value during `aho secrets-test` invocation. Verified
  by local mock test + four in-container W1 D3 gate revalidations
  (gate1 fingerprint JSON exit 0, gate2 AUTH_FAIL exit 4, gate3
  missing JSON exit 5, gate4 unregistered-UID exit 4). Image
  `aho:0.2.17-rc2` built and pushed to ghcr (manifest digest
  `sha256:b6dd0596…`); pull-clean and healthcheck-clean both
  verified. Closure clean - no contestation.

- **F-0.2.17-W4-001 - ChromaDB iteration-context index does not
  auto-refresh on carry-forwards-0.2.16.md updates.** Closure
  mechanism: D2 append-triggered reindex hook in
  `src/aho/gap_carry_forward_writer.append_to_file`. Every append
  triggers `aho.rag.index_artifact` post-write; failure path:
  warning + OTEL counter increment, append still succeeds.
  **Closure framing per drafter Option C arbitration: closed at
  data level.** D2 append-triggered reindex landed; chromadb
  chunk015 of carry-forwards-workstream chunks contains literal
  F-0.2.17-W4-001 substring (verified twice independently in W6
  D2 live probe + W6 D3 halt-investigation). The audit-time
  lookup-ranking surface (top-24 cosine miss on opaque IDs in a
  158-chunk corpus) is a separate defect captured as new
  F-0.2.17-W6-001. The two W6 carry-forward additions (W6-001 +
  W6-002, see below) were both appended via this hook in the
  D7-style dogfooding pattern; both invocations returned
  `reindex_status: 'ok'` - production-shape verification of the
  D2 closure invariant.

## Carry-forwards ADDED

Two new W6 carry-forwards, surfaced by D3 self-audit drafter
arbitration + D2 substrate observation:

- **F-0.2.17-W6-001 - Audit-time lookup ranking misses opaque-ID
  matches in carry-forwards file.** Severity: important. Source:
  0.2.17 W6 D3 self-audit. Summary: `audit_ref_lookup` retrieves
  top-24 chunks by cosine similarity then filters to literal-ID-
  containing chunks. Opaque alphanumeric IDs (F-0.2.17-WN-NNN
  shape) carry low embedding signal; recency-weighting boosts
  current-iteration chunks over the 0.2.16 carry-forwards file;
  158-chunk corpus has many higher-cosine competitors. The chunk
  containing the literal token IS in chromadb (verified twice
  independently) but does not rank top-24 → status=unverified
  surfaces in audit RAG enrichment. Disposition: drafter-
  recommended structural fix - add ID-keyed metadata field at
  index time so direct lookup by ID-token avoids cosine entirely.
  Alternative options (larger pool multiplier, lower threshold
  floor) are statistical and less robust. Target: 0.3.x base-
  tier hardening. Audit traceability: W6 D3 (audit/W6.json sha
  bb7b1d1f...) F-0.2.17-W4-001 unverified finding +
  acceptance/W6.json deliverables[2].evidence.lookup_ranking_failure_mode.

- **F-0.2.17-W6-002 - Council embed timeout default too tight
  under VRAM contention.** Severity: info. Source: 0.2.17 W6 D2
  live probe. Summary: default `AHO_COUNCIL_EMBED_TIMEOUT_S=30s`
  in `src/aho/council/embed.py` is too short when nomic-embed-text
  cold-loads after qwen3.5:9b model swap on 8GB VRAM. Live probe
  required bump to 300s to complete chunked embedding of the
  50KB carry-forwards file. Without the bump the reindex hook
  failure-handling path fires (warning + counter, append still
  succeeds) but no actual indexing occurs. Mechanism: substrate
  condition (Ollama state hygiene + 8GB VRAM contention with co-
  resident large models - qwen3.5:9b at 7.4GB held by aho-
  nemoclaw or aho-openclaw user-service), not a council/embed
  defect. Same family as 0.2.15 substrate findings. Disposition:
  bump default in `src/aho/council/embed.py` from 30 → 120 in
  0.3.x or earlier substrate fix. The reindex hook degradation
  behavior is correct; only the default tightness is the
  concern. Target: 0.3.x base-tier hardening or earlier substrate
  fix. Audit traceability: acceptance/W6.json
  deliverables[1].evidence.substrate_observation_during_probe_runs.

The carry-forwards file update is **complete in this turn** -
both new entries appended via
`aho.gap_carry_forward_writer.append_to_file` in the same
dogfooding pattern W2 / W4 / W5 used. Writer logged
`entry_count_before=34 → entry_count_after=36 (entries_added=2)`
under its strict regex; the permissive cross-iteration counter
took the file from 41 to 43 (W4 close-note convention).

The two counts measure different things - the strict regex counts
canonical `- **{id} - {title}**` entries inside the file scope of
the writer's heading detection; the permissive counter sweeps the
entire file including legacy entries. Both are honest; neither
contradicts the other. Same shape as W4 + W5 close notes.

**Production-shape D2 closure invariant verification:** both
W6-001 and W6-002 appends returned `reindex_status: 'ok'` from
the writer's reindex hook. The carry-forwards file is freshly
indexed in chromadb after each append. The hook's full round-trip
is exercised: file mutation → index_artifact call → chunked embed
via nomic-embed-text → chromadb upsert → success. F-0.2.17-W4-001
closure invariant holds in production-shape: any subsequent audit
run will see the appended entries on its next RAG enrichment lookup
(modulo the F-0.2.17-W6-001 lookup-ranking concern, which is the
separate defect just captured).

## Auditor-seat-transition continuation

W6 is the **fifth deployment of the in-container llama auditor**
(W2 baseline, W3 RAG-enriched, W4 RAG + deterministic post-hoc
filter, W5 RAG + filter against documentation-heavy work, W6 RAG
+ filter against final-code-change work). The protocol-level loop
has now closed five times in succession with progressively-
stabilized auditor infrastructure.

**Bootstrap test 7 (loop closure on final code-change workstream)
passes structurally.** D3 self-audit ran the W4-stabilized
primitive (model + RAG + filter) against W6's own acceptance
archive; the audit emitted a structurally valid disposition
(`halt`); the filter was active and eligible; the drafter
reviewed; this close note is authored; the operator signs. The
state machine `pending_audit → blocked → pending_drafter_review
→ operator_sign` advances exactly as the architecture specifies.
The temporary `blocked` state during the halt-and-surface
window between executor halt and drafter arbitration is a real
state-machine vertex - first observed at W6, validates the
halt-and-surface protocol's integrity (executor cannot
unilaterally advance the state machine past a halt condition;
drafter arbitration is required).

Adversarial-Authorship-at-base-tier holds across documentation
work (W5) and final-code-change work (W6).

**Filter activity at D3:** filter_eligible=true,
registered_id_count=9, model_findings_count=2,
active_findings_count=2, suppressed_count=0. The filter ran on
every model finding and produced the right answer for each. The
F-0.2.17-W4-001 finding's description has no fake-ID phrase, so
the filter correctly preserved it as an active finding - that's
exactly the structural narrowness the W4 D1 hardening was
designed to provide.

**Pattern note (fourth occurrence pattern-confirmed).** The
structural pre-check self-referential pattern fired again at W6
D3 (AUDIT-PILLAR11 critical), now occurring four times within
the 0.2.17 iteration (W3 D5, W4 D7, W5 D8, W6 D3). F-0.2.17-W5-001
captures this with a two-option disposition (JSON path exclusion
preferred; context-aware regex secondary). Confidence in the
0.3.x base-tier hardening target is high - pattern is fully
characterized.

## Pre-0.3.x hard gates (final state at W6 close)

**Hard gate (one remaining):**

- **F-0.2.17-W1-003** - Telegram bot token rotation. Operator-
  side, post-0.2.17. The only remaining pre-tsP3 hard gate.
  Status as of W6 close-note authoring:
  **operator_action_pending**.

**Carry-forwards into 0.3.x (not hard gates):**

- F-0.2.17-W5-001 - Structural pre-check self-referential pattern
  scope discrimination (now four occurrences pattern-confirmed).
  Target: 0.3.x base-tier hardening.
- F-0.2.17-W5-002 - Plan-doc / repo-convention path drift.
  Target: drafter chat-side process improvement + 0.3.x plan-doc
  convention notes.
- F-0.2.17-W6-001 - Audit-time lookup ranking misses opaque-ID
  matches. Target: 0.3.x base-tier hardening.
- F-0.2.17-W6-002 - Council embed timeout default too tight under
  VRAM contention. Target: 0.3.x base-tier hardening or earlier
  substrate fix.

This reminder is surfaced at every iteration close until the
F-0.2.17-W1-003 rotation completes. Per the recurring protocol:
surfaced at W1 close, surfaced at W2 close, surfaced at W3 close,
surfaced at W4 close, surfaced at W5 close, **surfaced at W6
close (this note)**, surfaces before tsP3 handoff.

## Forward-looking note for 0.2.17 close

After this close note signs, 0.2.17 fully closes. Operator runs
token rotation per F-0.2.17-W1-003 outside the workstream
framework. Then 0.3.1 launches with clean carry-forward state
for the gates we control (F-0.2.17-W1-001, F-0.2.17-W4-001
closed at W6) plus four 0.3.x-scoped carry-forwards for base-tier
hardening:

- F-0.2.17-W5-001 (structural pre-check scope discrimination)
- F-0.2.17-W5-002 (plan-doc convention drift)
- F-0.2.17-W6-001 (audit-time lookup ranking on opaque IDs)
- F-0.2.17-W6-002 (embed timeout substrate tightening)

Plus operator-side F-0.2.17-W1-003 (token rotation), the only
remaining pre-tsP3 hard gate.

The 0.2.17 iteration close is drafter (claude-web) scope -
authored after operator signs this W6 close note. The close
covers all six workstreams (W0 through W6) plus the pre-tsP3
operator action queue.

## State at close

- **Acceptance archive:** sealed,
  `audit_status: "pending_drafter_review"` at close-note
  authoring time. Drafter has reviewed (this turn) and arbitrated
  D3 findings + added F-0.2.17-W6-001 + F-0.2.17-W6-002 carry-
  forwards; status holds at `pending_drafter_review` until
  operator signs this close note. sha256
  `b4d6287bc7e3d8146fc06b7c5870c7e8a9ab6fdf6fd9111768fd0299f0ec5fda`.
- **Audit archive:** sealed, untouched post-emit. sha256
  `bb7b1d1fcd429bd25730d7bbfcbb82ee30609866692f6bf4f5960b95da51d702`
  (target_artifact_sha256 inside the document is
  `f105f65c2d9e029a12b63e567b97e196e88f1ce69d337f4a2ab22e089690e867`,
  reflecting the pre-edit acceptance archive content the audit
  ran against - drafter arbitration occurs in the acceptance
  archive only, not the audit JSON).
- **Carry-forwards file:** updated in this turn. Two new entries
  appended (F-0.2.17-W6-001 under existing target heading
  `## Target: 0.3.x base-tier hardening`; F-0.2.17-W6-002 under
  new target heading `## Target: 0.3.x base-tier hardening or
  earlier substrate fix`). Strict-regex count (writer-internal):
  34 → 36. Permissive cross-iteration count (per W4 close
  convention): 41 → 43. Both reindex-hook invocations returned
  `reindex_status: 'ok'` - production-shape verification of D2
  closure invariant. File update is **complete** pending
  operator review of this close note. sha256
  `cd9f2726ee75a54c447dc6bf2a20275887d3fad563f3b68487d151019d83119b`.
- **0.2.17 iteration close gate:** blocked on operator signature
  on this close note. workstream_complete emit (next executor
  invocation, after operator sign) advances the state machine to
  `W6_workstream_complete` and clears the W6 launch-gate-complete
  state for the iteration. The 0.2.17 iteration-close
  orchestration follows in chat as drafter-scope work.
- **Image state:** `ghcr.io/soc-foundry/aho:0.2.17-rc2` published
  (manifest digest `sha256:b6dd0596…`); operator-side token
  rotation per F-0.2.17-W1-003 is the gate before any
  `aho:0.2.17` final-tag promotion.

## Pillar 11 invariant cross-check

- **Drafter (claude-web):** zero git operations. Plan-doc
  authoring (W6 plan-doc was authored pre-session), drafter-
  arbitration prose (this turn), and close-note authoring
  (this turn) is artifact-only.
- **Executor (Claude Code):** zero git operations.
  `pillar_11_invariant_check` in `acceptance/W6.json` reads
  `result: "pass"` with evidence: no git/gh/push/commit/PR/merge
  primitive invoked across the executor session; all writes
  targeted `src/aho/cli.py` (modify - secrets-test redesign),
  `src/aho/gap_carry_forward_writer.py` (modify - reindex hook +
  counter + helpers), `Dockerfile` (modify - image label rc1→rc2),
  `artifacts/tests/test_gap_carry_forward_writer_reindex.py`
  (new - 3 unit tests), `artifacts/iterations/0.2.17/probes/W6_reindex_live_probe.py`
  (new - D2 live verification probe),
  `artifacts/iterations/0.2.17/probes/W6_self_audit.py` (new -
  D3 self-audit probe), `artifacts/iterations/0.2.17/acceptance/W6.json`
  (this archive), `artifacts/iterations/0.2.17/audit/W6.json`
  (audit emit by self-audit probe),
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` (two
  appends for F-0.2.17-W6-001 + F-0.2.17-W6-002 via
  gap_carry_forward_writer in the same dogfooding pattern
  W2/W4/W5 established) - no `.git/`, no `~/.config/`, no
  `/etc/`, no `.ssh/` writes. F-0.2.17-W1-003 token rotation
  explicitly NOT performed (surfaced as continuing reminder
  under `outstanding_pre_03x_gates`).
- **ghcr.io image push observation:** podman push to ghcr.io is
  image-distribution, not source-control git op. Pillar 11
  forbids agent-side source-control writes (git/gh PR/merge/
  push/commit). Image push is part of the build/distribution
  surface and was in-scope for executor work per W6 plan-doc and
  executor prompt explicit authorization. First push attempt
  failed on stale podman auth store (separate from gh CLI's
  token store); operator (Kyle) refreshed credentials via
  `gh auth token | podman login ghcr.io --password-stdin`;
  second push attempt succeeded. Agent did not access or manage
  podman/ghcr credentials.
- **Auditor (llama3.2:3b in-container, RAG + filter):** zero git
  operations. In-container model has no shell, no filesystem
  write capability outside the audit primitive's controlled
  emitter path. Audit archive itself is JSON-only - no
  executable artifacts. The RAG retrieval step
  (`aho.council.audit_ref_lookup`) reads the host-mounted
  ChromaDB collection only; no git tree access. The W4 D1
  filter (`aho.council.audit_finding_filter`) is pure Python
  string + regex operations; no I/O of any kind.
- **Self-audit AUDIT-PILLAR11 finding clarification:** the
  `git-add`/`git-commit`/`git-push`/`gh pr create` tokens that
  triggered the structural pre-check appear inside the
  `pillar_11_invariant_check.evidence` field as the literal list
  of primitives the executor did NOT invoke. Same shape as W3
  D5 + W4 D7 + W5 D8 AUDIT-PILLAR11; same arbitration applies.
  The pre-check regex is conservative-by-design (flag for human
  review rather than auto-fail); the human review (this close
  note) confirms the tokens are descriptive prose attesting
  Pillar 11 compliance, not actual invocations. F-0.2.17-W5-001
  captures the recurring pattern (now four occurrences).
- **Decrypted secret value handling:** the `aho secrets-test`
  subcommand was invoked four times against the rc2 image as
  part of W1 D3 gate revalidation; in all four invocations the
  agent observed only the structured output (fingerprint JSON,
  AUTH_FAIL stderr, missing JSON, AUTH_FAIL UID stderr). The
  decrypted secret value never enters agent stdout in the new
  contract - that is the F-0.2.17-W1-001 closure invariant.

## Operator sign-off

Signed by:
Date:
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit halt under Option C - partial closure framing)
D3 self-audit drafter arbitration acknowledged: 1 auditor self-contradiction artifact (no action), 1 real surface captured as F-0.2.17-W6-001 (W4-001 closes at data layer, lookup-ranking layer captured separately), 1 self-referential structural pre-check artifact (fourth occurrence under existing F-0.2.17-W5-001)
Carry-forwards added acknowledged: F-0.2.17-W6-001 (audit-time lookup ranking misses opaque-ID matches), F-0.2.17-W6-002 (council embed timeout default too tight under VRAM contention)
Carry-forwards closed acknowledged: F-0.2.17-W1-001 (secrets-test hash-fingerprint redesign + image rebuild + ghcr push + pull-clean + healthcheck - clean closure), F-0.2.17-W4-001 (closed at data layer per drafter Option C arbitration; lookup-ranking concern captured separately as F-0.2.17-W6-001)
Pre-0.3.x hard gates (continuing): rotate ahomw:telegram_bot_token (F-0.2.17-W1-003) - only remaining hard gate before tsP3 handoff
Auditor-seat-transition continuation acknowledged (5th deployment, bootstrap test 7 passes structurally): yes
0.2.17 iteration close orchestration drafter delivery acknowledged: yes (drafter-scope work, follows operator sign on this close note)
0.2.17 iteration close gate: blocked on operator sign of this note

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-04T05:12:27Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit halt under Option C partial-closure framing)
Carry-forwards closed: F-0.2.17-W1-001 (secrets-test hash-fingerprint redesign + image rebuild + ghcr push + pull-clean + healthcheck), F-0.2.17-W4-001 (closed at data layer per drafter Option C arbitration; lookup-ranking layer captured separately as F-0.2.17-W6-001)
Carry-forwards added: F-0.2.17-W6-001 (audit-time lookup ranking misses opaque-ID matches in carry-forwards file), F-0.2.17-W6-002 (council embed timeout default too tight under VRAM contention)
D2 closure invariant production-shape verified: both W6-001 + W6-002 appends triggered reindex_status=ok via the new hook
Auditor-seat-transition continuation acknowledged (5th deployment, bootstrap test 7 passes structurally)
Pre-0.3.x final hard gate: rotate ahomw:telegram_bot_token (F-0.2.17-W1-003) - operator post-0.2.17, the only remaining hard gate before tsP3 handoff
0.3.x base-tier hardening carry-forwards (NOT hard gates): F-0.2.17-W5-001, F-0.2.17-W5-002, F-0.2.17-W6-001, F-0.2.17-W6-002
0.2.17 iteration close gate: lifted upon workstream_complete emit
