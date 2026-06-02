# Proposed Council Tenets (June 2026 Draft)

Based on the Sea Gypsy multi-pass debate work and the development of the naval crew model.

## Core Principles

1. **The human is Captain.**  
   The user sets the destination and overall intent. The crew executes and proposes improvements, but the Captain always holds final authority on direction and major decisions.

2. **This is a small ship with defined roles.**  
   We operate with a standing crew of specialized models using naval roles (Navigator, Helmsman, Bosun, Seaman, Quartermaster) plus temporary Coxswains when needed. Roles are explicit, and the crew is expected to be flexible on a small vessel.

3. **The crew improves the process.**  
   Models are not just executors of prompts. They are expected to critique previous runs, identify process waste or failure modes, and propose improvements to how the council works (Quarterdeck / After Action reviews).

4. **Every pass builds on the latest version.**  
   Strict cumulative discipline. No falling back to older baselines. Each major improvement cycle must start from the most recent best artifact and produce the next numbered version.

5. **Clear separation between core and project.**  
   Core harnesses, tooling, roles, and reusable functions live in the main aho repository. Per-project work (customer data, specific artifacts, iteration outputs) lives in ephemeral workspaces (`tmp/`) and eventually migrates out.

6. **Quartermaster is essential.**  
   Retrieval and semantic memory (nomic) is not optional. The Quartermaster maintains the "stores" and must be actively consulted for relevant context from source material.

7. **Generation and evaluation remain separate.**  
   (Retained from original Pillar 7) The model that produces work should not be the only one evaluating it. Multiple roles should review.

8. **The human holds the keys.**  
   (Retained and strengthened from original Pillar 11) No agent writes to git, merges, pushes, or manages secrets without explicit human approval.

9. **Small models + strong process beats big model + weak process.**  
   We optimize for what small, role-specialized, always-hot models can do reliably when given good structure, clear roles, and iterative feedback — not for what one giant model might do in a single shot.

10. **Versioning and traceability matter.**  
    We still believe in the spirit of the three-octet system (phase.iteration.run) for major work. At minimum, we maintain clear, cumulative versioned artifacts so progress is visible and auditable.

---

## Notes for Discussion

- Several original pillars around wrappers, durable transitions, and interrupt discipline feel less central now that we're running long, multi-round debate processes on local models.
- New emphasis on crew self-improvement and role clarity emerged strongly from the Sea Gypsy work.
- The "small ship" metaphor has proven very useful for explaining flexibility, rotation, and why everyone chips in.

This is a starting proposal for discussion. What feels right? What should be added, removed, or reworded?
