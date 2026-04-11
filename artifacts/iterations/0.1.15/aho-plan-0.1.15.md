# aho 0.1.15 — Plan

**Phase:** 0 | **Iteration:** 0.1.15 | **run_type:** mixed
**Primary:** Gemini CLI (W0–W3) | **Closer:** Claude Code (W4)

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.1.15
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.1.15.tar.gz --exclude=data/chroma --exclude=.venv --exclude=app/build .
printf '{"iteration":"0.1.15","phase":0,"status":"in_progress","run_type":"mixed"}\n' > .aho.json
tmux new-session -d -s aho-0.1.15 -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.15 'cd ~/dev/projects/aho; set -x AHO_EXECUTOR gemini-cli; gemini --yolo' Enter
```

## W0 — Report repair + hygiene + charter rewrite

### Part A — Mechanical report builder

Create `src/aho/feedback/report_builder.py`:

```fish
mkdir -p src/aho/feedback
```

Module signature:
- `build_report(iteration: str, project_root: Path = None) -> Path`
- Reads `.aho-checkpoint.json`, `data/aho_event_log.jsonl`, postflight result cache, `artifacts/harness/components.yaml` (gracefully empty if absent — populated in W1).
- Emits `artifacts/iterations/{iteration}/aho-report-{iteration}.md` with sections:
  1. Header (iteration, phase, run_type, generated timestamp, status)
  2. Executive Summary (mechanical: 3–5 sentences derived from workstream pass/fail counts + postflight summary)
  3. Workstream Detail (table from checkpoint + event counts per workstream)
  4. Component Activity (from §23 data, empty section if components.yaml missing)
  5. Postflight Results (gate-by-gate from postflight cache)
  6. Risk Register (extracted from event log entries with `severity=warn|reject`)
  7. Carryovers (parsed from prior run's Kyle's Notes if exists)
  8. Next Iteration Recommendation (mechanical: based on carryovers + open gates)
- Optional Qwen commentary appended as italicized section at end, never structural.

Wire into `src/aho/cli.py` close sequence: replace prior Qwen-first report generation with mechanical-first, Qwen-commentary-second.

Test: `artifacts/tests/test_report_builder.py` with 0.1.14 fixture data — assert 8 sections present, no Qwen call required.

### Part B — Hygiene

```fish
# MANIFEST refresh
python -c "
import json, hashlib, pathlib
root = pathlib.Path('src/aho')
files = {}
for p in sorted(root.rglob('*.py')):
    if p.name == '__init__.py': continue
    rel = str(p)
    files[rel] = hashlib.blake2b(p.read_bytes(), digest_size=8).hexdigest()
manifest = {'package': 'aho', 'version': '0.1.15', 'files': files}
pathlib.Path('MANIFEST.json').write_text(json.dumps(manifest, indent=2))
print(f'MANIFEST refreshed: {len(files)} files')
"
```

Create `src/aho/postflight/manifest_current.py`:
- Walks `src/aho/`, recomputes hashes, compares to MANIFEST.json
- Returns FAIL on any mismatch
- Wire into doctor sequence, replace existing WARN-only behavior

Fix `src/aho/postflight/build_log_complete.py` design doc path lookup:
```fish
rg -n "design.*path|design_path" src/aho/postflight/build_log_complete.py
```
Update to use `get_artifacts_root() / "iterations" / iteration / f"aho-design-{iteration}.md"`.

Registry sweep:
```fish
rg "iaomw" data/gotcha_archive.json data/script_registry.json
# replace any hits with ahomw
```

CHANGELOG.md rewrite — full file replacement with:
- Header `# aho changelog`
- Entries for 0.1.15, 0.1.14, 0.1.13, 0.1.12, 0.1.11, 0.1.10, 0.1.9 (each with theme + key changes from build logs)
- Restored 0.1.0-alpha entry with original `iaomw` references intact (historical accuracy)
- 0.1.9 IAO→AHO Rename entry with correct directional substitutions

Create `src/aho/postflight/changelog_current.py`:
- FAIL if CHANGELOG.md does not contain entry for current iteration
- Wire into close sequence

### Part C — Phase 0 charter rewrite

```fish
mv artifacts/phase-charters/iao-phase-0.md artifacts/phase-charters/iao-phase-0-historical.md
```

Create `artifacts/phase-charters/aho-phase-0.md`:
- Header: aho Phase 0, version 0.1.15, status active
- Why This Phase Exists: clone-to-deploy on P3, soc-foundry first push, Alex SF demo
- Phase Objectives: foundation (0.1.15) → ship to soc-foundry + P3 (0.1.16) → polish + claw3d (0.1.17) → multi-run ship gauntlet (0.18.x)
- Exit Criteria with live `[ ]` / `[x]` checkboxes
- Iteration roadmap table 0.1.15 through 0.18.x → Phase 1
- Charter revision history

Add `aho-phase-0.md` to canonical artifacts list — seven files total.

**W0 Gate:** `python -m pytest artifacts/tests/test_report_builder.py -v` green; `aho doctor` shows manifest_current ok; CHANGELOG.md contains 0.1.15 entry; `artifacts/phase-charters/aho-phase-0.md` exists with version 0.1.15 header.

## W1 — Component manifest system

```fish
mkdir -p src/aho/components artifacts/harness
```

Create `artifacts/harness/components.yaml`:

```yaml
schema_version: 1
components:
  - name: openclaw
    kind: agent
    path: src/aho/agents/openclaw.py
    status: stub
    owner: soc-foundry
    next_iteration: 0.1.16
    notes: "ephemeral Python only; global wrapper + install pending 0.1.16"
  - name: nemoclaw
    kind: agent
    path: src/aho/agents/nemoclaw.py
    status: stub
    owner: soc-foundry
    next_iteration: 0.1.16
    notes: "orchestration layer; routing logic stubbed; global wrapper pending 0.1.16"
  - name: telegram
    kind: external_service
    path: src/aho/telegram/notifications.py
    status: stub
    owner: soc-foundry
    next_iteration: 0.1.16
    notes: "deferred since 0.1.4 charter; bridge real implementation pending 0.1.16"
  - name: opentelemetry
    kind: external_service
    path: src/aho/logger.py
    status: active
    owner: soc-foundry
    notes: "dual emitter alongside JSONL; activated 0.1.15 W2"
  - name: qwen-client
    kind: llm
    path: src/aho/artifacts/qwen_client.py
    status: active
    owner: soc-foundry
  # ... walk src/aho/ and add every Python module
```

Auto-populate the rest from MANIFEST.json walk. Gemini: read MANIFEST.json, generate one entry per file with kind=python_module, status=active, owner=soc-foundry, path from manifest. Append to components.yaml under the explicit entries.

Create `src/aho/components/manifest.py`:
- `load_components() -> List[Component]` — parse YAML
- `attribute_workload(events: List[dict]) -> Dict[str, float]` — count events per source_agent / target, normalize to percentages
- `render_section() -> str` — markdown table for §23 + run report

Create `src/aho/components/__init__.py` exporting public API.

Add `components` subcommand to `src/aho/cli.py`:
- `aho components list` — table of all
- `aho components list --status stub` — filter
- `aho components attribution` — workload from event log

Add §23 to bundle spec — Gemini: locate bundle spec definition (likely `src/aho/bundle/__init__.py` or `src/aho/bundle/components_section.py`), add §23 section that calls `manifest.render_section()`.

Wire §23 data into report_builder.py Component Activity section.

Test: `artifacts/tests/test_components_manifest.py`:
- load_components returns ≥30 entries
- attribute_workload sums to 1.0 on fixture
- render_section produces markdown with openclaw/nemoclaw/telegram visible

**W1 Gate:** `aho components list` shows openclaw, nemoclaw, telegram with status=stub; bundle includes §23; report includes Component Activity section.

## W2 — OpenTelemetry instrumentation

```fish
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp --break-system-packages
```

Update `pyproject.toml` dependencies:
```
opentelemetry-api = ">=1.25"
opentelemetry-sdk = ">=1.25"
opentelemetry-exporter-otlp = ">=1.25"
```

Modify `src/aho/logger.py`:
- Add OTEL imports gated on `os.environ.get('AHO_OTEL_ENABLED') == '1'`
- Add `_otel_tracer` lazy init pointing at `OTLP exporter localhost:4317`
- In `log_event()`: continue JSONL write (authoritative), additionally emit span when enabled
- Span attributes: `iteration`, `workstream_id`, `event_type`, `source_agent`, `target`, `action`, `tokens`, `latency_ms`, `status`, `error`, `gotcha_triggered`
- Span name = `event_type`
- Trace propagation via `OTEL_TRACE_CONTEXT` env var for subprocess boundaries

Create `docker-compose.otel.yml` at repo root:
```yaml
version: "3.9"
services:
  jaeger:
    image: jaegertracing/all-in-one:1.55
    ports:
      - "16686:16686"
      - "4317:4317"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

Create `bin/aho-otel-up`:
```fish
#!/usr/bin/env fish
docker compose -f docker-compose.otel.yml up -d
echo "Jaeger UI: http://localhost:16686"
```

Create `bin/aho-otel-down`:
```fish
#!/usr/bin/env fish
docker compose -f docker-compose.otel.yml down
```

```fish
chmod +x bin/aho-otel-up bin/aho-otel-down
```

Capability gap: if `docker` not present, halt with `[CAPABILITY GAP] docker not installed`. Add to `artifacts/harness/p3-deployment-runbook.md` as P3 prereq.

Test: `artifacts/tests/test_logger_otel.py`:
- mock OTEL exporter
- assert span emitted with correct attributes when AHO_OTEL_ENABLED=1
- assert JSONL still written when AHO_OTEL_ENABLED=0

**W2 Gate:** `set -x AHO_OTEL_ENABLED 1; bin/aho-otel-up; python -c "from aho.logger import log_event; log_event(event_type='smoke', source_agent='test')"` produces visible span in Jaeger UI at localhost:16686. JSONL output unchanged.

## W3 — /app Flutter scaffold

Capability check first:
```fish
which flutter; or echo "[CAPABILITY GAP] flutter not installed"
```

If gap: halt cleanly, write checkpoint, notify Kyle. Otherwise proceed:

```fish
cd ~/dev/projects/aho
flutter create app --project-name aho_app --platforms web --org dev.tachtech.aho
cd app
mkdir -p lib/pages
```

Create five placeholder pages, each minimal stateless widget:
- `lib/pages/iteration_timeline.dart`
- `lib/pages/component_grid.dart`
- `lib/pages/workstream_detail.dart`
- `lib/pages/postflight_dashboard.dart`
- `lib/pages/event_log_stream.dart`

Each contains:
```dart
import 'package:flutter/material.dart';
class IterationTimelinePage extends StatelessWidget {
  const IterationTimelinePage({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(
    body: Center(child: Text('Iteration Timeline — 0.1.16+ wiring pending')),
  );
}
```

Update `app/lib/main.dart` to route between the five pages with a basic NavigationRail.

Smoke build:
```fish
cd ~/dev/projects/aho/app
flutter build web --release
test -f build/web/index.html; and echo "BUILD OK"; or echo "BUILD FAIL"
cd ..
```

Create wrappers:
```fish
printf '#!/usr/bin/env fish\ncd (dirname (status filename))/../app; flutter run -d chrome\n' > bin/aho-app-dev
printf '#!/usr/bin/env fish\ncd (dirname (status filename))/../app; flutter build web --release\n' > bin/aho-app-build
chmod +x bin/aho-app-dev bin/aho-app-build
```

Delete `src/aho/postflight/build_gatekeeper.py`:
```fish
rm src/aho/postflight/build_gatekeeper.py
```

Create `src/aho/postflight/app_build_check.py`:
- if `app/pubspec.yaml` does not exist → return ok with note "no app scaffold"
- else run `flutter build web --release` in `app/`, gate on exit code
- return FAIL on non-zero, ok on success

Update doctor sequence: remove build_gatekeeper, add app_build_check. Refresh MANIFEST.json after the file changes.

**W3 Gate:** `app/build/web/index.html` exists; `aho doctor` shows app_build_check ok; build_gatekeeper no longer in doctor output.

## W4 — Dogfood + close (Claude Code)

Handoff: checkpoint at `current_workstream=W4`, `executor=claude-code`, all W0–W3 = pass.

```fish
tmux new-session -d -s aho-0.1.15-close -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.15-close 'claude --dangerously-skip-permissions' Enter
```

Close sequence:
1. `python -m pytest artifacts/tests/ -v` — all green (target ~75 tests with new W0/W1/W2/W3 additions)
2. `aho doctor` — all gates green including new `manifest_current`, `changelog_current`, `app_build_check`
3. Verify components.yaml loads, `aho components list` shows openclaw/nemoclaw/telegram
4. Bundle generation with new §23
5. Mechanical report builder produces structured `aho-report-0.1.15.md`
6. Build log stub generator fires (Gemini won't have authored manual log)
7. Populate `aho-run-0.1.15.md` with workstream summary + Component Activity section + empty Kyle's Notes
8. Final checkpoint: `status=closed`, `closed_at=<timestamp>`
9. Notify stdout `[CLOSE COMPLETE] aho 0.1.15 W4 — ready for Kyle sign-off`

## Capability gaps expected

- **W2:** Docker may not be installed. Halt cleanly, notify Kyle, runbook updated.
- **W3:** Flutter may not be installed. Halt cleanly, notify Kyle.

Both halt-and-resume cleanly. Neither blocks subsequent runs in 0.1.16.

## Checkpoint schema

```json
{
  "iteration": "0.1.15",
  "phase": 0,
  "run_type": "mixed",
  "current_workstream": "W0",
  "workstreams": {"W0":"pending","W1":"pending","W2":"pending","W3":"pending","W4":"pending"},
  "executor": "gemini-cli",
  "started_at": null,
  "last_event": null
}
```
