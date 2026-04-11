# aho Plan — 0.2.7

**Phase:** 0 | **Iteration:** 2 | **Run:** 7
**Theme:** Visibility + carry-forward closeout
**Predecessor:** 0.2.6 (live-fire hardening, closed clean)
**Design:** `aho-design-0_2_7.md`
**Agent split:** Single-agent Claude Code throughout. Larger surface but coherent — dashboard, audit, and carry-forwards all touch related state surfaces.

---

## Workstreams

| WS | Surface | Outcome |
|---|---|---|
| W0 | Canonical bumps + decisions captured | 10 artifacts → 0.2.7, decisions.md from open questions |
| W1 | Dashboard backend aggregator | `bin/aho-dashboard` extended: `/api/state` JSON endpoint aggregating component, daemon, trace, MCP, model state |
| W2 | components.yaml coverage audit | `components-coverage.md` matrix, gaps named, fix-or-document decisions per row |
| W3 | install.fish gap fixes | Any new install.fish steps from W2 audit (likely 0–3 small additions) |
| W4 | Flutter dashboard UI | `web/claw3d/` Flutter Web app, 6 sections, polls `/api/state` every 5s, geist typography, trident palette |
| W5 | Orchestrator config + brave token | `~/.config/aho/orchestrator.json` schema, `bin/aho-secrets-init --add-brave-token`, fernet entry, openclaw + nemoclaw read config on startup |
| W6 | OTEL aho.tokens scalar fix | `set_attrs_from_dict` helper, 6 call site updates, unit test, aho-G064 |
| W7 | Evaluator score parser fix | Scale detection, raw field preservation, unit tests |
| W8 | Conductor smoke subcommand | `bin/aho-conductor smoke`, file marker task, span window assertion, aho-G065 |
| W9 | Close | Tests, postflight, bundle, run report, build log, changelog |

9 workstreams. Slightly smaller than 0.2.5 because the carry-forwards W6/W7/W8 are well-scoped from prior planning.

---

## Workstream details

### W0 — Bumps + decisions

- All 10 canonical artifacts → 0.2.7
- `.aho.json` `current_iteration` → 0.2.7
- `artifacts/iterations/0.2.7/decisions.md` captures Kyle's answers to design open questions:
  - Dashboard section priority order if cuts are needed
  - Components audit fix-vs-document policy per gap class
  - Brave token entry flow (interactive prompt vs capability gap)
  - Engine field reserved-vs-active
  - Iteration scope cut policy

### W1 — Dashboard backend aggregator

- Extend `bin/aho-dashboard` with HTTP server (Python `http.server` or `aiohttp` if already a dep)
- Endpoint `/api/state` returns single JSON document:
  ```
  {
    "system": { iteration, phase, run_type, last_close },
    "components": [ ... from components.yaml + verification status ],
    "daemons": [ ... from systemctl is-active + heartbeat freshness ],
    "traces": [ ... last 20 from event log ],
    "mcp": [ ... from bin/aho-mcp list cache ],
    "models": [ ... from bin/aho-models doctor ]
  }
  ```
- Endpoint `/` serves static files from `web/claw3d/build/web/`
- CORS headers for localhost only
- Polling-friendly: cache responses for 2s to avoid hammering downstream commands
- Tests: each section returns valid JSON, /api/state aggregates all 6 sections, static file serving works

### W2 — components.yaml coverage audit

- Parse `components.yaml` (88 entries)
- For each entry, identify install source (which install.fish step or wrapper installs it)
- For each entry, run kind-appropriate verification:
  - python_module → import check
  - mcp_server → `bin/aho-mcp list` membership
  - external_service → component-specific (chromadb dir, ollama daemon, etc.)
  - agent → systemd is-active or socket
  - llm → `ollama list` membership
- Produce `artifacts/iterations/0.2.7/components-coverage.md` markdown table
- For each gap (verified missing or unknown), mark fix or document per W0 decision
- Output is itself a deliverable, not just a working file

### W3 — install.fish gap fixes

- Apply fixes from W2 for any gaps marked "fix"
- Likely candidates based on prior analysis:
  - Explicit chromadb declaration in step 3 if W2 confirms transitive dep is fragile
  - opentelemetry exporter explicit declaration (same pattern)
  - Any other surprises from the audit
- All changes additive — install.fish step structure unchanged
- Re-run install.fish on NZXTcos to confirm idempotency holds

### W4 — Flutter dashboard UI

- Initialize `web/claw3d/` Flutter Web project (or extend existing placeholder)
- Six sections per design doc, top to bottom
- Stack: Flutter Web, Geist Sans/Mono, trident palette
- Single-page, no routing
- Polls `/api/state` every 5s via HTTP
- Read-only — no buttons that mutate
- Build output goes to `web/claw3d/build/web/`, served by W1 backend
- Tests: widget tests for each section, mock /api/state response
- Build artifact: `flutter build web` runs clean, no analyze warnings

### W5 — Orchestrator config + brave token

- Schema for `~/.config/aho/orchestrator.json` documented in `artifacts/harness/orchestrator-config.md`
- `bin/aho-secrets-init --add-brave-token` subcommand: prompt for token, encrypt to fernet store under key `brave_search_token`, update orchestrator.json reference
- `src/aho/agents/openclaw.py` reads orchestrator.json on startup, falls back to defaults if missing
- `src/aho/agents/nemoclaw.py` same pattern
- Default config written by `bin/aho-secrets-init` if missing
- Tests: config parsing, brave token encryption round-trip, default fallback

### W6 — OTEL aho.tokens scalar fix

- Locate OTEL span emission (grep for `set_attribute.*aho.tokens` first; fall back to `src/aho/logger.py` if no direct hits)
- Add `set_attrs_from_dict(span, prefix, d)` helper at the emission site
- Replace 6 known call sites: qwen-client, nemotron-client, glm-client, openclaw, nemoclaw, telegram
- Unit test: emit a span with the helper using a token dict, assert no stderr `Invalid type dict` errors
- Add aho-G064 to gotcha_archive.json
- Verify with `journalctl --user -u aho-nemoclaw --since "5 min ago" | grep "Invalid type"` returning zero hits after restart

### W7 — Evaluator score parser fix

- File: `src/aho/agents/roles/evaluator.py`
- Add scale detection: if score ≤ 1.0, multiply by 10
- Preserve `raw_score` and `raw_recommendation` fields in output dict
- Update existing tests if any assert old broken behavior
- New unit tests: GLM 0–1 input, Qwen 0–10 input, malformed input

### W8 — Conductor smoke subcommand

- Add `smoke` subcommand to `bin/aho-conductor`
- Implementation: generate marker filename, dispatch deterministic task, poll for completion, assert file exists + content correct + ≥7 spans in event log within timestamp window
- Cleanup: rm marker file after assertion
- Exit 0 on full pass, exit 1 with diagnostic on failure
- Add aho-G065 to gotcha_archive.json
- Test: shell out to `bin/aho-conductor smoke`, assert exit 0

### W9 — Close

- Full test suite green (target: 155+ tests, up from 143)
- Bundle generation, postflight green
- New postflight gates:
  - `dashboard_present` — assert `web/claw3d/build/web/index.html` exists
  - `components_coverage_present` — assert `components-coverage.md` exists for current iteration
  - `orchestrator_config_present` — assert `~/.config/aho/orchestrator.json` exists OR is documented as user-supplied
- Run report `aho-run-0_2_7.md`
- Build log `aho-build-log-0_2_7.md`
- CHANGELOG entry for 0.2.7
- Pending Kyle (carry to manual):
  - Run `install.fish` on NZXTcos as round-trip after W3 fixes
  - Visit `http://127.0.0.1:7800/` to verify dashboard renders
  - Eventually run `install.fish` on P3 (still 0.3.x scope)
  - Git commit + push 0.2.7

---

## Definition of done

- [ ] All 10 canonical artifacts at 0.2.7
- [ ] `bin/aho-dashboard` serves `/api/state` JSON and `/` static files
- [ ] `web/claw3d/` Flutter app builds clean and renders 6 sections
- [ ] Dashboard reachable at `http://127.0.0.1:7800/` after `bin/aho-dashboard start`
- [ ] `components-coverage.md` exists with all 88 components mapped
- [ ] All gaps from W2 either fixed in install.fish or documented
- [ ] `orchestrator.json` schema documented
- [ ] `bin/aho-secrets-init --add-brave-token` works end-to-end
- [ ] OTEL `Invalid type dict` errors gone from nemoclaw and conductor logs
- [ ] Evaluator returns correct normalized scores + preserves raw values
- [ ] `bin/aho-conductor smoke` exits 0 with verifiable file marker + 7-span trace
- [ ] aho-G064 + aho-G065 in gotcha registry (21 total)
- [ ] 3 new postflight gates pass
- [ ] Test suite green (155+ tests)
- [ ] install.fish still completes all 9 steps idempotently after W3 fixes
- [ ] Bundle validates clean

---

## Risk register

- **Scope size:** 9 workstreams again. W4 Flutter dashboard is the longest pole and the most likely to slip. Mitigation: if W4 runs long, ship 0.2.7 with the backend (W1) + audit (W2) + carry-forwards (W6–W8) and defer the Flutter UI to 0.2.8. The backend alone is useful — `curl http://127.0.0.1:7800/api/state | jq` is a valid (if ugly) dashboard substitute and gets Kyle the visibility he asked for.
- **Audit surprises:** W2 may surface 5+ gaps instead of the predicted 0–3. Mitigation: Kyle's W0 decision sets the fix-vs-document policy globally; W3 just executes. Don't let surprises trigger re-planning.
- **Brave token interactive prompt:** stdin prompts inside fish wrappers historically have edge cases. Mitigation: test with `printf 'token\n' | bin/aho-secrets-init --add-brave-token`.
- **Dashboard polling vs daemon load:** 5s polling × 6 sections × 88 components could hammer downstream commands. Mitigation: W1 caches /api/state for 2s.

---

## Out of scope

- P3 clone-to-deploy (still 0.3.x or later)
- Dashboard authentication, multi-user, websockets
- Replacing bin/aho-dashboard skeleton (extending it, not replacing)
- kjtcom anything
- MCP fetch/github/slack/google-drive replacement ADR (still separate)
- Telegram bot interactive token entry beyond what 0.2.6 already shipped
- Engine-driven behavior changes — orchestrator.json `engine` field is reserved metadata for 0.2.7
