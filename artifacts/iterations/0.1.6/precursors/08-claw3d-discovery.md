# Investigation 8 — Claw3D Discovery

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## Background

Kyle's notes from the 0.1.4 run report say: *"on 0.1.5 we must configure and deploy openclaw, claw3d and nemoclaw."* Claw3D is a component Kyle mentions but which had no clear definition in iao's codebase. This investigation searches for what it actually is.

---

## Search Results

### In iao project

| Location | Context |
|---|---|
| `CLAUDE.md` line 7 | "iao 0.1.5 is focused on configuring and deploying OpenClaw, NemoClaw, and Claw3D" |
| `docs/iterations/0.1.4/iao-run-report-0.1.4.md` line 40 | Kyle's note: "on 0.1.5 we must configure and deploy openclaw, claw3d and nemoclaw" |
| `MANIFEST.json` lines 23-24 | References `iao/postflight/claw3d_version_matches.py` and `iao/postflight/deployed_claw3d_matches.py` |
| `src/iao/postflight/__pycache__/` | Stale `.pyc` files for `claw3d_version_matches` and `deployed_claw3d_matches` — source files have been deleted but bytecode remains |
| `docs/sterilization-log-10.68.md` lines 48-54 | Documents that these postflight modules are "kjtcom-pipeline-specific by design" and need to be moved out of iao into a kjtcom plugin set |
| `docs/iterations/0.1.3/iao-bundle-0.1.3.md` | MANIFEST references to the same two postflight files |

### In kjtcom project

| Location | Context |
|---|---|
| `data/claw3d_components.json` | JSON file with `{"boards": [...]}` structure — lists PCB board components organized by category (Frontend, Backend, etc.) |
| `data/claw3d_iterations.json` | Iteration tracking data for the Claw3D visualization |
| `scripts/utils/sync_claw3d_data.py` | Sync script referencing `app/web/claw3d.html` |
| `scripts/bless_baseline.py` | Baseline checker with `claw3d` page URL: `kylejeromethompson.com/claw3d.html` |
| `scripts/run_evaluator.py` | Evaluator referencing `data/claw3d_components.json` and `app/web/claw3d.html` |
| `iteration_registry.json` | "Claw3D" and "Claw3D/Brave Search Integration" in iteration deliverables |
| `kjtco/docs/harness/project.md` | Extensive documentation: Claw3D is a **Three.js-based 3D PCB board visualization** deployed as `claw3d.html` on Firebase Hosting |

### Key finding from kjtcom docs

From `kjtco/docs/harness/project.md`:

> "CanvasKit (Flutter) and Three.js (Claw3D) prevent traditional DOM-based scraping for test verification."

> "ALL data must be inline JavaScript objects inside `claw3d.html`. Zero `fetch()` calls for any `.json` file."

> "Every iteration that modifies Claw3D must include a component review pass before finalizing."

**Claw3D is a Three.js 3D visualization of kjtcom's PCB board architecture**, rendered as a single HTML file (`claw3d.html`) and deployed on `kylejeromethompson.com`. It shows components as chips on a PCB board, organized by category (Frontend, Backend, etc.). It is a **kjtcom deliverable**, not an iao component.

### Not found anywhere

- No `claw3d` pip package, npm package, or ollama model
- No `claw3d` binary on PATH
- No `claw3d` in tripledb
- No iao source code for Claw3D (the postflight `.py` files were deleted; only stale `.pyc` remains)

---

## Analysis

Claw3D is **not an iao agentic component**. It is a **kjtcom frontend visualization** — a Three.js 3D rendering of the kjtcom system architecture, deployed as a static HTML page. It has nothing to do with OpenClaw or NemoClaw.

Kyle's run report note — "configure and deploy openclaw, claw3d and nemoclaw" — groups three things that are actually quite different:

| Component | What it is | Project | Relation to iao |
|---|---|---|---|
| OpenClaw | Agentic session wrapper around open-interpreter | iao | Core iao capability |
| NemoClaw | Orchestrator that routes tasks via Nemotron to OpenClaw sessions | iao | Core iao capability |
| Claw3D | Three.js PCB board visualization for kjtcom | kjtcom | kjtcom deployment artifact, not iao |

The iao postflight modules (`claw3d_version_matches.py`, `deployed_claw3d_matches.py`) that once existed were kjtcom-specific checks that verified the deployed `claw3d.html` matched expectations. The `docs/sterilization-log-10.68.md` explicitly documents that these "must be moved out of iao/iao/postflight/ into kjtco/postflight/" and were deleted from iao source (stale `.pyc` remains).

---

## Questions for Kyle

Before 0.1.6 can scope any Claw3D work, these need answers:

1. **Is the Claw3D work for 0.1.6 about deploying the kjtcom visualization, or about building something new in iao?** Evidence strongly suggests it's a kjtcom deployment concern.

2. **Should iao's postflight include Claw3D checks?** The sterilization log says no — these belong in a kjtcom plugin set. Does Kyle agree, or does he want iao to retain kjtcom-specific postflight checks?

3. **Is "configure and deploy claw3d" a kjtcom iteration task that got mixed into iao's scope?** If so, it should be tracked in kjtcom's iteration, not iao's.

4. **Does Kyle want an iao workstream that builds a postflight plugin system** so that kjtcom-specific checks (claw3d, flutter, map tab) can live in kjtcom's repo but be invoked by iao's postflight runner?

5. **The stale `.pyc` files in `src/iao/postflight/__pycache__/`** — should they be cleaned up in 0.1.6, or left until the plugin system is built?

---

## Conclusion

**Claw3D is a concept Kyle has introduced in the context of iao's next iteration, but it is actually a kjtcom frontend component (Three.js 3D PCB visualization), not an iao agentic capability.** It shares no code, architecture, or models with OpenClaw/NemoClaw. The "configure and deploy" language in Kyle's note likely refers to deploying the kjtcom `claw3d.html` page and ensuring its postflight checks work — a kjtcom concern that was previously (and incorrectly) housed in iao's postflight module before being removed during sterilization.

0.1.6 should either defer Claw3D entirely to a kjtcom iteration or, if Kyle wants it in iao's scope, scope it as a postflight plugin system that allows kjtcom-specific checks to run from iao without living in iao's source tree.
