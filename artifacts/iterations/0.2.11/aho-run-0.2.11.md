# aho Run Report — 0.2.11

**Phase:** 0 | **Iteration:** 2 | **Run:** 11
**Theme:** Verifiable acceptance framework + gate reconciliation (rescoped from 19 to 9 workstreams at W9)
**Executor:** claude-code | **Review:** per-workstream ON | **Sessions:** 1 (of planned 3)

---

## Workstream Summary

| WS | Title | Status | MCP Used | Acceptance | Notes |
|---|---|---|---|---|---|
| W0 | Bumps + decisions + carry-forwards | pass | none — bump workstream | prose (bootstrap) | |
| W1 | AcceptanceCheck primitive | pass | none — Python primitive | 3/3 checks (see acceptance/W1.json) | 12 tests, W1 retropatched to v2 |
| W2 | Retrofit workstream events | pass | none — event schema work | 5/5 checks (see acceptance/W2.json) | 8 tests, v2 schema live |
| W3 | Gate path reconciliation | pass | none — Python postflight gates | 6/6 checks (see acceptance/W3.json) | report/run alternate resolver, daemon_healthy(), G070-G072 |
| W4 | Gate verbosity | pass | none — Python postflight | 6/6 checks (see acceptance/W4.json) | CheckResult dataclass, per-check detail in run_quality + structural_gates |
| W5 | 0.2.9 residual debt | pass | none — Python postflight | 6/6 checks (see acceptance/W5.json) | readme_current __main__, manifest self-ref exclusion, §22 regression tests |
| W6 | Trident template fix | pass | none — Python postflight | 5/5 checks (see acceptance/W6.json) + W6-patch 6/6 | §3 Trident verifier, design-template.md, canonical 11 pillars (G073) |
| W7 | Event log relocation | pass | none — Python logger + infra | 8/8 checks (see acceptance/W7.json) | XDG path, migration, rotation, 14 file path updates, harness-watcher service, G070/G071 applied |
| W8 | /ws denominator + in_progress + MCP smoke | pass | none — Python/Telegram/CLI | 11/11 checks (see acceptance/W8.json) | /ws fixes, schema v3, G074-G076, mcp-readiness.md, README timestamp. --forensics-minutes 0 |
| W9 | Iteration close | pass | none — close workstream | 8/8 checks (see acceptance/W9.json) | Bundle, carry-forwards rescope, G077, retrospective. --forensics-minutes 0 |
| W10 | Task A: PDF summarize | — | — | — | rescoped to 0.2.13 (see carry-forwards.md) |
| W11 | Task B: SOW generate | — | — | — | rescoped to 0.2.13 (see carry-forwards.md) |
| W12 | Task C: Risk review | — | — | — | rescoped to 0.2.13 (see carry-forwards.md) |
| W13 | Task D: Email extract | — | — | — | rescoped to 0.2.13 (see carry-forwards.md) |
| W14 | Persona 3 retrospective | — | — | — | rescoped to 0.2.13 (see carry-forwards.md) |
| W15 | AUR installer abstraction | — | — | — | rescoped to 0.2.14 (see carry-forwards.md) |
| W16 | Retrofit otelcol + jaeger to AUR | — | — | — | rescoped to 0.2.14 (see carry-forwards.md) |
| W17 | Openclaw Errno 32 + 104 hardening | — | — | — | rescoped to 0.2.14 (see carry-forwards.md) |
| W18 | Tech-legacy-debt audit | — | — | — | rescoped to 0.2.12 (see carry-forwards.md) |

## MCP Tools Invoked

| WS | Server | Justification |
|---|---|---|
| W0 | none | Bump workstream — file edits only, no MCP domain match |
| W1 | none | Python primitive — dataclass + subprocess, no MCP domain match |
| W2 | none | Event schema work — Python/JSON, no MCP domain match |
| W3 | none | Postflight gate fixes + gotcha registry — Python, no MCP domain match |
| W4 | none | Gate verbosity refactor — Python postflight, no MCP domain match |
| W5 | none | 0.2.9 residual debt — postflight fixes, no MCP domain match |
| W6 | none | Trident template + gate — postflight, no MCP domain match |
| W7 | none | Event log relocation — logger/infra, no MCP domain match |
| W8 | none | /ws fixes + schema v3 + MCP smoke — Python/Telegram/CLI, no MCP domain match |
| W9 | none | Close workstream — retrospective artifacts, no MCP domain match |

## Agent Questions

- G077: Should 0.2.12 council-activation iteration include a formal council-readiness gate before dispatching workstreams to local agents?
- Schema v3 efficacy tracking landed but has zero data points from council execution. First meaningful measurement requires 0.2.12 council dispatch.
- 10 pre-existing test failures (older tests not updated for W4 tuple shape + W7 event log path). Carry to 0.2.12 tech-debt?

## Kyle's Notes

0.2.11 was scoped as a 19-workstream hybrid iteration per ADR-045:
verifiable acceptance framework (W1-W2), gate reconciliation (W3-W6),
residual 0.2.9 debt (W5), event log relocation (W7), /ws fixes +
MCP smoke + schema v3 (W8), pattern framework bootstrap (W8.5),
persona 3 validation (W9-W14), frontend reshape + Firestore
scaffolding (W14.5), AUR installer abstraction (W15-W16), Openclaw
hardening (W17), tech-legacy-debt audit (W18), close (W19). Three
sessions. Per-workstream review throughout.

It closed at W9 after 9 workstreams. Session 1 landed clean, and
mid-iteration retrospective surfaced a strategic miscalibration that
made the remaining scope off-mission. The iteration ends honest.

Session 1 deliverables are real and matter. The AcceptanceCheck
primitive (W1) replaced prose claims with executable assertions —
command + expected exit + expected pattern + result JSON archived
per workstream. W2 retrofitted workstream_complete events to carry
acceptance results inline, v2 schema. From W3 onward every
workstream emitted structured acceptance into the event log, and
W1's retroactive patch proved the framework could ingest results
from workstreams that predated it. The "overstated completion"
failure mode named in 0.2.10 is structurally closed — prose claims
are retired, the framework enforces verification.

Gate reconciliation closed the four cosmetic 0.2.10 postflight
failures. W3 fixed path resolution across artifacts_present,
bundle_completeness, and iteration_complete (the "report vs run
naming" drift). W4 refactored run_quality and structural_gates
to emit per-check detail via a CheckResult dataclass — a gate
failure now tells you which check and why, not just a summary
count. W5 closed 0.2.9 residual debt: readme_current timezone
normalization, bundle_quality §22 format, manifest_current
self-referential hash. Two of three had actually been fixed in
0.2.10 without being checked off — tracking hygiene gap, fed
forward to 0.2.12 audit scope.

W6 caught the iteration's most uncomfortable bug. The design doc
I produced in W0 referenced "Ten IAO Pillars" and included a
fabricated 10-pillar list. The README canonical is eleven.
pillars_present gate caught the drift mid-W6 when the agent hit
the contradiction between gate and design. I initially instructed
the agent to relax the gate to ≥10 pillars — the wrong fix. The
agent flagged the inconsistency again, I read the README, realized
I had invented content, and reversed course. W6-patch closed it:
design rewritten with canonical eleven verbatim from README, gate
tightened to exactly eleven, G073 registered (planner-guidance-can-
introduce-canonical-drift). Pillar 7 called it — drafter and
reviewer as separate roles — and the framework did what it was
supposed to do. Planner-memory of canonical content cannot be
trusted; canonical sources must be read at W0 and quoted into
decisions.md.

W7 relocated the event log from data/ to ~/.local/share/aho/events/
with size-based rotation. 208MB file migrated cleanly. Then the
forensic: the agent spent ~17 minutes unraveling migration orphans.
An old terminal-launched telegram process from 06:55 was still
running (PID 3682144, not systemd-managed), writing heartbeats to
the old path with stale code. The harness-watcher systemd service
had the old path hardcoded in its ExecStart as --watch argument.
tail -F was holding a handle on the old file via that service. All
three required systematic diagnosis through ps aux, fuser, lsof,
and service-file inspection. G074-G076 registered: orphan-process-
survives-service-restart, service-unit-files-hardcode-paths, daemon-
restart-is-not-migration-verification. Framework gap: Claude Code
unraveled this with zero harness contribution. A pre-migration
process census + post-migration fuser check would have caught all
three instantly. Gate candidate for 0.2.12.

W8 landed /ws status denominator, workstream_start in_progress
checkpoint transition, /ws last caption-with-attachment routing
(the bug from Telegram testing that survived several daemon
restarts), MCP protocol smoke column (9/9 servers pass), three
gotcha registrations from W7, CHANGELOG 0.2.10 and 0.2.11 entries,
README review timestamp, and schema v3 efficacy instrumentation.
Schema v3 adds agents_involved, token_count, harness_contributions,
ad_hoc_forensics_minutes to workstream_complete. W8 self-emitted
with v3 fields — the framework measuring itself. This is what
made Pillar 8 measurable for the first time.

And measurability surfaced the problem. Session 1 executed with
claude-code as 100% executor, zero council participation. No Qwen
dispatch. No GLM review. No Nemotron routing. Every workstream.
The MCP fleet passed all smoke tests but participated in zero
workstream work. Pillar 1 ("delegate everything delegable") and
Pillar 7 ("generation and evaluation are separate roles") were
aspirational, not operational.

W9 was the point to name it. Persona 3 validation executed by
claude-code alone would have validated persona 3 for claude-code,
not for the council-orchestrated architecture aho claims to be.
AUR retrofit executed by claude-code alone reinforces the same
pattern. Nine more workstreams of single-executor work, measured
by a v3 schema that will show delegate ratio at 100% executor /
0% council, while the iteration's deliverables moved the roadmap
forward on paper but the actual product — a continuous improvement
model for an LLM council working with other agentic components —
stayed fiction.

G077 registered at close: planner-executor-bias-consumes-council-
capacity. Root cause is planner-side. The planner operates from
descriptive context about the council architecture without
operational context about which agents are live or what dispatch
surfaces exist today. Defaults to the agent whose output pattern
is familiar, which is claude-code. The fix is not "tell claude-
code to delegate more" — it's "audit the council's actual dispatch
surface, build visibility primitives, make council dispatch the
path of least resistance, measure the delegate ratio per workstream."

0.2.12 absorbs all of that as a dedicated theme. Discovery first
(which agents operational, which dispatch surfaces exist, which
have ever executed workstream-level work). Visibility second
(aho council status CLI, real operational map). Design third
(workstream-level delegation pattern, dispatch contract routing
by capability). Implementation fourth (minimum viable council
dispatch, baselined against claude-code-only execution via schema
v3). The lego office visualization becomes the primary operational
diagram — council members as figures, dispatch lines showing work
volume and health and state. When one figure has every line
attached to it, the executor-bias problem is visible. When the
room is empty except for Claude Code, the product is fiction.
When figures are balanced and active, aho is doing what it claims.

Pattern framework bootstrap also slips to 0.2.12 with the
planner-discipline pattern as the first seed alongside age-fernet-
keyring, install-surface, daemon-lifecycle, and council-dispatch.
Five seeds. Artifacts/patterns/ as the folder. Evolution-log
semantics per pattern. Voluntary through 0.2.12, gated from 0.2.13.

Persona 3 validation moves to 0.2.13 where it becomes meaningful —
measure council vs claude-code delegate ratio per fixture task.
AUR + tech-debt prune + frontend reshape + Firestore scaffolding
consolidate into 0.2.14. P3 clone-to-deploy slides to 0.2.15 or
later depending on what 0.2.12-0.2.14 surface.

What this iteration proved is that the harness can catch strategic
drift at workstream granularity, not just tactical drift. G073 caught
a planner-authored fabrication. G077 caught a planner-authored
off-mission trajectory nine workstreams deep. Both were prevented
from propagating by per-workstream review plus canonical source
gates plus honest retrospective. Without per-workstream review,
0.2.11 would have shipped with drift into 0.2.12 roadmap, wrong
pillar count in canonical artifacts, and a "successful" persona 3
validation that proved nothing about the council. The cost of the
reshape is four workstreams' worth of roadmap slip. The value of
catching it is an honest 0.2.12 theme that moves aho toward the
actual objective: a continuous improvement model for an LLM
council working with other agentic components to optimize
productivity, reduce time-to-build, and reduce token spend.
Resilient and portable. Replicable across other PCs and GCP
projects. Anything that doesn't move toward this is off-mission.

0.2.11 closes honest. Seven unpushed iterations (0.2.5-0.2.11)
pending Kyle git commit + push. Bundle is 640KB, 64 tests green,
31 gotchas total registered, schema v3 live, pillars canonical,
event log on XDG, council activation queued for 0.2.12.

## Sign-off

- [x] All 9 executed workstreams pass (W10-W18 rescoped)
- [x] AcceptanceCheck results verified (W1-W9)
- [x] Postflight gates green (known: build-log cosmetic, canonical_artifacts harness versions)
- [x] Bundle generated (640KB)
- [x] Kyle reviewed and approved
