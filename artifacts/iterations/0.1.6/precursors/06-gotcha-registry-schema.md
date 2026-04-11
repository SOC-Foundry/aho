# Investigation 6 — Gotcha Registry Schema and Cross-Project Feasibility

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Current iao Schema

### Top-level structure

```python
type: dict
keys: ['gotchas']
```

The file is a dict with a single `"gotchas"` key containing a list. This is what caused the `AttributeError: 'dict' object has no attribute 'append'` error in the Gemini session — code tried to call `.append()` on the dict itself instead of on `d["gotchas"]`.

### Entry count

13 entries total.

### Entry schema (all keys across first 10 entries)

```
context, id, kjtcom_source_id, mitigation, pattern, symptoms, title
```

### Sample entry

```json
{
  "id": "iaomw-G103",
  "title": "Plaintext Secrets in Shell Config",
  "pattern": "Secrets stored as 'set -x' in config.fish are world-readable...",
  "symptoms": [
    "API keys or tokens visible in shell configuration files",
    "Secrets appearing in shell history or environment snapshots",
    "Risk of accidental exposure during live sessions"
  ],
  "mitigation": "Use iao encrypted secrets store (age + keyring)...",
  "context": "Added in iao 0.1.2 W3 during secrets architecture overhaul."
}
```

### Project code status

- **No `project_code` field** exists on any entry.
- 8 entries have `kjtcom_source_id` (values: G1, G19, G31, G39, G41, G49, G62, G71) — these are the migrated kjtcom entries.
- 5 entries are iao-native (no `kjtcom_source_id`).
- All entries use the `iaomw-G###` id format regardless of origin.

---

## Current kjtcom Schema

### Source file

`~/dev/projects/kjtcom/data/gotcha_archive.json`

### Top-level structure

```python
type: dict
keys: ['schema_version', 'last_updated', 'registry']
```

### Entry count

**0 entries.** The `registry` array is empty.

This is surprising. It suggests either:
1. The kjtcom gotcha data lives elsewhere (e.g., `~/dev/projects/kjtcom/template/gotcha/gotcha_registry.json`)
2. The gotcha archive was created as a schema placeholder and data was never backfilled
3. The gotcha data was consumed during migration and the source was left empty

### Other kjtcom gotcha files found

```
~/dev/projects/kjtcom/template/gotcha/gotcha_registry.json
~/dev/projects/kjtcom/app/build/web/assets/assets/gotcha_archive.json
~/dev/projects/kjtcom/app/build/unit_test_assets/assets/gotcha_archive.json
~/dev/projects/kjtcom/app/assets/gotcha_archive.json
~/dev/projects/kjtcom/app/lib/widgets/gotcha_tab.dart
```

The `template/gotcha/gotcha_registry.json` is likely the source of truth. The `app/assets/gotcha_archive.json` and `app/build/` variants are Flutter app assets — the gotcha data is displayed in the kjtcom app's "Gotcha" tab.

---

## tripledb Status

No `gotcha*` files found in `~/dev/projects/tripledb/`.

---

## Schema Delta

| Field | iao | kjtcom |
|---|---|---|
| Container | `{"gotchas": [...]}` | `{"schema_version": ..., "last_updated": ..., "registry": [...]}` |
| Entry ID format | `iaomw-G###` | `G###` (inferred from `kjtcom_source_id` values) |
| `project_code` | Not present | Not present |
| `title` | Present | Unknown (registry is empty) |
| `pattern` | Present | Unknown |
| `symptoms` | Present (list of strings) | Unknown |
| `mitigation` | Present | Unknown |
| `context` | Present | Unknown |
| `kjtcom_source_id` | Present on migrated entries | N/A |

The kjtcom schema cannot be fully characterized because the `data/gotcha_archive.json` registry is empty. The template/gotcha registry or the Flutter app assets would need inspection to determine the full kjtcom entry schema.

---

## Cross-Project Registry Options

### Option A — Single file with `project_code` field

Add a `project_code` field to each entry in iao's `data/gotcha_archive.json`. All entries from all projects live in one file.

**Structure:**
```json
{
  "gotchas": [
    {
      "id": "iaomw-G103",
      "project_code": "iaomw",
      "title": "...",
      ...
    },
    {
      "id": "kjtco-G001",
      "project_code": "kjtco",
      "title": "...",
      ...
    }
  ]
}
```

**Pros:**
- Simple — one file to query, one index to maintain
- Cross-project queries are trivial (filter by `project_code` or don't)
- Existing code only needs to learn about the `project_code` field
- Consistent with iao's current "everything in one place" philosophy

**Cons:**
- File grows with every project — could become large if many projects feed gotchas
- Merge conflicts if multiple agents write concurrently (not currently a concern in Phase 0)
- Mixes concerns — iao-specific gotchas live alongside kjtcom-specific ones

### Option B — One file per project

Split into `data/gotchas/iaomw.json`, `data/gotchas/kjtco.json`, `data/gotchas/tripl.json` with a merger at query time.

**Structure:**
```
data/gotchas/
├── iaomw.json  — {"gotchas": [...]}
├── kjtco.json  — {"gotchas": [...]}
└── tripl.json  — {"gotchas": [...]}
```

**Pros:**
- Clean separation — each project owns its registry
- Easier to import/export individual project gotchas
- No merge conflicts between projects
- Aligns with the 5-char project code convention

**Cons:**
- Query API needs a merger layer
- Cross-project search requires reading N files
- More file management — creating new project = creating new file
- Current code assumes a single file; needs more refactoring

### Recommendation

**Option A (single file with `project_code` field)** is recommended for 0.1.6 because:

1. **Simplicity.** The current file has 13 entries. Even with all kjtcom gotchas added, we're looking at maybe 100 entries total. A single JSON file handles this easily.
2. **Minimal refactor.** Add `project_code` to each entry, update the append logic to use `d["gotchas"].append(...)` instead of `d.append(...)`, and add a `project_code` parameter to query functions.
3. **Cross-project queries are the common case.** The whole point of the universal gotcha registry is that lessons from one project inform another. Splitting by project and then merging at query time adds complexity for the primary use case.
4. **Phase 0 constraints.** Only one machine, one operator, no concurrent writes. The merge conflict concern doesn't apply yet.

Option B becomes attractive at Phase 1+ if the registry grows beyond ~500 entries or if multiple machines contribute gotchas independently.

---

## Cross-Project Lookup Strategy

**Question:** Auto-include feeding projects always, or only on empty result?

**Recommendation: Always include, with project_code ranking.**

When querying gotchas for project X, return all matching gotchas across all projects but rank results from project X first. Rationale:
- A gotcha from kjtcom ("heredocs break agents") is just as relevant when working on iao
- "Only on empty result" creates a confusing UX where the same query returns different results depending on whether the home project has relevant entries
- Project-specific gotchas that are irrelevant (e.g., "Flutter widget rebuild" when working on iao) can be filtered by the consumer, not the query layer

Implementation: `query_gotchas(text, project_code=None)` returns all matches, sorted by relevance, with `project_code` as a tiebreaker (home project first).
