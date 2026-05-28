# 0.3.1 iteration close

**Iteration:** 0.3.1
**Status:** closed (early close at W2, substrate-pivot driven)
**Authored:** 2026-05-27 (post-W2-substrate-pivot decision; W2 sealed
acceptance + audit + close-note in place at authoring time; W2
workstream_complete pending operator sign on this iteration-close gate)
**Authoring agent:** claude-code (a8cos session, out-of-band council
global-use wiring task) under drafter (claude-web) direction
**Crowns but does not duplicate:** three workstream close notes (W0,
W1, W2) and the p3cos-council-port analysis at
`artifacts/iterations/0.3.1/p3cos-council-port-analysis.md`

## Summary

0.3.1 delivered three workstreams on a8cos base tier as host-agnostic
codebase substrate. Adversarial Authorship at base tier ran across all
three workstreams with the llama3.2:3b auditor seat. The iteration
closes early at W2 by operator direction: the substrate pivot decision
documented in §Substrate pivot moves the original W3-W7 scope to 0.3.2,
where p3cos (partial tier, RTX 2000 Ada 16GB) is the execution host for
the 9B council producer/evaluator work that a8cos hardware cannot drive
to convergence.

Three workstreams ran:

- **W0** documentary substrate. Plan-doc, ADR-0011 (substrate
  freshness), ADR-0012 (Chain of Trust L5 placement), CLAUDE.md
  rewrite, carry-forward fold-in inventory.
- **W1** substrate-freshness telemetry. 13-fact `aho-probe-substrate`,
  ChromaDB bootstrap (`aho-rag-bootstrap` lifts registered_count from
  0 to 20), `install.fish` idempotency hardening with structured
  per-step output, `aho-doctor` health-check.
- **W2** observability + tenant-data substrate. Env-driven OTLP
  exporter wiring, tenant-aware Firestore writer module
  (TTEOS / notjustavar / customer-codename pattern), `install.fish`
  tier-aware refactor (tier auto-detect at install time), alert
  bridge scaffolding, 14-fact telemetry.

All three closed `pass_with_findings`. All three were operator-signed
at their respective workstream close (W0 and W1 confirmed in the event
log via `workstream_complete` emits; W2 sealed and pending operator
sign at this iteration-close authoring time - see §State at close).

## Three-workstream summary

| WS | Title | Disposition | acceptance sha256 | audit sha256 | close note sha256 | workstream_complete (UTC) |
|---|---|---|---|---|---|---|
| W0 | Plan-doc + ADR-0011/0012 placement + CLAUDE.md rewrite + carry-forward fold-in + W0 self-audit | pass_with_findings | `ab374979...` | `9749cfed...` | `569187af...` | 2026-05-24T12:47:57Z |
| W1 | Substrate-freshness telemetry + ChromaDB bootstrap + install.fish idempotency + aho-doctor (registered_count 0->20) | pass_with_findings | `76047d77...` | `3a2c456d...` | `d4858fb5...` | 2026-05-25T15:27:58Z |
| W2 | Env-driven OTLP + tenant-aware Firestore writer + install.fish tier-aware refactor + alert bridge | pass_with_findings | `f213db07...` | `1d98fa0d...` | `1715b376...` | 2026-05-28T05:09:04Z |

Full sha256 values in §Sealed-archive inventory. Per-workstream details,
evidence, and findings live in the respective close notes; this
iteration-close note crowns the chain rather than duplicating it.

## Substrate pivot

The substrate pivot driving early iteration close was surfaced
out-of-band on a8cos during council global-use wiring (a task arising
from a new global `~/.claude/CLAUDE.md` rule routing every Claude Code
session through `aho-conductor dispatch`). The wiring is host-agnostic;
the empirical finding is that the **hardware ceiling on a8cos blocks
the 9B council producer (qwen3.5:9b)** from driving to convergence on
the conductor's actual workstream prompt.

### Three-run evidence

All three runs from `/tmp` (outside the repo), models pulled into host
Ollama, router prefix-near-miss fix and advisory-routing fallback in
place:

| # | Substrate budget | Outcome | Time | Failure mode |
|---|------------------|---------|------|--------------|
| 1 | qwen num_ctx 16384, GLM modelfile default (65K), cold load | TIMEOUT | 900s ceiling hit | Outer `timeout` killed the run; stdout buffered + lost on kill |
| 2 | qwen num_ctx 4096 + GLM num_ctx 4096 (tier-aware tuning applied) | FAIL exit 1 | 15m36s | `DegenerateGenerationError: Thinking repetition detected at token 2650, 924s elapsed`. Uncaught -> traceback |
| 3 | qwen num_ctx 4096 + GLM num_ctx 4096 + tier-gated `/no_think` prefix + `_COUNCIL_ERRORS` catches | FAIL exit 1 | 13m38s | `DegenerateGenerationError: Thinking repetition detected at token 2500, 808s elapsed`. Clean one-line via new exception handling. `/no_think` directive ignored by this Ollama qwen3.5:9b variant |

### Per-stage warm probe (isolation)

Each stage measured in isolation on warm models, short prompt,
num_ctx 4096:

| Stage | Model | Time | Output |
|-------|-------|------|--------|
| route | nemotron-mini:4b | 3.5s | `'reviewer'` (correct after router prefix-match fix) |
| produce | qwen3.5:9b | 110.0s | `'This is my one-sentence confirmation.'` (correct) |
| assess | GLM-4.6V-Flash-9B | 64.8s | `'{"score": 8, "recommendation": "approve", "issues": []}'` (correct) |

Total warm = ~178s. Each model loads and produces correct, parseable
output on toy prompts. The functional wiring is correct. The producer
falls over only when given the conductor's real workstream prompt
because qwen3.5 engages thinking mode and the CPU + iGPU substrate
cannot drive it to convergence before QwenClient's thinking-repetition
detector fires.

### Architectural conclusion

a8cos: AMD Ryzen 9 8945HS, Radeon 780M iGPU. `~/.config/aho/tier.json`
reports `tier=base, vram_gb=0`. Ollama runs all inference on CPU. A 9B
parameter model on CPU runs at roughly 3 tokens/second on this class of
silicon. qwen3.5 with thinking mode wants to emit 1000-3000 thinking
tokens before producer output; the elapsed time gives it enough
wall-clock to drift into repetition before convergence. `/no_think` is
documented in `dispatcher.py` `MODEL_FAMILY_CONFIG["qwen"]` and
`artifacts/council-models-0.2.14.md` as a contingency lever; this
Ollama community build does not honor it.

The hardware is the limit, not the wiring. Two architectural
conclusions follow, both folded into CLAUDE.md as a new carry-forward
under "Arising in 0.3.1 (architectural, severity: important; fold into
ADR-0007 W6 three-axis amendment)":

1. **Base-tier hosts (a8cos, x9cos) are orchestrators + llama3.2:3b
   auditor seat only.** Producer/evaluator work does not run on
   CPU-only base-tier hardware.
2. **Partial-tier hosts (p3cos, RTX 2000 Ada 16GB) are council
   producer/evaluator.** qwen3.5:9b + GLM-4.6V-Flash-9B execute on GPU
   where the model class is viable.

This makes VRAM-tier and council-role-tier two independent axes - the
ADR-0007 W6 three-axis amendment the carry-forward points to. 0.3.2
executes the partial-tier deployment + council port + the W3-W7 work
that did not run in 0.3.1.

Full evidence, scope, code-change inventory, transport decision, risk
register, and acceptance criteria for the p3cos port are in
`artifacts/iterations/0.3.1/p3cos-council-port-analysis.md` (sha in
§Sealed-archive inventory).

## Carry-forwards state at iteration close

### Closed in 0.3.1

- **F-0.2.18-W1-004** - stale tailnet FQDN baked into image. Closed
  via W1 substrate-freshness telemetry (13 facts emit
  `aho.observable.last_verified_age_seconds` OTEL gauge with per-fact
  warning thresholds; stale facts surface on dashboard).
- **F-0.2.18-W2-002** - `install.fish` tier-detection gap. Closed via
  W2 tier-aware refactor (auto-detect at install time, writes
  `~/.config/aho/tier.json` with `host_id`, `tier`, `families`,
  `bundle`, `vram_gb`, `rationale`).
- **F-0.2.18-W2-003** - `aho.council.dispatch` tier-routing missing.
  Closed via W2 tier-aware refactor (dispatch reads tier.json and
  routes audit calls accordingly).
- **F-0.2.18-W2-004** - per-host broker as systemd user unit. Closed
  via W2 substrate work (broker installed from
  `templates/systemd/aho-secrets-broker.service.template` like the
  other daemons; linger on; survives reboot).
- **F-0.3.1-W0-001** - drafter substrate-prerequisite gap. Closed
  inside W0 by drafter-arbitrated repair to plan-doc + CLAUDE.md.
- **F-0.3.1-W0-002** - ChromaDB collection empty post-install.
  Closed via W1 D8 `aho-rag-bootstrap` (lifts registered_count from
  0 to 20, structurally verified).
- **F-0.3.1-W0-004** - install.fish idempotency gap. Closed via W1
  structured per-step output + idempotency hardening.
- **F-0.3.1-W0-005** - tier.json schema gap. Closed via W2 tier-aware
  refactor writing the canonical shape.

### Code-closed but Track-B-gated

Operational closure pending operator-side provisioning (notjustavar
Firestore + Beacon convergence):

- **F-0.3.1-W0-003** - OTLP endpoint migration to Beacon. Code landed
  in W2 (env-driven OTLP exporter; reads
  `OTEL_EXPORTER_OTLP_ENDPOINT` per SDK standard with a localhost
  fallback). Operational closure awaits davidk surfacing the Beacon
  endpoint + token; once those are supplied, no aho-side code change
  is required to flip over. Outbound (aho -> Beacon) is ready to flow
  the moment the env values land. ADR-0013 candidate "Beacon as
  canonical OTLP aggregator" lands in 0.3.2 W6.

### Carrying forward to 0.3.2

- **F-0.3.1-W1-001** - nomic-embed chunk-size cap. Cosmetic; embed
  client truncates oversized chunks rather than raising a clear
  schema-violation error. Disposition: schema-violation surface in
  0.3.2.
- **F-0.3.1-W2-001** - gcloud / JRE Firestore emulator tooling. Cosmetic;
  the W2 emulator dry-run had host-side tooling friction
  (gcloud auth + JRE availability) that the W2 writer module itself is
  not the right surface to absorb. Disposition: install.fish or a
  separate `aho-emulator-bootstrap` in 0.3.2.
- **F-0.2.18-W0-008** - narrative-lift. Audit-machinery cluster
  (carry-forward from 0.2.18; remains deferred).
- **F-0.2.17-W6-001** - audit-time RAG lookup ranking on opaque IDs.
  Audit-machinery cluster.
- **F-0.2.17-W5-001** - audit structural pre-check self-referential
  pattern. Audit-machinery cluster.
- **F-0.2.18-W2-009** - prompt-instruction echo. Audit-machinery
  cluster.

The four audit-machinery cluster entries above are
small-model-semantic-discrimination limits per CLAUDE.md "Open and
deferred to 0.3.2 audit-machinery iteration." Target: 0.3.2
audit-machinery iteration (scope-defined by W2 D8 F1 manifestation
evidence per W2 close note §Forward-looking handoffs).

## Deferred to 0.3.2

The original 0.3.1 W3-W7 scope (per 0.3.1 plan-doc + W1/W2 plan-doc
amendments) executes in 0.3.2 on p3cos, where the partial-tier
substrate makes the 9B council producer/evaluator viable:

- **W3** - p3cos partial-tier deployment + qwen3.5:9b auditor seat.
  Bare-host bring-up via `install.fish` (tier-aware refactor from
  0.3.1 W2 already produces the right `tier.json` shape for p3cos).
  Image transfer pattern, partial-tier model pull, smoke contract.
- **W4** - Firestore dry-run. First substantial Tachtech-tenant data
  write (TTEOS / notjustavar) via the W2 tenant-aware writer module.
  Schema validation against real ingest patterns.
- **W5** - repo-resident docs reframing (Chain of Trust L5 framing +
  multi-host deployment hosts + identity discipline). Mirrors 0.2.17
  W5's repo-resident pattern.
- **W6** - ADR consolidation + Pillar 10/11/12/13 amendments. Folds
  in: ADR-0007 three-axis amendment (VRAM tier + council-role tier +
  attestation tier), ADR-0013 (Beacon as canonical OTLP aggregator),
  ADR-0014 (aho multi-tenant data architecture, TTEOS / notjustavar /
  customer-codename), Pillar 10 + Pillar 11 amendments + new
  Pillars 12 + 13 as a `harness/base.md` version-bump.
- **W7** - final code-change closures + iteration-final self-audit.

The council global-use wiring done out-of-band in this session (see
§Out-of-band work) also folds into 0.3.2 - either inside W3 as a
sub-deliverable or as a new W (e.g. W3.5 "council global-use
cross-host routing"); drafter authors the plan-doc amendment.

## Out-of-band work (council global-use wiring on a8cos)

Per `artifacts/iterations/0.3.1/p3cos-council-port-analysis.md` §9.
Inventory below; nothing committed (Pillar 11). Operator commits when
the drafter folds these into the 0.3.2 plan-doc.

**Source files modified (uncommitted):**

- `src/aho/pipeline/router.py` - `_match_category` now handles
  prefix-near-miss in addition to substring. Resolves the
  "review" -> "reviewer" classifier flake. Used only by
  `nemoclaw.route`; blast radius contained.
- `src/aho/agents/conductor.py` - `dispatch()` is project-context-aware
  (cwd, `.aho.json`, git, artifact writeback to
  `<cwd>/aho-output/council-dispatch-<ts>.json`); routing is advisory
  (falls back to `assistant` on `DispatchError` instead of aborting);
  `smoke()` rewritten to assert on real pipeline output (role,
  non-empty producer, parseable score+recommendation, written
  artifact, event-log spans); `_COUNCIL_ERRORS` tuple
  (`DispatchError`, `GLMParseError`, `DegenerateGenerationError`,
  `requests.RequestException`) for clean exception handling in
  `smoke()` and `main()`.
- `src/aho/orchestrator_config.py` - added `get_host_tier()`,
  `get_tier_num_ctx()`, `get_tier_glm_ctx_override()`. Reads
  `~/.config/aho/tier.json`. Base-tier helpers; partial+ tiers
  preserve historical behavior.
- `src/aho/agents/openclaw.py` - `OpenClawSession.__init__` accepts
  `num_ctx`; defaults to tier-derived value.
- `src/aho/artifacts/glm_client.py` - `generate()` accepts `num_ctx`;
  defaults to tier-derived value (base sets 4096; partial/full leaves
  modelfile default in place).
- `src/aho/agents/roles/workstream_agent.py` - tier-gated `/no_think`
  prefix on base hosts. Empirically ineffective on this Ollama
  qwen3.5:9b variant; drafter decides at 0.3.2 W6 whether to keep or
  drop.

**Documentation added (uncommitted):**

- `docs/operations/council-global-use.md` - new operations doc. What
  runs, how it starts at login, model requirements, health-check,
  tier-aware context-window section.
- `CLAUDE.md` - new carry-forward entry "Arising in 0.3.1
  (architectural, severity: important; fold into ADR-0007 W6
  three-axis amendment)." Captures the empirical substrate-pivot
  finding.

**Substrate state changed on a8cos (no rollback needed):**

- Council models pulled into host Ollama: `qwen3.5:9b` (6.6 GB),
  `nemotron-mini:4b` (2.7 GB), `haervwe/GLM-4.6V-Flash-9B:latest`
  (8.0 GB). `llama3.2:3b` was already present. Disk impact ~17 GB;
  800+ GB still free. Drafter decides at 0.3.2 W3 close whether to
  retain on a8cos for dev / test fall-back or unpull for
  tier-purity.

Carry-forwards arising in this out-of-band work:

- The substrate-pivot architectural carry-forward (already captured
  in CLAUDE.md; see §Substrate pivot above) is the load-bearing item.
- All six source-file edits + two documentation files carry into
  0.3.2 W3 (or W3.5) for operator commit; the diffs themselves are
  the deliverable, not requiring re-derivation.

## State at close

- **W0 acceptance archive sealed and event-log-confirmed:**
  `workstream_complete` event timestamp 2026-05-24T12:47:57Z; operator
  signature 2026-05-24T12:44:34Z (W0 close note).
- **W1 acceptance archive sealed and event-log-confirmed:**
  `workstream_complete` event timestamp 2026-05-25T15:27:58Z; operator
  signature 2026-05-25T15:23:09Z (W1 close note).
- **W2 acceptance archive sealed and event-log-confirmed:**
  `workstream_complete` event timestamp 2026-05-28T05:09:04Z; operator
  signature 2026-05-28T05:08:39Z (W2 close note operator sign-off block
  appended in the same close sequence). The W2 emit was the dropped
  state-machine thread: the W2 acceptance archive sealed
  2026-05-26T15:34:46-07:00, then operator sign + `workstream_complete`
  emit were not completed at that time; both landed during the 0.3.1
  iteration-close sequence on 2026-05-28.

Checkpoint state at iteration close:
`current_workstream=W2, last_event=W2_workstream_complete, workstreams={W1: workstream_complete, W2: workstream_complete}, iteration=0.3.1`.

State-machine integrity note: the W2 `workstream_complete` emit
landed with the wrong iteration field (`0.2.18`) because the helper
sourced `_ITERATION` from `.aho.json` and that file's
`current_iteration` had not been advanced from `0.2.18` to `0.3.1`.
Two surgical corrections were applied during the close sequence:
the just-emitted event-log line's `iteration` field was rewritten
in place from `0.2.18` to `0.3.1` (timestamp and event identity
preserved); `.aho.json` `current_iteration` was advanced to
`0.3.1`. No other event-log lines were touched. This is the
F-0.3.1-W0-001-shaped substrate-prerequisite gap surfacing once
more at iteration close; capture as a 0.3.2 entry if the drafter
chooses (suggested ID: F-0.3.1-iteration-close-001, low severity,
substrate-config drift between `.aho.json` and the actual iteration
state).

Sealed-archive posture at iteration close: all six sealed JSON
archives (acceptance + audit for W0, W1, W2) are untouched.
W0 and W1 close notes are untouched. **W2 close note had an
operator sign-off block appended during this close sequence**
(per directive: the W2 close-note never received its sign block at
W2 close, was completed here); its sha advanced from
`970f105e...` (pre-sign) to `1715b376...` (post-sign). The new sha
is the one recorded in §Sealed-archive inventory below.

## Pillar 11 invariant at iteration close

Pillar 11 held across all three workstreams. Zero git operations by
drafter, executor, or auditor across W0, W1, W2 or the out-of-band
council global-use wiring. All commits operator-side. No agent read
raw secret material; the broker contract (ADR-0009) was the only
sanctioned credential path. No hardware-side actions taken by any
agent.

The out-of-band council global-use wiring (§Out-of-band work) extends
the Pillar 11 posture: code edits proposed in the working tree,
operator commits when the drafter folds them into 0.3.2 plan-doc.
The same applies to the iteration-close note itself: drafter reviews,
operator signs, no agent emits the iteration-close event (iteration
close is documentation, not a state-machine event).

## Cross-project contamination

Lane discipline held throughout 0.3.1. `git config user.email` was
`*@socfoundry.com` for all aho work (sovereign domain lane). No
customer-engagement codenames, foreign-node keys, or kjtcom-construct
leakage observed. The W2 first-tenant Firestore writer module
preserved the tenant-namespaced project shape
(TTEOS / notjustavar / customer-codename); no cross-lane reference
collisions surfaced during W2 dry-run.

## Sealed-archive inventory

Every artifact below is sealed; modifying any of them after operator
sign on this iteration-close note would invalidate the close.
Recorded for auditability:

### W0

- `artifacts/iterations/0.3.1/acceptance/W0.json` -
  `ab37497914bb9b194e7434138bd88a9d3a1278185d1cb37dd11836983731a7ff`
- `artifacts/iterations/0.3.1/audit/W0.json` -
  `9749cfed8fd5268e0facf36915459f616200e7c43de21ff778f75f9e83115e14`
- `artifacts/iterations/0.3.1/W0-close-note.md` -
  `569187af00ba52922d495b26184b5351fc79ce3d2611b03eceff0f30485b0f3b`
- `artifacts/iterations/0.3.1/W0-to-W1-handoff.md` -
  `4b3da6bb23294135b0f7cef53be4f22aba92f8861eb8c1af558a5882a70d7b31`
- `artifacts/iterations/0.3.1/carry-forward-fold-in.md` -
  `a0137d18731973920c4e9311e28014a742034b8e1ea524439ee3bc978c47cdd6`

### W1

- `artifacts/iterations/0.3.1/acceptance/W1.json` -
  `76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba`
- `artifacts/iterations/0.3.1/audit/W1.json` -
  `3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d`
- `artifacts/iterations/0.3.1/W1-close-note.md` -
  `d4858fb576405775f556b89124880e80fe04c2b663f359aa2b855c16ea26a17c`
- `artifacts/iterations/0.3.1/W1-plan-doc-amendment.md` -
  `70e5a429a8973ccdba873533284823a500413a833d8041aa7f0a49d166e68c33`

### W2

- `artifacts/iterations/0.3.1/acceptance/W2.json` -
  `f213db07c17cca9a9ff565aa066af35813ba7f54ddf7eca2988b0a8a2cc51d34`
- `artifacts/iterations/0.3.1/audit/W2.json` -
  `1d98fa0d4d8acbc81a8fc1367aac09bba1aca1baf2e5c2f513a2ad47756e0fd6`
- `artifacts/iterations/0.3.1/W2-close-note.md` -
  `1715b37697d30dc38472fe09642fa20b631c6ca4470c7b6f4aa4d7907b82c0a4`
  (post-operator-sign; pre-sign sha was
  `970f105e8c239d12f703cb426d2b7de8216f1ec51e45338b877a81bb57ac3047`)
- `artifacts/iterations/0.3.1/W2-plan-doc-amendment.md` -
  `8118ace07548f06e49d6cc2f8696520a580aa8c54e5d7c77e74e10fff2f75aad`

### ADRs introduced in 0.3.1 W0

- `artifacts/adrs/0011-substrate-freshness.md` (new at W0) -
  `416596570035ae94089b525986209ce4140b4374ed4fca7fd839f250d16c79ea`
- `artifacts/adrs/0012-chain-of-trust-l5.md` (new at W0) -
  `7a6f9ccf93b7b5b0771c471aaddb6a17fdcc347b453f1db2406db808c0327cf9`

### Out-of-band analysis (driving the substrate-pivot decision)

- `artifacts/iterations/0.3.1/p3cos-council-port-analysis.md` -
  `b8a4e328160cde1e2eb203ca6962535156acae01efae8f9a888d80ff19ba066d`

### Verification

All sha256 values above were computed by direct `sha256sum` on the
sealed files at iteration-close authoring time. Cross-check with
`sha256sum -c` against this inventory before signing.

## Iteration close attestation

This iteration-close note is a documentation artifact, not a
state-machine event. The canonical state advancements are the
`workstream_complete` event chain (W0, W1 emitted; W2 pending operator
sign per §State at close). **No additional event-log event is emitted
on iteration close** - the chain itself is the state machine.

The early close at W2 is operator-directed and substrate-pivot driven,
not failure-driven. W0 and W1 sealed-and-emitted; W2 sealed and
pending operator sign at authoring time. The W3-W7 original scope
moves to 0.3.2 (§Deferred to 0.3.2) where p3cos partial-tier compute
makes the 9B council producer/evaluator work viable.

### Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-28T12:17:46Z
W0 close acknowledged: yes (sha
`569187af00ba52922d495b26184b5351fc79ce3d2611b03eceff0f30485b0f3b`,
operator-signed 2026-05-24T12:44:34Z, workstream_complete
2026-05-24T12:47:57Z)
W1 close acknowledged: yes (sha
`d4858fb576405775f556b89124880e80fe04c2b663f359aa2b855c16ea26a17c`,
operator-signed 2026-05-25T15:23:09Z, workstream_complete
2026-05-25T15:27:58Z)
W2 close acknowledged: yes (sha
`1715b37697d30dc38472fe09642fa20b631c6ca4470c7b6f4aa4d7907b82c0a4`,
operator-signed 2026-05-28T05:08:39Z, workstream_complete
2026-05-28T05:09:04Z; the late-emit corrective surgery for the
0.2.18 -> 0.3.1 iteration-tag mismatch is documented in §State at
close)
Substrate-pivot decision acknowledged: yes
(9B council producer/evaluator moves to p3cos partial-tier in 0.3.2)
Carry-forwards state acknowledged: yes
(8 closed in iteration: F-0.2.18-W1-004, F-0.2.18-W2-002,
F-0.2.18-W2-003, F-0.2.18-W2-004, F-0.3.1-W0-001, F-0.3.1-W0-002,
F-0.3.1-W0-004, F-0.3.1-W0-005; 1 code-closed Track-B-gated:
F-0.3.1-W0-003 awaits davidk Beacon endpoint + token; 6 carrying to
0.3.2: F-0.3.1-W1-001, F-0.3.1-W2-001, F-0.2.18-W0-008,
F-0.2.17-W6-001, F-0.2.17-W5-001, F-0.2.18-W2-009)
Sealed-archive inventory acknowledged: yes
Out-of-band work inventory acknowledged: yes
(council global-use wiring on a8cos; 6 source files + 2 docs +
CLAUDE.md carry-forward, all uncommitted at authoring time;
operator commits when drafter folds into 0.3.2)
0.3.2 launch scope acknowledged: yes
(W3 partial-tier deployment + qwen auditor seat on p3cos,
W4 Firestore dry-run, W5 repo-resident docs reframing, W6 ADR
consolidation + Pillar 10/11/12/13 amendments, W7 final closures;
council global-use wiring folds into W3 or new W3.5)
Iteration scope complete at W2: yes
0.3.1 iteration: closed
