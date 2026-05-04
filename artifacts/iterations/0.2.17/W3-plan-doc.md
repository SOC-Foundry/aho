# 0.2.17 W3 plan doc

**Workstream:** W3 — auditor-RAG integration (load-bearing fix from F-0.2.17-W2-006)
**Iteration:** 0.2.17
**Phase boundary:** 0.2.17 ships base container on NZXTcos. W0–W2 produced the substrate; W3 closes the auditor-capability gap surfaced by W2's self-audit and replay disagreements. W4 layers materiality dashboard surfaces and per-component claw3d bricks. W5 consolidates ADRs and runs retrospective.
**Executor:** Claude Code (`claude --dangerously-skip-permissions`) on NZXTcos.
**Drafter:** Claude web (Kyle's project folder, persistent).
**Auditor:** llama3.2 in-container, via `aho.council.audit` — same seat as W2, but THIS workstream extends the auditor's prompt construction with pre-prompt RAG enrichment. Bootstrap test 4: does RAG-augmented auditor produce materially different findings than RAG-less auditor on the same artifacts?
**Time budget:** 2–4 hours executor wall-time. Hard ceiling 5 hours. Daytime session — operator (Kyle) is watching.
**Adversarial Authorship contract:** Drafter drafts. Executor implements. Auditor (llama3.2 with RAG enrichment) audits. Drafter reviews disposition pre-sign. Operator signs.
**Pre-0.3.x hard gate carry-forward (recurring reminder):** F-0.2.17-W1-003 — rotate `ahomw:telegram_bot_token`. Surface at W3 close. Surface at W4 close. Surface at W5 close. Surface before tsP3 handoff.

---

## Scope

W3 closes F-0.2.17-W2-006 (auditor reference-resolution gap) by extending `aho.council.audit` prompt construction with pre-prompt RAG enrichment. Before sending the audit prompt to llama3.2, the harness:

1. Scans the audit target for reference-shaped tokens (carry-forward IDs, ADR refs, gotcha refs, finding IDs).
2. Queries `aho.rag` for each detected reference against the project's iteration-context collection.
3. Injects retrieval results as a "registered references" context section in the audit prompt.
4. Llama audits with explicit context on which IDs are registered, what they mean, and what their dispositions are.

W3 also runs a comparison bootstrap test: re-runs the W0, W1, W2 audit replays from W2's D9/D10/D11 with the new RAG-enriched auditor and compares findings to the original W2 disposition. If the RAG-enriched auditor stops flagging the false-positives that W2's audit produced (F-W0-004 "not corroborated," F-0.2.17-W1-003 "looks placeholder," etc.), the architecture's materiality claim has its first hard evidence point.

W3 does NOT include: claw3d brick rendering (W4); materiality four-bucket dashboard surfaces (W4); per-component bricks (W4); ADR documents (W5).

## Deliverables

### D1 — Reference-token detection in audit target

**Module:** `src/aho/council/audit_ref_extract.py` (new).

**Shape:** Scan audit target text for reference-shaped tokens via regex. Match patterns:
- Carry-forward IDs: `F-\d+\.\d+\.\d+-W\d+-\d+`, `F-W\d+-\d+`, `F-host-\d+`, `W\d+-AF\d+`
- Audit finding IDs: `AF\d+`, `AF-\d+\.\d+\.\d+-W\d+-\d+`
- ADR references: `ADR[\s-]?\d+`, `ADR \d{4}`
- Gotcha references: `G\d+`, `Sec\d+`
- Deliverable IDs: `D\d+`, `B\d+\.\d+`

Returns a deduplicated list of detected references with their detected kind. Raises on malformed input (empty target, non-string).

**Acceptance gate:**
- Against W0 acceptance archive: detects all references known to be present (F-0.2.17-W0-001 through F-0.2.17-W0-005, AF003, ADR 0007, ADR 0008, B2.3, etc.). Spot-check via grep + manual count.
- Against W1 acceptance archive: detects F-0.2.17-W1-001/002/003, AF-0.2.17-W1-001/002/003, etc.
- Against W2 acceptance archive: detects F-0.2.17-W2-001/002/003/006, F-0.2.17-W1-003 (referenced in pre-0.3.x gates).
- Empty input raises `RefExtractError`.

### D2 — RAG retrieval per detected reference

**Module:** `src/aho/council/audit_ref_lookup.py` (new).

**Shape:** For each detected reference from D1, query `aho.rag` against the project's iteration-context collection with the reference ID as query text. Returns top-k matches with metadata (source_iteration, source_workstream, source_artifact_path, snippet, score). k=3 per reference. Coalesces results across references — single dedup'd retrieval set with reference-IDs annotated per result.

If a reference produces zero retrievals, mark it as `unverified` in the output. The auditor will treat `unverified` references as "should flag for verification, not auto-flag as fake."

**Acceptance gate:**
- Against W0 audit target: F-0.2.17-W0-003 retrieval returns the actual carry-forward entry text from `carry-forwards-0.2.16.md` line 485 region.
- Against W2 audit target: F-0.2.17-W1-003 retrieval returns the W1 acceptance archive's Pillar 11 incident entry. F-W0-004 retrieval returns 0.2.16 W4 carry-forward closure context.
- Spurious reference (intentionally fake test ID `F-FAKE-9.9.9-W9-999`) returns `unverified` with empty retrieval set, not a false positive match.

### D3 — Pre-prompt RAG enrichment in audit prompt construction

**Module:** `src/aho/council/audit.py` (modify existing).

**Shape:** In the audit-prompt construction path (currently builds system + user message blocks), insert a new context section between system and user blocks: `"## Registered references retrieved from project context"`. Content is the formatted output of D2 — for each detected reference: ID, kind, top-1 retrieval snippet (truncated to 200 chars), source artifact path, registered status (`registered | unverified`).

If detected reference list is empty, omit the context section entirely (don't pad the prompt with empty headers).

Update audit prompt rules to reference the new context section explicitly: "Before flagging any reference ID as 'not real' or 'placeholder,' check the Registered references section above. If the ID appears there with `registered` status, do NOT flag it. If it appears with `unverified` status, flag for verification rather than as fake."

Token budget: keep enrichment under 5K tokens to leave headroom in the 32K context window. If detected references > 30, truncate to top-30 by retrieval score.

**Acceptance gate:**
- Audit prompt construction against W0 acceptance archive includes the registered-references section with ≥10 entries.
- Audit prompt construction against synthetic input with zero references omits the section entirely.
- Token count of constructed prompt remains under 28K (leaving 4K for response generation).

### D4 — Replay W2's D9, D10, D11 audits with RAG enrichment

**Process:** Re-run the three W2 audits using the new RAG-enriched audit primitive against the same sealed targets (acceptance/W0.json + amendment, acceptance/W1.json, acceptance/W2.json). Output llama dispositions to new paths (do NOT overwrite W2's sealed replay artifacts).

**Output paths:**
- `audit/replay/W0-llama-rag.json` (RAG-enriched W0 audit replay)
- `audit/replay/W1-llama-rag.json`
- `audit/replay/W2-self-audit-rag.json`
- `audit/replay/comparison-rag-vs-non-rag.json` (structural comparison: did RAG enrichment change the dispositions, finding counts, or false-positive rate?)

**Acceptance gate:**
- Three RAG-enriched audits produce dispositions.
- Comparison artifact records: per-replay disposition match/mismatch with non-RAG audit; per-replay finding count delta; per-replay novel-findings (RAG version found things non-RAG missed, or vice versa); per-replay false-positive resolution (did RAG version stop flagging F-W0-004, F-0.2.17-W1-003, etc. as not-real?).
- **The materiality claim is testable here.** If RAG enrichment resolves the false positives (auditor no longer flags real IDs as fake), F-0.2.17-W2-006 is closed and W3's load-bearing thesis is validated. If RAG enrichment fails to resolve them (llama still pattern-matches and ignores the registered-references section), the architectural fix doesn't work and W3 surfaces a deeper issue.

Disagreement-handling: if RAG-enriched audits produce *substantively different* dispositions from non-RAG audits in a way that suggests one is wrong (e.g., RAG version says clean, non-RAG version found a real Pillar 11 violation), executor halt-and-surfaces — this is a cross-audit disagreement that needs drafter arbitration before W3 closes.

### D5 — W3 self-audit with RAG enrichment

**Process:** After D1–D4 land, executor writes preliminary W3 acceptance archive at `acceptance/W3.json` with `audit_status: "pending_audit"`. Llama with RAG enrichment audits the W3 acceptance archive itself. Disposition lands at `audit/W3.json`.

W3 self-audit is the loop-closure test: does the auditor that W3 just upgraded correctly audit W3's own work? Bootstrap test 4 in the architecture artifact's progression.

**Acceptance gate:**
- W3 self-audit disposition lands.
- Drafter reviews disposition pre-sign in chat.
- Same disposition options as W2: `clean | halt | surface_to_drafter`. Confidence floor 0.85 still locks `clean` below threshold.
- If self-audit produces false-positive findings about W3's own carry-forward references (the same shape that motivated W3 in the first place), that's a hard fail — RAG enrichment didn't actually fix the problem.

## Cross-references

- **Architecture artifact:** `aho-base-container-architecture.md` — RAG-as-context-feed for auditor seat per §Component decomposition (`aho.rag` feeds context to triage and audit).
- **F-0.2.17-W2-006:** auditor reference-resolution gap. **W3 closes this carry-forward.**
- **W2 sealed archives:** `acceptance/W2.json` (sha `4a5ab02b…`), `audit/W2.json` (sha `b9c2f1bb…`). DO NOT MODIFY.
- **W2 sealed replay archives:** `audit/replay/W0-llama.json`, `W0-comparison.json`, `W1-llama.json`, `W1-comparison.json`. DO NOT MODIFY. New replay artifacts land at new paths (`-rag.json` suffix).
- **`aho.rag`:** the W2 D1 implementation. W3 builds on it; does not modify.
- **`aho.council.audit`:** the W2 D4 implementation. W3 modifies the prompt-construction path only — the audit primitive's structure (confidence floor, disposition shape, etc.) is untouched.
- **G001/G022/G081/G083/Pillar 11:** unchanged.

## Acceptance archive shape

`artifacts/iterations/0.2.17/acceptance/W3.json`:
- `audit_status: "pending_audit"` at write time, transitions to `pending_drafter_review` after D5 emits.
- One entry per D1–D5.
- `carry_forwards_added` for any new findings (likely zero unless D4 surfaces something).
- `carry_forwards_closed: ["F-0.2.17-W2-006"]` if D4 confirms RAG enrichment resolved the reference-resolution false positives.
- `pillar_11_invariant_check: "pass"` with executor-session-log evidence.
- `outstanding_pre_03x_gates` listing F-0.2.17-W1-003 (token rotation) per recurring protocol.
- Sealed sha recorded.

## Halt-and-surface conditions

- Wall-time crosses 4 hours (soft warning) or 5 hours (hard ceiling).
- D2 RAG retrieval against W2 ChromaDB collection fails reproducibly (Ollama connection drop, ChromaDB index missing).
- D4 surfaces a substantive cross-audit disagreement between RAG-enriched and non-RAG dispositions.
- D5 self-audit produces false-positive ID-validation findings (RAG enrichment didn't fix the problem).
- Token budget for enriched prompt exceeds 28K (truncation logic broken).

## Out of scope (deferred)

- claw3d brick rendering → W4.
- Materiality four-bucket dashboard surfaces → W4.
- Per-component bricks → W4.
- Role-collapse trip-wire brick rendering (the OTEL signal already emits per W2 D5; W4 wires it to the brick) → W4.
- ADR documents (ADR-0007 amendment, ADR-0009, ADR-0010) → W5.
- Component decomposition doc + claw3d brick spec as repo-resident → W5.
- Token rotation (F-0.2.17-W1-003) → operator-side, pre-0.3.x hard gate.
- Secrets-test subcommand removal (F-0.2.17-W1-001) → W5 retrospective or earlier fold-in.

## Executor prompt

(Lands as separate artifact at `artifacts/iterations/0.2.17/prompts/W3-executor.md` after this plan doc is reviewed.)
