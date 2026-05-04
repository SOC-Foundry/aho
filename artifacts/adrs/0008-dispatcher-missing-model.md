# ADR 0008 — Dispatcher Behavior on Missing Model Family

**Status:** Accepted
**Date:** 2026-05-01
**Iteration of record:** aho 0.2.16 W4
**Decision owner:** Kyle Thompson (signs), Claude Code (drafted), Gemini CLI (audits)
**Context surface:** aho project-internal — dispatcher routing semantics
under tiered containerized deployment. Binds 0.2.17 W3 dispatcher work.

---

## Context

ADR 0007 establishes that aho ships as a single tier-aware container
image whose model bundle is determined at install time by host GPU
capacity. A base-tier host has nemotron-mini, nomic-embed-text, and
llama3.2:3b. A partial-tier host adds qwen3.5:9b and GLM-4.6V-Flash-9B.
A full-tier host adds Nemotron Super.

Today's dispatcher (`src/aho/pipeline/dispatcher.py`) operates under an
implicit assumption that every request maps to a model the host has
loaded. That assumption holds in 0.2.x because aho runs on one
machine with all five model families pulled. It stops holding the
moment 0.2.17 ships a base-tier container to NZXTcos: a request for
`family=qwen` on a base-tier host has no local model to dispatch to.

The dispatcher needs a defined behavior for this case. Four options
are on the table:

**Option A — Hard error.**
Dispatcher refuses the request and raises `ModelNotAvailableError`
(new typed exception, G083-compliant). The caller decides how to
recover.

**Option B — Local fallback.**
Dispatcher routes the request to the nearest-available local model
(by some defined nearness metric), logs a degradation warning, and
returns the fallback's output to the caller.

**Option C — Cloud route.**
Dispatcher routes the request to a configured remote endpoint that
hosts the missing model (a cloud-tier serving plane). The caller is
unaware that the dispatch went off-host.

**Option D — Hybrid (development affordance).**
On the host running aho's container, base-tier dispatches go to the
container's bundled Ollama. Partial- or full-tier dispatches escape
the container via the host network and reach the host's *native*
Ollama (which has the partial- or full-tier models). The development
operator can do partial-tier work on a base-tier-classified container
host.

Each option is operationally distinct and has different failure-mode
characteristics; they are not freely substitutable.

A second forcing constraint: 0.2.17 development happens on NZXTcos,
which is a base-tier *container host* but has historically run
partial-tier models on the bare host. That bare-host capability does
not vanish when the container is introduced — the operator still
wants to do partial-tier development work on NZXTcos. If the
container can only ever dispatch to base-tier models, partial-tier
development requires leaving the container, which defeats the
container's value during the iteration that introduces it.

## Decision

### Production deployment: Option A (hard error)

In production deployment — i.e., the container is running on a host
where `AHO_DISPATCH_HYBRID_MODE` is **unset** — the dispatcher
hard-errors on a request for a model family the host's tier bundle
does not include.

Specifically:

1. A new typed exception `ModelNotAvailableError(DispatchError)` is
   added to `src/aho/pipeline/dispatcher.py`.
2. At dispatcher entry, the requested family is validated against
   the host's tier bundle (read from the tier manifest at the
   host-mounted path described in §Tier manifest contract below).
3. If the family is not in the bundle and `AHO_DISPATCH_HYBRID_MODE`
   is unset, raise `ModelNotAvailableError` with the requested
   family, the host's tier, and the bundle contents in the
   exception payload.
4. Caller-side error handling decides whether to retry against a
   different family, escalate to a remote endpoint, or surface to
   the operator. The dispatcher does not silently substitute.

### Development: Option D (hybrid)

When `AHO_DISPATCH_HYBRID_MODE=1` is set on the container's
environment, the dispatcher's family-not-in-bundle branch routes
the request to the *host's* Ollama at a configured network address
(`AHO_DISPATCH_HYBRID_HOST_URL`, default
`http://host.containers.internal:11434` for Podman; equivalent
docker-host alias for Docker). Specifically:

1. If `AHO_DISPATCH_HYBRID_MODE=1` and the requested family is not
   in the container's tier bundle: dispatch to
   `${AHO_DISPATCH_HYBRID_HOST_URL}/api/chat` with the same
   request payload that would normally go to the container's
   bundled Ollama.
2. The dispatcher logs an event (`dispatch_hybrid_routed`) with
   the requested family, the routing decision, and a clear
   `aho.dispatch.hybrid=true` span attribute. The Pillar 8 cost
   dashboard is unaffected (these are local Ollama calls, no
   token cost), but the trace surface explicitly shows the
   off-container hop.
3. If hybrid mode is set but the host's Ollama also lacks the
   family, the dispatcher hard-errors with `ModelNotAvailableError`
   the same as production behavior — hybrid mode is not a magic
   wand, it is a development affordance for operator-configured
   host state.

### Override knob: explicit per-call parameter

Both behaviors above can be overridden at the dispatch call site
via an explicit parameter:

- `dispatch(..., on_missing="error")` — production semantics
  regardless of env var.
- `dispatch(..., on_missing="fallback")` — opt into Option B
  (local fallback, future work — not implemented in 0.2.17, see
  carry-forward below).
- `dispatch(..., on_missing="cloud")` — opt into Option C (cloud
  route, future work — not implemented in 0.2.17, see
  carry-forward below).
- `dispatch(..., on_missing="hybrid")` — opt into Option D
  regardless of env var (used in tests to assert hybrid-mode
  routing).
- Default (no parameter): respect `AHO_DISPATCH_HYBRID_MODE` env
  var as described above.

The parameter is the explicit override; the env var is the
deployment-mode default. Tests pin the parameter; production
deployments pin the env var (unset).

### Tier manifest contract

`install.fish` writes the tier manifest to `~/.config/aho/tier.json`
**on the host** at install time. The container mounts
`~/.config/aho/` as a read-only volume and reads `tier.json` from
the mount point inside the container.

Manifest shape:

```json
{
  "tier": "base",
  "vram_mb": 8192,
  "bundle": ["nemotron-mini:4b", "nomic-embed-text", "llama3.2:3b"],
  "families": ["nemotron", "nomic", "llama3"],
  "host_id": "NZXTcos",
  "deployment_mode": "development",
  "installed_at": "2026-05-15T12:00:00Z"
}
```

The `deployment_mode` field is set by install.fish based on context:
`development` when run on a developer workstation, `production` when
run in a CI/registry-build context (see §Deployment-mode resource
attribute below). The dispatcher reads this field on startup and
emits it as a resource attribute on every span and event.

Rationale for host-side manifest path: host-side
`cat ~/.config/aho/tier.json` shows the current tier without
`podman exec` ceremony. Observability tools that aren't
container-aware (a dashboard reading the host filesystem, a
post-install self-check script) can consume the manifest without
crossing the container boundary. The container's read-only mount
preserves the install.fish-as-sole-writer contract.

Dispatcher reads the manifest on startup; caches in-process; re-reads
on SIGHUP or container restart. Family-resolution logic
(longest-prefix match against `MODEL_FAMILY_CONFIG`) consumes the
`families` list.

### Deployment-mode resource attribute

Every span and event emitted by the harness inside the container
carries a new resource attribute `aho.deployment.mode` with values
in `{development, production}`. The value flows from the tier
manifest's `deployment_mode` field, which install.fish populates:

- **development** — install.fish was invoked on a developer
  workstation (interactive shell, hybrid mode permitted, base- or
  partial-tier host). NZXTcos and tsP3 fall in this category for
  0.2.17 / 0.3.x.
- **production** — install.fish was invoked in a CI/registry-build
  context (non-interactive, `AHO_INSTALL_PRODUCTION=1` set, or run
  from a deployment automation harness). Cloud-tier hosts and any
  host that ships customer-facing workflows fall in this category.

The attribute exists specifically so the production-leak
monitoring rule (referenced in §Safety guard against env-var leak
and §Out of Scope below) has a way to distinguish dev hybrid use
(expected) from prod hybrid use (the violation). Without the
attribute the rule has no signal to fire on; with it the rule is
the conjunction
`aho.dispatch.hybrid=true AND aho.deployment.mode=production`.

install.fish self-detection logic for development vs. production is
out of this ADR's scope — likely a combination of
`AHO_INSTALL_PRODUCTION=1` env, TTY check, and an explicit
`--production` flag. The contract this ADR fixes is the
**resource-attribute taxonomy** and the **manifest field name**;
the detection mechanism lands in 0.2.17 W2 alongside the
install.fish tier-detection block.

### Safety guard against env-var leak

Three layers of defense against `AHO_DISPATCH_HYBRID_MODE` leaking
into a production deployment:

1. **Startup logging.** The container entrypoint logs the value of
   `AHO_DISPATCH_HYBRID_MODE` at startup — visible in the
   container's stdout and in OTEL events.

2. **Production deployment runbook assertion.** Production deployment
   procedures include an assertion that the env var is unset before
   declaring the deployment ready.

3. **Resource-attribute–based monitoring rule (carry-forward).** The
   `aho.deployment.mode` resource attribute (per §Deployment-mode
   resource attribute above) lets a Pillar 11–style alert rule fire
   on the conjunction
   `aho.dispatch.hybrid=true AND aho.deployment.mode=production`.
   The rule itself is a follow-on deliverable (carried forward;
   candidate for the engine-selection iteration's rule set, see
   §Out of Scope), but the attribute that makes it implementable
   is shipped in 0.2.17 W2.

A hybrid-mode-enabled container running in production is therefore
detectable by inspection (layer 1), gated by procedure (layer 2),
and ready to be alertable (layer 3) — no silent failure path.

## Rationale

> Production base-tier hosts hard-error on partial dispatches because
> silent fallback hides architectural mistakes.

The hard-error production posture is a Pillar 8 / Pillar 9 alignment.
A base-tier production host getting a partial-tier dispatch request
is, in production, a real incident — a workflow has been deployed
to the wrong host or a workflow is requesting capability the host
class is not provisioned for. Silently falling back to the
nearest-available local model substitutes a quietly-wrong answer
for a cleanly-loud failure; quiet wrong answers are how the gotcha
registry grows.

Option B (silent local fallback) was on the table; the operational
risk of substituting a smaller model for a larger one without the
caller knowing is the same class of risk that the harness
explicitly rejects in its acceptance discipline. A 4B model
classifying as a 9B model would breach Pillar 7's
generation-vs-evaluation separation in subtle ways — for example,
an Auditor request silently routed to a Producer-class model
because the Auditor model is missing.

Option C (cloud route) is the right answer in production *eventually*
— Phase C / 0.3.x — but it requires a cloud serving plane that does
not exist today. Pre-implementing the cloud-route option in 0.2.17
would require either mocking the cloud endpoint (which adds
complexity for zero deployment value) or pretending the option
exists in code without a backing service (which contradicts pillar
8's measure-not-estimate posture). The carry-forward below tracks
this option for revisit when Phase C lands.

Option D (hybrid) earns its keep specifically because 0.2.17
development happens on a host that is base-tier-as-container but
partial-tier-as-bare-host. Without the hybrid mode, partial-tier
development work in 0.2.17 has to leave the container, which
either (a) defeats the iteration's central deliverable (the
container as the harness's primary surface) or (b) forces the
operator to context-switch between containerized and bare-host
workflows for routine work. Either is a worse outcome than an
explicit, env-var-gated, log-visible hybrid mode whose
production-leak risk is mitigated by startup assertion.

The override parameter (`on_missing=...`) is the test surface and
the future-extensibility surface in one. Tests pin the desired
behavior explicitly; future ADRs adding fallback or cloud-route
implementations land on the parameter values that are already
reserved.

## Consequences

### Positive

- Dispatcher behavior on missing models is *defined* — currently
  the question has no documented answer.
- Production base-tier deployments fail loudly when asked for
  capability they don't have. Loud failures land in the gotcha
  registry; silent substitutions don't.
- 0.2.17 development on NZXTcos is unblocked for partial-tier work
  via the hybrid mode, without the iteration's central deliverable
  (the container) being a barrier to routine development.
- Pillar 7 (generation vs. evaluation separation) is preserved
  without runtime ambiguity — a missing Auditor model is a hard
  error, not a quiet swap to a Producer model.
- Future fallback (Option B) and cloud-route (Option C)
  implementations have a parameter slot pre-reserved; adding them
  is an extension, not a redesign.
- Tier manifest at `/opt/aho/tier.json` becomes a first-class
  artifact that other parts of the harness (dashboard, alerting,
  installer self-test) can also consume — single source of truth
  for "what tier am I."

### Negative

- Hybrid mode is a development affordance with a real production-leak
  risk if the env var is mis-set. Mitigation (startup logging +
  assertion) reduces but does not eliminate the risk. A future
  Pillar 11 alert rule could surface
  `aho.dispatch.hybrid_active=true` events in production-tier
  deployments as a real-time anomaly.
- Operators developing on NZXTcos must mentally track which Ollama
  serves which dispatch (container's bundled vs. host's native).
  Mitigation: the `dispatch_hybrid_routed` event log entry and
  the `aho.dispatch.hybrid=true` span attribute make the routing
  decision observable per-call.
- Container needs network reachability to the host's Ollama on the
  bare host (port 11434 by default). On Podman this is
  `host.containers.internal`; on Docker it is platform-dependent.
  Mitigation: the hybrid host URL is env-configurable
  (`AHO_DISPATCH_HYBRID_HOST_URL`).
- Tier manifest file becomes a new failure mode (corrupt manifest,
  missing manifest, mis-classified tier). Mitigation: dispatcher
  startup validates the manifest shape and refuses to start on
  invalid manifest, with a clear error message pointing to the
  install.fish self-check command.
- `ModelNotAvailableError` is a new typed exception that callers
  need to handle. Existing callers either don't catch it (and
  surface to the operator, which is the desired production
  behavior) or get updated to handle it (in iterations where
  cascade-orchestrator-level fallback decisions live).

### Neutral

- Override parameter (`on_missing=...`) is implemented as a
  no-op for `fallback` and `cloud` values in 0.2.17 — they raise
  `NotImplementedError` and are reserved for future ADRs that
  define their behavior. Test coverage asserts the
  `NotImplementedError` to lock the contract.
- The tier manifest format is a new contract. Future ADRs can
  amend it; the manifest version field is reserved (not added in
  0.2.17, but the dispatcher's manifest-load is forward-compatible
  with an optional `version` key).
- Hybrid mode does not change Pillar 11 — the dispatcher still
  does not write secrets, still does not commit, still does not
  push. Hybrid is a routing decision, not a privilege escalation.

## Out of Scope

- **Option B implementation (local fallback with degradation
  warning).** Reserved for a future ADR that defines the
  nearness metric and the warning protocol. The override
  parameter slot is reserved.
- **Option C implementation (cloud route).** Reserved for Phase C
  / 0.3.x once the cloud serving plane exists. The override
  parameter slot is reserved.
- **Per-family fallback policy.** A future ADR may define
  family-specific fallback rules (e.g., "qwen falls back to
  llama3 for chat tasks; nemotron has no fallback because its
  classifier role is uniquely structured"). 0.2.17 ships
  uniform hard-error.
- **Dispatcher-side tier upgrade detection.** If install.fish
  pulls a new model post-container-start, the dispatcher
  re-reads the manifest on SIGHUP — but there is no automatic
  notification from install.fish to the container. That
  interaction is a 0.2.17 W3 implementation detail, not an
  architectural decision; this ADR does not pre-decide it.
- **Multi-host Ollama load balancing.** A future deployment
  shape where multiple hosts run different model bundles and
  the dispatcher load-balances across them. Phase C / 0.3.x
  candidate.
- **Pillar 11 monitoring rule for hybrid-mode-in-production.**
  Worthy of a follow-on alert rule; out of this ADR's scope but
  carried as a candidate for the engine-selection iteration's
  rule set. The rule is the conjunction
  `aho.dispatch.hybrid=true AND aho.deployment.mode=production`.
  This ADR ships the `aho.deployment.mode` attribute so the rule
  is implementable when it lands; the rule itself is not in
  0.2.17 scope.

## Alternatives Considered

### Pure Option A — hard error in all modes

Drop the hybrid affordance entirely; dispatcher always
hard-errors on missing models. Operators developing partial-tier
work on NZXTcos run aho outside the container.

**Rejected.** 0.2.17's deliverable is the container as a usable
harness surface. Forcing operators outside the container for
routine partial-tier work undermines the iteration. Explicit
hybrid mode with leak mitigation is strictly better than a
silent context-switch convention.

### Pure Option B — silent local fallback

Dispatcher routes to nearest-available family with a logged
warning; never hard-errors.

**Rejected.** Silent substitution breaks Pillar 7 boundary
guarantees. A future engineer who launches an Auditor-role
cascade on a base-tier host and gets a Producer-class model
back without the warning being visible at the harness level
ships a broken Pillar 7 result without knowing it.

### Pure Option C — always cloud-route

Dispatcher always routes to a remote endpoint; local Ollama is
a build-only optimization.

**Rejected.** Local-loop is the 0.2.x deployment shape.
Cloud-only dispatcher would discard the bare-metal harness
posture that 0.2.x has held and require a cloud serving plane
that does not exist. Folds back to phase C work.

### Hybrid mode without env-var gate (always-on)

Dispatcher always tries the host's Ollama for missing-model
requests; production hosts have no host Ollama so the call
fails the same way as the hard-error path.

**Rejected.** Implicit behavior that varies by host
configuration is harder to reason about than explicit
env-var-gated behavior. The startup-log assertion is cheap and
removes ambiguity.

### Auto-detect host Ollama on container start

Dispatcher probes `host.containers.internal:11434` at start;
if Ollama responds, enables hybrid mode automatically.

**Rejected.** Auto-enabled hybrid mode is exactly the
production-leak risk this ADR mitigates. Explicit env var keeps
the operator in the decision.

### Make `on_missing` parameter the only surface; no env var

Drop the env var entirely; require every caller to pass
`on_missing="hybrid"` explicitly when in development mode.

**Rejected.** Threading a parameter through every dispatch
call site for a development-mode toggle is per-call ceremony for
a deployment-mode decision. Env var is the right level of
abstraction for the deployment mode; parameter is the right
level for explicit overrides (tests, edge cases).

## Revisit Triggers

This ADR is amended (not necessarily replaced) when any of the
following become true:

1. **A cloud serving plane exists.** Option C is implemented;
   `on_missing="cloud"` becomes a real code path; production
   deployment may pivot from hard-error default to cloud-route
   default. Phase C work.

2. **Local-fallback policy becomes desirable.** A future iteration
   defines a nearness metric and a degradation-acceptance posture;
   `on_missing="fallback"` is implemented. Likely follows the
   Auditor role-prompt bifurcation iteration.

3. **A second engineer onboards and routinely needs hybrid mode.**
   The env-var-gate posture may need to evolve into a per-user
   shell init or a workspace setting; the deployment-mode
   abstraction may need refinement.

4. **Pillar 11 monitoring rule for hybrid-in-production lands.** A
   follow-up rule fires when `aho.dispatch.hybrid=true` events
   show up on a tier=production-tagged host; this ADR is amended
   to cite the rule as the production-leak monitoring control.

## References

- `artifacts/adrs/0007-containerization-architecture.md` — tier
  classification this ADR's behavior depends on.
- `artifacts/adrs/0006-iteration-deliverable-discipline.md` — the
  0.2.17 graduation criterion explicitly invokes
  `AHO_DISPATCH_HYBRID_MODE=1` to validate this ADR's hybrid
  branch.
- `src/aho/pipeline/dispatcher.py` — implementation site for
  `ModelNotAvailableError`, manifest read, hybrid-mode branch.
  0.2.17 W3 work.
- `install.fish` — produces `/opt/aho/tier.json` or its host-path
  equivalent. 0.2.17 W2 work.
- `artifacts/iterations/0.2.17/aho-plan-0.2.17.md` §W3 — calls
  this ADR's behavior as the W3 acceptance.
- 0.2.15 dispatcher work — `MODEL_FAMILY_CONFIG`, longest-prefix
  family resolution; the manifest's `families` list maps to
  `MODEL_FAMILY_CONFIG` keys.
- `artifacts/harness/base.md` §The Eleven Pillars — pillar 7
  (generation vs. evaluation separation) is the primary
  constraint that motivates the hard-error production posture.
