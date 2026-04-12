# Install Surface Architecture — aho 0.2.9 W8.5

**Date:** 2026-04-11
**Type:** Architecture decision document (discovery insertion, per ADR-045)
**Scope:** Three-persona install taxonomy, aho-run dispatch spec, system services inventory
**Status:** Scope contract for 0.2.10 implementation. No code in this document.

---

## 1. Three-Persona Definition

aho serves three distinct use cases. Each persona has different install requirements, runtime expectations, and interaction patterns.

### Persona 1: Pipeline Builder

TTEOS infrastructure in GCP. The user works inside a git-cloned aho repo, running iterations with workstreams, checkpoints, and the full harness contract. All current aho functionality (0.1.0 through 0.2.9) serves this persona.

- **Install:** git clone + install.fish
- **Runtime:** iteration-scoped, workstream-gated, per-workstream review
- **Entry points:** `aho iteration`, `aho doctor`, `aho-conductor dispatch`
- **State:** `.aho.json`, `.aho-checkpoint.json`, `data/aho_event_log.jsonl`

### Persona 2: Framework Host

Clone aho once, import into other repos as a framework. The consuming repo inherits aho's harness, pillars, gotcha registry, and agent instructions without copying them. The aho repo is a dependency, not the workspace.

- **Install:** git clone aho + symlink or pip install from external repo
- **Runtime:** harness files referenced by path, not copied
- **Entry points:** `import aho` in Python, harness files read from `$AHO_PROJECT_ROOT`
- **State:** external repo's `.aho.json` points to aho's harness

### Persona 3: Impromptu Assistant

pwd-scoped one-shot work against arbitrary files. The user is in any directory — a client project, a downloads folder, a scratch pad — and wants aho to "do this task against these files" without entering the iteration/workstream framework.

- **Install:** system-local (daemon + CLI binary in PATH)
- **Runtime:** no iteration, no checkpoint, no workstream. Single task in, output out.
- **Entry points:** `aho-run "task description"` from any directory
- **State:** none persistent. Output written to `$AHO_CWD/aho-output/`

---

## 2. Component Install Location Taxonomy

Every aho component belongs to exactly one of two categories.

### Project-local (repo-scoped)

Lives inside the git-cloned aho repo. Travels with `git clone`. Required for persona 1 and 2. Not required for persona 3.

| Component | Path | Purpose |
|---|---|---|
| Python package | `src/aho/` | Core library: paths, config, logger, agents, secrets, bundle, doctor |
| Artifacts | `artifacts/` | Harness files, ADRs, iteration dirs, tests, scripts |
| State files | `.aho.json`, `.aho-checkpoint.json` | Iteration tracking |
| Event log | `data/aho_event_log.jsonl` | Structured event stream |
| Bin wrappers | `bin/` | Fish scripts wrapping Python modules |
| Templates | `templates/systemd/` | Service unit templates |
| Install orchestrator | `install.fish` | 9-step clone-to-deploy |
| Bootstrap | `bin/aho-bootstrap` | Environment setup from repo |
| MCP template | `.mcp.json.tpl` | Per-machine MCP config source |
| Agent instructions | `CLAUDE.md`, `GEMINI.md` | Persona 1 iteration instructions |
| Components manifest | `components.yaml` | Component registry |

### System-local (machine-scoped)

Installed per-machine, not per-repo. Managed by pacman, AUR, pip, npm, or upstream installers. Required for all three personas (persona 3 needs a subset).

| Component | Install method | Path |
|---|---|---|
| fish shell | pacman | `/usr/bin/fish` |
| Python 3.11+ | pacman | `/usr/bin/python` |
| Node.js + npm | pacman | `/usr/bin/node`, `/usr/bin/npm` |
| age | pacman | `/usr/bin/age` |
| jq, ripgrep, fd | pacman | `/usr/bin/` |
| libsecret | pacman | system library |
| Ollama | upstream script | `/usr/bin/ollama` |
| Ollama models | ollama pull | `~/.ollama/models/` |
| Dart SDK | pacman or upstream | `/usr/bin/dart` |
| Flutter SDK | upstream | user-installed |
| otelcol-contrib | AUR | `/usr/bin/otelcol-contrib` |
| Jaeger | AUR | `/usr/bin/jaeger` |
| MCP server fleet | npm -g | `/usr/lib/node_modules/` |
| OpenClaw daemon | systemd user service | socket at `/run/user/$UID/openclaw.sock` |
| Telegram daemon | systemd user service | socket at `~/.local/share/aho/telegram.sock` |
| Harness-watcher | systemd user service | event log watcher |
| OTEL collector | systemd user service | gRPC on 127.0.0.1:4317 |
| Jaeger UI | systemd user service | HTTP on 127.0.0.1:16686 |
| Dashboard | systemd user service (or ad-hoc) | HTTP on 127.0.0.1:7800 |
| aho-run binary | symlink in `~/.local/bin/` | persona 3 entry point |
| aho local install | `~/.local/share/aho/` | harness, registries, agent instructions |

**Note:** OpenClaw is changing from project-local to system-local per Decision 1 below. Currently it runs from the repo's Python package; after 0.2.10 it will be a persistent systemd user service reachable from any directory.

---

## 3. Kyle's Decisions (2026-04-11)

**Decision 1 — OpenClaw architecture:** Path A. Systemd user service + Unix domain socket at /run/user/$UID/openclaw.sock. Thin-client invocation from any directory. Persistent daemon managed by systemctl --user.

**Decision 2 — OTEL + Jaeger install:** AUR packages via bin/aho-aur install. otelcol-contrib and jaeger from AUR. Both run as systemd user services. Native binaries, not containers.

**Decision 3 — Persona 3 entry point command name:** aho-run. Top-level verb for one-shot work. Distinct from aho doctor, aho iteration, aho secret.

**Decision 4a — Working directory discovery:** aho-run inherits pwd by default. --cwd flag override supported.

**Decision 4b — Periodic harness/registry pulls:** explicit `aho update` command (not automatic). Stale-warning check on aho-run invocation when harness > 7 days old. Auto-pull on a systemd timer is deferred as a future opt-in feature.

**Decision 4c — Local install directory:** ~/.local/share/aho/ as the canonical install location. Layout:

```
~/.local/share/aho/
├── bin/              wrappers (aho-run, aho-doctor, etc.)
├── harness/          base.md, mcp-fleet.md, etc.
├── registries/       gotchas, scripts
├── agents/           CLAUDE*.md, GEMINI*.md
├── secrets/          fernet store, age key
└── runtime/          openclaw socket, pid files
```

~/.local/bin/aho-run as symlink to share/aho/bin/aho-run.

**Decision 4d — Agent instruction split:** two-file per agent.
- CLAUDE-iteration.md / GEMINI-iteration.md — current content, persona 1 iteration work
- CLAUDE-run.md / GEMINI-run.md — new, persona 3 one-shot work

Persona 3 instructions cover: $AHO_CWD pwd binding, output to $AHO_CWD/aho-output/, do-not-touch on harness/repo dirs, gotcha registry reference by path.

---

## 4. Persona 3 Dispatch Sequence (Spec Only)

```
User                    aho-run binary              OpenClaw daemon           Agent (Qwen/Claude)
  │                          │                            │                         │
  │  aho-run "summarize      │                            │                         │
  │   this PDF"              │                            │                         │
  │─────────────────────────>│                            │                         │
  │                          │  read $PWD                 │                         │
  │                          │  set AHO_CWD=$PWD          │                         │
  │                          │  set AHO_TASK="..."        │                         │
  │                          │                            │                         │
  │                          │  connect to socket         │                         │
  │                          │  /run/user/$UID/           │                         │
  │                          │   openclaw.sock            │                         │
  │                          │──────────────────────────>│                         │
  │                          │  {cwd, task, agent_hint}   │                         │
  │                          │                            │  route task             │
  │                          │                            │  pick agent             │
  │                          │                            │────────────────────────>│
  │                          │                            │  task + $AHO_CWD +      │
  │                          │                            │  CLAUDE-run.md          │
  │                          │                            │                         │
  │                          │                            │  agent reads files      │
  │                          │                            │  from $AHO_CWD          │
  │                          │                            │                         │
  │                          │                            │  agent writes output    │
  │                          │                            │<────────────────────────│
  │                          │                            │  $AHO_CWD/aho-output/  │
  │                          │                            │   run-<ts>.md           │
  │                          │  stream progress           │                         │
  │                          │<──────────────────────────│                         │
  │  render to stdout        │                            │                         │
  │<─────────────────────────│                            │                         │
  │                          │                            │                         │
  │  exit 0                  │                            │                         │
```

**Step-by-step:**

a. User types: `aho-run "summarize this PDF"` in any directory
b. aho-run binary (from ~/.local/bin/) reads $PWD
c. Sets env vars: AHO_CWD=$PWD, AHO_TASK="summarize this PDF"
d. Connects to openclaw socket at /run/user/$UID/openclaw.sock
e. Sends JSON dispatch: `{cwd, task, agent_hint}`
f. Openclaw daemon picks agent (Qwen local for small, Claude API for large — routing TBD)
g. Agent receives task + $AHO_CWD + CLAUDE-run.md as system prompt
h. Agent works, writes to $AHO_CWD/aho-output/run-\<ts\>.md
i. Openclaw streams progress back to aho-run via socket
j. aho-run renders progress to stdout, exits on completion

---

## 5. System Services Inventory (After 0.2.10)

| Service | Unit file | Socket/Port | Status |
|---|---|---|---|
| aho-openclaw.service | templates/systemd/ | /run/user/$UID/openclaw.sock | Existing, socket path changing |
| aho-telegram.service | templates/systemd/ | ~/.local/share/aho/telegram.sock | Existing |
| aho-harness-watcher.service | templates/systemd/ | (watches event log) | Existing |
| aho-otel-collector.service | templates/systemd/ | 127.0.0.1:4317 (gRPC) | New — AUR otelcol-contrib |
| aho-jaeger.service | templates/systemd/ | 127.0.0.1:16686 (UI) | New — AUR jaeger |
| aho-dashboard.service | templates/systemd/ | 127.0.0.1:7800 (HTTP) | Existing ad-hoc, promote to service |

All services run as systemd --user units. User linger requirement carries forward (`loginctl enable-linger $USER`).

---

## 6. Dependencies for 0.2.10 Implementation

What 0.2.10 must deliver to make aho-run work end-to-end:

| Deliverable | Type | Description |
|---|---|---|
| bin/aho-install | new wrapper | Populates ~/.local/share/aho/ from repo: copies harness, registries, agent files, creates bin symlinks |
| openclaw socket relocation | code change | Move from ~/.local/share/aho/openclaw.sock to /run/user/$UID/openclaw.sock |
| aho-run binary | new wrapper | Fish script in ~/.local/share/aho/bin/. Reads pwd, connects to openclaw, streams result. |
| CLAUDE-run.md | new file | Persona 3 agent instructions: $AHO_CWD binding, output conventions, no-touch rules |
| GEMINI-run.md | new file | Same as CLAUDE-run.md adapted for Gemini CLI |
| openclaw file bridge | code change | Connect chat + execute paths: read files from $AHO_CWD, inject into LLM context |
| Dashboard install section | code change | New dashboard card showing present/missing for every system-local and project-local component |
| AUR install path | code change | bin/aho-aur extended with otelcol-contrib and jaeger packages |
| Doctor system-local checks | code change | New doctor checks for otelcol-contrib, jaeger, openclaw socket at new path |

---

## 7. Updated Roadmap

| Iteration | Theme | Key deliverables |
|---|---|---|
| **0.2.10** | Install surface implementation | bin/aho-install, openclaw socket relocation, aho-run binary, CLAUDE-run.md/GEMINI-run.md, AUR packages, dashboard install section, doctor checks |
| **0.2.11** | Persona 3 validation on NZXTcos | 4 impromptu tasks from 0.2.9 W8 prompt re-run against installed surface. End-to-end aho-run validation. |
| **0.2.12** | Persona 2 validation | Clone-once, import into other repo as framework. Verify harness reference by path, not copy. |
| **0.2.13** | P3 clone-to-deploy | Phase 0 graduation test. Three personas validated on two machines. |

---

## 8. Open Questions for 0.2.10 W0

Known unknowns that need Kyle decisions before 0.2.10 starts:

1. **Openclaw agent routing policy:** Which tasks go to Qwen local vs Claude API vs Gemini CLI? Size-based threshold? Explicit flag? Agent-hint from aho-run?

2. **Dashboard as systemd service:** New unit file, or keep ad-hoc `bin/aho-dashboard &`? If service: should it auto-start on login?

3. **Log aggregation path:** OTEL collector config specifics — which exporters, which receivers, trace retention policy?

4. **Fernet store location:** Stay in ~/.config/aho/ (current) or move to ~/.local/share/aho/secrets/ (per decision 4c layout)? Migration path if moving?
