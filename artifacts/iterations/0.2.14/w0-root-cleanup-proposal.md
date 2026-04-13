# Root Directory Cleanup Proposal — 0.2.14 W0

**Status:** PROPOSAL ONLY — Kyle reviews and approves before any mv/rm executes.

---

## Inventory (all top-level files at repo root)

### Canonical (KEEP)

| File | Purpose |
|------|---------|
| CLAUDE.md | Executor instructions (claude-code) |
| GEMINI.md | Auditor instructions (gemini-cli) |
| README.md | Project README |
| VERSION | Iteration version stamp |
| MANIFEST.json | File manifest with checksums |
| pyproject.toml | Python package config |
| .gitignore | Git ignore rules |
| .aho.json | Project config |
| .aho-checkpoint.json | Iteration checkpoint state |
| install.fish | Active install script |
| CHANGELOG.md | Iteration changelog |
| COMPATIBILITY.md | Compatibility notes |
| docker-compose.otel.yml | OTEL stack compose |
| .mcp.json | Machine-local MCP config (gitignored, generated) |
| .mcp.json.tpl | MCP config template |
| projects.json | Multi-project config |

### Scratch from Prior Iterations (MOVE to `artifacts/iterations/0.2.12/scratch/`)

All files below have mtime 2026-04-12 (0.2.12 iteration). No `src/` or `artifacts/tests/` imports found. Only references are in historical bundle docs (aho-bundle-0.2.3.md, aho-bundle-0.2.12.md, etc.) — these are path mentions in MANIFEST snapshots, not functional dependencies.

**patch_*.py (19 files):**

| File | Size |
|------|------|
| patch_acceptance.py | 2,120 |
| patch_aggregator_test.py | 860 |
| patch_all.py | 3,933 |
| patch_baseline.py | 2,199 |
| patch_baseline2.py | 2,001 |
| patch_baseline3.py | 1,347 |
| patch_baseline_regex.py | 615 |
| patch_cli.py | 1,454 |
| patch_cli_postflight.py | 854 |
| patch_cli_w8.py | 1,637 |
| patch_glm_inventory.py | 722 |
| patch_inventory.py | 562 |
| patch_inventory_paths.py | 1,320 |
| patch_lines.py | 1,979 |
| patch_mcp_inventory.py | 1,340 |
| patch_nemotron_inventory.py | 1,036 |
| patch_run_report.py | 1,882 |
| patch_run_report_2.py | 1,203 |
| patch_server.py | 755 |
| patch_server_w7.py | 1,036 |

**run_acceptance_w*.py (7 files):**

| File | Size |
|------|------|
| run_acceptance_w2.py | 2,181 |
| run_acceptance_w3.py | 1,677 |
| run_acceptance_w4.py | 2,180 |
| run_acceptance_w5.py | 2,005 |
| run_acceptance_w6.py | 1,780 |
| run_acceptance_w7.py | 2,529 |
| run_acceptance_w8.py | 1,724 |

**Install script backups (2 files):**

| File | mtime | Size |
|------|-------|------|
| install.fish.v10.66.backup | 2026-04-08 | 2,126 |
| install-old.fish | 2026-04-08 | 2,126 |

### Stray (ADD to .gitignore)

| File | Reason |
|------|--------|
| firebase-debug.log | Firebase CLI debug output, 144KB, grows over time. Should not be tracked. |

---

## Proposed Actions

1. **Create** `artifacts/iterations/0.2.12/scratch/` directory
2. **Move** all 19 `patch_*.py` files to `artifacts/iterations/0.2.12/scratch/`
3. **Move** all 7 `run_acceptance_w*.py` files to `artifacts/iterations/0.2.12/scratch/`
4. **Move** `install.fish.v10.66.backup` and `install-old.fish` to `artifacts/iterations/0.2.12/scratch/`
5. **Add** `firebase-debug.log` to `.gitignore`
6. **Do NOT delete** any files — moves only, preserving history in iteration scratch dirs

**Total:** 28 files moved, 1 .gitignore entry added, 0 files deleted.

## Verification Performed

- `grep -rl` confirmed no `src/` imports of any scratch file
- `grep -rl` confirmed no `artifacts/tests/` imports of any scratch file
- All bundle-doc references are historical MANIFEST path listings, not functional
- All scratch files have 2026-04-12 mtime (0.2.12 iteration window)
- `install.fish.v10.66.backup` and `install-old.fish` have 2026-04-08 mtime (pre-0.2.10)
