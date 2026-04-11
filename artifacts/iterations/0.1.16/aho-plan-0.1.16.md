# aho 0.1.16 — Plan

**Phase:** 0 | **Iteration:** 0.1.16 | **run_type:** mixed
**Agent:** Claude Code single-agent throughout (no Gemini handoff)

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.1.16
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.1.16.tar.gz --exclude=data/chroma --exclude=.venv --exclude=app/build .
printf '{"aho_version":"0.1","name":"aho","project_code":"ahomw","artifact_prefix":"aho","current_iteration":"0.1.16","phase":0,"mode":"active","created_at":"2026-04-08T12:00:00+00:00","bundle_format":"bundle","last_completed_iteration":"0.1.15"}\n' > .aho.json
mkdir -p artifacts/iterations/0.1.16
tmux new-session -d -s aho-0.1.16 -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.16 'cd ~/dev/projects/aho; claude --dangerously-skip-permissions' Enter
```

## W0 — Close sequence repair + canonical artifacts + hygiene

### Part A — Close sequence repair

1. Read `src/aho/cli.py` and locate the iteration close subcommand (likely `def close()` or `def iteration_close()`).
2. Refactor the close sequence into explicit ordered steps. Pseudocode:

```python
def close_iteration(iteration: str) -> int:
    # Step 1: Tests
    if not run_tests(): return 1
    # Step 2: Bundle generation
    bundle_path = build_bundle(iteration)
    if not bundle_path.exists(): return 1
    # Step 3: Mechanical report
    report_path = report_builder.build_report(iteration)
    if not report_path.exists(): return 1
    # Step 4: Run file (consumes report_builder data)
    run_path = run_file_builder.build_run_file(iteration, report_data=report_builder.last_data)
    if not run_path.exists(): return 1
    # Step 5: Postflight gates (now real artifacts exist)
    postflight_result = doctor.run_postflight(iteration)
    if postflight_result.has_failures(): return 1
    # Step 6: Update .aho.json
    update_aho_json(iteration, last_completed=iteration)
    # Step 7: Final checkpoint write
    checkpoint.write_closed(iteration)
    return 0
```

3. Verify by reading the close subcommand top-to-bottom — each step is a labeled function call, no implicit ordering.

### Part B — Canonical artifacts gate

```fish
mkdir -p artifacts/harness
```

Create `artifacts/harness/canonical_artifacts.yaml` with the seven entries from the design doc.

Create `src/aho/postflight/canonical_artifacts_current.py`:
- Load YAML, iterate entries
- For each, read file, regex-match version pattern, compare to `.aho.json` `current_iteration`
- Return FAIL on any mismatch with details (file, found version, expected version)
- Return ok if all match

Wire into doctor sequence in `src/aho/doctor.py`. Remove legacy `manifest` SHA256 check from doctor sequence.

**Bump all seven canonical artifacts to 0.1.16 in this part of W0:**

```fish
# base.md
sed -i 's/^\*\*Version:\*\* 0\.1\.14/**Version:** 0.1.16/' artifacts/harness/base.md
sed -i 's/aho 0\.1\.14 W2 — terminology repair/aho 0.1.16 W0 — close sequence repair/' artifacts/harness/base.md

# agents-architecture.md
sed -i 's/^\*\*Version:\*\* 0\.1\.14/**Version:** 0.1.16/' artifacts/harness/agents-architecture.md
sed -i 's/Agents Architecture — aho 0\.1\.14/Agents Architecture — aho 0.1.16/' artifacts/harness/agents-architecture.md

# model-fleet.md
sed -i 's/^\*\*Version:\*\* 0\.1\.14/**Version:** 0.1.16/' artifacts/harness/model-fleet.md
sed -i 's/Document updated for aho 0\.1\.14 W2/Document updated for aho 0.1.16 W0/' artifacts/harness/model-fleet.md

# aho-phase-0.md (already at 0.1.15, bump to 0.1.16 in W1)
# README.md (handled in Part D)
# pyproject.toml (handled in Part D)
# CLAUDE.md and GEMINI.md - verify no version drift, content rule only
```

Test the new gate manually before wiring into close:
```fish
python -c "from aho.postflight.canonical_artifacts_current import check; print(check())"
```

### Part C — Run file wiring

1. Locate run file generator. Likely `src/aho/feedback/run.py` or similar. The current generator emits a skeleton with `agent: "unknown"` and empty wall clock — find this code path.
2. Refactor to import and consume `report_builder`:

```python
from aho.feedback.report_builder import build_report_data
from aho.components.manifest import render_section as render_components

def build_run_file(iteration: str) -> Path:
    report_data = build_report_data(iteration)  # workstream table with agents, wall clock
    components_md = render_components()
    
    template = load_template("run_file.md.j2")
    rendered = template.render(
        iteration=iteration,
        workstreams=report_data["workstreams"],  # has agent + wall clock per ws
        components=components_md,
        agent_questions=report_data["agent_questions"],
        kyle_notes_placeholder="<!-- Fill in after reviewing the bundle -->",
    )
    
    run_path = ITERATIONS_DIR / iteration / f"aho-run-{iteration}.md"
    run_path.write_text(rendered)
    return run_path
```

3. Update `prompts/run_file.md.j2` (or wherever the template lives) to include the workstream table with `{{ ws.agent }}` and `{{ ws.wall_clock }}` columns, plus a `## Component Activity` section that embeds `{{ components }}`.

### Part D — Hygiene

```fish
# README link fix
sed -i 's|artifacts/phase-charters/iao-phase-0.md|artifacts/phase-charters/aho-phase-0.md|g' README.md
sed -i 's|Iteration 0\.1\.14|Iteration 0.1.16|g' README.md

# README footer aho.run
sed -i 's|aho v0\.1\.14|aho v0.1.16 — aho.run|' README.md

# pyproject.toml version + URLs
sed -i 's|^version = "0\.1\.13"|version = "0.1.16"|' pyproject.toml
# Add [project.urls] section if not present
python -c "
import pathlib
p = pathlib.Path('pyproject.toml')
content = p.read_text()
if '[project.urls]' not in content:
    addition = '\n[project.urls]\nHomepage = \"https://aho.run\"\nRepository = \"https://github.com/soc-foundry/aho\"\n'
    content = content.replace('[project.scripts]', addition + '\n[project.scripts]')
    p.write_text(content)
"
```

Create `src/aho/feedback/aho_json.py` (or extend existing):
```python
def update_last_completed(iteration: str):
    p = Path(".aho.json")
    data = json.loads(p.read_text())
    data["last_completed_iteration"] = iteration
    p.write_text(json.dumps(data, indent=2) + "\n")
```

Wire into close sequence step 6.

**W0 Gate:**
```fish
python -c "from aho.postflight.canonical_artifacts_current import check; r = check(); assert r['status'] == 'ok', r"
python -m pytest artifacts/tests/ -x
```

## W1 — Iteration 1 graduation ceremony

```fish
mkdir -p artifacts/iterations/0.1
mkdir -p artifacts/iterations/0.2
```

### Part A — Iteration 1 close artifact

Create `artifacts/iterations/0.1/iteration-1-close.md`. Sections:
- Header (iteration 1, runs 0.1.0–0.1.16, graduated 2026-04-11)
- Iteration 1 Objective (as it actually played out): "Build the aho harness from scratch"
- Runs Delivered: table 0.1.0 through 0.1.16 with one-line theme each
- What Was Built: secrets, artifact loop, src-layout, terminology, components manifest, OTEL, Flutter scaffold, mechanical report builder, postflight gate library, build log stub generator, canonical artifacts discipline, close sequence ordering
- What Was Deferred (carries to iteration 2): openclaw global wrapper, nemoclaw global wrapper, telegram bridge real implementation, soc-foundry first push, P3 clone-to-deploy
- Lessons Learned: split-agent model, mechanical-first artifacts, postflight as gatekeeper, component visibility discipline, ordering bugs are silent killers, prose drift across rename sweeps
- Iteration 1 Exit Criteria Evaluation (table)

### Part B — Iteration 2 charter

Create `artifacts/iterations/0.2/iteration-2-charter.md`. Sections:
- Header (iteration 2, opens 2026-04-11, planned runs 0.2.1–0.2.x)
- Iteration 2 Objective: "Ship aho to soc-foundry/aho and validate clone-to-deploy on P3"
- Entry Criteria (from iteration 1 graduation): all checked
- Exit Criteria: soc-foundry/aho repo live, P3 clone succeeds, smoke test passes, openclaw/nemoclaw/telegram all `active` not `stub`
- Planned Runs:
  - 0.2.1 — Cleanup + soc-foundry initial push + openclaw/nemoclaw global wrappers + telegram bridge
  - 0.2.2 — P3 clone attempt + smoke test + capability gap capture
  - 0.2.3+ — Whatever P3 surfaces, fix in tight runs
- Iteration 2 graduates when P3 runs an aho iteration end-to-end

### Part C — Phase 0 charter update

Edit `artifacts/phase-charters/aho-phase-0.md`:
- Bump charter version to 0.1.16
- Add iteration boundary section: "Iteration 1 (0.1.0–0.1.16) — graduated 2026-04-11. Iteration 2 (0.2.x) — active. Iteration 3 (0.3.x) — planned."
- Add `aho.run` to header
- Update iteration roadmap table to reflect 3-iteration structure

### Part D — README iteration roadmap

Replace flat 0.1.x list in README with:
```markdown
## Iteration Roadmap

| Iteration | Theme | Status |
|---|---|---|
| 1 (0.1.x) | Build the harness | graduated 2026-04-11 |
| 2 (0.2.x) | Ship to soc-foundry + P3 | active |
| 3 (0.3.x) | Alex demo + claw3d + polish | planned |
| Phase 1 | Multi-project, multi-machine | planned |
```

**W1 Gate:** four files exist; all reference iteration boundary correctly; charter at 0.1.16.

## W2 — Dogfood + close (corrected sequence)

This is the proof that W0 worked. The corrected close sequence runs against 0.1.16 itself.

```fish
python -m aho.cli iteration close 0.1.16
```

Expected output ordering (verify by tailing event log):
1. Tests run, 80+ green
2. Bundle generated → `artifacts/iterations/0.1.16/aho-bundle-0.1.16.md` exists
3. Mechanical report generated → `aho-report-0.1.16.md` exists with rich content
4. Run file generated → `aho-run-0.1.16.md` exists with `claude-code` agents and real wall clock
5. Postflight gates run → all green including new `canonical_artifacts_current`
6. `.aho.json` shows `last_completed_iteration: 0.1.16`
7. Checkpoint closed

**Verify zero false positives:**
```fish
python -c "
import json
checkpoint = json.loads(open('.aho-checkpoint.json').read())
assert checkpoint['status'] == 'closed'
report = open('artifacts/iterations/0.1.16/aho-report-0.1.16.md').read()
assert 'fail' not in report.lower().split('postflight results')[1].split('---')[0]
print('CLOSE CLEAN')
"
```

**Verify run file shows real attribution:**
```fish
grep -A 10 'Workstream Summary' artifacts/iterations/0.1.16/aho-run-0.1.16.md
# Should show claude-code, not unknown
```

**W2 Gate:** zero failed postflight gates; run file populated with agent attribution; canonical_artifacts_current green; .aho.json updated; checkpoint closed.

## Capability gaps expected

None. Pure refactor + ceremony run, all on NZXTcos, no new external dependencies.

## Checkpoint schema

```json
{
  "iteration": "0.1.16",
  "phase": 0,
  "run_type": "mixed",
  "current_workstream": "W0",
  "workstreams": {"W0":"pending","W1":"pending","W2":"pending"},
  "executor": "claude-code",
  "started_at": null,
  "last_event": null
}
```
