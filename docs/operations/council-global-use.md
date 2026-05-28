# Council global-use wiring

How the aho base-container council is reached from any Claude Code session on
the host, what it depends on, how those dependencies start at login, and how to
health-check the whole thing.

## What the council is (runtime view)

The council is the local LLM fleet that produces work dispatched through:

```
aho-conductor dispatch "<task>"
```

Any Claude Code session, in any working directory, can route work through it
because:

- `aho` is installed (editable) into the user site-packages and `aho-conductor`
  is on `PATH` at `~/.local/bin/`.
- The conductor talks directly to the host Ollama HTTP API at
  `http://127.0.0.1:11434`.

Despite the "base container council" name, the council in the current
(unattested) substrate runs against the **host Ollama system service**, not a
container. No container serves the models; the conductor reaches Ollama directly
over loopback. The base-container concept belongs to the forward-looking
attestation trajectory (ADR-0012), not the current dispatch path.

## The dispatch flow

`aho-conductor dispatch "<task>"` runs the Adversarial Authorship role split
in-process (cold start, no socket dependency):

1. **Route** - classifier model picks a role for the task.
2. **Produce** - workstream agent produces the work.
3. **Assess** - evaluator agent reviews and returns a score + recommendation.
4. **Notify** - a Telegram notification fires (best-effort; silently skipped
   when no credentials are configured).

The result (`execution`, `review`, `role`, `project`) is printed as JSON and
also written to `<cwd>/aho-output/council-dispatch-<ts>.json`, so the calling
project keeps a durable artifact in its own tree. The calling project's
identity (directory name, `.aho.json` name/code when present, git status) is
injected into the workstream context so the council knows which folder it is
working in.

`aho-conductor smoke` runs the same flow against a fixed task and asserts the
chain produced: a classified role, non-empty producer output, a parseable
score/recommendation from the assessor, a written artifact, and event-log
spans. Exit code 0 means the council is reachable end to end.

> Note: the workstream agent is chat-only - it produces content, it does not
> execute code or create files on the host. The council is the producer of
> work product; the orchestrating Claude Code session integrates and verifies
> that product. `smoke` asserts on produced content and spans, not on host
> filesystem side effects.

## Required models (the council roster)

Declared in `artifacts/harness/model-fleet.txt` and pulled into the host Ollama:

| Model                              | Council role                         | Approx pull |
|------------------------------------|--------------------------------------|-------------|
| `qwen3.5:9b`                       | Producer / assessor (workstream)     | 6.6 GB      |
| `nemotron-mini:4b`                 | Classifier / triage (routing only)   | 2.7 GB      |
| `haervwe/GLM-4.6V-Flash-9B:latest` | Evaluator / vision (review)          | 8.0 GB      |
| `llama3.2:3b`                      | Fast triage / base-tier auditor      | 2.0 GB      |

Provision them with `ollama pull <model>` for each, or run `aho-models install`
on a host whose `~/.config/aho/tier.json` `bundle` lists the roster.

On a host with no discrete GPU, these run CPU-bound: functional but slow. The
evaluator (GLM, 9B) is the heaviest step; expect multi-second to multi-minute
review latency on CPU-only hosts.

## Tier-aware context windows

`aho-conductor dispatch` reads the per-host VRAM tier from
`~/.config/aho/tier.json` (see `aho.orchestrator_config.get_host_tier`) and
sizes the producer/evaluator context windows accordingly:

| Tier            | Workstream (qwen) `num_ctx` | Evaluator (GLM) `num_ctx` |
|-----------------|----------------------------|---------------------------|
| `base`          | 4096                       | 4096 (explicit override)  |
| `partial`/`full`| 16384 (QwenClient default) | None (modelfile default)  |

On base-tier hosts the council still works end to end; it just runs in a
smaller window so a CPU-only dispatch completes in bounded time instead of
blowing the smoke ceiling on the 65K GLM default + a 16K qwen prompt + cold
model loads. Partial/full-tier hosts keep the natural windows for full-quality
9B producer/evaluator output. The carry-forward architectural target is that
heavy producer/evaluator work routes to partial-tier hosts; base-tier hosts
orchestrate and run the lighter `llama3.2:3b` auditor seat (see CLAUDE.md
"Council producer/evaluator seats are partial-tier work" carry-forward,
folding into ADR-0007 at W6).

## What starts at login (durability)

No manual preparation is required across reboots:

- **Host Ollama** - a system-level systemd service, enabled. Check with
  `systemctl status ollama`; restart requires sudo.
- **Models** - persist on disk once pulled.
- **aho** - editable install; `aho` / `aho-conductor` stay on `PATH`.
- **aho user daemons** - `openclaw`, `nemoclaw`, `telegram`, `harness-watcher`,
  `secrets-broker` run as `systemctl --user` units, enabled, with login linger
  on, so they survive logout and reboot. These back the `aho run` path and the
  notification bridge; the `aho-conductor` path does not depend on them, so the
  council answers `dispatch`/`smoke` even if a daemon is down.

Manage the user daemons with `bin/aho-systemd {status|install|doctor}`.

## Health-check

| Command                 | Checks                                                    |
|-------------------------|-----------------------------------------------------------|
| `aho-conductor smoke`   | Full route -> produce -> assess -> notify, exit 0 = healthy |
| `aho council status`    | Component view (Ollama models, sockets, health score)     |
| `ollama list`           | Roster is pulled into host Ollama                         |
| `aho-models status`     | Roster presence vs the declared fleet file                |
| `bin/aho-systemd status`| User-daemon unit states                                   |

## Two routing paths (when to use which)

The host exposes two complementary ways to route work to the council:

- **`aho-conductor dispatch "<task>"`** - the full council flow
  (route/produce/assess/notify). Stateless cold start, talks directly to host
  Ollama, no socket dependency, writes an artifact into the calling folder.
  This is what the global rule invokes from arbitrary project folders.
- **`aho run "<task>"`** - single-agent, cwd-aware. Routes through the warm
  OpenClaw socket daemon (`$XDG_RUNTIME_DIR/openclaw.sock`), reads the calling
  folder's files for context, and writes output to `<cwd>/aho-output/`. Use it
  for fast project-local tasks where warm sessions and file context matter more
  than a separate evaluator pass.

Both are reachable from any working directory. `dispatch` is the auditable
producer-assessor path; `run` is the warm project-local path.
