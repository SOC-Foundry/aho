# 0.2.17 W6 plan doc

**Workstream:** W6 — final code-change closures (F-0.2.17-W1-001 secrets-test removal + F-0.2.17-W4-001 ChromaDB re-index hook)
**Iteration:** 0.2.17
**Phase boundary:** 0.2.17 final workstream. W5 produced ADRs and repo-resident docs. W6 closes the residual code-change carry-forwards, then 0.2.17 closes. After 0.2.17 close: operator runs pre-tsP3 final actions (rotate `ahomw:telegram_bot_token` per F-0.2.17-W1-003) outside the workstream framework. 0.3.1 launches with clean carry-forward state.
**Executor:** Claude Code (`claude --dangerously-skip-permissions`) on NZXTcos.
**Drafter:** Claude web.
**Auditor:** llama3.2 + RAG enrichment + deterministic post-hoc filter — same stabilized primitive.
**Time budget:** 2–4 hours executor wall-time. Hard ceiling 5 hours. Daytime session — operator watching.
**Adversarial Authorship contract:** standard.
**Pre-0.3.x hard gate (recurring reminder):** F-0.2.17-W1-003 — rotate `ahomw:telegram_bot_token`. Operator-side, post-0.2.17. Surface at W6 close. Surface before tsP3 handoff.

---

## Scope

W6 closes two outstanding code-change carry-forwards, both pre-0.3.x hard gates:

1. **F-0.2.17-W1-001 — `aho secrets-test` test-only subcommand removal from production image path.** Replace value-printing path with hash-fingerprint comparison so the broker round-trip can still be verified without exposing decrypted values to caller stdout. Alternative: gate the subcommand behind `AHO_DEV_BUILD=1` env so dev builds retain it, production images do not. Drafter recommends hash-fingerprint approach since it preserves the verification capability without breaking Pillar 11.

2. **F-0.2.17-W4-001 — ChromaDB iteration-context index does not auto-refresh on `carry-forwards-0.2.16.md` updates.** Hook re-index into `aho.gap_carry_forward_writer.append_to_file` so any carry-forward addition triggers a re-index of the source file. Verify: post-W6 audit run sees recently-added carry-forwards as `registered`, not `unverified`.

W6 also runs the final 0.2.17 self-audit and emits the iteration's terminal event.

W6 does NOT include: F-0.2.17-W1-003 token rotation (operator-side, post-0.2.17); 0.3.x partial-tier work; new image build (image rebuild may be required as a side effect of D1 — executor decides scope based on the implementation choice).

## Deliverables

### D1 — F-0.2.17-W1-001 closure: `aho secrets-test` redesign

**Module:** `src/aho/cli.py` (modify) + tests update.

**Shape:** Two implementation paths, executor picks based on cost:

- **Path A (drafter-preferred): Hash-fingerprint comparison.** Modify `secrets-test` subcommand to never print decrypted value. Instead, compute SHA-256 of decrypted value, return first 8 hex chars + value length as fingerprint. Operator on host can run a parallel `get_secret(project, name)` and compute matching fingerprint to verify equivalence. Output format: `{"project": "ahomw", "name": "telegram_bot_token", "fingerprint": "abc12345", "length": 46, "status": "ok"}`. No raw value ever in agent context.

- **Path B (alternative): Gate behind `AHO_DEV_BUILD=1`.** Modify `secrets-test` parser to check env var; if not set, parser returns "unknown command" error. Production images built without `AHO_DEV_BUILD=1` lack the subcommand entirely.

**Drafter recommendation: Path A.** Preserves verification capability without breaking Pillar 11. Path B works but means dev/prod images diverge, which is its own audit-trail problem.

**Acceptance gate:**
- Modified `secrets-test` no longer prints decrypted value. Output is fingerprint-shaped per Path A spec OR subcommand absent per Path B spec.
- Existing W1 D3 acceptance gates 1-4 still pass with the modified subcommand (with adjusted assertions per the new output shape).
- Pillar 11 invariant: agent stdout no longer contains the decrypted value during `aho secrets-test` invocation.
- Image rebuild required: `aho:0.2.17-rc2` (or `aho:0.2.17` if executor decides this is the final tag). Push to ghcr.io, verify pull-clean, healthcheck-clean.
- F-0.2.17-W1-001 closure recorded structurally in W6 acceptance archive `carry_forwards_closed`.

### D2 — F-0.2.17-W4-001 closure: ChromaDB re-index hook

**Module:** `src/aho/gap_carry_forward_writer.py` (modify).

**Shape:** Modify `append_to_file` (or whatever the canonical append entry point is) to trigger ChromaDB re-index of the modified file after the append completes. Re-index path: invoke `aho.rag.index_artifact` (or equivalent) on the file's path with appropriate project + iteration metadata.

Failure handling: if re-index fails (Ollama down, ChromaDB down, etc.), the append still succeeds but a warning is logged + an OTEL counter increments. The append is the load-bearing operation; re-index is best-effort for staleness avoidance.

**Acceptance gate:**
- Modified `append_to_file` triggers re-index post-write.
- Test fixture: append a synthetic carry-forward entry to a tmp copy of `carry-forwards-0.2.16.md`, verify subsequent RAG query for the synthetic ID returns the snippet (not null).
- Live verification: append a real W6-internal-test carry-forward (not a real lesson, just a probe — clearly marked `F-0.2.17-W6-PROBE`), verify RAG query returns it, then remove the probe entry.
- Re-index failure handling: simulate Ollama down, verify append still succeeds, warning logged, OTEL counter increments. Do NOT actually take Ollama down; mock the embed call to raise.
- F-0.2.17-W4-001 closure recorded structurally in W6 acceptance archive `carry_forwards_closed`.

### D3 — Final 0.2.17 self-audit

**Process:** After D1 + D2 land, executor writes preliminary W6 acceptance archive. Llama+RAG+filter audits it. The audit's RAG enrichment should now show recently-added carry-forwards as `registered` (D2 fix verifies live).

**Output:** `audit/W6.json`.

**Acceptance gate:**
- Self-audit disposition lands.
- RAG enrichment shows F-0.2.17-W4-001 + F-0.2.17-W1-001 status as `registered` (or whatever their post-W5/W6 state is). If still `unverified`, D2 didn't actually fix the staleness — halt-and-surface.
- Filter outcome recorded.
- Drafter arbitrates findings before operator signs.

## Cross-references

- **W5 sealed archives**: `acceptance/W5.json`, `audit/W5.json`. DO NOT MODIFY.
- **All prior workstream sealed archives**: W0/W1/W2/W3/W4 + close notes. DO NOT MODIFY.
- **carry-forwards-0.2.16.md**: 39 entries at W5 launch (may be 39 + W5-additions at W6 launch).
- **F-0.2.17-W1-003 (token rotation)**: out of W6 scope, operator post-0.2.17.

## Acceptance archive shape

`artifacts/iterations/0.2.17/acceptance/W6.json`:
- `audit_status: "pending_audit"` at write time, transitions to `pending_drafter_review` after D3.
- Entry per D1–D3.
- `carry_forwards_added`: any new findings.
- `carry_forwards_closed`: F-0.2.17-W1-001, F-0.2.17-W4-001.
- `pillar_11_invariant_check: "pass"`.
- `outstanding_pre_03x_gates`: F-0.2.17-W1-003 (the only remaining post-W6 gate).
- Sealed sha recorded.

## Halt-and-surface conditions

- Wall-time > 4h soft, > 5h hard.
- D1: image rebuild fails or pull-clean post-push fails.
- D2: re-index hook fails to make recent additions queryable.
- D3: self-audit shows W4-001 / W1-001 still as `unverified` or `outstanding`.

## Out of scope (deferred)

- F-0.2.17-W1-003 token rotation → operator-side, post-0.2.17.
- 0.3.x partial-tier work → 0.3.1.

## Executor prompt

(Lands as separate artifact at `artifacts/iterations/0.2.17/prompts/W6-executor.md`.)
