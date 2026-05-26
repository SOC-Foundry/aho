# 0.2.17 W2 plan doc

**Workstream:** W2 - feedback loop wiring + ChromaDB integration + auditor-seat transition
**Iteration:** 0.2.17
**Phase boundary:** 0.2.17 ships base container on NZXTcos. W1 produced the image and stubs; W2 makes the council real and transitions audit ownership from external (Gemini CLI) to in-container (llama3.2). W3 layers materiality measurement and claw3d. W4 consolidates ADRs and runs retrospective.
**Executor:** Claude Code (`claude --dangerously-skip-permissions`).
**Drafter:** Claude web (Kyle's project folder, persistent).
**Auditor (this iteration):** llama3.2 in-container, via `aho.council.audit` produced by W2 itself. **This is the auditor-seat transition.** Gemini CLI exited the audit chain at W1 close. From W2 forward, llama3.2 is the structural spot-checker; drafter (Claude web) is the architectural-judgment gap-net.
**Time budget:** 4–8 hours executor wall-time. Hard ceiling 10 hours. Beyond 10 hours = halt-and-surface, do not continue. This is an overnight run; operator is unavailable for ~8 hours starting at executor launch.
**Adversarial Authorship contract:** Drafter (me) drafts plan + executor prompt. Executor (Claude Code) implements. Auditor (llama3.2 in-container) audits at end-of-workstream. Drafter (me) reviews llama's disposition pre-sign. Operator (Kyle) signs after drafter review.
**Pre-0.3.x hard gate carry-forward (recurring reminder):** F-0.2.17-W1-003 - rotate `ahomw:telegram_bot_token`. Surface at W2 close. Surface at W3 close. Surface at W4 close. Surface before tsP3 handoff.

---

## Scope

W2 makes the council real and bootstraps the in-container auditor seat. By close, the framework is auditing itself - a load-bearing thesis test for the architecture's "harness-as-IQ" and "Adversarial Authorship at base-tier" claims.

W2 ships:

1. **`aho.rag` real implementation** against host-mounted ChromaDB; recency-weighted retrieval; nomic embeddings via host Ollama.
2. **Four real council component implementations** replacing W1 stubs: `aho.council.embed` (nomic), `aho.council.triage` (nemotron-mini), `aho.council.audit` (llama3.2), `aho.council.dispatch` (real routing).
3. **Two real feedback-loop components**: `aho.audit_disposition_emitter`, `aho.gap_carry_forward_writer`.
4. **Anti-rubber-stamp hardening verified** across the three failure modes (G083 raise-on-malformed, GLM removed from auditor candidacy at base tier, llama confidence floor lock).
5. **W0 audit replay** - llama3.2 audits sealed `acceptance/W0.json` after-the-fact; disposition compared structurally to Gemini's sealed W0 audit. **Bootstrap test 1.**
6. **W1 audit replay** - llama3.2 audits sealed `acceptance/W1.json` after-the-fact; disposition compared structurally to Gemini's sealed W1 audit. **Bootstrap test 2.**
7. **W2 self-audit** - llama3.2 audits W2's own acceptance archive at end-of-workstream. **Bootstrap test 3 (loop closure).**
8. **Materiality telemetry hooks** - OTEL signals emitted for the four buckets (llama-caught, drafter-caught, escaped, carry-forward-resolution-rate). Not yet wired to claw3d (W3); just emitted so W3 has data.

W2 does NOT include: claw3d brick rendering (W3); materiality four-bucket dashboard surfaces (W3); ADR documents (W4); secrets-test subcommand redesign (per F-0.2.17-W1-001 / W1-003 - fold into W2 if low-effort, otherwise W4).

## Disagreement-handling protocol (D9/D10 specific)

Per pinned scope:

- If llama's W0 audit replay (D9) disagrees with Gemini's sealed W0 audit on any disposition (deliverable result, finding severity, count_coherence_check, etc.) - **record both dispositions in the W2 acceptance archive's D9 evidence section. Do not attempt to reconcile. Do not modify Gemini's sealed W0 audit.** Flag the disagreement count and shape (which findings, which axis of disagreement) in the D9 disposition note.
- Same pattern for W1 audit replay (D10).
- Disagreements are NOT findings against W2. They are data points. Drafter (me, in chat) arbitrates each disagreement post-close, before W3 launch. Drafter-arbitrated dispositions either become carry-forward entries (if the disagreement reveals a gotcha or design issue) or get logged as "no action required, dispositions differ on stylistic axis" in the W2 close note.

If executor encounters a disagreement that looks substantively important (e.g., llama flags a Pillar 11 violation Gemini missed, or vice versa), executor halt-and-surfaces immediately rather than completing W2 around the unresolved disagreement. Substantively important = "if true, would invalidate a sealed archive's disposition." Stylistic important = "different framing of the same finding" - record and continue.

## W2 self-audit protocol (D11 specific)

Per pinned scope:

- D11 runs at end-of-workstream after D1–D10 complete. Sequential, not per-deliverable.
- Llama3.2 audits W2's own acceptance archive (the artifact W2 just produced).
- Disposition options: `clean | halt | surface_to_drafter`. Below confidence floor 0.85, disposition locks to `surface_to_drafter` per architecture artifact §Anti-rubber-stamp hardening.
- Llama's disposition lands in W2's audit archive (`audit/W2.json`) as the iteration's primary audit record - replacing what would have been Gemini's slot.
- Executor halt-and-surfaces after D11 emits, regardless of disposition. Drafter (me) reviews llama's disposition pre-sign in chat with operator. **Operator does not sign until drafter has reviewed.**

If llama's W2 self-audit disposition is `surface_to_drafter` - that's the gap-net activating. Drafter reads the disposition, the W2 acceptance archive, and the surfaced findings; either confirms the findings as real (W2 closes pass_with_findings or fails depending on severity) or arbitrates as auditor-overzealous (W2 closes pass with drafter-arbitrated note). Same shape as Adversarial Authorship working through Gemini in W0/W1, just with llama in the seat.

## Deliverables

### D1 - `aho.rag` real implementation against host-mounted ChromaDB

**Module:** `src/aho/rag.py` (replaces or extends W1 placeholder if present).

**Shape:**
- ChromaDB client connecting to host-mounted volume at `/var/lib/aho/chroma` (declared in W1 Dockerfile).
- Single collection per project, named `{project_label}-iteration-context`.
- Embedding source: `aho.council.embed` (which calls nomic via host Ollama). RAG and embed are tightly coupled - same embedding shape for index and query.
- Recency weighting: query results weighted by `iteration_seq_ordinal` of the source artifact, with exponential decay. More recent iterations weighted higher per existing aho ChromaDB pattern.
- Query interface: `query(text: str, k: int = 5, project: str | None = None) -> list[dict]` returning ranked retrievals with metadata (source_iteration, source_workstream, source_artifact_path, snippet, score).
- Indexing interface: `index_artifact(path: str, project: str, iteration: str, workstream: str)` reads file, embeds via nomic, writes to collection with metadata.
- Pre-seed at W2 launch: index all sealed artifacts from 0.2.16 W0–W4 + 0.2.17 W0 + 0.2.17 W1 (acceptance archives, audit archives, close notes, plan doc, carry-forwards-0.2.16.md). This produces the retrieval substrate for D9 and D10 audit replays.

**Acceptance gate:**
- `aho rag query "telegram bot token" --project ahomw` returns at least one result citing the W1 acceptance archive's F-0.2.17-W1-003 entry (Pillar 11 incident).
- `aho rag query "GitHub Packages last-tag DELETE" --project ahomw` returns at least one result citing F-0.2.17-W0-003 from the carry-forwards file.
- Pre-seed index landed: ChromaDB collection size matches expected count (executor enumerates expected from a recursive grep of sealed artifact paths).
- Recency weighting verified: query for a topic appearing in both 0.2.16 and 0.2.17 returns the 0.2.17 result first.

### D2 - `aho.council.embed` real implementation

**Module:** `src/aho/council/embed.py` (replaces W1 stub).

**Shape:** Calls nomic-embed-text via host Ollama at `host.containers.internal:11434`. Returns embedding vector matching nomic's actual dimensionality (768). Raises on malformed input. OTEL span per call with `model_id`, `tier`, `latency_ms`, `input_token_count`, `output_dim`. No `stub: true` attribute (real impl).

**Acceptance gate:**
- `embed("test input")` returns a 768-dim float vector, real values (not zeros).
- Latency p50 < 200ms on NZXTcos for typical iteration-context-shaped input.
- Malformed input (None, int, empty string) raises `CouncilEmbedInputError`.
- OTEL span lands with full attribute set.

### D3 - `aho.council.triage` real implementation

**Module:** `src/aho/council/triage.py` (replaces W1 stub).

**Shape:** Calls nemotron-mini:4b via host Ollama. Two operation modes:
1. **Classify mode:** classify an artifact into a known category set (gotcha-candidate, ADR-relevance, gate-state, work-shape-tier-decision). Returns structured JSON with `category`, `confidence`, `rationale_summary`. Rubric-bounded; if model output is out-of-rubric, **raise - do not fall back to `categories[-1]`**. G083 hardening verified by explicit test in D8.
2. **Registry-delta drafting mode:** given an executor output and current registry state, draft proposed new gotcha-registry entries or ADR-relevance hits. Returns list of draft entries with `kind`, `proposed_text`, `confidence`, `rationale`. Drafts are *proposals* - never written to registry directly by triage; written by `aho.council.dispatch` after approval flow (W3 work; W2 just produces the proposals).

**Acceptance gate:**
- Classify mode against fixture artifact returns valid category from rubric, confidence in [0, 1], rationale present.
- Out-of-rubric output handling: when fed an artifact designed to elicit junk classification, raises `CouncilTriageMalformedError` rather than returning `categories[-1]`-shaped fallback.
- Registry-delta mode against fixture executor-output produces ≥1 proposal with valid shape.
- OTEL span per call with full attribute set including `confidence`, `mode`.

### D4 - `aho.council.audit` real implementation

**Module:** `src/aho/council/audit.py` (replaces W1 stub).

**Shape:** Calls llama3.2:3b via host Ollama. Structural spot-check contract per architecture artifact §Auditor contract:
- Did executor say it did X? Does the artifact corroborate X?
- Did executor reference a gotcha/ADR/carry-forward by ID? Does the ID resolve?
- Did the workstream contract require deliverables A, B, C? Is each present?
- Did executor close a checkpoint? Does state transition match contract?
- G081 banned phrases absent? (regex + nomic semantic confirm)
- Three-octet versioning, sign-off checkboxes `[x]/[ ]`, no agent git ops referenced.

Disposition shape: `{disposition: clean | halt | surface_to_drafter, confidence: float, findings: [...], evidence_traces: [...]}`.

**Confidence floor:** 0.85, structurally enforced. If `confidence < 0.85`, disposition is locked to `surface_to_drafter`. The `clean` disposition is unreachable below threshold. Implementation: validate the floor in code post-model-output, override `disposition` field if model returned `clean` at low confidence.

**Acceptance gate:**
- Audit against a fixture-good artifact (drafter-authored "obviously clean" artifact with all expected references resolving) returns `clean` with `confidence ≥ 0.85`.
- Audit against a fixture-bad artifact (drafter-authored with intentional defects: wrong sha, broken gotcha reference, banned G081 phrase, missing deliverable) returns `surface_to_drafter` with concrete findings naming each defect.
- Confidence floor lock verified: a third fixture forces low-confidence model output (artifact ambiguous on purpose); even if model says `clean`, post-validation overrides to `surface_to_drafter`.
- OTEL span per call with full disposition attributes.

### D5 - `aho.council.dispatch` real implementation

**Module:** `src/aho/council/dispatch.py` (replaces W1 stub).

**Shape:** Routes work to a council seat by (work_shape, role, tier). Routing table for base tier:
- `(structural_audit, audit, base)` → `aho.council.audit` (llama3.2)
- `(classify, triage, base)` → `aho.council.triage` (nemotron-mini)
- `(registry_delta_draft, triage, base)` → `aho.council.triage` (nemotron-mini)
- `(embed, retrieval, base)` → `aho.council.embed` (nomic)
- `(retrieve, retrieval, base)` → `aho.rag.query`
- Substantive drafting work at base tier → raise `CouncilDispatchEscalateRequired` exception with target `partial_tier_or_external_drafter`. Base tier doesn't host substantive drafters; it escalates out.

OTEL span per dispatch call with `model_id`, `role`, `work_shape`, `tier_decision`, `latency_ms`. Span attributes feed materiality telemetry (D12).

**Acceptance gate:**
- Dispatch round-trips for all four base-tier roles work end-to-end.
- Substantive-drafting dispatch raises `CouncilDispatchEscalateRequired` (not silent fallback).
- Role-collapse trip-wire emits when dispatched drafter and auditor are same model family - verified by test fixture.
- Routing decisions logged structurally; one OTEL span per dispatch.

### D6 - `aho.audit_disposition_emitter` real implementation

**Module:** `src/aho/audit_disposition_emitter.py` (new).

**Shape:** Writes audit disposition artifact in two-part format:
- Machine-parseable header (YAML or JSON front-matter): `disposition`, `confidence`, `auditor_model_id`, `audit_started_utc`, `audit_completed_utc`, `target_artifact_sha256`, `findings_count`, `evidence_trace_count`.
- Human-readable body: per-finding text written for drafter (me) to consume on next planning turn. Format per architecture artifact §Component decomposition.

Output path: `artifacts/iterations/{iteration}/audit/{workstream}.json` for top-level audits, `artifacts/iterations/{iteration}/audit/replay/{source}.json` for replay audits like D9 and D10.

**Acceptance gate:**
- Disposition artifact for fixture audit lands at expected path with both header and body sections.
- Header is machine-parseable: `python3 -c "import json; json.load(open(path))"` succeeds, schema validates.
- Body is human-readable: per-finding sections present, no raw JSON dumps in prose.

### D7 - `aho.gap_carry_forward_writer` real implementation

**Module:** `src/aho/gap_carry_forward_writer.py` (new).

**Shape:** When drafter (in chat) flags a gap that should carry forward, this component is invoked (by next iteration's executor in normal cadence; by D11 self-audit's surface_to_drafter path during W2). Writes a structured carry-forward entry to `artifacts/iterations/{prev_iteration}/carry-forwards-{prev_iteration}.md` following the existing entry shape (Severity / What surfaced / Mechanism / Disposition / Target / Source / Audit traceability).

**Acceptance gate:**
- Synthetic invocation with a drafted gap-shape produces a valid carry-forward entry matching the file's existing shape (regex against entry header, all required sections present).
- Entry inserts at the correct location (matches surrounding entry IDs by source iteration/workstream).
- File line count and entry count both increment by exactly +1 entry, +N lines per the entry's content.

### D8 - Anti-rubber-stamp hardening verification

**Module:** `tests/test_anti_rubber_stamp.py` (new test file).

**Shape:** Three explicit tests, one per failure mode:
1. **Nemotron raise-on-malformed:** feed nemotron-mini an out-of-rubric prompt designed to elicit garbled JSON; assert `CouncilTriageMalformedError` raises rather than `categories[-1]`-shaped fallback.
2. **Llama confidence-floor lock:** mock-feed `aho.council.audit` a model output with `disposition: clean, confidence: 0.6`; assert disposition is rewritten to `surface_to_drafter` post-validation.
3. **Role-collapse trip-wire:** invoke `aho.council.dispatch` such that a single iteration would assign drafter and auditor to same model family; assert dispatch raises `CouncilRoleCollapseError` rather than silently approving.

**Acceptance gate:**
- All three tests pass.
- All three tests fail when their respective hardening is bypassed (mutation-test the hardening itself - verify the test catches the failure mode it's protecting against).

### D9 - W0 audit replay (bootstrap test 1)

**Process:**
1. Read sealed `artifacts/iterations/0.2.17/acceptance/W0.json` plus `acceptance/W0-amendment-b2-3.json`.
2. Read sealed `artifacts/iterations/0.2.17/audit/W0.json` (Gemini's audit) - but DO NOT use its disposition as input. Llama audits independently.
3. Llama runs structural spot-check via `aho.council.audit` against W0 acceptance archive + amendment. Produces disposition.
4. Compare llama's disposition to Gemini's structurally: per-deliverable result match, per-finding match, count_coherence_check match.

**Output:** `artifacts/iterations/0.2.17/audit/replay/W0-llama.json` (llama's disposition, sha-recorded). `artifacts/iterations/0.2.17/audit/replay/W0-comparison.json` (per-axis comparison: agreement-count, disagreement-count, disagreement-shapes).

**Acceptance gate:**
- Llama produces a disposition (any shape).
- Comparison artifact lists every disagreement explicitly. Empty disagreement list is acceptable; just must be enumerated, not asserted.
- If any disagreement is "substantively important" (per disagreement-handling protocol above), executor halt-and-surfaces - does not continue to D10.

### D10 - W1 audit replay (bootstrap test 2)

**Process:** Same as D9, against `artifacts/iterations/0.2.17/acceptance/W1.json` and Gemini's `audit/W1.json`.

**Output:** `audit/replay/W1-llama.json`, `audit/replay/W1-comparison.json`.

**Acceptance gate:** Same as D9.

### D11 - W2 self-audit (bootstrap test 3, loop closure)

**Process:**
1. After D1–D10 land, executor writes preliminary W2 acceptance archive at `acceptance/W2.json` with `audit_status: pending_audit`.
2. Llama runs structural spot-check via `aho.council.audit` against the W2 acceptance archive itself. Produces disposition.
3. Disposition lands at `audit/W2.json` (the iteration's primary audit record, replacing Gemini's slot from W0/W1).

**Acceptance gate:**
- Llama produces a W2 self-audit disposition.
- Audit archive is structurally valid (sha-recordable, machine-parseable header, human-readable body).
- Executor halt-and-surfaces after D11 emits, regardless of disposition. **Drafter reviews pre-sign.**

### D12 - Materiality telemetry hooks

**Modules:** Touch all council components and dispatch to add OTEL emission for the four-bucket telemetry per ADR-0010 (architecture artifact §Materiality measurement protocol):

- `claim_vs_artifact_mismatches.caught_by_llama` - incremented when `aho.council.audit` emits a finding.
- `claim_vs_artifact_mismatches.caught_by_drafter` - placeholder counter, populated in W3 when drafter-flagged gaps land via `aho.gap_carry_forward_writer`.
- `claim_vs_artifact_mismatches.escaped` - placeholder counter, populated post-iteration when later iterations surface defects from prior closes.
- `carry_forward_resolution_rate` - placeholder counter, populated when an executor closes a carry-forward by reference in their workstream output.

W2 emits the signals; W3 wires them to claw3d brick rendering. W2's bar is "OTEL signals emit, structurally correct, no observable downstream renderer required."

**Acceptance gate:**
- Each of the four counter signals emits at least once during W2 execution (D8/D9/D10/D11 collectively cover this).
- Signals are structurally valid OTEL: counter type, `aho.materiality.*` attribute namespace, resource attributes include `aho.iteration: 0.2.17`, `aho.workstream: W2`, `aho.tier: base`.

## Cross-references

- **Architecture artifact:** `aho-base-container-architecture.md` - canonical design source.
- **W1 plan doc + close note:** `artifacts/iterations/0.2.17/W1-plan-doc.md`, `artifacts/iterations/0.2.17/W1-close-note.md`.
- **W1 acceptance + audit archives:** `artifacts/iterations/0.2.17/acceptance/W1.json` (sha `e4d076ee…`), `artifacts/iterations/0.2.17/audit/W1.json` (sha `8b2771ac…`). DO NOT MODIFY.
- **W0 acceptance + audit + amendment archives:** sha values per W0 close note. DO NOT MODIFY.
- **carry-forwards-0.2.16.md:** 32 entries at W2 launch. New W2-spawned carry-forwards land here following same shape.
- **ADR 0007:** containerization architecture. W2 amendments TBD in W4 retrospective; W2 itself doesn't write ADR documents.
- **ADR 0008:** dispatcher missing-model. W2 inherits hybrid-mode `host.containers.internal:11434`.
- **F-0.2.17-W1-001:** secrets-test subcommand still in rc1 image. **Fold into W2 if low-effort during D6 or D7 work** (replace value-printing path with hash-fingerprint comparison). If not low-effort, punt to W4 retrospective.
- **F-0.2.17-W1-002:** pasta SNAT firewall lesson. Documentation-shaped; no code action in W2.
- **F-0.2.17-W1-003:** Pillar 11 incident. **Token rotation is operator-side, NOT executor-side.** Executor does not rotate tokens. Pre-0.3.x hard gate continues to carry-forward.
- **G001:** fish-pure shell. All operator-facing surfaces and codeblocks fish-clean.
- **G022:** `command ls` not `ls`.
- **G081:** no celebratory framing.
- **G083:** silent rubber-stamp gotcha. D8 verifies hardening.
- **Pillar 11:** zero git operations. Operator holds all git ops. Executor does not push, commit, or PR.

## Acceptance archive shape

`artifacts/iterations/0.2.17/acceptance/W2.json`:
- `audit_status: "pending_audit"` at write time, transitions to `pending_drafter_review` after D11 emits.
- One entry per D1–D12.
- `carry_forwards_added` for any new findings during W2.
- `pillar_11_invariant_check: "pass"` with executor-session-log evidence.
- `agents_involved` lists drafter, executor, auditor (llama3.2 - explicit model_id).
- `auditor_seat_transition_recorded` field documenting that this is the first iteration with in-container auditor.

## Halt-and-surface conditions

Executor halt-and-surfaces immediately on:

- Wall-time crosses 8 hours with deliverables incomplete (soft); 10 hours = hard ceiling.
- Any of the four real council components (D2, D3, D4, D5) fails to produce a working call-and-response with host Ollama after 3 retries with same error.
- ChromaDB pre-seed in D1 fails (file paths not enumerable, embedding errors).
- D9 or D10 surfaces a *substantively important* disagreement between llama and Gemini (per disagreement-handling protocol).
- D11 self-audit lands disposition `surface_to_drafter` with severity findings that suggest deeper W2 architecture issues (executor's judgment call; err on the side of surfacing).
- Anti-rubber-stamp test (D8) fails on any of the three failure modes.
- OTEL emission silently fails (no spans landing in collector despite expected calls).

On halt, write partial W2 acceptance archive with `audit_status: "blocked"`, record specific failure mode, do not retry beyond what's specified. Drafter (me) re-engages in chat at next operator turn.

## Out of scope (deferred)

- **claw3d brick rendering** → W3.
- **Materiality four-bucket dashboard surfaces** → W3.
- **Per-component bricks** → W3.
- **ADR 0007 amendment, ADR 0009 secrets broker, ADR 0010 materiality** as repo-resident → W4.
- **Component decomposition doc + claw3d brick spec** as repo-resident → W4.
- **Real-replay audits of 0.2.16 W0–W4** → 0.2.18+ if useful retrospectively. W2 only replays 0.2.17 W0 + W1.
- **Container-resident model bundling** → 0.3.x.
- **Production-mode dispatch (non-hybrid)** → 0.3.x.

## Executor prompt

(Lands as separate artifact at `artifacts/iterations/0.2.17/prompts/W2-executor.md` after this plan doc is reviewed.)
