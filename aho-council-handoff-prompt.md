# Handoff: wire the aho council for global Claude Code use

Paste everything below into the Claude Code agent running inside
`~/Development/Projects/socfoundry/aho/`.

---

## Objective

A global Claude Code rule has been added (in `~/.claude/CLAUDE.md`) that makes
**every** Claude Code session, in **every** project, route all work through the
aho base container council via:

```
aho-conductor dispatch "<task>"
```

with the council as the producer of the work and the outer agent only
orchestrating and integrating. Right now that does not actually function from
outside the aho repo. Your job is to wire aho so that this global invocation
works reliably and survives reboots.

## How aho will be invoked from the outside (the new contract)

- Arbitrary Claude Code sessions, in unrelated working directories, will run
  `aho-conductor dispatch "<task>"` (and `aho-conductor smoke` to health-check).
- They rely on `aho-conductor` being on `PATH` (it is: `~/.local/bin/aho-conductor`).
- They expect the council to be reachable without any per-project setup. Treat
  "works from any cwd, on a fresh login" as the bar.

## Current verified state (gathered from outside the repo)

Environment: CachyOS, KDE/Wayland, fish shell, Python 3.14, PipeWire host.

1. `aho` and `aho-conductor` are installed on PATH at `~/.local/bin/`.
2. `aho-conductor smoke` FAILS. Trace ends in
   `src/aho/pipeline/dispatcher.py` `_run_dispatch` ->
   `urllib.error.HTTPError: HTTP Error 404: Not Found`.
3. `dispatcher.py` targets Ollama: `OLLAMA_BASE = "http://127.0.0.1:11434"`,
   docstring "Ollama HTTP API with multi-model support", `/api/chat`.
4. Ollama IS running (it returns an HTTP 404, not a connection refusal), but it
   only has these models pulled:
   - `llama3.2:3b`
   - `nomic-embed-text:latest`
5. The council expects (per `artifacts/council-models-0.2.14.md`):
   - `qwen3.5:9b` (used via OpenClaw / `get_openclaw_model()`)
   - `nemotron-mini:4b` (NemoClaw routing)
   - `haervwe/GLM-4.6V-Flash-9B` (community vision model)
6. NemoClaw uses a unix socket at `~/.local/share/aho/nemoclaw.sock`
   (`src/aho/agents/nemoclaw.py`); conductor routes NemoClaw -> workstream agent
   -> evaluator agent.
7. No containers are running (docker/podman `ps` empty) and nothing is listening
   on ports 7800-7899 (the `.aho.json` dashboard/port range).
8. There is a `Dockerfile`, `containers/Dockerfile.hello`, `docker-compose.otel.yml`,
   and an `aho-systemd` helper in `bin/`.

Leading hypothesis for the 404: the council model IDs requested by the code are
not present in the Ollama instance being hit (models not pulled), and/or the
intended "base container" that serves the council is not running, so dispatch
hits a host Ollama that lacks those models.

## What to resolve / decide

1. **Architecture question:** is the council supposed to run against the host
   Ollama (`127.0.0.1:11434`), or inside a dedicated "base container" that serves
   the models? The user's own term is "base container council," which implies a
   container. Confirm the intended design from the repo, then make reality match
   it (pull models on host, or build/run the base container that serves them).
2. **Make `aho-conductor smoke` pass** from an arbitrary cwd (not just inside the
   repo). Reconcile the model IDs the code requests (check
   `src/aho/orchestrator_config.py`, `get_openclaw_model()`, and any
   `OLLAMA_DEFAULTS`) against what is actually available, and fix the mismatch.
3. **Make it durable across reboots.** The user reboots regularly and hit
   ordering/availability races before. If the council depends on a container or a
   long-running service (e.g. the NemoClaw socket server, an Ollama-backed base
   container), wire it as a `systemd --user` unit (see `bin/aho-systemd`) so it is
   up at login without manual steps.
4. **Confirm the external contract.** From a directory OUTSIDE the aho repo, run
   `aho-conductor smoke` and a real `aho-conductor dispatch "<small verifiable task>"`
   and show they succeed end to end (route -> execute -> review -> notify), with
   the produced artifact and event-log spans.

## Acceptance criteria (definition of done)

- `aho-conductor smoke` exits 0 from any working directory on a fresh login.
- `aho-conductor dispatch "<task>"` completes the full conductor flow and returns
  a score/recommendation plus a produced artifact.
- Required council models are present (or served by the running base container).
- Whatever the council depends on is started automatically at login (no manual
  prep), and you have verified it by checking state after a restart of the
  relevant service(s).
- A short doc in the aho repo describes the global-use wiring: what runs, how it
  starts, the model/container requirements, and how to health-check it.

## Constraints and notes

- Do not use em dashes in any markdown you produce; use regular hyphens.
- Pulling the council models is several GB; confirm disk/bandwidth is acceptable
  before pulling, and prefer the quantizations the repo already standardizes on.
- Do not break the existing `aho` CLI surface that is already on PATH.
- If you change how dispatch resolves the Ollama endpoint or model IDs, keep it
  backward compatible with the documented council model set, or update
  `artifacts/council-models-*.md` and the changelog accordingly.
- Report what you changed and paste the passing `smoke` + `dispatch` output.

## Pointers (already located)

```
Conductor CLI      : bin/aho-conductor   (-> python -m aho.agents.conductor)
Dispatcher         : src/aho/pipeline/dispatcher.py   (OLLAMA_BASE, /api/chat)
Orchestrator/NemoClaw: src/aho/agents/nemoclaw.py     (socket ~/.local/share/aho/nemoclaw.sock)
Model config       : src/aho/orchestrator_config.py   (get_openclaw_model, OLLAMA_DEFAULTS)
Council model spec : artifacts/council-models-0.2.14.md
Container assets   : Dockerfile, containers/Dockerfile.hello, docker-compose.otel.yml
systemd helper     : bin/aho-systemd
Project config     : .aho.json  (dashboard_port 7800, port_range 7800-7899)
```
