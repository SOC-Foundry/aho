# aho Design — 0.2.4

**Phase:** 0 | **Iteration:** 2 | **Run:** 4
**Theme:** W1 remediation — canonical MCP list correction + verification harness
**Predecessor:** 0.2.3 (W1 failed post-run verification — see `aho-run-0_2_3-amended.md`)

---

## Why this iteration exists

0.2.3 shipped `bin/aho-mcp` with two independent defects:

1. **Fish scoping bug** — `set -l` at script scope made the package list invisible to functions. The wrapper printed an empty fleet and the installer was a no-op. Test suite did not catch it because no test exercised the CLI end-to-end.
2. **Unvalidated canonical list** — 2 of 12 packages 404 on npm; 2 more are deprecated. The list was written from memory and never round-tripped against the registry.

0.2.4 fixes both, hardens the harness against recurrence, and updates every place the canonical list lives so iao decisions, the wrapper, and the docs all agree.

This is a remediation iteration. No new features. No scope creep. Conductor smoke test, MCP/HyperAgents work, and Riverpod 2→3 stay where they are.

---

## Goals

1. `bin/aho-mcp list` enumerates a canonical, registry-verified set of MCP packages.
2. `bin/aho-mcp install` installs all of them cleanly with zero 404s and zero deprecation warnings.
3. Postflight catches future canonical-list drift automatically.
4. The 0.2.3 defects are captured as gotchas so they cannot recur silently.
5. The amended 0.2.3 run report is the historical record; 0.2.4 closes it out.

## Non-goals

- Replacement servers for github/slack/google-drive/fetch — separate ADR, not this iteration.
- Conductor smoke test — still pending Kyle, not 0.2.4 scope.
- MCP/HyperAgents integration in kjtcom — separate, larger scope.
- Any new feature work in W2/W3/W4 surfaces.

---

## The corrected canonical list (9 packages)

All 9 verified present on the npm registry as of 2026-04-11:

```
firebase-tools
@upstash/context7-mcp
firecrawl-mcp
@playwright/mcp
flutter-mcp
@modelcontextprotocol/server-filesystem
@modelcontextprotocol/server-memory
@modelcontextprotocol/server-sequential-thinking
@modelcontextprotocol/server-everything
```

**Removed (will not be reinstalled):**
- `@modelcontextprotocol/server-google-drive` — archived, no first-party replacement
- `@modelcontextprotocol/server-fetch` — Python-only (`uvx mcp-server-fetch`)
- `@modelcontextprotocol/server-github` — moved to `github/github-mcp-server` (Go binary)
- `@modelcontextprotocol/server-slack` — deprecated, no current replacement

**Added:**
- `@modelcontextprotocol/server-everything` — reference/test server, useful as conductor smoke target

`server-git` is a candidate but deferred to the same ADR that handles fetch/github/slack/gdrive — don't add it half-validated.

---

## The two new gotchas

### G-fish-set-l: fish `set -l` is invisible inside functions

Fish functions do not inherit local variables from the enclosing script scope. Any constant declared at the top of a fish script that needs to be read by a function inside the same script must use `set -g` (global), not `set -l` (local).

**Detection:** A function reading the variable sees it as empty. Loops over it iterate zero times. No error is raised.

**Fix pattern:** `set -g` for all script-level constants consumed by functions in the same file.

**Where it bit us:** `bin/aho-mcp` 0.2.3, both `script_version` and `mcp_packages`.

### G-mcp-canonical-drift: canonical package lists must be registry-verified

Any deliverable that includes a "canonical list of external packages" must include a registry verification step in its definition of done. Lists written from agent memory are stale on arrival — the MCP server ecosystem in particular reorganizes faster than any model's training cutoff.

**Detection:** `npm view <pkg> version` returns 404 or `npm install` emits deprecation warnings.

**Fix pattern:** Postflight runs `npm view` against every entry in the canonical list. Any 404 or deprecation flips a postflight check from OK to FAIL (not WARN — these are hard correctness issues).

**Where it bit us:** `bin/aho-mcp` 0.2.3, 2 of 12 packages 404, 2 of 12 deprecated.

---

## Verification harness changes

1. **New test: `test_aho_mcp_cli_e2e.fish`** — shells out to `bin/aho-mcp list`, asserts the header contains the version string in parens, asserts the row count equals the declared package count. This is the test that would have caught Defect 1 in the run, not after.

2. **New postflight check: `mcp_canonical_registry_verify`** — for each package in `mcp_packages`, runs `npm view <pkg> version` and asserts it returns a version (not 404). Fails the check on any 404 or deprecation. Adds ~5 seconds to postflight; worth it.

3. **Doctor extension:** `bin/aho-mcp doctor` already verifies installed-vs-missing. Add a second pass that runs the registry verification locally for the same defense-in-depth.

---

## What stays the same

- World A install model (global `sudo npm install -g`)
- `bin/aho-mcp` subcommand surface (`list | status | doctor | install`)
- iao secrets model (age + OS keyring)
- Phase 0 cadence and bundle structure
- Everything in W2/W3/W4 from 0.2.3 ships unchanged

---

## Open questions for Kyle before plan-doc execution

None. The scope is fully constrained by what 0.2.3 broke. Plan doc proceeds straight to workstream layout.
