# Pre-Iteration Decisions — 0.2.12

Theme: Council activation — discovery, visibility, design, measurement
Primary executor: gemini-cli (0.37.1 confirmed operational)
Sessions: 3 (W0-W7 discovery+visibility, W8-W14 design+implementation-start, W15-W19 dispatch+measure+close)
Council dispatch minimum: 3 real dispatches (W13 Qwen, W14 GLM, W15 MCP workflow-participant)
Tech-debt audit: audit-only in W18, execution deferred to 0.2.14
Pattern framework: 5 seeds in W12 — planner-discipline, age-fernet-keyring, install-surface, daemon-lifecycle, council-dispatch
README review: content review in W18 (not append-only)

## Canonical Eleven Pillars of AHO (quoted verbatim from README per G073):

1. Delegate everything delegable. The paid orchestrator decides; the local free fleet executes.
2. The harness is the contract. Agent instructions live in versioned harness files, not model context.
3. Everything is artifacts. Every task is artifacts-in to artifacts-out.
4. Wrappers are the tool surface. Every tool is invoked through a /bin wrapper.
5. Three octets, three meanings: phase, iteration, run. Strategic, tactical, and execution scope.
6. Transitions are durable. State is written to a durable artifact before any transition.
7. Generation and evaluation are separate roles. Drafter and reviewer are different agents.
8. Efficacy is measured in cost delta. Wall clock, token cost, and delegate ratio are ground truth.
9. The gotcha registry is the harness's memory. Failure modes are indexed with mitigations.
10. Runs are interrupt-disciplined. No preference prompts mid-run; only capability gaps halt.
11. The human holds the keys. No agent writes to git or manages secrets.
