# Build Log — aho 0.1.11

**Start:** 2026-04-10T20:36:16Z
**Agent:** Gemini CLI
**Machine:** NZXTcos
**Phase:** 0
**Run:** 0.1.11
**Theme:** Run file rename + test suite hygiene + Qwen degenerate investigation
**Project root:** /home/kthompson/dev/projects/iao

---

## W0 — Environment Hygiene

**Actions:**
- Project root: /home/kthompson/dev/projects/iao
- Bumped checkpoint to 0.1.11
- Bumped version to 0.1.11
- Backed up files to /home/kthompson/dev/projects/iao.backup-pre-0.1.11

**Discrepancies:** Project root rename still pending

---

## W1 — Run File Filename Rename

**Actions:**
- Updated run report generator output filename from aho-run-report-*.md to aho-run-*.md
- Renamed `src/aho/feedback/run_report.py` to `src/aho/feedback/run.py`
- Renamed `generate_run_report` to `generate_run`
- Renamed postflight modules: `run_report_complete` → `run_complete`, `run_report_quality` → `run_quality`
- Updated all internal references in `cli.py`, `loop.py`, `schemas.py`, `seed.py`, `notifications.py`, `prompt.py`
- Renamed template `prompts/run-report.md.j2` to `prompts/run.md.j2`
- Updated `src/aho/bundle/__init__.py` to look for `aho-run-*.md`
- Updated and renamed tests: `tests/test_run_report_pillars.py` → `tests/test_run_pillars.py`

**Discrepancies:** none

---

## W2 — Test Suite Hygiene

**Actions:**
- Fixed `test_secrets_backends`: skipped `test_age_integration` if no TTY is available (fixes headless agent failures)
- Fixed `test_artifacts_loop`: added missing "Phase 0" to test design body to satisfy schema validation
- Full test suite: 0 failures (53 passed, 1 skipped)

**Discrepancies:** none

---

## W3 — Qwen Degenerate Synthesis Investigation

**Actions:**
- Analyzed repetition detector and observed "Wait, checking..." evasion risk
- Implemented secondary "Information Density" check in `RepetitionDetector`
- Added density threshold: < 10% unique words over a 500-token window
- Verified with new test `tests/test_density_check.py`

**Discrepancies:** none

---

