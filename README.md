# aho (Fresh Start)

**Governance infrastructure for LLM-driven engineering — rebuilt around local models.**

This is a clean pivot after archiving the 0.3.x legacy implementation.

## Current Direction

We are building a new, lean, hardware-aware **Ollama multi-model council** using role-specialized models instead of one giant frontier agent.

Focus areas for this phase:
- Practical simultaneous model loading on consumer GPUs (starting with 8GB, targeting 16GB+)
- Role-specialized prompting (triage, auditor, embedder, producer, vision)
- Preserving and evolving the real institutional memory (Pillars + Gotcha Registry)
- Idempotent deployment and verification tooling for multi-machine fleets

## Repository Structure (Post-Archive)

```
.
├── archive/0.3.2/               # Complete legacy from the 0.3.x era
│   └── artifacts-legacy/        # All old iterations, tests, code, etc.
├── artifacts/                   # The preserved core wisdom
│   ├── harness/                 # Pillars (base.md), adversarial authorship, etc.
│   ├── adrs/                    # Architectural decisions worth carrying forward
│   └── gotcha_archive.json      # Institutional memory of failure modes + mitigations
├── bin/
│   ├── aho-ollama-global.fish   # Global multi-user Ollama + models installer
│   └── aho-ollama-verify.fish   # Functional + VRAM smoke tests
├── harness/                     # New harness definitions (role instructions, routing)
├── council/                     # New council implementation (model wiring, orchestration)
├── docs/                        # Light documentation + historical handoffs
└── README.md
```

## Preserved Value

The things worth carrying forward from years of work:

- **The Pillars** — Especially cost-delta measurement, human holds the keys, substrate probing, and host fungibility.
- **Gotcha Registry** — 37+ indexed failure modes with mitigations.
- **ADR discipline** and the better architectural decisions.
- The philosophy of **rich harnesses over raw model intelligence**.

The full historical record (all iterations, acceptance archives, etc.) lives in `archive/0.3.2/artifacts-legacy/`.

## Current Tooling

- `bin/aho-ollama-global.fish` — One-shot system-wide Ollama (systemd service + ollama user + shared /var/lib/ollama) + fleet pull. Now includes built-in post-deploy `ollama list` validation + minimal generate/embed smoke test that runs automatically after the last model finishes.
- `bin/aho-ollama-verify.fish` — Deeper functional + VRAM snapshot verification (light core by default; `--all` for heavies). Use after the global installer or for ongoing health.

These were developed on an 8GB RTX 2080 SUPER baseline and are running on the current 16 GB development host (RTX 2000 Ada). The declared fleet is conservative for 16 GB; simultaneous loading capacity will be measured next.

### Global Engagement (outside the aho repo)

Running `./bin/aho-ollama-global.fish` (under sudo) does two things for "council from anywhere":

1. Deploys the full Ollama system service + all models (visible to every user via `ollama list` / `OLLAMA_HOST`).
2. Installs stable shims for `aho`, `aho-conductor`, and `aho-ollama-verify` into the invoking user's `~/.local/bin/`, plus ensures that directory is on their `fish` PATH.

After the global run + re-login (or `exec fish`):
- You can type `aho-conductor dispatch "..."` or `aho ...` from **any** directory on the machine.
- The (future) lean Ollama council implementation will be reachable without per-project setup or being inside this checkout.

This fulfills the long-standing requirement that the LLM council can be engaged from Claude Code (or other agents) in unrelated projects. See the handoff prompt in `docs/` for the original contract.

## Hardware Context

- Current development host (this clone): **16 GB VRAM** (NVIDIA RTX 2000 Ada) — this is the "p3cos" class machine from prior audits.
- The scripts + README still reference the 8 GB baseline for conservatism; actual simultaneous capacity on 16 GB will be measured with the new verify tooling.

See `artifacts/aho-fresh-start-current-state-audit-2026-05-30.md` (and the p3cos reference it compares against) for the full before/after analysis of the legacy reset.

## Next Steps (Overnight-Friendly)

1. **Fire up the installer overnight** (dedicated 16GB version):
   ```
   tmux new -s aho-ollama
   sudo fish ./bin/aho-ollama-global-16gb.fish
   ```
   This version is tuned for your RTX 2000 Ada 16GB. It pulls a rich role-specialized fleet (Phi-4 14B, Qwen3 8B for evaluation, DeepSeek R1 14B, small specialized models, vision, nomic RAG + one extra heavy) and runs individual smoke tests with aggressive VRAM offloading between each model.
   The script will:
   - Set up the system-wide Ollama service + fleet
   - Run the built-in `ollama list` validation + generate/embed smoke
   - Install `aho` / `aho-conductor` / `aho-ollama-verify` shims into `~/.local/bin` (with PATH)
2. Morning: re-login (or `exec fish`), then from **any directory**:
   ```
   ollama list
   aho-ollama-verify
   ./bin/aho-ollama-verify.fish --all   # if desired
   ```
   You should also be able to run `aho-conductor` (once the new council dispatcher is wired) from any project.
3. Use the measured VRAM numbers + successful smoke to design the role-specialized harness in `harness/` and the new council router in `council/`.
4. Evolve the preserved `artifacts/harness/base.md` Pillars + `gotcha_archive.json` into the living contract for the lean Ollama council.

---

**This is no longer the old heavy Python council.**  
We're starting fresh with local models, real hardware constraints, and the parts of the old work that actually mattered.

Legacy code and full history: `archive/0.3.2/`