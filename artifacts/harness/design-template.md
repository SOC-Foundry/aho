# aho Design — X.Y.Z

**Phase:** N | **Iteration:** Y | **Run:** Z
**Theme:** <one-line theme>
**Iteration type:** <type per ADR-045>
**Executor:** <executor>
**Execution mode:** <mode>
**Scope:** <N> workstreams

---

## §1 Context

<prior iteration summary, what changed, what carries forward>

## §2 Goals

1. <goal 1>
2. <goal 2>

## §3 Trident

The Trident diagram is REQUIRED in every design doc. It uses Mermaid
`graph BT` (bottom-to-top) with exactly two classDefs:

- **shaft**: fill #0D9488 (teal), white text — represents the iteration
- **prong**: fill #161B22 (dark), stroke #4ADE80 (green) — represents workstream groups

Minimum 2 prongs, maximum 4. Each prong connects to the shaft via `-->`.

```mermaid
graph BT
    classDef shaft fill:#0D9488,stroke:#0D9488,color:#fff
    classDef prong fill:#161B22,stroke:#4ADE80,color:#4ADE80

    Shaft[X.Y.Z<br/>Theme Line]:::shaft

    P1[Prong 1 Name<br/>W0-WN<br/>Summary]:::prong
    P2[Prong 2 Name<br/>WN-WM<br/>Summary]:::prong
    P3[Prong 3 Name<br/>WM-WK<br/>Summary]:::prong

    P1 --> Shaft
    P2 --> Shaft
    P3 --> Shaft
```

## §4 Non-goals

- <explicit exclusion 1>

## §5 Pillars

<numbered pillar list — 10 or 11 depending on iteration scope>

## §6 Workstream Summary

| WS | Surface | Session | Session Role |
|---|---|---|---|
| W0 | ... | 1 | Setup |

## §7 Execution Contract

- <per-workstream review mode>
- <session boundaries>
- <halt-on-fail policy>

## §8 Open Questions for W0

<resolved or unresolved pre-iteration questions>

## §9 Risks

1. <risk + mitigation>

## §10 Success Criteria

- <measurable criterion 1>
