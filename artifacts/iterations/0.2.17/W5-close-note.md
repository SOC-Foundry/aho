# 0.2.17 W5 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `halt`).

W5 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W5.json`.
W5 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W5.json` with
`disposition: "halt"` (llama self-audit verbatim — driven by two
structural pre-check fires, both self-referential). Drafter
(claude-web) arbitrated all 10 findings and arbitrated disposition
to `pass_with_findings`. Two new carry-forwards added (W5-001
structural pre-check pattern; W5-002 plan-doc / repo-convention
path drift). Sealed shas (verified at close-note authoring time):

- acceptance archive sha256:
  `3ba226016b824641e8c07030cdc5bb74835c8d394228556a58850b1201520b8f`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `5bd170e930c4b3e26df735651407ba9595e42457754bdd6b0f69838d1bcbe4e6`
  (target_artifact_sha256 inside the audit document:
  `8795328226425c4536ac03bbe7e1ca2a991f65485cf190756aad5bb179faffbd`,
  reflecting the pre-edit acceptance archive content the audit ran
  against — drafter arbitration occurs in the acceptance archive
  only, not the audit JSON)
- carry-forwards file sha256 (post-W5-001 + W5-002 append):
  `72d0fc903477e9357defd41224d52c7841617a1e2b62a3bcd8fe39b43487b295`

Audit archive (`audit/W5.json`) is UNTOUCHED post-emit. The
disposition field reads `halt`; drafter arbitration is recorded
only in the acceptance archive's D8 `drafter_review_note` block
+ `carry_forwards_added` entries, and in this close note's prose.
Per Adversarial Authorship sealed-archive convention, audit
archives are not amended after emit — corrections and arbitrations
land in acceptance evidence and close-note prose, never in the
audit JSON.

## Materiality status

W5 lands the documentation consolidation. Three iterations of
auditor-seat data were already recorded across W2/W3/W4; W5
extends the evidence build with a fourth deployment of the
stabilized primitive against documentation-heavy work rather than
code-heavy work:

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
  ran on every model finding, suppressed_count=0 — none of the 8
  model findings have a fake-ID phrase substring. Filter live;
  filter correct. The audit-target shape (acceptance archive prose
  rather than test-result evidence) did not change the filter's
  correctness profile.

The W4 D1 filter does not bet on small-model prompt-following.
W5 confirms it also does not bet on the audit-target's semantic
domain (code vs documentation). Either domain produces the same
filter behavior because the filter inspects literal description
text, not domain context.

N=4 below the N≥8 threshold per ADR-0010. Qualified validation
unchanged.

## D8 self-audit findings section

W5 self-audit ran `aho.council.audit(artifact=W5_acceptance_archive,
rag_enrichment=True)` against the W5 acceptance archive at the
moment of seal-1 (pre-edit, target sha
`8795328226425c4536ac03bbe7e1ca2a991f65485cf190756aad5bb179faffbd`).
Llama returned disposition `halt` at confidence 0.95 with 10
findings (8 model + 2 structural pre-check). Drafter
(claude-web) arbitrated all 10 to `pass_with_findings`:

- **D1 / D2 / D3 / D5 / D6 / D7 (info, ×6).** Auditor surfaces
  plan-doc-vs-repo-convention path drift across the deliverables.
  Plan-doc said `docs/adr/`; repo convention is `artifacts/adrs/`;
  the W4 close-note already pointed at `artifacts/adrs/`. The
  executor surfaced this in D1/D2/D3 evidence's `path_resolution_note`
  fields explicitly and resolved by editing existing ADR-0007 in
  place + creating new ADR-0009 / ADR-0010 at `artifacts/adrs/`.
  Architecture docs and retrospective landed at `docs/architecture/`
  + `docs/retrospectives/` per plan-doc explicit (net-new
  directories). Auditor's literal description text re-uses the D2
  pattern wording rather than each deliverable's specific path,
  but the underlying signal — path drift in plan-doc — is correct
  across all six. **Captured as new carry-forward F-0.2.17-W5-002.**

- **F-0.2.17-W1-001 (info).** Auditor reports W1-001 (secrets-test
  subcommand removal) as a finding. The carry-forward is in fact
  registered, in fact open, in fact W6 scope per plan-doc. The
  auditor is reporting open carry-forwards as if they were W5
  substance defects rather than as informational status references
  — stylistic note, not a W5 defect. The carry-forward closes at
  W6 production-image cut.

- **F-0.2.17-W4-001 (info).** Same shape as W1-001 finding.
  Auditor reports W4-001 (ChromaDB re-index hook) as a finding;
  carry-forward is in fact registered, open, W6 scope. Closes at
  W6 along with W1-001.

- **AUDIT-G081 (important, structural pre-check).** Banned phrases
  ('clean close', 'landed beautifully', 'all green', 'shipped')
  matched literal text inside D6 evidence's
  `celebratory_framing_check` field, which explicitly enumerates
  the banned-phrase list as the phrases the retrospective avoided.
  Pre-check has no scope discrimination — it scans archive prose
  including fields whose content is explicitly the pattern set
  being checked.

- **AUDIT-PILLAR11 (critical, structural pre-check).** Git-op
  tokens ('git-add', 'git-commit', 'git-push') matched literal
  text inside `pillar_11_invariant_check.evidence.files_written`
  prose attesting that the executor did NOT invoke these
  primitives. Same shape as W3 D5 + W4 D7 (now confirmed across
  three audits). Pillar 11 invariant in fact respected; prose
  attests compliance.

**Drafter-arbitrated disposition: `pass_with_findings`.** All ten
findings are either (a) auditor correctly surfacing the
plan-doc-vs-repo-convention path drift (six findings, captured as
F-0.2.17-W5-002); (b) auditor reporting outstanding-state
observations on existing carry-forwards (two findings, accurate
status references); or (c) self-referential structural pre-check
fires (two findings, captured as F-0.2.17-W5-001 — third
occurrence in iteration; pattern-confirmed).

The D8 hard-fail condition — "self-audit produces fake-ID-on-
registered-anchor false positives that the filter should have
caught (W4 D1 hardening regression)" — **did not trigger.** No
finding has the failure shape. Filter was active and eligible
across all 8 model findings; suppressed_count=0 because no
candidate matched. **Bootstrap test 6 (loop closure with
stabilized auditor on documentation-heavy iteration) passes.**

## Carry-forwards CLOSED

None in W5 scope. The three pre-0.3.x gates (W1-001, W4-001,
W1-003) are explicitly W6 / operator scope per plan-doc.

## Carry-forwards ADDED

Two new W5 carry-forwards, surfaced by the D8 self-audit:

- **F-0.2.17-W5-001 — Structural pre-check self-referential
  pattern (third occurrence).** Severity: important. Source:
  0.2.17 W3 D5 + W4 D7 + W5 D8. Summary: audit-target prose that
  cites the regex patterns being checked (git-op tokens in Pillar
  11 evidence; G081 banned phrases in celebratory-framing
  compliance check) gets flagged as compliance failure by
  structural pre-checks. Pre-check has no awareness that a token
  appearing inside a compliance-evidence field is documentation,
  not violation. Disposition: structural pre-checks need scope
  discrimination — JSON path exclusion in pre-check scan (drafter
  recommendation: explicit and auditable; alternative
  context-aware regex with negative lookbehind is fragile because
  lookbehind state varies with field shape). Target: 0.3.x
  base-tier hardening. Audit traceability: W3 D5 + W4 D7 + W5 D8
  audit archives.

- **F-0.2.17-W5-002 — Plan-doc / repo-convention path drift.**
  Severity: info. Source: 0.2.17 W5 D8 audit findings 0-5.
  Summary: W5 plan-doc specified `docs/adr/` for new ADRs; repo
  convention is `artifacts/adrs/`; W4 close-note already pointed
  at `artifacts/adrs/`. Mechanism: drafter wrote plan-doc paths
  from chat-side architecture-artifact convention rather than
  consulting actual repo state; executor surfaced the drift in
  deliverable evidence rather than silent-picking. Disposition:
  future plan-docs should reference `artifacts/adrs/` for ADRs,
  `docs/architecture/` for architecture docs, `docs/retrospectives/`
  for retrospectives. Drafter chat-side convention update needed.
  Target: drafter chat-side process improvement + 0.3.x plan-doc
  convention notes.

The carry-forwards file update is **complete in this turn** — both
new entries appended via `aho.gap_carry_forward_writer.append_to_file`
in the same dogfooding pattern W2 / W4 used. Writer logged
`entry_count_before=32 → entry_count_after=34 (entries_added=2)`
under its strict regex; the permissive cross-iteration counter
took the file from 39 to 41 (W4 close-note convention).

The two counts measure different things — the strict regex counts
canonical `- **{id} — {title}**` entries inside the file scope of
the writer's heading detection; the permissive counter sweeps the
entire file including legacy entries. Both are honest; neither
contradicts the other. Same shape as W4 close note.

## Auditor-seat-transition continuation

W5 is the **fourth deployment of the in-container llama
auditor** (W2 first, W3 RAG-enriched, W4 RAG + deterministic
post-hoc filter, W5 RAG + filter against documentation-heavy
work). The protocol-level loop has now closed four times in
succession with progressively-stabilized auditor infrastructure.

**Bootstrap test 6 (loop closure with stabilized auditor on
documentation-heavy iteration) passes.** D8 self-audit ran the
W4-stabilized primitive (model + RAG + filter) against W5's own
acceptance archive; the audit emitted a structurally valid
disposition; the filter was active and eligible; the drafter
reviewed; this close note is authored; the operator signs. The
state machine `pending_audit → pending_drafter_review →
operator_sign` advances exactly as the architecture specifies.
Adversarial-Authorship-at-base-tier holds across documentation
work as well as code work.

**Filter activity at D8:** filter_eligible=true,
registered_id_count=16, model_findings_count=8,
active_findings_count=8, suppressed_count=0. The filter ran on
every model finding and produced the right answer for each.

**Pattern note (third occurrence pattern-confirms).** The
structural pre-check self-referential pattern has now fired in
W3 D5 (AUDIT-PILLAR11), W4 D7 (AUDIT-PILLAR11), and W5 D8
(AUDIT-G081 + AUDIT-PILLAR11). Three instances across the
iteration is enough signal to register as a real pattern requiring
fix rather than a one-off arbitration. F-0.2.17-W5-001 captures
this with two-option disposition (JSON path exclusion preferred;
context-aware regex secondary). 0.3.x base-tier hardening target.

## Pre-0.3.x hard gate (continuing reminder)

**Token rotation pre-0.3.x as a hard gate.** Operator (Kyle) must
rotate `ahomw:telegram_bot_token` before any 0.3.x work begins.
The 0.3.x launch gate cannot lift while the exposed token (from
W1's F-0.2.17-W1-003 incident) remains valid.
F-0.2.17-W1-003 carries this as the explicit operator-side
outstanding action.

This reminder is surfaced at every iteration close until the
rotation completes. Per the recurring protocol: surfaced at W1
close, surfaced at W2 close, surfaced at W3 close, surfaced at W4
close, **surfaced at W5 close (this note)**, surfaces at W6 close,
surfaces before tsP3 handoff.

Status check at W5 close:
- W4 close acknowledged the gate (operator sign-off line `Pre-0.3.x
  hard gates: rotate ahomw:telegram_bot_token (F-0.2.17-W1-003)`).
- Rotation status as of W5 close-note authoring:
  **operator_action_pending**.
- Outstanding pre-0.3.x gates: F-0.2.17-W1-003 (token rotation),
  F-0.2.17-W1-001 (secrets-test subcommand removal — W6 scope),
  F-0.2.17-W4-001 (ChromaDB re-index hook — W6 scope).

## Forward-looking note for W6

W6 closes the residual code-change carry-forwards. After W6 +
operator token rotation, 0.2.17 fully closes. Anticipated W6 scope
(drafter-input, not yet a plan):

- **F-0.2.17-W1-001 — secrets-test subcommand removal.** Production-
  image cut. Two candidate mechanisms (delete parser registration
  vs. `AHO_DEV_BUILD=1` env-gating); final mechanism pinned in W6
  plan-doc.
- **F-0.2.17-W4-001 — ChromaDB re-index hook.** Hook re-index into
  `gap_carry_forward_writer.append_to_file` OR schedule pre-audit
  re-index; either approach closes the staleness.
- **0.2.17 final close + tsP3 handoff.** After W6 closes its
  scope, 0.2.17 acceptance archive lands; operator runs token
  rotation per F-0.2.17-W1-003; 0.3.1 launches with clean
  carry-forward state for the gates we control. F-0.2.17-W5-001
  carries forward as 0.3.x base-tier hardening (auditor scope
  discrimination on structural pre-checks).

## State at close

- **Acceptance archive:** sealed,
  `audit_status: "pending_drafter_review"` at close-note
  authoring time. Drafter has reviewed (this turn) and arbitrated
  D8 findings + added F-0.2.17-W5-001 + F-0.2.17-W5-002 carry-
  forwards; status holds at `pending_drafter_review` until
  operator signs this close note. sha256
  `3ba226016b824641e8c07030cdc5bb74835c8d394228556a58850b1201520b8f`.
- **Audit archive:** sealed, untouched post-emit. sha256
  `5bd170e930c4b3e26df735651407ba9595e42457754bdd6b0f69838d1bcbe4e6`
  (target_artifact_sha256 inside the document is
  `8795328226425c4536ac03bbe7e1ca2a991f65485cf190756aad5bb179faffbd`,
  reflecting the pre-edit acceptance archive content the audit
  ran against — drafter arbitration occurs in the acceptance
  archive only, not the audit JSON).
- **Carry-forwards file:** updated in this turn. Two new entries
  appended (F-0.2.17-W5-001 under new target heading
  `## Target: 0.3.x base-tier hardening`; F-0.2.17-W5-002 under
  new target heading `## Target: drafter chat-side process
  improvement + 0.3.x plan-doc convention notes`). Strict-regex
  count (writer-internal): 32 → 34. Permissive cross-iteration
  count (per W4 close convention): 39 → 41. File update is
  **complete** pending operator review of this close note. sha256
  `72d0fc903477e9357defd41224d52c7841617a1e2b62a3bcd8fe39b43487b295`.
- **W6 launch gate:** blocked on operator signature on this close
  note. workstream_complete emit (next executor invocation, after
  operator sign) advances the state machine to
  `W5_workstream_complete` but does not lift the W6 launch gate
  by itself; the W6 plan-doc + W6 executor prompt is a drafter
  (claude-web) deliverable that follows operator sign.
- **W6 plan-doc + executor prompt:** deferred to chat after
  operator signs and this close note lands. Chat-first
  discipline holds; no W6 launch artifact edits drafted in this
  turn.

## Pillar 11 invariant cross-check

- **Drafter (claude-web):** zero git operations. Plan-doc
  authoring (W5 plan-doc was authored pre-session), drafter-
  arbitration prose (this turn), and close-note authoring
  (this turn) is artifact-only.
- **Executor (Claude Code):** zero git operations.
  `pillar_11_invariant_check` in `acceptance/W5.json` reads
  `result: "pass"` with evidence: no git/gh/push/commit/PR/merge
  primitive invoked across the executor session; all writes
  targeted `artifacts/adrs/` (0007 modify; 0009 + 0010 new),
  `docs/architecture/` (component-decomposition.md +
  claw3d-brick-spec.md, both new), `docs/retrospectives/`
  (0.2.17.md new), `artifacts/iterations/0.2.17/probes/`
  (W5_self_audit.py new), `artifacts/iterations/0.2.17/audit/W5.json`
  (audit emit by self-audit probe),
  `artifacts/iterations/0.2.17/acceptance/W5.json` (this archive),
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` (two
  appends for F-0.2.17-W5-001 + F-0.2.17-W5-002 via
  gap_carry_forward_writer in the same dogfooding pattern W2/W4
  established) — no `.git/`, no `~/.config/`, no `/etc/`, no
  `.ssh/` writes. F-0.2.17-W1-003 token rotation explicitly NOT
  performed (surfaced as continuing reminder under
  `outstanding_pre_03x_gates`).
- **Auditor (llama3.2:3b in-container, RAG + filter):** zero git
  operations. In-container model has no shell, no filesystem
  write capability outside the audit primitive's controlled
  emitter path. Audit archive itself is JSON-only — no
  executable artifacts. The RAG retrieval step
  (`aho.council.audit_ref_lookup`) reads the host-mounted
  ChromaDB collection only; no git tree access. The W4 D1
  filter (`aho.council.audit_finding_filter`) is pure Python
  string + regex operations; no I/O of any kind.
- **Self-audit AUDIT-PILLAR11 finding clarification:** the
  `git-add`/`git-commit`/`git-push` tokens that triggered the
  structural pre-check appear inside the
  `pillar_11_invariant_check.evidence` field as the literal list
  of primitives the executor did NOT invoke. Same shape as W3
  D5 + W4 D7 AUDIT-PILLAR11; same arbitration applies. The
  pre-check regex is conservative-by-design (flag for human
  review rather than auto-fail); the human review (this close
  note) confirms the tokens are descriptive prose attesting
  Pillar 11 compliance, not actual invocations. F-0.2.17-W5-001
  captures the recurring pattern.

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-04T03:27:43Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit halt)
D8 self-audit drafter arbitration acknowledged: 6 path-drift surfaces, 2 outstanding-gate observations, 2 self-referential structural pre-check artifacts
Carry-forwards added acknowledged: F-0.2.17-W5-001 (structural pre-check self-referential pattern), F-0.2.17-W5-002 (plan-doc / repo-convention path drift)
Pre-0.3.x hard gates (continuing): rotate ahomw:telegram_bot_token (F-0.2.17-W1-003) + remove secrets-test subcommand pre-final-promotion (F-0.2.17-W1-001) + ChromaDB re-index hook (F-0.2.17-W4-001)
Auditor-seat-transition continuation acknowledged (4th deployment, bootstrap test 6 passes): yes
W6 plan-doc + executor prompt drafter delivery acknowledged: yes (drafted at /mnt/user-data/outputs, ready for SCP to NZXTcos post-W5-close)
W6 launch gate: lifted
