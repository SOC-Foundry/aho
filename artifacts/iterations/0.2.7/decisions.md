# aho 0.2.7 — Decisions

**Captured:** 2026-04-11
**Source:** Kyle's responses to design doc open questions

---

## 1. Dashboard section priority

**Ship first (must land in 0.2.7):**
- Section 1: System banner (trivial, never defer)
- Section 2: Component coverage matrix (only diagnostic that doesn't exist elsewhere)
- Section 3: Daemon health

**Minimum viable dashboard:** banner + components matrix + daemon health = 3 sections.

**Defer order (cut from end if W4 runs long):**
1. Section 6 (model fleet) — defer first, covered by `bin/aho-models doctor`
2. Section 5 (MCP fleet) — defer second, covered by `bin/aho-mcp list`
3. Section 4 (recent traces) — defer third

**Floor:** If W4 cannot deliver 3 sections, dashboard ships as 0.2.8. 0.2.7 ships backend-only (W1+W2+W3+W5+W6+W7+W8).

## 2. Components audit — fix vs document

**DOCUMENT (do not fix in 0.2.7):**
- chromadb — transitive python dep via pip step 3
- opentelemetry-api/sdk/exporter — transitive python deps
- All python_module entries — install transitively with the package

**FIX:**
- brave-integration — real configuration step, W5 wires it via orchestrator.json
- Any external_service declared but not installable from install.fish (predicted: zero)
- Any agent/daemon in components.yaml but not in bin/aho-systemd install list (predicted: zero)

**Document policy:** each "document" row gets one-line "installed via: pip transitive" note. Not a TODO, not a defect.

## 3. Brave token entry — interactive prompt

Use interactive prompt. Token is short, single-line, low risk.

`bin/aho-secrets-init --add-brave-token` flow:
1. Prompt: "Paste Brave Search API key (input hidden):"
2. Read with `stty -echo`
3. Validate: non-empty, length check
4. Encrypt to fernet store under key `brave_search_token`
5. Update `~/.config/aho/orchestrator.json` to reference the key
6. Print: "Brave Search token stored. Verify with: bin/aho-secrets-init list"
7. Exit 0

Test path: `printf 'fake_token_value\n' | bin/aho-secrets-init --add-brave-token`

## 4. Engine field — reserved metadata only

0.2.7 writes, reads, and validates the field. No behavior changes. Default: "gemini".

orchestrator-config.md must include verbatim:
> engine: reserved field, no behavior in 0.2.7. See ADR-XXX (future) for activation timeline.

## 5. Scope cut policy

**Cut order (first thing cut first):**
1. Dashboard sections 4, 5, 6 (traces, MCP, models)
2. W4 entirely (Flutter UI) — ship backend-only with curl+jq
3. W6/W7/W8 carry-forwards stay regardless

**Do not cut:**
- W2 audit (foundational deliverable)
- W3 install.fish gap fixes (audit payoff)
- W5 brave token wiring (real user value)
- W6/W7/W8 carry-forwards (already deferred from 0.2.5)

**Floor for 0.2.7:** W0+W1+W2+W3+W5+W6+W7+W8+W9. Dashboard UI (W4) is the only optional piece.

**Hard stop:** If floor cannot ship in one pass, halt at end of W3, ship what landed, name rest as 0.2.8 carry-forward.
