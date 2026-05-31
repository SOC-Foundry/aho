# Handoff Prompt: aho Machine Deployment / Bootstrap Tool

**Target Agent:** Claude (or Gemini CLI)

**Context for you (the receiving agent):**

You are being asked to implement a critical piece of infrastructure for the "fresh start" version of the aho project.

## Project Philosophy (Important)

This is a deliberate fresh start after archiving the entire old 0.3.x heavy Python council implementation. The new direction is:

- Lean, fish-first, hardware-aware Ollama multi-model council
- Multiple frontier agents (Grok, Claude, Gemini CLI) acting as capable **executors** that drive work through the local council
- Global availability - the council must be usable from any directory on the machine without per-project setup
- Strong emphasis on clean architecture, idempotency, and avoiding the tech debt of the previous system

## The Task

Build a clean, modern, idempotent deployment script 'install.fish' that can bring a fresh Arch Linux machine into full participation in the aho council ecosystem.

The tool must handle three core responsibilities:

1. **Replicate explicit pacman packages** (native repository packages)
2. **Replicate explicit AUR packages** (via yay or equivalent)
3. **Pull the full declared Ollama model roster**

## Current State (as of 2026-05-31)

### Existing Manifests (source of truth)

These have already been seeded from the primary development machine (p3cos):

- `manifests/packages/pacman-native.txt` - Explicit native packages (~357 packages)
- `manifests/packages/aur-foreign.txt` - Explicit AUR packages (only 5: 1password, 1password-cli, google-chrome, jack, jetbrains-toolbox)
- `manifests/ollama/models.txt` - Current working 16GB model roster

### Relevant Existing Tooling

- `bin/aho-ollama-global-16gb.fish` - System-wide Ollama + model deployment (already handles the model pulling side quite well)
- `bin/aho-council-preflight.fish` and `bin/aho-council-postflight.fish` - New VRAM hygiene and model state tools
- Strong existing patterns around global fish configuration and systemd services for Ollama

## Hard Constraints

- **No heredocs in any fish code.** This is a non-negotiable rule in this project.
- The tool must be highly idempotent (safe to run multiple times).
- Prefer declarative manifests over hard-coded lists.
- Must work well with the multi-agent executor model (Grok, Claude, and Gemini CLI may all invoke council work on the same machine).
- Fish-first where possible (the primary operator uses fish heavily).
- Good error messages and dry-run support are expected.

## Suggested Scope / Deliverables

A reasonable v1 could include:

- A main entrypoint script (e.g. `bin/aho-deploy` or `bin/aho-machine-bootstrap.fish`)
- Clear separation between:
  - Package installation phase
  - Ollama model installation phase (can potentially delegate to or integrate with the existing `aho-ollama-global-16gb.fish`)
- Ability to read from the `manifests/` directory
- Proper handling of `yay` for AUR packages
- Pre-flight / post-flight style checks (similar in spirit to the new council pre/postflight scripts)
- Clear logging of what changed vs what was already present

## Success Criteria

After running the tool on a reasonably fresh Arch machine, it should be possible to:
- Use the full aho council tooling
- Idempotency - the script must be idempotent and run each time the aho council is engaged, if all the models and packages are present then it will not change anything on disk
- Have all declared models available via the global Ollama service
- Have a consistent, reproducible environment that matches the primary development machine's package + model state

## Tone & Style Guidance

- Match the existing lean, pragmatic, fish-heavy style of the fresh-start tooling.
- Avoid over-engineering. This is infrastructure that needs to be reliable and maintainable, not clever.
- The user values tools that "just work" and produce clear output.

---

**Current working directory for this task:** `~/Development/Projects/socfoundry/aho`

You have full context of the fresh-start philosophy and the existing `bin/` and `manifests/` structure.

Please implement the deployment/bootstrap tool described above.
