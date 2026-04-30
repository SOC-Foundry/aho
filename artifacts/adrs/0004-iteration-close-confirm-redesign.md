# ADR 0004 — `aho iteration close --confirm` Redesign

**Status:** Proposed (design only; implementation deferred to 0.2.16 W4)
**Date:** 2026-04-21
**Iteration of record:** aho 0.2.16 W0 (bonus — scope-appropriate design, implementation out of W0 budget)
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal — iteration-close state machine.

---

## Context

Two problems surfaced during the 0.2.15 close-out work and are carried into this ADR:

### Problem 1 — `aho iteration close --confirm` is a stub

`src/aho/cli.py:212-237` implements `aho iteration close`. The `--confirm` branch:

```python
if args.confirm:
    report_path = iter_dir / f"{prefix}-run-{iteration}.md"
    from aho.feedback.prompt import validate_signoff
    ok, missing = validate_signoff(report_path)
    if not ok:
        print(f"Sign-off incomplete: {', '.join(missing)}")
        sys.exit(1)
    print(f"Iteration {iteration} confirmed and closed.")
```

What this does:
- Reads `iteration` from `.aho.json` field `current_iteration`.
- Validates the sign-off sheet's checkbox state.
- Prints a success line.

What it does **not** do:
- Write any checkpoint mutation.
- Update `.aho.json` (`current_iteration` stays wherever it was).
- Emit any event (no `iteration_close`, no `iteration_complete`).
- Advance anything.

Consequence: Kyle observed `--confirm` printing `"Iteration 0.2.14 confirmed and closed"` even when the checkpoint was at 0.2.16. The `.aho.json` `current_iteration` field was stale (value `"0.2.14"`, `last_completed_iteration` `"0.2.13"`) — two iterations behind reality. The command printed that stale value and exited zero.

The non-`--confirm` branch (`cli.py:238-326`) is the real close committer — tests, bundle, report, postflight, `.aho.json` update via `update_last_completed`, checkpoint `status=closed`, `last_event=close_complete`. This is inverted semantics: the presence of `--confirm` should commit; its absence should dry-run.

### Problem 2 — Sign-off sheet has Kyle ticking checkboxes manually

The 0.2.15 sign-off sheet (`artifacts/iterations/0.2.15/sign-off-0.2.15.md`) lists per-workstream acceptance gates with `[ ]` / `[x]` checkboxes. Kyle manually edits the file to tick each box after verifying evidence. The close-confirm stub above checks those box states (via `validate_signoff`) before printing.

Pillar 1 (delegate everything delegable): the orchestrator's minutes are spent on judgment, scope, and novelty. Mechanical verification — "do all workstreams have a `pass`/`pass_with_findings` audit archive" — is not judgment work. It is mechanical work that should run locally without human checkbox-ticking.

### The count-drift recurrence

As a downstream consequence of the manual sign-off pattern, count drift creeps in. 0.2.15 W4's Gemini audit surfaced AF001: the sign-off claimed 21 carry-forwards, the footer of `carry-forwards-0.2.15.md` claimed 25, actual count was 27. Three different numbers in three places, all kept in sync by hand. The count coherence checker is now a standing Gemini audit step (GEMINI.md §Specific audit focus → count-coherence check), but the root-cause fix is to stop hand-maintaining the counts.

## Decision (design only)

Redesign `aho iteration close --confirm` so that:

1. `--confirm` is the **committing** verb and the only path that mutates state. Without `--confirm`, the command dry-runs.
2. The commit path reads acceptance and audit archives **directly** — no sign-off checkbox evaluation.
3. Pass/fail is asserted on the archives — every workstream must have an `acceptance/W{N}.json` with `audit_status` that points to an `audit/W{N}.json` (or `audit/W{N}-v{k}.json` if re-audited) with `audit_result ∈ {pass, pass_with_findings}`.
4. `.aho.json.current_iteration` and `last_completed_iteration` are advanced atomically with the checkpoint transition. The `last_completed_iteration` bump currently done by `update_last_completed(iteration)` is retained; `current_iteration` is advanced to the next iteration value as part of the same write (or explicitly deferred to a separate `aho iteration advance` command if preferred).
5. An `iteration_complete` event is emitted to the event log, carrying a manifest of the workstreams, their acceptance/audit references, and the count of carry-forwards (sourced from `carry-forwards-{iteration}.md` parse). The event payload is the canonical count; sign-off / bundle / carry-forwards file footers all **read** from this event instead of maintaining parallel copies.
6. Pillar 11 is preserved: Kyle triggers the close command. No agent runs it autonomously. The close command's authority is delegated *validation*, not *commission*.

### Proposed state machine

```
iteration_active
    │
    ├── workstreams all at "workstream_complete" ──→ close_ready
    │
close_ready
    │  (Kyle invokes: aho iteration close)          ──→ close_dry_run
    │     reports: gate state per workstream
    │     does: nothing mutative
    │
    │  (Kyle invokes: aho iteration close --confirm) ──→ close_commit
    │     reads: acceptance/W{N}.json + audit/W{N}.json for all N
    │     asserts: every audit_result ∈ {pass, pass_with_findings}
    │     runs: tests, bundle build, mechanical report, postflight
    │     writes: .aho.json (current_iteration advance + last_completed)
    │     writes: .aho-checkpoint.json (status=closed, last_event=iteration_complete)
    │     emits: iteration_complete event with workstream manifest
    │
    └── iteration_closed
```

### Sign-off-sheet disposition

The sign-off sheet becomes a **record**, not a gate. It continues to exist (bundled for human-readable iteration close review) but is generated post-close from the audit archives. The `[x]` boxes can be auto-ticked from the audit results, or the format can be simplified to a status summary without boxes. Either way, Kyle's role shifts from tick-the-boxes to approve-or-reject the **command invocation**. The keys-holding (Pillar 11) stays with Kyle; the hand-ticking (Pillar 1 violation) is removed.

### Count-of-carry-forwards single source of truth

Parse `carry-forwards-{iteration}.md` at close-commit time, count the bullet items, write the number into the `iteration_complete` event payload. Bundle generator, sign-off renderer, and any downstream consumer **read** this number from the event — never recount independently. AF001 goes away because only one count exists.

## Consequences

### Positive

- No more "prints 0.2.14 regardless of state" — the `--confirm` path actually commits state.
- No more manual checkbox-ticking — Pillar 1 violation removed.
- Count drift (AF001) goes away structurally.
- `.aho.json` / checkpoint drift detected on close — if `current_iteration` disagrees with the checkpoint at close time, the command halts and surfaces the discrepancy rather than silently advancing.

### Negative

- Behavior change for `--confirm`. Users (Kyle) have to adapt; today's muscle memory has the verb meaning "validate signoff and print." It will mean "validate archives and commit."
- Sign-off sheet changes role. Bundle consumers that look for checkboxes need to adapt.

### Neutral

- `validate_signoff` function at `aho.feedback.prompt` can be removed or repurposed for the dry-run reporting.

## Implementation plan

**Target:** 0.2.16 W4 close package (deliverable assembly is the natural moment because the close command is exercised).

**Steps:**

1. Rewrite `cmd_iteration` `close` branches in `src/aho/cli.py`:
   - `--confirm` performs the commit (archive reading, assertion, tests, bundle, report, `.aho.json` update, checkpoint write, event emit).
   - No-`--confirm` prints the dry-run report (what would be committed, what's missing, what's ready).
   - Sign-off file validation is optional (report it, don't gate on it).
2. Add `emit_iteration_complete(iteration, workstreams, carry_forward_count)` to `aho/workstream_events.py` (new function alongside existing start/complete helpers).
3. Update `bundle` generator to read carry-forward count from event log, not from footer text.
4. Update `render_summary` to read from event log.
5. Unit tests: dry-run path reports correctly on partially-closed iterations; `--confirm` fails cleanly when any audit is missing or `fail`; `--confirm` commits and emits event when all audits pass.
6. Refactor sign-off sheet template to be a post-close record (remove gating role). If retained as a bundle artifact, render from audit archives.

## Alternatives considered

- **Just fix `--confirm` to also commit** (minimal change). Rejected: leaves the sign-off checkbox gating in place, which is the Pillar 1 violation Kyle flagged.
- **Add a separate `aho iteration advance` command** for the current-iteration bump. Considered; can be added as a follow-on once the close-commit machinery is stable. Not a blocker for the main redesign.
- **Require `--confirm` to pass the iteration value on the command line** (e.g., `aho iteration close 0.2.16 --confirm`). This guards against `.aho.json.current_iteration` drift surfacing as a silent wrong-iteration close. Recommended addition to the above plan; cost is low.

## Filing

This ADR stands on its own. The corresponding finding in the W0 acceptance archive is **F-W0-002** — `aho iteration close --confirm` is a stub. The finding records the symptom and points here for the redesign; the redesign lands in W4 per this plan.

## References

- `src/aho/cli.py:212-326` — current close implementation.
- `.aho.json` — `current_iteration` field (observed stale at 0.2.14 during W0).
- `artifacts/iterations/0.2.15/sign-off-0.2.15.md` — current manual-checkbox format.
- `artifacts/iterations/0.2.15/audit/W4.json` — AF001 count-drift finding that motivated §Count-of-carry-forwards single source of truth.
- GEMINI.md §Specific audit focus → count-coherence check — the compensating control that the single-source-of-truth design removes the need for.
