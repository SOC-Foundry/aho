# ADR-0011: Substrate freshness telemetry

**Status:** Proposed (W0 of 0.3.1)
**Date:** 2026-05-23
**Deciders:** drafter (claude-web), operator
**Supersedes:** none
**Superseded by:** none

## Context

0.2.18 W1 baked a substrate fact (a host's tailnet FQDN) into the container image at probe-time. Seven days later the tailnet rolled (a workstation was rebuilt as part of the workstation reorganization documented in the multi-vault identity setup). 0.2.18 W2 pre-flight tried to use the stale FQDN and failed. The image had to be rebuilt. The incident is captured as F-0.2.18-W1-004.

The harness has discrete probe→bake→use steps. There is no model of *how stale a fact is* between probe and use. Once a probe outcome lands in an artifact (image label, plan-doc, install.fish), the harness treats that outcome as currently-true until something else writes over it. That assumption is wrong on a long-enough timescale for facts whose underlying reality changes — tailnet domain rolls, image FQDNs change when registries migrate, broker socket paths move when XDG variables shift, SSH host keys rotate, podman versions upgrade.

The `aho-quantum.md` chat-side input doc proposes substrate-fact freshness as a first-class OTEL signal, modeled on quantum decoherence: each fact has a characteristic decoherence time τ (DNS domains: months; sudo cache: minutes), and the probability that a baked fact is still currently-true decays as `p(t) = c + (m-c)·e^(-Δt/τ)`. The full proposal has three ambition tiers:

- **Lightweight (0.2.x carry-forward / 0.3.1 W1):** emit `aho.observable.last_verified_age_seconds` for ~10 substrate facts. Surface on dashboard as numbers. No formal decoherence model. Catches F-0.2.18-W1-004's failure mode.
- **Mid (0.3.x):** `aho posture` subcommand reads `~/.local/share/aho/observables.jsonl` append-only log, prints `<H>±σ`. Formula lives in `aho.observability`. Dashboard renders wave-packet visualization.
- **Full (0.4.x+):** iteration close becomes coherence-driven. Re-probe ages-out facts before close-package writes. Acceptance archives carry per-fact coherence metadata. Audits read coherence-weighted reference sets.

The full tier is charter-level rework. Mid-tier requires the lightweight-tier foundation. Lightweight tier closes F-0.2.18-W1-004 with bounded scope.

## Decision

**aho 0.3.1 W1 implements the lightweight tier as specified above.** Substrate-fact freshness becomes first-class telemetry but not yet a formal decoherence model.

### What lightweight tier ships

1. **Substrate-fact registry** at `src/aho/observability.py` — a small enumerated set of facts (initial 10 per plan-doc inventory) with per-fact metadata: `fact_id`, `description`, `probe_command` (the fish/python invocation that re-probes the fact), `warning_age_seconds` (per-fact τ-derived threshold; default 7 days for slow-changing infrastructure, much shorter for fast-changing facts).

2. **Append-only probe log** at `~/.local/share/aho/observables.jsonl`. Each line: `{fact_id, host, project, probe_outcome, probed_at_utc}`. Reads via `tail -n` or full-file scan; no separate database.

3. **OTEL gauge** `aho.observable.last_verified_age_seconds` with attributes `{fact_id, host, project, probe_outcome_class}`. Emitted on every probe and on every iteration-cycle's W0 audit pass.

4. **`bin/aho-probe-substrate`** fish wrapper that probes the 10 initial facts and writes outcomes to observables.jsonl. Idempotent. Runs on install.fish first-run AND on every iteration's W0 step.

5. **Dashboard surface** — claw3d brick rendering numeric `last_verified_age_seconds` per fact + summary count of facts exceeding `warning_age_seconds`. Red when count > 0.

### What lightweight tier explicitly does NOT ship

- **No decoherence formula.** `p(t) = c + (m-c)·e^(-Δt/τ)` is mid-tier (0.3.x post-0.3.1 or 0.4.x). Lightweight tier just measures age.
- **No `aho posture` subcommand.** Mid-tier.
- **No wave-packet visualization.** Mid-tier.
- **No iteration-close gating.** Full tier. Acceptance archives do not yet carry per-fact coherence metadata; close packages do not yet block on stale facts.
- **No automated re-probe-on-stale.** Lightweight tier surfaces the age; the *response* (rebuild image, re-bake plan-doc, etc.) is operator-driven by reading the dashboard.

### Initial 10 substrate facts (0.3.1 W1 scope)

Per `aho-plan-0.3.1.md` §W1:

1. Tailnet domain
2. Central OTLP collector bind
3. Image FQDN baked into install.fish or container env
4. SSH host keys per host
5. Podman availability + version per host
6. Broker socket presence per host
7. ChromaDB collection mount path
8. Ollama API endpoint per host
9. 1Password agent socket per host
10. CloudflareWARP DNS interception state per host

W1 executor confirms the inventory during implementation. Per-fact `warning_age_seconds` calibrated during W1 based on real-world change frequency.

## Consequences

**Positive:**
- Closes F-0.2.18-W1-004 structurally rather than via "be more careful next time."
- Makes substrate-fact freshness inspectable: operator can read `last_verified_age_seconds` for any fact at any time.
- Lays foundation for mid-tier (`aho posture` subcommand) and full-tier (coherence-driven iteration close) without committing to either's scope.
- Honest about scope: lightweight tier is one workstream of effort, not a charter-level rework.

**Negative:**
- Adds a new OTEL signal and append-only log to substrate. Disk-space cost is negligible (probe outcomes are ~200B each, ~10 facts × ~365 probes/year = ~700KB/year per host).
- Probe commands may themselves drift (the way to probe "Tailscale FQDN" today may differ in 6 months). Per-fact probe commands need themselves to be observable. **Acknowledge: probes are facts too.** Mid-tier addresses this; lightweight tier accepts the risk that probe commands may need manual update across iterations.
- Doesn't catch *rapid* decoherence (faster than the iteration cycle). Substrate facts that change between probe and use within the same workstream are not detected. Mitigation: keep `warning_age_seconds` tight for fast-changing facts (e.g., sudo cache: 30 minutes).

**Open questions for mid-tier (0.3.2+):**
- Per-fact τ calibration methodology — is τ static per fact, or does it update from observed inter-change time?
- Wave-packet visualization shape — what does `<H>±σ` actually look like as a dashboard widget?
- Rare-catastrophic vs gradient facts — aho-quantum.md flags this: DNS domains have months-τ but the failure mode is total. May need a separate class of `presumed_stable_until_observed_otherwise` observables that don't decay smoothly but flip hard on re-probe. Mid-tier scope.

**Open questions for full-tier (0.4.x+):**
- How does iteration-close gating compose with the existing `workstream_complete` event-chain state machine? Does coherence gating block the chain, or run alongside?
- Per-fact coherence metadata in acceptance archives — JSON schema extension shape.
- Audit-time coherence-weighted reference sets — `aho.council.audit_ref_lookup` reads per-fact ages, weights retrievals accordingly. May resolve F-0.2.18-W0-008 narrative-lift as a side effect.

## Cross-references

- `artifacts/aho-quantum.md` — chat-side input doc with three-tier framing
- `artifacts/aho-quantum-web.md` — companion web framing
- `artifacts/iterations/0.2.18/...` — F-0.2.18-W1-004 incident archive (W1 acceptance + audit + close note)
- `artifacts/adrs/0007-containerization-architecture.md` — tier framework (VRAM tiers) — independent axis from freshness telemetry
- `artifacts/adrs/0010-materiality-measurement.md` — N≥8 falsifiability threshold (independent measurement system)
- `aho-plan-0.3.1.md` §W1 — implementation scope

## Status notes

Status will advance from **Proposed** to **Accepted** at 0.3.1 W6 (ADR finalization workstream) once W1 implementation is complete and W1 acceptance archive seals.
