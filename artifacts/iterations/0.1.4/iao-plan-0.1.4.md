# iao — Plan 0.1.4

**Iteration:** 0.1.4 (three octets, locked — do not add a fourth)
**Phase:** 0 (NZXT-only authoring)
**Date:** April 09, 2026
**Machine:** NZXTcos
**Repo:** ~/dev/projects/iao
**Wall clock target:** ~8 hours soft cap (no hard cap)
**Run mode:** Single executor — Gemini CLI
**Status:** Planning

This plan operationalizes `iao-design-0.1.4.md`. Read the design first if you haven't. The design defines *what* and *why*; this plan defines *how* and *in what order*, in commands Gemini can paste and run.

Every command block in this plan is fish-shell compatible and copy-pasteable. Commands are grouped by workstream. Each workstream block is atomic — Gemini runs all commands in the block, then updates the checkpoint and moves on. If a command fails, Gemini retries up to 3 times (Pillar 7), then surfaces to the build log as a discrepancy and continues to the next workstream unless the failure is blocking.

---

## What is iao

iao is the methodology and Python package for running disciplined LLM-driven engineering iterations. iao 0.1.4 integrates the local model fleet (Qwen, Nemotron, GLM, ChromaDB), migrates kjtcom's harness registries into iao's universal layer, lays foundations for telegram and openclaw/nemoclaw, corrects the run-report mechanism that shipped broken in 0.1.3, and is the first iteration where Gemini CLI is the sole executor. See `iao-design-0.1.4.md` for the why.

---

## Section A — Pre-flight

### A.0 — Working directory and shell state

```fish
cd ~/dev/projects/iao
pwd
# Expected: /home/kthompson/dev/projects/iao

command ls -la .iao.json VERSION pyproject.toml
# Expected: all three files present
```

**Failure remediation:** If any file missing, wrong directory. Restore from `~/dev/projects/iao.backup-pre-0.1.3` or Kyle's latest backup.

### A.1 — Create 0.1.4 backup

```fish
test -d ~/dev/projects/iao.backup-pre-0.1.4
# Expected: fails (no backup yet)

cp -a ~/dev/projects/iao ~/dev/projects/iao.backup-pre-0.1.4
test -d ~/dev/projects/iao.backup-pre-0.1.4
# Expected: succeeds (exit 0)

du -sh ~/dev/projects/iao.backup-pre-0.1.4
# Expected: matches current project size
```

### A.2 — Git state clean (if git-tracked)

```fish
cd ~/dev/projects/iao
test -d .git; and git status --porcelain
# If .git exists: expected no output (clean)
# If .git does not exist: command fails silently (Phase 0 may not be git-tracked yet)
```

**Failure remediation:** If git is dirty, Kyle commits or stashes manually. Per Pillar 0, Gemini does not run `git commit`.

### A.3 — Python environment

```fish
python3 --version
# Expected: 3.14.x

which python3
# Expected: /usr/bin/python3

pip --version
# Expected: pip 25.x

which iao
# Expected: ~/.local/bin/iao
```

### A.4 — iao package functional

```fish
iao --version
# Expected: 0.1.3 (will bump to 0.1.4 in W0)

python3 -c "import iao; print(iao.__file__)"
# Expected: path under src/iao/__init__.py

iao doctor quick 2>&1 | head -20
# Expected: may fail because doctor CLI is missing (that's a W1 fix)
# If it fails, note in build log and continue — does not block launch
```

### A.5 — Ollama daemon and models

```fish
curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; d=json.load(sys.stdin); print('\n'.join(m['name'] for m in d['models']))"
# Expected output includes:
#   qwen3.5:9b
#   nemotron-mini:4b (or similar)
#   haervwe/GLM-4.6V-Flash-9B (or similar)
#   nomic-embed-text
```

**Failure remediation:** If Ollama not running, `systemctl --user start ollama`. If any model missing, `ollama pull <model_name>`.

### A.6 — Disk space

```fish
df -h ~/dev/projects/iao | tail -1
# Expected: at least 10G free (ChromaDB seeding needs headroom)
```

### A.7 — Sleep/suspend masked

```fish
systemctl status sleep.target 2>&1 | grep -E "Loaded|Active"
# Expected: "masked" or "Loaded: masked"
```

**Failure remediation:** `sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target`

### A.8 — `.iao.json` reflects 0.1.3 close state

```fish
jq .current_iteration .iao.json
# Expected: "0.1.3"

jq .last_completed_iteration .iao.json
# Expected: "0.1.3" (set by Kyle's manual close)

jq .phase .iao.json
# Expected: 0
```

### A.9 — No conflicting tmux session

```fish
tmux ls 2>/dev/null | grep "iao-0.1.4"
# Expected: no output
```

### A.10 — Required tools present (age may be missing — W1 installs)

```fish
which git python3 pip ollama jq keyctl
# Expected: all present

which age
# Expected: may fail (W1 installs)

npm list -g @google/gemini-cli 2>/dev/null
# Expected: shows gemini-cli version
```

### A.11 — Pre-flight summary printed

```fish
echo "PRE-FLIGHT COMPLETE
===================
Working dir: $(pwd)
Python: $(python3 --version)
iao: $(iao --version 2>&1)
Ollama models: $(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(len(json.load(sys.stdin)['models']))") present
Disk: $(df -h . | awk 'NR==2 {print \$4}') free

READY TO LAUNCH iao 0.1.4"
```

---

## Section B — Launch Protocol

### B.1 — Open tmux session

```fish
tmux new-session -d -s iao-0.1.4 -c ~/dev/projects/iao
tmux send-keys -t iao-0.1.4 'cd ~/dev/projects/iao' Enter
tmux send-keys -t iao-0.1.4 'set -x IAO_ITERATION 0.1.4' Enter
tmux send-keys -t iao-0.1.4 'set -x IAO_PROJECT_NAME iao' Enter
```

### B.2 — Initialize checkpoint

```fish
set ts (date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s\n' '{
  "iteration": "0.1.4",
  "phase": 0,
  "started_at": "'$ts'",
  "current_workstream": "W0",
  "workstreams": {
    "W0": {"status": "pending", "executor": "gemini-cli"},
    "W1": {"status": "pending", "executor": "gemini-cli"},
    "W2": {"status": "pending", "executor": "gemini-cli"},
    "W3": {"status": "pending", "executor": "gemini-cli"},
    "W4": {"status": "pending", "executor": "gemini-cli"},
    "W5": {"status": "pending", "executor": "gemini-cli"},
    "W6": {"status": "pending", "executor": "gemini-cli"},
    "W7": {"status": "pending", "executor": "gemini-cli"}
  },
  "completed_at": null,
  "mode": "single-executor"
}' > .iao-checkpoint.json

cat .iao-checkpoint.json | jq .iteration
# Expected: "0.1.4"
```

### B.3 — Launch Gemini CLI

```fish
tmux send-keys -t iao-0.1.4 'gemini --yolo' Enter
```

Gemini reads `GEMINI.md` at session start. GEMINI.md references this plan doc for per-workstream execution detail. Gemini executes W0 through W7 sequentially, pausing only at W3 for Kyle's AMBIGUOUS review and at W7 for Kyle's final review.

### B.4 — Monitor progress

Kyle attaches occasionally to observe. The iteration runs in the background. Expected wall clock: 8 hours. Telegram notifications (once W4 completes and W6 is wired) will ping Kyle at iteration close.

### B.5 — Iteration close

When Gemini completes W7, the iteration is in review pending state. Run report is at `docs/iterations/0.1.4/iao-run-report-0.1.4.md`. Kyle reviews, fills in notes, ticks sign-off boxes, runs `iao iteration close --confirm`.

---

## Section C — Workstream Execution Details

### W0 — Iteration Bookkeeping

**Executor:** Gemini CLI
**Wall clock target:** 10 min

```fish
cd ~/dev/projects/iao

# Update .iao.json to 0.1.4 (three octets exactly)
jq '.current_iteration = "0.1.4" | .phase = 0' .iao.json > .iao.json.tmp
mv .iao.json.tmp .iao.json

jq .current_iteration .iao.json
# Expected: "0.1.4"

# Update VERSION
echo "0.1.4" > VERSION
cat VERSION
# Expected: 0.1.4

# Update pyproject.toml
sed -i 's/version = "0.1.3"/version = "0.1.4"/' pyproject.toml
grep 'version = ' pyproject.toml | head -3
# Expected: version = "0.1.4" for iao

# Update CLI version string
grep -n "0.1.3" src/iao/cli.py
# Find the version string
sed -i 's/"iao 0.1.3"/"iao 0.1.4"/' src/iao/cli.py
grep 'iao 0.1' src/iao/cli.py

# Reinstall to pick up version
pip install -e . --break-system-packages --quiet

iao --version
# Expected: iao 0.1.4

# Append to build log
mkdir -p docs/iterations/0.1.4
printf '# Build Log — iao 0.1.4\n\n**Start:** %s\n**Executor:** gemini-cli\n**Machine:** NZXTcos\n**Phase:** 0\n**Iteration:** 0.1.4\n**Theme:** Model fleet integration, kjtcom harness migration, Telegram/OpenClaw foundations, Gemini-primary refactor, 0.1.3 cleanup\n\n---\n\n## W0 — Iteration Bookkeeping\n\n**Status:** COMPLETE\n**Wall clock:** ~5 min\n\nActions:\n- .iao.json current_iteration → 0.1.4 (three octets, no suffix)\n- VERSION → 0.1.4\n- pyproject.toml version → 0.1.4\n- cli.py version string → iao 0.1.4\n- Reinstalled via pip install -e .\n- iao --version returns 0.1.4\n\n---\n\n' (date -u +%Y-%m-%dT%H:%M:%SZ) > docs/iterations/0.1.4/iao-build-log-0.1.4.md

# Mark W0 complete in checkpoint
jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W0.status = "complete" | .workstreams.W0.completed_at = $ts | .current_workstream = "W1"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

**Acceptance:**
- `iao --version` returns `iao 0.1.4`
- `jq .current_iteration .iao.json` returns `"0.1.4"`
- `grep -rEn "0\.1\.4\.[0-9]+" src/ prompts/ 2>/dev/null` returns zero matches (no fourth octet anywhere)
- Build log exists at `docs/iterations/0.1.4/iao-build-log-0.1.4.md`

---

### W1 — 0.1.3 Cleanup

**Executor:** Gemini CLI
**Wall clock target:** 90 min

This workstream has 8 sub-deliverables. Gemini executes each in order, verifies each, then updates the checkpoint.

#### W1.1 — Fix run report checkpoint-read bug

```fish
# Read current run_report.py
cat src/iao/feedback/run_report.py

# Find where checkpoint is read. Look for early reads (module-level or __init__).
grep -n "checkpoint" src/iao/feedback/run_report.py

# The fix: ensure checkpoint is read inside generate_run_report() at render time,
# not at module import or module load.

# Gemini inspects the code, identifies the issue, and rewrites the affected function.
# Typical fix pattern:
#   - Move `with open(".iao-checkpoint.json") as f: checkpoint = json.load(f)`
#     from module level to the top of generate_run_report()
#   - OR: if already inside the function, verify it reads the file fresh
#         rather than a cached variable

# After fix, verify by running:
python3 -c "
from iao.feedback.run_report import generate_run_report
import json
from pathlib import Path
# Read checkpoint state
with open('.iao-checkpoint.json') as f:
    checkpoint = json.load(f)
# Check that W0 shows complete (we just completed it)
print('W0 status in checkpoint:', checkpoint['workstreams']['W0']['status'])
"
# Expected: W0 status in checkpoint: complete
```

Gemini edits `src/iao/feedback/run_report.py` directly via the Edit tool. The fix is small — move the checkpoint read to the render function entry point.

#### W1.2 — Question extraction from build log

```fish
# Create the extraction module
cat > src/iao/feedback/questions.py <<'PYEOF'
"""Extract agent questions from build log and event log for run report."""
import re
import json
from pathlib import Path


QUESTION_MARKER_RE = re.compile(
    r"(?:Agent Question for Kyle|Agent Question|Question for Kyle)[:\-]\s*(.+?)(?=\n\n|\n#|\n---|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def extract_questions_from_build_log(build_log_path: Path) -> list[str]:
    """Extract questions from build log markers.

    Looks for lines starting with 'Agent Question for Kyle:' or similar
    and collects the text until the next blank line, section, or EOF.
    """
    if not build_log_path.exists():
        return []
    content = build_log_path.read_text()
    matches = QUESTION_MARKER_RE.findall(content)
    return [m.strip() for m in matches if m.strip()]


def extract_questions_from_event_log(event_log_path: Path, iteration: str) -> list[str]:
    """Extract questions from JSONL event log tagged with the current iteration."""
    if not event_log_path.exists():
        return []
    questions = []
    for line in event_log_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "agent_question" and event.get("iteration") == iteration:
            text = event.get("text") or event.get("question") or ""
            if text:
                questions.append(text)
    return questions


def collect_all_questions(iteration: str, build_log_path: Path, event_log_path: Path) -> list[str]:
    """Collect questions from both sources, deduplicated."""
    build_log_questions = extract_questions_from_build_log(build_log_path)
    event_log_questions = extract_questions_from_event_log(event_log_path, iteration)
    seen = set()
    combined = []
    for q in build_log_questions + event_log_questions:
        if q not in seen:
            seen.add(q)
            combined.append(q)
    return combined
PYEOF

# Wire into run_report.py — Gemini edits run_report.py to call collect_all_questions
# and populate the Agent Questions section with the result (or "(none — no questions
# surfaced during execution)" if empty)

# Verify the module imports
python3 -c "from iao.feedback.questions import collect_all_questions; print('ok')"
# Expected: ok
```

#### W1.3 — Run report quality gate

```fish
cat > src/iao/postflight/run_report_quality.py <<'PYEOF'
"""Post-flight check: run report quality gate."""
import json
from pathlib import Path


def check(version: str = None) -> dict:
    """Validate run report quality.

    Returns dict with status (PASS/FAIL/DEFERRED), message, errors.
    """
    if version is None:
        with open(".iao.json") as f:
            version = json.load(f).get("current_iteration", "")
    run_report_path = Path(f"docs/iterations/{version}/iao-run-report-{version}.md")

    if not run_report_path.exists():
        return {"status": "DEFERRED", "message": f"Run report does not exist at {run_report_path}", "errors": []}

    errors = []
    content = run_report_path.read_text()
    size_bytes = run_report_path.stat().st_size

    # Minimum size
    if size_bytes < 1500:
        errors.append(f"Run report size {size_bytes} < 1500 bytes minimum")

    # Workstream summary table — check for table rows
    if "| W0 |" not in content:
        errors.append("Workstream summary table missing W0 row")
    # Count workstream rows
    ws_row_count = sum(1 for line in content.splitlines() if line.strip().startswith("| W"))
    if ws_row_count < 4:
        errors.append(f"Workstream summary table has only {ws_row_count} rows (expected ≥ 4)")

    # Sign-off section with 5 checkboxes
    if "## Sign-off" not in content:
        errors.append("Sign-off section missing")
    checkbox_count = content.count("- [ ]") + content.count("- [x]") + content.count("- [X]")
    if checkbox_count < 5:
        errors.append(f"Sign-off section has {checkbox_count} checkboxes (expected ≥ 5)")

    # Agent questions section
    if "## Agent Questions" not in content:
        errors.append("Agent Questions section missing")

    if errors:
        return {"status": "FAIL", "message": f"{len(errors)} quality check failures", "errors": errors}
    return {"status": "PASS", "message": "Run report passes quality gate", "errors": []}
PYEOF

# Verify the check loads
python3 -c "from iao.postflight.run_report_quality import check; print(check.__doc__[:50])"
# Expected: Validate run report quality.
```

#### W1.4 — Bundle spec expansion to 21 sections

```fish
# Read current bundle.py
grep -n "BUNDLE_SPEC\|BundleSection" src/iao/bundle.py | head -30

# Gemini edits src/iao/bundle.py to:
# 1. Insert a new BundleSection after Report (§4):
#    BundleSection(5, "Run Report", source_path=Path("docs/iterations/{version}/iao-run-report-{version}.md"), min_chars=1500)
# 2. Renumber all subsequent sections: Harness 5→6, README 6→7, CHANGELOG 7→8, CLAUDE.md 8→9, GEMINI.md 9→10, .iao.json 10→11, Sidecars 11→12, Gotcha Registry 12→13, Script Registry 13→14, MANIFEST 14→15, install.fish 15→16, COMPATIBILITY 16→17, projects.json 17→18, Event Log 18→19, File Inventory 19→20, Environment 20→21
# 3. Update validate_bundle() to expect 21 sections

# After edit, verify
python3 -c "
from iao.bundle import BUNDLE_SPEC
print(f'Section count: {len(BUNDLE_SPEC)}')
for s in BUNDLE_SPEC:
    print(f'§{s.number}. {s.title}')
"
# Expected: Section count: 21
#           §1. Design, §2. Plan, §3. Build Log, §4. Report, §5. Run Report, ...

# Update base.md ADR-028 amendment
printf '\n### iaomw-ADR-028 Amendment (0.1.4)\n\nBUNDLE_SPEC expanded from 20 to 21 sections. Run Report inserted as §5 between Report (§4) and Harness (§6). All subsequent sections renumbered +1. 0.1.3 W5 introduced the Run Report artifact after W3 froze BUNDLE_SPEC; this amendment closes the gap.\n' >> docs/harness/base.md

# Update bundle_quality.py to check for 21 sections
sed -i 's/if len(BUNDLE_SPEC) != 20/if len(BUNDLE_SPEC) != 21/' src/iao/postflight/bundle_quality.py 2>/dev/null
grep "21" src/iao/postflight/bundle_quality.py | head -3
```

#### W1.5 — `iao doctor` CLI subcommand wired

```fish
# Inspect current cli.py
grep -n "subparsers\|add_parser\|doctor" src/iao/cli.py | head -20

# Gemini edits src/iao/cli.py to add:
#
#   doctor_parser = subparsers.add_parser("doctor", help="Run health checks")
#   doctor_subparsers = doctor_parser.add_subparsers(dest="doctor_level")
#   doctor_subparsers.add_parser("quick", help="Quick health check (sub-second)")
#   doctor_subparsers.add_parser("preflight", help="Pre-flight readiness check")
#   doctor_subparsers.add_parser("postflight", help="Post-flight verification")
#   doctor_subparsers.add_parser("full", help="Run all levels")
#
#   And in the main dispatch:
#   elif args.command == "doctor":
#       from iao.doctor import run_all
#       level = args.doctor_level or "quick"
#       result = run_all(level=level)
#       sys.exit(0 if result.get("passed") else 1)

# Verify
iao doctor quick 2>&1 | head -20
# Expected: runs without argparse error (may show check output or empty list)

iao doctor --help 2>&1
# Expected: shows quick/preflight/postflight/full subcommands
```

#### W1.6 — `iao log workstream-complete` signature reconciliation

```fish
# Inspect current signature
grep -A 20 "log.*workstream" src/iao/cli.py | head -40

# Reality: three positional args (workstream_id, status with choices, summary)
# Documentation expected: two positional args (workstream_id, summary)
# Decision: keep 3-arg signature, update docs

# Verify the signature
iao log workstream-complete --help 2>&1
# Expected: shows 3 positional args

# Update GEMINI.md (produced by chat) and CLAUDE.md (demoted to pointer in W6) to use correct signature
# Not fixing in this workstream — GEMINI.md is authored in chat, will already have correct signature
# CLAUDE.md is pointer-ified in W6

# Add a convenience alias for common case: treat 2-arg invocation as "pass" status
# Gemini may edit cli.py to handle `iao log workstream-complete W1 "summary"` by defaulting status to "pass"
# if only 2 args supplied. This is a UX improvement, not required.
```

#### W1.7 — Versioning regex validator

```fish
# Check if config.py exists
test -f src/iao/config.py; and cat src/iao/config.py
# If not exists, create it; if exists, append

cat >> src/iao/config.py <<'PYEOF'

# --- iao 0.1.4 W1.7: versioning regex validator ---

import re as _re

IAO_VERSION_REGEX = _re.compile(r"^\d+\.\d+\.\d+$")


def validate_iteration_version(version: str) -> None:
    """Raise ValueError if version string is not exactly three octets.

    iao versioning is locked to X.Y.Z. The Z field is the iteration
    run number, not a patch or minor. Four-octet versioning is a
    pattern-match error from kjtcom and must be rejected.
    """
    if not isinstance(version, str):
        raise ValueError(f"Version must be string, got {type(version).__name__}")
    if not IAO_VERSION_REGEX.match(version):
        raise ValueError(
            f"Iteration version '{version}' does not match X.Y.Z three-octet format. "
            f"iao versioning is locked to three octets; see iaomw-G107 in gotcha registry."
        )
PYEOF

# Wire validator into iteration close command
# Gemini edits src/iao/cli.py iteration_close function to call validate_iteration_version()
# before doing any work

# Grep entire codebase for any 4-octet patterns
grep -rEn "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" src/ prompts/ tests/ 2>/dev/null
# Expected: zero matches (fix any that surface)

# Verify validator
python3 -c "
from iao.config import validate_iteration_version
validate_iteration_version('0.1.4')  # ok
try:
    validate_iteration_version('0.1.4.0')
    print('FAIL: should have raised')
except ValueError as e:
    print(f'OK: {e}')
"
# Expected: OK: Iteration version '0.1.4.0' does not match ...

# Add G107 to gotcha registry
python3 -c "
import json
p = 'data/gotcha_archive.json'
with open(p) as f:
    registry = json.load(f)
registry.append({
    'id': 'iaomw-G107',
    'title': 'Four-octet versioning drift from kjtcom pattern-match',
    'status': 'Resolved',
    'action': 'iao versioning is locked to X.Y.Z three octets per 0.1.2 bootstrap session. kjtcom uses X.Y.Z.W because kjtcom Z is semantic; iao Z is the iteration run number. Do not pattern-match from kjtcom. Regex validator added in src/iao/config.py; iao iteration close rejects non-conforming version strings.',
    'source': 'iao 0.1.3 planning drift + 0.1.4 W1.7 resolution',
    'code': 'iaomw'
})
with open(p, 'w') as f:
    json.dump(registry, f, indent=2)
print('G107 added')
"
```

#### W1.8 — `age` binary installation

```fish
which age 2>/dev/null
# If present, skip

sudo pacman -S --noconfirm age
age --version
# Expected: 1.3.x

# Update install.fish if age isn't already listed
grep "age" install.fish
# If not present, Gemini appends the install line
```

#### W1 verification and checkpoint update

```fish
# Run full test suite
pytest tests/ -v
# Expected: all tests pass (new tests added for W1.1-W1.7 should be present)

# Final grep for four-octet drift
grep -rEn "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" src/ prompts/ 2>/dev/null
# Expected: zero matches

# Append to build log
printf '\n## W1 — 0.1.3 Cleanup\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W1.1: Fixed run_report.py checkpoint-read bug (render-time read)\n- W1.2: Created src/iao/feedback/questions.py for build log + event log extraction\n- W1.3: Created src/iao/postflight/run_report_quality.py (1500 byte minimum, workstream table rows, sign-off checkboxes)\n- W1.4: Expanded BUNDLE_SPEC to 21 sections with Run Report as §5; updated ADR-028 in base.md\n- W1.5: Wired iao doctor CLI subcommand with quick/preflight/postflight/full levels\n- W1.6: Reconciled iao log workstream-complete 3-arg signature documentation\n- W1.7: Added three-octet versioning regex validator in src/iao/config.py; added iaomw-G107 to gotcha registry\n- W1.8: Installed age 1.3.x via pacman\n- All tests pass\n\n---\n\n' >> docs/iterations/0.1.4/iao-build-log-0.1.4.md

# Checkpoint update
jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W1.status = "complete" | .workstreams.W1.completed_at = $ts | .current_workstream = "W2"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

**Acceptance:**
- All 8 sub-deliverables verified
- `iao doctor quick` runs without error
- `validate_iteration_version('0.1.4.0')` raises ValueError
- BUNDLE_SPEC has 21 sections
- `age --version` returns 1.3.x
- All tests pass

---

### W2 — Model Fleet Integration

**Executor:** Gemini CLI
**Wall clock target:** 120 min

#### W2.1 — ChromaDB archive seeding

```fish
# Check ChromaDB is available
python3 -c "import chromadb; print(chromadb.__version__)" 2>&1
# If error, install: pip install chromadb --break-system-packages
```

Gemini creates `src/iao/rag/archive.py` (see design §6 W2.1 for interface). Key implementation notes:

```fish
# Create the archive module
cat > src/iao/rag/archive.py <<'PYEOF'
"""ChromaDB archive collections for iao consumer projects.

Each project gets a collection {project_code}_archive populated from
docs/iterations/ with nomic-embed-text embeddings.
"""
import json
import hashlib
from pathlib import Path
from typing import Iterable

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

CHROMADB_PATH = Path.home() / ".local/share/iao/chromadb"


def _get_client():
    if chromadb is None:
        raise RuntimeError("chromadb not installed; pip install chromadb")
    CHROMADB_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMADB_PATH))


def _get_embedder():
    return embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text",
    )


def seed_project_archive(project_code: str, project_path: Path) -> int:
    """Seed or re-seed a project's archive collection.

    Returns the number of documents added.
    """
    client = _get_client()
    embedder = _get_embedder()
    collection_name = f"{project_code}_archive"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedder,
    )

    iterations_dir = project_path / "docs" / "iterations"
    if not iterations_dir.exists():
        return 0

    docs = []
    ids = []
    metas = []
    for iter_dir in sorted(iterations_dir.iterdir()):
        if not iter_dir.is_dir():
            continue
        iteration = iter_dir.name
        for md_file in iter_dir.glob("*.md"):
            content = md_file.read_text()
            if len(content) < 500:
                continue
            doc_id = hashlib.sha256(f"{project_code}:{iteration}:{md_file.name}".encode()).hexdigest()[:16]
            docs.append(content[:8000])
            ids.append(doc_id)
            metas.append({
                "project_code": project_code,
                "iteration": iteration,
                "filename": md_file.name,
                "artifact_type": md_file.stem.replace(f"{project_code.rstrip('w')}-", "").split("-")[0],
            })

    if docs:
        collection.add(documents=docs, ids=ids, metadatas=metas)
    return len(docs)


def query_archive(project_code: str, query: str, top_k: int = 5) -> list[dict]:
    client = _get_client()
    collection_name = f"{project_code}_archive"
    try:
        collection = client.get_collection(collection_name, embedding_function=_get_embedder())
    except Exception:
        return []
    results = collection.query(query_texts=[query], n_results=top_k)
    return [
        {"id": i, "document": d, "metadata": m, "distance": dist}
        for i, d, m, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def list_archives() -> dict[str, int]:
    client = _get_client()
    archives = {}
    for coll in client.list_collections():
        name = coll.name
        if name.endswith("_archive"):
            archives[name] = coll.count()
    return archives
PYEOF

# Seed iaomw archive
python3 -c "
from pathlib import Path
from iao.rag.archive import seed_project_archive
count = seed_project_archive('iaomw', Path.home() / 'dev/projects/iao')
print(f'iaomw_archive: {count} documents')
"
# Expected: iaomw_archive: N documents (where N >= 10)

# Seed kjtco archive (may take 10+ minutes)
python3 -c "
from pathlib import Path
from iao.rag.archive import seed_project_archive
count = seed_project_archive('kjtco', Path.home() / 'dev/projects/kjtcom')
print(f'kjtco_archive: {count} documents')
"
# Expected: kjtco_archive: N documents (where N >= 100)

# Seed tripl archive if tripledb exists
test -d ~/dev/projects/tripledb; and python3 -c "
from pathlib import Path
from iao.rag.archive import seed_project_archive
count = seed_project_archive('tripl', Path.home() / 'dev/projects/tripledb')
print(f'tripl_archive: {count} documents')
"

# Verify
python3 -c "
from iao.rag.archive import list_archives
for name, count in list_archives().items():
    print(f'{name}: {count}')
"
```

#### W2.2 — `nemotron_client.py`

```fish
cat > src/iao/artifacts/nemotron_client.py <<'PYEOF'
"""Nemotron-mini:4b client for classification, extraction, tagging, summarization.

Nemotron is fast on CPU and well-suited for narrow instruction-following tasks.
Not a replacement for Qwen on long-form generation.
"""
import json
import time
from typing import Any

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "nemotron-mini:4b"
TIMEOUT = 120
MAX_RETRIES = 3


def _call(prompt: str, format_json: bool = False) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    if format_json:
        payload["format"] = "json"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except (requests.RequestException, KeyError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)


def classify(text: str, categories: list[str], bias: str = "") -> str:
    """Classify text into one of the provided categories.

    bias: optional guidance like "When in doubt, prefer X"
    """
    cat_list = " | ".join(categories)
    prompt = f"""Classify the following text into exactly one of: {cat_list}

{bias}

Respond with ONLY the category name, nothing else.

Text to classify:
{text[:4000]}

Category:"""
    result = _call(prompt).strip()
    # Find the first category that matches
    for cat in categories:
        if cat.lower() in result.lower():
            return cat
    return categories[-1]  # fallback to last category (usually the conservative choice)


def extract(text: str, schema: dict) -> dict:
    """Extract structured data from text per schema."""
    schema_json = json.dumps(schema, indent=2)
    prompt = f"""Extract the following fields from the text below.
Return ONLY valid JSON matching this schema:
{schema_json}

Text:
{text[:4000]}

JSON:"""
    result = _call(prompt, format_json=True)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {}


def tag(text: str, tags: list[str]) -> list[str]:
    """Multi-label tagging. Returns tags that apply to the text."""
    tag_list = ", ".join(tags)
    prompt = f"""Which of these tags apply to the text below? Tags: {tag_list}

Text:
{text[:4000]}

Respond with a JSON list of applicable tags, e.g. ["tag1", "tag3"]:"""
    result = _call(prompt, format_json=True)
    try:
        parsed = json.loads(result)
        if isinstance(parsed, list):
            return [t for t in parsed if t in tags]
        return []
    except json.JSONDecodeError:
        return []


def summarize(text: str, max_words: int = 100) -> str:
    """Short summary generation."""
    prompt = f"""Summarize the following text in {max_words} words or fewer.
Respond with ONLY the summary, no preamble.

Text:
{text[:6000]}

Summary:"""
    return _call(prompt)
PYEOF

# Smoke test
python3 -c "
from iao.artifacts.nemotron_client import classify
result = classify('hello world', ['greeting', 'farewell'])
print(f'Classification: {result}')
"
# Expected: Classification: greeting
```

#### W2.3 — `glm_client.py`

```fish
cat > src/iao/artifacts/glm_client.py <<'PYEOF'
"""GLM-4.6V-Flash-9B client for vision + tier-2 text evaluation.

Vision-capable: can process images alongside text prompts.
Text-only: serves as tier-2 fallback when Qwen's output is questionable.
"""
import base64
import json
import time
from pathlib import Path
from typing import Optional

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "haervwe/GLM-4.6V-Flash-9B"
TIMEOUT = 180
MAX_RETRIES = 3


def _call(prompt: str, images: Optional[list[str]] = None, format_json: bool = False) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    if images:
        payload["images"] = images
    if format_json:
        payload["format"] = "json"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()["response"].strip()
        except (requests.RequestException, KeyError):
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)


def evaluate(prompt: str, text: str) -> dict:
    """Tier-2 text evaluator. Returns dict with score and rationale."""
    full_prompt = f"""{prompt}

Text to evaluate:
{text[:6000]}

Respond with JSON: {{"score": <1-10>, "rationale": "<brief>"}}"""
    result = _call(full_prompt, format_json=True)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"score": 0, "rationale": "parse_error"}


def describe_image(image_path: Path, prompt: str = "Describe this image") -> str:
    """Vision: describe the contents of an image."""
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()
    return _call(prompt, images=[image_b64])


def validate_diagram(image_path: Path, expected_elements: list[str]) -> dict:
    """Check that a diagram contains expected elements."""
    elements_str = ", ".join(expected_elements)
    prompt = f"""Examine this diagram image. Which of these elements are present? Elements: {elements_str}

Respond with JSON: {{"present": ["el1", "el2"], "missing": ["el3"]}}"""
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()
    result = _call(prompt, images=[image_b64], format_json=True)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"present": [], "missing": expected_elements}
PYEOF

# Smoke test (text-only)
python3 -c "
from iao.artifacts.glm_client import evaluate
result = evaluate('Score this text for clarity', 'The quick brown fox jumps over the lazy dog.')
print(f'GLM evaluation: {result}')
"
# Expected: dict with score and rationale
```

#### W2.4 — ChromaDB context enrichment

```fish
cat > src/iao/artifacts/context.py <<'PYEOF'
"""Context enrichment for Qwen artifact generation.

Queries ChromaDB archives for similar past artifacts and formats them as
in-context examples to prepend to Qwen's system prompt. Implements ADR-014
(context-over-constraint) via retrieval.
"""
from iao.rag.archive import query_archive


def build_context_for_artifact(
    project_code: str,
    artifact_type: str,
    current_iteration: str,
    topic: str,
    top_k: int = 3,
    max_words: int = 6000,
) -> str:
    """Build a context block of similar past artifacts.

    Returns markdown ready to embed in a system prompt.
    """
    query = f"{artifact_type} for {topic}"
    results = query_archive(project_code, query, top_k=top_k)
    results = [r for r in results if r["metadata"].get("iteration") != current_iteration]

    if not results:
        return ""

    blocks = []
    word_budget = max_words
    for r in results:
        meta = r["metadata"]
        content = r["document"]
        content_words = content.split()
        if len(content_words) > word_budget:
            content = " ".join(content_words[:word_budget])
        word_budget -= len(content.split())
        blocks.append(
            f"### Example: {meta.get('artifact_type', 'unknown')} from {meta.get('iteration', '?')}\n\n{content}\n"
        )
        if word_budget <= 0:
            break

    header = f"## In-Context Examples\n\nThe following are past {artifact_type} documents from {project_code} that may serve as structural and stylistic references. Use them as inspiration, not templates — your iteration has its own events and outcomes.\n\n"
    return header + "\n---\n\n".join(blocks)
PYEOF

# Wire into loop.py — Gemini edits src/iao/artifacts/loop.py to call
# build_context_for_artifact() before each Qwen generation and prepend
# the returned string to the system prompt.

# Smoke test
python3 -c "
from iao.artifacts.context import build_context_for_artifact
ctx = build_context_for_artifact('iaomw', 'design', '0.1.4', 'bundle quality gates')
print(f'Context length: {len(ctx)} chars')
print(ctx[:500])
"
```

#### W2.5 — Model fleet benchmark

```fish
cat > scripts/benchmark_fleet.py <<'PYEOF'
"""Benchmark Qwen, Nemotron, GLM against real iao iteration corpus."""
import json
import time
from pathlib import Path

from iao.artifacts.nemotron_client import _call as nemotron_call
from iao.artifacts.glm_client import _call as glm_call
import requests


def qwen_call(prompt: str) -> tuple[str, float]:
    start = time.monotonic()
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen3.5:9b", "prompt": prompt, "stream": False},
        timeout=300,
    )
    resp.raise_for_status()
    elapsed = time.monotonic() - start
    return resp.json()["response"], elapsed


def run_benchmark():
    tasks = [
        {
            "name": "short_classification",
            "prompt": "Classify as 'universal' or 'project-specific': 'Use printf not heredocs in fish shell'\nAnswer:",
            "expected_keywords": ["universal"],
        },
        {
            "name": "medium_extraction",
            "prompt": 'Extract the workstream ID and status from: "W3 completed in 15 minutes with 3 files touched"\nRespond with JSON: {"workstream": "...", "status": "..."}',
            "expected_keywords": ["W3", "complet"],
        },
        {
            "name": "long_generation",
            "prompt": "Write a 500-word summary of why bundle quality gates matter for LLM-driven engineering iterations.",
            "expected_keywords": ["bundle", "quality", "gate"],
        },
    ]

    results = []
    for task in tasks:
        print(f"\nTask: {task['name']}")
        for model_name, caller in [("qwen3.5:9b", qwen_call), ("nemotron-mini:4b", lambda p: (nemotron_call(p), -1)), ("GLM-4.6V-Flash-9B", lambda p: (glm_call(p), -1))]:
            try:
                start = time.monotonic()
                output, _ = caller(task["prompt"])
                elapsed = time.monotonic() - start
                word_count = len(output.split())
                matched = all(kw.lower() in output.lower() for kw in task["expected_keywords"])
                results.append({
                    "task": task["name"],
                    "model": model_name,
                    "elapsed_sec": round(elapsed, 2),
                    "word_count": word_count,
                    "matched": matched,
                    "output_preview": output[:200],
                })
                print(f"  {model_name}: {elapsed:.2f}s, {word_count} words, matched={matched}")
            except Exception as e:
                print(f"  {model_name}: ERROR {e}")
                results.append({"task": task["name"], "model": model_name, "error": str(e)})
    return results


if __name__ == "__main__":
    results = run_benchmark()
    output_path = Path("docs/harness/model-fleet-benchmark-0.1.4.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Model Fleet Benchmark — 0.1.4\n", "", "| Task | Model | Elapsed | Words | Matched |", "|---|---|---|---|---|"]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['task']} | {r['model']} | ERROR | - | - |")
        else:
            lines.append(f"| {r['task']} | {r['model']} | {r['elapsed_sec']}s | {r['word_count']} | {'✓' if r['matched'] else '✗'} |")
    output_path.write_text("\n".join(lines) + "\n")
    print(f"\nWritten: {output_path}")
PYEOF

python3 scripts/benchmark_fleet.py
# Expected: runs to completion and writes docs/harness/model-fleet-benchmark-0.1.4.md
```

#### W2.6 — `docs/harness/model-fleet.md`

Gemini authors this document following the design §6 W2.6 outline. Target ≥ 1500 words. Novice-operability check: Luke should be able to read this cold.

#### W2.7 — Base.md ADR-035

```fish
printf '\n### iaomw-ADR-035: Model Fleet Integration\n\n- **Context:** Qwen3.5:9b on CPU hits a ~1700-word ceiling per decode, and iao is blocked by the ceiling if Qwen is the only model in the loop. Nemotron-mini:4b and GLM-4.6V-Flash-9B are installed but unused. ChromaDB was migrated in 0.1.2 W5 but never integrated.\n- **Decision:** Wire the full fleet: Qwen (long-form generation), Nemotron (classification/extraction/tagging/summarization), GLM (vision + tier-2 text evaluator fallback), ChromaDB + nomic-embed-text (semantic retrieval of past artifacts for in-context enrichment).\n- **Rationale:** ADR-014 (context-over-constraint) says Qwen quality is a function of context richness. ChromaDB retrieval lets Qwen see three relevant past artifacts as few-shot examples rather than writing cold. Nemotron absorbs narrow tasks that would waste Qwen tokens. GLM unlocks vision and serves as evaluator fallback.\n- **Consequences:**\n  - src/iao/artifacts/nemotron_client.py, glm_client.py, context.py added in 0.1.4 W2\n  - src/iao/rag/archive.py seeds ChromaDB collections per project\n  - Loop.py prepends ChromaDB context before Qwen generation\n  - scripts/benchmark_fleet.py establishes baseline metrics\n  - docs/harness/model-fleet.md documents fleet roles for operators\n' >> docs/harness/base.md
```

#### W2 checkpoint update

```fish
printf '\n## W2 — Model Fleet Integration\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W2.1: ChromaDB archive collections seeded (iaomw, kjtco, tripl if exists)\n- W2.2: nemotron_client.py with classify/extract/tag/summarize\n- W2.3: glm_client.py with evaluate/describe_image/validate_diagram\n- W2.4: context.py with build_context_for_artifact, wired into loop.py\n- W2.5: scripts/benchmark_fleet.py run, output at docs/harness/model-fleet-benchmark-0.1.4.md\n- W2.6: docs/harness/model-fleet.md (≥ 1500 words)\n- W2.7: iaomw-ADR-035 in base.md\n\n---\n\n' >> docs/iterations/0.1.4/iao-build-log-0.1.4.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W2.status = "complete" | .workstreams.W2.completed_at = $ts | .current_workstream = "W3"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W3 — kjtcom Harness Migration

**Executor:** Gemini CLI (pauses mid-workstream for Kyle's review)
**Wall clock target:** 90 min (excluding Kyle's review time)

#### W3.1 — Gotcha registry migration with Nemotron classification

```fish
# Verify kjtcom's registry exists
test -f ~/dev/projects/kjtcom/data/gotcha_archive.json
command ls ~/dev/projects/kjtcom/data/ 2>/dev/null
# If kjtcom registry is at a different path, adapt below

# Read kjtcom gotchas and classify each
python3 <<'PYEOF'
import json
from pathlib import Path
from iao.artifacts.nemotron_client import classify

kjtcom_registry_path = Path.home() / "dev/projects/kjtcom/data/gotcha_archive.json"
iao_registry_path = Path("data/gotcha_archive.json")
migration_map_entries = []
ambiguous_pile = []

if not kjtcom_registry_path.exists():
    print(f"kjtcom registry not found at {kjtcom_registry_path}")
    # Gemini checks alternative paths
    exit(1)

with open(kjtcom_registry_path) as f:
    kjtcom_gotchas = json.load(f)

with open(iao_registry_path) as f:
    iao_gotchas = json.load(f)

# Find next available iaomw-G number
existing_ids = {g["id"] for g in iao_gotchas}
next_num = 108  # G001-G107 taken

classified_universal = []
classified_kjtcom_specific = []

bias = "When in doubt, prefer KJTCOM-SPECIFIC. Only classify as UNIVERSAL if the lesson would apply to any Python + Ollama + fish-shell engineering iteration regardless of project. Classify as AMBIGUOUS only if the lesson is clearly universal but the examples or references tie to kjtcom too tightly for automated migration."

for g in kjtcom_gotchas:
    text = f"ID: {g.get('id')}\nTitle: {g.get('title', '')}\nAction: {g.get('action', '')[:500]}"
    category = classify(text, ["UNIVERSAL", "KJTCOM-SPECIFIC", "AMBIGUOUS"], bias=bias)

    if category == "UNIVERSAL":
        new_id = f"iaomw-G{next_num}"
        next_num += 1
        new_entry = {
            "id": new_id,
            "title": g.get("title", ""),
            "status": g.get("status", "Resolved"),
            "action": g.get("action", ""),
            "source": f"migrated from kjtcom {g.get('id')} in iao 0.1.4 W3",
            "code": "iaomw",
            "kjtcom_source_id": g.get("id"),
        }
        iao_gotchas.append(new_entry)
        classified_universal.append((g.get("id"), new_id))
        migration_map_entries.append(f"| {g.get('id')} | {new_id} | UNIVERSAL | yes |")
    elif category == "KJTCOM-SPECIFIC":
        classified_kjtcom_specific.append(g.get("id"))
        migration_map_entries.append(f"| {g.get('id')} | - | KJTCOM-SPECIFIC | no |")
    else:  # AMBIGUOUS
        ambiguous_pile.append(g)
        migration_map_entries.append(f"| {g.get('id')} | TBD | AMBIGUOUS | pending_review |")

# Write updated iao registry
with open(iao_registry_path, "w") as f:
    json.dump(iao_gotchas, f, indent=2)

print(f"UNIVERSAL (auto-migrated): {len(classified_universal)}")
print(f"KJTCOM-SPECIFIC (skipped): {len(classified_kjtcom_specific)}")
print(f"AMBIGUOUS (pending review): {len(ambiguous_pile)}")

# Write ambiguous pile to review file
if ambiguous_pile:
    review_path = Path("/tmp/iao-0.1.4-ambiguous-gotchas.md")
    lines = ["# Ambiguous Gotchas Review — iao 0.1.4 W3\n", ""]
    lines.append(f"Nemotron classified {len(ambiguous_pile)} kjtcom gotchas as AMBIGUOUS. Kyle must rule on each: UNIVERSAL (migrate) or KJTCOM-SPECIFIC (skip).\n")
    lines.append("")
    for i, g in enumerate(ambiguous_pile, 1):
        lines.append(f"## {i}. {g.get('id')}: {g.get('title', '')}\n")
        lines.append(f"**Action:** {g.get('action', '')}\n")
        lines.append(f"**Ruling:** ___________ (write UNIVERSAL or KJTCOM-SPECIFIC)\n")
        lines.append("")
    review_path.write_text("\n".join(lines))
    print(f"\n⚠ AMBIGUOUS REVIEW REQUIRED")
    print(f"  {len(ambiguous_pile)} entries written to {review_path}")
    print(f"  Kyle: review and rule on each, then resume with:")
    print(f"  iao iteration resume W3")
    exit(42)  # special exit code meaning "paused for review"
PYEOF
```

If exit code 42 is returned, Gemini writes to the build log:

```fish
printf '\n### W3 PAUSED for Kyle review\n\nNemotron classified %s kjtcom gotchas as AMBIGUOUS. Review file at /tmp/iao-0.1.4-ambiguous-gotchas.md. W3 resumes via `iao iteration resume W3` after Kyle provides rulings.\n' (wc -l < /tmp/iao-0.1.4-ambiguous-gotchas.md) >> docs/iterations/0.1.4/iao-build-log-0.1.4.md

# Send a desktop notification if available
notify-send "iao 0.1.4 W3 paused" "Ambiguous gotcha review required" 2>/dev/null
```

Gemini then either (a) proceeds to W4 if Kyle has indicated async review is acceptable, or (b) waits for Kyle to rule and run resume.

**Kyle's side (in chat):** Kyle pastes the ambiguous list, rules on each entry, Claude web produces a JSON response file at `/tmp/iao-0.1.4-ambiguous-rulings.json`, Kyle saves it to the filesystem, runs:

```fish
iao iteration resume W3
```

Which reads the rulings and completes W3.

#### W3.2 — Script registry migration

Similar flow to W3.1 but reading kjtcom's script registry and scripts directory.

#### W3.3 — ADR promotion audit

Cross-reference kjtcom's project-layer ADRs against iao's base.md. Nemotron classifies; universals get promoted.

#### W3.4 — Pattern catalog migration

Same as W3.3 for patterns.

#### W3.5 — Migration map document

Gemini writes `docs/harness/kjtcom-migration-map.md` with four tables populated from the per-entry classifications logged above.

#### W3.6 — ADR-036 appended to base.md

```fish
printf '\n### iaomw-ADR-036: kjtcom Harness Artifact Migration\n\n- **Context:** iao 0.1.2 W5 migrated kjtcom methodology code (RAG, logger, data modules) but did not migrate registry artifacts (gotchas, scripts, ADRs, patterns). iao entered 0.1.4 with 6 gotchas while kjtcom had 60+ accumulated lessons.\n- **Decision:** 0.1.4 W3 migrates universal kjtcom registry entries into iao using Nemotron for auto-classification, with a mid-iteration human review step for ambiguous cases.\n- **Rationale:** The gotcha registry is institutional memory. Without migration, Pillar 3 (Diligence) has nothing to query against.\n- **Consequences:** docs/harness/kjtcom-migration-map.md is the audit trail. Migrated entries preserve provenance via kjtcom_source_id field. Future kjtcom iterations may surface new universal lessons; a similar migration pass should follow.\n' >> docs/harness/base.md
```

#### W3 checkpoint update

```fish
jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W3.status = "complete" | .workstreams.W3.completed_at = $ts | .current_workstream = "W4"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W4 — Telegram Framework Generalization

**Executor:** Gemini CLI
**Wall clock target:** 75 min

See design §6 W4 for deliverables. Gemini creates:

```fish
mkdir -p src/iao/telegram
touch src/iao/telegram/__init__.py
```

Then creates `framework.py`, `notifications.py`, `config.py`, `cli.py` inside `src/iao/telegram/` per the design spec. Uses `python-telegram-bot` or `requests` for Telegram API calls.

```fish
# Install telegram library if needed
pip install python-telegram-bot --break-system-packages --quiet
python3 -c "import telegram; print(telegram.__version__)"

# Gemini creates the four module files...
# ... (full implementations per design §6 W4)

# Register iao telegram CLI subparser in src/iao/cli.py

# Migrate kjtcom bot.env into iao secrets
iao secret set kjtco TELEGRAM_BOT_TOKEN "$(grep KJTCOM_TELEGRAM_BOT_TOKEN ~/.config/kjtcom/bot.env | cut -d= -f2)"
iao secret set kjtco TELEGRAM_CHAT_ID "$(grep KJTCOM_TELEGRAM_CHAT_ID ~/.config/kjtcom/bot.env | cut -d= -f2)"

# Verify migration
iao secret get kjtco TELEGRAM_BOT_TOKEN | head -c 20
# Expected: first 20 chars of token

# Live smoke test
iao telegram test kjtco
# Expected: Telegram notification delivered to Kyle's chat

# Append to base.md
printf '\n### iaomw-ADR-037: Telegram Framework\n\n- **Context:** kjtcom has a 619-line kjtcom-specific telegram bot with plaintext credentials in bot.env. Per the 0.1.3 review, iao needs a generalized framework so any consumer project can scaffold a bot.\n- **Decision:** src/iao/telegram/ subpackage with TelegramBotFramework class, iao telegram init/test/status CLI commands, systemd service template, and bot.env → iao secrets migration.\n- **Rationale:** Telegram notifications and review bridge are foundational for the remote-review architecture (0.1.5). Framework must exist before the review agent can use it.\n- **Consequences:** kjtco secrets migrated to iao backend in 0.1.4 W4. Full bot.env retirement waits for kjtcom maintenance touch.\n' >> docs/harness/base.md
```

**W4 checkpoint update:** Same pattern as previous workstreams.

---

### W5 — OpenClaw + NemoClaw Foundations

**Executor:** Gemini CLI
**Wall clock target:** 90 min

```fish
# Install open-interpreter
pip install open-interpreter --break-system-packages

python3 -c "import interpreter; print('ok')"
# Expected: ok

# Create the agents subpackage
mkdir -p src/iao/agents/roles
touch src/iao/agents/__init__.py src/iao/agents/roles/__init__.py

# Gemini creates openclaw.py, nemoclaw.py, roles/base_role.py, roles/assistant.py per design §6 W5

# Smoke test
python3 scripts/smoke_nemoclaw.py
# Expected: runs, spawns nemoclaw session, receives response, exits 0

# Append to base.md
printf '\n### iaomw-ADR-038: Agent Architecture\n\n- **Context:** iao needs agent primitives for the 0.1.5 review loop: sessions that can execute code, read files, hold conversations. Open-interpreter is the execution primitive (openclaw); Nemotron is the orchestration driver (nemoclaw).\n- **Decision:** 0.1.4 W5 installs open-interpreter, creates src/iao/agents/{openclaw,nemoclaw,roles}/ subpackages, and proves a single-session smoke test. The review agent role and Telegram bridge are 0.1.5 deliverables.\n- **Rationale:** Foundation work. Must exist before the user-facing review architecture can be built.\n- **Consequences:** scripts/smoke_nemoclaw.py is the smoke test. docs/harness/agents-architecture.md documents the design. 0.1.5 W-review builds the reviewer role on top of these primitives.\n' >> docs/harness/base.md
```

Checkpoint update pattern.

---

### W6 — Notification Hook + Gemini-Primary Sync

**Executor:** Gemini CLI
**Wall clock target:** 60 min

Per design §6 W6:
- Wire Telegram notification into `iao iteration close`
- Update README.md for Gemini-primary
- Update install.fish
- Retire CLAUDE.md to pointer file
- Add `gemini_compat` post-flight check
- Append ADR-039 to base.md

```fish
# Example: CLAUDE.md retirement
cat > CLAUDE.md <<'MDEOF'
# CLAUDE.md (retired)

This file is preserved for Claude Code compatibility. The canonical agent brief for iao 0.1.4 and forward is **GEMINI.md** at the same location.

Claude Code operators should read GEMINI.md — the instructions are executor-agnostic and apply to both Gemini CLI and Claude Code.

iao 0.1.4 is the first iteration where Gemini CLI is the sole executor. Claude Code remains supported but is no longer the primary.

See: GEMINI.md
MDEOF
```

Checkpoint update pattern.

---

### W7 — Dogfood + Closing Sequence

**Executor:** Gemini CLI
**Wall clock target:** 75 min

```fish
# Run Qwen artifact loop with new hardened templates
iao iteration build-log 0.1.4
wc -w docs/iterations/0.1.4/iao-build-log-0.1.4.md
# Expected: ≥ 1500 words (lowered from 2000 per 0.1.3 calibration)

iao iteration report 0.1.4
wc -w docs/iterations/0.1.4/iao-report-0.1.4.md
# Expected: ≥ 1200 words

# Run full post-flight
iao doctor postflight
# Expected: all checks pass including bundle_quality (21 sections), run_report_quality, gemini_compat, ten_pillars_present, readme_current

# Close iteration
iao iteration close
# Expected: generates run report, generates bundle, prints workstream summary table, sends Telegram notification

# Verify all 4 run-report bug fixes
cat docs/iterations/0.1.4/iao-run-report-0.1.4.md | head -50
# Manual inspection:
# - Workstream table shows all 8 W rows with complete status and wall clock (Bug 1 fixed)
# - Agent Questions section populated OR explicit "(none ...)" message (Bug 2 fixed)
# - File size ≥ 1500 bytes (Bug 3 fixed — run_report_quality gate enforces)

wc -c docs/iterations/0.1.4/iao-run-report-0.1.4.md
# Expected: ≥ 1500 bytes

# Verify bundle has 21 sections with run report as §5
grep -c "^## §" docs/iterations/0.1.4/iao-bundle-0.1.4.md
# Expected: 21

grep "^## §5\." docs/iterations/0.1.4/iao-bundle-0.1.4.md
# Expected: ## §5. Run Report (Bug 4 fixed)

# Verify bundle quality
iao bundle validate docs/iterations/0.1.4/iao-bundle-0.1.4.md
# Expected: exit 0

wc -c docs/iterations/0.1.4/iao-bundle-0.1.4.md
# Expected: ≥ 100000 bytes (≥ 100 KB)

# Phase 0 graduation analysis
iao iteration graduate 0.1.4 --analyze
# Expected: Qwen produces Phase 0 progress assessment recommending CONTINUE with 0.1.5

# Update CHANGELOG
# Gemini appends 0.1.4 entry summarizing all 8 workstreams

# Mark W7 complete, iteration in review pending state
jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W7.status = "complete" | .workstreams.W7.completed_at = $ts | .current_workstream = "review_pending" | .completed_at = $ts' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json

# Stop. Print closing message.
echo "
================================================
ITERATION 0.1.4 EXECUTION COMPLETE
================================================
Run report: docs/iterations/0.1.4/iao-run-report-0.1.4.md
Bundle:     docs/iterations/0.1.4/iao-bundle-0.1.4.md
Workstreams: 8/8 complete

Telegram notification sent to Kyle.

NEXT STEPS:
1. Review the bundle
2. Open the run report and fill in Kyle's Notes for next iteration
3. Answer any questions in the Agent Questions section
4. Tick the 5 sign-off checkboxes
5. Run: iao iteration close --confirm

Until --confirm, iteration is in PENDING REVIEW state.
"
```

---

## Section D — Post-flight (After Kyle's `--confirm`)

### D.1 — Validate sign-off

```fish
iao iteration close --confirm
# Reads run report, verifies all 5 sign-off boxes ticked
# If not: prints missing items and exits nonzero
# If yes: updates .iao.json, marks iteration complete, bumps to next draft
```

### D.2 — Final post-flight

```fish
iao doctor postflight
# Expected: all checks pass
```

### D.3 — Seed next iteration

```fish
iao iteration seed
# Reads Kyle's Notes section from 0.1.4 run report
# Writes docs/iterations/0.1.5/seed.json as input for 0.1.5 design generation
```

### D.4 — Final state verification

```fish
jq .current_iteration .iao.json
# Expected: "0.1.4" (stays here until 0.1.5 planning begins)

jq .last_completed_iteration .iao.json
# Expected: "0.1.4"

command ls docs/iterations/0.1.4/
# Expected: iao-design-0.1.4.md, iao-plan-0.1.4.md, iao-build-log-0.1.4.md,
#           iao-report-0.1.4.md, iao-run-report-0.1.4.md, iao-bundle-0.1.4.md
```

### D.5 — Manual git commit (Kyle, per Pillar 0)

```fish
git status
git add -A
git commit -m "iao 0.1.4: model fleet, kjtcom migration, telegram, openclaw foundations, Gemini-primary, 0.1.3 cleanup"
```

---

## Section E — Rollback Procedure

```fish
tmux kill-session -t iao-0.1.4 2>/dev/null
rm -rf ~/dev/projects/iao
mv ~/dev/projects/iao.backup-pre-0.1.4 ~/dev/projects/iao
cd ~/dev/projects/iao
pip install -e . --break-system-packages
iao --version
# Expected: 0.1.3 (pre-0.1.4 state)
```

**When to rollback:** W1 cleanup surfaces unrecoverable test failures, W2 ChromaDB seeding corrupts storage, W4 telegram framework breaks iao secrets backend.

**When NOT to rollback:** Qwen word count still failing (expected, fallback handles it), Nemotron misclassifies some gotchas (Kyle can fix manually via chat review), W5 smoke test flaky (foundation work, acceptable partial ship).

---

## Section F — Wall Clock Targets

| Workstream | Target | Cumulative |
|---|---|---|
| Pre-flight | 15 min | 0:15 |
| W0 Bookkeeping | 10 min | 0:25 |
| W1 Cleanup (8 sub-deliverables) | 90 min | 1:55 |
| W2 Model fleet | 120 min | 3:55 |
| W3 kjtcom migration (excl. Kyle review) | 90 min | 5:25 |
| W4 Telegram framework | 75 min | 6:40 |
| W5 OpenClaw + NemoClaw | 90 min | 8:10 |
| W6 Notification + Gemini sync | 60 min | 9:10 |
| W7 Dogfood + closing | 75 min | 10:25 |

Soft cap is 8 hours; estimate runs 10 hours. Acceptable — no hard cap.

---

## Section G — Sign-off

This plan is the operational instruction set for iao 0.1.4. Gemini CLI is the sole executor. GEMINI.md (produced in chat alongside this plan) is the agent brief Gemini reads at session start.

The plan is immutable per ADR-012 once W0 begins. The build log records what actually happened. The report grades it. The run report is where Kyle's voice enters the loop at close.

— iao 0.1.4 planning chat, 2026-04-09
