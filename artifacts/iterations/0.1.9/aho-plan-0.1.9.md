# iao — Plan 0.1.9

**Iteration:** 0.1.9
**Phase:** 0 (UAT lab for aho)
**Predecessor:** 0.1.8 (graduated with conditions, sign-off #5 = not satisfied)
**Wall clock target:** ~7 hours soft cap, no hard cap
**Workstreams:** W0–W8 (nine)
**Authored:** 2026-04-10

Operational companion to `iao-design-0.1.9.md`. Design is the *why*, this is the *how*. Section C contains copy-pasteable fish blocks per workstream.

This iteration is a rename plus three non-rename items (RAG archive rebuild, build log filename split, evaluator baseline refresh). The rename workstreams (W1-W3, W5) are mechanical but surface-wide and must be atomic. W4 is the highest-leverage fix for 0.1.8's Qwen RAG problem. W6 directly answers Kyle's Agent Question 3 from 0.1.8 close. W7 partially addresses Conditions 3 and 4.

---

## Section A — Pre-flight checks

Run these in a fresh fish shell before launching any executor. If any fails, STOP and resolve.

```fish
# A.0 — Working directory
cd ~/dev/projects/iao
command pwd
# Expected: /home/kthompson/dev/projects/iao

# A.1 — 0.1.8 is closed
jq .last_completed_iteration .iao-checkpoint.json
# Expected: "0.1.8"

jq .iteration .iao-checkpoint.json
# Expected: "0.1.8" (will bump to 0.1.9 in W0)

# A.2 — Design and plan docs present
command ls docs/iterations/0.1.9/iao-design-0.1.9.md docs/iterations/0.1.9/iao-plan-0.1.9.md
# Expected: both files listed

# A.3 — iao binary still works
./bin/iao --version
# Expected: iao 0.1.8

# A.4 — Ollama models present
curl -s http://localhost:11434/api/tags | python3 -c "import json, sys; d = json.load(sys.stdin); names = [m['name'] for m in d['models']]; required = ['qwen3.5:9b', 'nemotron-mini:4b', 'nomic-embed-text:latest']; missing = [r for r in required if not any(r in n for n in names)]; print('OK' if not missing else f'MISSING: {missing}')"
# Expected: OK

# A.5 — Python version
python3 --version
# Expected: Python 3.14.x

# A.6 — ChromaDB archives present and current state
python3 -c "import chromadb; c = chromadb.PersistentClient(path='data/chroma'); [print(col.name, col.count()) for col in c.list_collections()]"
# Expected: iaomw_archive (with some count — this is the collection W4 will purge+rebuild), kjtco_archive, tripl_archive

# A.7 — Working tree is clean (git status should not show uncommitted changes that could be confused with rename work)
git status --short
# Expected: empty or only untracked items

# A.8 — 0.1.8 checkpoint is in the expected post-close state
jq . .iao-checkpoint.json
# Expected: iteration=0.1.8, last_completed_iteration should be 0.1.8 or 0.1.7, workstreams_complete reflects 0.1.8

# A.9 — Telegram credentials (non-blocking check)
./bin/iao telegram test iaomw 2>&1; or echo "Telegram not configured — non-blocking, will log in post-flight"

# A.10 — fish config untouched (Security-G001 — DO NOT CAT)
stat ~/.config/fish/config.fish >/dev/null; and echo "fish config exists"; or echo "MISSING"

# A.11 — Event log writable
touch data/iao_event_log.jsonl
command ls -l data/iao_event_log.jsonl
```

If all blocking checks pass (A.0 through A.8, A.10, A.11), launch the executor. Telegram (A.9) is non-blocking per Kyle's answer to Agent Question 2 in 0.1.8.

---

## Section B — Workstream ordering and dependencies

```
W0 (env hygiene + cleanup)
 └─→ W1 (Python source rename) — depends on W0 backup
      └─→ W2 (data files and paths rename) — depends on W1 (paths module is renamed)
           └─→ W3 (gotcha code prefix rename) — depends on W2 (data files renamed)
                └─→ W4 (ChromaDB rebuild + rename) — depends on W3 (evaluator uses new code prefix)
                     └─→ W5 (markdown/harness rename sweep) — depends on W4 (archive source docs are stable)
                          └─→ W6 (build log filename split + ADR-042) — depends on W5 (base.md is stable for ADR append)
                               └─→ W7 (evaluator baseline refresh + forbidden-chunks filter) — depends on W6
                                    └─→ W8 (dogfood + close) — depends on all prior
```

Strict sequential ordering. W1 through W5 are atomic within themselves — the repo is never half-renamed at the boundary between workstreams.

---

## Section C — Per-workstream fish command blocks

### W0 — Environment Hygiene + 0.1.8 Cleanup (20 min)

```fish
# W0.0 — Log W0 start
set W0_START (date -u +%Y-%m-%dT%H:%M:%SZ)
mkdir -p docs/iterations/0.1.9
printf '# Build Log — iao 0.1.9\n\n**Start:** %s\n**Agent:** %s\n**Machine:** NZXTcos\n**Phase:** 0 (UAT lab for aho)\n**Iteration:** 0.1.9\n**Theme:** IAO → AHO rename + RAG archive rebuild + build log filename split\n\n---\n\n## W0 — Environment Hygiene + 0.1.8 Cleanup\n\n**Start:** %s\n\n' "$W0_START" "$IAO_EXECUTOR" "$W0_START" > docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W0.1 — Verify location
cd ~/dev/projects/iao
command pwd

# W0.2 — Backup state (comprehensive — this iteration touches many files)
set BACKUP_DIR ~/dev/projects/iao.backup-pre-0.1.9
mkdir -p $BACKUP_DIR
cp -r src/iao $BACKUP_DIR/src-iao
cp -r tests $BACKUP_DIR/tests
cp -r docs/harness $BACKUP_DIR/docs-harness
cp -r data $BACKUP_DIR/data
cp -r bin $BACKUP_DIR/bin
cp pyproject.toml $BACKUP_DIR/pyproject.toml
cp .iao.json $BACKUP_DIR/.iao.json
cp .iao-checkpoint.json $BACKUP_DIR/.iao-checkpoint.json
cp CLAUDE.md $BACKUP_DIR/CLAUDE.md
cp GEMINI.md $BACKUP_DIR/GEMINI.md
command ls $BACKUP_DIR
# Expected: all listed

# W0.3 — Bump checkpoint iteration
jq '.iteration = "0.1.9" | .last_completed_iteration = "0.1.8"' .iao-checkpoint.json > .iao-checkpoint.json.tmp
mv .iao-checkpoint.json.tmp .iao-checkpoint.json
jq .iteration .iao-checkpoint.json
# Expected: "0.1.9"

# W0.4 — Verify design and plan docs present
test -f docs/iterations/0.1.9/iao-design-0.1.9.md; and echo "design OK"; or echo "design MISSING — STOP"
test -f docs/iterations/0.1.9/iao-plan-0.1.9.md; and echo "plan OK"; or echo "plan MISSING — STOP"

# W0.5 — Condition 5: rename ten_pillars_present.py → pillars_present.py
test -f src/iao/postflight/ten_pillars_present.py; and git mv src/iao/postflight/ten_pillars_present.py src/iao/postflight/pillars_present.py; or echo "ten_pillars_present.py not found — already renamed or gone"

# Update internal references (function names, imports, docstrings)
command rg -l "ten_pillars_present" src/ tests/ | xargs -r sed -i 's/ten_pillars_present/pillars_present/g'

# Verify
command rg -c "ten_pillars_present" src/ tests/
# Expected: 0

# W0.6 — Condition 6: move .pre-0.1.8 backup files out of repo root
mkdir -p ~/dev/projects/iao.backup-pre-0.1.8
for f in *.pre-0.1.8 docs/harness/*.pre-0.1.8
    if test -f $f
        mv $f ~/dev/projects/iao.backup-pre-0.1.8/
    end
end
command ls *.pre-* 2>/dev/null; or echo "no .pre-* files in root"

# Add .pre-* to .gitignore if not already present
command grep -q "^\*.pre-\*" .gitignore; or echo '*.pre-*' >> .gitignore

# W0.7 — Append W0 complete
printf '**Actions:**\n- Backed up full state tree to %s\n- Bumped checkpoint to 0.1.9\n- Condition 5: renamed ten_pillars_present.py → pillars_present.py + updated references\n- Condition 6: moved .pre-0.1.8 backups to ~/dev/projects/iao.backup-pre-0.1.8/\n- Added *.pre-* to .gitignore\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

**Escalation:** If W0.4 reports design or plan missing, STOP. Human setup failure. Kyle places the files and restarts.

---

### W1 — Python Source Rename (90 min)

```fish
# W1.0 — Log W1 start
printf '## W1 — Python Source Rename\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W1.1 — Inventory the rename surface
command rg -l "^from iao" src/ tests/ | wc -l
command rg -l "^import iao" src/ tests/ | wc -l
command rg -l " iao\." src/ tests/ | wc -l
# These give the scope estimate

# W1.2 — Atomic directory rename via git
git mv src/iao src/aho
command ls src/
# Expected: aho/ (and no iao/)

# W1.3 — Rewrite Python imports
command rg -l "^from iao" src/ tests/ scripts/ 2>/dev/null | xargs -r sed -i 's|^from iao|from aho|g'
command rg -l "^import iao" src/ tests/ scripts/ 2>/dev/null | xargs -r sed -i 's|^import iao\b|import aho|g'
command rg -l " iao\." src/ tests/ scripts/ 2>/dev/null | xargs -r sed -i 's| iao\.| aho.|g'
command rg -l "(iao\.cli\|iao\.config\|iao\.feedback\|iao\.artifacts\|iao\.postflight\|iao\.preflight\|iao\.rag\|iao\.agents\|iao\.bundle\|iao\.telegram\|iao\.secrets\|iao\.pipelines\|iao\.data\|iao\.install\|iao\.integrations)" src/ tests/ scripts/ 2>/dev/null | xargs -r sed -i 's|iao\.|aho.|g'

# W1.4 — Update pyproject.toml
sed -i 's/^name = "iao"/name = "aho"/' pyproject.toml
sed -i 's|iao = "iao\.cli:main"|aho = "aho.cli:main"|' pyproject.toml
command grep -n "^name\|\[project\.scripts\]" pyproject.toml
# Expected: name = "aho", entry point aho = "aho.cli:main"

# W1.5 — Rename bin/iao → bin/aho and update its internals
git mv bin/iao bin/aho
sed -i 's|from iao|from aho|g' bin/aho
sed -i 's|import iao\b|import aho|g' bin/aho
command cat bin/aho | head -20

# W1.6 — Reinstall the package under the new name
pip uninstall -y iao 2>/dev/null
pip install -e . --break-system-packages
./bin/aho --version
# Expected: aho 0.1.9

# W1.7 — Run the full test suite
python3 -m pytest tests/ -v 2>&1 | tail -30
# Expected: all tests pass

# W1.8 — Verify zero lingering iao imports
command rg -c "^from iao" src/ tests/
# Expected: 0
command rg -c "^import iao\b" src/ tests/
# Expected: 0

# W1.9 — Append W1 complete
printf '**Actions:**\n- git mv src/iao src/aho\n- Rewrote all Python imports (from iao → from aho)\n- Updated pyproject.toml name and entry point\n- Renamed bin/iao → bin/aho with internal updates\n- Reinstalled package under new name\n- All tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

**Escalation:** If W1.7 test suite fails, STOP. Roll back via Section E.1 restoring `src-iao`, revert pyproject.toml, reinstall. Re-attempt W1 with extra care on the sed patterns.

---

### W2 — Data Files and Paths Rename (45 min)

```fish
# W2.0 — Log W2 start
printf '## W2 — Data Files and Paths Rename\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W2.1 — Rename top-level state files
git mv .iao.json .aho.json
git mv .iao-checkpoint.json .aho-checkpoint.json
git mv data/iao_event_log.jsonl data/aho_event_log.jsonl
command ls -la .aho.json .aho-checkpoint.json data/aho_event_log.jsonl
# Expected: all three exist

# W2.2 — Update all Python references to these paths
command rg -l '\.iao\.json\|\.iao-checkpoint\.json\|iao_event_log' src/ tests/ scripts/ 2>/dev/null | xargs -r sed -i -e 's|\.iao\.json|.aho.json|g' -e 's|\.iao-checkpoint\.json|.aho-checkpoint.json|g' -e 's|iao_event_log|aho_event_log|g'

# Verify
command rg -c '\.iao\.json\|\.iao-checkpoint\.json\|iao_event_log' src/ tests/
# Expected: 0

# W2.3 — Update env var references: add AHO_* as primary, keep IAO_* as fallback for this iteration
command rg -l "IAO_ITERATION\|IAO_PROJECT_NAME\|IAO_PROJECT_CODE" src/ tests/ | xargs -r python3 -c '
import sys
for path in sys.argv[1:]:
    content = open(path).read()
    # Add AHO_* lookups with IAO_* fallback where os.environ.get is used
    content = content.replace(
        "os.environ.get(\"IAO_ITERATION\"",
        "os.environ.get(\"AHO_ITERATION\", os.environ.get(\"IAO_ITERATION\""
    )
    content = content.replace(
        "os.environ.get(\"IAO_PROJECT_NAME\"",
        "os.environ.get(\"AHO_PROJECT_NAME\", os.environ.get(\"IAO_PROJECT_NAME\""
    )
    content = content.replace(
        "os.environ.get(\"IAO_PROJECT_CODE\"",
        "os.environ.get(\"AHO_PROJECT_CODE\", os.environ.get(\"IAO_PROJECT_CODE\""
    )
    open(path, "w").write(content)
    print(f"updated {path}")
' ::: $argv

# W2.4 — Reinstall to pick up any paths module changes
pip install -e . --break-system-packages --quiet

# W2.5 — Verify aho CLI still works with the new state files
./bin/aho --version
# Expected: aho 0.1.9

jq .iteration .aho-checkpoint.json
# Expected: "0.1.9"

# W2.6 — Run test suite
python3 -m pytest tests/ -v 2>&1 | tail -20

# W2.7 — Append W2 complete
printf '**Actions:**\n- Renamed .iao.json → .aho.json\n- Renamed .iao-checkpoint.json → .aho-checkpoint.json\n- Renamed data/iao_event_log.jsonl → data/aho_event_log.jsonl\n- Updated all Python path references\n- Added AHO_* env var lookups with IAO_* fallback\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

---

### W3 — Gotcha Code Prefix Rename (45 min)

```fish
# W3.0 — Log W3 start
printf '## W3 — Gotcha Code Prefix Rename\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W3.1 — Inventory gotcha code references
command rg -c "iaomw-G" data/ src/ docs/ prompts/
# Expected: some count — this is the surface

# W3.2 — Rewrite gotcha_archive.json codes
python3 <<'PYEOF'
import json
p = "data/gotcha_archive.json"
d = json.load(open(p))
renamed = 0
for g in d.get("gotchas", []):
    if "code" in g and g["code"].startswith("iaomw-"):
        g["code"] = g["code"].replace("iaomw-", "aho-", 1)
        renamed += 1
json.dump(d, open(p, "w"), indent=2)
print(f"Renamed {renamed} gotcha codes")
PYEOF

# W3.3 — Rewrite all references across source and docs (NOT historical ADR bundles from prior iterations)
command rg -l "iaomw-G" src/ docs/harness/ docs/adrs/ prompts/ tests/ 2>/dev/null | xargs -r sed -i 's/iaomw-G/aho-G/g'

# Verify
command rg -c "iaomw-G" src/ docs/harness/ docs/adrs/ prompts/ tests/
# Expected: 0

# Historical iteration bundles are UNCHANGED (they're historical records)
command rg -c "iaomw-G" docs/iterations/
# Expected: N > 0 (historical bundles keep their original text)

# W3.4 — Update known_hallucinations.json: add retired iaomw-G* marker
python3 <<'PYEOF'
import json
p = "data/known_hallucinations.json"
d = json.loads(open(p).read())
forbidden_key = None
for k in d:
    if isinstance(d[k], list) and "forbidden" in k.lower():
        forbidden_key = k
        break
if forbidden_key:
    marker = "iaomw-G"  # any reference to old-prefix gotcha codes is retired
    if marker not in d[forbidden_key]:
        d[forbidden_key].append(marker)
        open(p, "w").write(json.dumps(d, indent=2))
        print(f"Added {marker} to forbidden list")
PYEOF

# W3.5 — Run test suite
python3 -m pytest tests/ -v 2>&1 | tail -20

# W3.6 — Append W3 complete
printf '**Actions:**\n- Renamed all iaomw-G* gotcha codes to aho-G* in data/gotcha_archive.json\n- Updated source, harness docs, ADR files, prompts, tests\n- Historical iteration bundles left unchanged (historical records)\n- Added iaomw-G marker to known_hallucinations forbidden list\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

---

### W4 — ChromaDB Archive Rebuild and Rename (75 min)

```fish
# W4.0 — Log W4 start
printf '## W4 — ChromaDB Archive Rebuild and Rename\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W4.1 — Write the rebuild script
cat > scripts/rebuild_aho_archive.py <<'PYEOF'
#!/usr/bin/env python3
"""Rebuild the ChromaDB archive as `aho_archive` from a filtered source.

Excludes:
- Diagnostic appendices (## Appendix A, ## Diagnostic, ## Exhibit sections)
- 0.1.5 INCOMPLETE iteration docs
- 0.1.6 forensic audit precursors
- 0.1.7 design doc Appendix A (the diagnostic corpus)
- Historical 0.1.2 – 0.1.4 iteration docs (can be re-added in 0.1.10 after review)

Includes:
- docs/harness/*.md (current state)
- docs/phase-charters/*.md
- docs/roadmap/*.md
- docs/adrs/*.md
- docs/iterations/0.1.8/iao-design-0.1.8.md
- docs/iterations/0.1.8/iao-plan-0.1.8.md
- docs/iterations/0.1.9/iao-design-0.1.9.md (if present at rebuild time)
- docs/iterations/0.1.9/iao-plan-0.1.9.md (if present at rebuild time)
"""
import re
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


SOURCE_DIRS = [
    "docs/harness",
    "docs/phase-charters",
    "docs/roadmap",
    "docs/adrs",
]
SOURCE_FILES = [
    "docs/iterations/0.1.8/iao-design-0.1.8.md",
    "docs/iterations/0.1.8/iao-plan-0.1.8.md",
    "docs/iterations/0.1.9/iao-design-0.1.9.md",
    "docs/iterations/0.1.9/iao-plan-0.1.9.md",
]

DIAGNOSTIC_HEADER_RE = re.compile(
    r"^##\s+(Appendix\s+[A-Z]|Diagnostic|Exhibit)",
    re.MULTILINE,
)


def strip_diagnostic_appendices(text: str) -> str:
    """Remove any section whose header matches DIAGNOSTIC_HEADER_RE, up to the next H2."""
    match = DIAGNOSTIC_HEADER_RE.search(text)
    if not match:
        return text
    # Everything before the diagnostic header is kept
    before = text[: match.start()]
    # Find the next H2 after the diagnostic header
    after_start = match.end()
    next_h2 = re.search(r"^##\s+", text[after_start:], re.MULTILINE)
    if next_h2:
        after = text[after_start + next_h2.start() :]
        # Recurse — there may be more diagnostic sections
        return strip_diagnostic_appendices(before + after)
    else:
        return before


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def collect_source_docs() -> list[tuple[Path, str]]:
    docs = []
    for d in SOURCE_DIRS:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.rglob("*.md"):
            docs.append((f, f.read_text()))
    for f in SOURCE_FILES:
        p = Path(f)
        if p.exists():
            docs.append((p, p.read_text()))
    return docs


def main():
    client = chromadb.PersistentClient(path="data/chroma")
    embedding_fn = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text",
    )

    # Build new collection with temp name first
    temp_name = "aho_archive_new"
    try:
        client.delete_collection(temp_name)
    except Exception:
        pass
    new_col = client.create_collection(
        name=temp_name,
        embedding_function=embedding_fn,
    )

    docs = collect_source_docs()
    print(f"Collected {len(docs)} source documents")

    ids = []
    contents = []
    metadatas = []
    for path, raw in docs:
        filtered = strip_diagnostic_appendices(raw)
        chunks = chunk_text(filtered)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{path.as_posix()}#chunk-{i}"
            ids.append(chunk_id)
            contents.append(chunk)
            metadatas.append({
                "source_file": path.as_posix(),
                "chunk_index": i,
                "source_iteration": "0.1.9",
                "chunk_type": "harness" if "docs/harness" in path.as_posix() else "iteration_doc",
            })

    if contents:
        new_col.add(ids=ids, documents=contents, metadatas=metadatas)
    print(f"Added {len(contents)} chunks to {temp_name}")

    # Verify the new collection has content
    count = new_col.count()
    if count == 0:
        raise SystemExit(f"ERROR: {temp_name} has 0 documents after rebuild — aborting")

    # Smoke-check: query for "pillar" and ensure no result contains iaomw-Pillar-
    results = new_col.query(query_texts=["pillar"], n_results=5)
    for doc in results.get("documents", [[]])[0]:
        if "iaomw-Pillar-" in doc:
            raise SystemExit(f"ERROR: {temp_name} still contains iaomw-Pillar- in results — rebuild filter failed")
        if "split-agent" in doc:
            raise SystemExit(f"ERROR: {temp_name} still contains split-agent in results — rebuild filter failed")

    # Only now delete the old collection and rename temp
    try:
        client.delete_collection("iaomw_archive")
        print("Deleted iaomw_archive")
    except Exception as e:
        print(f"Warning: could not delete iaomw_archive: {e}")

    # ChromaDB doesn't support rename directly — so we re-create under the final name
    final_col = client.create_collection(
        name="aho_archive",
        embedding_function=embedding_fn,
    )
    all_data = new_col.get()
    if all_data["ids"]:
        final_col.add(
            ids=all_data["ids"],
            documents=all_data["documents"],
            metadatas=all_data["metadatas"],
        )
    client.delete_collection(temp_name)
    print(f"Created aho_archive with {final_col.count()} documents")


if __name__ == "__main__":
    main()
PYEOF

# W4.2 — Run the rebuild script
python3 scripts/rebuild_aho_archive.py

# W4.3 — Verify the new collection exists and old is gone
python3 -c "
import chromadb
c = chromadb.PersistentClient(path='data/chroma')
cols = [col.name for col in c.list_collections()]
print('Collections:', cols)
assert 'aho_archive' in cols, 'aho_archive missing'
assert 'iaomw_archive' not in cols, 'iaomw_archive still present'
aho = c.get_collection('aho_archive')
print(f'aho_archive count: {aho.count()}')
assert aho.count() > 0, 'aho_archive is empty'
print('PASS')
"

# W4.4 — Update Python code to query aho_archive instead of iaomw_archive
command rg -l "iaomw_archive" src/aho/ tests/ scripts/ 2>/dev/null | xargs -r sed -i 's/iaomw_archive/aho_archive/g'
command rg -c "iaomw_archive" src/aho/ tests/ scripts/
# Expected: 0

# W4.5 — Run test suite
python3 -m pytest tests/ -v 2>&1 | tail -20

# W4.6 — Append W4 complete
printf '**Actions:**\n- Wrote scripts/rebuild_aho_archive.py with diagnostic-appendix filter\n- Rebuilt collection as aho_archive from filtered sources (docs/harness, phase-charters, roadmap, adrs, 0.1.8 + 0.1.9 design/plan)\n- Excluded diagnostic appendices, 0.1.5 INCOMPLETE, 0.1.6 precursors, 0.1.7 Appendix A\n- Historical 0.1.2-0.1.4 iteration docs excluded pending 0.1.10 review\n- Verified new collection has non-zero content and no iaomw-Pillar- or split-agent in query results\n- Deleted old iaomw_archive\n- Updated Python references to aho_archive\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

**Escalation:** If the rebuild script fails before `aho_archive` is populated, the old `iaomw_archive` is still intact. Do not proceed to W4.3/W4.4 until the new collection exists and has content. If the rebuild truly cannot complete, roll back W4 only (the Python still queries `iaomw_archive` via the W4.4 sed — revert that sed) and mark W4 as partial-ship.

---

### W5 — Markdown and Harness Rename Sweep (60 min)

```fish
# W5.0 — Log W5 start
printf '## W5 — Markdown and Harness Rename Sweep\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W5.1 — Inventory markdown identifier references
command rg -n "iaomw\b" docs/harness/ prompts/ README.md CHANGELOG.md MANIFEST.json COMPATIBILITY.md 2>/dev/null

# W5.2 — base.md: careful, surgical rewrite
# Review before applying:
command rg -n "iaomw\|src/iao/\|bin/iao\|\.iao\.json" docs/harness/base.md

# Apply only identifier renames (not prose mentions of "iao the project")
sed -i 's|src/iao/|src/aho/|g' docs/harness/base.md
sed -i 's|bin/iao\b|bin/aho|g' docs/harness/base.md
sed -i 's|\.iao\.json|.aho.json|g' docs/harness/base.md
sed -i 's|\.iao-checkpoint\.json|.aho-checkpoint.json|g' docs/harness/base.md
sed -i 's|iaomw_archive|aho_archive|g' docs/harness/base.md
sed -i 's|iaomw-G|aho-G|g' docs/harness/base.md

# Verify
command rg -n "iaomw\|src/iao/\|\.iao\.json" docs/harness/base.md
# Expected: 0 matches (or only in historical ADR context like ADR-041)

# W5.3 — prompts/*.md.j2: same surgical rewrite
for f in prompts/*.md.j2
    sed -i 's|src/iao/|src/aho/|g' $f
    sed -i 's|bin/iao\b|bin/aho|g' $f
    sed -i 's|\.iao\.json|.aho.json|g' $f
    sed -i 's|iaomw_archive|aho_archive|g' $f
    sed -i 's|iaomw-G|aho-G|g' $f
end

# W5.4 — README.md, CHANGELOG.md, MANIFEST.json, COMPATIBILITY.md
for f in README.md CHANGELOG.md COMPATIBILITY.md
    if test -f $f
        sed -i 's|src/iao/|src/aho/|g' $f
        sed -i 's|bin/iao\b|bin/aho|g' $f
        sed -i 's|\.iao\.json|.aho.json|g' $f
        sed -i 's|iaomw_archive|aho_archive|g' $f
    end
end

# MANIFEST.json needs JSON-safe editing
python3 <<'PYEOF'
import json
from pathlib import Path
p = Path("MANIFEST.json")
if p.exists():
    d = json.loads(p.read_text())
    s = json.dumps(d)
    s = s.replace("src/iao/", "src/aho/").replace("bin/iao", "bin/aho").replace(".iao.json", ".aho.json").replace("iaomw_archive", "aho_archive")
    p.write_text(json.dumps(json.loads(s), indent=2))
    print("MANIFEST.json updated")
PYEOF

# W5.5 — Append 0.1.9 entry to CHANGELOG
printf '\n## 0.1.9 — IAO → AHO Rename\n\n- Renamed Python package iao → aho\n- Renamed CLI bin/iao → bin/aho\n- Renamed state files .iao.json → .aho.json, .iao-checkpoint.json → .aho-checkpoint.json\n- Renamed ChromaDB collection iaomw_archive → aho_archive (rebuilt from filtered source, excluding diagnostic appendices)\n- Renamed gotcha code prefix iaomw-G* → aho-G*\n- Build log filename split: manual build log is authoritative, Qwen synthesis goes to -synthesis suffix (ADR-042)\n- Pillars and eleven-pillar content unchanged\n' >> CHANGELOG.md

# W5.6 — Verify
command rg -c "iaomw\|src/iao/\|bin/iao\b" docs/harness/ prompts/ README.md CHANGELOG.md COMPATIBILITY.md
# Expected: 0 (or only historical ADR context in base.md)

./bin/aho --version
# Expected: still aho 0.1.9

python3 -m pytest tests/ -v 2>&1 | tail -10

# W5.7 — Append W5 complete
printf '**Actions:**\n- Surgical identifier rename across base.md, prompts/*.md.j2, README, CHANGELOG, MANIFEST, COMPATIBILITY\n- Historical prose mentions of "iao" preserved where they refer to the project by name in context\n- Appended 0.1.9 CHANGELOG entry\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

---

### W6 — Build Log Synthesis Filename Split + ADR-042 (60 min)

```fish
# W6.0 — Log W6 start
printf '## W6 — Build Log Synthesis Filename Split + ADR-042\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W6.1 — Find the build log write path in loop.py
command rg -n "build.log\|build_log" src/aho/artifacts/loop.py

# W6.2 — Edit loop.py to write synthesis to the -synthesis filename
# Executor action: use str_replace/Edit to change the write target from
#   docs/iterations/<version>/aho-build-log-<version>.md
# to
#   docs/iterations/<version>/aho-build-log-synthesis-<version>.md
# Preserve the manual file path as a read input if the synthesis needs to reference it.

# W6.3 — Update build_log_complete postflight check
command rg -n "build_log_complete\|build.log.complete" src/aho/postflight/

# Executor action: update the postflight check to expect aho-build-log-<version>.md (manual) as primary;
# aho-build-log-synthesis-<version>.md (synthesis) as optional secondary.

# W6.4 — Update bundle spec to embed both files
command rg -n "BUNDLE_SPEC\|build_log" src/aho/bundle/__init__.py

# Executor action: in the bundle generator, §3 Build Log should embed the manual file.
# Either add §3a Build Log Synthesis, or extend §3 with a divider and both files.
# Recommendation: extend §3, add a subsection header "### Build Log Synthesis (Qwen)" below the manual.

# W6.5 — Append ADR-042 to base.md
cat >> docs/harness/base.md <<'ADREOF'

---

## ADR-042 — Manual build log is authoritative; Qwen synthesis is optional commentary

**Status:** Accepted
**Date:** 2026-04-10 (aho 0.1.9 W6)
**Supersedes:** (partial amendment to ADR-012)

### Context

During 0.1.8 W8 dogfood, Qwen synthesis for the build log was rejected 3 times by the W4 synthesis evaluator because the output contained retired patterns sourced from stale RAG context. The artifact loop would normally have overwritten the manual build log with each attempt. Claude Code intervened to preserve the manual build log as ground truth, but this required manual workaround rather than a structural safeguard.

The root cause is two artifacts sharing one filename. The manual build log (ground truth, written by the executor workstream-by-workstream) and the Qwen synthesis build log (optional commentary, evaluated for hallucinations) occupied the same file at `aho-build-log-<version>.md`. The loop treated the synthesis as a replacement rather than an augmentation.

### Decision

The manual build log and the Qwen synthesis live in separate files:
- `docs/iterations/<version>/aho-build-log-<version>.md` — manual ground truth, written by the executor, immutable per ADR-012
- `docs/iterations/<version>/aho-build-log-synthesis-<version>.md` — Qwen-generated commentary, evaluated by the synthesis evaluator, can fail without blocking graduation

The manual build log joins the immutable-inputs list in ADR-012 alongside the design and plan documents. The synthesis file is an optional output artifact that may be missing or empty without the iteration being considered incomplete.

The bundle §3 Build Log section embeds both files when present: the manual first, then the synthesis with a clear divider below.

### Consequences

- "Missing §4 Report" class failures (like 0.1.8) become non-issues because the manual build log is always present as ground truth, and the synthesis can fail without leaving the iteration without a canonical build log.
- Realizes Pillar 7 (generation and evaluation are separate roles) at the artifact level: the executor writes the manual log (generation role), Qwen writes the synthesis (a different generator), the evaluator checks the synthesis only (evaluation role). Neither generator reviews its own work.
- The `build_log_complete` postflight check distinguishes primary (manual) from secondary (synthesis) presence.
- Future iterations should consider extending this pattern to other canonical artifacts — the manual/synthesis split is a generalizable idea.

ADREOF

command grep -c "ADR-042" docs/harness/base.md
# Expected: 1

# W6.6 — Smoke test the filename split
mkdir -p /tmp/aho-smoke-w6/docs/iterations/0.1.99
touch /tmp/aho-smoke-w6/docs/iterations/0.1.99/aho-build-log-0.1.99.md
cd /tmp/aho-smoke-w6
# Run a minimal build-log generation against this throwaway dir
# (executor should figure out the right incantation; the key assertion is that
# aho-build-log-0.1.99.md is NOT overwritten)
cd ~/dev/projects/iao

# W6.7 — Run test suite
python3 -m pytest tests/ -v 2>&1 | tail -20

# W6.8 — Append W6 complete
printf '**Actions:**\n- Updated loop.py to write synthesis to aho-build-log-synthesis-<version>.md\n- Updated build_log_complete postflight check to distinguish manual (primary) vs synthesis (secondary)\n- Updated bundle generator to embed both files in §3\n- Appended ADR-042 to base.md\n- Tests pass\n\n**Discrepancies:** none\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

---

### W7 — Evaluator Baseline Refresh + Forbidden-Chunks Filter (60 min)

```fish
# W7.0 — Log W7 start
printf '## W7 — Evaluator Baseline Refresh + Forbidden-Chunks Filter\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W7.1 — Find the static baseline references in evaluator.py
command rg -n "scripts\|allowed_scripts\|known_good" src/aho/artifacts/evaluator.py

# W7.2 — Add dynamic baseline computation
# Executor action: add a function at evaluator load time that:
#   - walks scripts/ and collects all .py filenames as allowed_scripts
#   - imports aho.cli and introspects registered subcommands as allowed_cli_commands
#   - caches the results in module-level variables
# Replace any static lists with references to these cached dynamic lists.

# W7.3 — Add forbidden-chunks filter to rag/archive.py
command rg -n "def query_archive" src/aho/rag/archive.py

# Executor action: add a `forbidden_substrings` parameter to query_archive() that defaults to
# reading from data/known_hallucinations.json at call time. After retrieving top-k chunks from
# ChromaDB, filter out any chunk whose content contains any forbidden substring. Log filtered
# count via log_event("rag_chunk_filtered", count=N).

# W7.4 — Write the RAG filter test
cat > tests/test_rag_forbidden_filter.py <<'PYEOF'
"""Verify query_archive filters out chunks containing forbidden substrings."""
import json
from pathlib import Path

import pytest


def test_forbidden_filter_excludes_poisoned_chunks(tmp_path, monkeypatch):
    """If a query would return a chunk containing 'iaomw-Pillar-1', it must be filtered."""
    from aho.rag.archive import query_archive
    results = query_archive("pillar", forbidden_substrings=["iaomw-Pillar-"], n_results=10)
    for chunk in results.get("documents", [[]])[0]:
        assert "iaomw-Pillar-" not in chunk, f"forbidden substring not filtered: {chunk[:100]}"


def test_forbidden_filter_reads_from_known_hallucinations_by_default():
    """Without explicit forbidden_substrings, default should come from known_hallucinations.json."""
    from aho.rag.archive import query_archive
    results = query_archive("pillar", n_results=10)
    # The default forbidden list should include iaomw-Pillar-
    for chunk in results.get("documents", [[]])[0]:
        assert "iaomw-Pillar-" not in chunk
PYEOF

# W7.5 — Write the dynamic baseline test
cat > tests/test_evaluator_dynamic_baseline.py <<'PYEOF'
"""Verify evaluator reads allowed scripts and CLI commands from live repo state."""
from pathlib import Path

import pytest


def test_allowed_scripts_includes_new_file(tmp_path, monkeypatch):
    """Adding a new .py file to scripts/ should make it appear in the evaluator's allowed list."""
    # Create a throwaway script
    new_script = Path("scripts/test_w7_smoke.py")
    new_script.write_text("# smoke test\n")
    try:
        # Force the evaluator to reload its baseline
        from aho.artifacts import evaluator
        if hasattr(evaluator, "_baseline_cache"):
            evaluator._baseline_cache = None
        from aho.artifacts.evaluator import get_allowed_scripts
        scripts = get_allowed_scripts()
        assert "test_w7_smoke.py" in scripts, f"new script not in baseline: {scripts}"
    finally:
        new_script.unlink()


def test_allowed_cli_commands_from_introspection():
    """CLI command baseline should come from aho.cli, not a static list."""
    from aho.artifacts.evaluator import get_allowed_cli_commands
    commands = get_allowed_cli_commands()
    # The current CLI has these subcommands per aho/cli.py
    assert "iteration" in commands
    assert "doctor" in commands
    assert "registry" in commands
PYEOF

# W7.6 — Run tests
python3 -m pytest tests/test_rag_forbidden_filter.py tests/test_evaluator_dynamic_baseline.py -v

# W7.7 — Append W7 complete
printf '**Actions:**\n- Evaluator now computes allowed scripts from scripts/ directory at load time\n- Evaluator now computes allowed CLI commands from aho.cli introspection\n- Added forbidden_substrings parameter to query_archive() with default from known_hallucinations.json\n- RAG retrieval filters out chunks containing forbidden substrings\n- Added 2 unit test files (RAG filter, dynamic baseline)\n\n**Discrepancies:** (list any tests that did not pass — this workstream permits partial ship)\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

**Partial-ship criterion:** If the dynamic baseline rewrite breaks existing tests, revert evaluator.py changes and keep only the forbidden-chunks filter. The forbidden-chunks filter is the higher-priority deliverable (it's the Condition 1 secondary fix). Dynamic baseline is nice-to-have. Defer the dynamic baseline to 0.1.10 if needed.

---

### W8 — Dogfood + Close (60 min)

```fish
# W8.0 — Log W8 start
printf '## W8 — Dogfood + Close\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md

# W8.1 — Generate build log synthesis via Qwen (new filename split in effect)
./bin/aho iteration build-log 0.1.9

# Verify the synthesis file was created at the new path and the manual file is untouched
test -f docs/iterations/0.1.9/aho-build-log-0.1.9.md; and echo "manual OK"; or echo "manual MISSING"
test -f docs/iterations/0.1.9/aho-build-log-synthesis-0.1.9.md; and echo "synthesis OK"; or echo "synthesis MISSING"

# W8.2 — Generate report via Qwen
./bin/aho iteration report 0.1.9

# W8.3 — Run post-flight validation
./bin/aho doctor postflight 0.1.9

# W8.4 — Generate run report and bundle (does NOT --confirm)
./bin/aho iteration close

# W8.5 — Verification 1: aho binary version
./bin/aho --version
# Expected: aho 0.1.9

# W8.6 — Verification 2: src/iao gone, src/aho present
test ! -d src/iao; and echo "V2 PASS"; or echo "V2 FAIL"
test -d src/aho; and echo "V2b PASS"; or echo "V2b FAIL"

# W8.7 — Verification 3: .aho.json present, .iao.json gone
test -f .aho.json; and echo "V3 PASS"; or echo "V3 FAIL"
test ! -f .iao.json; and echo "V3b PASS"; or echo "V3b FAIL"

# W8.8 — Verification 4: bundle §3 structure (manual + synthesis both embedded if synthesis exists)
command grep -c "^## §3" docs/iterations/0.1.9/aho-bundle-0.1.9.md
# Expected: 1 (single §3 with embedded content)

# W8.9 — Verification 5: bundle §3, §4, §5 do NOT contain iaomw-Pillar- in synthesized content
# Extract the build log, report, run report sections and grep
python3 <<'PYEOF'
import re
bundle = open("docs/iterations/0.1.9/aho-bundle-0.1.9.md").read()
# Sections §3 through §5 are the generated/synthesized artifacts
sections = re.split(r"\n## §(\d+)", bundle)
issues = []
for i in range(1, len(sections), 2):
    num = sections[i]
    body = sections[i+1]
    if num in ("3", "4", "5"):
        if "iaomw-Pillar-" in body:
            issues.append(f"§{num} contains iaomw-Pillar-")
        if "split-agent" in body:
            issues.append(f"§{num} contains split-agent")
if issues:
    print("FAIL:", issues)
else:
    print("V5 PASS")
PYEOF

# W8.10 — Verification 6: §22 has ≥6 components with updated naming
python3 <<'PYEOF'
import re
bundle = open("docs/iterations/0.1.9/aho-bundle-0.1.9.md").read()
match = re.search(r"## §22.*?(?=\n## §|\Z)", bundle, re.DOTALL)
if not match:
    print("V6 FAIL: §22 not found")
else:
    rows = [line for line in match.group().split("\n") if line.startswith("|") and not line.startswith("|---")]
    components = set()
    for row in rows[1:]:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if cells:
            components.add(cells[0])
    print(f"Components: {sorted(components)}, count={len(components)}")
    if len(components) >= 6:
        print("V6 PASS")
    else:
        print(f"V6 FAIL: expected >=6, got {len(components)}")
PYEOF

# W8.11 — Verification 7: workstream summary has no unknown agents
command grep -c "| unknown " docs/iterations/0.1.9/aho-run-report-0.1.9.md
# Expected: 0

# W8.12 — Verification 8: bundle has 22 sections
command grep -c "^## §" docs/iterations/0.1.9/aho-bundle-0.1.9.md
# Expected: 22

# W8.13 — Kyle-satisfaction criterion K1: §4 Report is present and non-empty
python3 -c "
import re
bundle = open('docs/iterations/0.1.9/aho-bundle-0.1.9.md').read()
match = re.search(r'^## §4\. Report\s*\n(.*?)(?=^## §|\Z)', bundle, re.MULTILINE | re.DOTALL)
if not match:
    print('K1 FAIL: §4 not found')
elif 'MISSING' in match.group(1) or len(match.group(1).strip()) < 50:
    print(f'K1 FAIL: §4 appears empty or missing. Content: {match.group(1)[:100]}')
else:
    print('K1 PASS')
"

# W8.14 — Kyle-satisfaction criterion K2: synthesis evaluator reject count ≤ 1 in the event log
python3 -c "
import json
rejects = 0
for line in open('data/aho_event_log.jsonl'):
    try:
        e = json.loads(line)
        if e.get('event_type') == 'synthesis_evaluator_reject' and e.get('iteration') == '0.1.9':
            rejects += 1
    except Exception:
        pass
print(f'Synthesis rejects during 0.1.9: {rejects}')
if rejects <= 1:
    print('K2 PASS')
else:
    print(f'K2 FAIL: expected <=1, got {rejects}')
"

# W8.15 — Send Telegram notification (non-blocking if credentials not yet configured)
./bin/aho telegram notify "aho 0.1.9 complete — $(date -u +%H:%M) UTC" 2>&1; or echo "Telegram notification failed — non-blocking"

# W8.16 — Print closing message
printf '\n================================================\nITERATION 0.1.9 EXECUTION COMPLETE\n================================================\nRun report: docs/iterations/0.1.9/aho-run-report-0.1.9.md\nBundle:     docs/iterations/0.1.9/aho-bundle-0.1.9.md\nWorkstreams: 9/9 complete (or partial — see build log)\n\nNEXT STEPS (Kyle):\n1. Review the bundle\n2. Open the run report, fill in Kyles Notes\n3. Answer any agent questions\n4. Tick 6 sign-off checkboxes\n5. Run: ./bin/aho iteration close --confirm\n\nUntil --confirm, iteration is in PENDING REVIEW state.\n'

# W8.17 — Append W8 complete
printf '**Actions:**\n- Generated build log synthesis, report, run report, bundle via renamed loop\n- Ran all eight verification checks\n- Evaluated Kyle-satisfaction criteria K1, K2\n- Iteration in PENDING REVIEW state\n\n**Verification results:**\n- V1 aho --version returns aho 0.1.9: (pass/fail)\n- V2 src/iao gone, src/aho exists: (pass/fail)\n- V3 .aho.json present, .iao.json gone: (pass/fail)\n- V4 bundle §3 present: (pass/fail)\n- V5 synthesized sections have no retired-pattern literals: (pass/fail)\n- V6 §22 has >=6 components: (pass/fail)\n- V7 no unknown agents: (pass/fail)\n- V8 22 bundle sections: (pass/fail)\n\n**Kyle-satisfaction criteria:**\n- K1 §4 Report present and non-empty: (pass/fail)\n- K2 synthesis evaluator rejects <=1: (pass/fail)\n- K3 no new regressions: (review manually)\n\n**Discrepancies:** (fill in)\n\n---\n\n' >> docs/iterations/0.1.9/iao-build-log-0.1.9.md
```

**Escalation:** If V1-V8 fail, STOP and surface. If K1 fails (report missing or empty), Claude Code writes a minimal manual report from the build log (this is allowed and expected under the new ADR-042 pattern — the manual log is ground truth). If K2 fails (>1 synthesis rejects), log it clearly in the build log as a carryover to 0.1.10 and surface to Kyle's Notes for a graduation decision.

---

## Section D — Post-flight checks

```fish
# D.1 — All workstream headers logged
command grep -c "^## W[0-8] " docs/iterations/0.1.9/iao-build-log-0.1.9.md
# Expected: 9

# D.2 — No stray TODOs
command rg "TODO\|FIXME\|XXX" docs/iterations/0.1.9/iao-build-log-0.1.9.md

# D.3 — Bundle size sanity
command du -h docs/iterations/0.1.9/aho-bundle-0.1.9.md
# Expected: 100KB – 300KB (slightly larger than 0.1.8 due to dual build log)

# D.4 — Checkpoint completion
jq '.workstreams_complete' .aho-checkpoint.json

# D.5 — Event log has 0.1.9 entries
command grep -c '"iteration": "0.1.9"' data/aho_event_log.jsonl

# D.6 — Test suite green
python3 -m pytest tests/ -v 2>&1 | tail -5

# D.7 — No lingering retired identifiers in current state (historical iterations stay)
command rg -c "src/iao/\|bin/iao\b\|\.iao\.json\|iaomw_archive" src/aho/ tests/ docs/harness/ prompts/
# Expected: 0 (or only historical ADR context in base.md)
```

---

## Section E — Rollback procedure

If 0.1.9 fails catastrophically and Kyle needs to revert to 0.1.8 state:

```fish
# E.1 — Restore from backup
set BACKUP_DIR ~/dev/projects/iao.backup-pre-0.1.9
test -d $BACKUP_DIR/src-iao; or echo "ERROR: backup missing — STOP"

rm -rf src/aho
cp -r $BACKUP_DIR/src-iao src/iao
cp -r $BACKUP_DIR/bin/* bin/
cp $BACKUP_DIR/pyproject.toml pyproject.toml
cp $BACKUP_DIR/.iao.json .iao.json 2>/dev/null
cp $BACKUP_DIR/.iao-checkpoint.json .iao-checkpoint.json 2>/dev/null
cp -r $BACKUP_DIR/docs-harness/* docs/harness/
cp -r $BACKUP_DIR/data/* data/

# E.2 — Remove .aho.* files that shouldn't exist in 0.1.8 state
rm -f .aho.json .aho-checkpoint.json data/aho_event_log.jsonl

# E.3 — Reinstall iao under its old name
pip uninstall -y aho 2>/dev/null
pip install -e . --break-system-packages

# E.4 — Verify rollback
./bin/iao --version
# Expected: iao 0.1.8

# E.5 — Restore ChromaDB if W4 completed
# If aho_archive exists but iaomw_archive is gone, this is a one-way migration.
# Rollback means accepting that the old iaomw_archive is lost and the new aho_archive stays.
# Rename aho_archive back to iaomw_archive if needed (not required; rollback to 0.1.8 with aho_archive is fine).

# E.6 — Mark 0.1.9 incomplete
printf '# INCOMPLETE\n\n0.1.9 was attempted %s and rolled back.\nReason: (fill in)\n\nBackup preserved at %s\n' (date -u +%Y-%m-%d) $BACKUP_DIR > docs/iterations/0.1.9/INCOMPLETE.md

# E.7 — Pytest baseline
python3 -m pytest tests/ -v
```

Partial rollbacks (individual workstream) should be preferred where possible. Full rollback is the nuclear option and only runs if the rename fundamentally broke the codebase.

---

## Section F — Wall clock estimate

| Workstream | Target | Cumulative |
|---|---|---|
| W0 — Environment Hygiene + Cleanup | 20 min | 0:20 |
| W1 — Python Source Rename | 90 min | 1:50 |
| W2 — Data Files + Paths Rename | 45 min | 2:35 |
| W3 — Gotcha Code Prefix Rename | 45 min | 3:20 |
| W4 — ChromaDB Rebuild + Rename | 75 min | 4:35 |
| W5 — Markdown + Harness Sweep | 60 min | 5:35 |
| W6 — Build Log Filename Split + ADR-042 | 60 min | 6:35 |
| W7 — Evaluator Baseline + Forbidden Filter | 60 min | 7:35 |
| W8 — Dogfood + Close | 60 min | 8:35 |

**Soft cap:** 8:35
**Hard cap:** none

---

*Plan doc generated 2026-04-10, iao 0.1.9 planning chat (Kyle + Claude web)*
