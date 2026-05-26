# 0.2.17 W1 close note

**Disposition:** pass_with_findings.

W1 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W1.json`.
W1 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W1.json` with
`audit_result: "pass_with_findings"`. Sealed shas (verified at
close-note authoring time):

- acceptance archive sha256:
  `e4d076eec6c1e703635e9befb98bc46c7bf171c7fec3a4c3f64161ec60725a6e`
- audit archive sha256:
  `8b2771acd0c8cab833ee35f6be957b31f25e6255c9eb40fe055e6f92c75862ab`

Both archives are sealed and untouched by this close note. The
audit archive's `count_coherence_check` field reads "clean: 3
carry-forwards added (F-0.2.17-W1-001, 002, 003), all documented
in W1.json"; that internal claim is reconciled against the actual
file-line count in the Coherence summary section below.

## Audit findings

Three findings dispositioned in `audit/W1.json`. Gemini's summary
text is reproduced verbatim per finding so this close note is
internally complete without requiring read-through to the audit
archive.

- **AF-0.2.17-W1-001 (important) - Pillar 11 Incident Judgment
  (F-0.2.17-W1-003).** Status: `remediation_pending_operator`.
  Gemini summary verbatim: "The exposure of a Telegram bot token
  to the agent's stdout is a genuine Pillar 11 friction event.
  However, the executor's (Claude Code) transparent reporting and
  documentation of the incident as F-0.2.17-W1-003 demonstrates
  adherence to the Adversarial Authorship protocol. The
  remediation (rotating the token and redesigning secrets-test
  for hash/length comparison) is necessary and sufficient for W1
  closure. Mark as pass_with_findings." Disposition: accepted as
  pass_with_findings. Token-rotation operator-side action
  carried forward as a pre-0.3.x hard gate (see Pillar 11
  incident summary section below). secrets-test redesign for
  hash-fingerprint comparison scheduled for W2 (per
  F-0.2.17-W1-003 remediation field). No edits to acceptance or
  audit archive.

- **AF-0.2.17-W1-002 (info) - Subcommand Leakage
  (F-0.2.17-W1-001).** Status: `carry_forward`. Gemini summary
  verbatim: "Leaving 'secrets-test' in the rc1 image contradicts
  the plan-doc ideal but is acceptable for a release candidate.
  Must be removed before final promotion to avoid production-side
  secret exposure risk." Disposition: accepted. Subcommand removal
  scheduled for W4 at the latest, with W2 as the earlier
  candidate (per F-0.2.17-W1-001 remediation field; consider
  `AHO_DEV_BUILD=1` env-gating so dev images retain the
  affordance and production images do not). No edits required to
  rc1 image; rc1 stands as released.

- **AF-0.2.17-W1-003 (info) - Networking Insight
  (F-0.2.17-W1-002).** Status: `resolved`. Gemini summary
  verbatim: "The podman pasta SNAT behavior is a valuable
  discovery. The remediation (iif lo nft rules) correctly
  addresses the connectivity gap for hybrid-mode dispatches."
  Disposition: accepted. Operator-applied `iif lo` nft rule
  amendment is in place and verified (D5 evidence in
  `acceptance/W1.json`). Lesson recorded as F-0.2.17-W1-002 in
  the carry-forwards list as a deployment-doc requirement for
  ADR-0009 (secrets broker) and any future ADR-0007 firewall
  amendment.

## Carry-forwards section

Three new W1 carry-forwards to be added to
`artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` under the
"Target: 0.2.17" or "Target: 0.2.x cleanup" sections (specific
section placement to be confirmed by operator at carry-forwards
update time). Full entry text mirrors the W1.json deliverable
findings for completeness:

- **F-0.2.17-W1-001 - `aho secrets-test` test-only subcommand
  left in 0.2.17-rc1 image.** Severity: low. Source: 0.2.17 W1
  D7 (image-push acceptance gate). Title: "aho secrets-test
  test-only subcommand left in 0.2.17-rc1 image." Summary: "The
  W1 plan-doc gate 3 specified that 'aho secrets-test' is a
  test-only command that should be 'removed before image push'.
  The rc1 image was pushed with the subcommand still present.
  For an rc1 (release-candidate) tag this is acceptable, but
  the subcommand MUST be removed before any final 0.2.17 or
  0.3.x promotion." Remediation: "W4 (or earlier W2) edit:
  remove the secrets-test parser registration from
  `src/aho/cli.py` before the next image cut. Consider gating
  the subcommand behind `AHO_DEV_BUILD=1` env var so dev builds
  retain it but production images do not." Target iteration:
  0.2.17 W4 (or earlier removal).

- **F-0.2.17-W1-002 - Rootless podman pasta networking SNATs
  container→host traffic to host primary interface; firewall
  rules must be iif-scoped.** Severity: moderate. Source: 0.2.17
  W1 D5 (Ollama firewall mitigation). Title: "Rootless podman
  pasta networking SNATs container→host to host primary
  interface." Summary: "When a rootless podman container connects
  to host.containers.internal:NNNN, pasta translates the traffic
  so it arrives at the host on the lo interface with the host's
  primary IP as source. Firewall rules scoped by source-address
  ranges (127.0.0.0/8, 169.254.0.0/16) do NOT cover this path.
  Working rule pattern is interface-scoped: 'iif lo accept'."
  Remediation: "Documented in deployment notes for any future
  container-host firewall rule design. Future ADR-0009 (secrets
  broker) and any firewall-mitigation amendment to ADR-0007 must
  reference iif scoping." Target iteration: documentation lesson;
  ADR-0009 (secrets broker) and ADR-0007 amendments. Resolved
  in-iteration (D5 functional gates pass post-amendment); the
  carry-forward is the documentation-binding restatement.

- **F-0.2.17-W1-003 - `secrets-test` subcommand exposes decrypted
  value to agent (Pillar 11 friction).** Severity: moderate.
  Source: 0.2.17 W1 D3 Gate 1 (host+container broker round-trip).
  Title: "secrets-test command exposes decrypted secret value to
  caller (Pillar 11 friction)." Summary: "The 'aho secrets-test'
  subcommand prints the decrypted value to stdout to verify
  broker round-trip equivalence with direct host-side
  get_secret(). The plan-doc design assumed this exposure was
  acceptable for W1 acceptance; in practice, executing this gate
  caused the agent (executor) to read a Telegram bot token,
  contradicting CLAUDE.md hard rule 'No reading secrets'.
  Combined with F-0.2.17-W1-001 (subcommand baked into rc1
  image), the redesign for W2/W3 should: (a) remove the test-only
  subcommand from the production image entirely; (b) replace
  value-comparison gate with hash-fingerprint or length-only
  verification." Remediation: "Operator should rotate
  ahomw:telegram_bot_token. W2 acceptance gates should not
  surface raw secret values." Target iteration: 0.2.17 W2 or W3
  (broker test redesign). **Operator-side remediation outstanding
  (token rotation) is explicitly carried forward as a pre-0.3.x
  hard gate** - see Pillar 11 incident summary section below.

The actual append to
`artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` is
deferred until this close note is reviewed by the operator (next
chat turn), per the explicit instruction in the executor prompt
to halt and surface after authoring. The three entries above are
in close-note prose form; the carry-forwards file update will
adopt the canonical bullet shape used by F-0.2.17-W0-001 through
F-0.2.17-W0-005 in the same file.

## Coherence summary

- W0 close-state baseline: 22 baseline (from
  retrospective-0.2.16) + 7 W0-new entries (F-0.2.17-W0-001,
  -002, -003, -004, -005, F-host-001, F-host-002) = **29 total**
  in `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` at
  the end of W0 close.
- W1 close adds 3 new entries (F-0.2.17-W1-001, F-0.2.17-W1-002,
  F-0.2.17-W1-003) → **32 total** post-update.
- Audit archive's `count_coherence_check` reads "clean: 3
  carry-forwards added (F-0.2.17-W1-001, 002, 003), all
  documented in W1.json" - internally consistent with the count
  walk above.
- Reconciliation against the file's actual line count is pending
  the carry-forwards file update; current pre-update line count
  is 661. The post-update count walk (29 → 32) will be
  re-verified at file-update time before operator sign-off.
- The audit archive itself is not amended; the count walk is
  recorded here in the close note rather than as an archive
  amendment, preserving the audit's sealed state.

## Pillar 11 incident summary

**Incident:** F-0.2.17-W1-003. The `aho secrets-test` subcommand,
exercised at D3 Gate 1 (host+container broker round-trip
acceptance gate), printed the decrypted value of
`ahomw:telegram_bot_token` to the executor's Bash stdout. The
executor (Claude Code) read the token's bytes via tool output -
a direct contradiction of CLAUDE.md hard rule "No reading
secrets."

**Drafter-side design responsibility.** The W1 plan-doc
(`artifacts/iterations/0.2.17/W1-plan-doc.md` line 63) specified:
"`aho host run-container -- aho secrets-test ahomw
telegram_bot_token` (test-only command, removed before image
push) returns the same value that `get_secret("ahomw",
"telegram_bot_token")` returns when called directly on the host."
That specification - raw-value return for a value-equality gate -
**was wrong on Pillar 11 grounds**. The acceptance gate it
described could not be exercised by an agent without the agent
reading the secret. Drafter-side error; documented here as a
plan-doc design flaw, not an executor implementation flaw.

**Executor surfaced voluntarily.** The executor (Claude Code)
recorded the incident as F-0.2.17-W1-003 in the acceptance
archive at write time, called out the contradiction with CLAUDE.md
explicitly, and recommended operator-side rotation of
`ahomw:telegram_bot_token`. Adversarial Authorship protocol
working as designed: the executor's transparent self-reporting is
what allowed the auditor to disposition the incident as
pass_with_findings rather than fail. Gemini's AF-0.2.17-W1-001
summary explicitly credits this behavior.

**Remediation path.**
1. **Token rotation pre-0.3.x as a hard gate.** Operator
   (Kyle) rotates `ahomw:telegram_bot_token` before any 0.3.x
   work begins. The 0.3.x launch gate cannot lift while the
   exposed token remains valid. F-0.2.17-W1-003 carries this as
   the explicit operator-side outstanding action.
2. **Secrets-test redesign in W2** for hash-fingerprint or
   length-only comparison. The new gate must verify broker
   round-trip equivalence without surfacing the decrypted value
   to either the calling process's stdout or any artifact path
   touched by an agent. Candidate designs: SHA-256 fingerprint
   comparison (host computes hash and broker also returns the
   same hash); length+prefix comparison (broker returns
   `{length: N, prefix: "abc..."}` while value-equality is
   computed by the broker against the direct host-side
   `get_secret()` result and the boolean result is what crosses
   the socket boundary). Final design pinned in W2 plan-doc.
3. **Subcommand removal** scheduled by F-0.2.17-W1-001 (W4 at
   the latest, W2 as earlier candidate, with `AHO_DEV_BUILD=1`
   env-gating as a possible middle ground).

The combination of (1) operator rotation + (2) W2 redesign + (3)
subcommand removal closes the incident category, not just the
single-token instance.

## W2 auditor-shape note (forward-looking)

Gemini's W1 audit archive surfaces an observability asymmetry
explicitly under `otel_spot_checks`: "Gemini CLI has no OTLP
export capability. Auditor verification of OTEL signals relies
on inspecting 'W1.json' evidence and source code calls to
'_emit_tier_span' and 'emit_stub_span'." For W1 this was
acceptable - council components ship as stubs that emit
attribute-only spans, and the audit could verify the call sites
in source. For W2, council components emit real OTEL signals
(real producer/auditor work, real triage classification, real
embed roundtrips); source-code inspection alone will not be
sufficient to verify substantive trace content.

W2 audit prompt design must include either:
- **(a) Runtime-trace verification step.** The auditor runs (or
  the executor demonstrates) a representative workload and the
  resulting trace is exported to a path the auditor can inspect
  directly (e.g., `aho council demo --trace-out
  /tmp/w2-trace.json` or equivalent). The auditor verifies trace
  shape and attribute correctness against the W2 plan-doc
  contract.
- **(b) Executor-side OTEL-trace dump.** The executor produces a
  trace dump as a W2 acceptance artifact (e.g.,
  `acceptance/W2-otel-traces.json` or pointer to a Jaeger
  export), sealed at acceptance-write time. The auditor inspects
  the dump post-hoc rather than running the workload.

Recommendation: prefer (b) for archive-completeness and
sealed-evidence properties, with (a) as a backup if executor-side
trace export tooling is not yet ready. Final mechanism pinned in
the W2 plan-doc.

This is **not** a carry-forward (auditor-process concern, not
project-state concern), but is recorded here as input to W2
plan-doc design and to keep the auditor-shape evolution legible
across iterations.

## State at close

- **Acceptance archive:** sealed,
  `audit_status: "pending_audit"` at write time, now superseded
  by audit archive's `pass_with_findings`. sha256
  `e4d076eec6c1e703635e9befb98bc46c7bf171c7fec3a4c3f64161ec60725a6e`.
- **Audit archive:** sealed. sha256
  `8b2771acd0c8cab833ee35f6be957b31f25e6255c9eb40fe055e6f92c75862ab`.
- **Carry-forwards list:** update **pending operator review of
  this close note**. Three entries to be appended
  (F-0.2.17-W1-001, F-0.2.17-W1-002, F-0.2.17-W1-003) per the
  Carry-forwards section above; expected post-update total is
  32 (29 + 3 new).
- **W2 launch gate:** blocked on operator signature on this
  close note. workstream_complete emit (this turn) advances the
  state machine to `W1_workstream_complete` but does not lift
  the W2 launch gate.
- **W2 design + plan refinement:** deferred to chat after
  operator signs and the close note lands. Chat-first
  discipline holds; no W2 launch artifacts drafted in this
  turn. The W2 auditor-shape note above is plan-doc input, not
  a plan-doc draft.

## Pillar 11 invariant cross-check

- **Drafter (Claude web):** zero git operations. No commits, no
  pushes, no merges, no `git add`. Plan-doc and close-note
  authoring is artifact-only.
- **Executor (Claude Code):** zero git operations. Audit
  evidence in `acceptance/W1.json` `pillar_11_evidence`:
  `git_invocations_in_executor_session: 0`,
  `git_add_invocations: 0`, `git_commit_invocations: 0`,
  `git_push_invocations: 0`, `pr_creations: 0`,
  `merge_invocations: 0`, `git_index_modifications_attempted: 0`.
  `gh` token consumed via `gh auth token | podman login
  --password-stdin` only; never displayed; `podman logout`
  cleared credentials post-push.
- **Auditor (Gemini CLI):** zero git operations. Audit archive's
  `pillar_11_invariant_check: "pass"`.
- **Incident accurately captured.** F-0.2.17-W1-003 records the
  one Pillar 11 friction event (executor read a Telegram bot
  token via the `aho secrets-test` subcommand's stdout) with
  full disposition: voluntarily surfaced by executor, accepted
  by auditor as pass_with_findings, drafter-side design
  responsibility documented above, remediation path pinned.
- **Token rotation operator-side action:** documented as
  pre-0.3.x hard gate. The 0.3.x launch gate cannot lift while
  `ahomw:telegram_bot_token` (in its W1-exercised form) remains
  valid.

## Operator sign-off

Signed by:
Date:
Disposition acknowledged:
Carry-forwards acknowledged: F-0.2.17-W1-001, F-0.2.17-W1-002, F-0.2.17-W1-003
Token rotation pre-0.3.x hard gate acknowledged:
W2 launch gate:

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-03T04:41:29Z
Disposition acknowledged: pass_with_findings
Audit findings acknowledged: AF-0.2.17-W1-001 (Pillar 11 incident remediation pending), AF-0.2.17-W1-002 (subcommand leakage carry-forward), AF-0.2.17-W1-003 (pasta networking insight resolved)
Carry-forwards acknowledged: F-0.2.17-W1-001, F-0.2.17-W1-002, F-0.2.17-W1-003
Pre-0.3.x hard gate: rotate ahomw:telegram_bot_token (F-0.2.17-W1-003 remediation)
W2 launch gate: lifted
