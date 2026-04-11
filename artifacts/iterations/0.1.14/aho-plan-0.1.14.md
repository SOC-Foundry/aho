# aho 0.1.14 — Plan

**Phase:** 0 | **Iteration:** 0.1.14 | **Primary:** Gemini CLI (W0–W5) | **Closer:** Claude Code (W6)
**run_type:** mixed

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.1.14
tmux new-session -d -s aho-0.1.14 -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.14 'cd ~/dev/projects/aho; set -x AHO_EXECUTOR gemini-cli; gemini --yolo' Enter
```

## W0 — Hygiene + reorg cleanup

```fish
cd ~/dev/projects/aho
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.1.14.tar.gz --exclude=data/chroma --exclude=.venv .
printf '{"iteration":"0.1.14","phase":0,"status":"in_progress","run_type":"mixed"}\n' > .aho.json
```

**Flatten `artifacts/docs/`:**
```fish
command ls artifacts/docs/iterations/
mv artifacts/docs/iterations/0.1.2 artifacts/iterations/0.1.2
find artifacts/docs -type f
rm -rf artifacts/docs
command ls artifacts/
```

**Populate MANIFEST.json:**
```fish
python -c "
import json, pathlib
root = pathlib.Path('src/aho')
manifest = {'package': 'aho', 'version': '0.1.14', 'modules': sorted([str(p.relative_to(root).with_suffix('')).replace('/', '.') for p in root.rglob('*.py') if p.name != '__init__.py'])}
pathlib.Path('MANIFEST.json').write_text(json.dumps(manifest, indent=2))
"
command cat MANIFEST.json | head -20
```

**Restore fish marker in install.fish:**
```fish
rg "# >>> aho install >>>" install.fish
# if missing, prepend marker block with idempotency guard
```

**Gate:** `aho doctor` → 6 ok / 0 warn. `command ls artifacts/` shows no `docs` entry.

## W1 — Terminology sweep

### Pass 1: Agentic Harness Orchestration → Agentic Harness Orchestration

```fish
rg -l "Agentic Harness Orchestration" artifacts/ CLAUDE.md GEMINI.md README.md > /tmp/aho-pass1.txt
command cat /tmp/aho-pass1.txt
```

For each file: replace "Agentic Harness Orchestration" with "Agentic Harness Orchestration" in prose. Verify mermaid trident shaft text stays `A H O` (aho acronym — the three letters now stand for Agentic Harness Orchestration, no label change needed).

### Pass 2: ahomw → ahomw

```fish
rg -l "ahomw" artifacts/ src/ data/ projects.json CLAUDE.md GEMINI.md README.md > /tmp/aho-pass2.txt
command cat /tmp/aho-pass2.txt
```

Targets:
- `artifacts/harness/base.md` — footer `ahomw - inviolable` → `ahomw - inviolable`; every `ahomw-ADR-*` → `ahomw-ADR-*` (ADR-003, 005, 007, 009, 012, 014, 015, 017, 021, 027).
- `projects.json` — key `ahomw` → `ahomw`, name `iao` → `aho`, path `~/dev/projects/iao` → `~/dev/projects/aho`.
- `data/script_registry.json`, `data/gotcha_archive.json` — any `ahomw-*` → `ahomw-*`.
- `src/aho/registry.py` — hardcoded prefix strings.

### Pass 3: residual iao narrative

```fish
rg -n "\biao\b" artifacts/harness/ artifacts/adrs/ artifacts/roadmap/ CLAUDE.md GEMINI.md README.md | grep -v "iao-phase-0.md" > /tmp/aho-pass3.txt
command cat /tmp/aho-pass3.txt
```

Whitelist: `artifacts/phase-charters/iao-phase-0.md` filename only; `artifacts/iterations/0.1.2/` through `0.1.12/` fully excluded.

**Gate:**
```fish
rg -i "iterative agentic" artifacts/ CLAUDE.md GEMINI.md README.md  # zero
rg "ahomw" artifacts/ src/ data/ projects.json  # zero
```

## W2 — Six canonical artifacts repair

In order:

1. **`artifacts/harness/base.md`** — apply W1 Pass 2 changes, bump version header to 0.1.14, update timestamp.
2. **`artifacts/harness/agents-architecture.md`** — header to 0.1.14, footer to "Updated by Gemini CLI during aho 0.1.14 W2".
3. **`artifacts/harness/model-fleet.md`** — header version 0.1.13 → 0.1.14, footer "Document updated for aho 0.1.12 W3" → "Document updated for aho 0.1.14 W2".
4. **`CLAUDE.md`** — verify no residual drift, bump "Rewritten during 0.1.13 W1" note if any full expansion added.
5. **`GEMINI.md`** — same.
6. **`README.md`** — iteration label to 0.1.14, trident chart expansion text update, component count if §22 classification changed count.

**Gate:** `for f in artifacts/harness/base.md artifacts/harness/agents-architecture.md artifacts/harness/model-fleet.md CLAUDE.md GEMINI.md README.md; rg -l "0.1.14" $f; end` — all six hit.

## W3 — Build log stub generator

1. Create `src/aho/feedback/build_log_stub.py`:
   - `generate_stub(iteration: str, project_root: Path = None) -> Path`
   - Reads `.aho-checkpoint.json` and `data/aho_event_log.jsonl`
   - Writes `artifacts/iterations/{iteration}/aho-build-{iteration}.md`
   - Template: header with iteration + run_type + generation timestamp + bold "Auto-generated" marker; per-workstream synthesis (agent, status, event count, first/last event); event type histogram; event log tail (last 20 events).

2. Wire into `src/aho/cli.py` close sequence:
   ```python
   build_log_path = ITERATIONS_DIR / iteration / f"aho-build-{iteration}.md"
   if not build_log_path.exists():
       from aho.feedback.build_log_stub import generate_stub
       generate_stub(iteration)
   ```

3. Test:
   - `artifacts/tests/test_build_log_stub.py`
   - Fixture: synthetic checkpoint + 50-event log
   - Assert: stub file exists, contains workstream headers, contains "Auto-generated" marker, §3 bundle validation passes against stub.

**Gate:** `python -m pytest artifacts/tests/test_build_log_stub.py -v` → green.

## W4 — Postflight gate repair

1. **Layout variant detection** in `src/aho/postflight/`:
   - Add `src/aho/postflight/layout.py` with `detect_layout(doc_path: Path) -> LayoutVariant` (`w_based` | `section_based`).
   - `pillars_present.py`: branch on layout variant. W-based checks for W0–W6 headers + workstream summary table. §-based keeps current §-pattern check.
   - `structural_gates.py`: same branch.

2. **Run type classification**:
   - Extend checkpoint schema: `run_type` field (design declares it, checkpoint copies it forward).
   - `src/aho/postflight/run_complete.py`: read `run_type` from checkpoint, apply §22 floor:
     ```python
     FLOORS = {"agent_execution": 6, "reorg_docs": 2, "hygiene": 1, "mixed": 3}
     ```
   - If §22 component count ≥ floor, pass. Record the classification in run report.

3. Tests:
   - `artifacts/tests/test_postflight_layouts.py` — fixtures for both variants.
   - `artifacts/tests/test_postflight_run_types.py` — fixtures for each run_type.

4. Regression: replay 0.1.13 bundle through new gates:
   ```fish
   python -m aho.postflight.pillars_present artifacts/iterations/0.1.13/aho-bundle-0.1.13.md
   python -m aho.postflight.structural_gates artifacts/iterations/0.1.13/aho-bundle-0.1.13.md
   ```
   Both must pass.

**Gate:** new tests green, 0.1.13 regression green.

## W5 — P3 deployment dry-run

```fish
set SCRATCH /tmp/aho-p3-dryrun
rm -rf $SCRATCH
mkdir -p $SCRATCH
bin/aho-install --dry-run --target $SCRATCH
command ls -la $SCRATCH/.local/bin/
command ls -la $SCRATCH/.config/aho/
command ls -la $SCRATCH/.local/share/aho/
```

If `--dry-run` flag does not exist on `bin/aho-install`, add it as the first W5 step. Flag behavior: all XDG path operations rooted at `--target` instead of `$HOME`, no `pacman`/`pip` invocations, no Ollama service touches, emit capability-gap interrupts to stdout as prefixed lines.

Capture stdout + any surfaced gaps into `artifacts/harness/p3-deployment-runbook.md` updates.

```fish
bin/aho-install --dry-run --target $SCRATCH > /tmp/aho-p3-dryrun.log 2>&1
command cat /tmp/aho-p3-dryrun.log
rm -rf $SCRATCH
```

**Gate:** dry-run exit 0, runbook updated, scratch cleaned.

## W6 — Dogfood + close (Claude Code handoff)

Checkpoint at W5 complete with `current_workstream=W6`, `executor=claude-code`. Fresh tmux:

```fish
tmux new-session -d -s aho-0.1.14-close -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.14-close 'claude --dangerously-skip-permissions' Enter
```

1. `python -m pytest artifacts/tests/ -v` — all green.
2. `aho doctor` — 6 ok / 0 warn.
3. Verify manual build log absent → confirm stub generator fires → verify §3 populated.
4. Bundle generation + §1–§22 validation.
5. Postflight: `run_complete`, `run_quality`, `pillars_present`, `structural_gates` — all green via new layout variant + run_type gates.
6. Populate `artifacts/iterations/0.1.14/aho-run-0.1.14.md` with workstream summary, empty Kyle's Notes, unchecked sign-off.
7. Final checkpoint: `status=closed`, `closed_at=<timestamp>`.
8. Notify stdout with `[CLOSE COMPLETE]` marker.

## Capability-gap interrupts expected

- **W0:** None.
- **W1:** None (pure text sweep).
- **W2:** None.
- **W3:** None.
- **W4:** None.
- **W5:** None on NZXT (scratch root only, `--dry-run` forbids sudo).

If any surface: halt, write to checkpoint, notify stdout with `[CAPABILITY GAP]` prefix.

## Checkpoint schema

```json
{
  "iteration": "0.1.14",
  "phase": 0,
  "run_type": "mixed",
  "current_workstream": "W0",
  "workstreams": {
    "W0": "pending", "W1": "pending", "W2": "pending",
    "W3": "pending", "W4": "pending", "W5": "pending", "W6": "pending"
  },
  "executor": "gemini-cli",
  "started_at": null,
  "last_event": null
}
```
