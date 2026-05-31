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

- `bin/aho-ollama-global.fish` — One-shot system-wide Ollama + recommended model fleet deployment (multi-user).
- `bin/aho-ollama-verify.fish` — Quick functional + VRAM usage verification across the council models.

These were developed on an 8GB RTX 2080 SUPER machine and are designed to travel to better hardware.

## Hardware Context

- Primary development machine (this repo): 8GB VRAM (base tier)
- Target machine (p3cos): 16GB VRAM (partial tier) — significantly better simultaneous model capacity

## Next Steps

1. Clone this repo to the 16GB machine.
2. Run the global Ollama installer + verification.
3. Design the new council roles and model routing matrix based on actual measured simultaneous capacity.
4. Systematically review and evolve the preserved Pillars + Gotcha Registry into the new harness.

---

**This is no longer the old heavy Python council.**  
We're starting fresh with local models, real hardware constraints, and the parts of the old work that actually mattered.

Legacy code and full history: `archive/0.3.2/`