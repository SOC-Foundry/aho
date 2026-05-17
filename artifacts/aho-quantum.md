
  The exact failure mode this would have caught today: F-0.2.18-W1-004. W0 probe captured nzxtcos.tail78a311.ts.net
  as a substrate fact. We baked it into the W1 image. Seven days later that fact had decohered (tailnet rolled, a8
  was rebuilt) and we didn't know until W2 pre-flight tried to use it. The harness has discrete probe→bake→use steps
   with no model of "how stale is this fact." A decoherence indicator at W1 image-bake time would have flagged
  "probe artifact is 7 days old, τ_tailnet_domain ≈ months but coherence < threshold — re-probe before bake."
  Instead we paid for the rebuild. 

  Three substantive applications:
  
  1. Substrate-fact freshness as first-class OTEL signal. Per (host, fact, last_verified_at) tuple, gauge
  aho.observable.last_verified_age_seconds. Substrate facts: tailnet domain, NZXTcos collector bind, image FQDN
  bake, SSH host keys, podman availability, broker socket presence. The demo's τ is per-fact — DNS domains have
  months-of-τ, sudo cache has minutes. Decoherence formula p(t) = c + (m-c)·e^(-Δt/τ) becomes the dashboard panel.
  2. ADR-0010 materiality weighted by coherence, not just counted. Currently N counts audit cycles binarily. A
  decoherence-aware materiality: weight N by how recently each substrate fact was re-probed. An iteration that
  re-probes everything at close fully restores coherence; one that doesn't degrades it. N≥8 with high coherence >
  N≥10 with stale facts.
  3. Audit narrative-lift (F-0.2.18-W0-008) is the same shape one level up. The auditor's knowledge of "which
  findings are current" decohered between W0-005/006/007 closure and v3 audit — llama3.2:3b lifted prior-cycle
  finding titles as if they were current. Same decoherence problem, different observable: finding-ID currency. Could
   be addressed by tagging each finding with last_active_at and giving the auditor a coherence-weighted view of the
  registered-references section.
  
  Three ambition tiers to actually build:
  
  ┌───────────────────┬────────────────────────────────────────────────────────────────────────┬────────────────┐
  │       Tier        │                                 Scope                                  │      Time      │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┼────────────────┤
  │ Lightweight       │ Emit aho.observable.last_verified_age_seconds for the ~10 substrate    │                │
  │ (0.2.x            │ facts the iteration cycle bakes. Surface on dashboard as numbers. No   │ ~1 workstream  │
  │ carry-forward)    │ formal model. Catches F-0.2.18-W1-004's failure mode.                  │                │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┼────────────────┤
  │                   │ aho posture subcommand reads ~/.local/share/aho/observables.jsonl      │                │
  │ Mid (0.3.x)       │ (append-only probe-outcome log) and prints <H>±σ. Decoherence formula  │ ~1 iteration   │
  │                   │ lives in aho.observability. Dashboard renders the wave-packet          │                │
  │                   │ visualization.                                                         │                │
  ├───────────────────┼────────────────────────────────────────────────────────────────────────┼────────────────┤
  │                   │ Iteration close itself becomes coherence-driven: re-probe ages-out     │ Charter-level  │
  │ Full (0.4.x+)     │ facts before close-package writes. Acceptance archives carry per-fact  │ rework         │
  │                   │ coherence metadata. Audits read coherence-weighted reference sets.     │                │
  └───────────────────┴────────────────────────────────────────────────────────────────────────┴────────────────┘
  
  One thing worth thinking about: rare-catastrophic facts (tailnet domain has months-τ but the failure mode is
  total). The demo's gradient p(t) doesn't represent "tiny chance of total breakage". May need a separate class of
  observable — presumed_stable_until_observed_otherwise — that doesn't decay smoothly but flips hard when re-probed.
   Or: tie τ to "time since last change in upstream change-feed" rather than wall-clock — Tailscale's API exposes
  account events.
  
  The demo's core insight — measurement age is itself a first-class signal, not a free side-effect of having 
  measured something — is the right reframing of aho's probe/bake/use loop. Worth pursuing at the lightweight tier
  as a 0.3.x carry-forward.
