# Pattern C Protocol — aho 0.2.14

**Produced:** W0 0.2.13, patched W0 0.2.14 | **Status:** Active for 0.2.14+

---

## 1. Emitter Table (authoritative)

| Event | Emitter | When |
|-------|---------|------|
| `workstream_start` | Claude Code | At workstream begin. **REQUIRED.** Missing starts = protocol violation. |
| `pending_audit` | Claude Code | After acceptance archive written. Checkpoint advances to `pending_audit`. |
| `audit_complete` | Gemini CLI | After audit archive written. |
| `workstream_complete` | Claude Code | After reading Gemini's audit archive with `audit_result: "pass"` or `"pass_with_findings"`. **Never before `audit_complete` exists.** |

No other agents emit lifecycle events. No event is emitted by both agents.

## 2. When Gemini Audits

Gemini CLI audits **after** Claude Code writes its acceptance archive for a workstream and **before** the checkpoint advances to `workstream_complete`.

Sequence per workstream:
1. Claude Code executes scope per plan.
2. Claude Code writes acceptance archive to `artifacts/iterations/{iter}/acceptance/W{N}.json`.
3. Claude Code sets checkpoint status to `pending_audit` (NOT `workstream_complete`).
4. Claude Code emits `pending_audit`. **Claude STOPS here.**
5. Kyle hands context to Gemini CLI.
6. Gemini CLI reviews the acceptance archive + targeted spot-checks.
7. Gemini CLI writes audit archive (see section 3).
8. Gemini CLI emits `audit_complete`.
9. Claude Code returns in a **fresh session**, reads the audit archive, and emits `workstream_complete`.
10. Checkpoint advances to `workstream_complete`.

### workstream_start requirement (0.2.14 patch)

0.2.13 fired zero `workstream_start` events across all workstreams. This created a gap in lifecycle traceability — event log had complete events but no starts. Starting 0.2.14, `workstream_start` is REQUIRED at workstream begin. Missing starts are a protocol violation to be flagged in audit.

## 3. What Audit Produces

Gemini CLI writes an audit archive to:
```
artifacts/iterations/{iter}/audit/W{N}.json
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

### Audit archive overwrites forbidden (0.2.14 patch)

An audit archive, once written, is immutable. If a re-audit is required (e.g., after rework), Gemini writes a versioned file:
- First audit: `audit/W{N}.json`
- Re-audit: `audit/W{N}-v2.json`
- Further: `audit/W{N}-v3.json`, etc.

This prevents the timestamp coherence risk identified in the 0.2.13 triple-audit session, where batch auditing overwrote per-workstream audit timestamps.

## 4. How Checkpoint Advances

State machine per workstream:
```
in_progress → pending_audit → audit_complete → workstream_complete
```

- `in_progress`: Claude Code is executing. Set by `emit_workstream_start`.
- `pending_audit`: Claude Code finished; acceptance archive written; awaiting Gemini. Set by Claude.
- `audit_complete`: Gemini wrote audit archive with `audit_status: "audit_complete"` and `recommendation: "advance"`. Set by Gemini.
- `workstream_complete`: Claude read audit archive in fresh session and advanced checkpoint. Set by Claude.

If Gemini recommends `"rework"`, the workstream reverts to `in_progress` and Claude re-executes the identified gaps. If Gemini recommends `"halt"`, the iteration enters strategic-rescope.

### Checkpoint update scoping (0.2.14 patch)

`emit_workstream_complete()` and `emit_workstream_start()` MUST only modify the named workstream's state in the checkpoint. Sibling workstream states must be preserved. This was a bug in 0.2.13: emitting a lifecycle event for one workstream corrupted sibling states (W0/W1 reverted to `in_progress`, W3-W6 flipped from `skipped_per_rescope` to `in_progress`). Fixed in 0.2.14 W0.

### Terminal event session requirement (0.2.14 patch, from 0.2.13 carry-forwards)

`workstream_complete` events require a fresh executor session after audit, not an inline emit during the audit session. Claude returns, reads the audit archive, then emits in its own session. This prevents role-crossing (0.2.13 W0 ambiguity where Gemini attempted to emit `workstream_complete`).

## 5. Halt Conditions

Gemini halts the workstream (and potentially the iteration) if audit finds any of:

1. **Gaming**: Acceptance archive passes checks via manipulated thresholds, weakened assertions, or manufactured data rather than substantive work (G079).
2. **G083 reintroduction**: New code introduces `except Exception` blocks that return hardcoded positive values (G083).
3. **Acceptance-substance mismatch**: Acceptance archive claims pass but spot-check reveals the claimed behavior does not hold.
4. **Baseline regression**: `baseline_regression_check()` reveals new test failures beyond the baseline in `test-baseline.json`.
5. **Schema drift**: Acceptance archive shape deviates from the strict Pydantic `AcceptanceResult` model without documented rationale (G078).

A halt at any workstream triggers review with Kyle before proceeding.

## 6. Cautionary Examples (0.2.13)

**W0 role-crossing:** Gemini attempted to emit `workstream_complete` in its audit — this is Claude's terminal event. Corrected in CLAUDE.md after W0 audit identified the ambiguity. The emitter table (section 1) is now authoritative.

**Triple-audit timestamp coherence:** Gemini auditing W1, W2, W2.5 in one session gave all three archives timestamps from the batch session, not per-workstream. The overwrite ban (section 3) prevents this going forward.

**Stale workstream_complete:** During 0.2.13 close reconciliation, a `workstream_complete` event was emitted for W10 before verifying the audit archive existed. The state machine (section 4) is authoritative: `workstream_complete` follows `audit_complete`, not checkpoint status.
