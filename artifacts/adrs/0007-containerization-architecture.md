# ADR 0007 — Containerization Architecture

**Status:** Accepted
**Date:** 2026-05-01
**Iteration of record:** aho 0.2.16 W4
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal — packaging and deployment shape
for 0.2.17 onward. Inherits in 0.3.x for partial- and full-tier deployment;
informs Phase B/C architectural decisions.

---

## Context

Through 0.1.x and 0.2.x aho has run on NZXTcos via `install.fish` and
per-machine drift management. The harness, the pipeline, the dispatcher,
the dashboard, and the model bundle live as a colocated single-machine
deployment. Migrating to a second machine (tsP3, A8cos, Luke's box)
requires re-running install.fish and absorbing whatever drift the target
machine introduces — Arch family detection, VRAM tier, GPU vendor
peculiarities, ollama service hygiene, Python virtualenv shape.

The future-state architecture (per Kyle's strategic direction) places
aho's harness at the edge — engineer workstations, both local and remote
— with the heavy model compute at the center, on a Tier 2 cloud serving
plane. Bridging today's single-machine local loop to tomorrow's
distributed deployment requires a portable artifact that:

1. Encapsulates the harness + middleware + project layers in a form
   that pulls and runs on any compatible host without per-machine
   install.fish drift.
2. Adapts its model bundle to the host's GPU capacity at install time,
   rather than baking a single fat-or-skinny bundle into the image.
3. Preserves Pillar 11's secrets posture — secrets stay on the host,
   never in the image, never in the registry.
4. Targets a runtime that fits the CachyOS-posture local hosts and a
   Linux-on-cloud-VM serving target without runtime-hopping.

The container is the artifact. This ADR specifies its shape.

## Decision

### Single image, tier-conditional model bundle

aho ships as **one** image: `aho`. The image contains the harness, the
middleware, the project layers, the Python virtualenv, the `aho` CLI,
and Ollama itself. The image does **not** contain model weights.

The image's tier is determined at install time, not at build time, by
`install.fish` running on the host. install.fish polls
`nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits`,
classifies the host into a tier, and pulls the tier-appropriate model
set into a host-volume that the container mounts:

| Tier | VRAM threshold | Model bundle | Target hosts |
|---|---|---|---|
| **base** | < 12 GB or no nvidia-smi | nemotron-mini:4b (~2.7 GB), nomic-embed-text (~274 MB), llama3.2:3b (~2.0 GB) — total ~5 GB | iGPU hosts, NZXTcos (8 GB), integrated-only laptops |
| **partial** | 12 GB to < 32 GB | base bundle + qwen3.5:9b (~6.6 GB), haervwe/GLM-4.6V-Flash-9B (~8.0 GB) and any future ≤16-GB-fit models | tsP3 (16 GB), mid-tier discrete-GPU workstations |
| **full** | ≥ 32 GB | partial bundle + Nemotron Super (~42 GB) and future large-model additions | A100/H100-class cloud GPU pools (GCP intranet target) |

Models are stored in a host-mounted volume (e.g.,
`~/.local/share/aho/models/`) that Ollama inside the container reads from
via bind-mount. Pulling a model is host-side; loading a model is
container-side. The image's disk footprint stays bounded.

### NZXTcos categorization

NZXTcos (8 GB VRAM) is **base tier**. The threshold ≤ 12 GB places it
unambiguously in base; no caveat applies.

The historical NZXTcos behavior — running partial-tier models on the
bare host with `num_gpu` partial-CPU-offload workarounds — is
**out of scope for containerized deployment**. Those workarounds remain
available to the operator on the bare host (the legacy install.fish
path through 0.2.x close), but they are not what the container ships
or supports. Within the container, NZXTcos serves the base-tier bundle
and only the base-tier bundle.

Operational consequence: 0.2.17 development on NZXTcos validates the
base-tier container's harness pipeline against base-tier models inside
the container. Partial-tier work on NZXTcos during 0.2.17 development
is handled by ADR 0008's hybrid-mode dispatcher (host's native Ollama
serves partial-tier dispatches; container's bundled Ollama serves
base-tier dispatches). The hybrid mode is gated on an environment
variable so it cannot leak into production deployment.

### install.fish behavior

install.fish gains a tier-detection block that runs before model pulls:

```
function detect_tier
    if not command -q nvidia-smi
        echo base
        return 0
    end
    set vram (nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    if test $vram -lt 12000
        echo base
    else if test $vram -lt 32000
        echo partial
    else
        echo full
    end
end
```

The detected tier maps to a model-bundle list (literal
`ollama pull <model>` invocations per tier). install.fish runs the
appropriate pulls into the host-mounted models directory. Re-running
install.fish on a host with an unchanged tier is a no-op for already-
pulled models; tier changes (e.g., GPU upgrade) trigger additional
pulls without re-pulling the existing base.

Fallback: hosts without nvidia-smi default to base tier. AMD ROCm and
Apple Metal hosts are explicitly out of scope for the tier detection in
this ADR; they fall to base tier and are unblocked when ROCm/Metal
support is folded into a later iteration.

### Secrets model

Per Pillar 11, secrets do not live in the image, in the registry, or in
the container's writable layer. The container reads secrets from a
host-mounted path via bind-mount:

| Secret | Host path (default) | Container mount | Access |
|---|---|---|---|
| age identity (per-machine) | `~/.local/share/aho/age/identity.txt` | `/opt/aho/secrets/age/identity.txt` (read-only) | container reads, host owns |
| fernet-encrypted bulk secret bundle | `~/.local/share/aho/secrets/bundle.enc` | `/opt/aho/secrets/bundle.enc` (read-only) | container decrypts at runtime, host owns |

The container's user inside the image has read permission on the
mounted secret paths and no write permission. The age identity stays
per-machine — moving aho to a new host requires the operator to mint a
new age identity on that host and re-encrypt the bulk bundle for it.

The image itself ships with **zero** secrets baked in. The image is
therefore safe to publish to a registry without per-host
re-encryption.

### Registry choice

Starting decision: **local-first registry**. Either a local Harbor (or
equivalent) on the home network or a workspace/personal namespace on
GitHub Container Registry (e.g., `ghcr.io/socfoundry/aho`). The
specific local registry is decided in 0.2.17 W0; this ADR records the
deferral.

Cloud-side registry (the GCP intranet deployment target) is **not**
decided in this ADR. Phase C work selects the cloud registry once
serving-plane infrastructure decisions are firmer. Until then, the
cloud-tier full image is built and stored in the local registry; it
moves to the cloud registry whenever Phase C lands.

Multi-engineer pull sync (synchronizing image versions across
engineers' workstations from a shared registry) is also deferred.
0.2.17 ships single-operator (Kyle); Phase B work introduces a second
engineer and at that point the registry choice is revisited with
multi-engineer access semantics.

### Runtime choice

Starting preference: **Podman**. Rationale:

- Rootless by default. Aligns with the principle of least privilege
  for a single-operator workstation deployment.
- Daemonless. No persistent root-owned process; container lifetimes
  are tied to the operator's session.
- CachyOS first-class support. NZXTcos and other CachyOS hosts in the
  fleet ship with podman in the package mirrors and the systemd-user
  integration is mature.
- Drop-in `docker` CLI compatibility (`alias docker=podman` works for
  the surface we use). Migration cost from docker-based examples is
  near-zero.
- OCI-compliant. Images built by podman pull and run under docker; no
  vendor lock.

Docker is the **fallback** runtime — supported when Podman is not
available on a host (e.g., a future macOS or Windows engineer
workstation where Docker Desktop is the path of least resistance), but
not the recommended runtime for the Linux fleet that the 0.2.17 / 0.3
deployment targets.

The decision is **soft-deferred** — 0.2.17 W0 confirms Podman runs
cleanly on NZXTcos before locking the choice. If Podman surfaces a
blocker in W0 (e.g., GPU passthrough fragility under rootless mode),
the fallback to Docker is a one-decision pivot with no architectural
cascade.

### Runtime choice — 0.2.17 W0 confirmation (Podman engaged)

**Outcome: Podman, as originally preferred.** 0.2.17 W0 Bucket 2
confirmed Podman runs cleanly on NZXTcos. `podman 5.8.2` installed
via pacman, `podman run --rm hello-world` returned cleanly after a
one-time fix for the rootless overlay-storage backing (installed
`fuse-overlayfs`, ran `podman system reset --force` to clear stale
storage state, re-ran hello-world successfully). `nvidia-container-toolkit
1.19.0-1.1` and `libnvidia-container 1.19.0-1.1` installed alongside.

The soft-deferral resolves positively to Podman. Docker remains the
documented fallback per §Runtime choice above, available without
architectural cascade if a future host fails Podman.

**Mid-bucket detour worth recording.** Initial attempts to install
Podman via pacman failed at the network layer with corrupted CachyOS
package databases. Investigation surfaced the root cause as Tailscale
split-DNS hijacking specific CachyOS mirror domains and returning
incorrect IPs — not aho-introduced, not CachyOS-mirror-broken.
Resolved by Kyle's host-side split-DNS fix excluding the mirror
domains from Tailscale's resolver. The detour included a tentative
flip to Docker (already installed on NZXTcos at 29.4.1) under the
working assumption that the package-management failure was unrecoverable;
this section was originally drafted with "Docker engaged" before the
DNS root cause was identified. Reverted to Podman in the same W0
Bucket 2 once `pacman -S podman` succeeded post-DNS-fix.

The Tailscale-DNS-hijack incident is captured separately under
F-host-001 in `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
(re-targeted from "fix CachyOS infrastructure" to "document split-DNS
exclusions for package-mirror domains").

**Container-level deliverables in W0–W4 are unchanged from the
original plan.** Image build (W1), tier manifest (W2), hybrid-mode
dispatcher (W3), and telemetry wiring (W4) proceed under Podman as
originally scoped. `host.containers.internal` (Podman default) is
the hybrid-mode network address per ADR 0008.

### GPU passthrough deferral — 0.2.17 W0

**B2.3 (rootless Podman + NVIDIA Container Runtime end-to-end probe)
is deferred across the post-W0 reboot boundary.** The deferral is
explicit and bounded; it is not a verification skip.

**Empirical state at deferral:**
- `podman 5.8.2` installed and rootless hello-world verified (B2.1
  passing).
- `nvidia-container-toolkit 1.19.0-1.1` and `libnvidia-container
  1.19.0-1.1` installed (B2.2 passing).
- `sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml`
  fails with `failed to initialize NVML: Driver/library version
  mismatch`. Root cause: pacman update brought userspace libraries
  to `595.71.05` (`/usr/lib/libnvidia-ml.so.595.71.05`) while the
  running kernel still has the prior NVIDIA module loaded
  (`595.58.03`-class per `nvidia-smi` reporting before the upgrade).
  Standard fix is host reboot; module reload (`modprobe -r nvidia*
  && modprobe nvidia`) virtually always fails on an active desktop
  session because the modules are in use by Plasma/Wayland/X.

**Why deferral is acceptable for 0.2.17 W0/W3:**
ADR 0008's hybrid-mode dispatcher routes partial-tier dispatches
to `host.containers.internal:11434` — the host's *native* Ollama,
which uses the host GPU directly with no container in the path.
0.2.17 development on NZXTcos exercises that hybrid path; the
container does not need GPU passthrough for any 0.2.17 deliverable.
Container GPU passthrough becomes load-bearing for production-tier
(0.3.x) deployment, where the container's bundled Ollama serves
all dispatches and must reach the host GPU through NVIDIA Container
Runtime.

**Post-reboot validation — one-command exercise:**

```fish
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml \
  && podman run --rm --device nvidia.com/gpu=all \
       docker.io/nvidia/cuda:12.0-base nvidia-smi
```

Expected: `nvidia-smi` output from inside the container showing the
host's GPU (RTX 2080 SUPER, 8 GB VRAM) and the post-update driver
version (595.71.05). If both lines exit zero with that output, B2.3
passes. If either fails post-reboot, the failure is real (not
transient pre-reboot mismatch) and gets a follow-up surface.

**This validation is a 0.3.x deliverable gate, not a 0.2.17 gate.**
It can land at any point between this W0 close and 0.3.x W0 — the
W0 acceptance archive notes the deferral with this command as the
post-reboot verification step. Until validated, the
production-tier-on-base-host scenario is unsupported (ADR 0007's
§NZXTcos categorization already says NZXTcos's role inside the
container is base-tier-only; production tier is cloud or partial
host).

A reasonable layer order — non-normative, included so 0.2.17 W1's
Dockerfile work has a starting point:

1. base layer: minimal Debian/Ubuntu/CachyOS base + Python runtime +
   ollama binary.
2. system-deps layer: apt/pacman packages aho needs (curl, git,
   build-essential, NVIDIA container toolkit if applicable).
3. python-deps layer: aho's pyproject.toml dependencies via uv or pip.
4. aho-source layer: `src/aho/`, `bin/`, `artifacts/harness/` mounted
   into `/opt/aho/`.
5. entrypoint layer: container entrypoint that respects host secrets
   mount, host models mount, and `AHO_DISPATCH_HYBRID_MODE` env (per
   ADR 0008).

Models are **not** a layer. Models are host-volume content.

### Council roles

**Added in 0.2.17 W5** — consolidating four iterations (W0/W1/W2/W3/W4)
of in-container council deployment work into the ADR that owns the
container's runtime shape. The chat-side architecture artifact
`aho-base-container-architecture.md` §Seat assignments / §Auditor
contract / §Anti-rubber-stamp hardening sections are the source; this
subsection makes those decisions repo-resident and authoritative.

Five seats compose the council. Two are external (drafter, executor —
both run on operator's chat / CLI surfaces, not in the container).
Three are in-container (auditor, triage, retrieval). Each seat has a
named locus, a fixed model at base tier, and a contract surface.

| Seat | Locus | Base-tier model | Contract surface |
|---|---|---|---|
| **Drafter** | external (Claude web) | n/a — chat-resident | Plans, plan-doc authoring, drafter arbitration of audit findings, gap-net for what auditor cannot catch by design. Persistent across chat sessions. |
| **Executor** | external (Claude Code or Gemini CLI) | n/a — workstation-resident | Per-iteration; codified per iteration in plan doc. Implements deliverables; emits acceptance archive; emits OTEL telemetry; never invokes git. |
| **Auditor** | in-container | `llama3.2:3b` | Structural spot-check: claim-vs-artifact verification, contract-shape validation, invariant resolution. Confidence floor 0.85 structurally enforced. Disposition shape `clean | halt | surface_to_drafter` with `clean` unreachable below threshold. Deterministic post-hoc filter on RAG-aware findings (`aho.council.audit_finding_filter`, W4 D1) suppresses fake-ID-on-registered-anchor failure mode. Partial-tier and full-tier auditor models deferred to 0.3.x roadmap. |
| **Triage** | in-container | `nemotron-mini:4b` | Classification only. Raise-on-malformed (no `categories[-1]` fallback per G083). |
| **Retrieval** | in-container | `nomic-embed-text` + ChromaDB host-mounted volume | Recency-weighted query; sole embedding source; feeds context to triage and audit. |

#### Role-collapse trip-wire

`executor_model_family ≠ auditor_model_family` enforced as an OTEL
invariant at base tier. The trip-wire fires if executor and auditor
share a model family — Llama (Meta) vs. Claude/Gemini (Anthropic /
Google) is the cross-family separation that holds at 0.2.17 base tier.
The trip-wire surface lives at `src/aho/dashboard/lego/role_collapse_brick.py`
and reads OTEL resource attributes `aho.role` plus model-family
metadata; brick turns red if executor and auditor resolve to the same
family on the same workstream's events.

Pillar 7 ("generation and evaluation are separate roles") is the
binding constraint. The trip-wire makes the separation falsifiable
and observable at runtime.

#### Anti-rubber-stamp hardening

Three failure modes have been closed across the 0.2.17 audit-seat
work; together they form the base-tier anti-rubber-stamp posture:

1. **G083 raise-on-malformed.** Triage and audit primitives raise on
   malformed model output (missing fields, schema violations, unknown
   severity vocabulary outside `SEVERITY_SYNONYMS`). No silent fallback
   to a default category or default disposition. Implemented in
   `src/aho/council/triage.py` and `src/aho/council/audit.py`.

2. **GLM removed from auditor candidacy at base tier.** GLM's OOM
   behavior under co-resident loading on 8GB-VRAM hosts kills all
   loaded models. At base tier (NZXTcos, < 12GB VRAM) GLM is not in
   the auditor candidate set. Llama3.2:3b is the canonical base-tier
   auditor; GLM moves into the partial-tier candidate set on tsP3
   (16GB VRAM) under 0.3.x roadmap.

3. **Llama confidence-floor lock + W4 deterministic post-hoc filter.**
   Llama3.2:3b at 32K context cannot fit the full carry-forwards file
   + ADRs + gotcha registry alongside an audit target. Without
   reference-resolution context, the model systematically flags
   carry-forward IDs that match its placeholder-syntax heuristic as
   "looks fake." Two layers close the gap: (a) RAG enrichment via
   `aho.council.audit_ref_lookup` retrieves "is this ID registered?"
   from ChromaDB and inlines the answer into the audit prompt's
   `## Registered references` section (W3 D4); (b) deterministic
   post-hoc filter (`aho.council.audit_finding_filter`, W4 D1)
   inspects each finding for a registered anchor in description AND a
   fake-ID phrase from the canonical set, suppressing only when both
   match. Filter is deterministic and does not bet the architecture on
   small-model prompt-following — the model can ignore the
   registered-references rule and the failure mode is still contained.

Confidence-floor lock: the `clean` disposition is structurally
unreachable below the 0.85 confidence threshold. Below the floor, the
disposition collapses to `surface_to_drafter` so the drafter
arbitrates rather than the model rubber-stamping. Implementation lives
inside `aho.council.audit` disposition resolution.

#### Cross-references (sealed archives)

- W2 acceptance archive (in-container llama auditor first deployment;
  baseline materiality counter wiring): sha256
  `4a5ab02b8b831de1df3c5f45bf8578d9f641fd2a5ee6de9eed9a0b6fb213a2dd`.
- W3 acceptance archive (RAG enrichment landing; W0 false-positive
  closed; W2 self-audit false-positive persisted under same prompt
  rule): sha256
  `9ed9a88a5382d89f116083a1cf87de586ddd997da975ef8cd5091aa748c81790`.
- W4 acceptance archive (deterministic post-hoc filter landing;
  fake-ID-on-registered-anchor failure mode structurally contained;
  F-0.2.17-W2-006 + F-0.2.17-W3-001 closed via W4 D1): sha256
  `949908ffd933cfd9e5121432c5fd7294b060a39e17e4a2259d3a4cdc040c8300`.
- W4 audit archive (llama self-audit verbatim disposition
  `surface_to_drafter`; drafter-arbitrated to `pass_with_findings`):
  sha256 `9d5ab9ec11ba302a93cabf0fd33ed7d8963b58346eb208584e697e5a3d82a13a`.

These archives are **sealed** — modifications post-emit forbidden.
Re-audits create `audit/W{N}-v2.json`, `v3`, etc. per Adversarial
Authorship convention.

### k8s-readiness

The 0.2.17 image is built to be k8s-deployable in principle, even though
0.2.17 does not ship Kubernetes manifests. 0.3.x adds k8s manifests; 0.2.17
ensures the image they will reference does not bake in single-host
assumptions.

Five properties bind the image build:

1. Configuration via environment variables, not in-image config files.
   Volume-mountable config supports k8s ConfigMaps.
2. Secrets read from filesystem paths inside the container; k8s Secrets
   are volume-mounted as files.
3. Logs to stdout/stderr; OTEL telemetry sinks (host-mounted today) are
   not in scope here — that is signal export, not log output.
4. Graceful SIGTERM handling within 30s default
   terminationGracePeriodSeconds.
5. HTTP health-check endpoints at `GET /healthz` (liveness, no deps) and
   `GET /readyz` (readiness, tier+secrets+models reachable). Default port
   8080, env-configurable.

These are W1 acceptance gates. Out of scope for this iteration: actual
k8s manifests, Helm charts, Kustomize overlays, multi-replica behavior.
Those are 0.3.x work.

## Rationale

> The container's tier reflects what the host can support cleanly,
> not what workarounds enable.

Three forces shape this architecture:

1. **Portability is the goal, not image fatness.** A single image with
   a tier-conditional model bundle pulled at install time is dramatically
   smaller than three tier-specific images, and the install.fish-driven
   tier detection puts the right models on the right host without a
   build-time variant explosion. The cost is that install.fish runs once
   per host; the benefit is that the registry stores one image instead
   of three and image-version skew across tiers becomes impossible.

2. **Pillar 11 demands secrets stay host-side.** A container that bakes
   secrets in is a container that cannot be safely published to a
   registry. The host-volume secrets model preserves the existing
   per-machine age identity convention with zero change to the
   harness's secret-read path; the only new behavior is the bind-mount
   shape declared at container start.

3. **Production hard-edge separates from dev hybrid.** ADR 0008 covers
   what happens when the dispatcher is asked for a model the host's
   tier doesn't have. This ADR's job is to make the tier classification
   itself unambiguous: NZXTcos is base-tier *as a container host*. The
   partial-tier work the operator does on NZXTcos during 0.2.17
   development uses the host's native Ollama via the hybrid-mode env
   gate; that mode never leaks into production base-tier deployments
   because production deployments do not set the env var.

The Podman default and the local-registry-first deferral both follow
the same logic: pick the choice that fits the current host fleet and
the current operator count, document the deferral, revisit when the
fleet or operator count changes. Pre-deciding the cloud registry or
forcing a Docker default would optimize for a future state that hasn't
materialized.

## Consequences

### Positive

- aho gains a portable artifact that pulls cleanly across the host
  fleet. Onboarding a new host (Luke's box, a new tsP3 partition, a
  cloud VM) reduces to install.fish run + image pull + container run.
- Per-machine drift compresses to "what tier is the host" plus host
  secret materials. install.fish becomes lighter — no Python
  virtualenv setup, no pip install, no CachyOS-vs-Ubuntu branching at
  the harness level.
- Image versioning becomes a registry concern; local installs pin a
  tag, upgrades are explicit `podman pull` operations.
- Pillar 11 stays uncompromised. Secrets continue to live on the host;
  the registry is publish-safe.
- The cloud-side full-tier deployment (Phase C target) inherits this
  same image with a different tier classification. The architectural
  shape stays one-image-many-tiers; the cloud serving plane is a
  full-tier installation, not a separate artifact.
- ADR 0008's dispatch hybrid mode has a clean surface to bind to —
  the env var is read at container start and the dispatcher's
  routing decision flows from it.

### Negative

- install.fish gains a new responsibility (tier detection + model
  pull) that a single source-of-truth must own. Bug surface is real:
  mis-detection on an unusual GPU, mis-mapping of VRAM thresholds, or
  failure to fall back to base tier on a non-NVIDIA host all become
  failure modes. Mitigation: 0.2.17 W2 explicitly tests tier
  detection on NZXTcos and at minimum a non-NVIDIA fallback path.
- Image build adds a CI surface that does not exist today. Local
  podman build on Kyle's machine is the 0.2.17 starting point; multi-
  engineer image build coordination is a Phase B problem. Mitigation:
  pin the build to one host (NZXTcos) for 0.2.17 and 0.3.1, formalize
  later.
- Container abstraction adds a debugging layer. Failures inside the
  container can be harder to diagnose than failures on the bare host.
  Mitigation: aho's existing event log and OTEL pipelines emit from
  inside the container as well as outside; the harness-watcher's
  diagnostic surface is preserved.
- GPU passthrough configuration (NVIDIA Container Toolkit) is a
  per-host install step that lives outside aho's repo. Mitigation:
  install.fish documents the dependency; failure to configure
  passthrough surfaces as a clear container-start error rather than
  a silent fallback to CPU.
- The hybrid-mode env var (per ADR 0008) is a development-only
  affordance. Risk that it leaks into a production deployment.
  Mitigation: image entrypoint logs the hybrid-mode state at startup;
  production deployments add a startup assertion that the var is
  unset.

### Neutral

- The image stays runnable under Docker as a fallback; OCI compliance
  means the artifact is not tied to Podman.
- Existing `install.fish` behavior on the bare host is preserved as a
  legacy path through 0.2.x close. 0.2.17 introduces the container
  path alongside; deprecating the bare-host path is not in this
  ADR's scope.
- Phase C cloud registry choice stays deferred. The local registry
  acts as the single source of truth until Phase C lands, at which
  point image promotion (local → cloud) is a registry-mirror or
  re-tag operation, not a re-build.
- The model bundle's per-tier list is data, not architecture. Model
  upgrades (qwen3.5 → qwen-next, llama3.2 → llama4 if it exists) are
  amendments to the tier-bundle table, not amendments to this ADR.

## Out of Scope

- **Multi-engineer registry sync.** Coordinating image versions across
  multiple engineer workstations pulling from a shared registry is
  Phase B work. 0.2.17 / 0.3.1 ship single-operator.
- **Signed-image policy and SBOM emission.** Cosign signing,
  SLSA-style provenance attestations, SBOM generation — these become
  load-bearing when external consumers (Mercor, future customers,
  enterprise audit) require them. Phase B candidate.
- **Cloud-side registry choice.** GCP Artifact Registry vs. self-hosted
  Harbor on a GCP VM vs. another option — Phase C work, decided when
  serving-plane infrastructure decisions are firmer.
- **Kubernetes manifests for full-tier cloud deployment.** Single-pod
  vs. multi-pod-with-sidecar-Ollama, ConfigMap shape for tier
  designation, Secret shape for the age identity rotation, Service
  exposure for the harness-watcher dashboard — all 0.3.x work, not
  this ADR's scope.
- **AMD ROCm and Apple Metal tier detection.** install.fish's tier
  detection in 0.2.17 covers NVIDIA only. Non-NVIDIA hosts default to
  base. ROCm and Metal support, when added, are tier-detection
  amendments, not architectural changes — folded into a later iteration.
- **Container-internal ollama hot-reload of newly-pulled models.**
  When install.fish pulls a new model post-container-start, the
  running container needs to either restart or trigger an Ollama
  reload. Behavior is a 0.2.17 W3 implementation question; this ADR
  does not pre-decide it.
- **Image promotion automation.** Tag promotion from `aho:0.2.17-rc1`
  to `aho:0.2.17-base` is operator-driven in 0.2.17. Automation lands
  when CI lands.
- **Telemetry pipeline running inside the container vs. on the host.**
  aho's otelcol-contrib service is presumed to stay host-side in
  0.2.17 (the container emits to `host.containers.internal:4317` or
  equivalent). A container-internal collector deployment is a
  later choice.

## Alternatives Considered

### Three tier-specific images

Build three images: `aho-base`, `aho-partial`, `aho-full`. Each bakes
its tier's models in. Operator pulls the right image for their host.

**Rejected.** Image fatness explosion (full-tier ~42+ GB image) and
image-version skew across tiers (partial gets bumped to 0.2.17.1
while full stays on 0.2.17 because of pull cost) make the registry
operationally painful. Single-image-with-host-volume-models is
strictly simpler.

### Build-time model bundling via build-arg

Single Dockerfile, three builds with `--build-arg TIER=base|partial|full`
that include or exclude model layers conditionally.

**Rejected.** Same fatness problem, plus a build-arg matrix that
multiplies CI cost. The host-volume model store is the right place
for ~50 GB of weights regardless of containerization.

### Docker as the default runtime

Adopt Docker as the default; document Podman as an alternative.

**Rejected for Linux fleet.** Docker daemon's root-owned process
contradicts the principle-of-least-privilege posture aho has held
through 0.2.x. Daemonless Podman aligns with the harness's
single-operator-on-CachyOS deployment shape. Docker stays as a
fallback for hosts where Podman is not the path of least resistance
(future Windows / macOS engineer onboarding).

### Bake an age identity into the image at build time

Generate a per-image age identity, bake it into the image, encrypt
the bulk secret bundle for that identity.

**Rejected.** The image becomes per-host (one image per identity)
and registry publishability collapses. The point of containerizing
is portability; per-image identity defeats portability.

### Skip containerization entirely; rely on install.fish + Ansible/Salt

Stay with bare-host install.fish, layer a configuration-management
tool on top for multi-host orchestration.

**Rejected.** Configuration management does not solve the per-host
drift problem at the harness level — Python virtualenv state,
Ollama service hygiene, dispatcher cache state all stay per-host
under any CM tool. Containers absorb that surface into one artifact.

### A single fat image with all models

Build one image at full-tier and let base-tier hosts pull-and-only-
load the small ones.

**Rejected.** ~50 GB image pulls on a base-tier host. Bandwidth
cost on first pull is unacceptable for engineer workstation onboard.

### Helm chart starting point

Skip the local-podman path and start with a Helm chart targeting
Kubernetes.

**Rejected for 0.2.17.** The local-loop is base-tier on NZXTcos.
Kubernetes is full-tier on GCP. Starting with the Helm chart
optimizes for the destination state when the source state is what
0.2.17 needs to ship. Helm chart is a 0.3.x deliverable when the
full-tier deployment is the iteration's focus.

## Revisit Triggers

This ADR is amended (not necessarily replaced) when any of the
following become true:

1. **A second engineer is onboarded to the aho fleet.** Multi-engineer
   image build coordination, registry access semantics, and image
   version pinning policy all need decisions — those amendments
   live in a follow-on ADR or a Phase B amendment to this ADR.

2. **External consumers (Mercor, customers) require signed images
   with SBOM.** Cosign + SLSA + SBOM tooling lands; this ADR's
   build/publish section is amended with the signing convention.

3. **A non-NVIDIA host (ROCm or Metal) joins the fleet.** Tier
   detection and the GPU passthrough section are amended with the
   new vendor's classification rules.

4. **A cloud-tier deployment lands (Phase C).** The cloud registry
   choice is decided; the soft deferral becomes a hard pick;
   container-internal vs. host-side collector becomes a real
   question.

5. **0.2.17 W0 surfaces a Podman blocker.** Runtime preference flips
   to Docker; this ADR's §Runtime choice section is amended with
   the empirical reason.

## References

- `artifacts/iterations/0.2.17/aho-plan-0.2.17.md` — first iteration
  to consume this ADR; W0/W1/W2/W3/W4 outline aligns to it.
- `artifacts/adrs/0008-dispatcher-missing-model.md` — the dispatch-
  side counterpart to this ADR's tier classification; together they
  define what a tier means at runtime.
- `install.fish` — tier-detection block lives here once 0.2.17 W2
  lands.
- `artifacts/iterations/0.3-phase-plan.md` — phase-level
  consumption; partial- and full-tier deployments inherit this ADR.
- `artifacts/harness/base.md` §The Eleven Pillars — pillar 11
  (human holds the keys / secrets-on-host) is the binding constraint
  on the secrets model.
- 0.2.15 W0 install.fish work — the bare-host predecessor of the
  containerized install path.
