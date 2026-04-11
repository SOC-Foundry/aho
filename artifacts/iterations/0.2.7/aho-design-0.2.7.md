# aho Design — 0.2.7

**Phase:** 0 | **Iteration:** 2 | **Run:** 7
**Theme:** Visibility + carry-forward closeout — flutter dashboard, install.fish coverage audit, orchestrator config, three deferred 0.2.5 defects
**Predecessor:** 0.2.6 (live-fire hardening, closed clean)

---

## Why this iteration exists

0.2.6 proved install.fish runs end-to-end on NZXTcos. What it didn't prove is that *every component declared in components.yaml is actually installed by some step in install.fish*. Right now there's no way to see this — Kyle's exact words: "I can't tell because I don't have a dashboard lol." That's not a joke; it's the diagnostic. The system has 88 declared components, 4 daemons, 9 MCP packages, 4 models, an OTEL pipeline, ChromaDB, age + fernet secrets, and an event log. Verifying state today requires running 6+ separate commands and reading the output by eye. That's the problem 0.2.7 fixes.

0.2.7 has three goals that share a theme of *visibility into the installed system*.

**Primary: build the flutter dashboard.** The `web/claw3d/index.html` placeholder from 0.2.3 W3 finally gets a real implementation. The dashboard contract (`dashboard-contract.md` #10) was defined in 0.2.3 but never built against. 0.2.7 builds the consumer. The dashboard reads from the OTEL pipeline (`bin/aho-dashboard` already serves traces.jsonl as JSON from 0.2.3 W3) and renders component status, daemon health, recent traces, and component coverage against components.yaml. This is the artifact that lets Kyle answer "what's installed and running" with one glance.

**Secondary: install.fish completion audit.** Produce a coverage matrix that maps every entry in `components.yaml` to the install.fish step that installs it. Identify gaps. Fix gaps. ChromaDB is the canonical example: it's listed as `external_service active` and `data/chroma/` exists, but no install.fish step explicitly installs it. Either install.fish picks it up via the python pip step (chromadb is a python dep) or it doesn't and that's a real gap. The audit produces a deliverable matrix as part of the iteration record.

**Tertiary: orchestrator config + three 0.2.5 carry-forwards.** Configure openclaw and nemoclaw with engine selection (gemini) and search token (brave). Close out the three defects deferred from 0.2.5 plan: OTEL `aho.tokens` dict serialization, evaluator score parser, conductor `smoke` subcommand. These are bundled together because they're individually small and they all touch surfaces 0.2.7 is already exercising via the dashboard and audit work.

---

## Goals

1. Flutter dashboard at `web/claw3d/` renders live component status, daemon health, recent traces, and components.yaml coverage. Reads from existing OTEL/event log pipeline. No new backend infrastructure.
2. `components.yaml` coverage matrix produced as iteration deliverable. Every component mapped to its installer. Gaps named and either fixed or documented as known capability gaps.
3. install.fish gains any missing component install steps surfaced by the audit (likely 0–3 small additions).
4. openclaw and nemoclaw have configurable engine + search token via `~/.config/aho/orchestrator.json` (or similar). Defaults: engine=gemini, search=brave. Brave token entered via `bin/aho-secrets-init` extension or new `bin/aho-orchestrator config` subcommand.
5. OTEL `aho.tokens` dict serialization fix (W7 from 0.2.5 plan).
6. Evaluator score parser scale detection + raw field preservation (W8 from 0.2.5 plan).
7. `bin/aho-conductor smoke` subcommand with verifiable outcome (W9 from 0.2.5 plan).
8. Two new gotchas: aho-G064 (OTEL scalar attrs), aho-G065 (claimed-vs-installed verification). Both deferred from 0.2.5.

## Non-goals

- P3 clone-to-deploy (still future iteration, likely 0.3.x once dashboard is in)
- Dashboard authentication, multi-user, remote access — localhost only, single user
- Real-time websocket updates — polling at 5s intervals is fine for v1
- Replacing the existing bin/aho-dashboard JSON skeleton — the dashboard reads from it, doesn't replace it
- kjtcom anything
- MCP fetch/github/slack/google-drive replacement ADR (still separate)
- Telegram bot interactive token entry beyond what 0.2.6 already shipped

---

## The dashboard

**Stack:** Flutter Web. Single-page app. Tailwind-equivalent styling using Geist Sans/Mono per the existing aho typography lock. Color palette matches the existing trident chart (`#0D9488` shaft, `#161B22` background, `#4ADE80` accent, plus per-status colors).

**Route:** Served from `bin/aho-dashboard` (existing 0.2.3 skeleton) on `127.0.0.1:7800`. Flutter build output replaces the current raw-JSON output. The skeleton becomes a static file server.

**Sections (top to bottom):**

1. **System banner.** Iteration version, phase, run type, last close timestamp. Reads from `.aho.json` and `.aho-checkpoint.json`.
2. **Component coverage matrix.** Table of components.yaml entries × install state. Columns: name, kind, owner, install source, status (ok / missing / unknown). Color-coded. This is the answer to "what's installed."
3. **Daemon health.** 4 systemd user services (openclaw, nemoclaw, telegram, harness-watcher). Status from `systemctl --user is-active` polled every 5s. Heartbeat freshness from event log per dashboard-contract.md.
4. **Recent traces.** Last 20 events from `data/aho_event_log.jsonl`, newest first. Source agent → target with action. Click to expand for full event JSON.
5. **MCP fleet.** 9 packages, status from `bin/aho-mcp list` cache (refreshed on dashboard load). Version and registry verification status.
6. **Model fleet.** 4 ollama models, status from `bin/aho-models doctor`.

**Implementation notes:**
- Read-only. Dashboard never writes. No buttons that mutate state. (Phase 1+ may add controls; not 0.2.7 scope.)
- All data sources are existing files or existing wrapper outputs. No new backend code beyond a thin Python adapter that aggregates them into a single JSON endpoint for Flutter to consume.
- The aggregator endpoint lives at `bin/aho-dashboard` extended: `/api/state` returns the full dashboard JSON, `/` serves the Flutter app static files.

---

## Components coverage matrix

Produced as `artifacts/iterations/0.2.7/components-coverage.md`. Markdown table with one row per components.yaml entry. Columns: name, kind, install source, install verified, notes.

The audit process:
1. Parse components.yaml (88 entries)
2. For each entry, identify which install.fish step (if any) installs it
3. For each entry, run a verification command appropriate to its kind:
   - python_module → `python -c "import aho.<module>"`
   - mcp_server → `bin/aho-mcp list` membership
   - external_service → component-specific check (chromadb directory exists, ollama responds, etc.)
   - agent → systemd is-active or socket presence
   - llm → `ollama list` membership
4. Mark each row ok / missing / unknown
5. Identify gaps and either fix in install.fish or document as intentional

Predicted gaps (to be confirmed during W2):
- **chromadb** — installed via pip as transitive dep, not explicitly. Either declare it explicitly in install.fish step 3 (python) or document the transitive path.
- **opentelemetry exporter** — same pattern
- **brave-integration** — module exists but no token configured. The new orchestrator config (W3) addresses this.

---

## Orchestrator config

New file: `~/.config/aho/orchestrator.json`. Schema:

```
{
  "engine": "gemini",
  "search": {
    "provider": "brave",
    "token_secret_key": "brave_search_token"
  },
  "openclaw": {
    "default_model": "qwen3.5:9b"
  },
  "nemoclaw": {
    "classifier_model": "nemotron-mini:4b"
  }
}
```

The brave token itself lives in the existing fernet secrets store under key `brave_search_token`, never plaintext on disk. `bin/aho-secrets-init` gains a `--add-brave-token` flag that prompts for the token, encrypts it, stores it, and updates orchestrator.json to reference the key.

Engine field reserved for future per-workstream engine selection. For 0.2.7 it's metadata only — actual engine choice is still per-invocation. Future iteration uses this to drive default behavior.

---

## The three carry-forwards (compressed from 0.2.5 design §"Four 0.2.3 carry-forward fixes")

Same scope as documented in `aho-design-0_2_5.md`. Restated briefly:

**OTEL aho.tokens scalar fix.** Add `set_attrs_from_dict(span, prefix, d)` helper. Replace 6 dict-to-attribute call sites in qwen-client, nemotron-client, glm-client, openclaw, nemoclaw, telegram. Unit test asserts no `Invalid type dict` errors. aho-G064.

**Evaluator score parser fix.** Add scale detection (≤1.0 → multiply by 10). Preserve raw_score and raw_recommendation. Unit tests for both 0–1 and 0–10 inputs.

**Conductor smoke subcommand.** `bin/aho-conductor smoke` dispatches a deterministic file-marker task, asserts file exists with expected content, asserts ≥7 spans landed in event log within timestamp window. Exit 0 on full pass. aho-G065.

---

## What stays the same

- Phase 0 charter and Pillars
- Bundle structure (§1–§26)
- install.fish architecture from 0.2.5/0.2.6
- All wrappers from 0.2.5/0.2.6 except those modified in W3 and W7
- 4-daemon architecture
- iao secrets model

## Open questions for Kyle before plan-doc execution

1. **Dashboard depth for v1.** Six sections is the target. Is component coverage matrix the priority, or daemon health? If wall-clock pressure forces a cut, which two sections ship and which two defer to 0.2.8?

2. **components.yaml audit — fix gaps in 0.2.7 or document them?** Predicted gaps (chromadb transitive, opentelemetry transitive, brave-integration unconfigured) all have a "leave it as-is and document" path and a "make install.fish explicit" path. Lean: document for transitive deps, fix for brave-integration. Confirm.

3. **Brave token entry flow.** Same question as 0.2.5 telegram: capability gap with file-drop instructions, or interactive prompt inside `bin/aho-secrets-init --add-brave-token`? Lean interactive prompt this time — token is short, not multiline, low risk.

4. **Engine field purpose.** Is the orchestrator.json `engine` field forward-looking (reserved metadata, no behavior change in 0.2.7), or should 0.2.7 actually change something based on it? Lean reserved.

5. **Iteration size.** This is 7+ workstreams. Same risk as 0.2.5 — possible scope creep. Acceptable to defer dashboard sections 5 (MCP fleet) and 6 (model fleet) to 0.2.8 if W2 audit takes longer than expected?
