# Iteration 3 Charter — aho

**Iteration:** 3 (runs 0.3.1, 0.3.2, …)
**Phase:** 0 (Clone-to-Deploy)
**Status:** Planned (umbrella charter; sub-iteration plans land at
`aho-plan-0.3.1.md` etc. when each sub-iteration opens)
**Charter date:** 2026-05-01

---

## §1 Iteration deliverable (per ADR 0006 — multi-iteration form)

> **Iteration 3 ships aho beyond NZXTcos.** Across the 0.3.x runs, aho
> moves from "containerized base-tier on a single workstation"
> (0.2.17's deliverable) to "containerized partial-tier and full-tier
> deployments on additional hardware" — the second physical machine
> (tsP3, partial-tier, 16 GB) and the cloud-tier serving plane
> (full-tier, A100/H100-class). Each sub-iteration ships a
> physically-different tier as a runnable container instance and
> records the cross-tier deltas as substrate findings. Iteration 3
> graduates when both tier expansions ship and a single trace
> originating on a base-tier host (NZXTcos) reaches a full-tier
> serving plane via the cloud registry pipeline.

This umbrella charter does not enumerate per-sub-iteration deliverable
paragraphs — those land at sub-iteration open. ADR 0006 mandates the
deliverable paragraph + graduation criterion **per iteration**, where
"iteration" in three-octet versioning is the third-octet level (0.3.1,
0.3.2, …). The umbrella charter sets the multi-iteration objective;
each sub-iteration's plan opens with its own paragraph + criterion.

## §2 Sub-iteration roadmap (planned)

| Sub-iter | Theme | Tier shipped | Hardware | Status |
|---|---|---|---|---|
| 0.3.1 | Partial-tier container on tsP3 | partial | tsP3 (16 GB discrete GPU) | planned |
| 0.3.2 | Full-tier serving plane (cloud) | full | GCP A100-class VM | planned |
| 0.3.x | Cross-tier dispatcher routing + Pillar 7 cascade re-run | mixed | NZXTcos (base) → cloud (full) | planned, opens when 0.3.1 + 0.3.2 stable |

The roster is not authoritative — sub-iteration boundaries can shift
based on what 0.2.17 surfaces and what ADR 0007 / 0008 amendment
triggers fire (per their §Revisit Triggers sections). The roadmap is
the planning shape, not a contract.

## §3 Per-sub-iteration outlines

### §3.1 0.3.1 — Partial-tier on tsP3

**Iteration deliverable (placeholder, refined at 0.3.1 open):**
> 0.3.1 ships the partial-tier aho container on tsP3 (16 GB discrete
> GPU). install.fish detects partial tier, pulls the partial bundle
> (base + qwen3.5:9b + GLM-4.6V-Flash-9B), and the full harness
> pipeline runs cleanly inside the container against partial-tier
> models. Cross-machine OTEL flow validated: tsP3-emitted signals
> land in NZXTcos's collector via network OTLP, with `host.name=tsP3`
> as resource attr.

**Graduation criterion form (placeholder):** Form 1 (runnable test).
The 0.3.1 plan will define a fish-test sequence equivalent to
0.2.17's, parameterized for partial tier on tsP3.

**Workstream skeleton (5 workstreams expected):**
- W0 — 0.2.17 carry-forward closure + tsP3 hardware probe
- W1 — install.fish partial-tier pull on tsP3
- W2 — Cross-machine OTEL: tsP3 → NZXTcos collector
- W3 — Partial-tier dispatcher exercise (real qwen + GLM dispatches
  inside container)
- W4 — Close

**Inheritance from 0.2.17:**
- ADRs 0006, 0007, 0008 bind unchanged. Tier detection, manifest
  shape, and dispatcher behavior are reused.
- The hybrid-mode dispatcher behavior on tsP3 changes meaning —
  tsP3 *is* partial-tier, so hybrid-mode would route base-tier-only
  bundles' missing families upward, not downward. The semantics
  may need amendment depending on what tsP3 dispatches reveal;
  ADR 0008's revisit trigger #3 (second engineer / second host
  needs hybrid mode) covers this.

**Out of scope for 0.3.1:**
- Multi-tier dispatch routing (one host per dispatch; deferred to
  0.3.x).
- Full-tier deployment.
- Pillar 7 cross-model cascade re-run.
- Cloud serving plane.

### §3.2 0.3.2 — Full-tier serving plane (cloud)

**Iteration deliverable (placeholder, refined at 0.3.2 open):**
> 0.3.2 ships the full-tier aho container on a cloud-tier host
> (initial target: GCP A100-class VM). install.fish on the cloud
> host detects full tier, pulls the full bundle (including Nemotron
> Super), and the harness pipeline runs cleanly. The cloud registry
> choice is made (ADR 0007 §Registry choice deferral resolved). The
> cloud host emits OTEL signals to a cloud-tier collector (decision
> deferred to 0.3.2 W0).

**Graduation criterion form (placeholder):** Form 1 (runnable test) +
Form 3 (manual checklist) — full-tier deployment has both
mechanically-verifiable steps and operator-controlled steps
(provisioning, IAM, network reachability) that resist automation.

**Workstream skeleton (5 workstreams expected):**
- W0 — 0.3.1 carry-forward closure + cloud-host provisioning
- W1 — Cloud registry decision + image promotion (local → cloud)
- W2 — install.fish full-tier on cloud host + manifest write
- W3 — Full-tier dispatcher exercise + Nemotron Super
- W4 — Cross-host trace from base (NZXTcos) → cloud (A100), close

**Architectural inheritance and amendments expected:**
- ADR 0007 §Registry choice — deferred decision resolved here.
  Likely amendment.
- ADR 0007 §Cloud-side registry — Phase C deferral may be partially
  resolved.
- ADR 0007 may need a Kubernetes-vs-single-pod amendment if
  full-tier deployment requires K8s manifests.
- ADR 0008 §Out of Scope multi-host load balancing — partial
  resolution candidate; full multi-host LB is still Phase C.

**Out of scope for 0.3.2:**
- Multi-engineer registry sync (Phase B work — ADR 0007 §Out of
  Scope).
- Signed images + SBOM emission (Phase B).
- Full Kubernetes manifests (likely 0.3.x or Phase 1).
- ROCm / Apple Metal tier detection.

### §3.3 0.3.x — Cross-tier routing + Pillar 7 cascade re-run

**Iteration deliverable (placeholder, refined when sub-iter opens):**
> 0.3.x ships the cross-tier dispatcher: a single harness invocation
> on a base-tier host can route stages to a partial-tier host
> (tsP3) or full-tier serving plane (cloud) via OTLP-correlated
> traces, with each stage's resource attribution landing in the
> appropriate tier. The cross-model cascade re-run (Pillar 7
> verdict — Qwen vs GLM Auditors on identical Producer output)
> ships as the proof workload for cross-tier routing.

This is the iteration where the Pillar 7 verdict carry-forward from
0.2.16 closes — the cascade is the natural exercise for cross-tier
routing because different Auditor model families can live on
different tier hosts. Pairing the Pillar 7 deliverable with the
cross-tier deliverable means each surface validates the other.

**Workstream skeleton (5 workstreams expected):**
- W0 — Carry-forward closure + cross-tier routing design
  (potentially a new ADR amending 0008's `on_missing="cloud"`
  reservation)
- W1 — Cross-tier OTLP trace propagation
- W2 — Cascade orchestrator with cross-host stages
- W3 — Pillar 7 cascade re-run (paired Auditor)
- W4 — Pillar 7 verdict + close

**Architectural inheritance:**
- ADR 0008 `on_missing="cloud"` reservation likely promoted to
  implemented status.
- ADR 0007 multi-host coordination (load balancing, registry sync)
  amendments expected.

## §4 Multi-iteration graduation criterion (Form 3 — manual checklist)

Iteration 3 graduates as a unit when:

1. [ ] 0.3.1 closed cleanly (partial tier on tsP3 verified via
       per-sub-iter Form 1 fish test)
2. [ ] 0.3.2 closed cleanly (full tier on cloud verified via
       per-sub-iter Form 1 fish test + Form 3 manual checklist)
3. [ ] 0.3.x cross-tier closed cleanly (cross-tier trace captured,
       Pillar 7 verdict rendered with evidence)
4. [ ] All three tiers (base, partial, full) have at least one
       runnable container instance with current `aho:0.3.x` image
5. [ ] Per-tier OTEL signals visible in their respective
       collectors with correct `aho.deployment.mode` resource
       attribution
6. [ ] Cross-project contamination vigilance held throughout
       (zero contamination per CLAUDE.md discipline)
7. [ ] Phase 0 exit criteria reviewed for graduation eligibility
       (per `artifacts/phase-charters/aho-phase-0.md`)

## §5 Out of scope (umbrella-level)

- **Phase 1 work.** Multi-project orchestration, multi-machine
  parallel execution, federated registries — Phase 1 charter,
  not Iteration 3.
- **External-consumer reference pack assembly.** Mercor pack
  finalization stays graduated to its own iteration (paired with
  any external customer engagement that surfaces).
- **Kubernetes operator / Helm chart full implementation.** May
  enter scope at 0.3.2 W3 if full-tier deployment is K8s-native;
  out of scope otherwise.
- **AMD ROCm / Apple Metal tier support.** ADR 0007 §Revisit
  Triggers item 3 fires when a non-NVIDIA host joins the fleet;
  not in 0.3.x scope unless triggered.
- **CI for image build.** Local podman build on NZXTcos (the
  authoring host) remains the build path through Iteration 3.
- **Auditor role-prompt bifurcation redesign.** Long-standing
  carry from 0.2.x; its own iteration when prompt-engineering
  work is the iteration's center of gravity.
- **Auto-scaling of cloud serving plane.** 0.3.2 ships a static
  full-tier instance; auto-scaling is Phase B / Phase 1.

## §6 Cross-iteration carry tracking

Inheriting from 0.2.16 + 0.2.17 close-time carry-forwards:

- **Engine-selection ADR + bridge live wire-up** — paired with
  whichever 0.3.x sub-iteration first needs alert delivery on
  the cloud-tier (likely 0.3.2 W3).
- **Pillar 7 cross-model cascade re-run** — folded into 0.3.x
  cross-tier sub-iteration (§3.3 above).
- **Mercor reference pack assembly** — graduated to its own
  iteration; not Iteration 3 scope unless an external consumer
  forces it.
- **Cross-tier dispatcher routing semantics** — partially
  addressed by ADR 0008's `on_missing="cloud"` reservation;
  fully implemented in 0.3.x.
- **Multi-host Ollama load balancing** — ADR 0008 §Out of Scope
  lists this; partially addresses in 0.3.x cross-tier work.

## §7 Process discipline (umbrella-level reminders)

- Each sub-iteration plan opens with ADR 0006 deliverable
  paragraph + graduation criterion. The umbrella charter sets the
  multi-iteration objective; the per-sub-iter plans set their own
  scope.
- ADR numbers are not pre-allocated. Sub-iterations enumerate
  `artifacts/adrs/` at execution time and pick the next slot.
- Pillar 11 stays load-bearing throughout: human holds keys, no
  agent commits, no agent surfaces git operations. Cloud-host
  provisioning (0.3.2 W0) is Kyle-driven; agents prepare the
  artifacts (Terraform-equivalent or shell scripts) but do not
  execute provisioning.
- Cross-project contamination vigilance continues. Iteration 3 is
  the first time aho deploys to a non-Kyle-owned machine; this
  is exactly the surface where contamination risk goes up
  (cloud-side conventions may bleed into aho-internal language).
  Discipline holds.

---

*Iteration 3 charter — aho Phase 0. Created 2026-05-01 during
0.2.16 W4. Sub-iteration plans (`aho-plan-0.3.1.md`,
`aho-plan-0.3.2.md`, …) land at sub-iteration open and open with
ADR 0006-mandated deliverable paragraph + graduation criterion.
This charter does not bind those plans — it sets the
multi-iteration shape they fit into.*
