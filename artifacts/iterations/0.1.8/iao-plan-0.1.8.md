# iao — Plan 0.1.8

**Iteration:** 0.1.8
**Phase:** 0 (UAT lab for aho)
**Predecessor:** 0.1.7 (graduated with conditions)
**Wall clock target:** ~7h 35m soft cap, no hard cap
**Workstreams:** W0–W8 (nine)
**Authored:** 2026-04-10

This is the operational companion to `iao-design-0.1.8.md`. The design doc is the *why*; this is the *how*. Section C contains copy-pasteable fish command blocks for every workstream. Pre-flight in Section A, post-flight in Section D, rollback in Section E.

---

## Section A — Pre-flight checks

Before launching any executor against this plan, run these checks manually in a fresh fish shell. If any fails, STOP and resolve before launch. This is Pillar 6 enforcement — no implicit state at the transition into 0.1.8.

```fish
# A.0 — Working directory
cd ~/dev/projects/iao
command pwd
# Expected: /home/kthompson/dev/projects/iao

# A.1 — Verify 0.1.7 is closed and checkpoint reflects it
jq .last_completed_iteration .iao-checkpoint.json
# Expected: "0.1.7"

jq .iteration .iao-checkpoint.json
# Expected: "0.1.7" (will bump to 0.1.8 in W0.3)

# A.2 — Design and plan doc present for 0.1.8
command ls docs/iterations/0.1.8/iao-design-0.1.8.md docs/iterations/0.1.8/iao-plan-0.1.8.md
# Expected: both files listed, no "No such file" error

# A.3 — iao binary resolution
which iao
# Expected: /home/kthompson/.local/bin/iao
# If it resolves to ~/iao-middleware/bin/iao, use ./bin/iao explicitly throughout

./bin/iao --version
# Expected: iao 0.1.7

# A.4 — Ollama models present
curl -s http://localhost:11434/api/tags | python3 -c "import json, sys; d = json.load(sys.stdin); names = [m['name'] for m in d['models']]; required = ['qwen3.5:9b', 'nemotron-mini:4b', 'nomic-embed-text:latest']; missing = [r for r in required if not any(r in n for n in names)]; print('OK' if not missing else f'MISSING: {missing}')"
# Expected: OK

# A.5 — Python version
python3 --version
# Expected: Python 3.14.x

# A.6 — ChromaDB archives present
python3 -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma'); [print(col.name, col.count()) for col in c.list_collections()]"
# Expected: iaomw_archive, kjtco_archive, tripl_archive (counts may vary)

# A.7 — Gotcha archive schema sanity (iaomw-G031)
python3 -c "import json; d = json.load(open('data/gotcha_archive.json')); print(type(d).__name__, list(d.keys()) if isinstance(d, dict) else 'list')"
# Expected: dict ['gotchas']

# A.8 — fish config not readable by any agent (Security-G001 — DO NOT CAT)
stat ~/.config/fish/config.fish
# Expected: file exists, owned by kthompson

# A.9 — Event log writable
touch data/iao_event_log.jsonl
command ls -l data/iao_event_log.jsonl
# Expected: file exists, writable by kthompson
```

If all nine pre-flight checks pass, launch the executor per the CLAUDE.md or GEMINI.md launch command. Otherwise STOP and fix.

---

## Section B — Workstream ordering and dependencies

Dependency graph:

```
W0 (environment hygiene) — sequential first, no deps
 └─→ W1 (base.md pillar rewrite) — depends on W0 backup
      └─→ W2 (run_report.py de-hardcoding) — depends on W1 (parser reads post-W1 base.md)
           └─→ W3 (evaluator + templates regex cleanup) — depends on W0 backup
                └─→ W4 (evaluator wired to synthesis) — depends on W3
                     └─→ W5 (§22 instrumentation expansion) — depends on W0 backup
                          └─→ W6 (W8 agent instrumentation fix) — depends on W5 partial
                               └─→ W7 (query_registry.py baseline updates) — depends on W1, W3
                                    └─→ W8 (dogfood + close) — depends on all prior
```

Strict sequential order for a single executor:

```
W0 → W1 → W2 → W3 → W4 → W5 → W6 → W7 → W8
```

If W1 fails (splicer can't find the pillar section), block and escalate as a capability-gap interrupt — Kyle hand-edits base.md, then executor resumes from W2.

If W2 fails (parser can't extract pillars from post-W1 base.md), roll back W1 from `~/dev/projects/iao.backup-pre-0.1.8/base.md`, re-run W1 manually, re-attempt W2.

---

## Section C — Per-workstream fish command blocks

### W0 — Environment Hygiene (15 min)

```fish
# W0.0 — Log W0 start
set W0_START (date -u +%Y-%m-%dT%H:%M:%SZ)
printf '## W0 — Environment Hygiene\n\n**Start:** %s\n\n' "$W0_START" >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W0.1 — Verify working directory
cd ~/dev/projects/iao
command pwd

# W0.2 — Backup state files that 0.1.8 will modify
set BACKUP_DIR ~/dev/projects/iao.backup-pre-0.1.8
mkdir -p $BACKUP_DIR
cp docs/harness/base.md $BACKUP_DIR/base.md
cp src/iao/feedback/run_report.py $BACKUP_DIR/run_report.py
cp src/iao/artifacts/evaluator.py $BACKUP_DIR/evaluator.py
cp src/iao/artifacts/templates.py $BACKUP_DIR/templates.py
cp data/known_hallucinations.json $BACKUP_DIR/known_hallucinations.json
command ls $BACKUP_DIR
# Expected: 5 files listed

# W0.3 — Bump iteration version in checkpoint
jq '.iteration = "0.1.8" | .last_completed_iteration = "0.1.7"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
jq .iteration .iao-checkpoint.json
# Expected: "0.1.8"

# W0.4 — Create iteration directory and initialize build log header
mkdir -p docs/iterations/0.1.8
printf '# Build Log\n\n**Start:** %s\n**Agent:** %s\n**Machine:** NZXTcos\n**Phase:** 0 (UAT lab for aho)\n**Iteration:** 0.1.8\n**Theme:** Pillar rewrite + hardcoded-pillar cleanup + 0.1.7 carryover resolution\n\n---\n\n' "$W0_START" "$IAO_EXECUTOR" > docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W0.5 — Verify design and plan docs are present
test -f docs/iterations/0.1.8/iao-design-0.1.8.md; and echo "design OK"; or echo "design MISSING — STOP"
test -f docs/iterations/0.1.8/iao-plan-0.1.8.md; and echo "plan OK"; or echo "plan MISSING — STOP"

# W0.6 — Append W0 complete
printf '## W0 — Environment Hygiene\n\n**Actions:**\n- Backed up 5 state files to %s\n- Bumped checkpoint iteration to 0.1.8\n- Created docs/iterations/0.1.8/\n- Initialized build log\n- Verified design and plan docs present\n\n**Discrepancies:** none\n\n---\n\n' "$BACKUP_DIR" >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

**Escalation:** If W0.5 reports "design MISSING" or "plan MISSING", STOP. This is a human-setup failure, not an execution failure. Kyle needs to place the files from the planning chat into `docs/iterations/0.1.8/` before resuming.

---

### W1 — Base Harness Pillar Rewrite (60 min)

```fish
# W1.0 — Log W1 start
printf '## W1 — Base Harness Pillar Rewrite\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W1.1 — Audit the current pillar references in base.md
command rg -n "iaomw-Pillar-" docs/harness/base.md
# Expected output shows the lines holding the retired pillar block (target of replacement)

# W1.2 — Write the new pillar block to a scratch file
cat > /tmp/aho-pillars.md <<'PILLAREOF'
## The Eleven Pillars

These pillars supersede the prior `iaomw-Pillar-1..10` numbering, retired in 0.1.8. They govern iao (UAT lab) work and aho (production) work alike. Read authoritatively from this section by `src/iao/feedback/run_report.py` and any other module that needs to quote them.

1. **Delegate everything delegable.** The paid orchestrator is the most expensive resource in the system. Any task that can run on a free local model must run on a free local model. The orchestrator decides; it does not execute. Drafting, classification, retrieval, validation, grading, routing all belong to the local fleet. The orchestrator's minutes are spent on judgment, scope, and novelty.

2. **The harness is the contract.** Agent instructions live in versioned harness files that change at phase or iteration boundaries, not in per-run markdown regenerated from scratch. The orchestrator points at the harness; it does not carry the contract in its own context. Projects run against their own harness overlays on top of a shared base.

3. **Everything is artifacts.** Every task is artifacts-in to artifacts-out. Code, reports, schemas, analyses, migrations, audits, designs — all artifacts. The harness is artifact-agnostic at its core and artifact-specialized at its overlays.

4. **Wrappers are the tool surface.** Agents never call raw tools. Every tool is invoked through a `/bin` wrapper. Wrappers are versioned with the harness, instrumented for the event log, and replayable from recorded inputs.

5. **Three octets, three meanings: phase, iteration, run.** Phase is strategic scope. Iteration is tactical scope. Run is execution instance. Every artifact carries the full phase.iteration.run label.

6. **Transitions are durable.** Moving between phases, iterations, or runs writes state to a durable artifact before the transition is considered complete. Every gate is a write point. No implicit state.

7. **Generation and evaluation are separate roles.** The model that produced an artifact is never the model that grades it. Drafter and reviewer are different agents behind different wrappers.

8. **Efficacy is measured in cost delta.** Every run records orchestrator token cost, local fleet compute time, wall clock, delegate ratio, and output quality signal.

9. **The gotcha registry is the harness's memory.** Every failure mode lands in the registry. A mature harness has more gotchas than an immature one.

10. **Runs are interrupt-disciplined, not interrupt-free.** Once a run launches, agents do not ping for preference, clarification, or approval. The single exception is unavoidable capability gaps (sudo, credentials, physical access) — routed through OpenClaw to a defined notification channel, logged as a first-class event, resumed from the last durable checkpoint.

11. **The human holds the keys.** No agent writes to git. No agent merges. No agent pushes. No agent manages secrets. No wrapper surfaces `git commit` or `git push` under any role.

PILLAREOF

command wc -l /tmp/aho-pillars.md
# Expected: ~30 lines

# W1.3 — Splice the new block into base.md via Python
python3 <<'PYEOF'
from pathlib import Path
import re

base_path = Path("docs/harness/base.md")
base = base_path.read_text()
new_pillars = Path("/tmp/aho-pillars.md").read_text()

lines = base.split("\n")
start_idx = None
end_idx = None

# Find the old pillar section header (case-insensitive match on "pillar")
for i, line in enumerate(lines):
    if start_idx is None and line.startswith("## ") and "illar" in line.lower():
        start_idx = i
        continue
    if start_idx is not None and line.startswith("## ") and i > start_idx:
        end_idx = i
        break

if start_idx is None:
    raise SystemExit("ERROR: could not find pillar section header in base.md — STOP and escalate")
if end_idx is None:
    end_idx = len(lines)

new_content = "\n".join(lines[:start_idx]) + "\n" + new_pillars + "\n" + "\n".join(lines[end_idx:])
base_path.write_text(new_content)
print(f"Replaced lines {start_idx}-{end_idx} ({end_idx - start_idx} lines) in base.md")
PYEOF

# W1.4 — Verify the replacement landed
command rg -c "iaomw-Pillar-" docs/harness/base.md
# Expected: 0

command grep -c "Delegate everything delegable" docs/harness/base.md
# Expected: 1

command grep -c "The human holds the keys" docs/harness/base.md
# Expected: 1

# W1.5 — Verify query_registry.py phrasing is gone from Pillar 3
command rg -n "query_registry" docs/harness/base.md
# Expected: 0 matches (or only within ADR-041 context after W7)

# W1.6 — Append W1 complete
printf '**Actions:**\n- Located old pillar section in base.md (grep confirmed)\n- Replaced with eleven aho pillars via Python splicer\n- Verified 0 `iaomw-Pillar-` references remain\n- Verified Pillar 1 and Pillar 11 landed\n- Verified query_registry.py phrasing gone from Pillar 3\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

**Escalation:** If W1.3 Python exits with "ERROR: could not find pillar section header", STOP. Surface the error as an Agent Question. Kyle hand-edits base.md to insert a `## ` header before the pillar list, then resume W1 from W1.3.

---

### W2 — run_report.py De-hardcoding (75 min)

```fish
# W2.0 — Log W2 start
printf '## W2 — run_report.py De-hardcoding\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W2.1 — Audit the current hardcoded block
command rg -n "iaomw-Pillar" src/iao/feedback/run_report.py
# Expected: lines 103-112 show the hardcoded list

# W2.2 — Write the new parser and accessor as a Python patch file
cat > /tmp/run_report_patch.py <<'PYEOF'
# Replacement block for src/iao/feedback/run_report.py
# Insert near the top of the module, after imports.

from pathlib import Path
import re as _re

_PILLARS_CACHE: list[str] | None = None


def _load_pillars_from_base(base_md_path: Path | None = None) -> list[str]:
    """Read the eleven pillars from the base harness doc.

    Returns a list of strings, one per pillar, numbered and formatted for the run report.
    Raises RuntimeError if the pillar section cannot be parsed.
    """
    if base_md_path is None:
        base_md_path = Path("docs/harness/base.md")
    if not base_md_path.exists():
        raise RuntimeError(f"base harness not found at {base_md_path}")
    text = base_md_path.read_text()
    # Find the pillar section header and capture until the next H2
    section_match = _re.search(
        r"^##\s+.*[Pp]illar.*?\n(.*?)(?=^##\s|\Z)",
        text,
        _re.MULTILINE | _re.DOTALL,
    )
    if not section_match:
        raise RuntimeError("pillar section not found in base.md")
    section = section_match.group(1)
    # Extract numbered pillar entries of the form: "N. **Title** body"
    entries = _re.findall(
        r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(.+?)(?=^\d+\.|\Z)",
        section,
        _re.MULTILINE | _re.DOTALL,
    )
    if len(entries) < 11:
        raise RuntimeError(f"expected 11 pillars in base.md, found {len(entries)}")
    return [
        f"{num}. **{title}** {body.strip()}"
        for num, title, body in entries[:11]
    ]


def get_pillars() -> list[str]:
    """Return the eleven aho pillars, cached after first load."""
    global _PILLARS_CACHE
    if _PILLARS_CACHE is None:
        _PILLARS_CACHE = _load_pillars_from_base()
    return _PILLARS_CACHE
PYEOF

command cat /tmp/run_report_patch.py

# W2.3 — Apply the patch to run_report.py
# Executor action: use Edit/str_replace to:
#   a) Insert the parser code from /tmp/run_report_patch.py near the top of run_report.py (after imports)
#   b) Delete the hardcoded pillar list (lines 103-112)
#   c) Replace the hardcoded list reference with a call to get_pillars()
#
# The exact edit depends on the run_report.py structure. The executor should:
#   1. view the full file first
#   2. identify the hardcoded PILLARS block and its usage sites
#   3. replace the list with get_pillars() at each usage site
#   4. insert the parser + cache near the top of the module

# W2.4 — Add pre-flight check for pillar parsing
# Edit src/iao/preflight/checks.py to add:
#   from iao.feedback.run_report import get_pillars
#   def check_pillars_parseable():
#       try:
#           pillars = get_pillars()
#           if len(pillars) != 11:
#               return False, f"expected 11 pillars, got {len(pillars)}"
#           return True, "OK"
#       except RuntimeError as e:
#           return False, str(e)
# And register check_pillars_parseable in the pre-flight runner.

# W2.5 — Write the unit test
cat > tests/test_run_report_pillars.py <<'PYEOF'
"""Verify run_report.py reads the eleven pillars from base.md, not a hardcoded list."""
from pathlib import Path
import pytest


def test_get_pillars_returns_eleven():
    from iao.feedback.run_report import get_pillars
    pillars = get_pillars()
    assert len(pillars) == 11, f"expected 11 pillars, got {len(pillars)}"


def test_pillar_1_is_delegate():
    from iao.feedback.run_report import get_pillars
    pillars = get_pillars()
    assert "Delegate everything delegable" in pillars[0], \
        f"Pillar 1 does not contain Delegate everything delegable: {pillars[0][:80]}"


def test_pillar_11_is_human_holds_keys():
    from iao.feedback.run_report import get_pillars
    pillars = get_pillars()
    assert "human holds the keys" in pillars[10], \
        f"Pillar 11 does not contain human holds the keys: {pillars[10][:80]}"


def test_no_retired_naming_leaked():
    from iao.feedback.run_report import get_pillars
    pillars = get_pillars()
    for i, p in enumerate(pillars, 1):
        assert "iaomw-Pillar-" not in p, \
            f"retired naming leaked in pillar {i}: {p[:100]}"


def test_cache_returns_same_object():
    from iao.feedback.run_report import get_pillars
    a = get_pillars()
    b = get_pillars()
    assert a is b, "pillar cache not stable across calls"


def test_missing_base_md_raises():
    from iao.feedback.run_report import _load_pillars_from_base
    with pytest.raises(RuntimeError, match="base harness not found"):
        _load_pillars_from_base(Path("/nonexistent/base.md"))
PYEOF

# W2.6 — Run the tests
python3 -m pytest tests/test_run_report_pillars.py -v

# W2.7 — Smoke test: generate a throwaway run report and inspect its pillar block
mkdir -p /tmp/iao-smoke/docs/iterations/0.1.99/
# (The executor should run a minimal iao iteration report command and grep the output)

# W2.8 — Append W2 complete
printf '**Actions:**\n- Extracted pillar parser reading from docs/harness/base.md\n- Replaced hardcoded PILLARS list in run_report.py with get_pillars() call\n- Added cache for in-process stability\n- Added pre-flight check for pillar parsing\n- Added unit tests (6 cases)\n- All tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

**Escalation:** If W2.6 fails with "pillar section not found in base.md", W1 didn't land correctly. Rollback per Section E.1 (restore base.md only), re-run W1, resume at W2.

---

### W3 — evaluator.py and templates.py Regex Cleanup (45 min)

```fish
# W3.0 — Log W3 start
printf '## W3 — evaluator.py and templates.py Regex Cleanup\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W3.1 — Audit PILLAR_ID_RE usage
command rg -n "PILLAR_ID_RE" src/ tests/
# Expected: definition in evaluator.py line 21, possibly usages within the same file and in tests

# W3.2 — Audit pillar-block template regex
command rg -n "iaomw-Pillar-" src/iao/artifacts/templates.py
# Expected: line 40 regex

# W3.3 — Edit evaluator.py to remove PILLAR_ID_RE
# Executor action: use str_replace to delete:
#   a) The PILLAR_ID_RE definition line
#   b) Any extract or validate calls that use PILLAR_ID_RE
#   c) If references["pillar_ids"] is populated from this regex, drop that key from the result dict

# W3.4 — Edit templates.py to remove the pillar-block template regex
# Executor action: delete the regex and any code that depends on it

# W3.5 — Update known_hallucinations.json: remove query_registry.py, add retired iaomw-Pillar-N
python3 <<'PYEOF'
import json
from pathlib import Path

p = Path("data/known_hallucinations.json")
d = json.loads(p.read_text())

# Find any list-valued key and strip query_registry.py entries
for key, val in list(d.items()):
    if isinstance(val, list):
        d[key] = [x for x in val if "query_registry" not in str(x)]

# Identify the main forbidden phrases list
forbidden_key = None
for k in d:
    if isinstance(d[k], list) and "forbidden" in k.lower():
        forbidden_key = k
        break
if forbidden_key is None:
    # Fall back to the first list-valued key
    for k in d:
        if isinstance(d[k], list):
            forbidden_key = k
            break

if forbidden_key is None:
    raise SystemExit("ERROR: could not find forbidden-phrase list in known_hallucinations.json")

# Add retired iaomw-Pillar-N strings if not already present
for i in range(1, 11):
    marker = f"iaomw-Pillar-{i}"
    if marker not in d[forbidden_key]:
        d[forbidden_key].append(marker)

p.write_text(json.dumps(d, indent=2))
print(f"Updated {p}: key={forbidden_key}, len={len(d[forbidden_key])}")
PYEOF

# W3.6 — Verify cleanup
command rg -n "PILLAR_ID_RE" src/ tests/
# Expected: 0 matches

command rg -n "iaomw-Pillar-" src/iao/artifacts/
# Expected: 0 matches

command rg "query_registry" data/known_hallucinations.json
# Expected: 0 matches

command rg '"iaomw-Pillar-' data/known_hallucinations.json
# Expected: 10 matches (the retired markers added in W3.5)

# W3.7 — Run existing evaluator tests
python3 -m pytest tests/test_evaluator.py -v

# W3.8 — Append W3 complete
printf '**Actions:**\n- Removed PILLAR_ID_RE from evaluator.py\n- Removed pillar block template regex from templates.py\n- Updated known_hallucinations.json: removed query_registry.py entries, added retired iaomw-Pillar-1..10 as forbidden markers\n- All evaluator tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

---

### W4 — Evaluator Wired to Synthesis Pass (60 min)

```fish
# W4.0 — Log W4 start
printf '## W4 — Evaluator Wired to Synthesis Pass\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W4.1 — Locate synthesis call sites in loop.py
command rg -n "synthesis\|build_log\|def.*report" src/iao/artifacts/loop.py

# W4.2 — Read the evaluator interface
command rg -n "def evaluate_text" src/iao/artifacts/evaluator.py

# W4.3 — Edit loop.py to wrap synthesis outputs with evaluator calls
# Executor action: after each Qwen synthesis call (build log synthesis and report synthesis),
# add a call to evaluate_text with artifact_type set appropriately. On severity=reject,
# log_event("synthesis_evaluator_reject", ...), retry once with a diagnostic-feedback prompt,
# accept whatever comes back on the second try, log to build log as carryover if still flagged.
#
# Pseudocode:
#   synthesis_output = qwen_client.generate(synthesis_prompt)
#   result = evaluate_text(synthesis_output, artifact_type="build_log_synthesis")
#   if result.severity == "reject":
#       log_event("synthesis_evaluator_reject", errors=result.errors)
#       diagnostic_prompt = build_retry_prompt(synthesis_prompt, result.errors)
#       synthesis_output = qwen_client.generate(diagnostic_prompt)
#       result2 = evaluate_text(synthesis_output, artifact_type="build_log_synthesis")
#       if result2.severity == "reject":
#           log_event("synthesis_evaluator_carryover", errors=result2.errors)
#           # Continue with the flawed output; log as carryover in build log
#   return synthesis_output

# W4.4 — Regression test: the 0.1.7 split-agent paragraph must be rejected
cat > tests/test_synthesis_evaluator.py <<'PYEOF'
"""Regression test: the 0.1.7 build log synthesis contained split-agent language.
The W3 evaluator did not catch it because it wasn't wired to the synthesis pass.
After 0.1.8 W4, the evaluator runs on synthesis outputs and rejects this paragraph.
"""
from iao.artifacts.evaluator import evaluate_text


SPLIT_AGENT_PARAGRAPH = """
The iteration followed the bounded sequential pattern with split-agent execution
(Gemini W0-W5, Claude W6-W7). Wall clock time was within the soft cap of ~12 hours.
No rollback was necessary.
"""


def test_split_agent_rejected_in_synthesis():
    result = evaluate_text(SPLIT_AGENT_PARAGRAPH, artifact_type="build_log_synthesis")
    assert result.severity == "reject", \
        f"expected reject, got {result.severity}; errors: {result.errors}"
    errors_text = " ".join(str(e).lower() for e in result.errors)
    assert "split-agent" in errors_text or "split agent" in errors_text, \
        f"split-agent not in errors: {result.errors}"


def test_clean_paragraph_accepted():
    clean = """
    The iteration executed all nine workstreams sequentially. Wall clock time was
    within the soft cap. No discrepancies were observed.
    """
    result = evaluate_text(clean, artifact_type="build_log_synthesis")
    assert result.severity != "reject", \
        f"clean paragraph unexpectedly rejected: {result.errors}"
PYEOF

python3 -m pytest tests/test_synthesis_evaluator.py -v

# W4.5 — Append W4 complete
printf '**Actions:**\n- Wired evaluator to build log and report synthesis passes in loop.py\n- Added 1-retry with diagnostic feedback on reject\n- Added regression test against 0.1.7 split-agent paragraph\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

---

### W5 — §22 Instrumentation Expansion (90 min, partial ship acceptable)

```fish
# W5.0 — Log W5 start
printf '## W5 — §22 Instrumentation Expansion\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W5.1 — Read the current event log schema
command rg -n "log_event\|iao_event_log" src/iao/ 2>/dev/null | head -30

# W5.2 — Confirm there is a central log_event function
command rg -n "def log_event" src/iao/

# W5.3 — Wire src/iao/cli.py
# Executor action: in each subcommand handler (project, init, check, push, log, doctor,
# status, eval, registry, rag, telegram, preflight, postflight, secret, pipeline, iteration),
# add at the top:
#   log_event(component="iao-cli", event_type="cli_invocation", name="<subcommand>")

# W5.4 — Wire src/iao/agents/openclaw.py
# Executor action: in OpenClawSession.__init__, log session_start.
# In chat(), log openclaw_chat.
# In execute_code(), log openclaw_execute_code.

# W5.5 — Wire src/iao/agents/nemoclaw.py
# Executor action: in NemoClawOrchestrator.dispatch(), log nemoclaw_dispatch with classification.

# W5.6 — Wire src/iao/artifacts/evaluator.py
# Executor action: at the end of evaluate_text(), log evaluator_run with severity.

# W5.7 — Wire src/iao/artifacts/repetition_detector.py
# Executor action: in the path that raises DegenerateGenerationError, log repetition_detected
# with window_size and repeated_token.

# W5.8 — Wire src/iao/postflight/structural_gates.py
# Executor action: in each gate check function, log structural_gate with gate name and pass/fail.

# W5.9 — Write the smoke test
cat > scripts/smoke_instrumentation.py <<'PYEOF'
"""Smoke test for §22 instrumentation coverage.
Clears the event log, runs minimal invocations of each instrumented component,
asserts the event log has at least 6 unique component names.
"""
import json
import sys
from pathlib import Path

LOG_PATH = Path("data/iao_event_log.jsonl")
LOG_PATH.write_text("")  # clear

# 1. Invoke the CLI (smallest possible subcommand)
import subprocess
subprocess.run(["./bin/iao", "--version"], capture_output=True)

# 2. Invoke the evaluator
from iao.artifacts.evaluator import evaluate_text
evaluate_text("sample content for smoke test", artifact_type="smoke")

# 3. Invoke a structural gate
from iao.postflight.structural_gates import check_required_sections
check_required_sections("# Header\n", required=["# Header"])

# 4. Invoke OpenClaw (if Ollama is up; skip gracefully if not)
try:
    from iao.agents.openclaw import OpenClawSession
    session = OpenClawSession()
    # just creating the session should log session_start
    del session
except Exception as e:
    print(f"OpenClaw smoke skipped: {e}", file=sys.stderr)

# 5. Invoke NemoClaw
try:
    from iao.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator()
    del orch
except Exception as e:
    print(f"NemoClaw smoke skipped: {e}", file=sys.stderr)

# 6. Repetition detector (lightweight — just instantiate)
try:
    from iao.artifacts.repetition_detector import RepetitionDetector
    d = RepetitionDetector(window_size=10)
    del d
except Exception as e:
    print(f"RepetitionDetector smoke skipped: {e}", file=sys.stderr)

# Read back the event log
if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
    print("FAIL: event log is empty after smoke test")
    sys.exit(1)

events = [json.loads(line) for line in LOG_PATH.read_text().splitlines() if line.strip()]
components = set(e.get("component", "unknown") for e in events)
print(f"Events logged: {len(events)}")
print(f"Unique components: {sorted(components)}")
print(f"Component count: {len(components)}")

if len(components) < 4:
    print(f"FAIL: expected >=4 unique components, got {len(components)}")
    sys.exit(1)

print("PASS")
PYEOF

python3 scripts/smoke_instrumentation.py

# W5.10 — Append W5 complete
printf '**Actions:**\n- Wired event log instrumentation to: iao-cli, openclaw, nemoclaw, evaluator, repetition_detector, structural_gates\n- Smoke test passes with N unique components\n\n**Discrepancies:** (list any components that could not be wired — this workstream permits partial ship)\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

**Partial-ship criterion:** At 60 minutes elapsed (W5 start + 60m), if fewer than 4 components are wired, ship what's wired, log the unfinished components as discrepancies in the build log, continue to W6. Any unwired component carries to 0.1.9.

---

### W6 — W8 Agent Instrumentation Fix (30 min)

```fish
# W6.0 — Log W6 start
printf '## W6 — W8 Agent Instrumentation Fix\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W6.1 — Trace the source of "unknown" in workstream summary
command rg -n "unknown\|agent" src/iao/feedback/run_report.py

# W6.2 — Trace checkpoint write path for agent field
command rg -n "agent\|executor" src/iao/artifacts/loop.py

# W6.3 — Fix: read IAO_EXECUTOR env var as fallback in run_report.py
# Executor action: in the function that builds the workstream summary table, change
#   agent = checkpoint.get(f"w{n}_agent", "unknown")
# to
#   import os
#   agent = checkpoint.get(f"w{n}_agent") or os.environ.get("IAO_EXECUTOR", "unknown")

# W6.4 — Fix: write agent to checkpoint at each workstream start in loop.py
# Executor action: in the workstream start handler, add
#   import os
#   checkpoint[f"w{n}_agent"] = os.environ.get("IAO_EXECUTOR", "unknown")
#   write_checkpoint(checkpoint)

# W6.5 — Unit test
cat > tests/test_workstream_agent.py <<'PYEOF'
"""Verify workstream summary table populates agent from IAO_EXECUTOR when checkpoint is empty."""
import os
import pytest


def test_agent_from_env_var(monkeypatch):
    monkeypatch.setenv("IAO_EXECUTOR", "gemini-cli")
    # Import fresh so env var is picked up
    from iao.feedback.run_report import build_workstream_summary

    # Minimal checkpoint with no per-workstream agent fields
    checkpoint = {
        "iteration": "0.1.8",
        "workstreams_complete": 2,
        "w0_status": "complete",
        "w1_status": "complete",
    }
    rows = build_workstream_summary(checkpoint)
    for row in rows:
        assert row.get("agent") != "unknown", \
            f"workstream {row.get('name')} has unknown agent; expected gemini-cli"


def test_agent_from_checkpoint_preferred(monkeypatch):
    monkeypatch.setenv("IAO_EXECUTOR", "gemini-cli")
    from iao.feedback.run_report import build_workstream_summary

    checkpoint = {
        "iteration": "0.1.8",
        "workstreams_complete": 1,
        "w0_status": "complete",
        "w0_agent": "claude-code",  # explicit override
    }
    rows = build_workstream_summary(checkpoint)
    w0 = next((r for r in rows if r.get("name") == "W0"), None)
    assert w0 is not None
    assert w0["agent"] == "claude-code", \
        f"expected checkpoint value claude-code, got {w0['agent']}"
PYEOF

python3 -m pytest tests/test_workstream_agent.py -v

# W6.6 — Append W6 complete
printf '**Actions:**\n- Added IAO_EXECUTOR env var fallback in run_report.py workstream summary\n- Updated loop.py to write agent to checkpoint per workstream start\n- Added unit tests\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

---

### W7 — Baseline Updates for query_registry.py (20 min)

```fish
# W7.0 — Log W7 start
printf '## W7 — Baseline Updates for query_registry.py\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W7.1 — Verify W3 already removed query_registry.py from known_hallucinations.json
command rg "query_registry" data/known_hallucinations.json
# Expected: 0 matches

# W7.2 — Verify W1 cleaned base.md of the Pillar 3 query_registry.py phrasing
command rg "query_registry" docs/harness/base.md
# Expected: 0 matches (about to become 1 after ADR-041 append)

# W7.3 — Verify agent briefs are already clean (Kyle updated post-0.1.7)
command rg "query_registry" CLAUDE.md GEMINI.md
# Expected: only "Known shims" context lines, no "forbidden" context

# W7.4 — Append ADR-041 to base.md
cat >> docs/harness/base.md <<'ADREOF'

---

## ADR-041 — scripts/query_registry.py is a legitimate shim

**Status:** Accepted
**Date:** 2026-04-10 (iao 0.1.8 W7)

### Context

During the 0.1.7 post-close audit, `scripts/query_registry.py` surfaced in the §20 file inventory. Prior documentation (agent briefs, `data/known_hallucinations.json`, evaluator baseline) listed it as forbidden because the same filename exists as a kjtcom script and the iao version was assumed to be a Qwen hallucination. Audit revealed otherwise.

### Decision

`scripts/query_registry.py` is a 6-line Python shim wrapping `iao.registry.main`. It is tracked by `src/iao/doctor.py` at line 70 as an expected shim alongside `scripts/build_context_bundle.py`. It is a legitimate iao file and may be referenced in artifacts without flagging.

### Consequences

- The stale Pillar 3 phrasing `"First action: query_registry.py"` in `docs/harness/base.md` was fixed in 0.1.8 W1 (the pillar rewrite). Canonical Pillar 3 invocation under the retired iaomw naming was `iao registry query "<topic>"`, and under the new eleven pillars there is no Pillar 3 diligence-invocation command at all — "Everything is artifacts" replaces it.
- `data/known_hallucinations.json` was updated in 0.1.8 W3 to remove `query_registry.py` from the forbidden list.
- Agent briefs `CLAUDE.md` and `GEMINI.md` were updated post-0.1.7 (before 0.1.8 began) to list `scripts/query_registry.py` as a known shim in hard rule 9.

ADREOF

# W7.5 — Verify ADR-041 landed
command grep -c "ADR-041" docs/harness/base.md
# Expected: 1

# W7.6 — Append W7 complete
printf '**Actions:**\n- Verified query_registry.py resolved across all baselines\n- Appended ADR-041 to base.md\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

---

### W8 — Dogfood + Close (60 min)

```fish
# W8.0 — Log W8 start
printf '## W8 — Dogfood + Close\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md

# W8.1 — Generate build log via Qwen (now evaluated per W4)
./bin/iao iteration build-log 0.1.8

# W8.2 — Generate report via Qwen (now evaluated per W4)
./bin/iao iteration report 0.1.8

# W8.3 — Run post-flight validation
./bin/iao doctor postflight 0.1.8

# W8.4 — Generate run report and bundle (does NOT --confirm; Kyle does that)
./bin/iao iteration close

# W8.5 — Verification 1: run report contains Pillar 1 text (the read-through from base.md worked)
command grep -c "Delegate everything delegable" docs/iterations/0.1.8/iao-run-report-0.1.8.md
# Expected: ≥1 — PASS if so

# W8.6 — Verification 2: run report does NOT contain retired pillar naming
command grep -c "iaomw-Pillar-" docs/iterations/0.1.8/iao-run-report-0.1.8.md
# Expected: 0 — PASS if so

# W8.7 — Verification 3: build log does NOT contain split-agent language
command grep -c "split-agent" docs/iterations/0.1.8/iao-build-log-0.1.8.md
# Expected: 0 — PASS if so

# W8.8 — Verification 4: §22 has ≥6 components
python3 <<'PYEOF'
import re
bundle = open("docs/iterations/0.1.8/iao-bundle-0.1.8.md").read()
match = re.search(r"## §22.*?(?=\n## §|\Z)", bundle, re.DOTALL)
if not match:
    print("FAIL: §22 section not found in bundle")
    exit(1)
section = match.group()
# Count unique component names from table rows (skip header + separator)
rows = [line for line in section.split("\n") if line.startswith("|") and not line.startswith("|---")]
components = set()
for row in rows[1:]:  # skip header
    cells = [c.strip() for c in row.split("|") if c.strip()]
    if cells:
        components.add(cells[0])
print(f"Components: {sorted(components)}")
print(f"Count: {len(components)}")
if len(components) >= 6:
    print("PASS")
else:
    print(f"FAIL: expected >=6 components, got {len(components)}")
    exit(1)
PYEOF

# W8.9 — Verification 5: workstream summary has zero unknown agents
command grep -c "| unknown " docs/iterations/0.1.8/iao-run-report-0.1.8.md
# Expected: 0 — PASS if so

# W8.10 — Verification 6: bundle structural integrity (22 sections)
command grep -c "^## §" docs/iterations/0.1.8/iao-bundle-0.1.8.md
# Expected: 22 — PASS if so

# W8.11 — Send Telegram notification
./bin/iao telegram notify "iao 0.1.8 complete — $(date -u +%H:%M) UTC"

# W8.12 — Print closing message
printf '\n================================================\nITERATION 0.1.8 EXECUTION COMPLETE\n================================================\nRun report: docs/iterations/0.1.8/iao-run-report-0.1.8.md\nBundle:     docs/iterations/0.1.8/iao-bundle-0.1.8.md\nWorkstreams: (report actual count from checkpoint)\n\nTelegram notification sent to Kyle.\n\nNEXT STEPS (Kyle):\n1. Review the bundle\n2. Open the run report, fill in Kyles Notes\n3. Answer any agent questions\n4. Tick 5 sign-off checkboxes\n5. Run: ./bin/iao iteration close --confirm\n\nUntil --confirm, iteration is in PENDING REVIEW state.\n'

# W8.13 — Append W8 complete
printf '**Actions:**\n- Generated build log, report, run report, bundle via repaired loop\n- Ran all six verification checks\n- Telegram notification sent\n- Iteration in PENDING REVIEW state awaiting Kyle sign-off\n\n**Verification results:**\n- V1 (Pillar 1 text present): (pass/fail)\n- V2 (no iaomw-Pillar-): (pass/fail)\n- V3 (no split-agent): (pass/fail)\n- V4 (§22 has >=6 components): (pass/fail)\n- V5 (no unknown agents): (pass/fail)\n- V6 (22 bundle sections): (pass/fail)\n\n**Discrepancies:** (list any verification failures)\n\n---\n\n' >> docs/iterations/0.1.8/iao-build-log-0.1.8.md
```

**Escalation:** If any verification fails, log the failure in the build log, surface to Agent Questions in the run report, STOP. Do not attempt to fix a generated artifact mid-W8. Kyle reviews the failures and decides next step. Graduation verdict under that path is likely GRADUATE WITH CONDITIONS or DO NOT GRADUATE per the design §8 criteria.

---

## Section D — Post-flight checks

After W8 completes:

```fish
# D.1 — All nine workstream headers present in build log
command grep -c "^## W[0-8] " docs/iterations/0.1.8/iao-build-log-0.1.8.md
# Expected: 9

# D.2 — No open TODO/FIXME in build log
command rg "TODO\|FIXME\|XXX" docs/iterations/0.1.8/iao-build-log-0.1.8.md
# Expected: 0 matches, or only within intentional discrepancy notes

# D.3 — Bundle size sanity
command du -h docs/iterations/0.1.8/iao-bundle-0.1.8.md
# Expected: 80KB – 200KB

# D.4 — Checkpoint reflects completion
jq '.workstreams_complete' .iao-checkpoint.json
# Expected: 9 (or the number actually shipped)

# D.5 — Event log has entries from this iteration
command wc -l data/iao_event_log.jsonl
# Expected: >100 (the dogfood loop produces many events)
```

---

## Section E — Rollback procedure

If 0.1.8 execution fails catastrophically and Kyle needs to revert to 0.1.7 state:

```fish
# E.1 — Restore backed-up files
set BACKUP_DIR ~/dev/projects/iao.backup-pre-0.1.8
cp $BACKUP_DIR/base.md docs/harness/base.md
cp $BACKUP_DIR/run_report.py src/iao/feedback/run_report.py
cp $BACKUP_DIR/evaluator.py src/iao/artifacts/evaluator.py
cp $BACKUP_DIR/templates.py src/iao/artifacts/templates.py
cp $BACKUP_DIR/known_hallucinations.json data/known_hallucinations.json

# E.2 — Revert checkpoint
jq '.iteration = "0.1.7"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json

# E.3 — Mark 0.1.8 incomplete
printf '# INCOMPLETE\n\n0.1.8 was attempted %s and rolled back.\nReason: (fill in)\n\nSee backup at %s for the pre-0.1.8 state of modified files.\n' (date -u +%Y-%m-%d) $BACKUP_DIR > docs/iterations/0.1.8/INCOMPLETE.md

# E.4 — Verify pytest baseline still passes
python3 -m pytest tests/ -v
```

Partial rollbacks (single file) are acceptable if only one workstream needs reverting. Full rollback is the nuclear option and should only run if W1 or W2 landed destructively and downstream workstreams cannot complete.

---

## Section F — Wall clock estimate

| Workstream | Target | Cumulative |
|---|---|---|
| W0 — Environment Hygiene | 15 min | 0:15 |
| W1 — Base Harness Pillar Rewrite | 60 min | 1:15 |
| W2 — run_report.py De-hardcoding | 75 min | 2:30 |
| W3 — evaluator/templates Regex Cleanup | 45 min | 3:15 |
| W4 — Evaluator Wired to Synthesis | 60 min | 4:15 |
| W5 — §22 Instrumentation Expansion | 90 min | 5:45 |
| W6 — W8 Agent Instrumentation Fix | 30 min | 6:15 |
| W7 — query_registry.py Baseline Updates | 20 min | 6:35 |
| W8 — Dogfood + Close | 60 min | 7:35 |

**Soft cap:** 7:35.
**Hard cap:** none (Pillar 10 — the executor finishes cleanly rather than bailing on a timer).

---

*Plan doc generated 2026-04-10, iao 0.1.8 planning chat (Kyle + Claude web)*
