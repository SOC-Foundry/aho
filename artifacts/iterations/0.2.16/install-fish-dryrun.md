# install.fish Tier 1 Dry-Run — NZXTcos (0.2.16 W0)

**Date:** 2026-04-21
**Host:** NZXTcos
**Iteration:** 0.2.16 W0
**Purpose:** Evidence that install.fish Tier 1 section produces clean output on the Tier 1 reference host, finalizing the deliverable 0.2.15 W4 deferred.

## Scope of this dry-run

Read-only subcommands of `bin/aho-models` (`list`, `status`, `doctor`, `vet`) plus source inspection of `bin/aho-models` and `install.fish` platform-check block. **`aho-models install` is not run** on a fresh machine during a live iteration session — NZXTcos has the full Tier 1 set pulled from prior iterations, so re-pulling is a no-op with network cost. The `install` code path is verified by source inspection and by the `vet` smoke probe (which exercises the full /api/chat dispatch path per model and would fail fast on any missing model).

## Host identity

| Identifier | Value | Source |
|---|---|---|
| Hostname | NZXTcos | `hostname` |
| Architecture | x86_64 | `uname -m` |
| OS | Arch Linux | `/etc/arch-release` present |
| Shell | fish 4.6.0 | `fish --version` |
| GPU VRAM total | 8192 MiB | `nvidia-smi --query-gpu=memory.total` |
| GPU VRAM used at start of dry-run | 49 MiB | `nvidia-smi` (after post-probe unload) |

NZXTcos meets the Tier 1 minimum (x86_64 Arch + 8GB VRAM).

## Tier 1 roster (finalized)

Per `artifacts/harness/model-fleet.txt` after 0.2.16 W0 update:

```
qwen3.5:9b
llama3.2:3b
haervwe/GLM-4.6V-Flash-9B:latest
nemotron-mini:4b
```

Derived from 0.2.15 W0 `tier1-roster-validation-0.2.15.json`:
- qwen3.5:9b — **operational**, role: Producer/Assessor.
- llama3.2:3b — **operational**, first 0.2.15 W0 integration; role: Indexer (fast triage).
- haervwe/GLM-4.6V-Flash-9B:latest — **partial (retain)**; role: Auditor. Requires `num_gpu=30` partial offload at 8GB (full 41-layer offload OOMs).
- nemotron-mini:4b — **compromised (retain w/ caveat)**; classifier/triage-only role. 0.2.15 W4 F004 confirmed unsuitable for Assessor.

### Explicit "not installed at Tier 1" roster

Documented in `artifacts/harness/model-fleet.txt` comments. Listed here for sign-off visibility:

- `nomic-embed-text:latest` — RAG stack; deferred to 0.2.17 per 0.2.15 carry-forward. Endpoint coexistence with chat was validated in 0.2.15 W1 R12, but retrieval plumbing is not wired. The fleet file previously included this entry; removed from Tier 1 installation during 0.2.16 W0 to match the carry-forward decision.
- `gemma2:9b` — Tier 2+; >8GB VRAM. Waits on Luke's machine or P3 clones.
- `deepseek-coder-v2:16b-lite` — Tier 2+; >8GB VRAM.
- `mistral-nemo:12b` — Tier 2+; >8GB VRAM.

## Dry-run output

### `aho-models list`

```
qwen3.5:9b
llama3.2:3b
haervwe/GLM-4.6V-Flash-9B:latest
nemotron-mini:4b
```

### `aho-models status`

```
  [pulled]  qwen3.5:9b
  [pulled]  llama3.2:3b
  [pulled]  haervwe/GLM-4.6V-Flash-9B:latest
  [pulled]  nemotron-mini:4b
[aho-models] 4 pulled, 0 missing out of 4 declared models
```

4/4 — all Tier 1 models present.

### `aho-models doctor`

```
[aho-models] All 4 declared models present.
```

Exit 0. Clean.

### `aho-models vet` (smoke probe — new in 0.2.16 W0)

First run with initial `num_predict=32` **surfaced a real finding**: Qwen emitted 0-char content because thinking-mode consumed the full 32-token budget — a scaled-down reproduction of the 0.2.15 W4 cascade failure mode. Fix: raised smoke-probe `num_predict` to 256 (150-200 tokens for thinking + brief content). Re-run:

```
[aho-models] Vet qwen3.5:9b ...
[aho-models]   qwen3.5:9b emitted 2 chars — ok
[aho-models] Vet llama3.2:3b ...
[aho-models]   llama3.2:3b emitted 2 chars — ok
[aho-models] Vet haervwe/GLM-4.6V-Flash-9B:latest ...
[aho-models]   haervwe/GLM-4.6V-Flash-9B:latest emitted 32 chars — ok
[aho-models] Vet nemotron-mini:4b ...
[aho-models]   nemotron-mini:4b emitted 77 chars — ok
[aho-models] All 4 Tier 1 models passed smoke vet.
```

4/4 models dispatched and returned non-zero-char content via `/api/chat`.

## install.fish platform checks

Inspection of `install.fish:88-107`:

- Arch Linux check — `test -f /etc/arch-release` — halt if absent.
- fish shell check — `type -q fish` — halt if absent.
- x86_64 check — `test (uname -m) = "x86_64"` — halt if not.

All three pass on NZXTcos.

## New `bin/aho-models` capabilities (0.2.16 W0)

Source changes committed to `bin/aho-models`:

1. **`_check_vram`** — precondition for `install` subcommand. Reads `nvidia-smi --query-gpu=memory.total`; halts if absent, unreadable, or below 8000 MiB. Run before any `ollama pull`.
2. **`vet` subcommand** — per-model smoke probe via `/api/chat` with `num_predict=256`. Reports chars per model. Exit non-zero on any 0-char model.
3. **Ollama systemd note** — inline comment in `_check_ollama` now references that Ollama runs at system-level systemd (`/etc/systemd/system/ollama.service`), **not user**, so restart requires sudo. (From 0.2.15 W1 F008 / E2; documented where users hit permission walls.)
4. **Fleet-file expansion** — Tier 1 section marked, "not installed" roster preserved as comments with rationale.

## Findings surfaced by the dry-run

### Substrate hygiene — positive

- Clean VRAM baseline (49 MiB used at start, no resident models) met the 0.2.15 baseline-contamination-protocol criterion. No contamination risk during dry-run measurements.
- Ollama up and responsive on :11434.

### Vet smoke probe proved its worth on first run

- `num_predict=32` exhausted Qwen thinking-mode → 0-char content. Surfaced at dry-run time. Fix landed in-place (raise to 256). The probe effectively catches dispatcher-regression-at-install-time — it would have caught the 0.2.15 W4 substrate failure if this vet existed then.

### Dispatch path changes committed during the same W0

- `src/aho/pipeline/dispatcher.py` Qwen `num_predict=2000 → 8000` is what resolves the cascade-scale Producer failure; the smoke-vet `num_predict=256` is a separate smaller-scale budget for the install-time check.

## Out of scope for this dry-run

- Fresh-host install from zero (no Ollama, no models). That's covered by `bin/aho-pacman`, `bin/aho-aur`, `bin/aho-python` wrappers exercised during a real clone-to-deploy. W0 scope is finalizing the Tier 1 section, not running a fresh install from zero.
- Tier 2/3 model pulls (out of Tier 1 scope).
- RAG stack / nomic-embed-text wiring (0.2.17 carry-forward).

## Sign-off-ready state

- Tier 1 fleet declared and present on NZXTcos.
- `install.fish` delegates per-step; platform checks pass; Step 4 (`aho-models install`) gated behind VRAM precheck and Ollama liveness check.
- Smoke vet covers all 4 models.
- Explicit "not installed" list documented in the fleet file comments.
- One real finding (Qwen vet budget) surfaced and resolved in-place.
