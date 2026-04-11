# iao — Plan 0.1.7

**Iteration:** 0.1.7 (three octets, locked — do not add a fourth)
**Phase:** 0 (NZXT-only authoring)
**Theme:** Let Qwen Cook
**Date:** April 09, 2026
**Machine:** NZXTcos
**Repo:** ~/dev/projects/iao
**Wall clock target:** ~10 hours soft cap (no hard cap)
**Run mode:** Single executor — Gemini CLI primary, Claude Code fallback
**Iteration counter jump:** 0.1.4 → 0.1.7 directly (0.1.5 marked INCOMPLETE, 0.1.6 was forensic audit only)
**Status:** Planning (immutable once W0 begins)

This plan operationalizes `iao-design-0.1.7.md`. Read the design first if you haven't. The design defines *what* and *why*; this plan defines *how* and *in what order*, in commands the executor can paste and run.

---

## What is iao

iao is the methodology and Python package for running disciplined LLM-driven engineering iterations. 0.1.7 is the iteration that repairs the artifact loop supporting Qwen. Streaming, repetition detection, word-count inversion, anti-hallucination evaluator, rich seed, RAG freshness weighting, two-pass generation (experimental), component checklist in bundle, OpenClaw Ollama-native rebuild, full dogfood. See design §2 and Appendix A for the why.

---

## Section A — Pre-flight

### A.0 — Working directory and shell state

```fish
cd ~/dev/projects/iao
pwd
# Expected: /home/kthompson/dev/projects/iao

command ls -la .iao.json VERSION pyproject.toml
# Expected: all three files present

# Check current iao binary resolution (will be fixed in W0.1)
which iao
./bin/iao --version
```

### A.1 — Backup

```fish
test -d ~/dev/projects/iao.backup-pre-0.1.7
# Expected: fails (no backup yet)

cp -a ~/dev/projects/iao ~/dev/projects/iao.backup-pre-0.1.7
test -d ~/dev/projects/iao.backup-pre-0.1.7
# Expected: succeeds
```

### A.2 — Current iao state verification

```fish
jq .current_iteration .iao.json
# Expected: "0.1.4"

jq .last_completed_iteration .iao.json
# Expected: "0.1.4" (or "0.1.3" — W0 will set it to "0.1.4")

test -d docs/iterations/0.1.5
# Expected: succeeds (drafts exist from abandoned attempt)

command ls docs/iterations/0.1.5/
# Expected: iao-design-0.1.5.md, iao-plan-0.1.5.md

test -d docs/iterations/0.1.6/precursors
# Expected: succeeds (forensic audit output from 0.1.6)

test -d docs/iterations/0.1.7
# Expected: succeeds (this iteration's folder, contains this plan doc)
```

### A.3 — Ollama and model fleet

```fish
curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; d=json.load(sys.stdin); print('\n'.join(m['name'] for m in d['models']))"
# Expected output includes:
#   qwen3.5:9b
#   nemotron-mini:4b
#   haervwe/GLM-4.6V-Flash-9B:latest
#   nomic-embed-text:latest
```

### A.4 — Python environment

```fish
python3 --version
# Expected: 3.14.x

pip show iao | grep -E "Version|Location|Editable"
# Expected: Version 0.1.4, editable project location = ~/dev/projects/iao
```

### A.5 — ChromaDB archives exist

```fish
python3 -c "
from iao.rag.archive import list_archives
archives = list_archives()
for name, count in archives.items():
    print(f'{name}: {count}')
"
# Expected:
#   iaomw_archive: 17
#   kjtco_archive: 282
#   tripl_archive: 144
```

### A.6 — No conflicting tmux session

```fish
tmux ls 2>/dev/null | grep "iao-0.1.7"
# Expected: no output
```

### A.7 — Sleep/suspend masked

```fish
systemctl status sleep.target 2>&1 | grep -E "Loaded|Active"
# Expected: "masked"
```

### A.8 — Gotcha registry schema sanity check (G108 — new)

```fish
python3 -c "
import json
with open('data/gotcha_archive.json') as f:
    d = json.load(f)
print(f'Top-level type: {type(d).__name__}')
print(f'Has gotchas key: {\"gotchas\" in d if isinstance(d, dict) else False}')
if isinstance(d, dict) and 'gotchas' in d:
    print(f'Entries: {len(d[\"gotchas\"])}')
"
# Expected:
#   Top-level type: dict
#   Has gotchas key: True
#   Entries: 13
```

This is a **critical sanity check**. If anything in W0-W9 modifies the gotcha registry, it MUST use `d["gotchas"].append(...)`, not `d.append(...)`. The 0.1.4 W3 session crashed because it assumed the file was a list. It is a dict with a `gotchas` key.

### A.9 — Pre-flight summary

```fish
echo "
PRE-FLIGHT COMPLETE
===================
Working dir: $(pwd)
Python: $(python3 --version)
iao (pip): $(pip show iao | grep Version | cut -d' ' -f2)
Ollama models: $(curl -s http://localhost:11434/api/tags | python3 -c 'import sys,json; print(len(json.load(sys.stdin)[\"models\"]))') present
Disk: $(df -h . | awk 'NR==2 {print \$4}') free

READY TO LAUNCH iao 0.1.7
"
```

---

## Section B — Launch Protocol

### B.1 — Open tmux session

```fish
tmux new-session -d -s iao-0.1.7 -c ~/dev/projects/iao
tmux send-keys -t iao-0.1.7 'cd ~/dev/projects/iao' Enter
tmux send-keys -t iao-0.1.7 'set -x IAO_ITERATION 0.1.7' Enter
tmux send-keys -t iao-0.1.7 'set -x IAO_PROJECT_NAME iao' Enter
tmux send-keys -t iao-0.1.7 'set -x IAO_PROJECT_CODE iaomw' Enter
```

### B.2 — Initialize checkpoint

```fish
set ts (date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s\n' '{
  "iteration": "0.1.7",
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
    "W7": {"status": "pending", "executor": "gemini-cli"},
    "W8": {"status": "pending", "executor": "gemini-cli"},
    "W9": {"status": "pending", "executor": "gemini-cli"}
  },
  "completed_at": null,
  "mode": "single-executor"
}' > .iao-checkpoint.json

jq .iteration .iao-checkpoint.json
# Expected: "0.1.7"
```

### B.3 — Launch executor

**Gemini CLI:**
```fish
tmux send-keys -t iao-0.1.7 'gemini --yolo' Enter
```

**Claude Code (fallback):**
```fish
tmux send-keys -t iao-0.1.7 'claude --dangerously-skip-permissions' Enter
```

Both read their respective brief (GEMINI.md or CLAUDE.md) at session start. Both reference this plan doc Section C for execution detail. Both run W0 through W9 sequentially.

### B.4 — Monitor and close

Kyle attaches occasionally via `tmux attach -t iao-0.1.7`. When W9 completes, the executor stops in PENDING REVIEW state. Kyle reviews, fills Kyle's Notes in the run report, ticks sign-off boxes, runs `./bin/iao iteration close --confirm`.

---

## Section C — Workstream Execution

### W0 — Environment Hygiene

**Executor:** Gemini CLI
**Wall clock target:** 15 min

#### W0.1 — Fix PATH: remove stale global iao

```fish
which iao
# Before: /home/kthompson/iao-middleware/bin/iao
# After: ~/.local/bin/iao

# Check what fish config files set PATH
command ls ~/.config/fish/conf.d/ 2>/dev/null

# DO NOT cat the main config.fish (API key leak risk, G-Security-1)
# Instead, grep for iao-middleware specifically
grep -rn "iao-middleware" ~/.config/fish/conf.d/ ~/.config/fish/functions/ 2>/dev/null

# Gemini identifies the file and line, then edits via the Edit tool
# Remove the offending line (likely: `fish_add_path ~/iao-middleware/bin` or `set -x PATH ~/iao-middleware/bin $PATH`)
# DO NOT delete the fish config entirely — only remove the iao-middleware line

# Verify in a fresh fish session (new shell picks up the change)
fish -c "which iao"
# Expected: ~/.local/bin/iao
```

If the fresh fish session still returns the old path, hash -r may be needed, or the change may only take effect on the next login. For the purpose of this iteration, use `./bin/iao` explicitly throughout execution and rely on the PATH fix taking effect for future sessions.

#### W0.2 — Delete stale .pyc files

```fish
cd ~/dev/projects/iao
command ls src/iao/postflight/__pycache__/ | grep -E "(claw3d|flutter|map_tab|firestore_baseline)"
# Expected: several .cpython-314.pyc files for deleted modules

rm -f src/iao/postflight/__pycache__/claw3d_version_matches.*.pyc
rm -f src/iao/postflight/__pycache__/deployed_claw3d_matches.*.pyc
rm -f src/iao/postflight/__pycache__/deployed_flutter_matches.*.pyc
rm -f src/iao/postflight/__pycache__/map_tab_renders.*.pyc
rm -f src/iao/postflight/__pycache__/firestore_baseline.*.pyc

command ls src/iao/postflight/__pycache__/ | grep -E "(claw3d|flutter|map_tab|firestore_baseline)"
# Expected: no output
```

#### W0.3 — Close 0.1.4 formally in .iao.json

```fish
jq '.last_completed_iteration = "0.1.4" | .current_iteration = "0.1.7"' .iao.json > .iao.json.tmp
mv .iao.json.tmp .iao.json

jq .current_iteration .iao.json
# Expected: "0.1.7"

jq .last_completed_iteration .iao.json
# Expected: "0.1.4"
```

#### W0.4 — Update VERSION, pyproject, cli.py

```fish
echo "0.1.7" > VERSION
cat VERSION
# Expected: 0.1.7

sed -i 's/version = "0.1.4"/version = "0.1.7"/' pyproject.toml
grep 'version = ' pyproject.toml | head -3

# Update CLI version string
grep -n "0.1.4" src/iao/cli.py
sed -i 's/"iao 0.1.4"/"iao 0.1.7"/' src/iao/cli.py
grep 'iao 0.1' src/iao/cli.py

# Reinstall to pick up version
pip install -e . --break-system-packages --quiet

iao --version
# Expected: iao 0.1.7

./bin/iao --version
# Expected: iao 0.1.7

# These should now be identical (PATH fix in W0.1 + pip reinstall)
```

#### W0.5 — Create 0.1.5 INCOMPLETE marker

```fish
printf '# INCOMPLETE — iao 0.1.5

**Status:** Drafted but never executed.
**Date marked incomplete:** 2026-04-09 (during 0.1.7 W0)

## What happened

0.1.5 was scoped in a chat planning session between Kyle and Claude web after 0.1.4 closed. Before the full design and plan were authored in chat, Kyle asked Gemini CLI to generate the 0.1.5 artifacts via the Qwen artifact loop. Gemini ran `iao iteration design 0.1.5` and `iao iteration plan 0.1.5`. Both commands produced output files on disk. Neither was ever executed as an iteration.

## Why it was abandoned

The generated drafts exhibited severe quality failures:

1. The plan document entered a degenerate repetition loop in its tail, repeating the same 12-line footer block 15+ times until the generation truncated mid-word
2. The design document hallucinated file references including `query_registry.py` (a kjtcom file, not an iao file) and an invented list of subpackages (`src/iao/eval/`, `src/iao/llm/`, `src/iao/vector/`, `src/iao/agent/`, `src/iao/chain/`) none of which exist in iao
3. The design document mislabeled the phase as "Phase 1 (Production Readiness)" when iao is in Phase 0
4. The design document fabricated iteration history including a nonexistent 0.1.1 iteration
5. Six of eight workstream sections contained an identical risk paragraph (copy-paste boilerplate)
6. The design document revived the "split-agent handoff" pattern that was explicitly retired in 0.1.4

These failures were diagnosed in the iao 0.1.6 forensic audit. The 0.1.5 drafts are preserved at this path as diagnostic corpus and referenced directly in the 0.1.7 design document Appendix A.

## What was done instead

iao 0.1.6 ran as a forensic audit (eleven precursor reports) rather than a standard iteration. The audit findings drove the 0.1.7 scope.

iao 0.1.7 executes the repairs informed by the 0.1.5 failure modes. Streaming, repetition detection, word count inversion, anti-hallucination evaluator, rich seed, RAG freshness weighting, two-pass generation, component checklist, OpenClaw Ollama-native rebuild.

## Files preserved

- `iao-design-0.1.5.md` (34.7 KB / 5132 words, Qwen-generated, degenerate)
- `iao-plan-0.1.5.md` (26.0 KB / 3273 words, Qwen-generated, degenerate)

Both files are immutable historical record. Do not regenerate, do not edit, do not delete.

— iao 0.1.7 W0, 2026-04-09
' > docs/iterations/0.1.5/INCOMPLETE.md

test -f docs/iterations/0.1.5/INCOMPLETE.md
# Expected: passes
```

#### W0.6 — Verify 0.1.7 directory has the canonical inputs

```fish
command ls docs/iterations/0.1.7/
# Expected: iao-design-0.1.7.md, iao-plan-0.1.7.md
# (These were dropped in by Kyle before launch per Launch Protocol)

test -f docs/iterations/0.1.7/iao-design-0.1.7.md
test -f docs/iterations/0.1.7/iao-plan-0.1.7.md
# Expected: both pass

wc -c docs/iterations/0.1.7/iao-design-0.1.7.md
# Expected: roughly 70-80 KB
```

#### W0.7 — Initialize build log

```fish
printf '# Build Log — iao 0.1.7

**Start:** %s
**Executor:** gemini-cli
**Machine:** NZXTcos
**Phase:** 0
**Iteration:** 0.1.7
**Theme:** Let Qwen Cook — repair the artifact loop

---

## W0 — Environment Hygiene

**Status:** COMPLETE
**Wall clock:** ~10 min

Actions:
- W0.1: Removed ~/iao-middleware/bin from fish PATH
- W0.2: Deleted 5 stale .pyc files from src/iao/postflight/__pycache__/
- W0.3: .iao.json current_iteration → 0.1.7, last_completed_iteration → 0.1.4
- W0.4: VERSION, pyproject.toml, cli.py updated to 0.1.7
- W0.5: docs/iterations/0.1.5/INCOMPLETE.md created
- W0.6: Verified design and plan present in docs/iterations/0.1.7/
- W0.7: This build log initialized

Discrepancies: none

---

' (date -u +%Y-%m-%dT%H:%M:%SZ) > docs/iterations/0.1.7/iao-build-log-0.1.7.md
```

#### W0.8 — Mark W0 complete in checkpoint

```fish
jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W0.status = "complete" | .workstreams.W0.completed_at = $ts | .current_workstream = "W1"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

**Acceptance:**
- `./bin/iao --version` returns `iao 0.1.7`
- `jq .current_iteration .iao.json` returns `"0.1.7"`
- `test -f docs/iterations/0.1.5/INCOMPLETE.md` passes
- `grep -rEn "0\.1\.7\.[0-9]+" src/ prompts/ 2>/dev/null` returns zero matches

---

### W1 — Stream + Heartbeat + Repetition Detection

**Executor:** Gemini CLI
**Wall clock target:** 90 min

#### W1.1 — Streaming QwenClient

Read current implementation:

```fish
cat src/iao/artifacts/qwen_client.py
```

Replace the contents with the streaming implementation:

```fish
cat > src/iao/artifacts/qwen_client.py <<'PYEOF'
"""Streaming Qwen client with heartbeat and repetition detection.

iao 0.1.7 W1: replaced the non-streaming blocking implementation
with token-by-token streaming, 30-second elapsed-time heartbeats,
and a rolling-window repetition detector that kills degenerate
generation loops within seconds instead of minutes.
"""
import json
import sys
import time
from typing import Optional

import requests

from iao.artifacts.repetition_detector import RepetitionDetector, DegenerateGenerationError


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_TIMEOUT = 600  # was 1800 in 0.1.4, reduced after 0.1.6 audit
DEFAULT_NUM_CTX = 16384  # was 8192 in 0.1.4, bumped for long-form generation
HEARTBEAT_INTERVAL_S = 30


class QwenClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        num_ctx: int = DEFAULT_NUM_CTX,
        temperature: float = 0.2,
        verbose: bool = True,
    ):
        self.model = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.verbose = verbose

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response via streaming with heartbeat and repetition detection.

        Returns the complete response as a string. Raises DegenerateGenerationError
        if repetition detector fires. Raises requests.Timeout if the whole generation
        exceeds self.timeout.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": self.temperature,
            },
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        accumulated = []
        detector = RepetitionDetector(window_size=200, similarity_threshold=0.70)
        start = time.monotonic()
        last_heartbeat = start
        token_count = 0
        check_interval = 50  # check repetition every N tokens

        if self.verbose:
            print(f"[qwen] starting generation (model={self.model}, timeout={self.timeout}s)", file=sys.stderr, flush=True)

        try:
            with requests.post(OLLAMA_URL, json=payload, timeout=self.timeout, stream=True) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = chunk.get("response", "")
                    if token:
                        accumulated.append(token)
                        token_count += 1

                        # Stream token to stderr if verbose
                        if self.verbose:
                            sys.stderr.write(token)
                            sys.stderr.flush()

                        # Heartbeat check
                        now = time.monotonic()
                        if now - last_heartbeat >= HEARTBEAT_INTERVAL_S:
                            elapsed = int(now - start)
                            words = len("".join(accumulated).split())
                            if self.verbose:
                                print(
                                    f"\n[qwen] heartbeat: {elapsed}s elapsed, {token_count} tokens, {words} words so far",
                                    file=sys.stderr,
                                    flush=True,
                                )
                            last_heartbeat = now

                        # Repetition check every N tokens
                        if token_count % check_interval == 0:
                            detector.add_tokens(accumulated[-check_interval:])
                            if detector.check():
                                raise DegenerateGenerationError(
                                    f"Repetition detected at token {token_count}, {int(time.monotonic() - start)}s elapsed",
                                    sample=detector.get_sample(),
                                    total_tokens=token_count,
                                )

                    if chunk.get("done"):
                        break

        except requests.Timeout:
            elapsed = int(time.monotonic() - start)
            if self.verbose:
                print(f"\n[qwen] TIMEOUT after {elapsed}s, {token_count} tokens generated", file=sys.stderr)
            raise

        elapsed = int(time.monotonic() - start)
        full_text = "".join(accumulated)
        word_count = len(full_text.split())

        if self.verbose:
            print(
                f"\n[qwen] done: {elapsed}s elapsed, {token_count} tokens, {word_count} words",
                file=sys.stderr,
                flush=True,
            )

        return full_text
PYEOF
```

#### W1.2 — Repetition detector module

```fish
cat > src/iao/artifacts/repetition_detector.py <<'PYEOF'
"""Rolling-window repetition detector for LLM generation.

Addresses the 0.1.5 failure mode where Qwen entered a repetition loop
in the plan document's footer and generated the same 12-line block
fifteen-plus times before truncation. See iao 0.1.7 design Appendix A.
"""
from difflib import SequenceMatcher
from typing import Optional


class DegenerateGenerationError(Exception):
    """Raised when a generation appears to be in a repetition loop."""

    def __init__(self, message: str, sample: Optional[str] = None, total_tokens: int = 0):
        super().__init__(message)
        self.sample = sample
        self.total_tokens = total_tokens


class RepetitionDetector:
    """Detects degenerate repetition in streaming LLM output.

    Uses a rolling window: compares the last `window_size` tokens against
    the preceding `window_size` tokens using character-level sequence
    similarity. If the ratio exceeds `similarity_threshold`, the generation
    is considered degenerate.

    Usage:
        detector = RepetitionDetector(window_size=200, similarity_threshold=0.70)
        for token in stream:
            detector.add_tokens([token])
            if detector.check():
                raise DegenerateGenerationError(...)
    """

    def __init__(self, window_size: int = 200, similarity_threshold: float = 0.70):
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self._buffer: list[str] = []

    def add_tokens(self, tokens: list[str]) -> None:
        self._buffer.extend(tokens)
        # Keep only the last 2 * window_size tokens in memory
        max_keep = self.window_size * 2 + 50
        if len(self._buffer) > max_keep:
            self._buffer = self._buffer[-max_keep:]

    def check(self) -> bool:
        """Return True if the generation appears degenerate."""
        if len(self._buffer) < 2 * self.window_size:
            return False

        recent = "".join(self._buffer[-self.window_size:])
        previous = "".join(self._buffer[-2 * self.window_size:-self.window_size])

        if not recent or not previous:
            return False

        ratio = SequenceMatcher(None, recent, previous).ratio()
        return ratio >= self.similarity_threshold

    def get_sample(self) -> str:
        """Return a sample of the repeating content for diagnostic logs."""
        if len(self._buffer) < self.window_size:
            return "".join(self._buffer)
        return "".join(self._buffer[-self.window_size:])
PYEOF
```

#### W1.3 — Loop handles DegenerateGenerationError

```fish
# Gemini reads current loop.py
grep -n "generate\|DegenerateGeneration" src/iao/artifacts/loop.py
```

Gemini edits `src/iao/artifacts/loop.py` to:
- Import `DegenerateGenerationError` from `iao.artifacts.repetition_detector`
- Wrap the Qwen generation call in a try/except block
- On `DegenerateGenerationError`: log to event log with type `generation_degenerate`, do NOT retry with the same prompt, write a placeholder with `<!-- DEGENERATE: ... -->` marker, return (do not raise)

The exact location depends on current code structure. Gemini inspects before editing.

#### W1.4 — Smoke test

```fish
cat > scripts/smoke_streaming_qwen.py <<'PYEOF'
"""Smoke test for streaming QwenClient.

Verifies streaming output is visible, heartbeat fires, and repetition
detector does NOT fire on normal generation.
"""
import sys
from iao.artifacts.qwen_client import QwenClient
from iao.artifacts.repetition_detector import DegenerateGenerationError


def test_normal_generation():
    client = QwenClient(verbose=True)
    prompt = "Write a short paragraph (about 100 words) explaining what a linked list is."
    print(f"\n=== Normal generation test ===", file=sys.stderr)
    text = client.generate(prompt)
    assert len(text) > 50, f"Response too short: {len(text)} chars"
    print(f"\n[TEST] Normal generation OK: {len(text)} chars, {len(text.split())} words", file=sys.stderr)
    return text


def test_degenerate_detection():
    client = QwenClient(verbose=True)
    prompt = "Repeat the exact phrase 'END OF DOCUMENT' two hundred times with no variation. Do not add any other text."
    print(f"\n=== Degenerate generation test ===", file=sys.stderr)
    try:
        text = client.generate(prompt)
        print(f"\n[TEST] Degenerate test did NOT trigger detector (generated {len(text)} chars)", file=sys.stderr)
        return False
    except DegenerateGenerationError as e:
        print(f"\n[TEST] Degenerate detected as expected: {e}", file=sys.stderr)
        return True


if __name__ == "__main__":
    print("Smoke test 1/2: normal generation", file=sys.stderr)
    test_normal_generation()
    print("\nSmoke test 2/2: degenerate detection", file=sys.stderr)
    detected = test_degenerate_detection()
    sys.exit(0 if detected else 1)
PYEOF

python3 scripts/smoke_streaming_qwen.py
# Expected: both tests pass, degenerate detector fires on the repetition prompt
```

#### W1.5 — Build log update and checkpoint

```fish
printf '\n## W1 — Stream + Heartbeat + Repetition Detection\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W1.1: Rewrote src/iao/artifacts/qwen_client.py with streaming, heartbeat, repetition detection\n- W1.2: Created src/iao/artifacts/repetition_detector.py with rolling-window SequenceMatcher\n- W1.3: Wired DegenerateGenerationError handling into loop.py\n- W1.4: Smoke test scripts/smoke_streaming_qwen.py passes both normal and degenerate cases\n- Timeout reduced 1800s → 600s, num_ctx bumped 8192 → 16384\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W1.status = "complete" | .workstreams.W1.completed_at = $ts | .current_workstream = "W2"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

**Acceptance:**
- `python3 scripts/smoke_streaming_qwen.py` exits 0 with both tests visible
- `grep -n "DegenerateGenerationError" src/iao/artifacts/loop.py` shows the handler wired in
- `grep -n "stream.*True" src/iao/artifacts/qwen_client.py` confirms streaming enabled
- Existing `pytest tests/` still passes

---

### W2 — Word Count Inversion + Structural Gates

**Executor:** Gemini CLI
**Wall clock target:** 60 min

#### W2.1 — Invert schemas.py thresholds

```fish
cat src/iao/artifacts/schemas.py
# Inspect current structure
```

Gemini edits `schemas.py` to replace `min_words` with `max_words` for Qwen-generated artifacts, and adds `required_sections`:

```python
# New structure for each artifact:
SCHEMAS = {
    "design": {
        "max_words": 3000,  # was min_words: 5000
        "required_sections": [
            "What is iao",
            "§1",
            "§2",
            "§3",
            "§4",
            "§5",
            "§6",
            "§7",
            "§8",
            "§9",
            "§10",
        ],
        "required_terms": ["iteration", "workstream"],
    },
    "plan": {
        "max_words": 2500,  # was min_words: 3000
        "required_sections": [
            "What is iao",
            "Section A",
            "Section B",
            "Section C",
            "Section D",
            "Section E",
        ],
        "required_terms": ["workstream", "executor"],
    },
    "build-log": {
        "max_words": 1500,  # was min 1500 — explicit max now
        "required_sections": ["# Build Log", "## W0"],
        "required_terms": ["Start:"],
    },
    "report": {
        "max_words": 1000,  # was min 1200
        "required_sections": ["# Report", "## Summary", "## Workstream Scores"],
        "required_terms": ["status"],
    },
    "run-report": {
        "min_bytes": 1500,  # run report is structural, stays as minimum
        "required_sections": ["## Workstream Summary", "## Sign-off"],
    },
    "bundle": {
        "required_sections": 22,  # sections, not a single list
    },
}
```

Smoke test:

```fish
python3 -c "
from iao.artifacts.schemas import SCHEMAS
print(f'design max_words: {SCHEMAS[\"design\"][\"max_words\"]}')
print(f'plan max_words: {SCHEMAS[\"plan\"][\"max_words\"]}')
print(f'design required_sections: {len(SCHEMAS[\"design\"][\"required_sections\"])}')
"
# Expected: design 3000, plan 2500, 11 required sections for design
```

#### W2.2 — Update loop.py validation

Gemini reads `src/iao/artifacts/loop.py` and updates the post-generation validation logic:

- Remove the min-words retry loop
- Add a max-words warning log (not a retry)
- Add required_sections check: grep the generated text for each required section header; if missing, retry ONCE with a corrective prompt that lists the missing sections

#### W2.3 — Structural gate post-flight check

```fish
cat > src/iao/postflight/structural_gates.py <<'PYEOF'
"""Structural gate post-flight check.

Validates that generated artifacts contain all required section headers.
Added in iao 0.1.7 W2 after the 0.1.5 drafts showed that Qwen can produce
plausible-looking but structurally incomplete artifacts.
"""
import json
import re
from pathlib import Path

from iao.artifacts.schemas import SCHEMAS


def check_artifact(path: Path, artifact_type: str) -> dict:
    if not path.exists():
        return {"status": "DEFERRED", "message": f"Artifact not found: {path}", "errors": []}

    schema = SCHEMAS.get(artifact_type, {})
    required = schema.get("required_sections", [])
    if not required:
        return {"status": "PASS", "message": "No required sections defined", "errors": []}

    content = path.read_text()
    errors = []
    for section in required:
        # Handle both exact matches and pattern matches
        if section.startswith("§"):
            # Section header like "§1" must appear as "## §1" or similar
            if f"§{section[1:]}" not in content:
                errors.append(f"Missing section: {section}")
        elif section.startswith("#"):
            # Exact header match
            if section not in content:
                errors.append(f"Missing header: {section}")
        else:
            # Substring match in header
            if section not in content:
                errors.append(f"Missing section reference: {section}")

    if errors:
        return {"status": "FAIL", "message": f"{len(errors)} structural failures", "errors": errors}
    return {"status": "PASS", "message": f"All {len(required)} required sections present", "errors": []}


def check(version: str = None) -> dict:
    """Entry point for post-flight runner."""
    if version is None:
        with open(".iao.json") as f:
            version = json.load(f).get("current_iteration", "")

    iter_dir = Path(f"docs/iterations/{version}")
    results = {}

    for artifact_type, filename_pattern in [
        ("design", f"iao-design-{version}.md"),
        ("plan", f"iao-plan-{version}.md"),
        ("build-log", f"iao-build-log-{version}.md"),
        ("report", f"iao-report-{version}.md"),
    ]:
        path = iter_dir / filename_pattern
        results[artifact_type] = check_artifact(path, artifact_type)

    all_pass = all(r["status"] == "PASS" for r in results.values() if r["status"] != "DEFERRED")
    all_errors = []
    for at, r in results.items():
        for e in r.get("errors", []):
            all_errors.append(f"{at}: {e}")

    return {
        "status": "PASS" if all_pass else "FAIL",
        "message": f"Structural gates: {sum(1 for r in results.values() if r['status'] == 'PASS')} pass, {sum(1 for r in results.values() if r['status'] == 'FAIL')} fail, {sum(1 for r in results.values() if r['status'] == 'DEFERRED')} deferred",
        "errors": all_errors,
        "per_artifact": results,
    }
PYEOF

python3 -c "
from iao.postflight.structural_gates import check_artifact
from pathlib import Path
# Run against the 0.1.4 design (should pass)
r = check_artifact(Path('docs/iterations/0.1.4/iao-design-0.1.4.md'), 'design')
print(f'0.1.4 design: {r[\"status\"]}')
# Run against the 0.1.5 design (should fail or pass depending on exact header format)
r = check_artifact(Path('docs/iterations/0.1.5/iao-design-0.1.5.md'), 'design')
print(f'0.1.5 design: {r[\"status\"]}')
"
```

#### W2.4 — Update prompt templates

Gemini edits `prompts/design.md.j2`, `prompts/plan.md.j2`, `prompts/build-log.md.j2`, `prompts/report.md.j2` to:
- List required sections explicitly
- Include "Target length: X-Y words, DO NOT PAD IF YOU RUN OUT OF CONTENT. Stop when you have nothing more substantive to say."
- Reference the `{{ seed }}` context (will be populated in W4)

Example for `prompts/design.md.j2`:

```fish
# Read current template
cat prompts/design.md.j2
# Gemini edits to add the new instructions
```

#### W2.5 — Build log and checkpoint

```fish
printf '\n## W2 — Word Count Inversion + Structural Gates\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W2.1: schemas.py rewritten — max_words instead of min_words, required_sections added\n- W2.2: loop.py validation updated — no min-words retry, max warning, required_sections check\n- W2.3: src/iao/postflight/structural_gates.py created\n- W2.4: Prompt templates updated with required sections list and no-padding instruction\n- Validated against 0.1.4 design (passes) and 0.1.5 design (known failure)\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W2.status = "complete" | .workstreams.W2.completed_at = $ts | .current_workstream = "W3"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W3 — Anti-Hallucination Evaluator

**Executor:** Gemini CLI
**Wall clock target:** 75 min

#### W3.1 — Evaluator module

```fish
cat > src/iao/artifacts/evaluator.py <<'PYEOF'
"""Anti-hallucination evaluator for Qwen-generated artifacts.

Uses Nemotron for reference extraction and grep-validates every reference
against the actual codebase. Catches the 0.1.5 failure modes: hallucinated
file paths, hallucinated CLI commands, fabricated phase labels, revived
retired patterns. See iao 0.1.7 design Appendix A §A.2, §A.3, §A.6, §A.7.
"""
import json
import re
from pathlib import Path
from typing import Any

from iao.artifacts.nemotron_client import _call as nemotron_call


FILE_PATH_RE = re.compile(r"(?:^|\s|`)((?:src|scripts|docs|data|tests)/[\w/\.\-]+\.\w+)")
CLI_COMMAND_RE = re.compile(r"`?(?:iao|\./bin/iao)\s+([\w\-]+)(?:\s+[\w\-]+)?`?")
SCRIPT_NAME_RE = re.compile(r"`?(\w+\.py)`?")
ADR_ID_RE = re.compile(r"(iaomw-ADR-\d+)")
PILLAR_ID_RE = re.compile(r"(iaomw-Pillar-\d+)")
GOTCHA_ID_RE = re.compile(r"(iaomw-G\d+)")
PHASE_LABEL_RE = re.compile(r"Phase\s*:?\s*(\d+)(?:\s*\(([^)]+)\))?", re.IGNORECASE)


def extract_references(text: str) -> dict:
    """Extract references via regex. Nemotron used only for ambiguous cases."""
    return {
        "file_paths": sorted(set(FILE_PATH_RE.findall(text))),
        "cli_commands": sorted(set(CLI_COMMAND_RE.findall(text))),
        "script_names": sorted(set(SCRIPT_NAME_RE.findall(text))),
        "adr_ids": sorted(set(ADR_ID_RE.findall(text))),
        "pillar_ids": sorted(set(PILLAR_ID_RE.findall(text))),
        "gotcha_ids": sorted(set(GOTCHA_ID_RE.findall(text))),
        "phase_labels": [(p, lbl or "") for p, lbl in PHASE_LABEL_RE.findall(text)],
    }


def load_known_hallucinations() -> dict:
    p = Path("data/known_hallucinations.json")
    if not p.exists():
        return {"retired_patterns": [], "kjtcom_references_that_look_like_iao": [], "fabricated_history": []}
    return json.loads(p.read_text())


def validate_references(refs: dict, project_root: Path, seed: dict = None) -> dict:
    errors = []
    known = load_known_hallucinations()
    seed = seed or {}

    # File paths
    for fp in refs.get("file_paths", []):
        if not (project_root / fp).exists():
            errors.append(f"hallucinated file path: {fp}")

    # CLI commands
    cli_path = project_root / "src" / "iao" / "cli.py"
    if cli_path.exists():
        cli_content = cli_path.read_text()
        for cmd in refs.get("cli_commands", []):
            if cmd not in cli_content:
                errors.append(f"hallucinated CLI command: iao {cmd}")

    # ADR ids
    base_md = project_root / "docs" / "harness" / "base.md"
    if base_md.exists():
        base_content = base_md.read_text()
        for adr in refs.get("adr_ids", []):
            if adr not in base_content:
                errors.append(f"hallucinated ADR: {adr}")

    # Pillar ids (1-10 valid)
    for pillar in refs.get("pillar_ids", []):
        num_match = re.search(r"(\d+)", pillar)
        if num_match:
            num = int(num_match.group(1))
            if num < 1 or num > 10:
                errors.append(f"hallucinated pillar: {pillar}")

    # Gotcha ids
    gotcha_path = project_root / "data" / "gotcha_archive.json"
    if gotcha_path.exists():
        try:
            gdata = json.loads(gotcha_path.read_text())
            # REMEMBER: dict with "gotchas" key, not a list
            gotchas = gdata.get("gotchas", []) if isinstance(gdata, dict) else gdata
            known_ids = {g.get("id") for g in gotchas}
            for gid in refs.get("gotcha_ids", []):
                if gid not in known_ids:
                    errors.append(f"hallucinated gotcha: {gid}")
        except json.JSONDecodeError:
            pass

    # Phase labels: must match .iao.json phase
    iao_json = project_root / ".iao.json"
    if iao_json.exists():
        try:
            current_phase = json.loads(iao_json.read_text()).get("phase", 0)
            for phase_num, phase_label in refs.get("phase_labels", []):
                if int(phase_num) != current_phase:
                    errors.append(f"phase mismatch: text says Phase {phase_num}{' (' + phase_label + ')' if phase_label else ''}, .iao.json says Phase {current_phase}")
        except (json.JSONDecodeError, ValueError):
            pass

    # Known hallucinations from seed's anti_hallucination_list
    anti = seed.get("anti_hallucination_list", [])
    # Also check the global known_hallucinations file
    for bad_phrase in anti + known.get("retired_patterns", []) + known.get("kjtcom_references_that_look_like_iao", []):
        # Rebuild the original text isn't practical here — caller should pass full text
        pass

    # Severity
    if not errors:
        return {"severity": "clean", "errors": [], "message": "No hallucinations detected"}
    elif len(errors) <= 3:
        return {"severity": "warn", "errors": errors, "message": f"{len(errors)} minor hallucinations"}
    else:
        return {"severity": "reject", "errors": errors, "message": f"{len(errors)} hallucinations — artifact rejected"}


def evaluate_text(text: str, project_root: Path = None, seed: dict = None) -> dict:
    """Full evaluation: extract references, validate, return severity."""
    if project_root is None:
        project_root = Path.cwd()
    refs = extract_references(text)

    # Also check anti_hallucination_list phrases directly against text
    anti_errors = []
    known = load_known_hallucinations()
    anti = (seed or {}).get("anti_hallucination_list", [])
    all_bad = anti + known.get("retired_patterns", []) + known.get("kjtcom_references_that_look_like_iao", [])
    for bad_phrase in all_bad:
        if bad_phrase.lower() in text.lower():
            anti_errors.append(f"retired/anti pattern present: '{bad_phrase}'")

    validation = validate_references(refs, project_root, seed)
    validation["errors"] = anti_errors + validation.get("errors", [])
    # Re-assess severity
    n = len(validation["errors"])
    if n == 0:
        validation["severity"] = "clean"
    elif n <= 3:
        validation["severity"] = "warn"
    else:
        validation["severity"] = "reject"
    validation["message"] = f"{n} issues found, severity: {validation['severity']}"
    validation["references"] = refs
    return validation
PYEOF
```

#### W3.2 — Known hallucinations baseline

```fish
mkdir -p data
cat > data/known_hallucinations.json <<'JSONEOF'
{
  "retired_patterns": [
    "split-agent handoff",
    "split-agent",
    "Gemini executes W1 through W5",
    "Workstreams W1 through W5 are executed by Gemini",
    "Workstreams W6 and W7 are executed by Claude",
    "Phase 1 (Production Readiness)",
    "Phase: 1 (Production Readiness)"
  ],
  "kjtcom_references_that_look_like_iao": [
    "query_registry.py",
    "query_rag.py",
    "the query_registry.py script"
  ],
  "fabricated_history": [
    "0.1.1 (2026-04-05)",
    "Introduced run_report Bug",
    "Introduced Versioning Bug",
    "Introduced Legacy Harness"
  ]
}
JSONEOF
```

#### W3.3 — Wire evaluator into loop.py

Gemini edits `src/iao/artifacts/loop.py` to:
- After Qwen generates an artifact, call `evaluate_text(generated_text, project_root=Path.cwd(), seed=seed)`
- If `severity == "reject"`, retry ONCE with a corrective prompt that lists the hallucinated phrases
- Max 1 retry per artifact (total 2 generations max)
- Log result to event log with type `evaluator_result`

#### W3.4 — Test harness

```fish
cat > tests/test_evaluator.py <<'PYEOF'
"""Test anti-hallucination evaluator against known-bad and known-good corpora."""
from pathlib import Path
import pytest

from iao.artifacts.evaluator import evaluate_text, extract_references


PROJECT_ROOT = Path(__file__).parent.parent


def test_extract_references_finds_file_paths():
    text = "See src/iao/cli.py and scripts/smoke.py for details."
    refs = extract_references(text)
    assert "src/iao/cli.py" in refs["file_paths"]
    assert "smoke.py" in refs["script_names"]


def test_extract_references_finds_pillars():
    text = "Per iaomw-Pillar-1 (Trident) and iaomw-Pillar-7 we retry up to 3 times."
    refs = extract_references(text)
    assert "iaomw-Pillar-1" in refs["pillar_ids"]
    assert "iaomw-Pillar-7" in refs["pillar_ids"]


def test_evaluate_clean_0_1_4_design():
    path = PROJECT_ROOT / "docs" / "iterations" / "0.1.4" / "iao-design-0.1.4.md"
    if not path.exists():
        pytest.skip("0.1.4 design not present")
    text = path.read_text()
    result = evaluate_text(text, project_root=PROJECT_ROOT)
    # 0.1.4 may have some warnings but should not be reject-level
    assert result["severity"] in ("clean", "warn"), f"Expected clean or warn, got {result['severity']}: {result['errors'][:5]}"


def test_evaluate_rejects_0_1_5_design_hallucinations():
    path = PROJECT_ROOT / "docs" / "iterations" / "0.1.5" / "iao-design-0.1.5.md"
    if not path.exists():
        pytest.skip("0.1.5 design not present")
    text = path.read_text()
    result = evaluate_text(text, project_root=PROJECT_ROOT)
    # 0.1.5 should have multiple hallucinations
    assert result["severity"] in ("reject", "warn"), f"Expected reject or warn, got {result['severity']}"
    # Specifically should flag query_registry.py
    error_text = " ".join(result["errors"])
    assert "query_registry" in error_text or len(result["errors"]) >= 3, f"Expected query_registry.py flag or multiple errors, got: {result['errors']}"
PYEOF

pytest tests/test_evaluator.py -v
# Expected: 4 tests pass (or skip gracefully if 0.1.4/0.1.5 files don't exist)
```

#### W3.5 — Build log and checkpoint

```fish
printf '\n## W3 — Anti-Hallucination Evaluator\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W3.1: Created src/iao/artifacts/evaluator.py with extract_references, validate_references, evaluate_text\n- W3.2: Created data/known_hallucinations.json baseline from 0.1.5 diagnostic corpus\n- W3.3: Wired evaluator into loop.py — 1 retry with corrective prompt on reject\n- W3.4: Created tests/test_evaluator.py — passes against 0.1.4 (clean) and 0.1.5 (reject)\n- Evaluator catches query_registry.py, split-agent, Phase 1, infinite file list hallucinations\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W3.status = "complete" | .workstreams.W3.completed_at = $ts | .current_workstream = "W4"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W4 — Rich Structured Seed

**Executor:** Gemini CLI
**Wall clock target:** 60 min

#### W4.1 — Updated seed module

```fish
# Inspect current seed.py
cat src/iao/feedback/seed.py 2>/dev/null
```

Gemini rewrites `src/iao/feedback/seed.py` to produce the structured JSON per design §6 W4.1. Key functions:

- `extract_carryover_debts(previous_run_report_path)` — parses workstream summary table, returns list of debts
- `build_seed(source_iteration, target_iteration)` — assembles the full structured seed
- `write_seed(target_iteration, seed)` — writes to `docs/iterations/{target}/seed.json`

#### W4.2 — `iao iteration seed --edit` CLI flag

Gemini edits `src/iao/cli.py` to add `--edit` flag to the `iteration seed` subcommand. Flag behavior:
- Writes seed JSON to a temp file
- Launches `$EDITOR` (fallback: `kate`, `vim`, `nano`)
- Waits for editor exit
- Validates JSON well-formed
- Writes back to `docs/iterations/{target}/seed.json`

#### W4.3 — Seed consumed as system prompt

Gemini edits `src/iao/artifacts/loop.py` to:
- Before each Qwen generation, load `docs/iterations/{version}/seed.json` if present
- Convert to a markdown "Ground Truth" section
- Prepend to the system prompt passed to QwenClient

#### W4.4 — Write 0.1.7's own seed (dogfood prep)

```fish
./bin/iao iteration seed
# Should produce a structured seed for 0.1.7 based on 0.1.4 run report
```

Then manually populate key fields via `--edit` or direct JSON write:

```fish
python3 <<'PYEOF'
import json
from pathlib import Path

seed = {
    "source_iteration": "0.1.4",
    "target_iteration": "0.1.7",
    "phase": 0,
    "iteration_theme": "Let Qwen Cook — repair the artifact loop supporting Qwen",
    "kyles_notes": "From 0.1.4 run report: component checklist per run, deploy openclaw/nemoclaw (claw3d is kjtcom).",
    "agent_questions": [],
    "carryover_debts": [
        {"source": "0.1.4 W5", "description": "OpenClaw/NemoClaw non-functional stubs (NotImplementedError)", "severity": "blocking"},
        {"source": "0.1.4 W3", "description": "Ambiguous pile pause mechanism never fired; 8 kjtcom gotchas migrated without classification", "severity": "partial-doc"},
        {"source": "0.1.5", "description": "Artifact loop produces degenerate output — see INCOMPLETE.md", "severity": "blocking"}
    ],
    "scope_hints": "10 workstreams W0-W9. W1-W5 repair Qwen loop (streaming, structural gates, evaluator, rich seed, RAG recency). W6 experimental two-pass behind flag. W7 component checklist BUNDLE_SPEC §22. W8 OpenClaw Ollama-native rebuild bypassing open-interpreter/tiktoken. W9 dogfood.",
    "anti_hallucination_list": [
        "query_registry.py",
        "split-agent handoff",
        "Gemini executes W1 through W5, Claude executes W6 and W7",
        "Phase 1 (Production Readiness)",
        "src/iao/harness/",
        "src/iao/chain/",
        "src/iao/llm/",
        "src/iao/vector/"
    ],
    "retired_patterns": [
        "split-agent handoff (retired in 0.1.4)"
    ],
    "known_file_paths": [
        "src/iao/cli.py",
        "src/iao/artifacts/loop.py",
        "src/iao/artifacts/qwen_client.py",
        "src/iao/artifacts/nemotron_client.py",
        "src/iao/artifacts/glm_client.py",
        "src/iao/artifacts/evaluator.py",
        "src/iao/artifacts/repetition_detector.py",
        "src/iao/rag/archive.py",
        "src/iao/feedback/run_report.py",
        "src/iao/feedback/seed.py",
        "src/iao/postflight/structural_gates.py",
        "src/iao/bundle.py",
        "src/iao/agents/openclaw.py",
        "src/iao/agents/nemoclaw.py"
    ],
    "known_cli_commands": [
        "iao iteration design",
        "iao iteration plan",
        "iao iteration build-log",
        "iao iteration report",
        "iao iteration close",
        "iao iteration seed",
        "iao doctor quick",
        "iao doctor preflight",
        "iao doctor postflight",
        "iao registry query",
        "iao rag query",
        "iao secret list"
    ]
}

Path("docs/iterations/0.1.7/seed.json").write_text(json.dumps(seed, indent=2))
print(f"Seed written: {len(seed)} fields")
PYEOF
```

#### W4.5 — Build log and checkpoint

```fish
printf '\n## W4 — Rich Structured Seed\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W4.1: Rewrote src/iao/feedback/seed.py to produce structured JSON\n- W4.2: Added --edit flag to iao iteration seed CLI\n- W4.3: Wired seed loading into loop.py as Ground Truth section in system prompt\n- W4.4: Wrote docs/iterations/0.1.7/seed.json with full carryover debts and anti_hallucination_list\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W4.status = "complete" | .workstreams.W4.completed_at = $ts | .current_workstream = "W5"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W5 — RAG Freshness Weighting

**Executor:** Gemini CLI
**Wall clock target:** 45 min

#### W5.1 — Verify iteration metadata present

```fish
python3 -c "
from iao.rag.archive import _get_client
c = _get_client()
for name in ['iaomw_archive', 'kjtco_archive', 'tripl_archive']:
    try:
        col = c.get_collection(name)
        sample = col.get(limit=3, include=['metadatas'])
        metas = sample.get('metadatas', [])
        has_iter = all('iteration' in m for m in metas)
        print(f'{name}: {col.count()} docs, has iteration metadata: {has_iter}')
        if metas:
            print(f'  sample metadata: {metas[0]}')
    except Exception as e:
        print(f'{name}: ERROR {e}')
"
```

If any archive is missing iteration metadata, re-seed it (the archive.py module handles this).

#### W5.2 — Freshness-weighted query

Gemini edits `src/iao/rag/archive.py` to add `prefer_recent` parameter:

```python
def query_archive(project_code: str, query: str, top_k: int = 5, prefer_recent: bool = True) -> list[dict]:
    """Query with optional recency weighting.

    When prefer_recent=True, retrieves top_k*3 candidates then re-ranks by
    blending semantic similarity with iteration recency.
    """
    client = _get_client()
    collection_name = f"{project_code}_archive"
    try:
        collection = client.get_collection(collection_name, embedding_function=_get_embedder())
    except Exception:
        return []

    pool_size = top_k * 3 if prefer_recent else top_k
    results = collection.query(query_texts=[query], n_results=pool_size)

    items = []
    for i, d, m, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        similarity = max(0.0, 1.0 - dist)  # distance → similarity
        iteration = m.get("iteration", "0.0.0")
        recency = _recency_score(iteration)
        final = 0.6 * similarity + 0.4 * recency if prefer_recent else similarity
        items.append({"id": i, "document": d, "metadata": m, "similarity": similarity, "recency": recency, "score": final})

    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:top_k]


_RECENCY_MAP = {
    "0.1.4": 1.00,
    "0.1.3": 0.85,
    "0.1.2": 0.70,
    "0.1.0": 0.50,
}


def _recency_score(iteration: str) -> float:
    return _RECENCY_MAP.get(iteration, 0.30)
```

#### W5.3 — Context module uses recency

Gemini edits `src/iao/artifacts/context.py` `build_context_for_artifact()` to call `query_archive(..., prefer_recent=True)` by default.

#### W5.4 — Smoke test

```fish
cat > scripts/test_rag_recency.py <<'PYEOF'
"""Verify RAG recency weighting promotes 0.1.4 content over 0.1.2 content."""
from iao.rag.archive import query_archive

query = "artifact loop workstream structure"

print("=== Without recency preference ===")
results = query_archive("iaomw", query, top_k=5, prefer_recent=False)
for r in results:
    print(f"  {r['metadata'].get('iteration', '?')} / {r['metadata'].get('filename', '?')}")

print("\n=== With recency preference ===")
results = query_archive("iaomw", query, top_k=5, prefer_recent=True)
for r in results:
    print(f"  {r['metadata'].get('iteration', '?')} / {r['metadata'].get('filename', '?')}  (sim={r['similarity']:.2f} rec={r['recency']:.2f} score={r['score']:.2f})")
PYEOF

python3 scripts/test_rag_recency.py
# Expected: recency-preferred list shows 0.1.4 content higher than 0.1.2 content
```

#### W5.5 — Build log and checkpoint

```fish
printf '\n## W5 — RAG Freshness Weighting\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W5.1: Verified all 3 archives have iteration metadata\n- W5.2: Added prefer_recent parameter and _recency_score to archive.py\n- W5.3: context.py uses prefer_recent=True by default\n- W5.4: scripts/test_rag_recency.py confirms 0.1.4 content promoted over 0.1.2\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W5.status = "complete" | .workstreams.W5.completed_at = $ts | .current_workstream = "W6"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W6 — Two-Pass Generation (Experimental Flag)

**Executor:** Gemini CLI
**Wall clock target:** 90 min (partial ship acceptable)

#### W6.1 — Outline generator

Gemini creates a new function `generate_outline(artifact_type, seed, context)` in `src/iao/artifacts/loop.py`:

- Calls Qwen with `format: "json"`
- Prompt: "Produce an outline for a {artifact_type} document with JSON schema: {sections: [{id, title, summary, target_words}, ...]}"
- Returns parsed outline dict

#### W6.2 — Section generator

New function `generate_section(section, seed, context, artifact_type)`:

- Builds a tight prompt scoped to that section's title and summary
- Retrieves RAG context filtered to the section's topic
- Calls QwenClient with `max_tokens` enforcing the section's target_words × ~1.3

#### W6.3 — Assembly function

`assemble_from_sections(sections_text, artifact_type, metadata)` concatenates with proper headers.

#### W6.4 — CLI `--two-pass` flag

Gemini edits `src/iao/cli.py` to add `--two-pass` flag to `iteration design` and `iteration plan` subcommands. Single-pass stays default.

#### W6.5 — Smoke test

```fish
cat > scripts/smoke_two_pass.py <<'PYEOF'
"""Smoke test two-pass generation by producing a fake tiny design."""
from iao.artifacts.loop import generate_outline  # assuming it's exported

seed = {"iteration_theme": "smoke test", "target_iteration": "0.1.99"}
try:
    outline = generate_outline("design", seed, context="")
    print(f"Outline sections: {len(outline.get('sections', []))}")
    for s in outline.get('sections', [])[:3]:
        print(f"  {s.get('id')}: {s.get('title')}")
except NotImplementedError:
    print("Two-pass is partial ship (outline only) — OK")
PYEOF

python3 scripts/smoke_two_pass.py
```

**Partial ship criterion:** If W6 is blowing past 75 min, ship only the outline generator + CLI flag, leave section generation as `NotImplementedError`. Mark W6 status `partial` in checkpoint.

```fish
printf '\n## W6 — Two-Pass Generation (Experimental)\n\n**Status:** COMPLETE (or PARTIAL)\n**Wall clock:** ~XX min\n\nActions:\n- W6.1: generate_outline function in loop.py\n- W6.2: generate_section function in loop.py\n- W6.3: assemble_from_sections function in loop.py\n- W6.4: --two-pass flag added to iao iteration design/plan\n- W6.5: Smoke test scripts/smoke_two_pass.py\n- Flag behind experimental; single-pass remains default\n\nDiscrepancies: (if partial, note what was deferred)\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W6.status = "complete" | .workstreams.W6.completed_at = $ts | .current_workstream = "W7"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W7 — Component Checklist (BUNDLE_SPEC §22)

**Executor:** Gemini CLI
**Wall clock target:** 60 min

#### W7.1 — Event log instrumentation audit

```fish
# Find all places where model calls, CLI commands, tool calls happen
grep -rn "def generate\|subprocess.run\|requests.post" src/iao/ | head -30
```

Gemini adds event log writes at each instrumented site. Event format:

```python
import json
from pathlib import Path
from datetime import datetime, timezone

def log_event(event_type: str, component: str, task: str, status: str, **kwargs):
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "iteration": kwargs.pop("iteration", None) or _current_iteration(),
        "component": component,
        "task": task,
        "status": status,
        **kwargs,
    }
    Path("data/iao_event_log.jsonl").parent.mkdir(parents=True, exist_ok=True)
    with open("data/iao_event_log.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")
```

Add this helper to `src/iao/logger.py` or equivalent and call at each instrumented site.

#### W7.2 — Components section generator

```fish
mkdir -p src/iao/bundle
touch src/iao/bundle/__init__.py 2>/dev/null || true

cat > src/iao/bundle/components_section.py <<'PYEOF'
"""Generate BUNDLE_SPEC §22 Agentic Components from event log.

Added in iao 0.1.7 W7 to address Kyle's 0.1.4 run report note about
per-run component traceability.
"""
import json
from collections import defaultdict
from pathlib import Path


def generate_components_section(iteration: str, event_log_path: Path = None) -> str:
    if event_log_path is None:
        event_log_path = Path("data/iao_event_log.jsonl")

    if not event_log_path.exists():
        return "## §22. Agentic Components\n\n*(no event log found)*\n"

    events = []
    for line in event_log_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("iteration") == iteration:
                events.append(ev)
        except json.JSONDecodeError:
            continue

    if not events:
        return f"## §22. Agentic Components\n\n*(no events recorded for iteration {iteration})*\n"

    grouped = defaultdict(list)
    for ev in events:
        grouped[ev.get("component", "unknown")].append(ev)

    lines = [
        "## §22. Agentic Components",
        "",
        f"Per-run manifest of every model, agent, CLI command, and tool invoked during iteration {iteration}.",
        "",
        "| Component | Type | Tasks | Status | Notes |",
        "|---|---|---|---|---|",
    ]

    for component, events_list in sorted(grouped.items()):
        event_types = set(ev.get("type", "") for ev in events_list)
        tasks = sorted(set(ev.get("task", "") for ev in events_list if ev.get("task")))
        statuses = [ev.get("status", "") for ev in events_list]
        status_summary = f"{statuses.count('complete')} complete / {statuses.count('failed')} failed / {len(statuses)} total"
        notes = "; ".join(sorted(set(ev.get("notes", "") for ev in events_list if ev.get("notes"))))[:200]
        lines.append(
            f"| {component} | {', '.join(event_types)} | {', '.join(tasks)[:200]} | {status_summary} | {notes} |"
        )

    lines.extend(["", f"**Total events:** {len(events)}", f"**Unique components:** {len(grouped)}", ""])
    return "\n".join(lines)
PYEOF
```

#### W7.3 — BUNDLE_SPEC expansion to 22 sections

```fish
# Read current bundle.py
grep -n "BUNDLE_SPEC\|BundleSection" src/iao/bundle.py | head -30
```

Gemini edits `src/iao/bundle.py` to:
- Append a new BundleSection(22, "Agentic Components", ...) at the end
- Import and use `generate_components_section` when assembling the bundle
- Update `validate_bundle()` to expect 22 sections

```fish
# Update bundle_quality.py to check for 22 sections
sed -i 's/len(BUNDLE_SPEC) != 21/len(BUNDLE_SPEC) != 22/' src/iao/postflight/bundle_quality.py 2>/dev/null
```

#### W7.4 — ADR amendment

```fish
printf '\n### iaomw-ADR-028 Amendment (0.1.7)\n\nBUNDLE_SPEC expanded from 21 to 22 sections. §22 "Agentic Components" auto-generated from the iao event log at iteration close. Provides per-run audit trail of every model call, agent interaction, CLI command, and tool invocation. Addresses Kyle 0.1.4 run report note #1 about component traceability.\n' >> docs/harness/base.md
```

#### W7.5 — Build log and checkpoint

```fish
printf '\n## W7 — Component Checklist (BUNDLE_SPEC §22)\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W7.1: Added log_event helper, instrumented model/CLI/tool call sites\n- W7.2: Created src/iao/bundle/components_section.py\n- W7.3: BUNDLE_SPEC expanded to 22 sections\n- W7.4: ADR-028 amendment in base.md\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W7.status = "complete" | .workstreams.W7.completed_at = $ts | .current_workstream = "W8"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W8 — OpenClaw + NemoClaw Ollama-Native Rebuild

**Executor:** Gemini CLI
**Wall clock target:** 120 min

#### W8.1 — OpenClaw rebuild

```fish
# DELETE the old stub
rm src/iao/agents/openclaw.py

cat > src/iao/agents/openclaw.py <<'PYEOF'
"""OpenClaw — Qwen/Ollama-native execution primitive.

iao 0.1.7 W8 rebuild. NO dependency on open-interpreter, tiktoken, or Rust.
Pure Python stdlib + iao's existing QwenClient.

If anyone asks you to `pip install open-interpreter`, the request is wrong.
See docs/harness/base.md iaomw-ADR-040.
"""
import json
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from iao.artifacts.qwen_client import QwenClient


class OpenClawSession:
    def __init__(
        self,
        model: str = "qwen3.5:9b",
        role: str = "assistant",
        system_prompt: Optional[str] = None,
    ):
        self.model = model
        self.role = role
        self.system_prompt = system_prompt or f"You are a helpful {role}. Be concise."
        self.client = QwenClient(model=model, verbose=False)
        self.history: list[dict] = []
        self.session_id = str(uuid.uuid4())[:8]
        self.workdir = Path(f"/tmp/openclaw-{self.session_id}")
        self.workdir.mkdir(parents=True, exist_ok=True)

    def chat(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        conversation = "\n\n".join(
            f"{turn['role'].upper()}: {turn['content']}" for turn in self.history
        )
        prompt = f"{conversation}\n\nASSISTANT:"
        response = self.client.generate(prompt, system=self.system_prompt)
        self.history.append({"role": "assistant", "content": response})
        return response

    def execute_code(self, code: str, language: str = "python", timeout: int = 30) -> dict:
        if language == "python":
            cmd = ["python3", "-c", code]
        elif language == "bash":
            cmd = ["bash", "-c", code]
        else:
            return {"stdout": "", "stderr": f"unsupported language: {language}", "exit_code": -1, "timed_out": False}

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PATH": "/usr/bin:/bin", "HOME": str(self.workdir)},
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": f"timeout after {timeout}s", "exit_code": -1, "timed_out": True}

    def close(self):
        # Clean up workdir
        try:
            import shutil
            shutil.rmtree(self.workdir, ignore_errors=True)
        except Exception:
            pass
PYEOF
```

#### W8.2 — NemoClaw rebuild

```fish
rm src/iao/agents/nemoclaw.py

cat > src/iao/agents/nemoclaw.py <<'PYEOF'
"""NemoClaw — Nemotron-driven orchestrator for OpenClaw sessions.

iao 0.1.7 W8 rebuild. Routes tasks to OpenClaw sessions by role using
Nemotron classification. Replaces the 0.1.4 stub that raised NotImplementedError.
"""
from typing import Optional

from iao.agents.openclaw import OpenClawSession
from iao.artifacts.nemotron_client import classify


DEFAULT_ROLES = ["assistant", "code_runner", "reviewer"]


class NemoClawOrchestrator:
    def __init__(self, session_count: int = 1, roles: Optional[list[str]] = None):
        if roles is None:
            roles = ["assistant"] * session_count
        else:
            roles = roles[:session_count] + ["assistant"] * max(0, session_count - len(roles))

        self.sessions = [OpenClawSession(role=r) for r in roles]
        self.roles = roles

    def dispatch(self, task: str, role: Optional[str] = None) -> str:
        if role is None:
            # Classify the task
            role = classify(task, DEFAULT_ROLES, bias="Prefer 'assistant' for general tasks. Use 'code_runner' only if the task requires executing code. Use 'reviewer' only if the task is about evaluating an artifact.")

        # Find first session with this role
        matching_session = next((s for s in self.sessions if s.role == role), self.sessions[0])
        return matching_session.chat(task)

    def collect(self) -> dict:
        return {s.role: s.history for s in self.sessions}

    def close_all(self):
        for s in self.sessions:
            s.close()
PYEOF
```

#### W8.3 — Role definitions

```fish
cat > src/iao/agents/roles/base_role.py <<'PYEOF'
"""Base role definition for OpenClaw agents."""
from dataclasses import dataclass, field


@dataclass
class AgentRole:
    name: str
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=lambda: ["chat"])
PYEOF

cat > src/iao/agents/roles/assistant.py <<'PYEOF'
"""Assistant — general-purpose helper role."""
from iao.agents.roles.base_role import AgentRole


ASSISTANT_ROLE = AgentRole(
    name="assistant",
    system_prompt="You are a helpful assistant. Answer concisely. If asked to do something you cannot do, say so plainly.",
    allowed_tools=["chat"],
)
PYEOF

cat > src/iao/agents/roles/code_runner.py <<'PYEOF'
"""Code runner — role for code execution tasks."""
from iao.agents.roles.base_role import AgentRole


CODE_RUNNER_ROLE = AgentRole(
    name="code_runner",
    system_prompt="You are a code runner. When asked to solve a problem, write minimal code and execute it. Report the result factually.",
    allowed_tools=["chat", "execute_code"],
)
PYEOF

cat > src/iao/agents/roles/reviewer.py <<'PYEOF'
"""Reviewer — role for reviewing iao artifacts (full implementation deferred to 0.1.8)."""
from iao.agents.roles.base_role import AgentRole


REVIEWER_ROLE = AgentRole(
    name="reviewer",
    system_prompt="You are an artifact reviewer. Read the provided content and identify concerns. Do not modify the content.",
    allowed_tools=["chat"],
)
PYEOF
```

#### W8.4 — Smoke tests

```fish
cat > scripts/smoke_openclaw.py <<'PYEOF'
"""Smoke test OpenClaw — Ollama-native, no open-interpreter."""
import sys
from iao.agents.openclaw import OpenClawSession


def main():
    print("Creating OpenClawSession...", flush=True)
    session = OpenClawSession(role="assistant")
    print(f"Session ID: {session.session_id}", flush=True)

    print("\nTest 1: chat", flush=True)
    response = session.chat("What is 2+2? Answer with just the number.")
    print(f"Response: {response[:200]}", flush=True)
    assert "4" in response, f"Expected '4' in response, got: {response[:100]}"
    print("PASS", flush=True)

    print("\nTest 2: execute_code", flush=True)
    result = session.execute_code("print(2+2)", language="python")
    print(f"Result: {result}", flush=True)
    assert result["exit_code"] == 0
    assert "4" in result["stdout"]
    print("PASS", flush=True)

    session.close()
    print("\nAll OpenClaw smoke tests passed", flush=True)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
PYEOF

cat > scripts/smoke_nemoclaw.py <<'PYEOF'
"""Smoke test NemoClaw — orchestration via Nemotron."""
import sys
from iao.agents.nemoclaw import NemoClawOrchestrator


def main():
    print("Creating NemoClawOrchestrator...", flush=True)
    orch = NemoClawOrchestrator(session_count=1)
    print(f"Sessions: {len(orch.sessions)}, role: {orch.sessions[0].role}", flush=True)

    print("\nDispatching task: 'What is the capital of France?'", flush=True)
    response = orch.dispatch("What is the capital of France? Answer in one word.", role="assistant")
    print(f"Response: {response[:200]}", flush=True)
    assert "paris" in response.lower(), f"Expected 'Paris' in response, got: {response[:100]}"
    print("PASS", flush=True)

    orch.close_all()
    print("\nAll NemoClaw smoke tests passed", flush=True)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
PYEOF

python3 scripts/smoke_openclaw.py
# Expected: PASS on both chat and execute_code tests

python3 scripts/smoke_nemoclaw.py
# Expected: PASS on dispatch test
```

#### W8.5 — Architecture docs

Gemini creates `docs/harness/agents-architecture.md` ≥1500 words documenting:
- OpenClaw as execution primitive (Qwen + subprocess sandbox, NO open-interpreter)
- NemoClaw as orchestration (Nemotron-driven task routing)
- Role taxonomy
- Event log integration
- 0.1.8 roadmap: review agent role, telegram bridge

```fish
# Gemini writes the file directly via its Write tool
```

#### W8.6 — ADR-040

```fish
printf '\n### iaomw-ADR-040: OpenClaw/NemoClaw Ollama-Native Rebuild\n\n- **Context:** iao 0.1.4 W5 shipped OpenClaw and NemoClaw as stubs blocked by open-interpreter dependency on tiktoken which requires Rust to build on Python 3.14.\n- **Decision:** 0.1.7 W8 rebuilds both as Qwen/Ollama-native. OpenClaw uses QwenClient + subprocess sandbox. NemoClaw uses Nemotron classification for task routing. No open-interpreter, no tiktoken, no Rust.\n- **Rationale:** iao already has the streaming QwenClient (0.1.7 W1). Subprocess sandboxing is adequate for Phase 0. Nemotron classification is proven (0.1.4 W2).\n- **Consequences:** src/iao/agents/ now functional. Smoke tests pass. Review agent role and telegram bridge deferred to 0.1.8.\n' >> docs/harness/base.md
```

#### W8.7 — Build log and checkpoint

```fish
printf '\n## W8 — OpenClaw/NemoClaw Ollama-Native Rebuild\n\n**Status:** COMPLETE\n**Wall clock:** ~XX min\n\nActions:\n- W8.1: Rewrote src/iao/agents/openclaw.py with QwenClient + subprocess sandbox\n- W8.2: Rewrote src/iao/agents/nemoclaw.py with Nemotron classification\n- W8.3: Role definitions (assistant, code_runner, reviewer stub)\n- W8.4: scripts/smoke_openclaw.py and smoke_nemoclaw.py pass\n- W8.5: docs/harness/agents-architecture.md created (≥1500 words)\n- W8.6: iaomw-ADR-040 in base.md\n- No open-interpreter dependency anywhere (verified via grep)\n\nDiscrepancies: none\n\n---\n\n' >> docs/iterations/0.1.7/iao-build-log-0.1.7.md

jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W8.status = "complete" | .workstreams.W8.completed_at = $ts | .current_workstream = "W9"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
```

---

### W9 — Dogfood + Closing Sequence

**Executor:** Gemini CLI
**Wall clock target:** 75 min

#### W9.1 — Build log generation (Qwen via repaired loop)

```fish
./bin/iao iteration build-log 0.1.7
# Streaming visible, heartbeat every 30s, max 1500 words
# Evaluator runs after generation
# Structural gate checks
```

Watch the output. If repetition detector fires, check event log. If evaluator rejects, retry happens automatically once.

```fish
wc -w docs/iterations/0.1.7/iao-build-log-0.1.7.md
# Expected: ≤1500 words (target), ≥500 words (substantive)
```

#### W9.2 — Report generation

```fish
./bin/iao iteration report 0.1.7
# Same pattern, max 1000 words

wc -w docs/iterations/0.1.7/iao-report-0.1.7.md
# Expected: ≤1000 words
```

#### W9.3 — Post-flight validation

```fish
./bin/iao doctor postflight
# Expected: PASS for bundle_quality (22 sections), run_report_quality, structural_gates, gemini_compat, ten_pillars_present, readme_current
```

#### W9.4 — Iteration close

```fish
./bin/iao iteration close
# Generates run report, bundle
# Sends Telegram notification
# Prints workstream summary
# Exits without --confirm (Kyle's action)
```

#### W9.5 — Bug fix validation

Manually inspect generated artifacts:

```fish
# Run report
cat docs/iterations/0.1.7/iao-run-report-0.1.7.md
# Check: workstream table shows all W0-W9, Agent Questions section populated or explicit empty, sign-off section present

wc -c docs/iterations/0.1.7/iao-run-report-0.1.7.md
# Expected: ≥1500 bytes

# Bundle
grep -c "^## §" docs/iterations/0.1.7/iao-bundle-0.1.7.md
# Expected: 22

grep "^## §22\." docs/iterations/0.1.7/iao-bundle-0.1.7.md
# Expected: ## §22. Agentic Components

wc -c docs/iterations/0.1.7/iao-bundle-0.1.7.md
# Expected: ≥100 KB
```

#### W9.6 — Evaluator dogfood check

```fish
# Run the evaluator against our own generated artifacts
python3 -c "
from iao.artifacts.evaluator import evaluate_text
from pathlib import Path
import json

with open('docs/iterations/0.1.7/seed.json') as f:
    seed = json.load(f)

for artifact_name in ['iao-build-log-0.1.7.md', 'iao-report-0.1.7.md']:
    path = Path(f'docs/iterations/0.1.7/{artifact_name}')
    if path.exists():
        result = evaluate_text(path.read_text(), project_root=Path.cwd(), seed=seed)
        print(f'{artifact_name}: {result[\"severity\"]} ({len(result[\"errors\"])} errors)')
"
# Expected: clean or warn (not reject)
```

#### W9.7 — CHANGELOG

Gemini appends 0.1.7 entry summarizing all 10 workstreams.

#### W9.8 — Stop in review pending state

```fish
jq --arg ts (date -u +%Y-%m-%dT%H:%M:%SZ) '.workstreams.W9.status = "complete" | .workstreams.W9.completed_at = $ts | .current_workstream = "review_pending" | .completed_at = $ts' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json

echo "
================================================
ITERATION 0.1.7 EXECUTION COMPLETE
================================================
Run report: docs/iterations/0.1.7/iao-run-report-0.1.7.md
Bundle:     docs/iterations/0.1.7/iao-bundle-0.1.7.md (22 sections)
Workstreams: 10/10 complete (or partial — see build log)

Telegram notification sent to Kyle.

NEXT STEPS (Kyle):
1. Review the bundle
2. Open the run report, fill in Kyle's Notes
3. Answer any agent questions
4. Tick 5 sign-off checkboxes
5. Run: ./bin/iao iteration close --confirm

Until --confirm, iteration is in PENDING REVIEW state.
"
```

**DO NOT run `--confirm` yourself.** Kyle's action.

---

## Section D — Post-flight (after Kyle's --confirm)

```fish
./bin/iao iteration close --confirm
# Validates sign-off, updates .iao.json, marks iteration complete

./bin/iao doctor postflight
# Final validation

./bin/iao iteration seed
# Seeds 0.1.8 design input from 0.1.7 run report
```

Kyle then manually commits (Pillar 0):

```fish
git status  # if git-tracked at this point
# git add -A
# git commit -m "iao 0.1.7: Let Qwen Cook — loop repair, evaluator, component checklist, OpenClaw rebuild"
```

---

## Section E — Rollback

```fish
tmux kill-session -t iao-0.1.7 2>/dev/null
rm -rf ~/dev/projects/iao
mv ~/dev/projects/iao.backup-pre-0.1.7 ~/dev/projects/iao
cd ~/dev/projects/iao
pip install -e . --break-system-packages
./bin/iao --version
# Expected: 0.1.4 (pre-0.1.7 state)
```

Rollback if: W1 streaming breaks existing tests catastrophically, W3 evaluator rejects every artifact (false positive avalanche), W8 OpenClaw rebuild fails in a way that corrupts the agents package.

Do NOT rollback for: partial W6 (expected), OpenClaw smoke test flakiness (acceptable), evaluator warnings on 0.1.4 artifacts (historical, not blocking).

---

## Section F — Wall clock targets

| Workstream | Target | Cumulative |
|---|---|---|
| Pre-flight | 15 min | 0:15 |
| W0 Environment hygiene | 15 min | 0:30 |
| W1 Stream + repetition detection | 90 min | 2:00 |
| W2 Word count + structural gates | 60 min | 3:00 |
| W3 Evaluator | 75 min | 4:15 |
| W4 Rich seed | 60 min | 5:15 |
| W5 RAG freshness | 45 min | 6:00 |
| W6 Two-pass (experimental) | 90 min | 7:30 |
| W7 Component checklist | 60 min | 8:30 |
| W8 OpenClaw rebuild | 120 min | 10:30 |
| W9 Dogfood + close | 75 min | 11:45 |

Soft cap 10 hours, estimate 11:45. No hard cap. W6 is the primary partial-ship candidate.

---

## Section G — Sign-off

This plan is immutable once W0 begins. GEMINI.md and CLAUDE.md are the executor briefs; both reference this plan's Section C for execution detail. Either executor can run 0.1.7.

— iao 0.1.7 planning chat, 2026-04-09
