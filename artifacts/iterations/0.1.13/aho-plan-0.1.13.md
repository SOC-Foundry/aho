# aho 0.1.13 — Plan

**Phase:** 0 | **Iteration:** 0.1.13 | **Primary:** Gemini CLI | **Closer:** Claude Code

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.1.13
tmux new-session -d -s aho-0.1.13 -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.13 'cd ~/dev/projects/aho; set -x AHO_EXECUTOR gemini-cli; gemini --yolo' Enter
```

## W0 — Environment hygiene + backup

```fish
cd ~/dev/projects/aho
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.1.13.tar.gz --exclude=data/chroma --exclude=.venv .
printf '{"iteration":"0.1.13","phase":0,"status":"in_progress"}\n' > .aho.json
command ls ~/.ollama/models/manifests/registry.ollama.ai/library/ | grep -E 'qwen|nemotron|glm|nomic'
python -c "import chromadb; c=chromadb.PersistentClient(path='data/chroma'); print(c.get_collection('aho_archive').count())"
```

**Gate:** backup exists, Ollama models present, ChromaDB count > 0.

## W1 — Phase 0 rewrite (CLAUDE.md + GEMINI.md + README)

1. Read `artifacts/harness/base.md` (post-W3 path; pre-W3 it's at `docs/harness/base.md`) for Eleven Pillars source of truth.
2. Rewrite `CLAUDE.md` from scratch. Sections: Phase 0 Objective, Role, Eleven Pillars (verbatim), Split-agent model, Gotcha query-first rule, Sign-off format, What NOT to do, First actions checklist.
3. Rewrite `GEMINI.md` from scratch with same structure, Gemini-specific launch flags and security gotchas (never `cat ~/.config/fish/config.fish`, aho-Sec001).
4. Sync README Phase 0 section: new objective, new exit criteria, new folder layout diagram, bump iteration to 0.1.13.
5. Verify: `rg -i "iao" CLAUDE.md GEMINI.md README.md` returns zero hits (except whitelisted historical references).

**Gate:** three files rewritten, zero iao narrative prose.

## W2 — Harness + ADR prose sweep

```fish
rg -l -i "\biao\b" docs/harness/ docs/adrs/ docs/roadmap/ > /tmp/aho-stale-prose.txt
command cat /tmp/aho-stale-prose.txt
```

1. Rewrite `docs/harness/agents-architecture.md` body — opening paragraph ("Iteration 0.1.7 introduces a complete rebuild of the iao agentic foundations" → 0.1.13 language), P3 Diligence section (`iao.logger.log_event` → `aho.logger.log_event`), footer (remove "iao 0.1.7 W8" credit, replace with 0.1.13 rewrite note).
2. Rewrite `docs/adrs/0001-phase-a-externalization.md` end-to-end. Status stays Accepted. All `iao` → `aho`, all code examples updated, `from iao import` → `from aho import`, `pip install -e` references updated.
3. Bump all `docs/harness/*.md` headers to 0.1.13. Body rewrites only where narrative drift exists.
4. Whitelist: `docs/iterations/0.1.2/` through `docs/iterations/0.1.8/` — DO NOT touch (historical).
5. Whitelist: `docs/phase-charters/iao-phase-0.md` — DO NOT rename or rewrite content, filename is historical artifact.

**Gate:** `rg -i "\biao\b" docs/harness/ docs/adrs/` returns only whitelisted hits.

## W3 — Folder reorg execution

**Order matters.** Do in this sequence:

```fish
cd ~/dev/projects/aho
mkdir -p artifacts app pipeline
git mv docs artifacts/_docs_tmp  # NO — use plain mv, Pillar 11
mv docs/harness artifacts/harness
mv docs/adrs artifacts/adrs
mv docs/iterations artifacts/iterations
mv docs/phase-charters artifacts/phase-charters
mv docs/roadmap artifacts/roadmap
rmdir docs
mv scripts artifacts/scripts
mv templates artifacts/templates
mv prompts artifacts/prompts
mv tests artifacts/tests
```

**Then update code:**

1. `src/aho/paths.py` — add `ARTIFACTS_ROOT`, `HARNESS_DIR`, `ADRS_DIR`, `ITERATIONS_DIR`, `PROMPTS_DIR`, `TEMPLATES_DIR`, `SCRIPTS_DIR`, `TESTS_DIR`. All resolved from project root + `artifacts/`.
2. Grep for every hardcoded `docs/`, `scripts/`, `templates/`, `prompts/`, `tests/` in `src/aho/`:
   ```fish
   rg -l '"(docs|scripts|templates|prompts|tests)/' src/aho/ bin/
   ```
   Update each to use the new path constants.
3. `pyproject.toml` — update `[tool.pytest.ini_options] testpaths = ["artifacts/tests"]`. Update any package data globs.
4. `install.fish` — update any `docs/`, `scripts/`, `prompts/` references.
5. Create `app/README.md` and `pipeline/README.md` as scaffolds ("Reserved for Phase 1+ — consumer application and pipeline mount points").
6. Cross-reference sweep:
   ```fish
   rg -l '\]\(docs/|\]\(scripts/|\]\(templates/|\]\(prompts/|\]\(tests/' artifacts/ CLAUDE.md GEMINI.md README.md
   ```
   Update every hit.
7. Run test suite:
   ```fish
   cd ~/dev/projects/aho
   python -m pytest artifacts/tests/ -x
   ```

**Gate:** test suite green, zero broken imports, `rg '"docs/' src/aho/` empty.

## W4 — `/bin` wrapper scaffolding

1. Write `artifacts/harness/bin-wrapper-pattern.md` (~400 words): Pillar 4 statement, required instrumentation hooks (event log call via `aho.logger.log_event`, input capture to `data/replay/{uuid}.json`, exit code propagation, capability-gap interrupt contract via OpenClaw notification channel), fish syntax constraints, prohibited surfaces (`git commit`, `git push`, secret reads).
2. Write `bin/wrapper-template.fish` with stub functions for instrumentation hooks and a TODO marker for the actual tool invocation.
3. Implement `bin/openclaw` as reference wrapper. Wraps `src/aho/agents/openclaw.py` session dispatch. Logs to event log. Captures inputs. Handles capability-gap interrupts.
4. Smoke test:
   ```fish
   bin/openclaw --help
   bin/openclaw chat "say hello in five words"
   tail -5 data/aho_event_log.jsonl
   ```

**Gate:** wrapper executes, event log entry written, replay JSON captured.

## W5 — Global deployment prep (design only, no sudo on NZXT)

1. Write `artifacts/harness/global-deployment.md`: XDG layout, install flow, capability-gap interrupt list for P3.
2. Write `bin/aho-install` skeleton — idempotent fish installer. Sections: detect platform, clone/update repo, create XDG dirs (`~/.local/bin/`, `~/.config/aho/`, `~/.local/share/aho/`), symlink wrappers, emit capability-gap instructions for Kyle to run manually (sudo package installs, Ollama service enable).
3. Write `artifacts/templates/credentials.example.fish` — credential template with placeholders, comments pointing to `aho secret` CLI.
4. Write `artifacts/harness/p3-deployment-runbook.md` — step-by-step for Kyle on P3: prerequisites, clone command, install command, verification steps, expected capability-gap interrupts.

**Gate:** four files written, zero execution of sudo commands on NZXT.

## W6 — Dogfood + close (Claude Code)

Handoff checkpoint: `.aho-checkpoint.json` reflects W5 complete. Claude Code resumes:

```fish
cd ~/dev/projects/aho
tmux new-session -d -s aho-0.1.13-close -c ~/dev/projects/aho
tmux send-keys -t aho-0.1.13-close 'claude --dangerously-skip-permissions' Enter
```

1. Full test suite: `python -m pytest artifacts/tests/ -v`
2. `aho doctor` — all gates green.
3. Bundle generation: verify §1–§21 spec, verify §22 component checklist = 6.
4. Postflight gates: `run_complete`, `run_quality`, `pillars_present`, `structural_gates`.
5. Populate `artifacts/iterations/0.1.13/aho-run-0.1.13.md` with workstream summary, agent questions, empty Kyle's Notes.
6. Bundle: `artifacts/iterations/0.1.13/aho-bundle-0.1.13.md`.
7. Handoff message to Kyle via Telegram (if wrapper ready) or stdout.

**Gate:** all postflight green, bundle validated, sign-off ready for Kyle.

## Capability-gap interrupts expected

- **W5:** None on NZXT (design-only). P3 deployment (0.1.14+) will need sudo for package installs.
- **W3:** None expected; if file permission issues surface on moves, halt and notify.

## Checkpoint schema

```json
{
  "iteration": "0.1.13",
  "phase": 0,
  "current_workstream": "W0",
  "workstreams": {
    "W0": "pending", "W1": "pending", "W2": "pending",
    "W3": "pending", "W4": "pending", "W5": "pending", "W6": "pending"
  },
  "executor": "gemini-cli",
  "started_at": null,
  "last_event": null
}
```
