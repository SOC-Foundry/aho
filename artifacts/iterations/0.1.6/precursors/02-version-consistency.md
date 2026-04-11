# Investigation 2 — Version Consistency and Stale Install

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## The Problem

Kyle discovered that `iao iteration close --confirm` failed at the global `iao` binary level with "invalid choice: 'iteration'" but worked when invoked as `./bin/iao iteration close --confirm`. This investigation determines why.

---

## Three Invocation Paths

| Path | Resolves to | Version reported |
|---|---|---|
| `iao` (global) | `/home/kthompson/iao-middleware/bin/iao` | `0.1.0` |
| `./bin/iao` (local) | Direct shim in project | `0.1.4` |
| `python3 -m iao.cli` | Editable install → `src/iao/cli.py` | `0.1.4` |

**The global `iao` binary is a completely different program.** It resolves to `/home/kthompson/iao-middleware/bin/iao`, which is a bash script from an older project layout ("iao-middleware"). This is not a stale pip install — it's a separate, legacy binary.

---

## Evidence

### Global binary
```
$ which iao
/home/kthompson/iao-middleware/bin/iao

$ head -5 /home/kthompson/iao-middleware/bin/iao
#!/usr/bin/env bash
# iao CLI dispatcher
# v0.1.0
set -e
```

This is a bash dispatcher script from `iao-middleware/`, a predecessor directory to the current `~/dev/projects/iao/` project. It only exposes: `{project, init, check, status, eval, registry}` — no `iteration`, `doctor`, `telegram`, `log`, `rag`, `secret`, `pipeline`, `preflight`, or `postflight` subcommands.

### Local binary
```
$ ./bin/iao --help
{project,init,check,push,log,doctor,status,eval,registry,rag,telegram,
 preflight,postflight,secret,pipeline,iteration}
```

The local `./bin/iao` is a shim that invokes the source directly. It has all 16 subcommands.

### pip install state
```
$ pip show iao
Name: iao
Version: 0.1.4
Location: /home/kthompson/.local/lib/python3.14/site-packages
Editable project location: /home/kthompson/dev/projects/iao
```

iao 0.1.4 is installed in editable mode (`pip install -e .`). The registered entry point is `iao = "iao.cli:main"`. However, the global `iao` binary at `/home/kthompson/iao-middleware/bin/iao` takes precedence in `$PATH` over the pip-installed entry point.

### PATH ordering

The issue is PATH precedence. `/home/kthompson/iao-middleware/bin/` appears before `~/.local/bin/` in the shell PATH. When Kyle types `iao`, the shell finds the legacy bash dispatcher first.

---

## CLI Wiring Verification

The source at `src/iao/cli.py` has `iteration` fully wired:

```python
# Line 192: def cmd_iteration(args, parser):
# Line 193:     sub = args.iteration_cmd
```

The `iteration` subcommand supports `design`, `plan`, `build-log`, `report`, `close`, `seed`, `graduate`, and is registered in the argparse tree. This code is what `./bin/iao` and `python3 -m iao.cli` execute.

---

## Diagnosis

**Answer: (b) — `./bin/iao` is a shim that bypasses the stale global binary.**

The global `iao` binary is NOT a stale pip install. It is a completely separate legacy bash script from `~/iao-middleware/`. The pip-installed entry point does exist at `~/.local/bin/iao`, but `~/iao-middleware/bin/` shadows it in PATH.

The divergence:
1. `~/iao-middleware/bin/iao` — v0.1.0 bash dispatcher, 6 subcommands, legacy
2. `~/.local/bin/iao` — pip entry point, would call `iao.cli:main` (v0.1.4), but is shadowed
3. `./bin/iao` — local shim, calls source directly, 16 subcommands, current

---

## Root Cause and Minimum Fix

**Root cause:** `~/iao-middleware/bin/` is on PATH and shadows the pip-installed `iao` entry point. This predates the current project structure.

**Minimum fix:** Remove or rename `~/iao-middleware/bin/iao`, or reorder PATH so `~/.local/bin/` comes first, or remove `~/iao-middleware/bin/` from PATH entirely. Then `iao` will resolve to the pip-installed entry point which already points to the editable install of `src/iao/cli.py`.

**Recommended fix:** Delete or archive `~/iao-middleware/` entirely (it's a legacy artifact), remove its bin directory from fish PATH config, and verify `which iao` resolves to `~/.local/bin/iao` afterward.

---

## What This Tells Us

The `iteration` subcommand failure that Kyle hit was not a code bug — the code is correct. It was a deployment/PATH configuration issue. The 0.1.4 iteration close likely worked via `./bin/iao` but any time Kyle or an agent typed bare `iao`, they got the wrong binary. This may have caused confusion in previous agent sessions as well.
