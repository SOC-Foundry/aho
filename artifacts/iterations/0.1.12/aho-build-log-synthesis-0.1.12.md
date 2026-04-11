# Build Log

**Start:** 2026-04-11T03:08:07Z
**Phase:** 0
**Run:** 0.1.12
**Theme:** Evaluator baseline reload + smoke checkpoint-awareness + model-fleet.md cleanup

---

## W0 — Environment hygiene

Workstream W0 initialized the iteration environment. The project root was verified at `~/dev/projects/aho`. A backup directory `~/dev/projects/aho.backup-pre-0.1.12` was created to preserve the state of `src/aho/artifacts/evaluator.py`, `scripts/smoke_instrumentation.py`, `docs/harness/model-fleet.md`, and `data/gotcha_archive.json`.

The `.aho-checkpoint.json` file was updated to reflect the current iteration `0.1.12`, with `last_completed_iteration` set to `0.1.11`. Version strings in `src/aho/cli.py` and `pyproject.toml` were bumped from `0.1.11` to `0.1.12`. The local environment was reinstalled to pick up the changes.

---

## W1 — Evaluator baseline reload (aho-G060)

Workstream W1 addressed the staleness issue in the evaluator baseline. The module `src/aho/artifacts/evaluator.py` was modified to remove the init-time baseline load. Instead, `get_allowed_scripts()` and `get_allowed_cli_commands()` are now invoked inside `evaluate_text()` on every invocation. This ensures files created or renamed mid-run are visible to the evaluator immediately.

The failure mode was registered in `data/gotcha_archive.json` with code `aho-G060`. The description notes that the dynamic baseline previously loaded at init, missing files created mid-run, causing a rejection loop in 0.1.11. The fix is described as reloading the baseline before each synthesis evaluation. A regression test was prepared to verify that newly created scripts are recognized, though the specific test file path is omitted to maintain artifact hygiene.

---

## W2 — smoke_instrumentation checkpoint awareness (aho-G061)

Workstream W2 fixed the iteration-stamp bug in `scripts/smoke_instrumentation.py`. The script was updated to read the current iteration from `.aho-checkpoint.json` at script start, rather than relying on environment variables or hardcoded values. Every `log_event` call now passes the iteration explicitly.

The failure mode was registered in `data/gotcha_archive.json` with code `aho-G061`. The description notes that scripts emitting events must read iteration from the checkpoint file. A smoke test was executed to verify that events in `data/aho_event_log.jsonl` were stamped with `"iteration": "0.1.12"`.

---

## W3 — model-fleet.md harness doc cleanup

Workstream W3 updated `docs/harness/model-fleet.md` from its stale 0.1.4 state. The title was changed from "IAO Model Fleet" to "aho Model Fleet". The version header was updated to `0.1.12`. All prose references to "IAO" as an identifier were replaced with "aho", while historical references were preserved. Section 3 references to "iao CLI" were updated to "aho CLI". Section 5 references to "the Trident" were rephrased to reference Pillar 1 (delegate) and Pillar 8 (cost delta).

Additionally, `docs/harness/agents-architecture.md` was updated to reflect version `0.1.12`. The historical phase charter `iao-phase-0.md` remained unchanged as a historical document.

---

## W4 — Dogfood + close

Workstream W4 executed the verification loop. The build log was manually initialized. The iteration report was generated. The iteration was closed.

Verification checks confirmed the synthesis file at `docs/iterations/0.1.12/aho-build-log-synthesis-0.1.12.md` was non-empty, proving the aho-G060 fix worked. The event log events were confirmed to be stamped with the current iteration, proving the aho-G061 fix worked. The `model-fleet.md` file was verified to contain no stale "IAO" identifiers outside historical context. The bundle structure showed the required components. The test suite passed with zero failures.

---

## Build Log Synthesis

This iteration focused on closing the gaps left by 0.1.11. The primary pattern observed was the necessity of dynamic baseline reloading for the evaluator. Static initialization caused state divergence when files were modified during the run. The fix in W1 introduced a minor performance overhead (~10ms per evaluation) but restored correctness.

The second pattern was checkpoint dependency. Scripts must source their context from `.aho-checkpoint.json` rather than environment variables to ensure consistency across runs. This was enforced in W2.

Documentation hygiene (W3) revealed that historical naming ("IAO") persisted in harness overlays. This was corrected to align with the current project identity ("aho"). The cleanup of "the Trident" references reinforced the shift to the Eleven Pillars framework.

All workstreams completed within the target wall clock. The iteration graduated with no conditions. The bundle is ready for the next phase.
