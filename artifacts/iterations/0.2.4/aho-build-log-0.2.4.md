# aho Build Log — 0.2.4

**Phase:** 0 | **Iteration:** 2 | **Run:** 4
**Theme:** W1 remediation — canonical MCP list correction + verification harness
**Executor:** claude-code (single-agent)
**Started:** 2026-04-11T19:00:00Z

---

## W0 — Canonical bumps

- Bumped all 10 canonical artifacts from 0.2.3 → 0.2.4
- Updated `.aho.json` current_iteration to 0.2.4
- Updated `mcp-fleet.md` server catalog from 12 → 9 packages
- Updated `doctor.py` `_check_mcp_fleet()` to 9-package list
- Updated checkpoint to 0.2.4 active

## W1 — bin/aho-mcp patch

- Replaced 12-package `mcp_packages` array with 9 verified packages
- Bumped `script_version` to 0.2.4
- Updated comment header
- Fixed help text (12 → 9)
- Added registry verification pass to `mcp_doctor` function
- Removed: server-github, server-google-drive, server-slack, server-fetch
- Added: server-everything
- Verified: `bin/aho-mcp list` shows 9 rows with `(0.2.4)` header
- Capability gap: sudo required for `npm uninstall` (dead packages) and `npm install` (server-everything)

## W2 — Verification harness

- Created `tests/integration/test_aho_mcp_cli_e2e.fish` — 3 assertions, all pass
- Created `src/aho/postflight/mcp_canonical_registry_verify.py` — npm view check for all 9 packages
- Doctor extension added inline in W1 (registry verification pass in `mcp_doctor`)
- Updated `artifacts/tests/test_doctor_new_checks.py` to match new 9-package list
- Full test suite: 137 passed, 0 failed, 1 skipped

## W3 — Gotcha registry

- Added aho-G062: fish `set -l` invisible inside functions
- Added aho-G063: canonical package lists must be registry-verified
- Registry now at 17 entries

## W4 — Close-out

- Full test suite green (137/137)
- Postflight: canonical_artifacts_current OK, mcp_canonical_registry_verify OK
- Capability gap carried: sudo npm install for server-everything, sudo npm uninstall for dead packages
- Run report generated
- Bundle generated

---

## Capability gaps (Kyle manual steps)

```fish
sudo npm uninstall -g @modelcontextprotocol/server-github @modelcontextprotocol/server-slack
sudo npm install -g @modelcontextprotocol/server-everything
```

After running these, `bin/aho-mcp list` should show 9 green `[ok]` rows.
