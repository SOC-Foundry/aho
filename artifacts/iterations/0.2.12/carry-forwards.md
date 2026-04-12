# Carry-Forwards — 0.2.12

**Generated:** 2026-04-12 W8 Close

---

## TO 0.2.13: DISPATCH-LAYER REPAIR & DEBT REDUCTION
The critical blockers preventing true Council Deployment.
- **G083 Bulk Fix**: Systematic resolution of the 35 definitive and 117 ambiguous `except Exception:` silent-fallback patterns across the codebase.
- **GLM Parser Fix**: Sanitize or strip markdown JSON fences inside `EvaluatorAgent.review()` to prevent the hardcoded `{score:8, ship}` rubber stamp.
- **Nemotron Classifier Fix**: Remove the `categories[-1]` array default so invalid prompts or timeouts fail open rather than blindly defaulting to `reviewer`.
- **Nemoclaw Evaluation**: Assess the ~23s synchronous routing latency vs. migrating to direct Ollama access. Keep, refine, or replace.
- **OpenClaw Audit**: Run the formal operational status assessment since W6 marked it `unknown`.
- **OTEL Per-Agent Instrumentation**: Traces for logging dispatch metrics dynamically.
- **Tech-Debt Audit**: Full pruning execution mapped out in `tech-legacy-audit-0.2.12.md`.
- **README Content Review**: Refresh staleness noted at 0.2.11 boundary.

## TO 0.2.14: PERSONA 3 VALIDATION & FRAMEWORK EXPANSION
Post-repair deployments intended for 0.2.12 but deferred by the W8 close rescope.
- **Real Council Dispatches**: Execute W13-W16 using the un-broken 0.2.13 dispatch layer.
- **Schema v3 Baseline Measurement**: Measure delegate ratio efficiency.
- **Pattern Framework Bootstrap**: 5 seed patterns defined for `artifacts/patterns/`.
- **Persona 3 Validation**: Execute 4 fixture tasks (`aho run`) comparing council capability against the claude-code baseline execution ratio.
- **AUR Installer Abstraction**: General pacman package encapsulation.
- **Firestore Scaffolding**: Initial structure for remote configurations.
- **Frontend Reshape**: Multi-folder restructuring for dashboard/lego architectures.

## TO 0.2.15+: PHASE 0 GRADUATION
- **P3 Clone-to-Deploy**: True zero-touch migration validation against the secondary Arch Linux testing rig.
- **Openclaw Errno Hardening**: Errno 32 / 104 mitigation.
- **Phase 0 Graduation**: Target execution benchmark.

## TO 0.3.x+: DEFERRED ARCHITECTURE
- **aho.run Domain**: Cloudflare → Firebase Hosting integration.
- **Secrets Module Extraction**: Standalone separation from the `aho` package.
- **Multi-user Telegram**: Move beyond single-user `@aho_run_bot` routing.
- **Gemini CLI Remote Execution**: Extrapolate dispatch targeting to off-host configurations.
