# Retrospective — aho 0.2.13

**Phase:** 0 | **Iteration:** 0.2.13 | **Executor:** claude-code (drafter) | **Auditor:** gemini-cli
**Theme:** Dispatch-layer repair
**Status:** Rescoped at W2.5 (Path A). 4 workstreams delivered, 7 skipped, 1 close.
**Execution model:** Pattern C (Claude drafts, Gemini audits, Kyle signs)

---

## §1 What was planned

11 workstreams plus a hard gate at W2.5, organized in a trident:

- **Prong 1 (W0-W5):** Surgical fixes — setup, GLM parser repair, Nemotron classifier repair, model-quality gate, Nemoclaw benchmark, OpenClaw audit
- **Prong 2 (W6-W9):** G083 bulk repair — 35 definitive sites across agents/, council/, and remainder, plus 117 ambiguous site triage
- **Prong 3 (W8.5-W10):** Forensics + close — Qwen cameo, health rerun, retrospective

The design acknowledged from the start that W2.5 was a hard gate: if models rubber-stamped through fixed parsers, the iteration would close early. The plan allocated two sessions and sized for the early-close possibility.

Success criterion: council health ≥50/100 (from 35.3).

## §2 What was delivered

**W0 — Setup + Pattern C Prerequisites** (pass_with_findings)
- VERSION bumped to 0.2.13 across 6 canonical files
- Postflight 2-tuple ValueError patched in cli.py line 287
- Schema v3 AgentInvolvement Pydantic model: normalizes bare strings to `{agent, role: "primary"}`, supports "primary"|"auditor"|"cameo"
- Pattern C protocol documented in `artifacts/harness/pattern-c-protocol.md`
- Qwen cameo site scoped: `src/aho/workstream_gate.py:24` (_read_proceed_awaited)
- Baseline: 13 known failures, 0 new
- Finding: postflight exit code 1 at iteration start (expected — missing artifacts)
- Finding: baseline grew from 10→13, all 3 additions justified as pre-existing environment dependencies

**W1 — GLM Parser Fix** (pass)
- `GLMParseError(Exception)` added to evaluator_agent.py
- `_strip_markdown_fences()` helper handles ```json, bare ```, partial-wrap, whitespace
- Hardcoded `{score: 8, recommendation: ship}` fallback removed — parse failures now raise
- 3 new test cases, 2 existing tests updated to expect GLMParseError
- Baseline: 13 known, 0 new

**W2 — Nemotron Classifier Fix** (pass)
- `NemotronParseError(Exception)` and `NemotronConnectionError(Exception)` added to nemotron_client.py
- Both `categories[-1]` fallback returns removed
- Blanket `except Exception` replaced with specific `requests.ConnectionError`, `requests.HTTPError`, `requests.Timeout`
- 3 new test cases
- Disclosed pre-existing G083 site at `nemotron_client.py:164` (`_call()`) — out of W2 scope
- Baseline: 13 known, 0 new

**W2.5 — Model-Quality Gate** (pass_with_findings)
- **GLM result:** 5/5 inputs produced GLMParseError. 4 timeouts at 180s, 1 malformed JSON at 105s. The one response that completed contained real analysis (identified G083 defect in raw text) but used the wrong JSON schema. GLM-4.6V-Flash-9B at Q4_K_M is non-functional as a structured-output evaluator.
- **Nemotron result:** 10 inputs tested. 8/10 raw model responses were "feature" regardless of input content. 2/10 raised NemotronParseError (correct on empty responses). Model has severe feature-bias — effectively defaulting rather than classifying.
- **Gate decision:** Proceed (neither halt condition technically tripped), but substrate quality findings are severe enough to trigger Path A rescope. Parsers are honest (W1, W2 work). Models cannot produce usable signal through honest parsers.
- Baseline: 13 known, 0 new. 2 tests newly passing (environment-specific).

## §3 What was skipped and why

**W3 (Nemoclaw Benchmark), W4 (ADR-047 Nemoclaw Decision), W5 (OpenClaw Audit), W6 (G083 Tier 1: agents/), W7 (G083 Tier 2: council/), W8 (G083 Tier 3: remainder), W8.5 (Qwen Cameo), W9 (G083 Ambiguous Triage)** — all skipped per Path A rescope decision.

The trigger: W2.5 substrate findings. The iteration's design premised that fixing parsers (W1, W2) would restore honest signal from the dispatch layer. That premise was half-right: parsers are now honest, but the models behind them cannot produce usable structured output. GLM times out 80% of the time and produces wrong-schema JSON the other 20%. Nemotron returns "feature" 80% of the time regardless of input.

Running W3-W9 on top of non-functional substrate would produce meaningless data:
- W3 Nemoclaw benchmark would measure dispatch of a non-functional evaluator
- W4 ADR-047 would decide on dispatch architecture for a non-functional classifier
- W6-W8 G083 bulk repair would fix exception handling around models that can't respond
- W9 ambiguous triage would classify exception sites in code paths that never complete

The rescope preserves these as carry-forwards for 0.2.14, where the model viability question must be addressed first.

## §4 Pattern C trial

0.2.13 was the first iteration using Pattern C: Claude Code as primary drafter, Gemini CLI as auditor, Kyle as signer.

**What worked:**
- Role separation was clean from W1 onward. Claude drafted, Gemini audited, neither crossed into the other's function. Audits were substantive — Gemini's W2.5 audit independently confirmed the substrate findings rather than rubber-stamping.
- State machine discipline improved after W0. The protocol doc (written in W0) defined the checkpoint lifecycle clearly: `in_progress → pending_audit → audit_complete → workstream_complete`.
- Audit overhead was lower than budgeted. Design estimated ~20min per workstream × 11 workstreams = 3.5hr. Actual: 4 audits averaging 13min = ~52min total. Audits were lightweight verification, not re-execution.

**What didn't work:**
- W0 had role-crossing: Gemini attempted to emit `workstream_complete` in its audit, which is Claude's terminal event. Corrected in CLAUDE.md after W0 audit identified the ambiguity.
- Terminal events (`workstream_complete`) require a fresh Claude session to fire after audit. This adds friction — four separate session entries were needed just for checkpoint hygiene. The protocol doc should specify this requirement explicitly.
- Triple-audit session (Gemini auditing W1, W2, W2.5 in one run) created audit archive timestamp coherence risk. All three archives got timestamps from the batch session, not from the original per-workstream audit window. No data loss occurred, but the risk was unnecessary.
- `workstream_start` events were never emitted for any workstream. The event log has complete events but no start events, creating a cosmetic gap in the lifecycle record.

**Comparison to 0.2.12 single-agent:**
- 0.2.12 (Gemini-primary, 9 workstreams, discovery theme): Gemini executed and self-reviewed. Found G083 pattern natively. No audit overhead, no state machine coordination. Total execution was one continuous session with per-workstream review.
- 0.2.13 (Pattern C, 4 delivered workstreams, repair theme): Two-agent coordination added ~52min audit time and ~4 hygiene sessions. The audits caught one real finding (W0 role-crossing) and confirmed substance on the other three. Quality-per-workstream was comparable. Overhead was modest but non-zero.
- Pattern C's value proposition depends on workstream count. At 4 delivered workstreams, the overhead-to-value ratio is acceptable. At the planned 11, it would have been more significant.

## §5 Substrate findings

This is the headline of the iteration.

**GLM-4.6V-Flash-9B at Q4_K_M quantization:**
- 4/5 evaluation inputs timed out at 180s with no response
- 1/5 responded at 105s with text that correctly identified the G083 defect ("Exception handling uses pass to mask failures") — but delivered it in the wrong JSON schema (`defects` array instead of `score/issues/recommendation`)
- The model has evaluation capability buried in its text output, but cannot deliver structured JSON within any reasonable timeout at this quantization level
- The evaluator agent is non-functional as currently configured

**Nemotron-mini:4b:**
- 8/10 classification inputs returned "feature" regardless of input content
- 2/10 returned empty responses (correctly caught by NemotronParseError)
- The model has severe feature-bias — it is not classifying, it is defaulting
- The propose_gotcha pipeline has been routing nearly everything to the "feature" bucket
- Model behavior is non-deterministic across runs: same inputs produce different (but equally useless) outputs

**What this means:**
- The dispatch layer can no longer silently lie (W1, W2 achieved this)
- The dispatch layer also cannot help — the models behind the honest parsers are non-functional or near-non-functional
- Council health remains 35.3/100 — unchanged from 0.2.12. The parsers are fixed but the health score reflects member operational status, which hasn't changed
- The 0.2.14 model viability question supersedes everything: heavier quantization (Q8_0?), different model entirely (Qwen-as-evaluator?), or architectural pivot away from local LLM evaluation

## §6 Casing-variant design question

W2.5 surfaced a design edge case in Nemotron classification: the model occasionally returns casing variants of valid categories ("Gotcha" instead of "gotcha", "gotch" instead of "gotcha").

Post-W2 parser behavior:
- "Gotcha" → case-insensitive substring match → would return "gotcha" (correct)
- "gotch" → substring too short to match "gotcha" → NemotronParseError (arguably correct, arguably over-strict)

This needs a Kyle decision before 0.2.14 planning:
1. Soft-match: normalize to lowercase and accept fuzzy substring matches (permissive)
2. Strict: any non-exact match raises NemotronParseError (current behavior for "gotch")
3. New category: register casing variants as a diagnostic category for model quality monitoring

The decision affects how the classifier parser handles model non-determinism generally.

## §7 Coaching/process notes

- **Rescope honesty worked.** The W2.5 gate was designed as an early-close trigger and it triggered. The iteration closed at the gate rather than pushing through meaningless workstreams. This is the harness working as intended.
- **Checkpoint hygiene is manual overhead.** Terminal events required separate sessions. The workstream_start events were never emitted. Checkpoint reconciliation was a dedicated hygiene step. Consider automating checkpoint lifecycle in the harness for 0.2.14.
- **Audit archive batching is a protocol gap.** The triple-audit session worked but creates timestamp coherence risk. Protocol should specify one audit per session, or explicitly document batch-audit timestamp semantics.
- **Baseline stability is a strength.** 13 known failures, 0 new across all 4 workstreams. The test-baseline.json ledger and baseline_regression_check() are working as designed.
- **Parser fixes are durable.** GLMParseError and NemotronParseError are structurally sound. When models eventually produce real output, the parsers will handle it correctly. The investment in W1 and W2 is not wasted — it's infrastructure for when the substrate improves.
