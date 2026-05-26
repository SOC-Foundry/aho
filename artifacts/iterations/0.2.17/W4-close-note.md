# 0.2.17 W4 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `surface_to_drafter`).

W4 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W4.json`.
W4 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W4.json` with
`disposition: "surface_to_drafter"` (llama self-audit verbatim).
Drafter (claude-web) arbitrated all four D7 findings - three to
"auditor stylistic observations correctly reflecting RAG state" and
one to "self-referential structural pre-check" (same shape as W3 D5
AUDIT-PILLAR11). Sealed shas (verified at close-note authoring
time):

- acceptance archive sha256:
  `949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`
  (target_artifact_sha256 inside the audit document:
  `a1432e3dd323e06ca281918aaa1c43fdaeaab4832e1abc3c6f6083f236eefeb0`,
  reflecting the pre-edit acceptance archive content the audit ran
  against - drafter arbitration occurs in the acceptance archive
  only, not the audit JSON)
- carry-forwards file sha256 (post-W4-001 append):
  `c75e6de5e5ba9ecb860e5313c09a8d81976c185773c8c50ae2e57efdec1cc7ee`

Audit archive (`audit/W4.json`) is UNTOUCHED post-emit. The
disposition field reads `surface_to_drafter`; drafter arbitration
is recorded only in the acceptance archive's D7 evidence section
+ carry-forwards added entry, and in this close note's prose. Per
Adversarial Authorship sealed-archive convention, audit archives
are not amended after emit - corrections and arbitrations land in
acceptance evidence and close-note prose, never in the audit JSON.

## Materiality status

W4 lands the architecture-validation closure. The RAG enrichment +
deterministic post-hoc filter combination provides both
architecture validation (W0 closure when the model attends to the
registered-references context) and failure-mode containment (W4
D1 catches when the model does not attend). Three iterations of
materiality data now span the auditor-seat work:

- **W2 baseline:** in-container llama auditor with no RAG
  enrichment. False positives on registered-anchor IDs surfaced
  systematically (F-0.2.17-W2-006).
- **W3 partial fix:** RAG enrichment via aho.council.audit's
  pre-prompt context section. Closed 1 of 2 demonstrated false
  positives (W0 F-W0-004 closed; W2 self-audit F-0.2.17-W1-003
  persisted under same prompt rule, same context shape, same
  model - small-model prompt-following inconsistency at base
  tier).
- **W4 structural closure:** deterministic post-hoc filter on the
  finding list. Filter inspects each finding for (a) a registered
  anchor in the description AND (b) a fake-ID phrase from the
  canonical set. Suppresses ONLY when both match. Verified
  against the exact F-0.2.17-W1-003 false positive that W3 D4 left
  open (D1 acceptance gate 1, target sha
  `afbc33a3ae68d90f444e5661cf7146180de9798eb2534a1cfd1f004882bfc91a`).
  Verified NOT to over-suppress on the W3 self-audit (D1 gate 2,
  target sha
  `b3a4e2e6c88244f4b4fcd59f75b56112beed8287600eb2308a7cdb7f4a605efc`,
  three findings remain active). Synthetic positive and negative
  tests cover the structural-narrowness invariant.

The W4 D1 filter does NOT bet the architecture on small-model
prompt-following. The model can ignore the registered-references
rule and the failure mode is still contained because the filter
reads the same RAG context the prompt section was built from and
applies the suppression deterministically.

## D7 self-audit findings section

W4 self-audit ran `aho.council.audit(artifact=W4_acceptance_archive,
rag_enrichment=True)` against the W4 acceptance archive at the
moment of seal-1 (pre-edit, target sha
`a1432e3d…`). Llama returned disposition `surface_to_drafter`
at confidence 0.85 with four findings. Drafter (claude-web)
arbitrated all four:

- **F-0.2.17-W3-001 (important).** "The artifact claims that the
  carry-forward ID F-0.2.17-W3-001 is registered, but its source
  is not found in the iteration-context." - Auditor accurately
  reports W3-001 as unverified in RAG state. RAG enrichment shows
  W3-001 status=`unverified`, top_source_artifact_path=null. Filter
  did not suppress because no fake-ID phrase in description. The
  defect is upstream in the indexing pipeline, not in the audit.
  **Captured as new carry-forward F-0.2.17-W4-001 (ChromaDB index
  staleness).**

- **F-0.2.17-W9-999 (important).** "The artifact claims that the
  carry-forward ID F-0.2.17-W9-999 is registered, but its source
  is not found in the iteration-context." - Synthetic test ID
  from D1 acceptance gate 4 (the negative case, where an
  unverified-anchor + fake-phrase finding must NOT suppress). The
  test ID is genuinely unverified by construction. Same
  auditor-doing-its-job pattern as the W3-001 finding above. Not
  a substance defect.

- **G081 (info).** "The artifact mentions a gotcha G081, but does
  not provide any further information about it." - Stylistic
  information-density observation. G081 is registered in the RAG
  context. No fake-ID phrase. No action; the full G081 text lives
  in the harness-base reference, which is iteration-context
  scope, not W4 acceptance archive scope.

- **AUDIT-PILLAR11 (critical, structural pre-check).** "Possible
  Pillar 11 reference (agent-side git op): 'git-add',
  'git-commit', 'git-push'." - Auditor's structural pre-check
  regex matched the literal `git-add`, `git-commit`, `git-push`
  tokens inside `pillar_11_invariant_check.evidence` (the field
  documenting "we never invoke these"). Self-referential. Same
  shape as W3 D5 AUDIT-PILLAR11; same drafter arbitration
  applies. Structural pre-checks are regex-grounded and bypass
  the W4 D1 filter by design.

**Drafter-arbitrated disposition: `pass_with_findings`.** All four
findings either (a) accurately report RAG state for unverified
IDs, with the underlying staleness captured as F-0.2.17-W4-001;
(b) are stylistic / information-density observations; or (c) are
structural pre-checks self-referential to the Pillar 11 evidence
prose. None of them are W4 substance defects.

The D7 hard-fail condition - "self-audit produces fake-ID-on-
registered-anchor false positives that the filter should have
caught (i.e., model still flags a registered ID as 'not real' /
'placeholder' AND the filter fails to suppress it)" - **did not
trigger.** No finding has the failure shape. Filter was active
and eligible across all 3 model findings; suppressed_count=0
because no candidate matched. **Bootstrap test 5 (loop closure
with stabilized auditor) passes.**

## Carry-forwards CLOSED

Two W3-era carry-forwards close at W4 close, both via the W4 D1
deterministic post-hoc filter:

- **F-0.2.17-W2-006 - Auditor reference-resolution gap.**
  Closure basis: W4 D1 deterministic post-hoc filter
  structurally suppresses the F-0.2.17-W3-001 false-positive
  shape on the W2 self-audit-rag artifact. Combined with W3's W0
  closure, both demonstrated false positives (the only two that
  manifested across W0/W1/W2 RAG replays) are now structurally
  addressed. Closure condition met: D7 self-audit produced no
  novel fake-ID-on-registered-anchor false-positive shapes;
  filter was eligible (15 registered IDs) and ran on every model
  finding.

- **F-0.2.17-W3-001 - Llama3.2:3b inconsistently honors the
  registered-references prompt rule.** Closure basis: W4 D1
  deterministic post-hoc filter is the drafter-arbitrated path
  (c) closure. Filter verified against the exact F-0.2.17-W1-003
  false-positive that motivated this carry-forward (D1 gate 1).
  Closure condition met: same as W2-006 above.

Both closures recorded in `acceptance/W4.json::carry_forwards_closed`
with explicit closure_basis and closure_condition_met fields.

## Carry-forwards ADDED

One new W4 carry-forward, surfaced by the D7 self-audit's RAG
enrichment state inspection:

- **F-0.2.17-W4-001 - ChromaDB iteration-context index does not
  auto-refresh on carry-forwards-0.2.16.md updates.** Severity:
  important. Source: 0.2.17 W4 D7 self-audit RAG enrichment state
  inspection. Summary: D7's RAG enrichment showed three carry-
  forwards (F-0.2.17-W3-001, F-0.2.17-W3-002, F-0.2.17-W2-006) as
  status=`unverified` with top_source_artifact_path=null, despite
  all three being added in W2/W3 closes to
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`. The IDs
  are in fact registered in the file; the ChromaDB index built
  during W2 D1 pre-seed has not been refreshed since. Mechanism:
  `gap_carry_forward_writer.append_to_file` writes to the markdown
  file but does not trigger ChromaDB re-index. Disposition: hook
  re-index into the writer's append path, or schedule pre-audit
  re-index. Target: 0.2.17 W5 retrospective fold-in OR 0.3.x
  base-tier hardening. Audit traceability:
  `audit/W4.json` (sha `9d5ab9ec…`) finding entries 1–2 and the
  W2-006 reference entry in the rag_enrichment.references list.

The carry-forwards file update is **complete in this turn** - the
new entry was appended via `aho.gap_carry_forward_writer.append_to_file`
in the same dogfooding pattern W2 used for D7. The writer logged
`entry_count_before=31 → entry_count_after=32 (entries_added=1)`
under its strict regex; the W3 close note's permissive
cross-iteration counting convention took the file from 38 to 39.
The two counts measure different things - the strict regex counts
canonical `- **{id} - {title}**` entries inside the file scope of
the writer's heading detection; the permissive counter sweeps the
entire file including legacy entries that don't match the writer's
exact shape. Both are honest; neither contradicts the other.

**Note the irony.** The new carry-forward F-0.2.17-W4-001 surfaces
ChromaDB index staleness on this exact file, which the writer
just appended to. The writer's append path will need to trigger
re-index before the next audit's RAG enrichment will reflect
F-0.2.17-W4-001 as `registered`. Until then, an audit run today
would correctly flag F-0.2.17-W4-001 as `unverified` for the same
reason the D7 self-audit flagged W3-001 / W3-002 / W2-006 - the
defect captured by W4-001 is exhibited by W4-001 itself.

## Auditor-seat-transition continuation

W4 is the **third deployment of the in-container llama
auditor** (W2 first, W3 RAG-enriched, W4 RAG + deterministic
post-hoc filter). The protocol-level loop has now closed three
times in succession with progressively-stabilized auditor
infrastructure.

**Bootstrap test 5 (loop closure with stabilized auditor) passes.**
D7 self-audit ran the W4-stabilized primitive (model + RAG +
filter) against W4's own acceptance archive; the audit emitted a
structurally valid disposition; the filter was active and
eligible; the drafter reviewed; this close note is authored; the
operator signs. The state machine `pending_audit →
pending_drafter_review → operator_sign` advances exactly as the
architecture specifies. Adversarial-Authorship-at-base-tier holds.

**Filter activity at D7:** filter_eligible=true,
registered_id_count=15, model_findings_count=3, active_findings_count=3,
suppressed_count=0. The W4 plan-doc D7 acceptance gate explicitly
accepts both zero-suppression and non-zero-suppression as valid
outcomes ("either result demonstrates the W4 D1 fix is live").
This run produced zero - the model did not generate the
F-0.2.17-W3-001 failure shape on the W4 archive. The filter ran
on every finding and produced the right answer for each.

## Pre-0.3.x hard gate (continuing reminder)

**Token rotation pre-0.3.x as a hard gate.** Operator (Kyle) must
rotate `ahomw:telegram_bot_token` before any 0.3.x work begins.
The 0.3.x launch gate cannot lift while the exposed token (from
W1's F-0.2.17-W1-003 incident) remains valid.
F-0.2.17-W1-003 carries this as the explicit operator-side
outstanding action.

This reminder is surfaced at every iteration close until the
rotation completes. Per the recurring protocol: surfaced at W1
close, surfaced at W2 close, surfaced at W3 close,
**surfaced at W4 close (this note)**, surfaces at W5 close,
surfaces before tsP3 handoff.

Status check at W4 close:
- W3 close acknowledged the gate (operator sign-off line
  `Pre-0.3.x hard gate: rotate ahomw:telegram_bot_token`).
- Rotation status as of W4 close-note authoring:
  **operator_action_pending**.
- Outstanding pre-0.3.x gates: F-0.2.17-W1-003 (token rotation),
  F-0.2.17-W1-001 (secrets-test subcommand still in rc1 image -
  folded into W5 retrospective per W2 plan, now also explicitly
  surfaced for the pre-final-promotion gate).

## Forward-looking note for W5

W5 is the consolidation iteration. Drafter (claude-web) drafts
the W5 plan-doc + executor prompt after operator signs this close
note; this executor session does not author any forward-looking
artifacts per the W4 executor prompt's halt-and-surface
discipline. Anticipated W5 scope (drafter-input, not yet a plan):

- **ADR consolidation.** ADR-0007 amendment (containerization
  resolution), ADR-0009 (secrets broker), ADR-0010 (materiality
  measurement protocol). Convert from chat artifacts to repo-
  resident docs at `artifacts/adrs/`.
- **Component decomposition + claw3d brick spec.** The brick
  layer ships under `src/aho/dashboard/lego/bricks.py` in W4;
  the spec doc that names which signals each brick reads, what
  the synthetic load test looks like, and how the per-component
  faults map to brick reds, is W5 work. The acceptance archive
  records the brick coverage list verbatim from the W4 plan-doc;
  the spec doc converts that list into repo-resident artifact.
- **0.2.17 retrospective.** Three-iteration arc: W2 baseline →
  W3 partial fix → W4 structural closure. Honest accounting of
  the small-model prompt-following limitation and the structural
  fix that contains it.
- **F-0.2.17-W4-001 disposition.** W5 fold-in: hook re-index
  into `gap_carry_forward_writer.append_to_file`, OR define a
  pre-audit re-index step. Either approach closes the staleness.
- **F-0.2.17-W1-001 (secrets-test subcommand).** Removal /
  remediation pre-final-promotion.
- **Pre-0.3.x hard gate surface.** Token rotation surfaces again.

## State at close

- **Acceptance archive:** sealed,
  `audit_status: "pending_drafter_review"` at close-note
  authoring time. Drafter has reviewed (this turn) and arbitrated
  D7 findings + claimed F-0.2.17-W2-006 + F-0.2.17-W3-001 closures
  + added F-0.2.17-W4-001 carry-forward; status holds at
  `pending_drafter_review` until operator signs this close note.
  sha256
  `949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`.
- **Audit archive:** sealed, untouched post-emit. sha256
  `9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`
  (target_artifact_sha256 inside the document is
  `a1432e3dd323e06ca281918aaa1c43fdaeaab4832e1abc3c6f6083f236eefeb0`,
  reflecting the pre-edit acceptance archive content the audit
  ran against - drafter arbitration occurs in the acceptance
  archive only, not the audit JSON).
- **Carry-forwards file:** updated in this turn. One new entry
  appended (F-0.2.17-W4-001) under new target heading
  `## Target: 0.2.17 W5 retrospective fold-in OR 0.3.x base-tier hardening`.
  Strict-regex count (writer-internal): 31 → 32. Permissive
  cross-iteration count (per W3 close convention): 38 → 39.
  F-0.2.17-W2-006 + F-0.2.17-W3-001 closure status updates land
  in this close note's prose (per W2/W3 close conventions); the
  W2-era and W3-era entry bodies are unchanged in the file.
  File update is **complete** pending operator review of this
  close note. sha256
  `c75e6de5e5ba9ecb860e5313c09a8d81976c185773c8c50ae2e57efdec1cc7ee`.
- **W5 launch gate:** blocked on operator signature on this
  close note. workstream_complete emit (next executor invocation,
  after operator sign) advances the state machine to
  `W4_workstream_complete` but does not lift the W5 launch gate
  by itself; the W5 plan-doc + W5 executor prompt is a drafter
  (claude-web) deliverable that follows operator sign.
- **W5 plan-doc + executor prompt:** deferred to chat after
  operator signs and this close note lands. Chat-first
  discipline holds; no W5 launch artifact edits drafted in this
  turn.

## Pillar 11 invariant cross-check

- **Drafter (claude-web):** zero git operations. Plan-doc
  authoring (W4 plan-doc was authored pre-session, with the
  post-W3-close refresh that introduced D1), drafter-arbitration
  prose, and close-note authoring is artifact-only.
- **Executor (Claude Code):** zero git operations.
  `pillar_11_invariant_check` in `acceptance/W4.json` reads
  `result: "pass"` with evidence: no git/gh/push/commit/PR/merge
  primitive invoked across the executor session; all writes
  targeted `src/aho/council/` (audit_finding_filter.py new;
  audit.py modify), `src/aho/audit_disposition_emitter.py`
  (modify - surface suppressed_findings + finding_filter in
  emitted JSON), `src/aho/dashboard/lego/` (bricks.py,
  materiality_surfaces.py, role_collapse_brick.py,
  materiality_comparison.py, anti_rubber_stamp_dashboard.py -
  all new), `src/aho/materiality_baseline_extract.py` (new),
  `artifacts/tests/` (six new test files),
  `artifacts/iterations/0.2.17/probes/W4_self_audit.py` (new),
  `artifacts/iterations/0.2.17/audit/W4.json` (audit emit),
  `artifacts/iterations/0.2.17/acceptance/W4.json` (this
  archive), `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
  (one append for F-0.2.17-W4-001 via gap_carry_forward_writer
  in the same D7-dogfooding pattern W2 established) - no `.git/`,
  no `~/.config/`, no `/etc/`, no `.ssh/` writes.
  F-0.2.17-W1-003 token rotation explicitly NOT performed
  (surfaced as continuing reminder under
  `outstanding_pre_03x_gates`).
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
  `git-add`/`git-commit`/`git-push` tokens that triggered the
  structural pre-check appear inside the
  `pillar_11_invariant_check.evidence` field as the literal list
  of primitives the executor did NOT invoke. Same shape as W3
  AUDIT-PILLAR11; same arbitration applies. The pre-check regex
  is conservative-by-design (flag for human review rather than
  auto-fail); the human review (this close note) confirms the
  tokens are descriptive prose attesting Pillar 11 compliance,
  not actual invocations.

## Operator sign-off

Signed by:
Date:
Disposition acknowledged:
D7 self-audit drafter arbitration acknowledged:
F-0.2.17-W2-006 closure acknowledged (via W4 D1):
F-0.2.17-W3-001 closure acknowledged (via W4 D1):
Carry-forward added acknowledged: F-0.2.17-W4-001 (ChromaDB index staleness)
Pre-0.3.x hard gate (continuing): rotate ahomw:telegram_bot_token (F-0.2.17-W1-003)
F-0.2.17-W1-001 (secrets-test subcommand) folded into W5 retrospective:
Auditor-seat-transition continuation acknowledged:
W5 plan-doc + executor prompt drafter delivery acknowledged:
W5 launch gate:

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-03T19:54:16Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit surface_to_drafter)
Carry-forwards closed: F-0.2.17-W2-006, F-0.2.17-W3-001 (D1 deterministic post-hoc filter structurally verified + D7 produced no fake-ID-on-registered shapes)
Carry-forwards added: F-0.2.17-W4-001 (ChromaDB iteration-context index staleness)
Materiality status: architecture validated structurally - RAG enrichment + deterministic post-hoc filter combination provides architecture-validation when model attends + failure-mode containment when it does not
Pre-0.3.x hard gates: rotate ahomw:telegram_bot_token (F-0.2.17-W1-003) + remove secrets-test subcommand pre-final-promotion (F-0.2.17-W1-001) - both surfaced at W4 close per recurring protocol
W5 launch gate: lifted (W5 = retrospective + ADR consolidation, final 0.2.17 workstream)
