# aho Plan — 0.2.5

**Phase:** 0 | **Iteration:** 2 | **Run:** 5
**Theme:** Clone-to-deploy install.fish + 0.2.3 carry-forward hardening
**Predecessor:** 0.2.4 (closed clean)
**Design:** `aho-design-0_2_5.md`
**Agent split:** Single-agent Claude Code throughout. Larger surface than 0.2.4 but coherent enough that splitting would add coordination overhead.

---

## Workstreams

| WS | Surface | Outcome |
|---|---|---|
| W0 | Canonical bumps + Kyle decisions captured | 10 artifacts → 0.2.5, pacman/aur subset locked, smoke test path locked |
| W1 | `bin/aho-pacman` + `pacman-packages.txt` | Native package wrapper, declarative subset, idempotent |
| W2 | `bin/aho-aur` + `aur-packages.txt` | AUR wrapper with yay bootstrap, declarative subset (likely empty) |
| W3 | `bin/aho-models` + `model-fleet.txt` | Ollama fleet wrapper, paired with existing aho-models-status |
| W4 | `bin/aho-secrets-init` | Age keygen + keyring + telegram scaffold, absorbs 0.2.3 W4 logic |
| W5 | `bin/aho-systemd` + `bin/aho-python` | 4-daemon installer (closes harness-watcher gap), pip wrapper |
| W6 | `install.fish` orchestrator rewrite | Thin orchestrator calling W1–W5 + existing aho-mcp + aho doctor |
| W7 | OTEL `aho.tokens` scalar fix + helper + test | aho-G064 captured, dict→scalar flatten, no more stderr noise |
| W8 | Evaluator score parser fix + test | Scale detection, raw_score/raw_recommendation preservation |
| W9 | Conductor `bin/aho-conductor smoke` subcommand | Real verifiable smoke test, file marker + span assertion |
| W10 | Gotcha registry + tests + close | aho-G064 + aho-G065, e2e install.fish dry-run test, bundle, run report |

This is a 10-workstream iteration. Larger than typical but the surfaces are independent enough that they don't blocker each other inside a single executor.

---

## Workstream details

### W0 — Bumps + decisions

- All 10 canonical artifacts → 0.2.5
- `.aho.json` `current_iteration` → 0.2.5, bump on close
- Capture Kyle's answers to design open questions in `artifacts/iterations/0.2.5/decisions.md`:
  - Final pacman subset
  - Final AUR subset
  - `bin/aho-install` rename decision (keep or rename to `bin/aho-bootstrap`)
  - Telegram scaffolding flow confirmation
  - Smoke test Path A or Path B

### W1 — bin/aho-pacman

- `artifacts/harness/pacman-packages.txt` — declarative list, comments allowed, one package per line
- `bin/aho-pacman` subcommands: `list`, `status`, `install`, `doctor`
- `install` runs `sudo pacman -S --needed (cat artifacts/harness/pacman-packages.txt | grep -v '^#')`
- `status` shows installed/missing per package
- `doctor` asserts all listed packages present
- Capability gap halts on sudo password timeout
- Test: list parses correctly, status returns expected counts, install runs in dry-run mode without errors

### W2 — bin/aho-aur

- `artifacts/harness/aur-packages.txt` — likely empty, header comment explaining why
- `bin/aho-aur` subcommands match `bin/aho-pacman` surface
- Yay bootstrap: if `command -q yay` fails, clone from AUR and `makepkg -si`
- If list is empty: install/status/doctor are no-ops that report "no AUR packages declared"
- Test: empty list handled gracefully, yay bootstrap idempotent

### W3 — bin/aho-models

- `artifacts/harness/model-fleet.txt` — 4 models from NZXTcos
- `bin/aho-models` subcommands: `list`, `status` (delegates to existing aho-models-status), `install`, `doctor`
- `install` runs `ollama pull <model>` for each
- `doctor` asserts all 4 present in `ollama list` output
- Capability gap halt if ollama daemon not running
- Test: parses fleet file, doctor detects missing models

### W4 — bin/aho-secrets-init

- Absorb existing 0.2.3 W4 age keygen logic from `bin/aho-install`
- New unified surface: `bin/aho-secrets-init [--force]`
- First run: prompt for age passphrase, generate key at `~/.config/aho/age.key`, create keyring entry, scaffold `~/.config/aho/telegram/`, halt with capability gap for token entry
- Subsequent runs: detect existing key, skip generation, report state
- `--force` requires explicit confirmation, refuses if existing key present without confirmation
- Test: first-run flow with mocked passphrase, second-run no-op detection

### W5 — bin/aho-systemd + bin/aho-python

- `bin/aho-systemd` subcommands: `list`, `status`, `install`, `doctor`
- `install` deploys all 4 user service units from `templates/systemd/` (including aho-harness-watcher.service which closes 0.2.3 W3)
- Verifies linger enabled
- `bin/aho-python install` is `pip install -e . --break-system-packages` + verify `aho` on PATH
- Tests: systemd install on fresh dirs idempotent, python install verifies CLI

### W6 — install.fish orchestrator rewrite

- New `install.fish` at repo root
- Step order per design doc §"install.fish (rewrite)"
- Each step writes timestamped line to `~/.local/state/aho/install.log`
- Capability gap detection: any wrapper exits non-zero with `[CAPABILITY GAP]` in output, install.fish halts and prints resume instructions
- Resume: re-running install.fish skips completed steps via state file `~/.local/state/aho/install.state` (per-step pass/fail/pending)
- Final step: `aho doctor` full sweep
- Test: dry-run mode that mocks all wrappers, verifies step ordering and capability-gap halt behavior

### W7 — OTEL aho.tokens scalar fix

- New helper in `src/aho/otel.py`: `set_attrs_from_dict(span, prefix, d)` — recursively flattens dict into scalar attributes with dotted prefix
- Replace dict assignments in qwen-client, nemotron-client, glm-client, openclaw, nemoclaw, telegram (6 sites per 0.2.1 W3)
- Unit test: emit a span with the helper, assert no `Invalid type dict` errors in captured stderr
- Add aho-G064 to gotcha_archive.json

### W8 — Evaluator score parser fix

- File: `src/aho/agents/roles/evaluator.py` (or wherever evaluator output normalization lives)
- Add scale detection: if score ≤ 1.0, multiply by 10
- Preserve `raw_score` and `raw_recommendation` fields alongside normalized
- Unit tests: GLM 0–1 input, Qwen 0–10 input, malformed input
- Update existing evaluator tests if they assert on the old broken behavior

### W9 — Conductor smoke subcommand

- Add `smoke` subcommand to `bin/aho-conductor` (currently only `dispatch <task>`)
- Implementation: dispatches a deterministic task (`Create file /tmp/aho-smoke-marker-$RANDOM containing OK`), waits for completion, asserts:
  - File exists
  - File contains `OK`
  - Event log has 7+ spans for this dispatch (filter by timestamp window)
- Returns exit 0 on full pass, non-zero with diagnostic on any failure
- Add aho-G065 to gotcha_archive.json
- Test: shell out to `bin/aho-conductor smoke`, assert exit 0

### W10 — Close

- Full test suite green (target: 145+ tests, up from 137)
- Bundle generation, postflight green
- New postflight gates:
  - `install_fish_orchestrator_present` — assert install.fish exists, calls all 7 wrappers, syntax-checks via `fish -n`
  - `pacman_subset_declared` — assert `pacman-packages.txt` exists and is non-empty
  - `model_fleet_declared` — assert `model-fleet.txt` exists and matches running ollama list
- Run report `aho-run-0_2_5.md`
- Bundle update §24 Infrastructure with install.fish architecture
- Pending Kyle (carry to manual):
  - Run `install.fish` on NZXTcos as round-trip verification (idempotent re-run)
  - Eventually run `install.fish` on P3 as 0.2.6 validation
  - Git commit + push 0.2.5

---

## Definition of done

- [ ] All 10 canonical artifacts at 0.2.5
- [ ] `bin/aho-pacman`, `bin/aho-aur`, `bin/aho-models`, `bin/aho-secrets-init`, `bin/aho-systemd`, `bin/aho-python` all exist with `list/status/install/doctor` surfaces
- [ ] `pacman-packages.txt`, `aur-packages.txt`, `model-fleet.txt` exist under `artifacts/harness/`
- [ ] `install.fish` rewritten as orchestrator, calls all 7 wrappers in order
- [ ] `aho-harness-watcher.service` deployed on NZXTcos via `bin/aho-systemd install`
- [ ] OTEL `Invalid type dict` errors gone from nemoclaw and conductor logs
- [ ] Evaluator returns correct normalized scores + preserves raw values
- [ ] `bin/aho-conductor smoke` exits 0 with verifiable file marker + 7-span trace
- [ ] aho-G064 + aho-G065 in gotcha registry (19 total)
- [ ] 3 new postflight gates pass
- [ ] Test suite green (145+ tests)
- [ ] install.fish dry-run on NZXTcos passes idempotency check (run twice, second run is no-op)
- [ ] Bundle validates clean

---

## Risk register

- **Scope size:** 10 workstreams in one iteration is the largest aho has run. Risk: mid-iteration fatigue, defects piling up. Mitigation: W7/W8/W9 are independent of W1–W6 — if W6 install.fish runs long, defer W9 conductor smoke to 0.2.6 and ship 0.2.5 with the install.fish surface only.
- **Pacman subset accuracy:** wrong subset means P3 install fails on first try. Mitigation: W0 captures Kyle's manual review of `pacman -Qqe` before W1 starts.
- **Telegram first-run UX:** capability gap with file-drop instructions is the safest path but feels clunky. Acceptable for 0.2.5; revisit in 0.3.x if Phase 0 graduates.
- **Idempotency edge cases:** install.fish re-run after a partial failure needs `install.state` to be reliable. Test must cover the partial-failure-then-resume path explicitly.

---

## Out of scope (do not touch)

- Actual P3 clone-to-deploy execution (0.2.6)
- kjtcom anything
- MCP fetch/github/slack/google-drive replacement ADR (separate)
- Riverpod, Bourdain pipeline, etc.
- Telegram interactive token entry
- Adding `server-git` to MCP fleet
