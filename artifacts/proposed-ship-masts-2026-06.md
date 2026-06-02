# Proposed Ship Masts (June 2026 Draft)

**Status:** First draft for discussion  
**Context:** Reframing the original 11 Pillars using the naval crew metaphor that has proven effective during the Sea Gypsy multi-pass council work.

## Core Metaphor

We operate as a **small ship**. 

The human is the **Captain** — sets the destination, holds ultimate authority, and performs all git operations.

The models form a standing crew with clear roles (Navigator, Helmsman, Bosun, Seaman, Quartermaster). External specialists can be brought aboard temporarily as **Coxswains**.

On a small ship, roles must be respected but everyone is expected to chip in when needed. The crew is responsible not only for executing the voyage but for continually improving how the ship sails.

---

## The Ship Masts

### 1. The Captain Holds the Keys
The human (Captain) sets the overall intent and destination. The Captain alone performs all git add, commit, push, merge, and secret management actions. No model ever writes to the repository or manages credentials.

### 2. We Operate as a Small Ship
We maintain a deliberately small standing crew with clear naval roles. This requires clarity of responsibility while demanding flexibility — everyone must be willing to chip in when needed on a small vessel. External specialists (Coxswains) are brought aboard only for specific sub-tasks requiring unique expertise.

### 3. Each Voyage Builds on Previous Journeys
We maintain strict cumulative discipline. Every major pass starts from the most recent best version and produces the next numbered version. We do not reset or fall back to older baselines. Progress is measured by the quality and coherence of the latest artifact, which itself builds on all previous journeys.

### 4. Clear Separation Between Ship and Cargo
Core reusable harnesses, tooling, roles, and functions belong to the ship (the aho repository). Per-project work, customer data, iteration artifacts, and temporary experiments belong to the cargo and live in ephemeral workspaces (`tmp/`). The cargo moves with the project (e.g. to tteos); the ship remains.

### 5. The Quartermaster Is Never Optional
Retrieval and semantic memory (Quartermaster / nomic) is a standing crew role. When context from source material is needed, the Quartermaster must be consulted. Crude heuristics and page guessing are not acceptable substitutes for proper retrieval.

### 6. Generation and Evaluation Are Separate Roles
The model (or role) that produces work should not be the sole evaluator of that work. Multiple roles should participate in review. Self-grading bias is actively countered.

### 7. Efficacy Is Measured in Real Cost and Quality
Every significant run tracks wall-clock time, local compute, token usage (where relevant), and output quality signals. We optimize for practical results on real hardware, not theoretical capability.

### 8. The Gotcha Registry Is the Ship’s Memory
Every significant failure mode, process breakdown, or recurring problem is recorded in the Gotcha Registry. A healthy ship accumulates institutional memory. New voyages should consult the registry before repeating old mistakes.

### 9. Runs Are Iterative Feedback Loops
The crew reviews its outputs and continually improves not only the project-specific tasks at hand, but also extracts and codifies system-wide instruction sets and processes developed during each project. These reusable patterns are captured and made available for future voyages, turning project-specific learning into enduring ship-wide capability.

---

## Notes on This Draft

- Reframed as **Ship Masts** and reduced to 9 core tenets.
- Strengthened the "small ship" concept as a defining characteristic (Mast 2).
- Removed the previous Mast 3 ("The Crew Improves the Process") and the old Mast 11 ("Small-Ship Flexible") per direction.
- Renamed and strengthened Mast 4 to "Each Voyage Builds on Previous Journeys" to emphasize cumulative progress across multiple passes.
- Strong emphasis remains on role clarity, cumulative versioning discipline, Quartermaster as a required role, separation of ship vs cargo, and human authority over git/credentials.
- Mast 9 reframed as "Runs Are Iterative Feedback Loops" to capture the crew's responsibility to extract reusable system-wide processes from project work for future use.

---

**This is a discussion draft.** 

What feels right? What feels off? What should be added back or adjusted?

We can iterate before updating the authoritative `artifacts/harness/base.md`.