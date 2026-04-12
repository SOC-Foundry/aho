# aho Run Report — 0.2.12
**Iteration:** 0.2.12
**Theme:** Council activation — discovery, visibility, design, measurement
**Primary executor:** gemini-cli
**Status:** Closed pending Kyle sign-off
---
## Workstreams
| WS | Surface | Session | Role | Status | Notes |
|---|---|---|---|---|---|
| W0 | Bumps + decisions + executor health check | 1 | Setup | pass | gemini 0.37.1 healthy, 7 daemons healthy, 12 canonicals bumped |
| W1 | Council inventory discovery | 1 | Discovery | pass | Generated inventory.md with 17 members, implemented strict AcceptanceResult schema |
| W1.5 | Harness hardening | 1 | Discovery | pass | 11 baseline failures registered to path-change isolation breakage (target 0.2.13 fix). prompt-conventions.md drafted but may need expansion as execution yields more edge cases. |
| W2 | Qwen/Nemoclaw dispatch surface audit | 1 | Discovery | pass | Qwen-3.5:9B responds successfully to direct Ollama interrogation and NemoClaw dispatch via socket. Latency is ~23.7s per round-trip. Both registered as operational. Gotcha registry paths reconciled to canonical XDG location, fixed 3 source hardcodes, registered aho-G082 to document dual-path write risks. |
| W3 | GLM evaluator audit | 1 | Discovery | pass | GLM is responsive via Ollama (54s latency) but the evaluator-agent implementation is critically flawed. The naive JSON parser crashes on markdown fences (```json), causing the agent to silently swallow the error and return a hardcoded fallback (`score: 8, ship`). W14 readiness is blocked until parsing logic is fixed. |
| W4 | Nemotron audit | 1 | Discovery | pass | Nemotron audited. Operational via Ollama, but heavily compromised. Found a direct instance of the aho-G083 anti-pattern: unparseable classifications and connection errors in `_classify_impl` are silently caught and return `categories[-1]` (`reviewer`). This routes malformed tasks directly into GLM's rubber-stamp fallback, masking routing failures completely. W13 readiness depends on fixing this exception mask. |
| W5 | MCP fleet workflow-participant audit | 1 | Discovery | pass | 4 key MCPs (context7, sequential-thinking, playwright, filesystem) successfully invoked as mid-workstream participants. No gap status found for these 4 tools. Track B scan for G083 anti-pattern found 155 `except Exception` blocks: 3 safe, 35 definitive G083-class, and 117 ambiguous requiring review. The anti-pattern is systemic across the codebase, not contained just to GLM and Nemotron. |
| W6 | aho council status CLI | 1 | Visibility | pass | Successfully introduced `aho council status` subcommand capturing the operational snapshot, including member status, pulled Ollama models, Nemoclaw socket presence, and overall G083 density penalty. Added --json, --member, and --verbose flags and mapped it to the `/api/council` dashboard endpoint. No baseline regressions introduced. |
| W7 | Lego office visualization foundation | 1 | Visibility | pass | Created static operational SVG architecture layout using council status data. Mapped dispatch boundaries correctly: NemoClaw acts as the central hub, LLMs as processing desks, and MCPs grouped to the side as tools. Visually reveals systemic structural flaws: NemoClaw has explicit outgoing relationship lines to models flagged completely red due to the G083 gaps discovered in previous workstreams. Fully served by the dashboard endpoint `/lego/`. |
| W8 | Iteration close | 2 | Close | pass | Executed strategic rescope boundary closing 0.2.12. Evaluated systemic G083 impact, generated retrospective, rewrote carry-forwards, constructed v10.66 context bundle, and prepared Kyle's sign-off sheet. |
---
## Agent Questions & Capability Gaps
- [ ] (Reserved)
---
## Kyle's Notes

- What surprised you most about the discovery-phase data (GLM's rubber-stamp parsing or Nemotron's categories[-1] fallback)?
- Does the systemic 155-instance G083 scope fundamentally reshape your view of the legacy code's reliability?
- Did the Pattern A/B/C data clarify or muddy the executor decision (gemini-cli vs claude-code)?
- Given the 23-second latency overhead of NemoClaw dispatch, does Nemotron remain viable as a synchronous router, or do we move immediately to direct Ollama invocations in 0.2.13?

---
## Sign-off

- [ ] Session 1 (W0-W7) Discovery & Visibility
- [ ] Session 2 (W8) Close
