# aho Local-vs-Global Parameter Model

This document explains how **aho** manages state across your workstation and your projects. Understanding this split is critical for keeping secrets safe and ensuring that aho can manage multiple projects on the same machine without cross-contamination.

## The Core Concept

aho divides all parameters and state into two buckets:

1.  **Local state** (Per-project): Things that belong to a specific engineering project.
2.  **Global state** (Per-workstation): Things that belong to the machine and the engineer.

---

## 1. Local State (Per-project)

Local state lives entirely within the project's root directory. It is generally tracked in git (except for large artifacts or temporary build logs).

**Location:** `~/dev/projects/<project-name>/`

**Key Artifacts:**
-   `.aho.json`: Project metadata (name, project code, current iteration version, GCP project ID).
-   `CLAUDE.md` / `GEMINI.md`: AI agent briefings specific to this project's rules and context.
-   `artifacts/docs/iterations/<version>/`: The aho iteration artifacts (Design, Plan, Build Log, Report, Bundle).
-   `data/`: Project-specific datasets and registries (script registry, gotcha archive).

**Why it's local:** If you zip up the project directory and give it to another aho-enabled engineer, they should have everything they need to understand the project's history and current status.

---

## 2. Global State (Per-workstation)

Global state lives in the user's home directory. It is **never** tracked in project repositories. It contains secrets and registries of which projects exist on this specific machine.

**Location:** `~/.config/aho/`

**Key Artifacts:**
-   `secrets.fish.age`: The encrypted master secrets file. Contains API keys and tokens for all services.
-   `projects.json`: A registry of every aho project on this machine and their local paths.
-   `active.fish`: A generated file that points to the currently "active" project. Sourced by your shell.
-   `credstore/`: (Future) Encrypted credential files for non-human bots.

**Why it's global:** You don't want your private Gemini API key or your client's database password sitting in a git repo. By keeping them in `~/.config/aho/`, they are available to any project you work on, but safe from accidental commits.

---

## How they interact

When you run an `aho` command, the tool follows this logic:

1.  **Identify the Project:** It looks for a `.aho.json` in the current directory. If not found, it checks the `IAO_PROJECT_ROOT` environment variable (set by `active.fish`).
2.  **Load Secrets:** It checks if a session is unlocked in the OS keyring. If yes, it decrypts `~/.config/aho/secrets.fish.age` and loads the secrets into memory.
3.  **Merge Configuration:** It combines the project-local metadata from `.aho.json` with the global secrets.

## Best Practices for Engineers

-   **Never move secrets to local:** If a project needs an API key, add it to the global store via `aho secret set`. Never hardcode it in `.aho.json` or a `.env` file.
-   **Keep .aho.json accurate:** When you start a new iteration, update the version in `.aho.json`. This ensures that artifacts are written to the correct local subdirectories.
-   **Use 'aho project switch':** This command updates the global `active.fish` and your shell's environment to point at the project you are currently focused on.
