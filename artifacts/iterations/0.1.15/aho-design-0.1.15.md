# aho 0.1.15 — Design

**Phase:** 0 | **Iteration:** 0.1.15 | **Theme:** Foundation for Phase 0 exit
**Run Type:** mixed | **Wall clock:** ~2 hours | **Primary:** Gemini CLI W0–W3 | **Closer:** Claude Code W4

## Context

First of three Phase 0 exit-track iterations. 0.1.15 lays foundation; 0.1.16 ships to soc-foundry + P3; 0.1.17 polishes for Alex. 0.18.x is the multi-run ship gauntlet. Phase 1 opens when P3 + Alex validation lands clean.

This run is foundation only. No soc-foundry, no P3, no global installs. Five sharp workstreams that make the next iteration possible.

## Objectives

1. **Report repair (W0).** Mechanical, ground-truth-driven report builder. Qwen as commentary layer only, never structural author. Reports stop breaking, stop hallucinating, stop being shallow.
2. **Component manifest system (W1).** `components.yaml` source of truth, merged with MANIFEST.json + event log attribution into a live component report. New §23 in bundle, new top-level section in run report, new `aho components` CLI. **First-class entries for openclaw, nemoclaw, telegram with status=stub, next_iteration=0.1.16.**
3. **OpenTelemetry instrumentation (W2).** OTEL SDK wired into `aho.logger.log_event` as dual emitter alongside JSONL. Workstreams = traces, tool/LLM calls = spans. Local Jaeger via docker-compose.
4. **/app Flutter scaffold (W3).** `flutter create app`, package `aho_app`, placeholder pages, `flutter build web` smoke test. Replaces deleted `build_gatekeeper.py` with new `app_build_check.py`.
5. **Hygiene + Phase 0 charter rewrite (W0).** MANIFEST refresh + `manifest_current` postflight gate, CHANGELOG.md restoration, Phase 0 charter rewrite to current objective, `build_log_complete` WARN fix.

## Non-goals

- soc-foundry initial push (0.1.16 run 1)
- openclaw/nemoclaw global wrappers (0.1.16)
- telegram bridge real implementation (0.1.16)
- P3 clone or smoke test (0.1.16+)
- claw3d location decision and scaffold (0.1.17)
- Real Flutter app pages with data wiring (0.1.16+)
- Cross-platform installer (dropped from charter — Arch + fish only)

## Workstreams

### W0 — Report repair + hygiene + charter rewrite

Three-part workstream — foundation must land before component/OTEL/Flutter work piles on top of broken upstream reporting.

**Part A — Mechanical report builder.** New `src/aho/feedback/report_builder.py`. Reads checkpoint + event log + postflight results + component manifest (when available). Emits `aho-report-{iteration}.md` with structured sections: Executive Summary, Workstream Detail, Component Activity (gracefully empty when components.yaml absent — populated from W1 onward), Postflight Results, Risk Register, Carryovers, Next Iteration Recommendation. Qwen call is optional commentary layer wrapping the mechanical output, never the structural author. ADR-042 extends to reports: mechanical is authoritative, Qwen is commentary.

**Part B — Hygiene.** MANIFEST.json refresh (recompute all hashes). New `src/aho/postflight/manifest_current.py` — FAIL on stale hashes. Fix `build_log_complete.py` design doc path lookup WARN. Sweep `data/gotcha_archive.json` and `data/script_registry.json` for any residual `iaomw-*` prefixes. Rewrite `CHANGELOG.md`: restore historical 0.1.0-alpha entry accuracy (W1 over-correction reverted), add entries for 0.1.9 through 0.1.15, wire into close sequence as required artifact (new postflight `changelog_current.py`).

**Part C — Phase 0 charter rewrite.** New `artifacts/phase-charters/aho-phase-0.md` with current clone-to-deploy objective, current 3-iteration exit roadmap, live exit criteria checkboxes. Retire `artifacts/phase-charters/iao-phase-0.md` to historical (rename to `iao-phase-0-historical.md`, keep for audit trail). Add to canonical artifacts list — seven files now: `base.md`, `agents-architecture.md`, `model-fleet.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`, `aho-phase-0.md`.

**Gate:** report builder produces structured output on 0.1.14 fixture data; manifest_current gate green; CHANGELOG.md current; Phase 0 charter at `artifacts/phase-charters/aho-phase-0.md` with version 0.1.15.

### W1 — Component manifest system

**This is the visibility layer that resolves the multi-iteration component-info gap.**

New `artifacts/harness/components.yaml`. Schema per component: `name`, `kind` (python_module | cli_wrapper | external_service | agent | llm | mcp), `path`, `status` (active | stub | broken | deprecated), `owner` (default `soc-foundry`), `workload_pct` (computed from event log attribution, null until W2 OTEL ships), `dependencies` (list), `next_iteration` (when status != active), `notes`.

Walk `src/aho/` and populate every Python module. Walk `bin/` and populate every wrapper. Add explicit entries for:
- **openclaw** — kind=agent, path=`src/aho/agents/openclaw.py`, status=stub, next_iteration=0.1.16, notes="ephemeral Python only; global wrapper + install pending 0.1.16"
- **nemoclaw** — kind=agent, path=`src/aho/agents/nemoclaw.py`, status=stub, next_iteration=0.1.16, notes="orchestration layer; routing logic stubbed; global wrapper pending 0.1.16"
- **telegram** — kind=external_service, path=`src/aho/telegram/notifications.py`, status=stub, next_iteration=0.1.16, notes="deferred since 0.1.4 charter; bridge real implementation pending 0.1.16"
- **qwen-client**, **nemotron-client**, **glm-client** — kind=llm, status=active
- **chromadb**, **ollama** — kind=external_service, status=active
- **opentelemetry** — kind=external_service, status=stub, next_iteration=0.1.15 W2 (active by end of this run)

New `src/aho/components/manifest.py`: `load_components() -> List[Component]`, `attribute_workload(events: List[Event]) -> Dict[str, float]`, `render_section() -> str` (markdown for §23 + run report).

New `aho components` CLI subcommand: lists all, filters by status, shows attribution.

New §23 in bundle spec. New top-level "Component Activity" section in run report (W0 builder consumes this).

Tests: `artifacts/tests/test_components_manifest.py` — load, attribute, render.

**Gate:** `aho components` lists ≥30 entries including the three named stubs; §23 renders in 0.1.15 bundle; run report shows component section.

### W2 — OpenTelemetry instrumentation

OTEL SDK in `pyproject.toml`: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`. 

`src/aho/logger.py` becomes dual emitter: continues writing JSONL (authoritative per ADR-007), additionally emits OTEL spans when `AHO_OTEL_ENABLED=1`. Span shape: workstream = trace, tool call = span, LLM call = span with attributes `model`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `exit_code`. Trace ID propagation via `OTEL_TRACE_CONTEXT` env var across subprocess boundaries.

`docker-compose.otel.yml` at repo root: Jaeger all-in-one + OTEL collector. New wrappers `bin/aho-otel-up` and `bin/aho-otel-down` (Pillar 4). Capability gap on Docker install for P3 — documented in `artifacts/harness/p3-deployment-runbook.md`.

JSONL stays authoritative. OTEL is additive, never load-bearing. If collector is down, log_event still writes JSONL and continues.

Tests: `test_logger_otel.py` — span emission with mock exporter.

**Gate:** with `AHO_OTEL_ENABLED=1` and Jaeger up, a smoke test workstream produces visible spans in Jaeger UI. JSONL output unchanged.

### W3 — /app Flutter scaffold

`flutter create app --project-name aho_app --platforms web --org dev.tachtech.aho`. Five placeholder pages under `app/lib/pages/`: `iteration_timeline.dart`, `component_grid.dart`, `workstream_detail.dart`, `postflight_dashboard.dart`, `event_log_stream.dart`. Each page is a stateless widget with the page name as a header and "0.1.16+ wiring pending" body — real wiring lands in 0.1.16+.

Wrappers `bin/aho-app-dev` (`flutter run -d chrome`) and `bin/aho-app-build` (`flutter build web --release`).

Delete `src/aho/postflight/build_gatekeeper.py`. New `src/aho/postflight/app_build_check.py`: if `app/pubspec.yaml` exists, run `flutter build web --release` and gate on exit code; if absent, no-op pass.

Update `MANIFEST.json` to remove build_gatekeeper, add app_build_check. Update doctor sequence.

`flutter create` capability gap: if Dart SDK missing or `flutter` not on PATH, halt cleanly with `[CAPABILITY GAP] flutter not installed` and write to checkpoint. Kyle handles install, resumes.

**Gate:** `app/build/web/index.html` exists and serves; new postflight gate green.

### W4 — Dogfood + close (Claude Code)

Test suite. `aho doctor`. Bundle §1–§23. New mechanical report builder produces structured report. Run report shows component section with openclaw/nemoclaw/telegram visible as stubs. All postflight green: `manifest_current`, `app_build_check`, `changelog_current`, plus existing gates. Checkpoint closed.

## Risks

- **W0 mechanical report builder is the most novel piece.** Risk: edge cases in fixture data parsing. Mitigation: builder is additive, falls back to current report path on exception.
- **W3 Flutter SDK absence.** Mitigation: explicit capability-gap halt, clean resume.
- **W2 Docker absence.** Mitigation: dual-emit means OTEL is purely additive — if collector unavailable, JSONL continues unbroken.

## Success criteria

- Run report shows §23 component activity with openclaw, nemoclaw, telegram visible as `stub`.
- Mechanical report builder produces structured output without Qwen.
- `aho components` CLI works.
- OTEL spans visible in Jaeger when enabled.
- `flutter build web` succeeds in `app/`.
- All postflight gates green including new `manifest_current`, `app_build_check`, `changelog_current`.
- Phase 0 charter at new path with current objective.
- Sign-off #5 = `[x]`.
