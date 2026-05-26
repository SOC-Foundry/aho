# 0.2.17 W5 plan doc

**Workstream:** W5 - ADR consolidation + repo-resident component decomposition + repo-resident claw3d brick spec + 0.2.17 retrospective
**Iteration:** 0.2.17
**Phase boundary:** 0.2.17 ships base container on NZXTcos. W0–W4 produced the substrate, the council, the auditor-RAG integration, and the structural filter. W5 converts four iterations of chat-side decisions into repo-resident authoritative ADRs and produces the iteration retrospective. W6 closes the residual code-change carry-forwards (F-0.2.17-W1-001 secrets-test removal, F-0.2.17-W4-001 ChromaDB re-index hook). After W6 closes, operator runs pre-tsP3 final actions (token rotation per F-0.2.17-W1-003) outside the workstream framework, then 0.3.1 launches.
**Executor:** Claude Code (`claude --dangerously-skip-permissions`) on NZXTcos.
**Drafter:** Claude web.
**Auditor:** llama3.2 + RAG enrichment + deterministic post-hoc filter - full stabilized audit primitive from W4. Bootstrap test 6 in the architecture's progression.
**Time budget:** 4–8 hours executor wall-time. Hard ceiling 10 hours. Overnight session - operator unavailable for ~8 hours starting at executor launch.
**Adversarial Authorship contract:** drafter drafts, executor implements, auditor (llama+RAG+filter) audits at end-of-workstream, drafter reviews disposition pre-sign, operator signs.
**Pre-0.3.x hard gate (recurring reminder):** F-0.2.17-W1-003 - rotate `ahomw:telegram_bot_token`. Operator action queued post-0.2.17-close per pinned protocol. Surface at W5 close. Surface at W6 close. Surface before tsP3 handoff. Closes outside W5/W6 scope.

---

## Scope

W5 ships authoritative repo-resident documentation derived from four iterations of chat-side architectural work. By close, the chat-side architecture artifact (`aho-base-container-architecture.md`) is superseded by repo-resident ADRs and decomposition docs; chat-side artifact retained as historical/working reference but no longer authoritative.

W5 ships:

1. **ADR-0007 amendment** - §council-roles subsection, base-tier seat assignments, role-collapse trip-wire, anti-rubber-stamp hardening, confidence-floor lock.
2. **ADR-0009 (new)** - Secrets broker boundary spec (Pillar 11 invariant in code + per-engineer onboarding).
3. **ADR-0010 (new)** - Materiality measurement protocol with three-iteration evidence build (W2 baseline / W3 partial / W4 structural).
4. **Component decomposition repo-resident doc** - `docs/architecture/component-decomposition.md` (new).
5. **claw3d brick spec repo-resident doc** - `docs/architecture/claw3d-brick-spec.md` (new).
6. **0.2.17 retrospective** - `docs/retrospectives/0.2.17.md` (new).
7. **Architecture-artifact supersession marker** - header note added to chat-side `aho-base-container-architecture.md` indicating canonical location is now `docs/architecture/`. Chat-side artifact retained verbatim, superseded.
8. **W5 self-audit** with stabilized auditor (bootstrap test 6).

W5 does NOT include: F-0.2.17-W1-001 secrets-test subcommand removal (W6); F-0.2.17-W4-001 ChromaDB re-index hook (W6); F-0.2.17-W1-003 token rotation (operator-side, post-0.2.17); 0.3.x partial-tier work.

## Deliverables

### D1 - ADR-0007 amendment

**Path:** `docs/adr/0007-containerization-architecture.md` (modify existing).

**Shape:** Add new subsection §council-roles between existing §k8s-readiness and §GPU passthrough deferral. Subsection content drawn verbatim where possible from chat-side architecture artifact §Seat assignments, §Auditor contract, §Anti-rubber-stamp hardening:

- Drafter seat: external (Claude web), persistent across chat sessions, gap-net for what auditor cannot catch by design.
- Executor seat: external (Claude Code or Gemini CLI), per-iteration, codified per iteration in plan doc.
- Auditor seat: in-container (llama3.2 at base tier; partial-tier and full-tier deferred to 0.3.x roadmap). Structural spot-check contract: claim-vs-artifact verification, contract-shape validation, invariant resolution. Confidence floor 0.85 structurally enforced. Disposition shape `clean | halt | surface_to_drafter` with `clean` unreachable below threshold. Deterministic post-hoc filter on RAG-aware findings (per W4 D1) suppresses fake-ID-on-registered-anchor failure mode.
- Triage seat: in-container (nemotron-mini), classification only, raise-on-malformed (no `categories[-1]` fallback per G083).
- Retrieval seat: in-container (nomic-embed-text + ChromaDB host-mounted volume), recency-weighted query, sole embedding source, feeds context to triage and audit.
- Role-collapse trip-wire: `executor_model_family ≠ auditor_model_family` enforced as OTEL invariant. Llama (Meta) vs Claude/Gemini (Anthropic/Google) cross-family.
- Anti-rubber-stamp hardening: three failure modes (G083 raise-on-malformed, GLM removed from auditor candidacy at base tier, llama confidence-floor lock + W4 deterministic post-hoc filter).

**Acceptance gate:**
- ADR-0007 amendment committed (drafter authoring; operator commits per Pillar 11) with §council-roles subsection present.
- All five seat assignments documented with model and locus.
- Confidence-floor lock and post-hoc filter referenced explicitly with cross-references to W2/W3/W4 sealed archives.

### D2 - ADR-0009 (new) Secrets broker boundary spec

**Path:** `docs/adr/0009-secrets-broker-boundary.md` (new).

**Shape:** New ADR following project ADR template. Content drawn from chat-side architecture artifact §Pillar 11 / Secrets boundary + W1 D3 implementation evidence:

- Context: container-host security boundary for credential access. Pillar 11 invariant requires zero credential material in image layers; container has zero git write capability; per-engineer onboarding scales beyond two operators without keystore mixing.
- Decision: host-side unix-socket broker (`${XDG_RUNTIME_DIR}/aho-secrets.sock`) authenticates connecting peer via SO_PEERCRED, validates project label, returns single decrypted value per request. Container-side `aho.secrets_client` connects to bind-mounted socket, JSON line request/response, no caching across container restarts. Wrapper `aho host run-container` registers UID before `podman run`, unregisters on exit.
- Three rules (verbatim from chat-side artifact): (1) no credential material in image layers ever, (2) per-user secret access via host-side broker, (3) no SSH agent socket forwarded.
- Per-engineer onboarding: each engineer runs `aho host install`, generates own age identity, populates own fernet store, starts own broker. Image is identical across engineers; mounts differ per host. Container literally cannot push under anyone's identity, including its own.
- Implementation evidence: 0.2.17 W1 D3 (acceptance archive sha `e4d076ee…`). Pillar 11 incident F-0.2.17-W1-003 captures drafter-side design responsibility lesson - value-printing in test subcommand violated the boundary; replaced with hash-fingerprint comparison in W6.

**Acceptance gate:**
- ADR-0009 file present at `docs/adr/0009-secrets-broker-boundary.md`.
- Three rules quoted verbatim from chat-side artifact.
- W1 D3 cross-reference with sha included.
- F-0.2.17-W1-003 Pillar 11 incident referenced as worked example of why hash-fingerprint contract exists.

### D3 - ADR-0010 (new) Materiality measurement protocol

**Path:** `docs/adr/0010-materiality-measurement.md` (new).

**Shape:** New ADR. Content from chat-side architecture artifact §Materiality measurement protocol + W2/W3/W4 evidence:

- Context: architecture's "harness-as-IQ" claim requires falsifiable evidence. Token-spend reduction is downstream artifact, not design driver. Primary objective: better project outcomes than single-agent executor on the same work.
- Decision: four-bucket OTEL counter telemetry. (1) llama-caught: claim-vs-artifact mismatches auditor flagged. (2) drafter-caught: defects llama dispositioned `clean` that drafter flagged on next planning turn. (3) escaped: defects neither caught, surfaced later. (4) carry-forward resolution rate.
- Falsifiability threshold: after N≥8 iterations, ≥30% reduction in escaped defects vs baseline, non-zero llama-caught + drafter-caught buckets, carry-forward resolution rate ≥60% within 2 iterations of flagging.
- 0.2.17 evidence build (three-iteration progression, recorded honestly):
  - **W2 (baseline)**: no auditor enhancement. Self-audit produced false positive (F-0.2.17-W1-003 flagged "looks placeholder" despite being sealed real).
  - **W3 (partial fix)**: RAG enrichment closed W0 false positive (F-W0-004 no longer flagged). W2 self-audit re-run still produced the false positive - small-model prompt-following inconsistency.
  - **W4 (structural closure)**: deterministic post-hoc filter structurally suppresses fake-ID-on-registered-anchor failure mode regardless of model behavior. Both demonstrated false positives now caught.
- N=4 (W0/W1/W2/W3) below the 8-iteration threshold for full materiality validation. Three-iteration evidence build is *qualified validation*, not full validation. ADR-0010 explicitly states this.

**Acceptance gate:**
- ADR-0010 file present at `docs/adr/0010-materiality-measurement.md`.
- Four-bucket protocol documented with OTEL counter names matching W2 D12 implementation.
- Falsifiability threshold explicit.
- Three-iteration evidence build (W2/W3/W4) recorded with sealed archive shas.
- N=4 caveat explicit - qualified validation, not full validation.

### D4 - Component decomposition repo-resident doc

**Path:** `docs/architecture/component-decomposition.md` (new).

**Shape:** New doc converting chat-side architecture artifact §Component decomposition into repo-resident form:

- Process tier: `aho.cli`, `aho.dispatcher`, `aho.workstream`, `aho.adversarial`, `aho.secrets_client`, `aho.artifact_writer`.
- Council tier: `aho.council.dispatch`, `aho.council.triage`, `aho.council.audit`, `aho.council.embed`, `aho.rag`.
- Observation tier: `aho.otel`, `aho.health`, `aho.signal`, `aho.audit_disposition_emitter`, `aho.gap_carry_forward_writer`.
- Council audit extensions (W3+W4): `aho.council.audit_ref_extract`, `aho.council.audit_ref_lookup`, `aho.council.audit_finding_filter`.
- Materiality (W2+): `aho.materiality`.
- Host-mounted (not in image): ChromaDB volume, iteration state volume, tier config, secrets broker socket.
- Out-of-process model layer: hybrid mode (development) via `host.containers.internal:11434`; production deferred to 0.3.x.
- Per-component contract: brief description, contract surface, source path, sha at W4 close.

**Acceptance gate:**
- File present at `docs/architecture/component-decomposition.md`.
- Each component listed with source path and W4-close sha.
- Council audit extensions (W3 + W4 additions) present.
- Materiality component (W2 D12) present.

### D5 - claw3d brick spec repo-resident doc

**Path:** `docs/architecture/claw3d-brick-spec.md` (new).

**Shape:** Convert chat-side architecture artifact §claw3d coverage + W4 D2 brick implementations into repo-resident form. Per-component panel definitions with red-conditions, materiality four-bucket dashboard surfaces, role-collapse trip-wire brick, materiality comparison surface, anti-rubber-stamp verification dashboard (four-surface version per W4 D6).

**Acceptance gate:**
- File present at `docs/architecture/claw3d-brick-spec.md`.
- 10 per-component bricks documented with red-conditions.
- Materiality dashboard surfaces documented.
- Anti-rubber-stamp dashboard documented as four-surface version (W4 D6 update).

### D6 - 0.2.17 retrospective

**Path:** `docs/retrospectives/0.2.17.md` (new).

**Shape:** Iteration retrospective covering:

- What shipped: base container on NZXTcos, full council, RAG-enriched + filter-stabilized auditor, materiality telemetry, claw3d brick rendering.
- What worked: chat-first hard meta-rule held throughout. Adversarial Authorship state machine produced honest dispositions. F-0.2.17-W1-003 Pillar 11 incident surfaced voluntarily by executor (system functioning as designed). W3→W4 progression from partial to structural closure of W2-006 / W3-001 demonstrated the iteration-over-iteration sharpening loop.
- What didn't: drafter-side design specification of secrets-test value-printing was wrong on Pillar 11 grounds (F-0.2.17-W1-003 root cause). Drafter conflated "executor" role with "Claude Code recipient" three times in chat (operator surfaced repeatedly). Initial W4 plan doc didn't anticipate auditor-RAG integration - refreshed post-W3-close with deterministic post-hoc filter as new D1.
- What surfaced unexpectedly: pasta networking SNATs container-host traffic to host primary IP arriving on lo (F-0.2.17-W1-002). GitHub Packages last-tag DELETE behavior (F-0.2.17-W0-003). NVIDIA CUDA tag scheme drift (F-0.2.17-W0-005). ChromaDB index staleness (F-0.2.17-W4-001).
- Materiality data summary: three-iteration evidence build recorded, N=4 below threshold, qualified validation.
- Forward-looking input to 0.3.x: partial-tier on tsP3 with qwen3.5:9b likely raises model-consistency floor; auditor-capability gap predicted to narrow with stronger model. Pre-0.3.x hard gates: F-0.2.17-W1-003 token rotation + F-0.2.17-W1-001 secrets-test subcommand removal (W6 closure).
- All carry-forwards summary: total entries in `carry-forwards-0.2.16.md` at W5 launch, status of each W0-NNN, W1-NNN, W2-NNN, W3-NNN, W4-NNN entry. Closures, openings, deferrals.

**Acceptance gate:**
- File present at `docs/retrospectives/0.2.17.md`.
- Five sections (shipped, worked, didn't, surfaced, materiality) populated.
- All carry-forwards (39 entries at W4 close) summary present.

### D7 - Architecture artifact supersession marker

**Path:** Modify chat-side `aho-base-container-architecture.md` (the chat-side artifact, location TBD - most likely operator's project folder, surfaced as needed via uploaded files in chat).

**Note:** This artifact may not be in the repo at all. If it isn't, the supersession marker becomes a documentation note in `docs/architecture/component-decomposition.md` indicating that the chat-side artifact predated and informed the repo-resident docs. Executor surfaces the actual location during D7 work; if no chat-side artifact found in repo, D7 reduces to: add a "Provenance" section to the repo-resident decomposition doc citing the chat-side artifact as historical input.

**Acceptance gate:**
- Either (a) chat-side artifact has supersession header pointing to `docs/architecture/`, OR (b) repo-resident decomposition doc has Provenance section citing chat-side artifact as input.

### D8 - W5 self-audit with stabilized auditor

**Process:** After D1–D7 land, executor writes preliminary W5 acceptance archive. Llama+RAG+filter audits it. Disposition at `audit/W5.json`. Halt-and-surface after emit. Drafter reviews pre-sign.

**Acceptance gate:**
- Self-audit disposition lands.
- Filter outcome recorded (eligible, registered_id_count, suppressed_count).
- Drafter arbitrates findings before operator signs.
- This is bootstrap test 6 - sixth deployment of the auditor primitive. By now, the auditor has been used on its own work three times (W2 self-audit, W3 self-audit, W4 self-audit) plus three replays + W5 self-audit. Pattern recognition on auditor failure modes should be predictable.

## Cross-references

- **Chat-side architecture artifact** (`aho-base-container-architecture.md`): superseded at W5 close per D7.
- **W4 sealed archives**: `acceptance/W4.json` (sha `949908ff…`), `audit/W4.json` (sha `9d5ab9ec…`). DO NOT MODIFY.
- **All prior workstream sealed archives**: W0/W0-amendment-b2-3/W1/W2/W3 + close notes. DO NOT MODIFY.
- **carry-forwards-0.2.16.md**: 39 entries at W5 launch. Updates only via `gap_carry_forward_writer.append_to_file` per established pattern.
- **F-0.2.17-W1-001**: secrets-test subcommand removal - W6 scope.
- **F-0.2.17-W4-001**: ChromaDB re-index hook - W6 scope.
- **F-0.2.17-W1-003**: token rotation - operator-side, post-0.2.17.

## Acceptance archive shape

`artifacts/iterations/0.2.17/acceptance/W5.json`:
- `audit_status: "pending_audit"` at write time, transitions to `pending_drafter_review` after D8.
- Entry per D1–D8.
- `carry_forwards_added` for any new findings.
- `carry_forwards_closed`: empty unless something surfaces. Closures of W1-001/W4-001/W1-003 are W6/operator scope.
- `pillar_11_invariant_check: "pass"` with executor-session-log evidence.
- `outstanding_pre_03x_gates` listing F-0.2.17-W1-003 + F-0.2.17-W1-001 + F-0.2.17-W4-001.
- `agents_involved` listing drafter, executor, auditor (llama3.2 + RAG + filter).
- Sealed sha recorded.

## Halt-and-surface conditions

- Wall-time > 8h soft, > 10h hard.
- D1–D5 ADR / doc generation produces files that don't validate against project doc template (executor surfaces malformed shape).
- D6 retrospective produces obviously-wrong carry-forward summary count (cross-check against `carry-forwards-0.2.16.md` actual count).
- D8 self-audit produces fake-ID-on-registered findings the filter should have caught (W4 D1 hardening regression).

## Out of scope (deferred)

- F-0.2.17-W1-001 secrets-test subcommand removal → W6.
- F-0.2.17-W4-001 ChromaDB re-index hook → W6.
- F-0.2.17-W1-003 token rotation → operator-side, post-0.2.17.
- 0.3.x partial-tier deployment on tsP3 → 0.3.1.

## Executor prompt

(Lands as separate artifact at `artifacts/iterations/0.2.17/prompts/W5-executor.md`.)
