# Carry-Forwards — 0.2.14

**Generated:** 2026-04-13 W2 Close

---

## TO 0.2.15: MEASUREMENT MATRIX + ROSTER EXPANSION

- **Council composition expansion** — Llama 3.2 3B already on NZXTcos disk (~2GB). Pull DeepSeek-Coder-V2 16B-Lite Q4_K_M (NOT Q2 — quantization-quality tradeoff documented in 0.2.14 W1.5 chat) to tsP3-cos. Pull Mistral-Nemo 12B to tsP3-cos for long-context. Pull Gemma 2 9B for Pillar 7 partner. **0.2.15 W0 candidate.**

- **Capability-routed vs role-assigned cascade** — Architectural decision for 0.2.15 planning. Current cascade is fixed 5-stage role sequence; expanded roster naturally suggests capability-routed (Triage Officer routes to Specialist by task type). Both valid, different matrix designs. **0.2.15 W0 design decision.**

- **Dispatcher choice revisitation** — W1 chose direct Ollama HTTP over Nemoclaw despite Nemoclaw supporting bypass. Sound for W1.5 surgical fix. 0.2.15 should revisit: Nemoclaw-with-explicit-routing vs direct-Ollama vs new thin wrapper. Pillar 4 argues for wrapper layer eventually. Nemoclaw needs ~20 lines for `model_id` routing. **0.2.15 W1 candidate.**

- **Auditor role-prompt bifurcation** — Current auditor splits "validate deltas" (rubber-stamp prone) from "find issues" (genuine critique in `additional_findings`). Restructure so validation gets genuine pass/conditional/fail judgment. Same prompt design concern for helpfulness bias at end of stages — system prompts need "output final deliverable, do not ask follow-up questions" baked in. **0.2.15 prompt engineering workstream.**

- **Pattern C protocol patch** — Add rule: "Raw response field is ground truth for output integrity inspection. Parsed JSON validity is necessary but insufficient. Auditors must inspect raw response text for template leakage, truncation, drift." Lesson from W1's characterization drift that Gemini's audit surfaced. **0.2.15 W0 harness update.**

- **GLM and Nemotron substrate decisions** — Both substrate-compromised since 0.2.13 W2.5. Decisions still deferred awaiting matrix data. 0.2.15 matrix should explicitly include both with new roster to confirm/refute on properly-configured dispatcher (`/api/chat`, proper `num_ctx`). **0.2.15 matrix scope.**

- **OpenClaw status** — Confirmed in W0 to be Qwen wrapper. Cosmetic council member, not distinct capability. 0.2.15 decides: deprecate, keep as alias, or repurpose with different model. **0.2.15 council composition review.**

## TO 0.2.15: HARNESS + INFRASTRUCTURE

- **`emit_workstream_start` ordering issue** — W0 logging fired pre-version-bump because AHO_ITERATION env was null. Workaround: emit_start fires AFTER iteration env set. Document in protocol. **0.2.15 W0 protocol patch.**

- **`emit_workstream_complete` side-effect root cause unresolved** — W0 patched the symptom (checkpoint update scoped to named workstream only); original corruption mechanism in `emit_workstream_start` unknown. Investigate in 0.2.15 if recurs. **0.2.15 — investigate if triggered.**

- **Gotcha registry location** — W0 couldn't find canonical file at `artifacts/harness/gotcha-registry*`. Gotchas referenced inline from CLAUDE.md, design docs, carry-forwards. Locate or create in 0.2.15. **0.2.15 W0 candidate.**

- **Existing `test_workstream_events.py` corrupts checkpoints** — Doesn't mock `find_project_root`. Caused checkpoint resets during W1 (3 times). `test_emit_sibling_preservation.py` (W0 addition) properly mocks it. Fix existing tests in 0.2.15. **0.2.15 W0 candidate.**

- **Checkpoint corruption cleanup** — 0.2.14 checkpoint accumulated spurious entries from test suite (W_V3_TEST, W_V1_COMPAT, W_PARSE_TEST, etc.). Need checkpoint sanitization — remove test artifacts, reconcile real workstream states. **0.2.15 W0 candidate.**

- **MCP fleet** — 5 unknown/incomplete from W1 vetting (firebase-tools auth, firecrawl API key, dart role, memory role, everything role). Resolve in 0.2.15 W0 alongside roster expansion. **0.2.15 W0 candidate.**

## TO 0.2.15: ARCHITECTURE CANDIDATES

- **Executor-as-outer-loop-judge architecture** — Surfaced in 0.2.14 W1.5 chat session. Beyond Pillar 7 restoration within cascade, add two-tier evaluator pattern at orchestrator boundary:
  - Lower-tier evaluator (council LLM, working name "Critic") does first-pass artifact judgment after cascade produces draft
  - Claude/Gemini (working name "Arbiter") does second-tier evaluation with calibration authority
  - When Arbiter disagrees with Critic's judgment, Arbiter emits "calibration signals" dispatched back to Critic
  - Critic's learning persists harness-wide (all evaluator-tier council members benefit) in gotcha-registry-format (category-tagged, queryable) — scope decision: harness-wide learning, not per-model
  - Rejection threshold N=3 before escalation to human review or task-type flag
  - Adds Pillar 7 separation at orchestrator boundary (Claude/Gemini different by training, scale, failure modes from Qwen/Llama/Gemma)
  - Extra round-trip cost acknowledged, worthwhile during early calibration phase
  - Harness contract implications: CLAUDE.md and GEMINI.md need new "evaluation rubric" section; new canonical file at `artifacts/harness/evaluation-rubric.md`
  - Working names ("Critic", "Arbiter", "calibration signals") are placeholders; permanent names after first real test
  - **0.2.15 design decision: implement alongside roster expansion, defer to 0.2.16, or skip entirely.**

- **Capability-routed cascade** — See roster expansion entry above. The architectural question: does the cascade stay as a fixed 5-stage sequence (indexer_in → producer → auditor → indexer_out → assessor) or become dynamically routed based on input classification? Both designs have different implications for matrix measurement. **0.2.15 W0 design decision.**

## TO 0.2.16+: INFRASTRUCTURE + PORTABILITY

- **A8cos third-machine install** — Planned post-0.2.15. Portability concerns: age identity per-machine, install.fish end-to-end test on fresh CachyOS, Ollama model pre-pull, MCP per-machine auth. A8cos reframed as orchestration/dev machine (integrated GPU/CPU, AMD APU, shared system RAM, no discrete GPU). Not a council-execution machine — 9B+ models impractical. Could run Llama 3.2 3B via CPU inference if needed. **P3 clone (not A8cos) is the model expansion target.** NZXTcos and tsP3-cos stay current composition until P3 clone proves out. **0.2.16+ candidate.**

- **Machine role reframing** — A8cos: orchestration/dev (runs Claude Code, manages harness, dispatches). NZXTcos: primary inference (Qwen, Llama 3.2 3B, future roster). tsP3-cos: secondary inference (expansion candidates — DeepSeek, Mistral-Nemo). P3 clone: fresh install target. **0.2.16+ bootstrap iteration for A8cos focuses on orchestration role.**

- **Firestore migration of staging** — aho heading toward Firestore-hosted. Current staging uses local filesystem (`artifacts/iterations/*/deltas/staging/`). 0.2.15+ should plan Firestore document writes for delta staging. **0.2.15+ planning.**

---

**Count:** 18 items. **Key categories:** roster expansion (4), harness/infrastructure (6), architecture candidates (2), 0.2.16+ infrastructure (3), deferred substrate decisions (3).
