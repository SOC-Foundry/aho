# aho Fresh-Start Current-State Audit — Post-Cleanup Clone
**Date of audit:** 2026-05-30 (evening, post-clone)  
**Checkout location:** `/home/kthompson/Development/Projects/socfoundry/aho` (updated clone)  
**Git HEAD:** `907a8ee` — "Big cleanup: Archive 0.3.x legacy + fresh start for new Ollama council" (origin/main)  
**Prior reference:** `aho-p3cos-current-state-audit-2026-05-30.md` (p3cos tree at `00c9264`, 0.3.1 claims, VERSION=0.2.14)  
**Purpose:** Objective snapshot of the "updated repo" after the explicit legacy archive + reset. Focus on whether the highest-risk gaps from the p3cos audit were closed by the pivot, what new drift was introduced in the cleanup commit, and readiness of the new Ollama global deployment path.

This report is deliberately constructively critical and treats the fresh start as the new baseline under the preserved Pillars and harness contracts.

---

## 1. Git Provenance & Working Tree (Radical Minimalism)

| Aspect                  | Observation |
|-------------------------|-------------|
| Remote                  | `git@github-socfoundry:SOC-Foundry/aho.git` (origin/main) |
| Branch / HEAD           | `main` @ `907a8ee` (the cleanup itself) |
| Prior commits visible   | 0.3.1 "KT completed" series + earlier 0.2.x still in history |
| Uncommitted / staged    | Clean (per initial snapshot + no edits yet) |
| VERSION file            | **Deleted** (was stale at 0.2.14; correct resolution for fresh start) |
| Files deleted in cleanup| 1000+ (src/, Dockerfile, GEMINI.md, CHANGELOG, MANIFEST, old .mcp, logs, many iteration artifacts) |
| archive/ directory      | **Documented in README but absent** from both working tree and the 907a8ee tree. `.gitignore` now protects `archive/` as "local only". Full history lives only in git objects. |

**Key difference from p3cos audit:** The old tree was bloated with partial 0.3.x implementation + untracked debug. This tree is intentionally skeletal — the "fresh start" is real on disk.

---

## 2. Resolution of p3cos Audit Highest-Risk Items

The p3cos audit's #1 risk was:

> "The cross-host Ollama transport layer (get_ollama_base + client updates + partial routing table entries) — this is the explicit justification for the 0.3.1 early close..."

**Status in fresh start: CLOSED BY ARCHITECTURAL RESET (not by implementation).**

- `get_ollama_base`, `AHO_OLLAMA_BASE`, `ollama.peer`, the Python `dispatcher.py` / `qwen_client.py` / `glm_client.py` / `nemotron_client.py` / `council/dispatch.py` ROUTING_TABLE, `tier_manifest.py` TIER_BUNDLES, fragmented GLM tags ("GLM-4.6V-Flash-9B" vs real `haervwe/GLM-4.6V-Flash-9B:latest`), preflight/doctor substring heuristics — **all of this code is gone**.
- No more 404s from model ID mismatches on a host Ollama that only had llama3.2:3b + nomic.
- The old "council global-use wiring" claims that were only partially landed are now moot.
- `src/aho/` no longer exists. `council/` and `harness/` are now tiny placeholder dirs whose READMEs explicitly say "start fresh here based on the preserved wisdom in `artifacts/`".

**Remaining related surface (legacy only):**
- `bin/aho-models`, `bin/aho-models-status`, `bin/aho-doctor`, `bin/aho-probe-substrate` etc. still contain `http://localhost:11434` and reference the deleted `artifacts/harness/model-fleet.txt`.
- Old docs (`docs/operations/council-global-use.md`, `docs/aho-council-handoff-prompt.md`) describe the pre-pivot architecture.
- These are noise, not load-bearing for the new path.

---

## 3. The New Ollama Council Path (What Actually Ships Now)

Two new fish scripts are the only load-bearing deployment artifacts for the "new Ollama council":

- `bin/aho-ollama-global.fish` — System-wide Ollama (dedicated `ollama` user + `/etc/systemd/system/ollama.service` + `/var/lib/ollama` models dir + `/etc/fish/conf.d/ollama.fish` for all users). Pulls a curated 8GB-VRAM-friendly fleet last.
- `bin/aho-ollama-verify.fish` — VRAM snapshots + basic + structured-JSON + embedding functional tests per model. Has `--all` / `--quick` / single-model modes.

**Current declared fleet (inside global.fish):**
```
phi4-mini
nomic-embed-text
qwen3-embedding:0.6b
qwen3:4b
qwen3:8b
qwen3.5:35b-a3b   # MoE, pulled last, "may take 30-90+ minutes"
```

**Hardware reality on this clone host:**
- `nvidia-smi`: NVIDIA RTX 2000 Ada Generation, **16380 MiB** (16 GB VRAM).
- The scripts and README still talk exclusively about "8GB VRAM (RTX 2080 SUPER)" as the development target. The 16 GB machine (p3cos in the prior audit) is now the actual checkout host. Model list is therefore conservative for this hardware.

**Ollama service posture (new):**
- Binds `OLLAMA_HOST=127.0.0.1:11434` (good, explicit).
- Models dir owned by ollama:ollama under /var/lib.
- Global fish users get OLLAMA_HOST exported.
- Conflicts with any prior user-level `ollama.service` are explicitly stopped during install.

This directly satisfies several p3cos-era gaps: consistent endpoint, no more per-script localhost assumptions in the *new* path, proper multi-user, systemd durability.

**Gap vs p3cos intent:** Cross-host (tailnet / p3cos as heavy producer for other base hosts) is not addressed yet. The fresh start is deliberately "single-host global first, prove simultaneous loading on real 16 GB hardware, then design the council roles/routing matrix."

---

## 4. Documentation vs Implementation Fidelity (New Drifts Introduced)

**Good fidelity:**
- `artifacts/harness/base.md` (Pillars), `adversarial-authorship-protocol.md`, `gotcha_archive.json` (474 lines), and the 15 ADRs are untouched and correctly positioned as the preserved core.
- One retrospective (`docs/retrospectives/0.2.17.md`) survives.
- The p3cos audit artifact itself was carried forward in the clone (still in repo root).

**New drift / hygiene issues created by 907a8ee:**
1. **README promises non-existent archive/**: "The full historical record ... lives in `archive/0.3.2/artifacts-legacy/`." Neither the directory nor any extracted legacy tree exists in the commit or on disk. `.gitignore` now hides it. Operators following the README will be confused.
2. **p3cos audit md left in root**: Valuable as the anchor for this exact comparison, but it is now an orphan dated artifact. Should live under `artifacts/audits/`.
3. **Legacy bin/ scripts are broken**: `aho-models` will immediately fail ("Fleet file not found") and still hardcodes old localhost + old model names. Same for doctor, probe-substrate, etc. They were not archived or updated.
4. **Retrospective coverage still thin**: Only 0.2.17 survives the cull. The "efficacy is measured" Pillar is harder to honor without more historical signal.
5. **Hardware numbers in scripts/README lag reality**: 8 GB assumptions everywhere on a 16 GB host.

**Internal-only policy still respected**: No tt-*, drafter-context, or CLAUDE/GEMINI.md in the tree (the cleanup removed the latter two).

---

## 5. Recommended Comparison Checklist (Updated for Fresh Start)

Run these on any future clone and diff against this report + the p3cos reference:

1. `git log --oneline -1` → must be 907a8ee or later cleanup descendant
2. `test -f VERSION && echo stale || echo absent` (absent = correct)
3. `test -d archive && echo "archive present (unexpected)" || echo "archive absent (as designed)"`
4. `git grep -l "get_ollama_base\|AHO_OLLAMA_BASE" -- . ':(exclude).git' | wc -l` → 0 expected
5. `git grep -E "http://(localhost|127.0.0.1):11434" -- bin/aho-ollama-*.fish` → only the two new controlled files
6. `ls artifacts/harness/` → base.md, adversarial-*.md, gotcha_archive.json, prompt-conventions.md, secrets-architecture.md (no model-fleet.txt)
7. `./bin/aho-ollama-global.fish --help 2>&1 | cat` (or just read it) and confirm MODELS array
8. `ls docs/retrospectives/` → only 0.2.17.md
9. `test -f artifacts/aho-fresh-start-current-state-audit-2026-05-30.md && echo present`
10. `nvidia-smi --query-gpu=memory.total --format=csv,noheader` (document the actual VRAM for the fleet choice)
11. After running the global installer: `ollama list` + `./bin/aho-ollama-verify.fish`

---

## 6. Positive Observations

- The reset was decisive and honest about the state of the 0.3.1 "wiring."
- New deployment tooling (global + verify) is written in fish, matches the operator's actual shell, produces real systemd durability, and includes VRAM telemetry — a clear improvement over the old Python preflight/doctor heuristics.
- The preserved artifacts/ tree is high-signal and small.
- The p3cos audit md was not lost in the clone; it is the exact reference we needed for this comparison.

---

## 7. Risk / Action Items (Prioritized)

**High (do before relying on the new council):**
- Populate or remove the false `archive/` claim in README + consider actually extracting a useful subset of 0.3.x history into a local-only tarball or git subtree if operators will need the old council-models-0.2.14.md details.
- Move `aho-p3cos-current-state-audit-2026-05-30.md` into `artifacts/audits/`.
- Either delete/rename the broken legacy `bin/aho-models*` + `aho-doctor` family or give them a "legacy-" prefix and update their comments to point at the two new ollama-*.fish scripts.
- Update all 8 GB / RTX 2080 SUPER comments + the fleet list itself to reflect the actual 16 GB development host (or make the fleet configurable by detected VRAM).

**Medium:**
- Add the post-deploy `ollama list` + smoke test to `aho-ollama-global.fish` (this task's explicit request).
- Add at least one more retrospective (0.3.x lessons + the substrate pivot decision) so the "harness is the contract" claim has living memory.
- Decide the long-term story for cross-host / partial-tier council (the original justification for the p3cos machine). The new lean council on 16 GB should make the capacity math clearer.

**Low:**
- The single remaining retrospective is a historical fact, not a crisis.

---

## 8. Summary

The cloned "updated aho" is materially different from the p3cos tree in exactly the way the cleanup message advertises: the half-implemented, localhost-fragmented, cross-host-claimed-but-not-delivered 0.3.x council has been excised. What remains is a clean, minimal skeleton + two new fish scripts that actually install and verify a real multi-model Ollama service for all users.

The highest-risk item from the p3cos audit is closed (by deletion + reset, not by finishing the transport layer). New hygiene drifts were introduced in the cleanup commit itself (README vs reality on archive/, legacy scripts left in broken state, hardware numbers not updated).

This tree is ready for the next phase: run the global installer on the 16 GB host (overnight, with the 35b-a3b MoE last), validate with `ollama list`, execute the built-in smoke, then use the measured simultaneous capacity to design the actual role-specialized harness and router in `harness/` and `council/`.

**Session update (same evening):** As part of this audit + handoff, the post-deploy `ollama list` validation + minimal generate/embed smoke test was implemented directly in `bin/aho-ollama-global.fish`. Later the same evening the global installer was further extended with `_install_aho_cli_surface` (plus `project_root` detection and PATH setup) so that `aho`, `aho-conductor`, and `aho-ollama-verify` become available in `~/.local/bin` from any directory after the run — directly addressing the requirement that the LLM council can be engaged *outside* the aho checkout. README and audit updated.

The p3cos audit artifact served its purpose perfectly as the reference for this comparison.

**End of report.**