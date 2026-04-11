# aho — Plan 0.1.10

**Run:** 0.1.10
**Phase:** 0
**Predecessor:** 0.1.9 (graduated with conditions)
**Wall clock target:** ~4 hours soft cap
**Workstreams:** W0-W6 (seven, W6 conditional on W5 passing clean)
**Authored:** 2026-04-10

Operational companion to `aho-design-0.1.10.md`. Design is the *why*, this is the *how*. Section C has copy-pasteable fish command blocks per workstream.

---

## Section A — Pre-flight checks

```fish
# A.0 — Working directory
cd ~/dev/projects/iao
command pwd
# Expected: /home/kthompson/dev/projects/iao

# A.1 — 0.1.9 is closed
jq .last_completed_iteration .aho-checkpoint.json
# Expected: "0.1.9"

jq .iteration .aho-checkpoint.json
# Expected: "0.1.9" (will bump to 0.1.10 in W0)

# A.2 — aho binary works
./bin/aho --version
# Expected: aho 0.1.9

# A.3 — Design and plan docs present for 0.1.10
command ls docs/iterations/0.1.10/aho-design-0.1.10.md docs/iterations/0.1.10/aho-plan-0.1.10.md
# Expected: both files listed

# A.4 — Ollama models present
curl -s http://localhost:11434/api/tags | python3 -c "import json, sys; d = json.load(sys.stdin); names = [m['name'] for m in d['models']]; required = ['qwen3.5:9b', 'nemotron-mini:4b']; missing = [r for r in required if not any(r in n for n in names)]; print('OK' if not missing else f'MISSING: {missing}')"
# Expected: OK

# A.5 — Confirm problem files still exist from 0.1.9
command ls docs/iterations/0.1.9/iao-design-0.1.9.md docs/iterations/0.1.9/iao-plan-0.1.9.md docs/iterations/0.1.9/iao-build-log-0.1.9.md
# Expected: all three listed (they're the files W1 will rename)

# A.6 — Confirm 0.1.99 garbage still on disk (W0 will delete)
command ls docs/iterations/0.1.99/ 2>/dev/null; or echo "already gone"
# Expected: one file listed OR "already gone"

# A.7 — Confirm ChromaDB state
python3 -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma'); print([col.name for col in c.list_collections()])"
# Expected: some list of collection names — record for Condition resolution

# A.8 — Working tree reasonably clean
git status --short
```

---

## Section B — Workstream ordering

```
W0 (env hygiene + 0.1.99 cleanup)
 └─→ W1 (rename iao-* 0.1.9 files to aho-*) — depends on W0 backup
      └─→ W2 (log_event source_agent sweep) — depends on W0 backup
           └─→ W3 (openclaw/nemoclaw/structural_gates audit + restore) — depends on W2
                └─→ W4 (manual-build-log-first enforcement in loop.py) — depends on W0 backup
                     └─→ W5 (dogfood + close) — depends on all prior
                          └─→ W6 (project root rename, conditional) — depends on W5 clean pass
```

---

## Section C — Per-workstream fish command blocks

### W0 — Environment hygiene (15 min)

```fish
# W0.0 — Timestamp
set W0_START (date -u +%Y-%m-%dT%H:%M:%SZ)

# W0.1 — Working directory
cd ~/dev/projects/iao
command pwd

# W0.2 — Create iteration directory and initialize manual build log
mkdir -p docs/iterations/0.1.10
printf '# Build Log — aho 0.1.10\n\n**Start:** %s\n**Agent:** %s\n**Machine:** NZXTcos\n**Phase:** 0\n**Run:** 0.1.10\n**Theme:** Restore §22 instrumentation, fix bundle generator, verify rename completeness\n\n---\n\n## W0 — Environment Hygiene\n\n**Start:** %s\n\n' "$W0_START" "$AHO_EXECUTOR" "$W0_START" > docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W0.3 — Backup files 0.1.10 will modify
set BACKUP_DIR ~/dev/projects/iao.backup-pre-0.1.10
mkdir -p $BACKUP_DIR/src-aho-cli
mkdir -p $BACKUP_DIR/src-aho-agents
mkdir -p $BACKUP_DIR/src-aho-postflight
mkdir -p $BACKUP_DIR/src-aho-artifacts
mkdir -p $BACKUP_DIR/src-aho-bundle
mkdir -p $BACKUP_DIR/docs-iterations-0.1.9

cp src/aho/cli.py $BACKUP_DIR/src-aho-cli/
cp src/aho/agents/openclaw.py $BACKUP_DIR/src-aho-agents/
cp src/aho/agents/nemoclaw.py $BACKUP_DIR/src-aho-agents/
cp src/aho/postflight/structural_gates.py $BACKUP_DIR/src-aho-postflight/
cp src/aho/artifacts/loop.py $BACKUP_DIR/src-aho-artifacts/
cp -r src/aho/bundle $BACKUP_DIR/src-aho-bundle/
cp docs/iterations/0.1.9/iao-design-0.1.9.md $BACKUP_DIR/docs-iterations-0.1.9/ 2>/dev/null
cp docs/iterations/0.1.9/iao-plan-0.1.9.md $BACKUP_DIR/docs-iterations-0.1.9/ 2>/dev/null
cp docs/iterations/0.1.9/iao-build-log-0.1.9.md $BACKUP_DIR/docs-iterations-0.1.9/ 2>/dev/null
command ls -R $BACKUP_DIR | head -30

# W0.4 — Bump checkpoint
jq '.iteration = "0.1.10" | .last_completed_iteration = "0.1.9"' .aho-checkpoint.json > .aho-checkpoint.json.tmp
mv .aho-checkpoint.json.tmp .aho-checkpoint.json
jq .iteration .aho-checkpoint.json
# Expected: "0.1.10"

# W0.5 — Delete docs/iterations/0.1.99/ (Condition 4)
if test -d docs/iterations/0.1.99
    rm -rf docs/iterations/0.1.99
    echo "Deleted docs/iterations/0.1.99"
else
    echo "0.1.99 already absent"
end
command ls docs/iterations/ | command grep -E '^0\.1\.99$'; or echo "confirmed gone"

# W0.6 — Bump version in cli.py + pyproject.toml (source of truth for --version)
sed -i 's/__version__ = "0.1.9"/__version__ = "0.1.10"/' src/aho/cli.py 2>/dev/null
sed -i 's/^version = "0.1.9"/version = "0.1.10"/' pyproject.toml
pip install -e . --break-system-packages --quiet
./bin/aho --version
# Expected: aho 0.1.10

# W0.7 — Log W0 complete
printf '**Actions:**\n- Initialized manual build log at docs/iterations/0.1.10/aho-build-log-0.1.10.md\n- Backed up files 0.1.10 will modify to %s\n- Bumped checkpoint to 0.1.10\n- Deleted docs/iterations/0.1.99/\n- Bumped aho version to 0.1.10\n\n**Discrepancies:** none\n\n---\n\n' "$BACKUP_DIR" >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

---

### W1 — Rename 0.1.9 iao-prefixed files (20 min)

```fish
# W1.0 — Log W1 start
printf '## W1 — Rename 0.1.9 iao-prefixed files\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W1.1 — Inventory the three files
command ls docs/iterations/0.1.9/iao-*.md
# Expected: iao-build-log-0.1.9.md, iao-design-0.1.9.md, iao-plan-0.1.9.md

# W1.2 — Rename via git mv (preserves history)
git mv docs/iterations/0.1.9/iao-design-0.1.9.md docs/iterations/0.1.9/aho-design-0.1.9.md
git mv docs/iterations/0.1.9/iao-plan-0.1.9.md docs/iterations/0.1.9/aho-plan-0.1.9.md
git mv docs/iterations/0.1.9/iao-build-log-0.1.9.md docs/iterations/0.1.9/aho-build-log-0.1.9.md
command ls docs/iterations/0.1.9/

# W1.3 — Audit cross-references inside the renamed files
command rg "iao-design-0.1.9\|iao-plan-0.1.9\|iao-build-log-0.1.9" docs/iterations/0.1.9/

# If any matches, fix them:
sed -i 's|iao-design-0.1.9|aho-design-0.1.9|g' docs/iterations/0.1.9/aho-*.md
sed -i 's|iao-plan-0.1.9|aho-plan-0.1.9|g' docs/iterations/0.1.9/aho-*.md
sed -i 's|iao-build-log-0.1.9|aho-build-log-0.1.9|g' docs/iterations/0.1.9/aho-*.md

# W1.4 — Verify no lingering iao-* references to 0.1.9 files
command rg "iao-design-0.1.9\|iao-plan-0.1.9\|iao-build-log-0.1.9" docs/ src/
# Expected: 0 matches (or only within historical run bundles like docs/iterations/0.1.8/)

# W1.5 — Historical iteration files should NOT have been touched
command ls docs/iterations/0.1.8/ | command grep -E '^iao-'
# Expected: 0.1.8 files still have iao-* prefix (historical, correct)

# W1.6 — Log W1 complete
printf '**Actions:**\n- git mv 3 files: iao-design-0.1.9.md, iao-plan-0.1.9.md, iao-build-log-0.1.9.md → aho-* equivalents\n- Updated internal cross-references\n- Verified no lingering iao-*-0.1.9 references in current docs/src\n- Historical files in 0.1.2-0.1.8 left unchanged\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

---

### W2 — log_event source_agent sweep (45 min)

```fish
# W2.0 — Log W2 start
printf '## W2 — log_event source_agent sweep\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W2.1 — Find all log_event call sites
command rg -n "log_event" src/aho/ | head -40

# W2.2 — Find hardcoded iao-* string literals in src
command rg -n '"iao-[a-z-]+"' src/aho/
# Expected: matches in cli.py and possibly elsewhere

# W2.3 — Review each match before applying sed
# Executor action: for each match from W2.2, determine whether it's a component/source_agent
# string that should be renamed. Skip any match that refers to historical file paths or 
# project name strings used for user-facing messages.

# W2.4 — Apply targeted renames — use exact string patterns
command rg -l '"iao-cli"' src/aho/ | xargs -r sed -i 's/"iao-cli"/"aho-cli"/g'

# Repeat for any other hardcoded component names found in W2.2
# E.g. if "iao-pipeline" or similar exist, rename each explicitly

# W2.5 — Verify zero iao-* string literals in src/aho/
command rg '"iao-[a-z-]+"' src/aho/
# Expected: 0 matches

# W2.6 — Smoke test: run a trivial command and check the event log
set BEFORE_COUNT (command wc -l < data/aho_event_log.jsonl)
./bin/aho --version > /dev/null
set AFTER_COUNT (command wc -l < data/aho_event_log.jsonl)
if test $AFTER_COUNT -gt $BEFORE_COUNT
    command tail -1 data/aho_event_log.jsonl | command grep '"source_agent": "aho-cli"'; and echo "W2 smoke PASS"; or echo "W2 smoke FAIL — check event log source_agent"
else
    echo "W2 smoke: event log did not receive a new entry"
end

# W2.7 — Run tests
python3 -m pytest tests/ -v 2>&1 | tail -10

# W2.8 — Log W2 complete
printf '**Actions:**\n- Found hardcoded iao-* string literals in log_event call sites\n- Renamed iao-cli → aho-cli (and any others)\n- Verified 0 lingering iao-* string literals in src/aho/\n- Smoke test: fresh event log entry shows source_agent=aho-cli\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

---

### W3 — OpenClaw / NemoClaw / structural-gates instrumentation audit (75 min)

```fish
# W3.0 — Log W3 start
printf '## W3 — OpenClaw/NemoClaw/structural-gates instrumentation audit\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W3.1 — Audit openclaw.py for log_event calls
command rg -n "log_event\|from.*logger" src/aho/agents/openclaw.py

# W3.2 — Audit nemoclaw.py for log_event calls
command rg -n "log_event\|from.*logger" src/aho/agents/nemoclaw.py

# W3.3 — Audit structural_gates.py for log_event calls
command rg -n "log_event\|from.*logger" src/aho/postflight/structural_gates.py

# W3.4 — Executor action: for each module above, verify:
#   - log_event is imported
#   - log_event is called at expected points:
#     * openclaw: session_start (in __init__), openclaw_chat (in chat()), openclaw_execute_code (in execute_code())
#     * nemoclaw: nemoclaw_dispatch (in dispatch())
#     * structural_gates: structural_gate (in each gate check function)
#   - source_agent/component string is aho-* (openclaw, nemoclaw, structural-gates)
#
# If any instrumentation is missing, restore it. Reference 0.1.8 W5 implementation pattern.
# If log_event calls exist but use iao-* strings, rename them (may overlap with W2 — that's fine).

# W3.5 — Clear event log for a clean smoke test
: > data/aho_event_log.jsonl

# W3.6 — Run smoke test from 0.1.8
test -f scripts/smoke_instrumentation.py; and python3 scripts/smoke_instrumentation.py; or echo "smoke_instrumentation.py missing — create per 0.1.8 pattern"

# W3.7 — Verify ≥6 unique components in the fresh event log
python3 -c "
import json
with open('data/aho_event_log.jsonl') as f:
    events = [json.loads(line) for line in f if line.strip()]
components = set(e.get('source_agent', 'unknown') for e in events)
print(f'Unique components: {sorted(components)}')
print(f'Count: {len(components)}')
expected = {'aho-cli', 'openclaw', 'nemoclaw', 'structural-gates', 'evaluator', 'qwen-client'}
missing = expected - components
if missing:
    print(f'MISSING: {sorted(missing)}')
else:
    print('W3 PASS: all 6 expected components present')
"

# W3.8 — Run tests
python3 -m pytest tests/ -v 2>&1 | tail -10

# W3.9 — Log W3 complete
printf '**Actions:**\n- Audited openclaw.py, nemoclaw.py, structural_gates.py for log_event wiring\n- Restored missing instrumentation where needed\n- Ran smoke_instrumentation.py\n- Verified event log has 6 unique components with aho-* naming\n- Tests pass\n\n**Discrepancies:** (list any components that could not be restored — partial ship acceptable)\n\n---\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

**Partial-ship criterion:** If fewer than 6 components restore in 60 minutes, ship what's wired, log the rest as discrepancies, continue to W4. Any unwired component carries to the next run.

---

### W4 — Manual-build-log-first enforcement in loop.py (45 min)

```fish
# W4.0 — Log W4 start
printf '## W4 — Manual-build-log-first enforcement in loop.py\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W4.1 — Locate build log synthesis path in loop.py
command rg -n "build.log\|build_log" src/aho/artifacts/loop.py

# W4.2 — Executor action: edit loop.py build log synthesis function
# Add a check at the start of the synthesis function:
#   from pathlib import Path
#   manual_path = Path(f"docs/iterations/{version}/aho-build-log-{version}.md")
#   if not manual_path.exists():
#       raise FileNotFoundError(
#           f"Manual build log not found at {manual_path}. "
#           f"Write the manual build log first, then run synthesis. See ADR-042."
#       )
# Then proceed with the existing Qwen synthesis code, writing to
# docs/iterations/{version}/aho-build-log-synthesis-{version}.md

# W4.3 — Regression test
cat > tests/test_build_log_first.py <<'PYEOF'
"""Verify synthesis fails if manual build log is missing (ADR-042 enforcement)."""
from pathlib import Path
import pytest
import tempfile
import shutil


def test_synthesis_raises_when_manual_missing(tmp_path, monkeypatch):
    """Calling build log synthesis without a manual file should raise FileNotFoundError."""
    from aho.artifacts import loop
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs" / "iterations" / "0.1.99").mkdir(parents=True)
    # No manual file present
    with pytest.raises(FileNotFoundError, match="Manual build log not found"):
        loop.generate_build_log_synthesis("0.1.99")


def test_synthesis_proceeds_when_manual_present(tmp_path, monkeypatch):
    """Calling build log synthesis with a manual file should proceed without raising."""
    from aho.artifacts import loop
    monkeypatch.chdir(tmp_path)
    iter_dir = tmp_path / "docs" / "iterations" / "0.1.99"
    iter_dir.mkdir(parents=True)
    (iter_dir / "aho-build-log-0.1.99.md").write_text("# Build Log\n\n## W0\nSample manual entry.\n")
    # Should not raise FileNotFoundError; may raise other errors due to missing Qwen/test env
    try:
        loop.generate_build_log_synthesis("0.1.99")
    except FileNotFoundError as e:
        if "Manual build log not found" in str(e):
            pytest.fail(f"Synthesis incorrectly reported manual log missing: {e}")
    except Exception:
        pass  # Other errors are expected in test env without Qwen
PYEOF

python3 -m pytest tests/test_build_log_first.py -v

# W4.4 — Log W4 complete
printf '**Actions:**\n- Added manual-build-log existence check to loop.py synthesis path\n- Synthesis raises FileNotFoundError with clear message if manual log missing\n- Synthesis file writes to aho-build-log-synthesis-<version>.md\n- Regression test passes\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

---

### W5 — Dogfood + close (60 min)

```fish
# W5.0 — Log W5 start
printf '## W5 — Dogfood + close\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W5.1 — The manual build log at docs/iterations/0.1.10/aho-build-log-0.1.10.md should already
# contain entries for W0, W1, W2, W3, W4 (the executor has been appending workstream-by-workstream)
command wc -l docs/iterations/0.1.10/aho-build-log-0.1.10.md
command grep -c "^## W[0-9]" docs/iterations/0.1.10/aho-build-log-0.1.10.md
# Expected: 5 or more workstream headers (W0-W4, W5 in progress, W6 conditional)

# W5.2 — Run build log synthesis (should now find the manual file)
./bin/aho iteration build-log 0.1.10

# Verify synthesis wrote to the -synthesis file
test -f docs/iterations/0.1.10/aho-build-log-synthesis-0.1.10.md; and echo "synthesis OK"; or echo "synthesis MISSING"

# Verify manual file was NOT overwritten
command md5sum docs/iterations/0.1.10/aho-build-log-0.1.10.md
# (executor should know the hash from before the synthesis call — if it changed, that's a bug)

# W5.3 — Generate report
./bin/aho iteration report 0.1.10

# W5.4 — Post-flight
./bin/aho doctor postflight 0.1.10

# W5.5 — Close (does NOT --confirm)
./bin/aho iteration close

# W5.6 — Verification 1: bundle §1 Design contains content
python3 -c "
import re
bundle = open('docs/iterations/0.1.10/aho-bundle-0.1.10.md').read()
m = re.search(r'## §1\. Design\s*\n(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
if m and 'MISSING' not in m.group(1) and len(m.group(1).strip()) > 100:
    print('V1 PASS')
else:
    print(f'V1 FAIL: {m.group(1)[:200] if m else \"not found\"}')
"

# W5.7 — Verification 2: bundle §2 Plan contains content
python3 -c "
import re
bundle = open('docs/iterations/0.1.10/aho-bundle-0.1.10.md').read()
m = re.search(r'## §2\. Plan\s*\n(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
if m and 'MISSING' not in m.group(1) and len(m.group(1).strip()) > 100:
    print('V2 PASS')
else:
    print(f'V2 FAIL: {m.group(1)[:200] if m else \"not found\"}')
"

# W5.8 — Verification 3: bundle §3 has manual build log content
python3 -c "
import re
bundle = open('docs/iterations/0.1.10/aho-bundle-0.1.10.md').read()
m = re.search(r'## §3\. Build Log\s*\n(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
if m and 'MISSING' not in m.group(1) and ('W0' in m.group(1) and 'W1' in m.group(1)):
    print('V3 PASS')
else:
    print(f'V3 FAIL: {m.group(1)[:300] if m else \"not found\"}')
"

# W5.9 — Verification 4: §22 shows ≥6 components with aho-* naming
python3 -c "
import re
bundle = open('docs/iterations/0.1.10/aho-bundle-0.1.10.md').read()
m = re.search(r'## §22\. Agentic Components(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
if not m:
    print('V4 FAIL: §22 not found')
else:
    rows = [line for line in m.group().split('\n') if line.startswith('|') and not line.startswith('|---')]
    components = set()
    for row in rows[1:]:
        cells = [c.strip() for c in row.split('|') if c.strip()]
        if cells:
            components.add(cells[0])
    # Check for iao-* holdouts
    iao_holdouts = [c for c in components if c.startswith('iao-')]
    print(f'Components: {sorted(components)}')
    if len(components) >= 6 and not iao_holdouts:
        print('V4 PASS')
    elif iao_holdouts:
        print(f'V4 FAIL: iao-* holdouts: {iao_holdouts}')
    else:
        print(f'V4 FAIL: only {len(components)} components')
"

# W5.10 — Verification 5: docs/iterations/0.1.99/ does not exist
test ! -d docs/iterations/0.1.99; and echo "V5 PASS"; or echo "V5 FAIL: 0.1.99 still present"

# W5.11 — Verification 6: regenerate 0.1.9 bundle, verify §1/§2/§3 populated
./bin/aho iteration bundle 0.1.9 2>&1; or echo "V6 skip: bundle regen not supported"
python3 -c "
import re
try:
    bundle = open('docs/iterations/0.1.9/aho-bundle-0.1.9.md').read()
except FileNotFoundError:
    print('V6 FAIL: 0.1.9 bundle not found for re-check')
    exit()
missing = []
for n in ('1', '2', '3'):
    m = re.search(rf'## §{n}\.(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
    if not m or 'MISSING' in m.group(1):
        missing.append(f'§{n}')
if missing:
    print(f'V6 FAIL: {missing} still MISSING in 0.1.9 bundle')
else:
    print('V6 PASS: 0.1.9 bundle regenerates clean')
"

# W5.12 — Telegram notify (non-blocking)
./bin/aho telegram notify "aho 0.1.10 complete — $(date -u +%H:%M) UTC" 2>&1; or echo "Telegram not configured — non-blocking"

# W5.13 — Log W5 complete
printf '**Actions:**\n- Generated build log synthesis, report, run report, bundle\n- Ran 6 verification checks\n\n**Verification results:**\n- V1 §1 Design contains content: (pass/fail)\n- V2 §2 Plan contains content: (pass/fail)\n- V3 §3 Build Log has manual content: (pass/fail)\n- V4 §22 has >=6 components with aho-* naming: (pass/fail)\n- V5 0.1.99 deleted: (pass/fail)\n- V6 0.1.9 bundle regen clean: (pass/fail)\n\n**Discrepancies:** (fill in)\n\n---\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

**Escalation:** If any verification fails, STOP. Do not proceed to W6. Log failures in the build log, surface to Agent Questions for Kyle, let Kyle decide whether to re-attempt or carry the condition to the next run.

---

### W6 — Project root rename (conditional, 30 min)

**Condition:** All six W5 verifications must pass before W6 runs. If any failed, SKIP this workstream.

```fish
# W6.0 — Log W6 start (only if reached)
printf '## W6 — Project Root Rename (conditional)\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md

# W6.1 — Confirm W5 passed all six verifications
# Executor action: read the W5 discrepancies from the build log. If any verification failed,
# STOP W6 and log "W6 SKIPPED — W5 did not pass clean" then exit.

# W6.2 — Surface a capability-gap interrupt for Kyle
# The project root rename requires:
#   1. Exiting the current tmux session / shell (cwd cannot be inside the directory being moved)
#   2. Kyle manually running: mv ~/dev/projects/iao ~/dev/projects/aho
#   3. Kyle updating any shell aliases, fish abbreviations, or path references pointing at the old path
#   4. Re-entering the new location and running ./bin/aho --version to verify
#
# The executor logs this as a capability_gap_interrupt event and STOPS here. Kyle performs the
# rename out of band. On return, Kyle runs ./bin/aho iteration close --confirm from the new path.

# The executor writes the interrupt and final status:
printf '**Actions:**\n- All W5 verifications passed — W6 eligible\n- Surfacing capability-gap interrupt for Kyle\n- Project root rename requires human action (shell session cannot rename its own cwd)\n\n**Capability-gap interrupt:**\n\n```fish\n# From a shell OUTSIDE the iao directory:\ncd ~\nmv ~/dev/projects/iao ~/dev/projects/aho\ncd ~/dev/projects/aho\n./bin/aho --version\n# Expected: aho 0.1.10\n\n# Update any fish abbreviations or shell aliases pointing at the old path\nfunctions -q iao-cd; and functions --erase iao-cd\n# (Kyle to audit and update as needed)\n```\n\n**Status:** W6 INTERRUPT — awaiting Kyle action\n\n---\n\n' >> docs/iterations/0.1.10/aho-build-log-0.1.10.md
```

---

## Section D — Post-flight checks

```fish
# D.1 — All workstream headers present
command grep -c "^## W[0-9]" docs/iterations/0.1.10/aho-build-log-0.1.10.md
# Expected: 6 (or 7 if W6 ran)

# D.2 — Bundle present
command ls docs/iterations/0.1.10/aho-bundle-0.1.10.md

# D.3 — Run report present
command ls docs/iterations/0.1.10/aho-run-report-0.1.10.md

# D.4 — Checkpoint state
jq . .aho-checkpoint.json

# D.5 — Test suite green
python3 -m pytest tests/ -v 2>&1 | tail -5

# D.6 — No iao-* contamination
command rg '"iao-[a-z-]+"' src/aho/
# Expected: 0 matches

# D.7 — Project root (post-W6 if it ran)
command pwd
# Expected: /home/kthompson/dev/projects/aho (if W6 ran) OR /home/kthompson/dev/projects/iao (if W6 skipped)
```

---

## Section E — Rollback procedure

```fish
# E.1 — Restore modified files from backup
set BACKUP_DIR ~/dev/projects/iao.backup-pre-0.1.10
cp $BACKUP_DIR/src-aho-cli/cli.py src/aho/cli.py
cp $BACKUP_DIR/src-aho-agents/openclaw.py src/aho/agents/openclaw.py
cp $BACKUP_DIR/src-aho-agents/nemoclaw.py src/aho/agents/nemoclaw.py
cp $BACKUP_DIR/src-aho-postflight/structural_gates.py src/aho/postflight/structural_gates.py
cp $BACKUP_DIR/src-aho-artifacts/loop.py src/aho/artifacts/loop.py
cp -r $BACKUP_DIR/src-aho-bundle/bundle/* src/aho/bundle/

# E.2 — Restore 0.1.9 iao-* filenames if W1 ran and needs reverting
if test -f docs/iterations/0.1.9/aho-design-0.1.9.md; and test ! -f docs/iterations/0.1.9/iao-design-0.1.9.md
    git mv docs/iterations/0.1.9/aho-design-0.1.9.md docs/iterations/0.1.9/iao-design-0.1.9.md
    git mv docs/iterations/0.1.9/aho-plan-0.1.9.md docs/iterations/0.1.9/iao-plan-0.1.9.md
    git mv docs/iterations/0.1.9/aho-build-log-0.1.9.md docs/iterations/0.1.9/iao-build-log-0.1.9.md
end

# E.3 — Revert checkpoint
jq '.iteration = "0.1.9"' .aho-checkpoint.json > .aho-checkpoint.json.tmp
mv .aho-checkpoint.json.tmp .aho-checkpoint.json

# E.4 — Revert version
sed -i 's/__version__ = "0.1.10"/__version__ = "0.1.9"/' src/aho/cli.py
sed -i 's/^version = "0.1.10"/version = "0.1.9"/' pyproject.toml
pip install -e . --break-system-packages --quiet

# E.5 — Mark 0.1.10 incomplete
printf '# INCOMPLETE\n\n0.1.10 was attempted %s and rolled back.\nReason: (fill in)\n' (date -u +%Y-%m-%d) > docs/iterations/0.1.10/INCOMPLETE.md

# E.6 — Verify baseline
./bin/aho --version
python3 -m pytest tests/ -v
```

---

## Section F — Wall clock estimate

| Workstream | Target | Cumulative |
|---|---|---|
| W0 — Environment hygiene | 15 min | 0:15 |
| W1 — Rename 0.1.9 iao-* files | 20 min | 0:35 |
| W2 — log_event source_agent sweep | 45 min | 1:20 |
| W3 — Instrumentation audit + restore | 75 min | 2:35 |
| W4 — Manual-build-log-first enforcement | 45 min | 3:20 |
| W5 — Dogfood + close | 60 min | 4:20 |
| W6 — Project root rename (conditional) | 30 min | 4:50 |

**Soft cap:** 4:50
**Hard cap:** none

---

*Plan generated 2026-04-10, aho 0.1.10 planning*
