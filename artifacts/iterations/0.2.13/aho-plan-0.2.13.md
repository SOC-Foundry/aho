# aho 0.2.13 — Plan Doc

**Theme:** Dispatch-layer repair | **Executor:** Claude Code | **Auditor:** Gemini CLI | **Sessions:** 2

---

## W0 — Setup + Pattern C Prerequisites
**Role:** Setup | **Session:** 1
**Scope:**
- Bump canonicals, version stamps
- Executor health check (claude-code, gemini-cli, ollama, nemoclaw socket, daemons)
- Patch postflight 2-tuple vs 3-tuple ValueError in `src/aho/cli.py` (not architectural — just make it work; robustness deferred to .14)
- Extend schema v3 `agents_involved` to role-tagged: `{agent: str, role: "primary"|"auditor"|"cameo"}`. Update validator, update acceptance.py, update 0.2.12 archives retroactively (read-only migration).
- Document Pattern C audit-loop protocol in `artifacts/harness/pattern-c-protocol.md`: when Gemini audits, what audit produces, how checkpoint advances, halt conditions.
- Select Qwen cameo G083 site from 35 definitive list: smallest blast radius, single file, no cross-module imports. Record selection in W0 acceptance.

**Acceptance:** Postflight exits 0 on `aho iteration postflight`. Schema v3 accepts role-tagged agents_involved. Pattern C protocol doc exists. Cameo site recorded. Baseline regression: clean (10 known failures, no new).
**Auditor:** Gemini verifies postflight clean, schema validates sample role-tagged archive, protocol doc complete.

---

## W1 — GLM Parser Fix
**Role:** Repair | **Session:** 1
**Scope:** Strip markdown fences (```json ... ```) before `json.loads()` in GLM evaluator. On parse failure, raise `GLMParseError`. Remove hardcoded `{score: 8, ship}` fallback. Test pairs: verified-good JSON input, verified-bad markdown-wrapped input, verified-bad malformed input.
**Acceptance:** Parse test pairs all produce expected outcome (real result or raise). No baseline regression. No G083 pattern in new code.
**Auditor:** Gemini re-runs test pairs, confirms raise-path actually raises.

---

## W2 — Nemotron Classifier Fix
**Role:** Repair | **Session:** 1
**Scope:** Raise `NemotronClassifyError` on parse failure in `_classify_impl`. Remove `return categories[-1]` default. Test pairs: good classification, malformed response, connection error.
**Acceptance:** All three test cases produce expected behavior. No baseline regression. No G083 pattern in new code.
**Auditor:** Gemini re-runs test pairs, confirms connection-error path raises not defaults.

---

## W2.5 — Model-Quality Gate (HARD GATE)
**Role:** Gate | **Session:** 1
**Scope:** With W1 and W2 parsers fixed, feed GLM 5 verified-bad evaluation inputs (code with known defects) and Nemotron 5 verified-misrouted classification inputs. Measure: do models produce real negative signal, or rubber-stamp through fixed parsers?
**Halt condition:** If ≥3/5 GLM evaluations ship verified-defective code, OR ≥3/5 Nemotron classifications route verified-misrouted tasks correctly to wrong agent, iteration enters strategic-rescope. Close at W2.5 with substrate-truth report. Nemoclaw decision deferred to 0.2.14+.
**Proceed condition:** Models produce real signal. W3-W10 proceed.
**Auditor:** Gemini independently runs the 10 test inputs, confirms Claude's measurements.

---

## W3 — Nemoclaw Benchmark
**Role:** Measurement | **Session:** 1 or 2
**Scope:** 5 test tasks run two ways: direct Ollama invocation vs Nemoclaw socket dispatch. Measure latency, token cost, correctness. Record in `artifacts/iterations/0.2.13/nemoclaw-benchmark.json`.
**Acceptance:** 5 tasks × 2 paths × 3 metrics captured. No baseline regression.
**Auditor:** Gemini spot-checks 1 task end-to-end, confirms numbers.

---

## W4 — ADR-047 Nemoclaw Decision
**Role:** Decision | **Session:** 2
**Scope:** Write ADR-047 with W3 evidence. Decision: keep, replace with direct Ollama, or hybrid. Include rationale, tradeoffs, migration path if replace/hybrid.
**Acceptance:** ADR-047 exists, references W3 benchmark, decision explicit.
**Auditor:** Gemini reviews ADR for evidence grounding, no opinion-without-data.

---

## W5 — OpenClaw Audit
**Role:** Discovery | **Session:** 2
**Scope:** Same 7-section shape as Qwen/GLM/Nemotron audits in 0.2.12. Produce `openclaw-audit.md`. Status field: operational | gap | unknown.
**Acceptance:** 7 sections complete, status determined.
**Auditor:** Gemini spot-checks audit against live OpenClaw state.

---

## W6 — G083 Tier 1: src/aho/agents/
**Role:** Bulk Repair | **Session:** 2
**Scope:** All G083 definitive sites in `src/aho/agents/`. Per-site commits. Halt on ANY regression.
**Acceptance:** Zero G083 in agents/. baseline_regression_check green after each site.
**Auditor:** Gemini reviews per-site diffs, confirms no G083 reintroduction.

---

## W7 — G083 Tier 2: src/aho/council/
**Role:** Bulk Repair | **Session:** 2
**Scope:** All G083 definitive sites in `src/aho/council/`. Per-site commits. Halt on regression.
**Acceptance:** Zero G083 in council/. baseline clean.
**Auditor:** Gemini reviews diffs.

---

## W8 — G083 Tier 3: Remainder
**Role:** Bulk Repair | **Session:** 2
**Scope:** Remaining definitive sites from 35-site set. Halt on regression.
**Acceptance:** All 35 definitive sites repaired. baseline clean.
**Auditor:** Gemini reviews diffs.

---

## W8.5 — Qwen Cameo
**Role:** Forensics | **Session:** 2
**Scope:** Qwen executes the pre-scoped G083 site from W0. Full acceptance archive. Forensics data (time, context needs, bug-catching) captured for three-executor comparison.
**Acceptance:** Site repaired, archive complete, forensics recorded.
**Auditor:** Gemini audits Qwen's work same as Claude's workstreams.

---

## W9 — G083 Ambiguous Triage
**Role:** Classification | **Session:** 2
**Scope:** Classify 117 ambiguous `except Exception` cases into `artifacts/iterations/0.2.13/g083-ambiguous-classified.json`: safe | G083-class | needs-human-review. Execution deferred to 0.2.14.
**Acceptance:** All 117 classified. File complete.
**Auditor:** Gemini spot-checks 10 random classifications.

---

## W10 — Health Rerun + Close
**Role:** Close | **Session:** 2
**Scope:** Rerun `aho council status`. Verify health ≥50. Retrospective, carry-forwards, v10.66 bundle, Kyle's Notes stub, sign-off sheet.
**Acceptance:** Health measured. All close artifacts present. Bundle 300-500KB.
**Auditor:** Gemini final audit of iteration artifacts.

---

## Workstream Count: 11 (W0, W1, W2, W2.5, W3, W4, W5, W6, W7, W8, W8.5, W9, W10)
Sized for 2 sessions. W2.5 gate may close early.
