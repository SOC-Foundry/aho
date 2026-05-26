# 0.2.17 W4 plan doc (refreshed post-W3-close)

**Workstream:** W4 - deterministic post-hoc filter on RAG-aware audit findings + claw3d brick rendering + materiality dashboard surfaces
**Iteration:** 0.2.17
**Phase boundary:** 0.2.17 ships base container on NZXTcos. W3 produced auditor-RAG integration with partial materiality validation (small-model prompt-following inconsistency surfaced as F-0.2.17-W3-001). W4 closes that residual gap with a deterministic post-hoc filter, then layers visualization on top of the now-stabilized auditor. W5 consolidates ADRs and runs retrospective.
**Executor:** Claude Code (`claude --dangerously-skip-permissions`) on NZXTcos.
**Drafter:** Claude web.
**Auditor:** llama3.2 with RAG enrichment + (after D1 lands) deterministic post-hoc filter on findings. Same in-container audit primitive, structurally stabilized for known small-model failure modes.
**Time budget:** 4–8 hours executor wall-time. Hard ceiling 10 hours. Overnight session - operator unavailable for ~8 hours starting at executor launch.
**Adversarial Authorship contract:** drafter drafts, executor implements, auditor (llama+RAG+filter) audits at end-of-workstream, drafter reviews disposition pre-sign, operator signs.
**Pre-0.3.x hard gate carry-forward (recurring reminder):** F-0.2.17-W1-003 - rotate `ahomw:telegram_bot_token`. Surface at W4 close. Surface at W5 close. Surface before tsP3 handoff.

---

## Refresh rationale (delta from initial W4 plan doc)

W3 close surfaced F-0.2.17-W3-001 - llama3.2:3b inconsistently honors the registered-references prompt rule. Drafter arbitration selected path (c) deterministic post-hoc filter as the structural fix appropriate for base-tier auditor model. This refresh adds the filter as the new D1 (foundation deliverable) and renumbers the previously-planned brick / dashboard work to D2–D7. The brick rendering benefits from a stabilized auditor first - bricks built on top of an inconsistent auditor would surface that inconsistency through the visualization layer rather than fixing it.

The rest of the W4 scope (claw3d bricks, materiality surfaces, role-collapse trip-wire, comparison surface, anti-rubber-stamp dashboard, self-audit) is unchanged from the initial draft.

## Scope

W4 ships:

1. **Deterministic post-hoc filter on RAG-aware audit findings (new D1).** Closes F-0.2.17-W3-001 / F-0.2.17-W2-006 structurally rather than via prompt-following. After llama returns its finding list, the filter inspects each finding for: (a) does the description contain a fake-ID phrase pattern ("not real," "looks placeholder," "matches naming conventions," etc.); (b) does the finding's anchor ID appear in the registered-references context with `registered` status. If both true, the finding is dropped with a structured suppression record (so the filtering action is auditable and falsifiable). Drafter explicitly chose this path over (a) prompt strengthening or (b) stronger model - both of which leave the model as a load-bearing decision-maker rather than a structurally-checked one.

2. **Per-component bricks for every `aho.*` component** in the architecture artifact §claw3d coverage list (10 bricks).

3. **Materiality four-bucket dashboard surfaces** rendering the W2 OTEL counters.

4. **Role-collapse trip-wire brick** rendering the W2 D5 OTEL invariant.

5. **Materiality comparison surface** - pre-base-container vs post-base-container side-by-side.

6. **Anti-rubber-stamp verification dashboard** - three failure-mode surfaces + overview.

7. **W4 self-audit** with the now-stabilized auditor (RAG enrichment + post-hoc filter).

W4 does NOT include: ADR documents (W5); component decomposition repo-resident doc (W5); full retrospective (W5); claw3d UI design polish beyond brick correctness; tsP3-deployment claw3d (0.3.1).

## Deliverables

### D1 - Deterministic post-hoc filter on RAG-aware audit findings (new, drafter-arbitrated path c from F-0.2.17-W3-001)

**Module:** `src/aho/council/audit_finding_filter.py` (new).

**Shape:** Post-`council.audit` function operating on the model's returned findings list. For each finding:

1. Extract anchor IDs from finding description via the same regex set used by `audit_ref_extract` (D1 of W3) - carry-forward IDs, ADR refs, gotcha refs, etc.
2. Check if any extracted anchor ID appears in the audit's `rag_enrichment.references` list with `status: "registered"`.
3. Check if finding description matches the fake-ID phrase set: `"not real"`, `"does not look real"`, `"looks placeholder"`, `"looks like a placeholder"`, `"matches naming conventions"`, `"not corroborated"`, `"cannot be corroborated"`, `"appears fictitious"`, `"appears fabricated"`. Case-insensitive, whole-phrase match.
4. If both (registered anchor + fake-ID phrase): drop the finding from the active list, append it to a new `suppressed_findings` list with reason `"registered_id_flagged_as_fake"` and the matched phrase.
5. Suppressed findings are recorded structurally - auditable and falsifiable. Operator (or a future audit) can inspect what was suppressed and why.

**Anti-rubber-stamp constraint (G083 hardening extends to filter):** The filter does NOT silently drop findings on uncertainty. It only drops findings where BOTH conditions are explicitly met. Any finding with a fake-ID phrase but no registered anchor stays active (auditor is flagging an unverified ID, which is legitimate). Any finding with a registered anchor but no fake-ID phrase stays active (auditor is flagging something else about a known ID, which is legitimate). The filter is structurally narrow - it suppresses ONLY the specific failure mode F-0.2.17-W3-001 captures, nothing else.

**Acceptance gate:**
- Run filter against W2's non-RAG audit (the original `audit/W2.json` with the `G081 critical "F-0.2.17-W1-003 does not look real"` finding): finding suppresses, suppressed_findings list contains exactly that one entry with reason `registered_id_flagged_as_fake`. Wait - F-0.2.17-W1-003 wasn't in the registered-references in the non-RAG audit because non-RAG didn't have RAG enrichment. So this test must run against the W2 self-audit-rag artifact (`audit/replay/W2-self-audit-rag.json`, sha `afbc33a3…`) where F-0.2.17-W1-003 IS in the registered-references list as `registered`. Verify the finding suppresses there.
- Run filter against W3's self-audit (`audit/W3.json`, sha `b3a4e2e6…`): three findings present, none should suppress (none have a fake-ID phrase, despite anchor IDs being registered). Active findings count remains 3, suppressed count is 0. This verifies the structural narrowness - the filter doesn't over-suppress.
- Inject synthetic finding `{id: "F-FAKE-1", description: "F-0.2.17-W1-003 looks like a placeholder ID"}` against an audit context with F-0.2.17-W1-003 in registered-references. Verify suppression with the right structured record.
- Inject synthetic finding `{id: "AF-1", description: "F-0.2.17-W9-999 cannot be corroborated"}` against an audit context where F-0.2.17-W9-999 is NOT in registered-references. Verify NO suppression - auditor's flag stays active because the ID is unverified, which is legitimate to flag.
- Filter integration: `aho.council.audit` calls the filter immediately after the model's response is parsed and before the disposition is finalized. The filter modifies the `findings` list in place and adds the `suppressed_findings` field to the output structure.

### D2 - Per-component bricks (10 bricks)

(unchanged from initial W4 plan doc - see acceptance gates per architecture artifact §claw3d coverage)

Components: `aho.dispatcher`, `aho.adversarial`, `aho.workstream`, `aho.secrets_client`, `aho.otel`, `aho.health`, `aho.signal`, `aho.council.audit` (now with filter status visible), `aho.council.triage`, `aho.council.embed + aho.rag` (combined).

**Acceptance gate:** Each brick renders against live OTEL state from a 5-min synthetic load test. Reds on injected fault. Greens during normal operation. `aho.council.audit` brick now also shows filter activity - count of suppressed findings per audit.

### D3 - Materiality four-bucket dashboard surfaces

(unchanged - four bucket surfaces per ADR-0010 + overview comparison)

### D4 - Role-collapse trip-wire brick

(unchanged - single brick rendering `aho.adversarial` OTEL invariant)

### D5 - Materiality comparison surface (with vs without base container)

(unchanged - side-by-side two-column rendering, baseline reconstruction from 0.2.16, post-0.2.17 actuals)

### D6 - Anti-rubber-stamp verification dashboard

**Modified shape:** Three failure-mode surfaces now extends to FOUR, adding the new D1 filter as a hardening surface:

- Nemotron raise-on-malformed (G083 protection on triage).
- Llama confidence-floor lock (rubber-stamp protection on audit).
- Role-collapse trip-wire (W3 D3 / D4 brick).
- **Deterministic post-hoc filter on RAG-aware audit findings** (W4 D1 - registered-ID-flagged-as-fake suppression count, suppressed_findings inspection surface).

Plus overview surface aggregating all four with a single summary state.

**Acceptance gate:** Each surface renders trip-wire / suppression counts from W2/W3/W4 OTEL state. New filter surface shows suppression activity per audit, with drill-down to individual suppressed_findings records (auditable / falsifiable).

### D7 - W4 self-audit with stabilized auditor

(numbered up from initial D6) After D1–D6 land, executor writes preliminary W4 acceptance archive. Llama with RAG enrichment AND post-hoc filter audits it. Disposition at `audit/W4.json`. Halt-and-surface after emit. Drafter reviews pre-sign.

**New acceptance gate vs initial draft:** Self-audit produces no fake-ID-on-registered-anchor findings (filter suppresses any that arise). If the filter surface shows zero suppressions during self-audit (no findings of that shape were generated), great - model is now consistent. If the filter shows non-zero suppressions, that's also fine - filter caught the inconsistency structurally and prevented it from surfacing as a false positive. Either result demonstrates the W4 D1 fix is live.

## Cross-references

- **Architecture artifact:** `aho-base-container-architecture.md` §claw3d, §Materiality measurement protocol, §Anti-rubber-stamp hardening.
- **W3 sealed archives:** `acceptance/W3.json` (sha `9ed9a88a…`), `audit/W3.json` (sha `b3a4e2e6…`), and W3 RAG-replay artifacts. DO NOT MODIFY.
- **F-0.2.17-W2-006 + F-0.2.17-W3-001:** both close at W4 close once the deterministic filter is in place AND verified working against the W2 self-audit-rag persistent false positive. The filter must structurally suppress that specific finding for closure to be valid.
- **F-0.2.17-W3-002 (plan-doc spurious-ID test token):** documentation note only, no code action.
- **W2 OTEL counter signals + W3 audit primitive:** unchanged. W4 reads + extends, never modifies.

## Acceptance archive shape

`artifacts/iterations/0.2.17/acceptance/W4.json`:
- `audit_status: "pending_audit"` at write time, transitions to `pending_drafter_review` after D7.
- Entry per D1–D7.
- `carry_forwards_added` for any new findings.
- `carry_forwards_closed: ["F-0.2.17-W2-006", "F-0.2.17-W3-001"]` if D1 filter verified suppresses the specific F-0.2.17-W1-003 false positive on the W2 self-audit-rag artifact AND no novel false-positive shapes surface during D7.
- `pillar_11_invariant_check: "pass"` with executor-session-log evidence.
- `outstanding_pre_03x_gates` listing F-0.2.17-W1-003.
- `agents_involved` listing drafter, executor, auditor (llama3.2 + RAG + filter).
- Sealed sha recorded.

## Halt-and-surface conditions

- Wall-time > 8h soft, > 10h hard.
- D1 filter fails to suppress the F-0.2.17-W1-003 false positive on the W2 self-audit-rag artifact (filter implementation broken).
- D1 filter over-suppresses on the W3 self-audit (active finding count drops below 3, filter is too aggressive).
- D2 brick rendering fails on >2 components after 3 retries.
- D3 OTEL counter retrieval fails.
- D5 baseline reconstruction produces obviously-wrong numbers.
- D7 self-audit suggests deeper architectural issues with materiality claim.

## Out of scope (deferred)

- ADR-0007 amendment, ADR-0009 secrets broker, ADR-0010 materiality as repo-resident docs → W5.
- Component decomposition + claw3d brick spec as repo-resident → W5.
- 0.2.17 retrospective → W5.
- Token rotation (F-0.2.17-W1-003) → operator-side, pre-0.3.x.
- Secrets-test subcommand removal (F-0.2.17-W1-001) → W5 retrospective or earlier fold-in.
- Container-resident model bundling → 0.3.x.
- tsP3 partial-tier deployment claw3d → 0.3.1.

## Executor prompt

(Lands as separate artifact at `artifacts/iterations/0.2.17/prompts/W4-executor.md`.)
