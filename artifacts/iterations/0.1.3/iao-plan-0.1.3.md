# iao — Plan 0.1.3

**Iteration:** 0.1.3.1 (phase 0, iteration 1, run 1 — first execution of 0.1.3)
**Phase:** 0 (NZXT-only authoring)
**Date:** April 09, 2026
**Machine:** NZXTcos
**Repo:** ~/dev/projects/iao
**Wall clock target:** ~6–8 hours, soft cap (no hard cap)
**Run mode:** Bounded sequential, split-agent
**Status:** Planning

This plan operationalizes `iao-design-0.1.3.md`. Read the design doc first if you haven't. The design defines *what* and *why*; this plan defines *how* and *in what order*.

---

## What is iao

(Novice-operability constraint, every iao artifact opens with this.)

iao is the methodology and Python package for running disciplined LLM-driven engineering iterations. iao 0.1.3 hardens the artifact loop, consolidates the folder layout, refactors the Python package to src-layout, scaffolds universal pipeline patterns, establishes the human feedback loop, and brings iao's own README and harness into compliance with the rules iao enforces on consumer projects. See `iao-design-0.1.3.md` for the why; this document is the executable plan.

---

## Section A — Pre-flight

The pre-flight phase runs before any workstream begins. Every check must pass (or be explicitly noted-and-proceeded per Pillar 6 + Pattern-22) before launch.

### A.0 — Working directory and shell state

```fish
cd ~/dev/projects/iao
pwd
# Expected: /home/kthompson/dev/projects/iao

command ls -la .iao.json VERSION pyproject.toml
# Expected: all three files present
```

**Failure remediation:** If any file missing, you are in the wrong directory or the project is corrupted. Restore from `~/dev/projects/iao.backup-pre-0.1.3` and re-investigate.

### A.1 — Backup the project before launch

```fish
test -d ~/dev/projects/iao.backup-pre-0.1.3
# Expected: nothing (no output) on first run — we're about to create it

cp -a ~/dev/projects/iao ~/dev/projects/iao.backup-pre-0.1.3
test -d ~/dev/projects/iao.backup-pre-0.1.3
# Expected: silent (exit 0)

du -sh ~/dev/projects/iao.backup-pre-0.1.3
# Expected: matches du -sh ~/dev/projects/iao
```

**Failure remediation:** If backup fails (disk space, permissions), do not launch. Free space or fix permissions first.

### A.2 — Git state clean

```fish
cd ~/dev/projects/iao
git status --porcelain
# Expected: no output (clean working tree)

git log --oneline -5
# Expected: shows last 5 commits, most recent should be the 0.1.2 close
```

**Failure remediation:** If working tree is dirty, Kyle must commit or stash before launch. Per Pillar 0, the agent does NOT run git commit. Surface the dirty state and stop.

### A.3 — Python environment

```fish
python3 --version
# Expected: 3.14.x (NZXT has 3.14.3)

which python3
# Expected: /usr/bin/python3

pip --version
# Expected: pip 25.x

which iao
# Expected: ~/.local/bin/iao or /usr/local/bin/iao
```

**Failure remediation:** If Python is missing or wrong version, reinstall. If pip is missing, `sudo pacman -S python-pip`.

### A.4 — iao package installed

```fish
iao --version
# Expected: 0.1.0 (will be bumped to 0.1.3 in W0)

python3 -c "import iao; print(iao.__file__)"
# Expected: a path inside ~/dev/projects/iao/iao/__init__.py

iao doctor quick
# Expected: all quick checks pass
```

**Failure remediation:** If `iao --version` fails, `cd ~/dev/projects/iao && pip install -e . --break-system-packages`. If `iao doctor quick` fails, read the error and fix before launch.

### A.5 — Ollama daemon and models

```fish
curl -s http://localhost:11434/api/tags | head -5
# Expected: JSON response listing models

ollama list | grep -E "qwen3.5:9b|nomic-embed-text"
# Expected: both models present
```

**Failure remediation:** If Ollama not running, `systemctl --user start ollama` or `ollama serve &`. If models missing, `ollama pull qwen3.5:9b` and/or `ollama pull nomic-embed-text`.

### A.6 — Disk space

```fish
df -h ~/dev/projects/iao | tail -1
# Expected: at least 5G free
```

**Failure remediation:** Free space before launch. iao 0.1.3 doesn't write much but the bundle generation in W7 needs headroom.

### A.7 — Sleep/suspend masked

```fish
systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target | grep "Active:"
# Expected: all four should show "inactive (dead)" or be masked

systemctl status sleep.target | grep "Loaded:"
# Expected: "masked" or similar
```

**Failure remediation:** If not masked, run `sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target` per the standard NZXT pre-flight from previous iterations.

### A.8 — `.iao.json` reflects 0.1.2 close state

```fish
cat .iao.json | jq .current_iteration
# Expected: "0.1.2" or "0.1.3.0"

cat .iao.json | jq .name
# Expected: "iao" or "iaomw"
```

**Failure remediation:** If iteration field is wrong, edit `.iao.json` manually before launch (this is W0's first action anyway; if it's already done, skip to W1).

### A.9 — No active tmux session for this iteration

```fish
tmux ls 2>/dev/null | grep "iao-0.1.3"
# Expected: no output (no existing session)
```

**Failure remediation:** If a session named `iao-0.1.3` exists, kill it: `tmux kill-session -t iao-0.1.3`. Then verify the bundle from any previous attempt is moved aside before relaunching.

### A.10 — Required tools present

```fish
which git python3 pip ollama jq age keyctl
# Expected: all present

age --version
# Expected: 1.3.x (installed in 0.1.2 W1)
```

**Failure remediation:** Install any missing tool. `age` should already be present from 0.1.2 W1; if not, `sudo pacman -S age`.

### A.11 — Pre-flight summary

After all 11 pre-flight checks pass, print:

```
PRE-FLIGHT COMPLETE
====================
Working dir: ~/dev/projects/iao
Backup: ~/dev/projects/iao.backup-pre-0.1.3 (created)
Git state: clean
Python: 3.14.3
iao package: 0.1.0 (will bump to 0.1.3 in W0)
Ollama: running, qwen3.5:9b present
Disk: XXG free
Sleep: masked
.iao.json: ready
tmux: no conflicting session
Tools: git python3 pip ollama jq age keyctl all present

READY TO LAUNCH iao 0.1.3.1
```

If any check failed, do NOT launch. Surface the failure to Kyle, fix, re-run pre-flight from A.0.

---

## Section B — Launch Protocol

### B.1 — Open tmux session

```fish
tmux new-session -d -s iao-0.1.3 -c ~/dev/projects/iao
tmux send-keys -t iao-0.1.3 'cd ~/dev/projects/iao && set -x IAO_ITERATION 0.1.3.1 && set -x IAO_PROJECT_NAME iao' Enter
```

### B.2 — Initialize checkpoint

```fish
printf '%s\n' '{
  "iteration": "0.1.3.1",
  "phase": 0,
  "started_at": "REPLACE_WITH_CURRENT_TIMESTAMP",
  "current_workstream": "W0",
  "workstreams": {
    "W0": {"status": "pending", "agent": "gemini-cli"},
    "W1": {"status": "pending", "agent": "gemini-cli"},
    "W2": {"status": "pending", "agent": "gemini-cli"},
    "W3": {"status": "pending", "agent": "gemini-cli"},
    "W4": {"status": "pending", "agent": "gemini-cli"},
    "W5": {"status": "pending", "agent": "gemini-cli"},
    "W6": {"status": "pending", "agent": "claude-code"},
    "W7": {"status": "pending", "agent": "claude-code"}
  },
  "handoff_at": null,
  "completed_at": null
}' > .iao-checkpoint.json
```

The launching shell replaces the timestamp placeholder with `(date -u +%Y-%m-%dT%H:%M:%SZ)`.

### B.3 — Launch Gemini CLI for W0–W5

```fish
tmux send-keys -t iao-0.1.3 'gemini --yolo' Enter
```

Gemini reads `GEMINI.md` (project root) and `CLAUDE.md` (project root) for context. The first instruction Gemini sees is "Read GEMINI.md and execute W0 through W5 from iao-plan-0.1.3.md, updating .iao-checkpoint.json as you go. Stop after W5 and write a handoff entry to the checkpoint."

Kyle's role during Gemini's run: monitor occasionally, intervene only on Pillar 6 violations (Gemini asking permission for non-destructive actions). The expected wall clock for W0–W5 is ~4 hours.

### B.4 — Handoff to Claude Code for W6–W7

When Gemini's W5 completes and the checkpoint shows `"current_workstream": "handoff"`, attach to the tmux session:

```fish
tmux attach -t iao-0.1.3
```

Verify the checkpoint:

```fish
cat .iao-checkpoint.json | jq '.workstreams.W5.status'
# Expected: "complete"

cat .iao-checkpoint.json | jq '.handoff_at'
# Expected: an ISO timestamp, not null
```

Then exit Gemini and launch Claude Code:

```fish
exit  # exit Gemini
claude --dangerously-skip-permissions
```

Claude Code reads `CLAUDE.md`, picks up at W6, completes W6 and W7. Expected wall clock for W6–W7 is ~2.5 hours.

### B.5 — Iteration close

When Claude Code completes W7 (the dogfood test + closing sequence), it stops and prints:

```
ITERATION 0.1.3.1 EXECUTION COMPLETE
=====================================
Run report: docs/iterations/0.1.3/iao-run-report-0.1.3.1.md
Bundle: docs/iterations/0.1.3/iao-bundle-0.1.3.1.md (XX KB)
Workstreams: 8/8 complete

NEXT STEPS:
1. Review the bundle (take it offline if you want)
2. Open the run report and fill in your notes for the next iteration
3. Answer any questions in the "Agent Questions for Kyle" section
4. Tick the sign-off boxes
5. Run: iao iteration close --confirm

Until you run --confirm, this iteration is in PENDING REVIEW state.
```

This is where the agent stops. The human takes over.

---

## Section C — Workstream Execution Details

### W0 — Iteration Bookkeeping

**Agent:** Gemini CLI
**Wall clock target:** 5 min
**Files touched:** `.iao.json`, `VERSION`, `.iao-checkpoint.json`

**Steps:**

1. Read current state:
   ```fish
   cat .iao.json
   cat VERSION
   ```

2. Update `.iao.json`:
   ```fish
   jq '.current_iteration = "0.1.3.1" | .phase = 0 | .iteration_position = "first"' .iao.json > .iao.json.tmp && mv .iao.json.tmp .iao.json
   ```

3. Update `VERSION`:
   ```fish
   echo "0.1.3" > VERSION
   ```

4. Verify logger picks up new iteration:
   ```fish
   python3 -c "from iao.logger import get_iteration; print(get_iteration())"
   # Expected: 0.1.3.1
   ```

5. Update checkpoint:
   ```fish
   jq '.workstreams.W0.status = "complete" | .workstreams.W0.completed_at = "ISO_TIMESTAMP" | .current_workstream = "W1"' .iao-checkpoint.json > .iao-checkpoint.json.tmp && mv .iao-checkpoint.json.tmp .iao-checkpoint.json
   ```

6. Append to build log:
   ```fish
   iao log workstream-complete W0 "Iteration bookkeeping: bumped .iao.json to 0.1.3.1, VERSION to 0.1.3, updated checkpoint"
   ```

**Acceptance:** All four files reflect 0.1.3.1 / phase 0 / 0.1.3.

---

### W1 — Folder Consolidation

**Agent:** Gemini CLI
**Wall clock target:** 45 min
**Files touched:** `artifacts/docs/iterations/*` → `docs/iterations/*`, `iao/iao/paths.py`, `iao/iao/bundle.py`, `iao/iao/postflight/*.py`, `prompts/*.j2`, multiple grep targets

**Steps:**

1. **Create new directories:**
   ```fish
   mkdir -p docs/{phase-charters,archive,drafts}
   ```

2. **Move iteration outputs:**
   ```fish
   mv artifacts/docs/iterations/* docs/iterations/ 2>/dev/null
   # If docs/iterations/ doesn't exist yet, mkdir first
   mkdir -p docs/iterations
   mv artifacts/docs/iterations/* docs/iterations/
   ```

3. **Verify the move:**
   ```fish
   command ls docs/iterations/
   # Expected: 0.1.0/  0.1.2/  (and possibly 0.1.3/ if W0 created it)
   command ls artifacts/docs/iterations/ 2>/dev/null
   # Expected: empty or "no such file"
   ```

4. **Remove the empty artifacts tree:**
   ```fish
   rmdir artifacts/docs/iterations 2>/dev/null
   rmdir artifacts/docs 2>/dev/null
   rmdir artifacts 2>/dev/null
   # If any rmdir fails because of leftover content, list it and stop for human review
   ```

5. **Remove the empty iao/iao/docs/ tree:**
   ```fish
   rmdir iao/iao/docs/harness 2>/dev/null
   rmdir iao/iao/docs 2>/dev/null
   ```

6. **Grep the codebase for old path references:**
   ```fish
   grep -rn "artifacts/docs" iao/ prompts/ tests/ docs/ bin/ 2>/dev/null
   # Expected: a list of references that need updating
   ```

7. **Update each reference:**

   For `iao/iao/paths.py`:
   ```python
   # OLD: ITERATION_DIR = REPO_ROOT / "artifacts" / "docs" / "iterations"
   # NEW: ITERATION_DIR = REPO_ROOT / "docs" / "iterations"
   ```

   For `iao/iao/bundle.py`: same substitution.

   For `iao/iao/postflight/artifacts_present.py`: same substitution.

   For `iao/iao/postflight/iteration_complete.py`: same substitution.

   For each prompt template in `prompts/*.j2`: search for `artifacts/docs` and substitute.

8. **Run tests:**
   ```fish
   pytest tests/test_paths.py -v
   # Expected: pass
   pytest tests/ -v
   # Expected: all tests pass; if any fail, fix and retry (max 3 retries per Pillar 7)
   ```

9. **Verify with iao CLI:**
   ```fish
   iao bundle --dry-run --version 0.1.3.1
   # Expected: lists files from docs/iterations/0.1.3/, not artifacts/docs/iterations/
   ```

10. **Final grep:**
    ```fish
    grep -rn "artifacts/docs" iao/ prompts/ tests/ docs/ bin/ 2>/dev/null | grep -v "iao-design-0.1.3.md" | grep -v "iao-plan-0.1.3.md"
    # Expected: zero matches outside the design and plan docs themselves
    ```

11. **Mark complete:**
    ```fish
    iao log workstream-complete W1 "Folder consolidation: moved artifacts/docs/iterations to docs/iterations, removed empty artifacts/ and iao/iao/docs/, updated all path references, all tests pass"
    ```

**Acceptance per design §6 W1:**
- `find ~/dev/projects/iao -type d -name docs` returns exactly one path
- `pytest tests/test_paths.py` passes
- `iao bundle --dry-run` reads from new location
- Zero `artifacts/docs` matches in source files

**Failure modes:**
- **Unexpected files in `artifacts/`:** If `rmdir` fails because of unknown content, do not force-remove. Surface to Kyle.
- **Test failures after path update:** Read the test output, find the missed reference, update it. Pillar 7 max 3 retries.
- **Grep returns matches in places we didn't expect:** Update each carefully. Documentation files (.md) referencing the path can be left alone if they're historical (kjtcom-audit.md from 0.1.2 is historical and immutable).

---

### W2 — src-layout Refactor

**Agent:** Gemini CLI
**Wall clock target:** 40 min
**Files touched:** `iao/iao/*` → `iao/src/iao/*`, `pyproject.toml`, `iao.egg-info/`, `bin/iao`, `MANIFEST.json`, `COMPATIBILITY.md`, `data/gotcha_archive.json`

**Steps:**

1. **Create src directory and move package:**
   ```fish
   mkdir -p src
   mv iao/iao src/iao
   command ls src/iao/
   # Expected: __init__.py, cli.py, bundle.py, doctor.py, all subpackages
   ```

2. **Verify old location empty:**
   ```fish
   command ls iao/ 2>/dev/null
   # Expected: nothing or "no such file"
   rmdir iao 2>/dev/null
   ```

3. **Update pyproject.toml:**

   Read the current pyproject.toml. Find the `[tool.setuptools]` section (or `[project]` section if using PEP 621). Add or update:
   ```toml
   [tool.setuptools.packages.find]
   where = ["src"]
   include = ["iao*"]

   [tool.setuptools.package-dir]
   "" = "src"
   ```

4. **Remove old egg-info:**
   ```fish
   rm -rf iao.egg-info
   ```

5. **Reinstall:**
   ```fish
   pip install -e . --break-system-packages
   # Expected: successful install, new egg-info created under src/
   ```

6. **Verify install location:**
   ```fish
   python3 -c "import iao; print(iao.__file__)"
   # Expected: /home/kthompson/dev/projects/iao/src/iao/__init__.py
   ```

7. **Verify CLI:**
   ```fish
   iao --version
   # Expected: 0.1.3
   iao --help
   # Expected: full subcommand list
   iao doctor quick
   # Expected: passes
   ```

8. **Run full test suite:**
   ```fish
   pytest tests/ -v
   # Expected: all 8+ test files pass
   ```

   If tests fail, read the failures. Most likely cause: a test file imports something via a path that depends on flat layout. Update the import or the test fixture. Pillar 7 max 3 retries.

9. **Update MANIFEST.json:**
   Update file paths inside MANIFEST.json to reflect the src/ prefix.

10. **Update COMPATIBILITY.md:**
    Append a note: "0.1.3: Python package moved to src-layout. Import path unchanged (`import iao`); filesystem path is now `src/iao/` instead of `iao/iao/`."

11. **Add gotcha to registry:**
    ```fish
    # Read current gotcha_archive.json, append iaomw-G104
    ```
    New entry:
    ```json
    {
      "id": "iaomw-G104",
      "title": "Flat-layout Python package shadows repo name",
      "status": "Resolved",
      "action": "Use src-layout from project start; refactor early if inherited. iao 0.1.3 W2 migrated iao/iao/ to iao/src/iao/.",
      "source": "iao 0.1.3 W2",
      "code": "iaomw"
    }
    ```

12. **Mark complete:**
    ```fish
    iao log workstream-complete W2 "src-layout refactor: moved iao/iao/ to iao/src/iao/, updated pyproject.toml, reinstalled, all tests pass"
    ```

**Acceptance per design §6 W2:**
- `find ~/dev/projects/iao/iao -type f` returns nothing
- `find ~/dev/projects/iao/src/iao -name "__init__.py" | wc -l` ≥ 8
- `iao --version` returns `0.1.3`
- `pytest tests/` passes

**Failure modes:**
- **pyproject.toml syntax error:** revert to backup, re-edit carefully
- **Import errors:** the most common cause is a test file with `from iao.iao.X import Y` (which never worked but might have been tolerated). Fix the import.
- **CLI entry point broken:** check `pyproject.toml [project.scripts]` section, ensure `iao = "iao.cli:main"` (or whatever the entry was) still resolves.

---

### W3 — Universal Bundle Spec + Quality Gates

**Agent:** Gemini CLI
**Wall clock target:** 90 min
**Files touched:** `docs/harness/base.md`, `src/iao/bundle.py`, `prompts/bundle.md.j2`, `prompts/design.md.j2`, `prompts/plan.md.j2`, `prompts/build-log.md.j2`, `prompts/report.md.j2`, `src/iao/postflight/bundle_quality.py` (new), `tests/test_bundle.py` (new), `data/gotcha_archive.json`

**Steps:**

1. **Read current base.md:**
   ```fish
   cat docs/harness/base.md
   ```

2. **Append iaomw-ADR-028 (Universal Bundle Specification):**

   The full ADR text per design §6 W3.1. Includes the complete §1–§20 section list with descriptions.

3. **Append iaomw-ADR-029 (Bundle Quality Gates):**

   Defines minimum content checks per section. Specifically:
   - Bundle file ≥ 50 KB
   - All 20 section headers present
   - Each section non-empty (≥ 200 chars between adjacent headers)
   - §1 Design ≥ 3000 chars
   - §2 Plan ≥ 3000 chars
   - §3 Build Log ≥ 1500 chars and contains entries for all declared workstreams
   - §4 Report ≥ 1000 chars and contains a workstream scores table

4. **Append iaomw-ADR-012-amendment (Artifact Immutability extends to iao):**

   Resolves 0.1.2 Open Question 5 in favor of immutability. Design and plan are immutable inputs from W0 onward; only build log, report, run report, and bundle are produced by execution.

5. **Append iaomw-Pattern-32 (Existence-Only Success Criteria):**

   Documents the 0.1.2 W7 failure mode. Prevention: every success criterion must include a content check, not just an existence check.

6. **Append iaomw-G104 to gotcha registry:** (also done in W2 for src-layout — this is a different gotcha)

   Wait — re-checking. W2 already used G104 for src-layout. W3's gotcha is **iaomw-G105**: "Existence-Only Acceptance Criteria":

   ```json
   {
     "id": "iaomw-G105",
     "title": "Existence-only acceptance criteria mask quality failures",
     "status": "Resolved",
     "action": "Every success criterion must include a content check, not just an existence check. iao 0.1.3 W3 added bundle quality gates enforcing minimum size and section completeness.",
     "source": "iao 0.1.2 W7 retrospective + iao 0.1.3 W3",
     "code": "iaomw"
   }
   ```

7. **Rewrite `src/iao/bundle.py`:**

   New module structure:
   ```python
   """iao bundle generation and validation.

   Implements the §1–§20 universal bundle specification per
   iaomw-ADR-028. Bundle is mechanical aggregation of real files,
   not LLM synthesis.
   """

   from dataclasses import dataclass
   from pathlib import Path
   from typing import Optional, Callable

   @dataclass
   class BundleSection:
       number: int
       title: str
       source_path: Optional[Path]  # None for sections that aggregate multiple files
       min_chars: int
       validator: Optional[Callable] = None

   BUNDLE_SPEC = [
       BundleSection(1, "Design", source_path=Path("docs/iterations/{version}/iao-design-{version}.md"), min_chars=3000),
       BundleSection(2, "Plan", source_path=Path("docs/iterations/{version}/iao-plan-{version}.md"), min_chars=3000),
       BundleSection(3, "Build Log", source_path=Path("docs/iterations/{version}/iao-build-log-{version}.md"), min_chars=1500),
       BundleSection(4, "Report", source_path=Path("docs/iterations/{version}/iao-report-{version}.md"), min_chars=1000),
       BundleSection(5, "Harness", source_path=None, min_chars=2000),  # base.md + project.md if exists
       BundleSection(6, "README", source_path=Path("README.md"), min_chars=1000),
       BundleSection(7, "CHANGELOG", source_path=Path("CHANGELOG.md"), min_chars=200),
       BundleSection(8, "CLAUDE.md", source_path=Path("CLAUDE.md"), min_chars=500),
       BundleSection(9, "GEMINI.md", source_path=Path("GEMINI.md"), min_chars=500),
       BundleSection(10, ".iao.json", source_path=Path(".iao.json"), min_chars=100),
       BundleSection(11, "Sidecars", source_path=None, min_chars=0),  # optional, can be empty
       BundleSection(12, "Gotcha Registry", source_path=Path("data/gotcha_archive.json"), min_chars=500),
       BundleSection(13, "Script Registry", source_path=Path("data/script_registry.json"), min_chars=0),  # may not exist for iao
       BundleSection(14, "iao MANIFEST", source_path=Path("MANIFEST.json"), min_chars=100),
       BundleSection(15, "install.fish", source_path=Path("install.fish"), min_chars=500),
       BundleSection(16, "COMPATIBILITY", source_path=Path("COMPATIBILITY.md"), min_chars=200),
       BundleSection(17, "projects.json", source_path=Path("projects.json"), min_chars=100),
       BundleSection(18, "Event Log (tail 500)", source_path=None, min_chars=0),  # tail of jsonl
       BundleSection(19, "File Inventory (sha256_16)", source_path=None, min_chars=500),  # generated
       BundleSection(20, "Environment", source_path=None, min_chars=500),  # generated
   ]

   def build_bundle(version: str, repo_root: Path) -> Path:
       """Assemble the bundle for the given iteration version."""
       # Read each section's source, render via Jinja, write to docs/iterations/<version>/iao-bundle-<version>.md
       ...

   def validate_bundle(bundle_path: Path) -> list[str]:
       """Return list of validation errors. Empty list = passing."""
       errors = []
       content = bundle_path.read_text()
       size_bytes = bundle_path.stat().st_size
       if size_bytes < 50000:
           errors.append(f"Bundle size {size_bytes} < 50000 bytes minimum")
       for section in BUNDLE_SPEC:
           header = f"## §{section.number}."
           if header not in content:
               errors.append(f"Section {section.number} ({section.title}) header missing")
       # Section content checks
       ...
       return errors
   ```

8. **Rewrite `prompts/bundle.md.j2`:**

   Jinja template that loops over the 20 sections and embeds each source file's content as a fenced code block under a `## §N. <Title>` header. The template does NOT call out to Qwen — it's pure Jinja rendering of real file content.

9. **Update `prompts/design.md.j2`:**

   Add required sections:
   ```jinja
   ## §3. The Trident
   {{ trident_block }}

   ## §4. The Ten Pillars
   {{ ten_pillars_block }}
   ```

   The `trident_block` and `ten_pillars_block` variables are loaded from `docs/harness/base.md` at template render time. Qwen does NOT generate these — they're loaded verbatim.

   Add minimum word count: 5000. The Qwen generation loop in `src/iao/artifacts/loop.py` checks output length and re-prompts if under.

10. **Update `prompts/plan.md.j2`:**

    Add required sections: pre-flight checklist, launch protocol, per-workstream details, post-flight checklist, rollback procedure. Min word count: 3000.

11. **Update `prompts/build-log.md.j2`:**

    Add required sections per design §6 W3.7. Min word count: 2000.

12. **Update `prompts/report.md.j2`:**

    Add required sections per design §6 W3.8. Mandatory workstream scores table. Min word count: 1500.

13. **Create `src/iao/postflight/bundle_quality.py`:**

    ```python
    """Post-flight check: bundle quality gate."""
    from pathlib import Path
    from iao.bundle import validate_bundle
    from iao.paths import iteration_dir

    def check(version: str = None) -> dict:
        """Returns {status, message, errors}."""
        if version is None:
            from iao.config import current_iteration
            version = current_iteration()
        bundle_path = iteration_dir(version) / f"iao-bundle-{version}.md"
        if not bundle_path.exists():
            return {"status": "FAIL", "message": "Bundle file does not exist", "errors": []}
        errors = validate_bundle(bundle_path)
        if errors:
            return {"status": "FAIL", "message": f"{len(errors)} validation errors", "errors": errors}
        return {"status": "PASS", "message": "Bundle conforms to §1–§20 spec", "errors": []}
    ```

14. **Wire bundle_quality into iao doctor postflight:**

    Update `src/iao/doctor.py` (or wherever the postflight registry lives) to include `bundle_quality` in the postflight check list.

15. **Create `tests/test_bundle.py`:**

    Tests for `build_bundle` and `validate_bundle`. Use a tmp directory with a fake iteration to verify the spec is enforced.

16. **Run tests:**
    ```fish
    pytest tests/test_bundle.py -v
    pytest tests/ -v
    ```

17. **Mark complete:**
    ```fish
    iao log workstream-complete W3 "Universal bundle spec + quality gates: added §1–§20 to base.md as ADR-028, ADR-029, ADR-012-amendment, Pattern-32, G105. Rewrote bundle.py to enforce spec. Updated all 5 prompt templates with minimum word counts and required sections. Added bundle_quality post-flight check. All tests pass."
    ```

**Acceptance per design §6 W3:** Per design doc.

**Failure modes:**
- **Jinja template syntax errors:** test render with a fake context before committing
- **Min word count too aggressive:** if Qwen genuinely cannot hit 5000 words on first try, the loop retries up to 3 times with progressively more guidance, then surfaces to run report

---

### W4 — Universal Pipeline Scaffolding

**Agent:** Gemini CLI
**Wall clock target:** 90 min
**Files touched:** `src/iao/pipelines/` (new subpackage), `templates/pipelines/skeleton/` (new), `docs/harness/pipeline-pattern.md` (new), `src/iao/postflight/pipeline_present.py` (new), `tests/test_pipelines.py` (new), `src/iao/cli.py` (add pipeline subparser), `docs/harness/base.md` (add ADR-030)

**Steps:**

1. **Create the subpackage structure:**
   ```fish
   mkdir -p src/iao/pipelines
   touch src/iao/pipelines/__init__.py
   ```

2. **Create `src/iao/pipelines/pattern.py`:**

   Defines the `PipelinePattern` class with the 10-phase abstract structure:
   ```python
   from dataclasses import dataclass
   from typing import Literal

   PhaseName = Literal[
       "phase1_extract",
       "phase2_transform",
       "phase3_normalize",
       "phase4_enrich",
       "phase5_production_run",
       "phase6_frontend",
       "phase7_production_load",
       "phase8_hardening",
       "phase9_optimization",
       "phase10_retrospective",
   ]

   PHASE_DESCRIPTIONS = {
       "phase1_extract": "Acquire raw data from source",
       "phase2_transform": "Convert raw data to intermediate format (transcribe, OCR, parse)",
       "phase3_normalize": "Apply schema and normalize fields",
       "phase4_enrich": "Add derived data from external sources",
       "phase5_production_run": "Execute the full pipeline at production scale",
       "phase6_frontend": "Build or update consumer-facing interface",
       "phase7_production_load": "Load processed data into production storage",
       "phase8_hardening": "Re-enrichment, gap filling, schema upgrades",
       "phase9_optimization": "Performance, cost, monitoring",
       "phase10_retrospective": "Document lessons, write ADRs, plan next phase",
   }

   @dataclass
   class PipelinePattern:
       name: str
       phases: list[PhaseName]
       checkpoint_path: str

       @classmethod
       def standard(cls, name: str) -> "PipelinePattern":
           return cls(
               name=name,
               phases=list(PHASE_DESCRIPTIONS.keys()),
               checkpoint_path=f"pipelines/{name}/checkpoint.json",
           )
   ```

3. **Create `src/iao/pipelines/scaffold.py`:**

   Implements the `iao pipeline init <name>` logic. Reads templates from `templates/pipelines/skeleton/`, substitutes the pipeline name, writes to `pipelines/<name>/`.

4. **Create `src/iao/pipelines/validate.py`:**

   Validates a pipeline directory against the pattern. Checks all 10 phase files exist, each has a `main()` function, checkpoint.json exists.

5. **Create `src/iao/pipelines/registry.py`:**

   Tracks pipelines in the consumer project. Reads `.iao.json` for `pipelines` list. Provides `list_pipelines()` and `get_pipeline_status()` functions.

6. **Create the template files in `templates/pipelines/skeleton/`:**

   For each phase, a `.template` file with:
   - Top docstring
   - `main()` function stub
   - Checkpoint read at start
   - Checkpoint write at end
   - TODO marker for project-specific logic

   Example for `phase1_extract.py.template`:
   ```python
   """{{ pipeline_name }} — Phase 1: Extract.

   Acquires raw data from source. Project-specific implementation
   replaces the TODO block.
   """
   import json
   from pathlib import Path

   PIPELINE = "{{ pipeline_name }}"
   PHASE = "phase1_extract"
   CHECKPOINT_PATH = Path(__file__).parent / "checkpoint.json"

   def read_checkpoint() -> dict:
       if CHECKPOINT_PATH.exists():
           return json.loads(CHECKPOINT_PATH.read_text())
       return {}

   def write_checkpoint(state: dict) -> None:
       CHECKPOINT_PATH.write_text(json.dumps(state, indent=2))

   def main() -> int:
       checkpoint = read_checkpoint()
       if checkpoint.get(PHASE, {}).get("status") == "complete":
           print(f"{PIPELINE}/{PHASE} already complete, skipping")
           return 0

       # TODO: project-specific extraction logic goes here
       # Examples:
       #   - kjtcom: yt-dlp pulls audio from YouTube playlist
       #   - tripledb: firestore export from source project
       #   - bookpdf: download PDF from source URL
       raise NotImplementedError(f"{PHASE} TODO")

       checkpoint.setdefault(PHASE, {})["status"] = "complete"
       write_checkpoint(checkpoint)
       return 0

   if __name__ == "__main__":
       raise SystemExit(main())
   ```

   Repeat for phases 2 through 10 with appropriate variations.

7. **Create `templates/pipelines/skeleton/checkpoint.json.template`:**
   ```json
   {
     "pipeline": "{{ pipeline_name }}",
     "created_at": "{{ timestamp }}",
     "phases": {}
   }
   ```

8. **Create `templates/pipelines/skeleton/README.md.template`:**

   A README skeleton for new pipelines explaining the 10-phase pattern, how to fill in each phase, where the checkpoint lives.

9. **Add `iao pipeline` subparser to `src/iao/cli.py`:**

   Subcommands: `init`, `list`, `validate`, `status`. Wire each to the corresponding function in the new subpackage.

10. **Create `src/iao/postflight/pipeline_present.py`:**

    Post-flight check that validates pipelines if the project declares any. Returns SKIP if `.iao.json.pipelines` is empty or absent. iao itself doesn't have pipelines (it IS the pipeline framework), so this check is SKIP for iao.

11. **Wire `pipeline_present` into `iao doctor postflight`.**

12. **Create `docs/harness/pipeline-pattern.md`:**

    A real document (≥ 1500 words) describing the 10-phase pattern in abstract terms, with concrete mappings to:
    - kjtcom (YouTube transcription pipeline)
    - tripledb (Firestore migration pipeline)
    - hypothetical PDF book OCR pipeline
    - hypothetical CSV ETL pipeline

13. **Append `iaomw-ADR-030` to base.md:**

    Documents the universal pipeline pattern as a harness primitive.

14. **Create `tests/test_pipelines.py`:**

    Tests for scaffold, validate, registry. Use tmp directories with fake projects.

15. **Run tests:**
    ```fish
    pytest tests/test_pipelines.py -v
    pytest tests/ -v
    ```

16. **Smoke test:**
    ```fish
    cd /tmp
    mkdir test-pipeline-scaffold && cd test-pipeline-scaffold
    iao pipeline init demo
    command ls pipelines/demo/
    # Expected: 10 phase files + checkpoint.json + README.md
    iao pipeline validate demo
    # Expected: clean
    cd ~/dev/projects/iao
    rm -rf /tmp/test-pipeline-scaffold
    ```

17. **Mark complete:**
    ```fish
    iao log workstream-complete W4 "Universal pipeline scaffolding: created src/iao/pipelines/ subpackage with pattern, scaffold, validate, registry. Created templates/pipelines/skeleton/ with 10 phase templates + checkpoint + README. Added iao pipeline CLI subparser with init/list/validate/status. Created docs/harness/pipeline-pattern.md. Added ADR-030 to base.md. Smoke test passed in /tmp."
    ```

**Acceptance per design §6 W4:** Per design doc.

---

### W5 — Human Feedback Loop + Run Report

**Agent:** Gemini CLI
**Wall clock target:** 75 min
**Files touched:** `src/iao/feedback/` (new subpackage), `prompts/run-report.md.j2` (new), `src/iao/cli.py` (extend iteration subparser), `src/iao/postflight/run_report_complete.py` (new), `tests/test_feedback.py` (new), `docs/harness/base.md` (add ADR-031, ADR-032, reframe Pillar 10)

**Steps:**

1. **Create the subpackage:**
   ```fish
   mkdir -p src/iao/feedback
   touch src/iao/feedback/__init__.py
   ```

2. **Create `src/iao/feedback/run_report.py`:**

   Generates the run report. Reads the build log and report, extracts workstream outcomes, assembles the markdown structure per design §6 W5.2.

3. **Create `src/iao/feedback/seed.py`:**

   Reads the previous iteration's run report. Extracts the "Kyle's Notes for Next Iteration" section. Produces a JSON seed file at `docs/iterations/<next_version>/seed.json` with the notes as input context for the next design generation.

4. **Create `src/iao/feedback/summary.py`:**

   Renders the workstream summary table to stdout at iteration close. Reads the build log, formats as a markdown table, prints with terminal-friendly box drawing.

5. **Create `src/iao/feedback/prompt.py`:**

   Handles the interactive `--confirm` flow. Reads the run report file, parses the sign-off section, verifies all boxes are ticked. Refuses to mark iteration complete if any box is unchecked.

6. **Create `prompts/run-report.md.j2`:**

   Jinja template for the run report. Variables: iteration version, workstream list, build log path, bundle path, agent questions list. Does NOT call Qwen — pure mechanical assembly.

7. **Add `iao iteration close` and `iao iteration close --confirm` to `src/iao/cli.py`:**

   ```python
   @iteration_subparser.command("close")
   @click.option("--confirm", is_flag=True)
   def iteration_close(confirm: bool):
       if not confirm:
           # Generate run report, print summary table, generate bundle, print next-steps
           ...
       else:
           # Validate sign-off, mark iteration complete in .iao.json, increment version
           ...
   ```

8. **Add `iao iteration seed` command:**

   Reads the previous iteration's run report Kyle's notes section, produces a seed JSON.

9. **Create `src/iao/postflight/run_report_complete.py`:**

   Verifies run report exists, summary table is populated, returns DEFERRED if Kyle's notes empty.

10. **Wire `run_report_complete` into `iao doctor postflight`.**

11. **Append to base.md:**
    - Reframe `iaomw-Pillar-10` from "Continuous Improvement (iao push feedback loop)" to "Continuous Improvement (Run Report → Kyle's notes → seed next iteration design. Feedback loop is first-class artifact.)"
    - Add `iaomw-ADR-031: Run Report as Canonical Artifact`
    - Add `iaomw-ADR-032: Human Sign-off Required for Iteration Close`

12. **Create `tests/test_feedback.py`:**

    Tests for run_report generation, seed extraction, summary rendering, prompt validation.

13. **Run tests:**
    ```fish
    pytest tests/test_feedback.py -v
    pytest tests/ -v
    ```

14. **Mark complete and write handoff entry:**
    ```fish
    iao log workstream-complete W5 "Human feedback loop + run report: created src/iao/feedback/ subpackage with run_report, seed, summary, prompt. Added iao iteration close, iao iteration close --confirm, iao iteration seed CLI commands. Added run_report_complete post-flight check. Reframed Pillar 10 in base.md, added ADR-031, ADR-032. All tests pass."

    # Write handoff entry to checkpoint
    jq '.workstreams.W5.status = "complete" | .handoff_at = "ISO_TIMESTAMP" | .current_workstream = "handoff"' .iao-checkpoint.json > .iao-checkpoint.json.tmp && mv .iao-checkpoint.json.tmp .iao-checkpoint.json
    ```

15. **Stop.** Gemini's portion is complete. Print to stdout:
    ```
    GEMINI W0–W5 COMPLETE
    Handoff to Claude Code: cat .iao-checkpoint.json
    Next: exit gemini, run: claude --dangerously-skip-permissions
    ```

**Acceptance per design §6 W5:** Per design doc.

---

### W6 — README Sync + Phase 0 Charter Retrofit + 10 Pillars Enforcement

**Agent:** Claude Code
**Wall clock target:** 75 min
**Files touched:** `README.md` (rewrite), `docs/phase-charters/iao-phase-0.md` (new), `src/iao/postflight/ten_pillars_present.py` (new), `src/iao/postflight/readme_current.py` (new), `prompts/design.md.j2` (template enforcement), `docs/harness/base.md` (add ADR-033, ADR-034, Pattern-33), `data/gotcha_archive.json`, `tests/test_postflight_pillars.py` (new)

**Steps:**

1. **Read the current README:**
   ```fish
   cat README.md
   ```

2. **Read kjtcom's README for reference structure:**

   Pull the §6 README block from a recent kjtcom bundle (`/path/to/kjtcom/docs/iterations/.../kjtcom-bundle-XX.X.X.md` if available, or grab `~/dev/projects/kjtcom/README.md` directly). Match its structure: hero paragraph, status line, trident mermaid, 10 pillars list, component review, data architecture, live components, architecture, etc.

3. **Rewrite `README.md`:**

   New structure per design §6 W6.1. Concrete sections:
   - **Hero paragraph** (what is iao, novice operability)
   - **Status line:** "Phase 0 (NZXT-only authoring) | Iteration 0.1.3.1 | Status: Bundle quality hardening + folder consolidation + src-layout + pipeline scaffolding + human feedback loop"
   - **Trident mermaid** (verbatim from base.md)
   - **The Ten Pillars of IAO** (verbatim from base.md, numbered list)
   - **What iao Does** (the harness is the product, the model is the engine)
   - **Component Review** (chip count: secrets backend, artifact loop, pipeline scaffold, post-flight, pre-flight, run report, bundle, doctor, registry, harness, install — count actual subpackages and modules)
   - **Architecture** (Python package layout, CLI surface, harness file locations, bundle structure)
   - **Active iao Projects** (table)
   - **Phase 0 Status** (current phase, exit criteria checklist with checkboxes)
   - **Roadmap** (link to roadmap doc)
   - **Installation** (`pip install -e .` for now)
   - **Contributing** (Phase 0 single-author)
   - **License**

4. **Create `docs/phase-charters/iao-phase-0.md`:**

   Copy §1 of `docs/iterations/0.1.3/iao-design-0.1.3.md` (the Phase 0 Charter section). Add front-matter:
   ```markdown
   # Phase 0 Charter — iao

   **Phase:** 0 — NZXT-only authoring
   **Charter author:** iao planning chat (retroactive)
   **Charter version:** 0.1
   **Charter date:** 2026-04-09
   **Iteration where chartered:** 0.1.3.1
   **Status:** active

   ---

   (full charter text from design doc §1)
   ```

5. **Create `src/iao/postflight/ten_pillars_present.py`:**

   Implements the design check. Reads design docs in `docs/iterations/<current_version>/`, greps for trident block and all 10 pillars. Reads README.md, same checks.

6. **Create `src/iao/postflight/readme_current.py`:**

   Checks README mtime against iteration start time (from .iao-checkpoint.json). FAIL if mtime is older than checkpoint start.

7. **Wire both checks into `iao doctor postflight`.**

8. **Update `prompts/design.md.j2`:**

   Add `{{ trident_block }}` and `{{ ten_pillars_block }}` as required template placeholders. Loaded from base.md at render time. Render-time validation rejects output that doesn't substitute these blocks.

9. **Append to base.md:**
   - `iaomw-ADR-033: README Currency Enforcement`
   - `iaomw-ADR-034: Trident and Pillars Verbatim Requirement`
   - `iaomw-Pattern-33: README Drift`

10. **Add `iaomw-G106` to gotcha registry:**
    ```json
    {
      "id": "iaomw-G106",
      "title": "README falls behind reality without enforcement",
      "status": "Resolved",
      "action": "Add post-flight check that verifies README.mtime > iteration_start. iao 0.1.3 W6 added readme_current check.",
      "source": "iao 0.1.3 W6",
      "code": "iaomw"
    }
    ```

11. **Create `tests/test_postflight_pillars.py`:**

    Tests for both new post-flight checks. Use a tmp directory with fake design docs and READMEs.

12. **Run tests:**
    ```fish
    pytest tests/test_postflight_pillars.py -v
    pytest tests/ -v
    ```

13. **Run the new checks against this iteration:**
    ```fish
    iao doctor postflight --check ten_pillars_present
    # Expected: PASS (this design doc has all 10 pillars in §4)

    iao doctor postflight --check readme_current
    # Expected: PASS (README was just rewritten in this workstream)
    ```

14. **Mark complete:**
    ```fish
    iao log workstream-complete W6 "README sync + Phase 0 charter retrofit + 10 pillars enforcement: rewrote README.md on kjtcom structure with trident, 10 pillars, component review, architecture. Created docs/phase-charters/iao-phase-0.md from design §1. Added ten_pillars_present and readme_current post-flight checks. Updated design.md.j2 with verbatim block placeholders. Added ADR-033, ADR-034, Pattern-33, G106 to harness. All tests pass."
    ```

**Acceptance per design §6 W6:** Per design doc.

---

### W7 — Qwen Loop Hardening + Dogfood + Closing Sequence

**Agent:** Claude Code
**Wall clock target:** 90 min
**Files touched:** `src/iao/artifacts/loop.py`, `src/iao/artifacts/qwen_client.py`, `src/iao/artifacts/templates.py`, `src/iao/artifacts/schemas.py`, `CHANGELOG.md`, `VERSION` (bump check), `.iao.json` (current_iteration update)

**Steps:**

1. **Update `src/iao/artifacts/loop.py`:**

   - Read template requirements from W3
   - Implement word count check after each Qwen output
   - On under-length output, prompt Qwen with "Your previous output was X words; the minimum is Y. Expand the following sections: ..."
   - Max 3 retries (Pillar 7)
   - On 3rd failure, append to run report `Agent Questions for Kyle`: "Qwen could not produce a {artifact_type} of minimum length {Y} after 3 retries. Best attempt was {X} words. Decide whether to ship the undersized artifact or escalate."

2. **Update `src/iao/artifacts/qwen_client.py`:**

   - Rewrite system prompt to include:
     - The trident mermaid
     - The 10 pillars verbatim
     - The §1–§20 bundle structure as reference
     - Three few-shot examples from `~/dev/projects/kjtcom/docs/iterations/10.69.1/` if accessible (kjtcom-design-10.69.0.md, kjtcom-plan-10.69.0.md, kjtcom-build-log-10.69.1.md)
   - Use `ollama_config.py` for the API client

3. **Update `src/iao/artifacts/templates.py`:**

   - Loads templates from `prompts/`
   - Provides trident_block and ten_pillars_block as template variables (loaded from base.md)
   - Renders with Jinja2

4. **Update `src/iao/artifacts/schemas.py`:**

   - JSON schemas for build log, report, run report, bundle metadata
   - Validation called from loop.py after each Qwen output
   - Design and plan have NO schema validation in W7 — they are immutable inputs per ADR-012 amendment

5. **Run dogfood test:**
   ```fish
   iao iteration build-log 0.1.3.1
   # Expected: Qwen generates docs/iterations/0.1.3/iao-build-log-0.1.3.1.md
   # Read the actual W0–W6 events from event log
   # Output ≥ 2000 words

   wc -w docs/iterations/0.1.3/iao-build-log-0.1.3.1.md
   # Expected: ≥ 2000

   iao iteration report 0.1.3.1
   # Expected: Qwen generates docs/iterations/0.1.3/iao-report-0.1.3.1.md
   # Includes workstream scores table
   # Output ≥ 1500 words

   wc -w docs/iterations/0.1.3/iao-report-0.1.3.1.md
   # Expected: ≥ 1500
   ```

6. **Run closing sequence:**
   ```fish
   iao doctor postflight
   # Expected: all checks pass (or DEFERRED appropriately)
   # Specifically: bundle_quality must PASS (not just exist)
   #               ten_pillars_present must PASS
   #               readme_current must PASS
   #               run_report_complete must DEFERRED (Kyle hasn't filled in yet)
   #               build_log_complete must PASS

   iao iteration close
   # Expected: generates run report at docs/iterations/0.1.3/iao-run-report-0.1.3.1.md
   # Generates bundle at docs/iterations/0.1.3/iao-bundle-0.1.3.1.md
   # Prints workstream summary table to stdout
   # Prints next-steps message
   ```

7. **Verify bundle quality:**
   ```fish
   wc -c docs/iterations/0.1.3/iao-bundle-0.1.3.1.md
   # Expected: ≥ 50000 bytes

   grep -c "^## §" docs/iterations/0.1.3/iao-bundle-0.1.3.1.md
   # Expected: 20

   iao bundle validate docs/iterations/0.1.3/iao-bundle-0.1.3.1.md
   # Expected: exit 0
   ```

8. **Run Phase 0 graduation analysis:**
   ```fish
   iao iteration graduate 0.1.3.1 --analyze
   # Expected: Qwen produces Phase 0 progress assessment
   # Expected output: continue with 0.1.4
   ```

9. **Update CHANGELOG.md:**

   Append the 0.1.3 entry with all 8 workstreams summarized.

10. **Update VERSION:**

    Already done in W0 — verify it's still `0.1.3`.

11. **Update `.iao.json` to next iteration draft:**
    ```fish
    jq '.current_iteration = "0.1.4.0"' .iao.json > .iao.json.tmp && mv .iao.json.tmp .iao.json
    ```

12. **Mark W7 complete in checkpoint:**
    ```fish
    jq '.workstreams.W7.status = "complete" | .workstreams.W7.completed_at = "ISO_TIMESTAMP" | .current_workstream = "review_pending" | .completed_at = "ISO_TIMESTAMP"' .iao-checkpoint.json > .iao-checkpoint.json.tmp && mv .iao-checkpoint.json.tmp .iao-checkpoint.json
    ```

13. **Print closing message and STOP:**
    ```
    ITERATION 0.1.3.1 EXECUTION COMPLETE
    =====================================
    Run report: docs/iterations/0.1.3/iao-run-report-0.1.3.1.md
    Bundle:     docs/iterations/0.1.3/iao-bundle-0.1.3.1.md (XX KB)
    Workstreams: 8/8 complete

    NEXT STEPS:
    1. Review the bundle (take it offline if you want)
    2. Open the run report and fill in your notes for the next iteration
    3. Answer any questions in the "Agent Questions for Kyle" section
    4. Tick the sign-off boxes at the bottom of the run report
    5. Run: iao iteration close --confirm

    Until you run --confirm, this iteration is in PENDING REVIEW state.

    Goodbye.
    ```

    Then exit Claude Code. The iteration is in human-review state.

**Acceptance per design §6 W7:** Per design doc.

---

## Section D — Post-flight (After Kyle's --confirm)

When Kyle returns, fills in his notes, ticks the sign-off boxes, and runs `iao iteration close --confirm`, the post-flight sequence runs:

### D.1 — Validate sign-off

```fish
iao iteration close --confirm
# This command does the following internally:
# 1. Reads docs/iterations/0.1.3/iao-run-report-0.1.3.1.md
# 2. Verifies all sign-off checkboxes are ticked
# 3. If not, prints "Sign-off incomplete: <missing>" and exits nonzero
# 4. If yes, marks iteration complete in .iao.json
```

### D.2 — Final post-flight check pass

```fish
iao doctor postflight
# Expected: all checks PASS (no DEFERRED for run_report_complete now that Kyle filled it in)
```

### D.3 — Seed next iteration

```fish
iao iteration seed
# Reads Kyle's notes section from the run report
# Produces docs/iterations/0.1.4/seed.json with the notes as input context
# (Used by 0.1.4 W7's Qwen design generation)
```

### D.4 — Final state verification

```fish
cat .iao.json | jq .current_iteration
# Expected: "0.1.4.0"

cat .iao-checkpoint.json | jq .completed_at
# Expected: ISO timestamp, not null

command ls docs/iterations/0.1.3/
# Expected: iao-design-0.1.3.md, iao-plan-0.1.3.md, iao-build-log-0.1.3.1.md,
#           iao-report-0.1.3.1.md, iao-run-report-0.1.3.1.md, iao-bundle-0.1.3.1.md
```

### D.5 — Manual git commit (Kyle, per Pillar 0)

```fish
git status
git add -A
git status
# Review what's about to be committed
git commit -m "iao 0.1.3.1: bundle quality, folder consolidation, src-layout, pipelines, feedback loop, Phase 0 charter"
```

(Pillar 0: the agent never runs git commit. Kyle does this manually after reviewing the diff.)

---

## Section E — Rollback Procedure

If iao 0.1.3.1 fails catastrophically at any point:

```fish
# Kill any running tmux session
tmux kill-session -t iao-0.1.3 2>/dev/null

# Remove the broken iao directory
rm -rf ~/dev/projects/iao

# Restore from backup
mv ~/dev/projects/iao.backup-pre-0.1.3 ~/dev/projects/iao

# Reinstall
cd ~/dev/projects/iao
pip install -e . --break-system-packages

# Verify
iao --version
# Expected: 0.1.0 (the pre-0.1.3 state)

# Re-source shell
exec fish
```

**When to rollback:**
- src-layout refactor (W2) breaks every test and the failure isn't a quick fix
- Folder consolidation (W1) leaves the codebase in an inconsistent state
- Bundle quality gates (W3) reject the bundle and the rejection cascade can't be untangled
- Any state where `iao --version` returns a non-zero exit code or wrong version

**When NOT to rollback:**
- Single test failure that has a clear fix (just fix it)
- Wall clock running long but workstreams still completing (let it run)
- Qwen producing undersized artifacts (the run report mechanism handles this — surface to Kyle, don't roll back)
- Kyle hasn't filled in run report notes yet (this is expected — wait for him)

---

## Section F — Wall Clock Targets

| Workstream | Target | Cumulative |
|---|---|---|
| Pre-flight (A.0–A.11) | 15 min | 0:15 |
| W0 Bookkeeping | 5 min | 0:20 |
| W1 Folder consolidation | 45 min | 1:05 |
| W2 src-layout refactor | 40 min | 1:45 |
| W3 Bundle spec + quality gates | 90 min | 3:15 |
| W4 Pipeline scaffolding | 90 min | 4:45 |
| W5 Feedback loop + run report | 75 min | 6:00 |
| Handoff Gemini → Claude Code | 5 min | 6:05 |
| W6 README + charter + pillar enforcement | 75 min | 7:20 |
| W7 Qwen hardening + dogfood + closing | 90 min | 8:50 |
| **Total** | **8h 50min** | |

Soft cap is 8 hours, with the understanding that 50 minutes of overrun is within tolerance. No hard cap. If the iteration is still progressing at 10 hours, let it continue. If it's stalled at 8 hours, surface the stall to Kyle.

---

## Section G — Sign-off

This plan is the operational instruction set for iao 0.1.3.1. It is read by both Gemini CLI (W0–W5) and Claude Code (W6–W7). Both agents have separate briefings: GEMINI.md for Gemini, CLAUDE.md for Claude Code. Both briefings reference this plan for execution detail.

This plan is immutable per ADR-012 once W0 begins. The build log records what actually happened. The report grades it. The run report is where Kyle's voice enters the loop.

— Bootstrap planning chat, 2026-04-09
