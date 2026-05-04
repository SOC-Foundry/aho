# 0.2.17 W3 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `halt`).

W3 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W3.json`.
W3 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W3.json` with
`disposition: "halt"` (llama self-audit verbatim). Drafter
(claude-web) arbitrated all three D5 findings to "auditor
self-referential artifacts, not W3 substance defects" — see D5
self-audit findings section below. Sealed shas (verified at
close-note authoring time):

- acceptance archive sha256:
  `9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `b3a4e2e6c88244f4b4fcd59f75b56112beed8287600eb2308a7cdb7f4a605efc`
  (target_artifact_sha256 inside the audit document:
  `b1c093fa8863919f8f0720715abe6e4f3683cf0a9984c042ff7a473571e68cc4`)
- audit/replay/W0-llama-rag.json sha256:
  `022c3550d19268e61e5365cf06111839c15f2df6e8095756ebcd486513fa97bc`
- audit/replay/W1-llama-rag.json sha256:
  `0cbf90bb2dda18f10c300f8ecf2bdeadfd7fe99642e16ecef3a1257973423226`
- audit/replay/W2-self-audit-rag.json sha256:
  `afbc33a3ae68d90f444e5661cf7146180de9798eb2534a1cfd1f004882bfc91a`
- audit/replay/comparison-rag-vs-non-rag.json sha256:
  `3057c9540fb6cd14052a72eff1b844cd5609bd7dcd2c34f1863fd836f4fae3b4`

Audit archive (`audit/W3.json`) is UNTOUCHED post-emit. The
disposition field reads `halt`; drafter arbitration is recorded
only in the acceptance archive's D5 evidence section + carry-
forward arbitration entries, and in the close-note prose below.
Per Adversarial Authorship sealed-archive convention, audit
archives are not amended after emit — corrections and
arbitrations land in acceptance evidence and close-note prose,
never in the audit JSON.

## Materiality thesis result

W3 is the load-bearing test of "RAG enrichment closes the
auditor reference-resolution gap." The result is
**partial validation**.

D4 ran the auditor primitive (`aho.council.audit` with
`rag_enrichment=True`) against the same three sealed archives W2
audited without RAG enrichment. The comparison artifact at
`audit/replay/comparison-rag-vs-non-rag.json` records:

- **W0 replay (non-RAG → RAG):** the W2-era false positive
  ("F-W0-004 not corroborated") **closed**. The RAG-enriched
  auditor honored the registered-references context section;
  F-W0-004 surfaced as `registered` with snippet pointing to
  the 0.2.17 plan-doc carry-forward closure context, and the
  auditor did not reproduce the false-positive finding.
- **W1 replay:** non-RAG produced no fake-ID finding, so there
  was nothing to close. Both runs converged on the same Pillar
  11 friction finding via F-0.2.17-W1-003 (sealed Pillar 11
  incident from W1 close); only the disposition framing
  differed (RAG: `halt`; non-RAG: `surface_to_drafter`).
  Stylistic disagreement, not substantive.
- **W2 self-audit replay:** the W2-era false positive
  ("F-0.2.17-W1-003 does not look real (matches naming
  conventions)") **persisted**. The RAG-enriched auditor's
  registered-references section listed F-0.2.17-W1-003 as
  `registered` with a snippet citing the W1 acceptance
  Pillar 11 incident — the prompt context was correct — but
  llama still emitted the same fake-ID flag. Same prompt rule,
  same context shape, same model, different outcome from the W0
  replay.

**Closure rate: 1 of 2 demonstrated false positives closed.**
**F-0.2.17-W2-006 is therefore PARTIAL CLOSURE — not full closure.**

The architecture works in principle. The W0 closure is a real
data point that the RAG-as-context-feed for auditor seat from
the architecture artifact's §Component decomposition is
load-bearing — when the auditor honors the registered-references
context, the false positive disappears. The W2 persistence is
also a real data point: small-model prompt-following at base
tier is the bottleneck. Llama3.2:3b will sometimes ignore the
authoritative context section and emit pattern-matched
findings about ID syntax in isolation.

This is honest materiality data. It validates the architecture
direction while qualifying the "auditor at base tier" claim
with model-consistency reservations. **Forward-looking input to
0.3.x partial-tier design:** a stronger auditor model (qwen3.5:9b,
llama3.3, etc.) likely raises the prompt-following consistency
floor; that is a 0.3.x evaluation question, not a 0.2.17 one.

The substantive cross-audit halt-and-surface condition (RAG
version says clean while non-RAG version found a real Pillar 11
violation) **did not trigger** in any of the three replays. All
disagreements are stylistic or "auditor missed a context cue,"
not substantive coverage gaps.

## D5 self-audit findings section

W3 self-audit ran `aho.council.audit(artifact=W3_acceptance_archive,
rag_enrichment=True)` against the W3 acceptance archive at the
moment of seal-1 (pre-edit). Llama returned disposition `halt`
at confidence 0.95 with three findings. Drafter (claude-web)
arbitrated all three to **auditor self-referential artifacts,
not W3 substance defects**:

- **F-0.2.17-W3-001 (important).** "Llama3.2:3b inconsistently
  honors the registered-references prompt rule." — The
  auditor echoed the executor-added carry-forward title
  verbatim. Tautological — the carry-forward itself captures
  the real issue (small-model prompt-following inconsistency).
  The "finding" is just the carry-forward title showing up
  again. Not a substance defect; the auditor is reporting
  W3-001 as a finding because W3-001's title describes a
  problem.

- **G081 (info).** "No celebratory framing in G081." —
  Confirmation-shape. The auditor read the structural pre-check
  result that says "G081 banned-phrases pass" and reported it
  as a finding rather than as the absence-of-finding it is.
  Llama is summarizing the pre-check pass status as if it were
  a per-finding observation. Not a substance defect; G081
  pre-check did pass cleanly.

- **AUDIT-PILLAR11 (critical, structural pre-check).**
  "Possible Pillar 11 reference (agent-side git op): 'git-add',
  'git-commit', 'git-push'." — The auditor's structural
  pre-check regex matched the literal `git-add`, `git-commit`,
  `git-push` tokens inside `pillar_11_invariant_check.evidence`
  (the field documenting "we never invoke these"). Self-
  referential. Same shape as a security scanner flagging its
  own regex pattern. Not a substance defect; no git operation
  was invoked across the executor session — the literal tokens
  appear inside the prose that ATTESTS Pillar 11 compliance.

**Drafter-arbitrated disposition: `pass_with_findings`.** All
three findings are auditor self-referential artifacts inherent
to small-model audit at base tier. None of them surface a
W3-substance defect that requires remediation. The arbitration
is recorded in `acceptance/W3.json::deliverables[D5].evidence.
drafter_review_note` and in this prose; the sealed
`audit/W3.json` is unmodified.

The D5 hard-fail condition (false-positive ID-validation
findings — "the same shape that motivated W3 in the first
place") **did not trigger**. None of the three findings flag a
reference ID as fake or placeholder. The shape that
F-0.2.17-W2-006 named is absent from the W3 self-audit; the
RAG enrichment did its job at the structural level. The
inconsistency captured by F-0.2.17-W3-001 is at the prompt-
following level, not the ID-validation level.

## F-0.2.17-W2-006 carry-forward disposition

**F-0.2.17-W2-006 stays OPEN.** Drafter arbitration: partial
closure does not constitute full closure. The W3 work resolved
the W0-replay manifestation of the gap (F-W0-004 no longer
flagged as fake) but did NOT resolve the W2-self-audit
manifestation (F-0.2.17-W1-003 still flagged as not-real-
looking). Closing F-0.2.17-W2-006 on a 1-of-2 closure record
would misrepresent the materiality data.

`acceptance/W3.json::carry_forwards_partial_closure_claim` records
the partial-closure claim with explicit drafter arbitration:

> "OPEN — partial closure does not constitute full closure.
> F-0.2.17-W3-001 inherits as more specific surface of same
> underlying issue. Closes via W4 deterministic post-hoc filter."

F-0.2.17-W3-001 (small-model prompt-following inconsistency)
is the more-specific carry-forward that the W4 work targets.
F-0.2.17-W2-006 closes when F-0.2.17-W3-001 closes — the W4
deterministic post-hoc filter (drafter-arbitrated path c)
addresses both at the same structural level.

## New carry-forwards

Two new W3 carry-forwards appended to
`artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`. Full
entry text mirrors `acceptance/W3.json::carry_forwards_added`
and follows the canonical bullet shape used by the W2 entries
(F-0.2.17-W2-001 through F-0.2.17-W2-006) in the same file.

- **F-0.2.17-W3-001 — Llama3.2:3b inconsistently honors the
  registered-references prompt rule.** Severity: important.
  Source: 0.2.17 W3 D4 RAG-vs-non-RAG comparison artifact.
  Summary: "D4 W2 self-audit re-run with RAG enrichment
  continued to flag F-0.2.17-W1-003 as 'ID does not look real
  (matches naming conventions)' even though the registered-
  references section listed it as `registered` with a snippet
  pointing to W1 acceptance archive. The W0 replay correctly
  stopped flagging F-W0-004; the W2 self-audit did not stop
  flagging F-0.2.17-W1-003. Same prompt rule, same context
  shape, same model, different outcome." Mechanism: "Small-
  model prompt-following inconsistency at base tier. Llama3.2:3b
  honors the registered-references rule on some prompts but
  not others — the rule is paragraph-form text at the end of a
  large system prompt, and the model selectively attends."
  Disposition: "Drafter selects path (c) deterministic post-
  hoc filter as the structural fix appropriate for base-tier
  auditor model. After llama emits a finding, a deterministic
  post-pass drops findings whose anchor IDs are listed
  `registered` in the prompt context AND whose description
  matches the fake-ID phrase set ('not real', 'looks
  placeholder', 'matches naming conventions', etc.). This
  closes the gap without relying on prompt-following on a
  small model. Architecture: same RAG context pipeline; new
  filter layer between the audit primitive's model output and
  the disposition return." Target: "0.2.17 W4 — deterministic
  post-hoc filter on RAG-aware audit findings (drafter-
  arbitrated path c)." Audit traceability: surfaced in
  `audit/replay/comparison-rag-vs-non-rag.json` (sha
  `3057c954…`) and consolidated in W3 D4 evidence.

- **F-0.2.17-W3-002 — Plan-doc spurious-ID test token is not
  structurally detectable.** Severity: info. Source: 0.2.17 W3
  D1/D2 implementation. Summary: "Plan doc D2 acceptance gate
  names `F-FAKE-9.9.9-W9-999` as the spurious test ID expected
  to return `unverified`. The carry_forward_full pattern
  requires digits after `F-`, so `F-FAKE-...` is not detected
  at D1 and therefore never reaches D2. F-9.9.9-W9-999 was
  substituted as the structurally-valid synthetic spurious
  token; gate semantics held." Disposition: "Document the
  substitution in any later replay. No code change needed."
  Target: drafter awareness during W3 close-note authoring
  (this turn).

The carry-forwards file update is **complete in this turn**.
Operator review of the file update lands at the same chat turn
as operator review of this close note.

## Coherence summary

- W2 close-state baseline: 36 total in
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
  (per W2 close note, using the cross-iteration tracking
  convention).
- W3 close adds 2 new entries (F-0.2.17-W3-001, F-0.2.17-W3-002)
  → **38 total** post-update (cross-iteration tracking
  convention via permissive header regex).
- F-0.2.17-W2-006 status note: stays OPEN per drafter
  arbitration; W2's existing entry is unchanged in the file.
  Status update lands in this close note's prose, not in the
  W2-era entry's body — same convention as W2's W0/W1-era
  status updates.
- Acceptance archive's `carry_forwards_added` field lists
  exactly two entries (F-0.2.17-W3-001, F-0.2.17-W3-002);
  matches the file-side append count of +2.
- `carry_forwards_closed` field is empty (no W3 closure
  claimed beyond partial). `carry_forwards_partial_closure_
  claim` lists F-0.2.17-W2-006 with drafter-arbitrated
  decision OPEN.
- Audit archive itself is not amended; the count walk is
  recorded here in the close note rather than as an archive
  amendment, preserving the audit's sealed state.

## Auditor seat transition section (continuation)

W3 is the **second deployment of the in-container llama
auditor (W2 was the first), now upgraded with RAG
enrichment.** The bootstrap test 4 from the architecture
artifact's progression — does the auditor that W3 just
upgraded correctly audit W3's own work? — has its result.

**The loop closes structurally.** D5 self-audit ran the
upgraded primitive against W3's own acceptance archive; the
audit emitted a structurally valid disposition; the drafter
reviewed; the close note authored; the operator signs. The
state machine `pending_audit → pending_drafter_review →
operator_sign` advances exactly as the architecture
specifies. From a Adversarial-Authorship-at-base-tier
perspective the protocol works.

**The loop closes with a model-consistency caveat.** D4's
1-of-2 false-positive closure rate is the honest data point.
The architecture's RAG-as-context-feed primitive is the
correct shape; the small-model prompt-following inconsistency
is the bottleneck. The W4 deterministic post-hoc filter
addresses the small-model case at the structural level rather
than relying on prompt-following — same RAG context pipeline,
new structural layer between model output and disposition
return.

**Drafter sign-off on the bootstrap test 4 result.** From a
drafter (claude-web) perspective: the upgrade lands cleanly
at the protocol level (loop closes), and the model-consistency
caveat is captured as a concrete W4 deliverable
(F-0.2.17-W3-001) rather than as an ambiguous "needs more
work." The materiality data is honest, the partial-closure
claim is explicit, and the forward-looking work is scoped.
This is the design intent of the gap-net pattern — surface
what the auditor cannot fully resolve, then arbitrate with
the broader context the auditor lacks.

## Pre-0.3.x hard gate (continuing reminder)

**Token rotation pre-0.3.x as a hard gate.** Operator (Kyle)
must rotate `ahomw:telegram_bot_token` before any 0.3.x work
begins. The 0.3.x launch gate cannot lift while the exposed
token (from W1's F-0.2.17-W1-003 incident) remains valid.
F-0.2.17-W1-003 carries this as the explicit operator-side
outstanding action.

This reminder is surfaced at every iteration close until the
rotation completes. Per the recurring protocol: surfaced at
W1 close, surfaced at W2 close, **surfaced at W3 close (this
note)**, surfaces at W4 close, surfaces at W5 close, surfaces
before tsP3 handoff. Executor is not authorized to rotate
tokens; this is operator-only.

Status check at W3 close:
- W2 close acknowledged the gate (operator sign-off line
  `Pre-0.3.x hard gate: rotate ahomw:telegram_bot_token`).
- Rotation status as of W3 close-note authoring:
  **operator_action_pending**.
- Outstanding pre-0.3.x gates: F-0.2.17-W1-003 (token
  rotation), F-0.2.17-W1-001 (secrets-test subcommand still in
  rc1 image — folded into W5 retrospective per W2 plan).

## Forward-looking note for W4

**F-0.2.17-W3-001 (deterministic post-hoc filter on RAG-aware
audit findings) is a W4 deliverable.** Drafter (Claude web)
will refresh the existing W4 plan doc + executor prompt
before W4 launch to include the filter as a sixth deliverable
alongside the existing claw3d brick rendering scope.

**Filter shape (drafter-arbitrated path c):** after llama
emits an audit disposition, a deterministic post-pass walks
the findings list. Each finding's `id` field (the anchor ID)
is checked against the RAG enrichment context — if the anchor
appears in `rag_enrichment.references` with `status:
"registered"` AND the finding's `description` matches the
fake-ID phrase set (`"not real"`, `"looks placeholder"`,
`"matches naming conventions"`, `"not corroborated"`, etc.),
the finding is dropped before the disposition returns. The
filter logs each drop so materiality counters and audit
traceability hold. Architecture: same RAG context pipeline
from W3; new structural layer between model output and
disposition return; the audit primitive's contract surface
(disposition + confidence + findings + evidence_traces) is
unchanged from the consumer perspective.

**Why path (c) over (a) prompt-strengthening or (b) model
upgrade:** path (a) bets the architecture on small-model
prompt-following, which W3 D4 demonstrated is unreliable;
path (b) is appropriate for 0.3.x partial-tier work but
breaks the "auditor at base tier" claim 0.2.17 is supposed
to validate. Path (c) keeps base-tier auditor and closes the
specific failure mode at the structural level — the
materiality buckets stay honest because the filter logs
every drop.

**Other W4 scope unchanged:** claw3d brick rendering,
materiality four-bucket dashboard surfaces, per-component
bricks, role-collapse trip-wire brick wiring (the OTEL signal
from W2 D5 → brick render). W5 retrospective and ADRs remain
W5.

## State at close

- **Acceptance archive:** sealed,
  `audit_status: "pending_drafter_review"` at close-note
  authoring time. Drafter has reviewed (this turn) and
  arbitrated D5 findings + F-0.2.17-W2-006 partial-closure
  claim; status holds at `pending_drafter_review` until
  operator signs this close note. sha256
  `9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`.
- **Audit archive:** sealed, untouched post-emit. sha256
  `b3a4e2e6c88244f4b4fcd59f75b56112beed8287600eb2308a7cdb7f4a605efc`
  (target_artifact_sha256 inside the document is
  `b1c093fa8863919f8f0720715abe6e4f3683cf0a9984c042ff7a473571e68cc4`,
  reflecting the pre-edit acceptance archive content the
  audit ran against — drafter arbitration occurs in the
  acceptance archive only, not the audit JSON).
- **RAG-replay audit archives (D4):** sealed, untouched.
  Three RAG-enriched dispositions plus the rag-vs-non-rag
  comparison artifact. Drafter arbitration recorded in this
  close note + acceptance archive D4 evidence; replay JSONs
  themselves are not amended.
- **Carry-forwards file:** updated in this turn. Two new
  entries appended (F-0.2.17-W3-001, F-0.2.17-W3-002).
  Permissive (cross-iteration convention) count: 36 → 38.
  F-0.2.17-W2-006 status update is in this close note's
  prose; the W2-era entry body is unchanged. File update is
  **complete** pending operator review of this close note.
- **W4 launch gate:** blocked on operator signature on this
  close note. workstream_complete emit (next executor
  invocation, after operator sign) advances the state machine
  to `W3_workstream_complete` but does not lift the W4 launch
  gate by itself; the W4 plan-doc + W4 executor prompt
  refresh (to fold in F-0.2.17-W3-001 as the sixth deliverable)
  is a drafter (claude-web) deliverable that follows operator
  sign.
- **W4 plan-doc refresh:** deferred to chat after operator
  signs and this close note lands. Chat-first discipline
  holds; no W4 launch artifact edits drafted in this turn.
  The deterministic-post-hoc-filter scope from F-0.2.17-W3-001
  is plan-doc input, not a plan-doc draft.

## Pillar 11 invariant cross-check

- **Drafter (claude-web):** zero git operations. Plan-doc
  authoring (W3 plan-doc was authored pre-session), drafter-
  arbitration prose, and close-note authoring is artifact-only.
- **Executor (Claude Code):** zero git operations.
  `pillar_11_invariant_check` in `acceptance/W3.json` reads
  `result: "pass"` with evidence: no git/gh/push/commit/PR/merge
  primitive invoked across the executor session; all writes
  targeted `src/aho/council/` (audit.py modify;
  audit_ref_extract.py + audit_ref_lookup.py new),
  `src/aho/audit_disposition_emitter.py` (modify, pass-through
  for `rag_enrichment`), `artifacts/iterations/0.2.17/probes/`
  (W3_audit_replay_rag.py new), `artifacts/iterations/0.2.17/
  audit/replay/` (4 new JSON outputs),
  `artifacts/iterations/0.2.17/acceptance/W3.json` — no `.git/`,
  no `~/.config/`, no `/etc/`, no `.ssh/` writes;
  F-0.2.17-W1-003 token rotation explicitly NOT performed
  (surfaced as continuing reminder under `outstanding_pre_03x_
  gates`).
- **Auditor (llama3.2:3b in-container, RAG-enriched):** zero
  git operations. In-container model has no shell, no
  filesystem write capability outside the audit primitive's
  controlled emitter path. Audit archive itself is JSON-only
  — no executable artifacts. The RAG retrieval step
  (`aho.council.audit_ref_lookup`) reads the host-mounted
  ChromaDB collection only; no git tree access.
- **Self-audit AUDIT-PILLAR11 finding clarification:** the
  `git-add`/`git-commit`/`git-push` tokens that triggered the
  structural pre-check appear inside the
  `pillar_11_invariant_check.evidence` field as the literal
  list of primitives the executor did NOT invoke. The pre-
  check regex is conservative-by-design (flag for human review
  rather than auto-fail); the human review (this close note)
  confirms the tokens are descriptive prose attesting Pillar
  11 compliance, not actual invocations.

## Operator sign-off

Signed by:
Date:
Disposition acknowledged:
D5 self-audit drafter arbitration acknowledged:
F-0.2.17-W2-006 partial-closure decision acknowledged (stays OPEN; closes via W4 path c):
Carry-forwards acknowledged: F-0.2.17-W3-001, F-0.2.17-W3-002
Pre-0.3.x hard gate (continuing): rotate ahomw:telegram_bot_token (F-0.2.17-W1-003)
Auditor-seat-transition continuation acknowledged:
W4 plan-doc refresh acknowledged (drafter to fold F-0.2.17-W3-001 as sixth W4 deliverable):
W4 launch gate:

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-03T15:30:14Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit halt)
Materiality thesis result: partial validation (architecture works in principle; small-model prompt-following inconsistency at base tier; deterministic post-hoc filter selected for W4 structural fix)
F-0.2.17-W2-006 disposition: stays OPEN; F-0.2.17-W3-001 inherits as more specific surface; closes via W4 deterministic filter
Carry-forwards acknowledged: F-0.2.17-W3-001, F-0.2.17-W3-002
Pre-0.3.x hard gate: rotate ahomw:telegram_bot_token (F-0.2.17-W1-003 remediation) — surfaced at W3 close per recurring protocol
W4 launch gate: lifted (W4 plan doc refresh required to add deterministic post-hoc filter as new D1)
