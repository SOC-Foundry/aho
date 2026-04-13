# 0.2.15 Planning Inputs — Surfaced during 0.2.14 close session

Not part of 0.2.14 acceptance archive. Material that emerged in W2 close conversation and belongs in 0.2.15 planning context.

## Fleet topology

Fleet as of 0.2.14 close:
- **A8cos** — AMD APU integrated GPU; Tier 0 (orchestration/dev, daily driver)
- **NZXTcos** — RTX 2080 SUPER 8GB; Tier 1 (partial council)
- **tsP3-cos** — RTX 2000 Ada 16GB; Tier 2 (live aho host, aho.run target, full council)
- **Luke's machine** — 24GB GPU; Tier 3 (first 24GB clone, matrix headroom baseline); spec request sent to Alex
- **Intranet GCP project** — unlimited; Tier ∞ (future cloud burst)

Strategic decision (tentative): move daily-driver work to A8cos, dedicate tsP3-cos to aho for reproducible matrix baselines. Resource isolation during calibration phase.

## Tiered install system

install.fish refactor into detection-based tiers:
- **Tier 0 (Minimal):** aho CLI, harness, MCP, middleware, gotcha registry, event logging. No council models.
- **Tier 1 (Partial / 8GB):** Tier 0 + Qwen 3.5:9B + Llama 3.2 3B. No 12B+ models.
- **Tier 2 (Full / 16GB):** Tier 1 + Gemma 2 9B + DeepSeek-Coder-V2 16B-Lite Q4 + Mistral-Nemo 12B.
- **Tier 3 (Full+ / 24GB+):** Tier 2 + Q5/Q6 quantizations + multi-model concurrent loading.
- **Tier ∞ (Cloud):** Intranet GCP, separate deployment model.

install.fish has never been tested on fresh CachyOS. Likely hidden "already set up" assumptions. First fresh-install test on A8cos (Tier 0, lowest blast radius).

## Multi-iteration arc: 0.2.16-0.2.18

Fleet bootstrap sequencing (tentative):
- **0.2.16** — Tiered install spec + A8cos bootstrap (Tier 0)
- **0.2.17** — Luke's machine bootstrap (Tier 3) + matrix headroom testing
- **0.2.18** — tsP3-cos refresh / clone bootstrap (Tier 2 production) + aho.run hosting

0.2.15 measurement matrix must precede fleet bootstrap so roster decisions are evidence-based before clones happen.

## Cross-project contamination (process risk)

Observed during 0.2.14 W2 drafting: kjtcom bundle version label (v10.66) bled into aho W2 prompt via memory recall. Risk pattern: chat recalls "bundle spec" and can pull from kjtcom's more mature artifact without flagging project-origin.

Mitigation candidates:
- Project-scoped version labels with explicit prefix (aho-bundle-spec-v1, never v10.66)
- Harness contract rule: any version reference verifies against current project's canonical spec file
- Explicit project-boundary checks when memory recall crosses projects
- 0.2.15 pre-W0 workstream candidate: audit aho artifacts (harness, ADR numbering, gotcha registry, bundle spec, install.fish) for kjtcom-pattern contamination. Identify aho-native vs inherited-intentional vs inherited-accidental.
