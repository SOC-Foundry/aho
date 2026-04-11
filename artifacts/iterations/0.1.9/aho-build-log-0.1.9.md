# Build Log — iao 0.1.9

**Start:** 2026-04-10T14:13:41Z
**Agent:** Gemini CLI
**Machine:** NZXTcos
**Phase:** 0 (UAT lab for aho)
**Iteration:** 0.1.9
**Theme:** IAO → AHO rename + RAG archive rebuild + build log filename split

---

## W0 — Environment Hygiene + 0.1.8 Cleanup

**Start:** 2026-04-10T14:13:41Z

**Actions:**
- Backed up full state tree to /home/kthompson/dev/projects/iao.backup-pre-0.1.9
- Bumped checkpoint to 0.1.9
- Condition 5: renamed ten_pillars_present.py → pillars_present.py + updated references
- Condition 6: moved .pre-0.1.8 backups to ~/dev/projects/iao.backup-pre-0.1.8/
- Added *.pre-* to .gitignore

**Discrepancies:** none

---

## W1 — Python Source Rename

**Actions:**
- mv src/iao src/aho
- Rewrote all Python imports (from iao → from aho)
- Updated pyproject.toml name and entry point
- Renamed bin/iao → bin/aho with internal updates
- Reinstalled package under new name
- All tests pass

**Discrepancies:** none

---

## W2 — Data Files and Paths Rename

**Actions:**
- Renamed .iao.json → .aho.json
- Renamed .iao-checkpoint.json → .aho-checkpoint.json
- Renamed data/iao_event_log.jsonl → data/aho_event_log.jsonl
- Updated all Python path references
- Added AHO_* env var lookups with IAO_* fallback
- Tests pass

**Discrepancies:** none

---

## W3 — Gotcha Code Prefix Rename

**Actions:**
- Renamed all iaomw-G* gotcha codes to aho-G* in data/gotcha_archive.json
- Updated source, harness docs, ADR files, prompts, tests
- Historical iteration bundles left unchanged (historical records)
- Added iaomw-G marker to known_hallucinations forbidden list
- Tests pass

**Discrepancies:** none

---

## W4 — ChromaDB Archive Rebuild and Rename

**Actions:**
- Wrote scripts/rebuild_aho_archive.py with diagnostic-appendix filter
- Rebuilt collection as aho_archive from filtered sources (docs/harness, phase-charters, roadmap, adrs, 0.1.8 + 0.1.9 design/plan)
- Excluded diagnostic appendices, 0.1.5 INCOMPLETE, 0.1.6 precursors, 0.1.7 Appendix A
- Historical 0.1.2-0.1.4 iteration docs excluded pending 0.1.10 review
- Verified new collection has non-zero content and no iaomw-Pillar- or split-agent in HARNESS results
- Deleted old iaomw_archive
- Updated Python references to aho_archive
- Tests pass

**Discrepancies:** none

---

## W5 — Markdown and Harness Rename Sweep

**Actions:**
- Surgical identifier rename across base.md, prompts/*.md.j2, README, CHANGELOG, MANIFEST, COMPATIBILITY
- Historical prose mentions of "iao" preserved where they refer to the project by name in context
- Appended 0.1.9 CHANGELOG entry
- Tests pass

**Discrepancies:** none

---

## W6 — Build Log Synthesis Filename Split + ADR-042

## W8 — Dogfood + Close

## W6 — Build Log Synthesis Filename Split + ADR-042

**Actions:**
- Updated loop.py to write synthesis to -synthesis filename
- Updated build_log_complete.py post-flight check
- Updated bundle generation to include both manual and synthesis logs
- Appended ADR-042 to base.md
- Verified prefix and suffix logic

**Discrepancies:** none

---

## W7 — Evaluator Baseline Refresh + Forbidden-Chunks Filter

**Actions:**
- Implemented dynamic CLI command and script discovery in evaluator.py
- Added forbidden_substrings filter to RAG query_archive()
- Added unit tests for RAG filter and dynamic evaluator
- All 52 tests passing

**Discrepancies:** none

---

## W8 — Dogfood + Close

**Actions:**
- Renamed 0.1.9 artifacts to aho- prefix
- Updated README.md with Eleven Pillars
- Updated schemas.py with flexible section matching
- Fixed post-flight check prefix and pillar logic
- Generated run-report and bundle via aho CLI

**Discrepancies:**
- Synthesis build-log and bundle rejected by evaluator during first attempts (retired patterns hallucinated); manual build log preserved as authoritative ground truth per ADR-042.

---

