# Carry-Forwards — 0.2.11

**Generated:** 2026-04-12 W0 | **Updated:** 2026-04-12 W9 close (strategic rescope)

---

## TO 0.2.12: COUNCIL ACTIVATION (new iteration theme)

**Objective:** Establish a continuous improvement model for the LLM council working with other agentic components (daemons, pipelines, web pages, MCPs, executor agents, registries, harnesses) to optimize productivity, reduce time-to-build, and reduce token spend. Must be resilient and portable, replicable across other PCs and GCP projects. Anything that doesn't move toward this objective is off-mission.

**Specific deliverables:**

- Discovery: council inventory — which agents (Qwen, GLM, Nemotron, evaluator-agent, OpenClaw, Nemoclaw, MCP servers) are operational today, which have dispatch surfaces, which have ever executed a workstream task
- Visibility: `aho council status` CLI enumerating operational agents, dispatch surfaces, queue depth, recent routing decisions
- Design: workstream-level delegation pattern — dispatch contract for routing tasks to council members by capability
- Implementation: minimum viable council dispatch, baselined via schema v3 efficacy against claude-code-only execution
- Lego office visualization: council members as figures in an office, dispatch lines show work volume + health + state. Primary operational diagram, not decorative
- Pattern framework bootstrap (was 0.2.11 W8.5): planner-discipline + age-fernet-keyring + install-surface + daemon-lifecycle + council-dispatch patterns; `artifacts/patterns/` folder; evolution-log per pattern
- Tech-debt prune from W18 audit (slipped from 0.2.11)
- Full README review — stale sections include "What aho Does" bullets, iteration roadmap, three-persona model (0.2.10 shipped this, README describes as future), Canonical Folder Layout (data/ reference stale post-W7)
- Migration verify CLI (G076 — process census + fuser on old paths)
- AcceptanceCheck enhancements beyond MVP (richer assertion types, timeout tuning)

## TO 0.2.13: PERSONA 3 VALIDATION

Now meaningful because council can carry the work, not just claude-code.

- 4 fixture tasks from 0.2.9 W8 spec: PDF summarize, SOW generate, risk review, email extract (exact-match 7 unique)
- Fixtures at /tmp/aho-persona-3-test/ — regenerate via reportlab per 0.2.9 spec
- Measure council vs claude-code delegate ratio on each task
- Persona 2 framework-mode validation (confirm no silent dependencies before prune execution)
- P3 (ThinkStation) clone-to-deploy validation
- Phase 0 graduation: `git clone` + `install.fish` on P3 produces working aho environment
- Local model fleet operational on P3 hardware

## TO 0.2.14: AUR + TECH DEBT + FRONTEND

- AUR installer abstraction (aur_or_binary helper + aho-G048 keyring resilience class)
- Retrofit otelcol-contrib + jaeger to AUR pattern
- Tech-legacy-debt audit + prune execution (includes 8 aho-* shim wrapper deletion)
- Openclaw Errno 32 + 104 hardening (was 0.2.11 W17)
- Frontend multi-folder reshape: top-level dashboard/, nexus/, lego/, app-shared/ siblings; TelemetryClient polling skeleton; three-bundle Flutter builds
- Firestore scaffolding: service account with scoped permissions stored in age-fernet keyring; aho_installs, aho_iterations, aho_components, aho_gotchas, aho_patterns collections with Pydantic schemas; rules file deployed via firebase deploy
- aho firestore sync CLI
- Full README content review (W8 flagged as stale)

## TO 0.3.x+: Deferred Architecture

- aho.run domain Cloudflare → Firebase Hosting
- Secrets module standalone extraction (currently embedded in aho package)
- Multi-user Telegram support (currently single-user @aho_run_bot)
- Gemini CLI remote executor routing (currently local-only execution)
