# aho — Plan 0.1.12

**Run:** 0.1.12
**Phase:** 0
**Predecessor:** 0.1.11 (graduated with conditions)
**Wall clock target:** ~2.5 hours
**Workstreams:** W0-W4

---

## Section A — Pre-flight

```fish
cd ~/dev/projects/aho
command pwd
# Expected: /home/kthompson/dev/projects/aho

./bin/aho --version
# Expected: aho 0.1.11

jq .last_completed_iteration .aho-checkpoint.json
# Expected: "0.1.11"

command ls docs/iterations/0.1.12/aho-design-0.1.12.md docs/iterations/0.1.12/aho-plan-0.1.12.md

python3 -m pytest tests/ -v 2>&1 | tail -5
```

---

## Section C — Workstreams

### W0 — Environment hygiene (15 min)

```fish
mkdir -p docs/iterations/0.1.12
printf '# Build Log — aho 0.1.12\n\n**Start:** %s\n**Agent:** %s\n**Phase:** 0\n**Run:** 0.1.12\n**Theme:** Evaluator baseline reload + smoke checkpoint-awareness + model-fleet.md cleanup\n\n---\n\n' (date -u +%Y-%m-%dT%H:%M:%SZ) "$AHO_EXECUTOR" > docs/iterations/0.1.12/aho-build-log-0.1.12.md

set BACKUP_DIR ~/dev/projects/aho.backup-pre-0.1.12
mkdir -p $BACKUP_DIR
cp src/aho/artifacts/evaluator.py $BACKUP_DIR/
cp scripts/smoke_instrumentation.py $BACKUP_DIR/
cp docs/harness/model-fleet.md $BACKUP_DIR/
cp data/gotcha_archive.json $BACKUP_DIR/

jq '.iteration = "0.1.12" | .last_completed_iteration = "0.1.11"' .aho-checkpoint.json > .tmp && mv .tmp .aho-checkpoint.json
sed -i 's/__version__ = "0.1.11"/__version__ = "0.1.12"/' src/aho/cli.py
sed -i 's/^version = "0.1.11"/version = "0.1.12"/' pyproject.toml
pip install -e . --break-system-packages --quiet
./bin/aho --version
```

### W1 — Evaluator baseline reload (aho-G060) (60 min)

```fish
printf '## W1 — Evaluator baseline reload (aho-G060)\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md

# W1.1 — Locate the baseline load site
command rg -n "get_allowed_scripts\|get_allowed_cli_commands\|_baseline_cache" src/aho/artifacts/evaluator.py

# W1.2 — Executor action: edit evaluator.py
# Find the module-level baseline cache (likely a global dict or a @lru_cache decorator).
# Replace with per-call computation inside evaluate_text():
#
#   def evaluate_text(text, artifact_type=None):
#       allowed_scripts = get_allowed_scripts()  # now called per-invocation
#       allowed_cli = get_allowed_cli_commands()
#       ...
#
# Ensure get_allowed_scripts() walks scripts/ and src/aho/ fresh each call.
# Expected overhead: ~10ms per evaluation. Acceptable.

# W1.3 — Register aho-G060 in gotcha_archive.json
python3 <<'PYEOF'
import json
p = "data/gotcha_archive.json"
d = json.load(open(p))
new_gotcha = {
    "code": "aho-G060",
    "title": "Evaluator dynamic baseline loads at init, misses files created mid-run",
    "surfaced_in": "0.1.11 W4",
    "description": "The evaluator's allowed-files baseline loaded at module init, before the current run's W1 could create or rename files. Synthesis runs that referenced newly-created files were rejected as hallucinations, causing a 2-hour rejection loop in 0.1.11.",
    "fix": "Reload baseline inside evaluate_text() on every call. ~10ms overhead, correct in the presence of mid-run file changes.",
    "status": "fixed in 0.1.12 W1"
}
gotchas = d.get("gotchas", d if isinstance(d, list) else [])
if any(g.get("code") == "aho-G060" for g in gotchas):
    print("aho-G060 already registered")
else:
    gotchas.append(new_gotcha)
    if isinstance(d, list):
        json.dump(gotchas, open(p, "w"), indent=2)
    else:
        d["gotchas"] = gotchas
        json.dump(d, open(p, "w"), indent=2)
    print("Registered aho-G060")
PYEOF

# W1.4 — Regression test
cat > tests/test_evaluator_reload.py <<'PYEOF'
"""Verify evaluator baseline reloads on every evaluate_text call."""
from pathlib import Path


def test_newly_created_script_is_recognized(tmp_path, monkeypatch):
    from aho.artifacts import evaluator
    new_script = Path("scripts/aho_g060_reload_test.py")
    new_script.write_text("# reload test\n")
    try:
        result = evaluator.evaluate_text(
            "This run uses scripts/aho_g060_reload_test.py to verify reload.",
            artifact_type="test"
        )
        assert "aho_g060_reload_test.py" not in str(result.errors), \
            f"New script flagged as hallucinated: {result.errors}"
    finally:
        new_script.unlink()
PYEOF

python3 -m pytest tests/test_evaluator_reload.py -v

printf '**Actions:**\n- Replaced init-time baseline load with per-call reload in evaluator.py\n- Registered aho-G060 in gotcha_archive.json\n- Added regression test tests/test_evaluator_reload.py\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md
```

### W2 — smoke_instrumentation checkpoint-awareness (aho-G061) (30 min)

```fish
printf '## W2 — smoke_instrumentation checkpoint-awareness (aho-G061)\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md

# W2.1 — Find current iteration source in the script
command rg -n "iteration\|IAO_ITERATION\|AHO_ITERATION" scripts/smoke_instrumentation.py

# W2.2 — Executor action: edit smoke_instrumentation.py
# At script start, add:
#   import json
#   from pathlib import Path
#   _checkpoint = json.loads(Path(".aho-checkpoint.json").read_text())
#   ITERATION = _checkpoint["iteration"]
# Remove any env var or hardcoded iteration value.
# Pass ITERATION explicitly to every log_event call (or set it as a module-level default).

# W2.3 — Register aho-G061
python3 <<'PYEOF'
import json
p = "data/gotcha_archive.json"
d = json.load(open(p))
new_gotcha = {
    "code": "aho-G061",
    "title": "Scripts emitting events should read iteration from checkpoint not env",
    "surfaced_in": "0.1.11 W4",
    "description": "smoke_instrumentation.py logged events stamped with the previous iteration version because it read from an env var that wasn't re-exported after checkpoint bump.",
    "fix": "Scripts that emit events must read iteration from .aho-checkpoint.json at script start.",
    "status": "fixed in 0.1.12 W2"
}
gotchas = d.get("gotchas", d if isinstance(d, list) else [])
if not any(g.get("code") == "aho-G061" for g in gotchas):
    gotchas.append(new_gotcha)
    if isinstance(d, list):
        json.dump(gotchas, open(p, "w"), indent=2)
    else:
        d["gotchas"] = gotchas
        json.dump(d, open(p, "w"), indent=2)
    print("Registered aho-G061")
PYEOF

# W2.4 — Smoke test
set BEFORE (command wc -l < data/aho_event_log.jsonl)
python3 scripts/smoke_instrumentation.py
set AFTER (command wc -l < data/aho_event_log.jsonl)
command tail -n (math $AFTER - $BEFORE) data/aho_event_log.jsonl | command grep '"iteration": "0.1.12"' | command wc -l
# Expected: non-zero — events stamped with current iteration

printf '**Actions:**\n- Updated smoke_instrumentation.py to read iteration from .aho-checkpoint.json\n- Registered aho-G061\n- Smoke test: events stamped 0.1.12 correctly\n\n---\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md
```

### W3 — model-fleet.md harness doc cleanup (20 min)

```fish
printf '## W3 — model-fleet.md cleanup\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md

# W3.1 — Review current state
command rg -n "IAO\|iao\b" docs/harness/model-fleet.md

# W3.2 — Targeted edits via sed (identifier references only)
sed -i 's/^# IAO Model Fleet/# aho Model Fleet/' docs/harness/model-fleet.md
sed -i 's/^\*\*Version:\*\* 0\.1\.4/**Version:** 0.1.12/' docs/harness/model-fleet.md
sed -i 's/^\*\*Scope:\*\* Universal IAO fleet/**Scope:** Universal aho fleet/' docs/harness/model-fleet.md
sed -i 's/The IAO Model Fleet/The aho Model Fleet/' docs/harness/model-fleet.md
sed -i 's/IAO utilizes/aho utilizes/' docs/harness/model-fleet.md
sed -i 's/IAO iteration loop/aho iteration loop/' docs/harness/model-fleet.md
sed -i 's/IAO templates/aho templates/' docs/harness/model-fleet.md
sed -i 's/by the `iao` CLI/by the `aho` CLI/' docs/harness/model-fleet.md
sed -i 's/IAO ensures/aho ensures/' docs/harness/model-fleet.md
sed -i 's|the Trident.*Performance and Security prongs|Pillars 1 (delegate everything delegable) and 8 (efficacy measured in cost delta)|' docs/harness/model-fleet.md
sed -i 's/^\*Document produced for iao 0\.1\.4 W2\.6\.\*/*Document updated for aho 0.1.12 W3.*/' docs/harness/model-fleet.md

# Also bump agents-architecture.md header (it references iao 0.1.7 but body uses src/aho/)
sed -i 's/^# Agents Architecture — iao 0\.1\.7/# Agents Architecture — aho 0.1.12/' docs/harness/agents-architecture.md
sed -i 's/^\*\*Version:\*\* 0\.1\.7/**Version:** 0.1.12/' docs/harness/agents-architecture.md

# W3.3 — Verify
command rg -n "^# IAO\|IAO Model Fleet\|IAO utilizes" docs/harness/model-fleet.md
# Expected: 0

printf '**Actions:**\n- Updated model-fleet.md: title, version 0.1.4→0.1.12, IAO identifier references to aho\n- Replaced "Trident" prong references with Pillar 1 and Pillar 8\n- Bumped agents-architecture.md header from 0.1.7 to 0.1.12\n- Historical phase charter iao-phase-0.md left unchanged\n\n---\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md
```

### W4 — Dogfood + close (45 min)

```fish
printf '## W4 — Dogfood + close\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md

./bin/aho iteration build-log 0.1.12
./bin/aho iteration report 0.1.12
./bin/aho iteration close

# V1 — Synthesis non-empty (aho-G060 fix proof)
test -s docs/iterations/0.1.12/aho-build-log-synthesis-0.1.12.md; and echo "V1 PASS"; or echo "V1 FAIL: synthesis empty"

# V2 — Event log stamped 0.1.12 (aho-G061 fix proof)
command grep -c '"iteration": "0.1.12"' data/aho_event_log.jsonl
# Expected: non-zero

# V3 — model-fleet.md clean
command rg -c "^# IAO\|IAO utilizes\|Version:\*\* 0\.1\.4" docs/harness/model-fleet.md
# Expected: 0

# V4 — §22 components
python3 -c "
import re
b = open('docs/iterations/0.1.12/aho-bundle-0.1.12.md').read()
m = re.search(r'## §22(.*?)(?=^## §|\Z)', b, re.MULTILINE | re.DOTALL)
rows = [l for l in m.group().split('\n') if l.startswith('|') and not l.startswith('|---')]
comps = set()
for r in rows[1:]:
    cells = [c.strip() for c in r.split('|') if c.strip()]
    if cells: comps.add(cells[0])
print(f'Components: {sorted(comps)}')
print('V4 PASS' if len(comps) >= 6 else f'V4 FAIL: {len(comps)}')
"

# V5 — Manual build log in §3
python3 -c "
import re
b = open('docs/iterations/0.1.12/aho-bundle-0.1.12.md').read()
m = re.search(r'## §3\. Build Log(.*?)## §4', b, re.DOTALL)
print('V5 PASS' if m and 'MISSING' not in m.group(1) and 'W0' in m.group(1) else 'V5 FAIL')
"

# V6 — Run file named correctly
test -f docs/iterations/0.1.12/aho-run-0.1.12.md; and echo "V6 PASS"; or echo "V6 FAIL"

# V7 — Tests green
python3 -m pytest tests/ -v 2>&1 | tail -5

printf '**Verification results:**\n- V1 synthesis non-empty: (pass/fail)\n- V2 event log stamped 0.1.12: (pass/fail)\n- V3 model-fleet.md clean: (pass/fail)\n- V4 §22 ≥6 components: (pass/fail)\n- V5 manual build log in §3: (pass/fail)\n- V6 run file named correctly: (pass/fail)\n- V7 tests green: (pass/fail)\n\n---\n\n' >> docs/iterations/0.1.12/aho-build-log-0.1.12.md
```

---

## Section E — Rollback

```fish
set BD ~/dev/projects/aho.backup-pre-0.1.12
cp $BD/evaluator.py src/aho/artifacts/evaluator.py
cp $BD/smoke_instrumentation.py scripts/smoke_instrumentation.py
cp $BD/model-fleet.md docs/harness/model-fleet.md
cp $BD/gotcha_archive.json data/gotcha_archive.json
jq '.iteration = "0.1.11"' .aho-checkpoint.json > .tmp && mv .tmp .aho-checkpoint.json
sed -i 's/__version__ = "0.1.12"/__version__ = "0.1.11"/' src/aho/cli.py
sed -i 's/^version = "0.1.12"/version = "0.1.11"/' pyproject.toml
pip install -e . --break-system-packages --quiet
```

---

## Section F — Wall clock

| Workstream | Target | Cumulative |
|---|---|---|
| W0 — Env hygiene | 15 min | 0:15 |
| W1 — aho-G060 reload fix | 60 min | 1:15 |
| W2 — aho-G061 smoke script | 30 min | 1:45 |
| W3 — model-fleet.md cleanup | 20 min | 2:05 |
| W4 — Dogfood + close | 45 min | 2:50 |

**Soft cap:** 2:50
