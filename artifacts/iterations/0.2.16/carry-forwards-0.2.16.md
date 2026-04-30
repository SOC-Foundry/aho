# Carry-Forwards — 0.2.16

Items deferred out of 0.2.16 workstreams, grouped by target. This file is
append-only as workstreams close; it folds into the 0.2.16 retrospective at
iteration close.

## Target: 0.2.16 iteration close-out drift repair

- **W1-AF003 — Baseline failure count typo in acceptance/W1.json**
  - Severity: cosmetic
  - Location: `artifacts/iterations/0.2.16/acceptance/W1.json` →
    `test_results.baseline_regression.baseline_reference_failed_count` claims
    `14`, should be `13`.
  - Disposition: accepted as typo. Sealed archive is not edited post-audit; fix
    at iteration close-out alongside any other cosmetic drift found at close.
  - Source: gemini W1 audit (`artifacts/iterations/0.2.16/audit/W1.json` — AF003).

- **W2-AF003 — Baseline test-count coherence drift (421 vs 427)**
  - Severity: cosmetic (Gemini filed "important"; Kyle's disposition downgrades
    to cosmetic since the numeric baseline is mis-labeled, not incorrect — the
    zero-new-failures signal holds and all 12 failures match baseline entries).
  - Location: `artifacts/iterations/0.2.16/acceptance/W1.json` and
    `acceptance/W2.json` → `test_results.baseline_regression.tests_collected`
    both report `421`. Independent audit collection finds 427 total; 421 matches
    only after the standard W2 ignore-set is applied.
  - Disposition: accepted as-is. Update `artifacts/harness/test-baseline.json`
    counts in the next workstream or iteration close-out to reflect the 427
    total. Do NOT edit the sealed W1/W2 acceptance archives.
  - Future workstreams should include the explicit ignore list in
    `baseline_regression` reporting to prevent this class of count drift (see
    harness-hygiene carry-forward below).
  - Source: gemini W2 audit (`artifacts/iterations/0.2.16/audit/W2.json` — AF003).

## Target: 0.2.16 W3 adjunct OR 0.2.17 harness hygiene

- **F-W1-001 — OTEL_RESOURCE_ATTRIBUTES `${VAR}` expansion wrapper**
  - Severity: important
  - Claude Code does not shell-expand `${AHO_ITERATION}` / `${AHO_WORKSTREAM}`
    in `.claude/settings.json` env values. Literal values work; placeholders
    land verbatim in logs. Aggregator filters dead `${...}` residue but the raw
    files retain it.
  - Proposed fix: `aho workstream init W{N}` bin wrapper that writes literal
    values into `.claude/settings.json` at workstream boundary (Pillar 4 surface).
  - Source: W1 acceptance archive (`acceptance/W1.json` → `findings[0]`).

- **W2 auditor-quality note — explicit ignore-set in baseline_regression reporting**
  - Severity: cosmetic (process)
  - The W2 baseline_regression block reported `tests_collected: 421` without
    enumerating the ignore-set (`test_nemoclaw_real.py`,
    `test_cascade_integration.py`, `test_live_models.py`, `test_glm_live.py`)
    that produced 421. Without the explicit list, 421 vs 427 count drift is
    opaque to future auditors.
  - Proposed fix: future `acceptance/W{N}.json` entries under
    `test_results.baseline_regression` include an `ignored_modules` array
    listing the excluded test files, or equivalent pytest `--ignore` command
    reproducer.
  - Source: W2 close (Kyle disposition on AF003 — auditor-quality related note).

## Target: 0.2.17

- **AF004 — `api_error_count` / `internal_error_count` alias in otel_aggregator.py**
  - Severity: important
  - `api_error_count` is only incremented inside the `internal_error` event
    block in `src/aho/dashboard/otel_aggregator.py`; both fields in `/api/otel`
    output will always be identical in the current implementation.
  - Disposition: clarify intent (alias, missing event mapping, or remove dead
    field). Design decision, not a W1-close decision.
  - Source: gemini W1 audit (AF004).

- **AF005 — `api_retries_exhausted_count` dead field in otel_aggregator.py**
  - Severity: important
  - Initialized and rolled up by the aggregator but never incremented at any
    event ingestion site. Will always return 0.
  - Disposition: map to an actual event, or remove. Same treatment as AF004.
  - Source: gemini W1 audit (AF005).

- **W0 F-W0-004 — conftest allowlist brittleness**
  - Severity: important
  - Carried from W0. The `test_workstream_events.py` fixture has corrupted the
    checkpoint three times across recent iterations; W0 added an allowlist in
    `artifacts/tests/conftest.py` but the underlying fragility persists for any
    future test author who emits workstream events outside the allowlist.
  - Target: 0.2.17 test isolation iteration.
  - Source: W1 acceptance archive (`carry_forward_candidates[1]`).

- **Historical trend graphs (time series of cost/tokens)**
  - Severity: info
  - `/api/otel` returns point-in-time aggregates only. Trend graphs require a
    metric backend that retains data points (Prometheus remote_write from
    otelcol, or Grafana direct scrape). Mercor Grafana reference implementation
    in the claude-otel repo may offer the template.
  - Source: W1 acceptance archive (`carry_forward_candidates[2]`).

- **Dashboard polling cadence unification (/api/state at 5s vs /api/otel at 2s)**
  - Severity: info
  - Server-side caches are 2s on both; Flutter-side 5s for `/api/state` is a
    stale-era choice. One-line tweak, not in W1 scope.
  - Source: W1 acceptance archive (`carry_forward_candidates[3]`).

- **W2-AF004 — `dispatch.duration_ms` measurement-site gap on error paths**
  - Severity: info
  - On success, `dispatch.duration_ms` is sourced from
    `result['wall_clock_seconds'] * 1000.0` (same as event log — single source
    of truth, zero drift). On `DispatchError`, it is sourced from a span-local
    monotonic delta. Happy-path drift was measured at 0.11ms; error-path drift
    is unmeasured and introduces a theoretical two-measurement-site divergence.
  - Proposed target: add test coverage for error-path duration consistency (and
    unify the measurement site if the test surfaces material drift).
  - Source: gemini W2 audit (`artifacts/iterations/0.2.16/audit/W2.json` — AF004).

- **Classifier quality probe — nemotron-mini:4b category-mapping drift**
  - Severity: info
  - W2 end-to-end probe observed nemotron-mini:4b classify "Write a Python
    function that computes fibonacci numbers." as `prose` rather than `code`.
    Orthogonal to trace-propagation scope (the W2 deliverable); captured as an
    observation only.
  - Proposed target: if classifier-conformance drift becomes a recurring theme,
    a dedicated probe + test-suite workstream is the right container — not an
    ad-hoc fix inside unrelated work.
  - Source: W2 acceptance archive (`acceptance/W2.json` →
    `otel_telemetry_evidence.classify_category_note` and
    `carry_forward_candidates[1]`).

- **Closure-capture pattern for span-attribute population**
  - Severity: info
  - Alternative to W2's additive dict-extension (`tokens_eval` /
    `tokens_prompt` keys on the dispatcher return dict). Closure-captured locals
    would keep the return contract narrow but tangle span-attribute population
    into the retry loop's many early-return points. Dict-extension won on the
    simplicity axis for W2; closure-capture stays viable if the return contract
    ever needs to tighten to a fixed schema.
  - Proposed target: any future iteration where dispatcher return contract
    tightening is in scope.
  - Source: W2 acceptance archive (`acceptance/W2.json` →
    `scope_notes.dispatcher_return_shape_delta` and `carry_forward_candidates[2]`).

## Target: next collector config touch

- **Collector OTLP alias deprecation warning (tracked from W0)**
  - Severity: cosmetic
  - otelcol-contrib v0.149.0 prints "otlp alias deprecated, use otlp_grpc" on
    the `otlp/jaeger` exporter at collector startup. Unchanged through W1 and
    W2. Functional behavior unaffected.
  - Proposed fix: rename exporter key to `otlp_grpc/jaeger` (and any other
    `otlp/*` alias usages) the next time the collector config is edited.
  - Source: W2 acceptance archive (`acceptance/W2.json` →
    `carry_forward_candidates[3]`); originally surfaced in W0.
