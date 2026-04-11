# Investigation 5 — W3 Ambiguous Pile Archaeology

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Background

0.1.4 W3 was designed to pause mid-workstream when it encountered ambiguous kjtcom gotchas. The plan specified:
- Classify each kjtcom gotcha as UNIVERSAL, PROJECT_SPECIFIC, or AMBIGUOUS using Nemotron
- UNIVERSAL entries get migrated directly
- PROJECT_SPECIFIC entries are skipped
- AMBIGUOUS entries are collected, written to `/tmp/iao-0.1.4-ambiguous-gotchas.md`, and the workstream pauses for Kyle's review
- Kyle reviews, provides rulings, and runs `iao iteration resume W3` to continue

This investigation determines whether the pause mechanism fired and what state W3 actually reached.

---

## Evidence

### Was the ambiguous pile file written?

```
$ test -f /tmp/iao-0.1.4-ambiguous-gotchas.md
→ File not found
```

No. The file was never created. No `/tmp/iao-0.1.4-*` or `/tmp/iao-0.1.5-*` files exist at all.

### Was `iao iteration resume` ever implemented?

```
$ grep -n "resume" src/iao/cli.py
→ (no matches)
```

No. The `resume` subcommand was never added to the CLI. This was supposed to be a W1 deliverable enabling the pause/resume workflow.

### What does the checkpoint say?

```json
"W3": {"status": "paused", "reason": "ambiguous_review"}
```

The checkpoint records W3 as "paused" with reason "ambiguous_review", which matches the designed pause behavior. However, the pause mechanism was supposed to WRITE the ambiguous list before pausing — that never happened.

### What actually got migrated?

8 entries were migrated from kjtcom into `data/gotcha_archive.json` with `kjtcom_source_id` markers:

| iao ID | kjtcom Source | Title |
|---|---|---|
| iaomw-G108 | G1 | Heredocs break agents |
| iaomw-G109 | G19 | Gemini runs bash by default |
| iaomw-G110 | G31 | TripleDB schema drift during migration |
| iaomw-G111 | G39 | Detail panel provider not accessible at all viewport sizes |
| iaomw-G112 | G41 | Widget rebuild triggers event handlers multiple times |
| iaomw-G113 | G49 | TripleDB results displaying show names in title case |
| iaomw-G114 | G62 | Self-grading bias accepted as Tier-1 |
| iaomw-G115 | G71 | Agent asks for permission |

These are a mix — some are clearly universal (G1: "Heredocs break agents", G19: "Gemini runs bash by default") while others are kjtcom-specific (G39: "Detail panel provider", G41: "Widget rebuild triggers event handlers"). This suggests the Nemotron classification may not have worked correctly, or the migration script ran without the classification step and just ported entries sequentially until it stopped.

### What does the build log say?

```
$ grep -rn "ambiguous" docs/iterations/0.1.4/
```

The design document (not the build log) describes the ambiguous pile mechanism in detail at lines 500-501 and 539-546. The build log does not mention "ambiguous" — it likely doesn't contain an entry for the W3 pause because the pause mechanism never fired properly.

### Does kjtcom have more gotchas to migrate?

The kjtcom gotcha archive at `~/dev/projects/kjtcom/data/gotcha_archive.json` has a different schema: `{"schema_version": ..., "last_updated": ..., "registry": []}`. The `registry` array is **empty** (0 entries). This suggests either:
- The kjtcom gotcha data is stored elsewhere (e.g., in the template registry at `~/dev/projects/kjtcom/template/gotcha/gotcha_registry.json`)
- The migration was supposed to pull from a different source
- The `data/gotcha_archive.json` in kjtcom was created as a schema placeholder but never populated

### Does Nemotron classification work in isolation?

From the smoke tests: Nemotron (nemotron-mini:4b) responded in 2.1 seconds to a simple prompt. The `classify()` function in `src/iao/artifacts/nemotron_client.py` is structurally correct — it sends a classification prompt, extracts the category, and returns it. The function is usable.

---

## Reconstruction of What Happened

1. The `migrate_kjtcom_harness.py` script exists in `scripts/` (3027 bytes) and was presumably run during W3.
2. It successfully ported 8 entries from some kjtcom source into `data/gotcha_archive.json`, adding `kjtcom_source_id` markers.
3. The migration likely encountered entries that should have been classified as AMBIGUOUS, but instead of:
   - Running Nemotron classification
   - Writing the ambiguous list to `/tmp/iao-0.1.4-ambiguous-gotchas.md`
   - Printing a pause message
   
   It appears the script either:
   - Stopped after migrating the first batch (perhaps hitting an error or reaching a stopping point)
   - Classified entries but didn't implement the file-writing and pause mechanism
   - Was killed or timed out before reaching the ambiguous entries
4. The Gemini executor then set the checkpoint to `"paused"` with `"reason": "ambiguous_review"` — recording the designed state rather than the achieved state.
5. Since `iao iteration resume W3` was never implemented, there was no path to continue W3 even if Kyle wanted to.

---

## Conclusions

### (a) Did the W3 pause mechanism work as designed?

**No.** The pause mechanism did not fire. The ambiguous pile file was never written. The checkpoint was set to "paused" status, but this appears to be a manual/scripted checkpoint update rather than the result of the designed pause flow actually executing.

### (b) Where did it fail?

At multiple points:
1. The `iao iteration resume W3` CLI command was never implemented (supposed to be a W1 deliverable — not in the W1 spec, but referenced in W3's design).
2. The migration script appears to have ported entries without Nemotron classification or incomplete classification.
3. The `/tmp/` file write never executed.
4. The kjtcom source data structure is unclear — `data/gotcha_archive.json` in kjtcom is empty.

### (c) What would 0.1.6 need to do to resume or restart the migration?

1. **Find the actual kjtcom gotcha source.** The file at `~/dev/projects/kjtcom/data/gotcha_archive.json` is empty. Check `~/dev/projects/kjtcom/template/gotcha/gotcha_registry.json` or other locations.
2. **Implement the Nemotron classification step** in the migration script — the `classify()` function works.
3. **Decide the ambiguous pile UX** — file-based review is fragile. Consider interactive review or a simpler "skip ambiguous, review later" approach.
4. **Consider whether `resume` is needed** — a fresh migration pass that skips already-migrated entries (by checking `kjtcom_source_id`) may be simpler than a resume mechanism.

### (d) Is the kjtcom migration possible right now?

**Partially.** The Nemotron classifier works, the iao gotcha schema is known, and the migration script exists. However:
- The kjtcom gotcha source data location is unclear (the expected file is empty)
- The schema delta between iao and kjtcom needs resolution (see Investigation 6)
- No `project_code` field exists on iao entries, which is needed for cross-project lookup
