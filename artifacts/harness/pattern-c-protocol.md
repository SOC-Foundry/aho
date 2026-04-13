# Pattern C Protocol — aho 0.2.13

**Produced:** W0 | **Status:** Active for 0.2.13

---

## 1. When Gemini Audits

Gemini CLI audits **after** Claude Code writes its acceptance archive for a workstream and **before** the checkpoint advances to `workstream_complete`.

Sequence per workstream:
1. Claude Code executes scope per plan.
2. Claude Code writes acceptance archive to `artifacts/iterations/0.2.13/acceptance/W{N}.json`.
3. Claude Code sets checkpoint status to `pending_audit` (NOT `workstream_complete`).
4. Kyle hands context to Gemini CLI.
5. Gemini CLI reviews the acceptance archive + targeted spot-checks.
6. Gemini CLI writes audit archive (see section 2).
7. Checkpoint advances to `workstream_complete` only after audit.

Claude Code never fires `workstream_complete` in 0.2.13. Kyle or the audit handoff protocol advances the checkpoint.

## 2. What Audit Produces

Gemini CLI writes an audit archive to:
```
artifacts/iterations/0.2.13/audit/W{N}.json
```

Audit archive shape:
- `workstream_id`: e.g. "W0"
- `auditor`: "gemini-cli"
- `timestamp`: ISO 8601
- `acceptance_archive_reviewed`: path to Claude's acceptance file
- `spot_checks_performed`: list of commands/files checked
- `findings`: list of observations (pass, concern, or fail)
- `audit_status`: "audit_complete" | "audit_failed"
- `recommendation`: "advance" | "rework" | "halt"

## 3. How Checkpoint Advances

State machine per workstream:
```
in_progress → pending_audit �� audit_complete → workstream_complete
```

- `in_progress`: Claude Code is executing.
- `pending_audit`: Claude Code finished; acceptance archive written; awaiting Gemini.
- `audit_complete`: Gemini wrote audit archive with `audit_status: "audit_complete"` and `recommendation: "advance"`.
- `workstream_complete`: Checkpoint updated after audit. Kyle signs iteration-level.

If Gemini recommends `"rework"`, the workstream reverts to `in_progress` and Claude re-executes the identified gaps. If Gemini recommends `"halt"`, the iteration enters strategic-rescope.

## 4. Halt Conditions

Gemini halts the workstream (and potentially the iteration) if audit finds any of:

1. **Gaming**: Acceptance archive passes checks via manipulated thresholds, weakened assertions, or manufactured data rather than substantive work (G079).
2. **G083 reintroduction**: New code introduces `except Exception` blocks that return hardcoded positive values (G083).
3. **Acceptance-substance mismatch**: Acceptance archive claims pass but spot-check reveals the claimed behavior does not hold.
4. **Baseline regression**: `baseline_regression_check()` reveals new test failures beyond the 10 known baseline failures in `test-baseline.json`.
5. **Schema drift**: Acceptance archive shape deviates from the strict Pydantic `AcceptanceResult` model without documented rationale (G078).

A halt at any workstream triggers review with Kyle before proceeding. A halt at W2.5 (model-quality gate) triggers iteration-level strategic-rescope per the design doc.
