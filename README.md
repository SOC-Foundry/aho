# aho

**Governance infrastructure for LLM-driven engineering on local hardware.**

## What is AHO

AHO is a disciplined system for doing serious engineering work with small, role-specialized local models instead of relying on one giant frontier model.

The core idea is simple but powerful:

- The **Captain** (you) sets the destination and overall intent.
- A rotating **Navigator** translates that intent into concrete orders.
- A small standing crew of specialized models (Helmsman, Bosun, Seaman, Quartermaster) executes the work.
- External specialists (Coxswain) are brought in temporarily when unique expertise is required.

This is not prompt engineering. It is crew engineering.

## How It Works - The Naval Council Model

AHO runs as a small-ship crew rather than a traditional “one model does everything” setup. The structure uses explicit naval roles so that responsibilities, accountability, and rotation are clear.

### Core Standing Crew (always-hot on 16 GB)

- **Helmsman** (`hermes3:3b`): The primary steering role. Responsible for the actual high-quality drafting, rewriting, and repair work. This is the model that does the heavy lifting on producing refined output.
- **Bosun** (`qwen2.5:3b`): Handles repairs and process discipline. Owns fixing structural problems in the work (broken sections, duplication, inconsistent quality, etc.) and enforcing standards.
- **Seaman** (`gemma2:2b`): The flexible generalist. Good at a wide variety of specific tasks, quick scans, and triage. Can be thrown at many different jobs.
- **Quartermaster** (`nomic-embed-text`): Maintains the “stores” and charts. Provides semantic retrieval and memory over source material (the PDF in the Sea Gypsy case), tracks what has been addressed, and supplies precise context when the rest of the crew needs it.

### Rotating / Ephemeral Roles

- **Navigator**: The current executor of a major task. Translates the Captain’s intent into concrete orders for the crew and keeps the overall effort on course. This role is deliberately ephemeral and rotates. Grok currently fills it for most work, but Claude or Gemini can step in.
- **Coxswain**: A temporary specialist brought in by the Captain or Navigator for specific sub-tasks that require unique expertise the standing crew doesn’t have (advanced reasoning, long-context work, coding, domain knowledge, etc.). The Coxswain operates for a defined scope and then stands down. This role can be filled by Claude, Gemini, or even Grok depending on the need.

Here is the current role assignment:

| Role              | Model                          | Notes |
|-------------------|--------------------------------|-------|
| Captain           | Human (user)                   | Ultimate authority. Sets the destination and overall intent. |
| Navigator         | Rotating (Grok, Claude, Gemini, etc.) | The current executor of a major task. Translates the Captain’s intent into concrete orders for the crew. This role is ephemeral and rotates depending on who is steering a given voyage. |
| Helmsman          | hermes3:3b                     | Primary steering. Responsible for the actual high-quality work of moving the project forward and producing refined output. |
| Bosun             | qwen2.5:3b                     | Repairs issues that arise (structural problems in the text, broken processes, duplication, etc.). Maintains standards and process discipline. |
| Seaman            | gemma2:2b                      | Most flexible generalist. Good at a variety of specific tasks but less optimal for heavy multitasking or long-horizon strategy. |
| Quartermaster     | nomic-embed-text               | Maintains the “stores” and charts. Responsible for retrieval, semantic memory of source material, versioning discipline, and providing precise context to the rest of the crew. |
| Coxswain          | Claude / Gemini / Grok (as needed) | Temporary specialist brought in by the Captain or Navigator for specific sub-tasks that require unique expertise not covered by the core crew. Operates for a defined scope and then returns to shore. |

This small-ship model forces flexibility. The Navigator sometimes has to chip in on execution, the Helmsman is expected to follow orders but can also surface process problems, and external Coxswains can be called in without bloating the always-hot crew. The goal is disciplined, role-aware collaboration rather than one giant prompt.

## The Eleven Pillars

These remain the foundational operating principles (sourced from `artifacts/harness/base.md`). They have not been significantly revised since earlier work with Claude and are likely due for an update.

1. Delegate everything delegable.
2. The harness is the contract.
3. Everything is artifacts.
4. Wrappers are the tool surface.
5. Three octets, three meanings: phase, iteration, run.
6. Transitions are durable.
7. Generation and evaluation are separate roles.
8. Efficacy is measured in cost delta.
9. The gotcha registry is the harness’s memory.
10. Runs are interrupt-disciplined, not interrupt-free.
11. The human holds the keys.

> **Note:** These pillars are currently under review. Several were written for a different era of tooling and may need updating to better reflect the current small-model, role-specialized council approach.

## Concrete Example: The Sea Gypsy

The current driving project is the transcription and cleanup of *The Sea Gypsy* (1924), a travel/adventure book co-authored by Edward A. Salisbury and Merian C. Cooper (the man who would later create *King Kong*).

### Why We’re Doing It
This is family history. Edward A. Salisbury was the user’s great-great-grandfather. The book is a first-hand account of a global voyage on the ketch *Wisdom*, including time in the Andaman Islands, Abyssinia, the South Seas, and the Red Sea. The goal is to produce a clean, readable version so the user’s 17-year-old son can actually engage with his ancestor’s story.

Edward Salsbury captured exotic animals from the South Pacific for carnivals. He later began capturing cannibals and selling them to carnivals as well. He and Merian C. Cooper became close friends and business partners; together they made the film *Gow* in 1928.

This led a group of investors to loan both men a large sum of money so that Salsbury could capture a 100-foot gorilla in the South Pacific. Salsbury took the money and went to Italy instead, where he died sailing the *Wisdom* drunk. The investors then came after Cooper to repay the loan. Cooper created *King Kong* to pay them back. And the story in *The Sea Gypsy* is, in essence, the tale of what would have happened if Salsbury had actually succeeded.

### Challenges Overcome
- The source PDF was a poor 1920s scan (reprinted by “Forgotten Books”) with heavy OCR artifacts, vector pages, JPX errors, and full-page illustration plates that traditional OCR turned into garbage.
- Early passes were pure CPU (ocrmypdf + tesseract) and produced usable but rough text.
- We then shifted to using the small local council (the same four models above) for a multi-round “debate” system: one model finds problems, another reviews against the original PDF, and the strongest writer produces repairs.
- We had to invent and iterate on process (linear passes → debate system → proper cumulative versioning) while the models themselves were doing the text work.

### Progress Made (as of early June 2026)
- Multiple cumulative versioned artifacts produced (v2 → v3 → v4 linear passes, followed by a full overnight debate run producing v5 material).
- A working multi-agent debate system using the naval roles above.
- Strict discipline around always improving the *latest* version instead of branching or resetting.
- A proper ephemeral workspace model (`tmp/`) created so project work can live separately from the core aho harnesses and eventually migrate cleanly to the target GCP project (tteos).
- 77+ sections meaningfully improved in a single 3-round overnight debate pass.

### What Still Needs Work
- Hardware is the current limiter. The 16 GB RTX 2000 Ada is workable but forces compromises on model size and parallelism. Better hardware will unlock significantly stronger Helmsman and Reviewer performance.
- The debate system’s final assembly and merging logic is still crude. We are actively improving the “merger” tooling so that debate improvements integrate cleanly into the main reading copy instead of producing messy partial files.
- The 11 Pillars themselves need a serious review pass. Many were written for a different tooling era.

This project has become the primary forcing function for evolving the aho council from “Grok designs clever prompts” into a real, self-improving crew that can operate over long time horizons.

---

## Changelog

*(Changelog to be appended here once retrieved)*