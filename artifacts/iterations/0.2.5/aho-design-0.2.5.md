# aho Design — 0.2.5

**Phase:** 0 | **Iteration:** 2 | **Run:** 5
**Theme:** Clone-to-deploy install.fish + 0.2.3 carry-forward hardening
**Predecessor:** 0.2.4 (W1 remediation, closed clean)

---

## Why this iteration exists

0.2.5 has two intertwined goals.

**Primary:** rebuild `install.fish` as a complete clone-to-deploy entry point that takes a fresh CachyOS/Arch box from `git clone` to a working aho environment with zero manual Python edits. This is the gating deliverable for Phase 0 graduation — Phase 0 ends when P3 can clone aho and reach an operational state. Today, install.fish is a partial scaffold that only handles a subset of the steps. NZXTcos has all 4 daemons running, the model fleet pulled, the MCP fleet installed, and age keys generated, but only because Kyle did most of that work by hand or via separate wrappers across 0.2.1–0.2.4. None of it is reproducible from a single command.

**Secondary:** close the four 0.2.3 carry-forward defects discovered during 0.2.4 close. They are small individually but they erode trust in the run reports if they keep accumulating. Bundling them into the same iteration as install.fish makes sense because three of the four (`harness-watcher` deployment, OTEL dict bug, conductor smoke definition) touch surfaces that 0.2.5 is already modifying.

---

## Goals

1. `install.fish` is a thin orchestrator. Every step delegates to a `bin/aho-*` wrapper. Pillar 4 holds.
2. Running `install.fish` on a fresh CachyOS box brings up a complete aho environment: native packages, AUR packages, Python package, model fleet, age keys, OS keyring bootstrap, MCP fleet, all 4 systemd daemons (including harness-watcher), telegram scaffolding.
3. `install.fish` is idempotent. Running it twice on the same machine is safe — second run is mostly no-op.
4. `install.fish` halts cleanly on capability gaps (sudo prompts, secret entry, network failure) and resumes from the same point after the gap is closed.
5. The four 0.2.3 carry-forward defects are fixed with tests preventing recurrence.
6. Two new gotchas captured (OTEL scalar attributes, claimed-vs-installed verification).

## Non-goals

- Actually running install.fish on P3 (that's 0.2.6 validation, not 0.2.5 work).
- Telegram secret entry beyond a placeholder prompt + capability gap halt.
- Replacing `bin/aho-install` (it becomes one of the steps install.fish calls, possibly renamed `bin/aho-bootstrap`).
- Anything from kjtcom or the future MCP replacement ADR.
- Pulling Flutter into install.fish — Flutter is a kjtcom dependency, not an aho dependency. Kjtcom bootstrap installs Flutter on top of aho.

---

## The wrapper decomposition

Seven wrappers, one orchestrator.

### `bin/aho-pacman` (new)

Native package installation via `sudo pacman -S --needed`. Declares an explicit aho-required subset of pacman packages. Reads from `artifacts/harness/pacman-packages.txt` (one package per line, comments allowed). Idempotent by virtue of `--needed`.

The aho-required subset (to be finalized with Kyle from `pacman -Qqe` on NZXTcos):
- Base toolchain: fish, tmux, git, base-devel, python, python-pip
- Crypto/secrets: age
- Node ecosystem: nodejs, npm
- Optional but harness-relevant: jq, ripgrep, fd, htop

NOT in the subset: browsers, fonts, KDE/desktop extras, printer drivers, falcon-sensor, anything Kyle uses personally on NZXTcos that doesn't belong on a clean P3 install.

### `bin/aho-aur` (new)

AUR package installation via yay. Bootstraps yay itself if missing (clone from AUR, makepkg, install). Reads from `artifacts/harness/aur-packages.txt`.

The aho-required AUR subset is intentionally tiny:
- (likely empty for aho proper)

google-cloud-cli is kjtcom, not aho. flutter-bin is kjtcom, not aho. The other 12 AUR packages on NZXTcos are personal/desktop. **The aho AUR subset may be the empty set, in which case `bin/aho-aur` still exists for future use but `aur-packages.txt` is empty.** Confirm with Kyle during W2.

### `bin/aho-models` (new)

Model fleet installer via `ollama pull`. Reads from `artifacts/harness/model-fleet.txt`. Pairs with existing `bin/aho-models-status`. The 4 models on NZXTcos:
- `qwen3.5:9b`
- `nemotron-mini:4b`
- `haervwe/GLM-4.6V-Flash-9B:latest`
- `nomic-embed-text:latest`

Idempotent — `ollama pull` on an existing model is a no-op.

### `bin/aho-secrets-init` (new)

Combines age keygen + OS keyring bootstrap + telegram scaffolding. On first run:
- Generate age key at `~/.config/aho/age.key` if missing, prompt for passphrase
- Initialize OS keyring entry for aho secrets store
- Create telegram scaffolding directory + placeholder secrets entries
- Halt with `[CAPABILITY GAP]` instructions for telegram bot token + chat id entry

On subsequent runs: detect existing key, skip generation, report state.

Existing `bin/aho-install` 0.2.3 W4 logic (`_check_age_key`) folds into this wrapper.

### `bin/aho-systemd` (new)

Installs and enables the 4 user daemons from `templates/systemd/`:
- `aho-openclaw.service`
- `aho-nemoclaw.service`
- `aho-telegram.service`
- `aho-harness-watcher.service` ← **closes 0.2.3 W3 gap**

Verifies `loginctl enable-linger $USER` is set. Idempotent — `systemctl --user enable` is safe to repeat.

### `bin/aho-python` (new, thin)

Wraps `pip install -e . --break-system-packages` and verifies the `aho` CLI is on PATH. Exists as a wrapper for symmetry — Pillar 4 says every tool is invoked through a `/bin` wrapper.

### `bin/aho-mcp` (existing, no changes)

0.2.4 surface holds. install.fish calls `bin/aho-mcp install`.

### `install.fish` (rewrite)

Becomes a thin orchestrator. Step order:

1. Platform check (CachyOS or Arch, fish present, x86_64)
2. `bin/aho-pacman install` (native packages)
3. `bin/aho-aur install` (AUR packages, possibly no-op)
4. `bin/aho-python install` (pip install -e .)
5. `bin/aho-models install` (ollama pull fleet)
6. `bin/aho-secrets-init` (age + keyring + telegram scaffold)
7. `bin/aho-mcp install` (12-package npm fleet)
8. `bin/aho-systemd install` (4 user daemons)
9. `aho doctor` (final verification, all gates)

Each step writes a line to an install log at `~/.local/state/aho/install.log` with timestamp + status. Capability gaps halt with explicit resume instructions ("after entering telegram token, re-run `install.fish` and it will resume from step 7").

## The four 0.2.3 carry-forward fixes

### Fix 1: OTEL `aho.tokens` dict serialization (G-otel-scalar-attrs)

OTEL span attributes accept only scalars (`bool`, `str`, `bytes`, `int`, `float`) or sequences of scalars. The current `qwen-client`, `nemotron-client`, and `glm-client` all set `aho.tokens` to a dict like `{"total": 56, "input": 30, "output": 26}`. OTEL drops the attribute and emits an error to stderr.

**Fix:** flatten dict-shaped token counts into separate scalar attributes:
- `aho.tokens.total = 56`
- `aho.tokens.input = 30`
- `aho.tokens.output = 26`

Add a helper in `src/aho/otel.py` (or wherever the span emitter lives) called `set_attrs_from_dict(span, prefix, d)` that does this expansion. Replace the four direct dict assignments with calls to the helper. Add a unit test that asserts no `Invalid type dict` errors are emitted during a span emission.

**Gotcha:** aho-G064 OTEL span attributes must be scalars; flatten dicts via prefix expansion.

### Fix 2: Evaluator score parser coercion

GLM returned `"score": 1.0` (float, normalized 0–1 scale), and the evaluator coerced it to `"score": 8` (int, 0–10 scale) without an explicit conversion. The recommendation field was also rewritten from GLM's actual sentence to the literal string `"ship"`.

Two bugs:
- Score scale mismatch: GLM speaks 0–1, parser expects 0–10. Either normalize on the parser side (multiply by 10) or update the prompt to ask for 0–10.
- Recommendation rewrite: parser is converting GLM's natural language into a category enum without preserving the original text.

**Fix:** in the evaluator output normalizer (likely `src/aho/agents/roles/evaluator.py` or similar), preserve `raw_score` and `raw_recommendation` alongside the normalized fields. Add explicit scale detection (if score ≤ 1, multiply by 10) with a unit test for both 0–1 and 0–10 inputs.

### Fix 3: `aho-harness-watcher.service` deployment

Service template exists in `templates/systemd/` from 0.2.3 W3 but was never installed on NZXTcos. **Fixed structurally by `bin/aho-systemd install` adding it to the deploy list.** No additional code change needed beyond the wrapper.

### Fix 4: Conductor smoke test definition (G-claimed-vs-installed)

The current dispatch (`bin/aho-conductor dispatch "smoke test 7-span trace"`) verifies the 7-span pipeline works as plumbing but doesn't verify any real outcome. Qwen roleplays the deliverables. GLM rubber-stamps the roleplay.

**Fix:** define a real smoke test that has a verifiable outcome. Two paths:

- **Path A (cheap):** dispatch a task whose success can be checked by file existence. E.g., `bin/aho-conductor dispatch "Create file /tmp/aho-smoke-marker containing the text OK"`. After dispatch, verify the file exists with the right content.
- **Path B (better):** add a `bin/aho-conductor smoke` subcommand that runs Path A internally + asserts the 7 spans landed in the event log + asserts the deliverable file exists. Returns exit 0 on full success, non-zero on any failure.

**Recommendation:** Path B. Lives in 0.2.5 W4 conductor hardening. Becomes the canonical smoke test going forward.

**Gotcha:** aho-G065 workstream "pass" requires post-install verification on the target machine, not just code generation.

---

## What stays the same

- Phase 0 charter and Pillars
- Bundle structure (§1–§26)
- iao secrets model
- Conductor 7-span pipeline (it works, leave it alone except for the smoke test definition)
- All of W2/W3/W4 from 0.2.3 except the harness-watcher deployment gap
- All of W0–W4 from 0.2.4

## Open questions for Kyle before plan-doc execution

1. **Pacman subset confirmation:** the proposed subset (fish, tmux, git, base-devel, python, python-pip, age, nodejs, npm, jq, ripgrep, fd, htop) is my best guess. Need Kyle to add/remove items by inspecting his actual `pacman -Qqe` output. install.fish cannot ship until this list is locked.

2. **AUR subset:** confirm empty for aho proper, or name the AUR packages aho actually requires.

3. **`bin/aho-install` rename:** keep the name and let install.fish call it as one step? Or rename to `bin/aho-bootstrap` for clarity? Lean: rename. The current name is confusing now that install.fish is the top-level entry point.

4. **Telegram scaffolding:** confirm the first-run flow is "create directory + placeholder + halt with capability-gap message telling Kyle to drop the token in." No interactive prompts.

5. **Smoke test path:** Path A or Path B above. Lean Path B.
