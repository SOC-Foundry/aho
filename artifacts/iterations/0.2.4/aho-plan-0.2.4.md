# aho Plan — 0.2.4

**Phase:** 0 | **Iteration:** 2 | **Run:** 4
**Theme:** W1 remediation
**Predecessor:** 0.2.3 (W1 failed post-run, see amended run report)
**Design:** `aho-design-0_2_4.md`
**Agent split:** Single-agent Claude Code throughout (small, surgical iteration)

---

## Workstreams

| WS | Surface | Outcome |
|---|---|---|
| W0 | Canonical bumps | 10 artifacts → 0.2.4, userMemories iao decisions list updated |
| W1 | `bin/aho-mcp` patch + canonical list correction | 9-package list, sed fix verified, install clean |
| W2 | Verification harness | New e2e CLI test, new postflight registry check, doctor extension |
| W3 | Gotcha registry | G-fish-set-l + G-mcp-canonical-drift entries |
| W4 | Run report close-out + bundle | Bundle at 0.2.4, postflight green, 0.2.3 amended report archived |

No W5 needed — single-agent run, W4 handles close-out.

---

## W1 — `bin/aho-mcp` patch (the actual patch)

### Step 1: confirm the scoping fix is still in place

```fish
grep "^set" bin/aho-mcp
```

Expected:
```
set -g script_version "0.2.4"
set -g mcp_packages \
```

If `script_version` still says `0.2.3`, bump it manually as part of the W0 canonical bump pass.

### Step 2: replace the package array

The 0.2.3 array has 12 entries. Replace with 9. The cleanest way is to rewrite the block in-place. Below is the exact target block — apply with str_replace or by hand:

**Old block (lines ~7-20):**
```fish
set -g mcp_packages \
    firebase-tools \
    @upstash/context7-mcp \
    firecrawl-mcp \
    @playwright/mcp \
    flutter-mcp \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-github \
    @modelcontextprotocol/server-google-drive \
    @modelcontextprotocol/server-slack \
    @modelcontextprotocol/server-fetch \
    @modelcontextprotocol/server-memory \
    @modelcontextprotocol/server-sequential-thinking
```

**New block:**
```fish
set -g mcp_packages \
    firebase-tools \
    @upstash/context7-mcp \
    firecrawl-mcp \
    @playwright/mcp \
    flutter-mcp \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-memory \
    @modelcontextprotocol/server-sequential-thinking \
    @modelcontextprotocol/server-everything
```

### Step 3: uninstall the dead packages from NZXTcos

```fish
sudo npm uninstall -g \
    @modelcontextprotocol/server-github \
    @modelcontextprotocol/server-slack
```

(google-drive and fetch never installed — nothing to clean up.)

### Step 4: install the new addition

```fish
bin/aho-mcp install
```

Should prompt for sudo once, install `@modelcontextprotocol/server-everything`, and report all 9 already present on the rest.

### Step 5: verify

```fish
bin/aho-mcp list
```

Expected: header `MCP Server Fleet (0.2.4)`, 9 rows, all green `[ok]`.

```fish
bin/aho-mcp doctor
```

Expected: `All 9 MCP servers present. OK.`

---

## W2 — Verification harness

### test_aho_mcp_cli_e2e.fish

Lives at `tests/integration/test_aho_mcp_cli_e2e.fish`. Three assertions:

1. `bin/aho-mcp list` exits 0
2. Output contains `MCP Server Fleet (0.2.4)` (catches the empty-parens regression)
3. Output line count for `[ok]`/`[--]` rows equals 9 (catches the empty-list regression)

### Postflight check: `mcp_canonical_registry_verify`

Runs once per postflight. For each package in `mcp_packages`:
- `npm view <pkg> version` → must return a semver
- Output containing `deprecated` → FAIL
- Exit code non-zero → FAIL

No network = SKIP with WARN (capability gap, not a defect).

### Doctor extension

`bin/aho-mcp doctor` adds a second pass after the installed-vs-missing check that runs the same `npm view` verification locally. Belt-and-suspenders.

---

## W3 — Gotcha registry entries

Two new entries in the gotcha registry (full text in design doc §"The two new gotchas"):

- **G-fish-set-l** — fish `set -l` invisible inside functions, use `set -g` for script-level constants
- **G-mcp-canonical-drift** — canonical package lists must be registry-verified, never written from agent memory

---

## W0 — Canonical bumps

All 10 canonical artifacts bump 0.2.3 → 0.2.4. userMemories iao canonical MCP list updated to the 9-package set. install.fish updated if it references any of the 4 removed packages.

---

## W4 — Close-out

- Bundle generation, postflight green (incl. new registry check)
- Run report `aho-run-0_2_4.md` produced
- Amended `aho-run-0_2_3-amended.md` archived alongside original
- Pending Kyle: manual conductor smoke test (still carried from 0.2.3), git commit + push for both 0.2.3 amended + 0.2.4

---

## Definition of done

- [ ] `bin/aho-mcp list` shows 9 green rows, header reads `(0.2.4)`
- [ ] `bin/aho-mcp doctor` reports all 9 present + registry-verified
- [ ] `bin/aho-mcp install` runs clean, zero 404s, zero deprecation warnings
- [ ] `tests/integration/test_aho_mcp_cli_e2e.fish` exists and passes
- [ ] Postflight `mcp_canonical_registry_verify` exists and passes
- [ ] Gotcha registry contains G-fish-set-l and G-mcp-canonical-drift
- [ ] All 10 canonical artifacts at 0.2.4
- [ ] userMemories iao MCP list reflects the 9-package set
- [ ] Bundle validates clean, postflight 0 FAIL
