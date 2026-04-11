# aho — Plan 0.1.11

**Run:** 0.1.11
**Phase:** 0
**Predecessor:** 0.1.10 (graduated clean)
**Wall clock target:** ~3 hours
**Workstreams:** W0-W4 (five)
**Authored:** 2026-04-10

---

## Section A — Pre-flight checks

```fish
# A.0 — Working directory (may be aho or iao depending on whether Kyle ran the W6 rename)
cd ~/dev/projects/aho 2>/dev/null; or cd ~/dev/projects/iao
command pwd

# A.1 — 0.1.10 is closed
jq .last_completed_iteration .aho-checkpoint.json
# Expected: "0.1.10"

# A.2 — aho binary works
./bin/aho --version
# Expected: aho 0.1.10

# A.3 — Design and plan docs present
command ls docs/iterations/0.1.11/aho-design-0.1.11.md docs/iterations/0.1.11/aho-plan-0.1.11.md

# A.4 — Ollama models
curl -s http://localhost:11434/api/tags | python3 -c "import json, sys; d = json.load(sys.stdin); names = [m['name'] for m in d['models']]; print('OK' if any('qwen' in n for n in names) else 'MISSING qwen')"

# A.5 — Current test baseline (record failures before W2 fixes them)
python3 -m pytest tests/ -v 2>&1 | tail -20
```

---

## Section B — Workstream ordering

```
W0 (env hygiene + root confirmation)
 └─→ W1 (run file filename rename)
      └─→ W2 (test suite hygiene)
           └─→ W3 (Qwen degenerate investigation)
                └─→ W4 (dogfood + close)
```

---

## Section C — Per-workstream fish command blocks

### W0 — Environment hygiene + project root confirmation (20 min)

```fish
# W0.0 — Determine current project root
cd ~/dev/projects/aho 2>/dev/null; and set PROJECT_ROOT ~/dev/projects/aho; or begin; cd ~/dev/projects/iao; set PROJECT_ROOT ~/dev/projects/iao; end
command pwd

# W0.1 — Log project root state
if test "$PROJECT_ROOT" = ~/dev/projects/aho
    echo "Project root rename CONFIRMED: ~/dev/projects/aho"
else
    echo "Project root rename PENDING: still at ~/dev/projects/iao"
    echo "Non-blocking — continuing with current path"
end

# W0.2 — Create iteration directory and initialize manual build log
mkdir -p docs/iterations/0.1.11
printf '# Build Log — aho 0.1.11\n\n**Start:** %s\n**Agent:** %s\n**Machine:** NZXTcos\n**Phase:** 0\n**Run:** 0.1.11\n**Theme:** Run file rename + test suite hygiene + Qwen degenerate investigation\n**Project root:** %s\n\n---\n\n' (date -u +%Y-%m-%dT%H:%M:%SZ) "$AHO_EXECUTOR" "$PROJECT_ROOT" > docs/iterations/0.1.11/aho-build-log-0.1.11.md

# W0.3 — Backup files W1 will modify
set BACKUP_DIR "$PROJECT_ROOT".backup-pre-0.1.11
mkdir -p $BACKUP_DIR
cp src/aho/feedback/run_report.py $BACKUP_DIR/ 2>/dev/null
cp -r src/aho/postflight $BACKUP_DIR/postflight 2>/dev/null
cp -r src/aho/bundle $BACKUP_DIR/bundle 2>/dev/null
cp src/aho/artifacts/repetition_detector.py $BACKUP_DIR/ 2>/dev/null

# W0.4 — Bump checkpoint
jq '.iteration = "0.1.11" | .last_completed_iteration = "0.1.10"' .aho-checkpoint.json > .aho-checkpoint.json.tmp
mv .aho-checkpoint.json.tmp .aho-checkpoint.json

# W0.5 — Bump version
sed -i 's/__version__ = "0.1.10"/__version__ = "0.1.11"/' src/aho/cli.py
sed -i 's/^version = "0.1.10"/version = "0.1.11"/' pyproject.toml
pip install -e . --break-system-packages --quiet
./bin/aho --version
# Expected: aho 0.1.11

# W0.6 — Log W0 complete
printf '## W0 — Environment Hygiene\n\n**Actions:**\n- Project root: %s\n- Bumped checkpoint to 0.1.11\n- Bumped version to 0.1.11\n- Backed up files to %s\n\n**Discrepancies:** (note if project root rename is still pending)\n\n---\n\n' "$PROJECT_ROOT" "$BACKUP_DIR" >> docs/iterations/0.1.11/aho-build-log-0.1.11.md
```

---

### W1 — Run file filename rename (60 min)

```fish
# W1.0 — Log W1 start
printf '## W1 — Run File Filename Rename\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md

# W1.1 — Audit the current filename pattern
command rg -n "run.report\|run_report" src/aho/feedback/run_report.py | head -20
command rg -n "run.report\|run_report" src/aho/bundle/__init__.py | head -10
command rg -n "run.report\|run_report" src/aho/postflight/ | head -20

# W1.2 — Update the run report generator output filename
# Executor action: in src/aho/feedback/run_report.py, find the output path construction
# and change from:
#   f"aho-run-report-{version}.md"
# to:
#   f"aho-run-{version}.md"
#
# Also update any function names if they reference "run_report" in a way that generates the filename.

# W1.3 — Rename postflight modules
# Executor action:
#   mv src/aho/postflight/run_report_complete.py src/aho/postflight/run_complete.py
#   mv src/aho/postflight/run_report_quality.py src/aho/postflight/run_quality.py
#   Update the filename check inside each module to look for aho-run-{version}.md
#   Update src/aho/postflight/__init__.py imports if they reference the old module names

# W1.4 — Update bundle spec
# Executor action: in src/aho/bundle/__init__.py, update the §5 "Run Report" section to
# look for aho-run-{version}.md when embedding

# W1.5 — Update prompts template if it references the output filename
command rg "run-report\|run_report" prompts/run-report.md.j2
# If matches found, update. Also consider renaming the template file itself:
#   mv prompts/run-report.md.j2 prompts/run.md.j2
# and updating any code that references the template filename.

# W1.6 — Verify no lingering references
command rg -c "run-report\|run_report" src/aho/
# Expected: 0 (or only within historical-context prose/comments)
# Note: function NAMES like build_workstream_summary() in run_report.py are fine to keep;
# the MODULE can stay named run_report.py. What changes is the OUTPUT FILENAME only.
# If you want to rename the module too, that's fine but not required.

# W1.7 — Run tests
python3 -m pytest tests/ -v 2>&1 | tail -20

# W1.8 — Log W1 complete
printf '**Actions:**\n- Updated run report generator output filename from aho-run-report-*.md to aho-run-*.md\n- Renamed postflight modules: run_report_complete → run_complete, run_report_quality → run_quality\n- Updated bundle spec §5 file lookup\n- Verified no lingering run-report filename references\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md
```

---

### W2 — Test suite hygiene (45 min)

```fish
# W2.0 — Log W2 start
printf '## W2 — Test Suite Hygiene\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md

# W2.1 — Identify the two pre-existing failures
python3 -m pytest tests/test_secrets_backends.py tests/test_artifacts_loop.py -v 2>&1

# W2.2 — Fix test_secrets_backends (age tty issue)
# Executor action: read the test, determine which test function fails.
# Options:
#   a) Add @pytest.mark.skipif(not sys.stdin.isatty(), reason="age requires TTY") to the failing test
#   b) Mock the age subprocess call so it doesn't need a real TTY
#   c) If the test is checking age backend availability, add a try/except around the age invocation
# Prefer option (a) for simplicity — the test still runs when a TTY is present (developer machine),
# and skips cleanly in agent environments.

# W2.3 — Fix test_artifacts_loop (missing "Phase 0")
# Executor action: read the test, find the assertion that expects "Phase 0".
# Determine whether the loop output was changed during 0.1.8's pillar rewrite or 0.1.9's rename.
# Update the test expectation to match the current output format.

# W2.4 — Run full test suite
python3 -m pytest tests/ -v
# Expected: 0 failures

# W2.5 — Log W2 complete
printf '**Actions:**\n- Fixed test_secrets_backends: (describe fix)\n- Fixed test_artifacts_loop: (describe fix)\n- Full test suite: 0 failures\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md
```

---

### W3 — Qwen degenerate synthesis investigation (45 min)

```fish
# W3.0 — Log W3 start
printf '## W3 — Qwen Degenerate Synthesis Investigation\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md

# W3.1 — Read the repetition detector
command cat src/aho/artifacts/repetition_detector.py

# W3.2 — Document the current detection parameters
# Executor action: note the window_size, threshold, and algorithm. Write findings to build log.

# W3.3 — Review the 0.1.10 event log for the degenerate event
command rg "degenerate\|Wait.*checking\|killed" data/aho_event_log.jsonl | tail -10

# W3.4 — Analyze: does "Wait, checking..." evade the rolling-window detector?
# The rolling-window detector catches repeated N-grams. "Wait, checking..." may vary slightly
# per iteration ("Wait, let me check...", "Wait, I need to check...") and not form a strict
# repeated N-gram. If that's the case, the detector needs a secondary signal:
#   - Information density: measure unique tokens per window. If the ratio of unique tokens to
#     total tokens drops below a threshold (e.g. 0.3), flag as degenerate even without strict
#     repetition.
#   - Stall detection: if N seconds pass with fewer than M *new* unique tokens appearing in
#     the stream, flag as stalled.
#
# Executor action: if the fix is straightforward (adding an information-density check to the
# existing detector), implement it. If it requires significant architecture, document the
# finding in the build log and propose a concrete fix for a future run.

# W3.5 — If implementing a fix, add a test
# Executor action: write a test that feeds "Wait, checking... Wait, let me verify..."
# repeated with slight variation into the detector and asserts it raises DegenerateGenerationError.

# W3.6 — Run tests
python3 -m pytest tests/ -v 2>&1 | tail -10

# W3.7 — Log W3 complete
printf '**Actions:**\n- Documented repetition detector parameters: (window_size, threshold, algorithm)\n- Analyzed "Wait, checking..." degenerate pattern from 0.1.10\n- (Implemented fix / Documented finding for future run)\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md
```

---

### W4 — Dogfood + close (60 min)

```fish
# W4.0 — Log W4 start
printf '## W4 — Dogfood + Close\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md

# W4.1 — Verify manual build log has workstream headers
command grep -c "^## W[0-9]" docs/iterations/0.1.11/aho-build-log-0.1.11.md
# Expected: 4 (W0-W3, W4 in progress)

# W4.2 — Build log synthesis
./bin/aho iteration build-log 0.1.11

# W4.3 — Report synthesis
./bin/aho iteration report 0.1.11

# W4.4 — Close (no --confirm)
./bin/aho iteration close

# W4.5 — Verification 1: close produced aho-run-0.1.11.md, NOT aho-run-report-0.1.11.md
test -f docs/iterations/0.1.11/aho-run-0.1.11.md; and echo "V1 PASS"; or echo "V1 FAIL"
test ! -f docs/iterations/0.1.11/aho-run-report-0.1.11.md; and echo "V1b PASS"; or echo "V1b FAIL: old filename still generated"

# W4.6 — Verification 2: bundle §5 references aho-run-0.1.11.md
command grep "aho-run-0.1.11.md" docs/iterations/0.1.11/aho-bundle-0.1.11.md; and echo "V2 PASS"; or echo "V2 FAIL"

# W4.7 — Verification 3: no run-report references in src
command rg -c "run-report" src/aho/ 2>/dev/null
# Expected: 0 (PASS) or only within comments/historical context

# W4.8 — Verification 4: test suite green
python3 -m pytest tests/ -v 2>&1 | tail -5
# Expected: 0 failures → V4 PASS

# W4.9 — Verification 5: §22 has ≥6 components
python3 -c "
import re
bundle = open('docs/iterations/0.1.11/aho-bundle-0.1.11.md').read()
m = re.search(r'## §22\. Agentic Components(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
if not m:
    print('V5 FAIL: §22 not found')
else:
    rows = [line for line in m.group().split('\n') if line.startswith('|') and not line.startswith('|---')]
    components = set()
    for row in rows[1:]:
        cells = [c.strip() for c in row.split('|') if c.strip()]
        if cells:
            components.add(cells[0])
    print(f'Components: {sorted(components)}, count={len(components)}')
    print('V5 PASS' if len(components) >= 6 else f'V5 FAIL: only {len(components)}')
"

# W4.10 — Verification 6: manual build log in bundle §3
python3 -c "
import re
bundle = open('docs/iterations/0.1.11/aho-bundle-0.1.11.md').read()
m = re.search(r'## §3\. Build Log(.*?)(?=^## §4)', bundle, re.MULTILINE | re.DOTALL)
if m and 'MISSING' not in m.group(1) and 'W0' in m.group(1):
    print('V6 PASS')
else:
    print('V6 FAIL')
"

# W4.11 — Log W4 complete
printf '**Actions:**\n- Generated synthesis, report, run file, bundle\n- V1 run file named aho-run-0.1.11.md: (pass/fail)\n- V2 bundle §5 references new name: (pass/fail)\n- V3 no run-report refs in src: (pass/fail)\n- V4 test suite green: (pass/fail)\n- V5 §22 ≥6 components: (pass/fail)\n- V6 manual build log in §3: (pass/fail)\n\n**Discrepancies:** (fill in)\n\n---\n\n' >> docs/iterations/0.1.11/aho-build-log-0.1.11.md
```

---

## Section D — Post-flight checks

```fish
command grep -c "^## W[0-9]" docs/iterations/0.1.11/aho-build-log-0.1.11.md
# Expected: 5 (W0-W4)

command du -h docs/iterations/0.1.11/aho-bundle-0.1.11.md

python3 -m pytest tests/ -v 2>&1 | tail -3
```

---

## Section E — Rollback procedure

```fish
set BACKUP_DIR (command pwd).backup-pre-0.1.11
cp $BACKUP_DIR/run_report.py src/aho/feedback/run_report.py
cp -r $BACKUP_DIR/postflight/* src/aho/postflight/
cp -r $BACKUP_DIR/bundle/* src/aho/bundle/
cp $BACKUP_DIR/repetition_detector.py src/aho/artifacts/repetition_detector.py

jq '.iteration = "0.1.10"' .aho-checkpoint.json > .aho-checkpoint.json.tmp
mv .aho-checkpoint.json.tmp .aho-checkpoint.json

sed -i 's/__version__ = "0.1.11"/__version__ = "0.1.10"/' src/aho/cli.py
sed -i 's/^version = "0.1.11"/version = "0.1.10"/' pyproject.toml
pip install -e . --break-system-packages --quiet

printf '# INCOMPLETE\n\n0.1.11 rolled back %s.\nReason: (fill in)\n' (date -u +%Y-%m-%d) > docs/iterations/0.1.11/INCOMPLETE.md

python3 -m pytest tests/ -v
```

---

## Section F — Wall clock estimate

| Workstream | Target | Cumulative |
|---|---|---|
| W0 — Environment hygiene | 20 min | 0:20 |
| W1 — Run file filename rename | 60 min | 1:20 |
| W2 — Test suite hygiene | 45 min | 2:05 |
| W3 — Qwen degenerate investigation | 45 min | 2:50 |
| W4 — Dogfood + close | 60 min | 3:50 |

**Soft cap:** 3:50

---

*Plan generated 2026-04-10, aho 0.1.11 planning*
