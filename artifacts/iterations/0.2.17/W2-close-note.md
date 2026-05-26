# 0.2.17 W2 close note

**Disposition:** pass_with_findings (drafter-arbitrated from llama
self-audit `surface_to_drafter`).

W2 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W2.json`.
W2 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W2.json` with
`disposition: "surface_to_drafter"`. Drafter (claude-web)
arbitrated the surfaced finding to "auditor-capability gap, not
W2-substance defect" and consolidated it with the W0 replay
disagreement into F-0.2.17-W2-006. Sealed shas (verified at
close-note authoring time):

- acceptance archive sha256:
  `4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`
- audit archive sha256 (UNTOUCHED, llama's verbatim disposition):
  `b9c2f1bb5ef4b4af4b0670ef8f84440ccef0a6dbed7be70a160bb031a886ab22`
- audit/replay/W0-llama.json sha256:
  `46ba8fc325c25b1f1d5e3f87a498af7ad1fe39ca0e83819c9fade5857c4b8aeb`
- audit/replay/W0-comparison.json sha256:
  `9d98ce420ce4401d2fe7a120f84281ddef5eacdd4be04f529b9fec0674644dc9`
- audit/replay/W1-llama.json sha256:
  `a6a1267f7ad79a6838e3b34cbf973ad043a0c7753fb6724dd8ae71f1831bd7ee`
- audit/replay/W1-comparison.json sha256:
  `b3aee2a487298101deee95beaeeda09f47a52e34a59da0580414f4bbdf88aaa7`

Audit archive (`audit/W2.json`) is UNTOUCHED post-emit. The
disposition field reads `surface_to_drafter`; drafter arbitration
is recorded only in the acceptance archive's D9 / D11 evidence
sections and in the close-note section below. Per Adversarial
Authorship sealed-archive convention, audit archives are not
amended after emit - corrections and arbitrations land in
acceptance evidence and close-note prose, never in the audit JSON.

## D9 / D10 / D11 disposition section

Three audit-replay / self-audit dispositions, each requiring
drafter arbitration.

- **D9 - W0 audit replay (llama vs Gemini sealed audit/W0.json).**
  Llama disposition: `halt` at confidence 0.99, one finding plus
  a novel finding ("F-W0-004 not corroborated"). Gemini sealed
  disposition: `pass_with_findings` (3 findings AF001–AF003).
  Topical overlap: llama's primary finding overlaps with
  Gemini's AF003 via keywords [0007, deferral, passthrough] -
  same B2.3 GPU passthrough deferral that Gemini sealed as
  acceptable per ADR 0007 amendment (hybrid mode is the planned
  workaround). Drafter arbitration: stylistic disagreement
  (severity inflation on B2.3 deferral overlap) plus a novel
  false-positive on F-W0-004 (an ID that IS sealed and
  registered in the 0.2.16 W4 surface). Both axes consolidated
  with D11 finding as F-0.2.17-W2-006 - the auditor
  reference-resolution gap is the root cause of both
  disagreements; W3 closes the gap. No invalidation of the
  sealed Gemini W0 disposition; Gemini's `pass_with_findings`
  stands.

- **D10 - W1 audit replay (llama vs Gemini sealed audit/W1.json).**
  Llama disposition: `surface_to_drafter` at confidence 0.99,
  one finding citing F-0.2.17-W1-003 (the sealed Pillar 11
  incident). Gemini sealed disposition: `pass_with_findings`
  (3 findings AF-0.2.17-W1-001 through 003). Topical overlap:
  llama's finding overlaps with Gemini's AF-0.2.17-W1-001 via
  keywords [secrets, stdout, test] - same Pillar 11 friction
  event. Disposition axis agrees (`surface_to_drafter` ↔
  `pass_with_findings`). Drafter arbitration: framing
  difference only - Gemini uses architectural framing ("Pillar
  11 friction"), llama uses symptom-level description ("aho
  secrets-test prints decrypted value to stdout"). Same
  finding, different vocabulary. Stylistic. No new
  carry-forward; no invalidation of sealed disposition.

- **D11 - W2 self-audit (llama against the W2 acceptance
  archive itself).** Llama disposition:
  `surface_to_drafter` at confidence 0.90, one finding flagging
  the reference to F-0.2.17-W1-003 in the W2 acceptance archive
  as "the ID does not look real (matches naming conventions)" at
  severity critical. F-0.2.17-W1-003 is in fact the sealed
  Pillar 11 ID from W1 close - referenced multiple times across
  acceptance, audit, and carry-forwards artifacts. Drafter
  arbitration: false-positive on small-model ID-validation
  reasoning. Llama at audit time has no tool-access to the
  carry-forwards registry, ADR set, or gotcha state, and
  pattern-matches reference IDs by syntax in isolation.
  Consolidated with D9 novel finding as F-0.2.17-W2-006. The
  pattern is: D9 W0 replay flagged F-W0-004 as not corroborated
  (false positive - F-W0-004 is real, registered in 0.2.16 W4);
  D11 self-audit flagged F-0.2.17-W1-003 as not real-looking
  (false positive - same ID is sealed in W1 audit chain). Same
  root cause. **W2 closes pass_with_findings - the
  auditor-capability gap is W3 work, not a W2-substance
  defect.** The gap-net activated as designed; the disposition
  surfaced to drafter exactly as the architecture specifies.

Drafter consolidation note: F-0.2.17-W2-004 (W0 stylistic
disagreement) and F-0.2.17-W2-005 (D11 false-positive) were
removed from the acceptance archive's `carry_forwards_added`
list and replaced with the single consolidated entry
F-0.2.17-W2-006 above. The consolidation reflects that both
findings have the same root cause (auditor reference-resolution
without registry access) and a single W3 fix closes both.

## Carry-forwards section

Four new W2 carry-forwards appended to
`artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`. Full
entry text mirrors the W2.json `carry_forwards_added` field and
matches the canonical bullet shape used by F-0.2.17-W0-001
through F-0.2.17-W1-003 in the same file.

- **F-0.2.17-W2-001 - ChromaDB host-side dev fallback path
  documentation.** Severity: info. Source: 0.2.17 W2 D1
  implementation experience. Summary: "AHO_CHROMA_DIR defaults
  to /var/lib/aho/chroma; on hosts without operator-side sudo to
  create /var/lib/aho, the rag layer falls back to
  ~/.local/share/aho/chroma. This is correct behavior for
  hybrid host/container dev but is not yet documented in ADR
  0007." Disposition: "Document the fallback in ADR 0007
  amendment at W4 retrospective. No code change needed." Target:
  0.2.17 W4.

- **F-0.2.17-W2-002 - nomic-embed-text context-length cap
  surfaces as HTTP 400.** Severity: info. Source: 0.2.17 W2 D1
  implementation experience. Summary: "nomic-embed-text in
  Ollama 0.20 returns HTTP 400 'the input length exceeds the
  context length' above ~7000 chars for whitespace-heavy text
  and ~5000 for dense JSON. RAG layer chunks at 4000 chars with
  500-char overlap to stay well under both limits."
  Disposition: "Documented in src/aho/rag/__init__.py
  docstring; future fine-grained chunking work is W3+ scope."
  Target: 0.3.x.

- **F-0.2.17-W2-003 - Llama3.2:3b mirrors source-artifact
  severity vocabulary.** Severity: info. Source: 0.2.17 W2 D10
  W1 replay run. Summary: "Llama3.2:3b prefers severity
  vocabulary present in the audit target (e.g. 'moderate' from
  W1 carry-forward entries) over enum strings in the prompt.
  Required adding an explicit, exhaustive severity-synonym
  table to aho.council.audit. Unknown severity strings still
  raise (G083 preserved)." Mechanism: "Small-model token-mimicry
  of source-artifact vocabulary under format=json constraint."
  Disposition: "Synonym table is documented and exhaustive in
  src/aho/council/audit.py SEVERITY_SYNONYMS. No further
  action. If a future audit target uses a severity word outside
  the synonym set, that's a real schema gap to surface."
  Target: 0.3.x.

- **F-0.2.17-W2-006 - Auditor reference-resolution gap (llama
  systematically flags carry-forward / ADR / gotcha IDs as
  "not real-looking" without registry access at audit time).**
  Severity: important. Source: 0.2.17 W2 D9 (W0 replay) + D11
  (W2 self-audit). Summary: "D9 produced novel false-positive
  finding ('F-W0-004 not corroborated'). D11 self-audit
  produced false-positive finding ('F-0.2.17-W1-003 does not
  look real'). Both IDs are in fact sealed and registered."
  Mechanism: "Llama at 32K context cannot fit full carry-forwards
  file + ADRs + gotcha registry alongside audit target. Without
  RAG-mediated retrieval, the auditor pattern-matches ID syntax
  and concludes 'looks like placeholder.'" Disposition: "W3
  must wire aho.rag.query into aho.council.audit prompt
  construction. Auditor retrieves 'is this ID registered?' via
  ChromaDB query before flagging reference-resolution issues.
  This is the RAG-as-context-feed for auditor seat from
  architecture artifact §Component decomposition (aho.rag feeds
  context to triage and audit)." Target: 0.2.17 W3 - RAG-audit
  integration during materiality / claw3d work. Audit
  traceability: surfaced in W2 self-audit disposition
  (`audit/W2.json` sha `b9c2f1bb…`); documented in this close
  note as drafter arbitration of D9 / D11 findings.

The carry-forwards file update is **complete in this turn** -
all four entries appended via `aho.gap_carry_forward_writer`
(D7) before close-note authoring, since the W2 plan executor
runs both the writer and this prose. Operator review of the
file update lands at the same chat turn as operator review of
this close note.

## Coherence summary

- W1 close-state baseline: 32 total in
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
  (per W1 close note, using the cross-iteration tracking
  convention).
- W2 close adds 4 new entries (F-0.2.17-W2-001, -002, -003,
  -006) → **36 total** post-update (cross-iteration tracking
  convention via permissive header regex).
- Strict-header tracker (the `aho.gap_carry_forward_writer`
  regex `^- \*\*[A-Za-z0-9.\-_/]+ - `): 25 → **29** post-update.
  The +4 delta is consistent across both conventions; the
  baseline drift between conventions (28-vs-25 and 32-vs-29)
  reflects multi-word IDs in older entries that the strict
  regex skips. Drift is documented here for future-iteration
  traceability; no action required on existing entries.
- Acceptance archive's `carry_forwards_added` field lists
  exactly four entries (F-0.2.17-W2-001, -002, -003, -006);
  matches the file-side append count of +4.
- Audit archive itself is not amended; the count walk is
  recorded here in the close note rather than as an archive
  amendment, preserving the audit's sealed state.

## Auditor seat transition section

W2 is the **first iteration in which `audit/{workstream}.json`
is produced by an in-container auditor (`llama3.2:3b`) rather
than by an external Adversarial Authorship reviewer.** Gemini
CLI exited the audit chain at W1 close; from W2 forward, llama
is the structural spot-checker and drafter (claude-web) is the
architectural-judgment gap-net. This is the load-bearing
"Adversarial Authorship at base-tier" thesis test from the
W2 plan-doc.

**The thesis held.** The bootstrap pattern across D9 / D10 /
D11 was: llama produced structurally valid dispositions on
real archives, surfaced findings (some real-overlap, some
false-positive), and routed to drafter via the
`surface_to_drafter` disposition exactly as designed. The
drafter (in this chat turn) reviewed, identified the
auditor-capability gap, and consolidated the gap into a single
carry-forward (F-0.2.17-W2-006) with a concrete W3 fix.

**The thesis surfaced its own gap.** The drafter-arbitrated
F-0.2.17-W2-006 captures the lesson: small-model auditor at
base tier cannot reason about registered identifiers without a
registry handle. The W2 architecture explicitly anticipated
this - `aho.rag.query` exists as the substrate primitive (D1).
W3 wires it into the auditor prompt-construction path. The
W2-to-W3 handoff is therefore: substrate exists (W2 D1 RAG +
138 chunks of indexed iteration context), wire-up pending (W3
audit-RAG integration). After W3, llama's structural
spot-check has registry-resolution support and the
reference-resolution false positives go away.

**Drafter sign-off on the thesis test.** From a drafter
(claude-web) perspective: the Adversarial Authorship at
base-tier protocol works as the architecture specifies. The
gap-net activates exactly when the architecture says it
should - when the auditor surfaces something it cannot
fully resolve, the drafter arbitrates with the broader
context the auditor lacks. This is the design intent of the
two-tier structural-vs-architectural separation, not a
failure mode.

## Pre-0.3.x hard gate (continuing reminder)

**Token rotation pre-0.3.x as a hard gate.** Operator (Kyle)
must rotate `ahomw:telegram_bot_token` before any 0.3.x work
begins. The 0.3.x launch gate cannot lift while the exposed
token (from W1's F-0.2.17-W1-003 incident) remains valid.
F-0.2.17-W1-003 carries this as the explicit operator-side
outstanding action.

This reminder is surfaced at every iteration close until the
rotation completes. Per the W2 executor prompt: surface at W2
close (this note), surface at W3 close, surface at W4 close,
surface before tsP3 handoff. Executor is not authorized to
rotate tokens; this is operator-only.

Status check at W2 close:
- W1 close acknowledged the gate (operator sign-off line
  `Pre-0.3.x hard gate: rotate ahomw:telegram_bot_token`).
- Rotation status as of W2 close-note authoring:
  **operator_action_pending**.
- Outstanding pre-0.3.x gates: F-0.2.17-W1-003 (token
  rotation), F-0.2.17-W1-001 (secrets-test subcommand still in
  rc1 image - folded into W4 retrospective per W1 close).

## State at close

- **Acceptance archive:** sealed,
  `audit_status: "pending_drafter_review"` at close-note
  authoring time. Drafter has reviewed (this turn) and
  consolidated D9 / D11 findings; status holds at
  `pending_drafter_review` until operator signs this close note.
  sha256
  `4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`.
- **Audit archive:** sealed, untouched post-emit. sha256
  `b9c2f1bb5ef4b4af4b0670ef8f84440ccef0a6dbed7be70a160bb031a886ab22`.
- **Replay audit archives (D9, D10):** sealed, untouched.
  Drafter arbitration recorded in the acceptance archive +
  this close note; replay JSONs themselves are not amended.
- **Carry-forwards file:** updated in this turn. Four new
  entries appended (F-0.2.17-W2-001, -002, -003, -006).
  Strict-regex post-update count: 29; permissive (cross-
  iteration convention) count: 36. File update is **complete**
  pending operator review of this close note.
- **W3 launch gate:** blocked on operator signature on this
  close note. workstream_complete emit (next executor
  invocation, after operator sign) advances the state machine
  to `W2_workstream_complete` but does not lift the W3 launch
  gate by itself; the W3 plan-doc + W3 executor prompt are
  drafter (claude-web) deliverables that follow operator sign.
- **W3 design + plan refinement:** deferred to chat after
  operator signs and this close note lands. Chat-first
  discipline holds; no W3 launch artifacts drafted in this
  turn. The auditor-RAG integration scope from F-0.2.17-W2-006
  is plan-doc input, not a plan-doc draft.

## Pillar 11 invariant cross-check

- **Drafter (claude-web):** zero git operations. Plan-doc,
  executor-prompt, drafter-arbitration prose, and close-note
  authoring is artifact-only.
- **Executor (Claude Code):** zero git operations.
  `pillar_11_invariant_check` in `acceptance/W2.json` reads
  `result: "pass"` with evidence: no git/gh/push/commit/PR/merge
  primitive invoked across the executor session; all writes
  targeted `src/aho/`, `artifacts/iterations/0.2.17/`,
  `artifacts/tests/` - no `.git/`, no `~/.config/`, no `/etc/`,
  no `.ssh/` writes; F-0.2.17-W1-003 token rotation explicitly
  NOT performed (surfaced as continuing reminder under
  `outstanding_pre_03x_gates`).
- **Auditor (llama3.2:3b in-container):** zero git operations.
  In-container model has no shell, no filesystem write
  capability outside the audit primitive's controlled emitter
  path. Audit archive itself is JSON-only - no executable
  artifacts.
- **Materiality counters:** four counters emit correctly
  (D12 verification probe). `caught_by_llama` increments per
  finding inside `aho.council.audit`; `caught_by_drafter`
  increments per appended carry-forward in
  `aho.gap_carry_forward_writer`; `escaped` and
  `carry_forward_resolution_rate` are placeholder bumps W3
  wires to real-flow integration.

## Operator sign-off

Signed by:
Date:
Disposition acknowledged:
D9/D10/D11 drafter arbitration acknowledged:
Carry-forwards acknowledged: F-0.2.17-W2-001, F-0.2.17-W2-002, F-0.2.17-W2-003, F-0.2.17-W2-006
Pre-0.3.x hard gate (continuing): rotate ahomw:telegram_bot_token (F-0.2.17-W1-003)
Auditor-seat-transition acknowledged:
W3 launch gate:

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-03T14:04:46Z
Disposition acknowledged: pass_with_findings (drafter-arbitrated from llama self-audit surface_to_drafter)
Auditor-seat transition acknowledged: Gemini exited W1 close; llama3.2 first deployment in W2; capability gap captured as F-0.2.17-W2-006, W3 fix
Carry-forwards acknowledged: F-0.2.17-W2-001, F-0.2.17-W2-002, F-0.2.17-W2-003, F-0.2.17-W2-006
Pre-0.3.x hard gate: rotate ahomw:telegram_bot_token (F-0.2.17-W1-003 remediation) - surfaced at W2 close per recurring protocol
W3 launch gate: lifted
