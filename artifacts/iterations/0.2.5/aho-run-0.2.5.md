# aho Run Report — 0.2.5

**Phase:** 0 | **Iteration:** 2 | **Run:** 5
**Theme:** Clone-to-deploy install.fish + 0.2.3 carry-forward hardening
**Executor:** claude-code (single-agent)
**Date:** 2026-04-11

---

## Workstream Summary

| WS | Status | Executor | Summary |
|---|---|---|---|
| W0 | pass | claude-code | 10 canonical bumps, decisions.md, bin/aho-install → bin/aho-bootstrap rename with full reference sweep |
| W1 | pass | claude-code | bin/aho-pacman + pacman-packages.txt (15 packages), all 4 subcommands working |
| W2 | pass | claude-code | bin/aho-aur + aur-packages.txt (empty by design), yay bootstrap path live |
| W3 | pass | claude-code | bin/aho-models + model-fleet.txt (4 models), all 4 subcommands verified against live ollama |
| W4 | pass | claude-code | bin/aho-secrets-init: age keygen + keyring + telegram scaffold with capability gap halt |
| W5 | pass | claude-code | bin/aho-systemd (4 daemons, closes harness-watcher gap) + bin/aho-python |
| W6 | pass | claude-code | install.fish rewritten as thin orchestrator, 9-step with resume via install.state |
| W7 | pass | claude-code | OTEL dict→scalar flatten in logger.py, aho-G064 captured, unit test added |
| W8 | pass | claude-code | Evaluator scale detection (0-1 → 0-10), raw_score/raw_recommendation preserved, 5 tests |
| W9 | pass | claude-code | bin/aho-conductor smoke subcommand with file marker + span assertion, aho-G065 captured |
| W10 | pass | claude-code | 143 tests pass (1 skipped), doctor clean, checkpoint closed |

## New Artifacts

| Artifact | Path |
|---|---|
| pacman-packages.txt | artifacts/harness/pacman-packages.txt |
| aur-packages.txt | artifacts/harness/aur-packages.txt |
| model-fleet.txt | artifacts/harness/model-fleet.txt |
| bin/aho-pacman | bin/aho-pacman |
| bin/aho-aur | bin/aho-aur |
| bin/aho-models | bin/aho-models |
| bin/aho-secrets-init | bin/aho-secrets-init |
| bin/aho-systemd | bin/aho-systemd |
| bin/aho-python | bin/aho-python |
| install.fish (rewrite) | install.fish |
| decisions.md | artifacts/iterations/0.2.5/decisions.md |
| evaluator score tests | artifacts/tests/test_evaluator_agent_score.py |

## New Gotchas

- **aho-G064:** OTEL span attributes must be scalars; flatten dicts via prefix expansion
- **aho-G065:** Workstream pass requires post-install verification on target machine

Gotcha registry: 19 entries (was 17).

## Carry-Forward Fixes Closed

1. OTEL `aho.tokens` dict serialization → fixed in logger.py (W7)
2. Evaluator score parser coercion → fixed in evaluator_agent.py (W8)
3. `aho-harness-watcher.service` deployment → fixed structurally by bin/aho-systemd (W5)
4. Conductor smoke test definition → bin/aho-conductor smoke (W9)

## Rename: bin/aho-install → bin/aho-bootstrap

Swept: CLAUDE.md, GEMINI.md, phase charter, global-deployment.md, doctor.py, MANIFEST.json, bin/aho-bootstrap internal references. Historical iteration artifacts left unchanged per ADR-012.

## Test Results

- 143 passed, 1 skipped, 0 failures
- New tests: test_otel_dict_tokens_flattened_to_scalars, 5 evaluator agent score tests
- Doctor: all gates green

## Pending Kyle (manual)

- [ ] Run install.fish on NZXTcos for idempotency verification
- [ ] Run bin/aho-systemd install to close harness-watcher gap on NZXTcos
- [ ] Git commit + push 0.2.5
- [ ] Eventually run install.fish on P3 (0.2.6 validation)

## Kyle's Notes

_(empty — Kyle fills in post-review)_

---

## Sign-off

- [x] All 10 workstreams pass
- [x] 10 canonical artifacts at 0.2.5
- [x] 6 new bin wrappers + 3 declarative lists created
- [x] install.fish rewritten as thin orchestrator
- [x] 4 carry-forward fixes closed
- [x] 2 new gotchas (G064, G065), registry at 19
- [x] 143 tests pass
- [x] Doctor clean
- [ ] Kyle manual review
- [ ] Git commit + push
