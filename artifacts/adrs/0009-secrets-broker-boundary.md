# ADR 0009 - Secrets Broker Boundary

**Status:** Accepted
**Date:** 2026-05-03
**Iteration of record:** aho 0.2.17 W5 (consolidating 0.2.17 W1 D3 implementation)
**Decision owner:** Kyle Thompson (signs), Claude web (drafted), Claude Code (executed at W1 D3), llama3.2 + RAG + filter (audits at W5)
**Context surface:** aho project-internal - credential boundary between
container and host under tiered containerized deployment. Binds 0.2.17
W1 D3, W2 broker test redesign, F-0.2.17-W1-001 subcommand removal,
F-0.2.17-W1-003 token rotation. Inherits in 0.3.x for partial- and
full-tier deployment.

---

## Context

ADR 0007 establishes that aho ships as a single tier-aware container
image with secrets stored host-side and bind-mounted into the
container. ADR 0007 §Secrets model fixes the *what* - secrets do not
live in the image, in the registry, or in the container's writable
layer - but does not fix the *how*: the mechanism by which the
container reads those secrets at runtime, the authentication
boundary between container and host, and the per-engineer onboarding
shape.

Three forces shape the boundary mechanism:

1. **Pillar 11 invariant.** No credential material in image layers,
   ever. The image must be safe to publish to a registry without
   per-host re-encryption. The container itself must have no git
   write capability under any identity, including its own.

2. **Per-engineer onboarding scales beyond two operators.** A
   secret-mixing keystore (one fernet store shared across operators,
   one age identity that every operator decrypts with) collapses the
   moment a second engineer joins. The broker must work in a shape
   where each engineer runs their own broker against their own
   fernet store with their own age identity, and the image is
   bit-identical across all engineers' workstations.

3. **Authentication binds to the operating-system boundary, not to a
   credential the container holds.** Any credential the container
   holds for the broker is a credential that lives in image layers
   or in container runtime config - both Pillar 11 violations.
   Authentication must instead derive from the host kernel's process
   identity (UID, project label) at the socket layer.

The 0.2.17 W1 D3 implementation landed the broker with these
properties; this ADR is the repo-resident authoritative spec.

## Decision

### Three rules

The boundary is governed by three rules. These are **verbatim** from
the chat-side architecture artifact `aho-base-container-architecture.md`
§Pillar 11 / Secrets boundary; this ADR makes them repo-resident and
authoritative:

1. **No credential material in image layers ever.** The image is
   bit-identical across operators and across hosts. The image is
   safe to publish to any registry without per-host re-encryption.
   No age identity, no fernet key, no project secrets, no API
   tokens are baked into any layer.

2. **Per-user secret access via host-side broker.** Each operator
   runs their own broker against their own fernet store with their
   own age identity. The broker authenticates the connecting peer
   via SO_PEERCRED, validates the project label the peer requested,
   and returns a single decrypted value per request. No shared
   keystore; no broker-to-broker crosstalk.

3. **No SSH agent socket forwarded.** The container has no path to
   any host-side identity that could push, commit, or merge under
   any user's name. SSH agent forwarding (`SSH_AUTH_SOCK`) is
   excluded from the container's mount set. The container literally
   cannot push under anyone's identity, including its own.

These three rules are jointly Pillar 11. Each rule independently
closes one failure mode the other two leave open; together they make
the failure-mode space empty under the operator-count and trust
posture aho holds.

### Mechanism

**Host-side broker (`src/aho/host/secrets_broker.py`).** A unix-socket
service bound to `${XDG_RUNTIME_DIR}/aho-secrets.sock` (default
`/run/user/<uid>/aho-secrets.sock`) with mode `0600`. The broker:

- Authenticates the connecting peer via `SO_PEERCRED` (Linux
  `struct ucred`).
- Restricts control operations (register UID, unregister UID) to the
  broker-owner UID.
- Restricts data operations (`get`) to UIDs registered by the broker
  owner with a project label match.
- Returns a single decrypted value per request, JSON line
  request/response.
- Logs request shape (`op`, `uid`, `project`, `name`, `outcome`) but
  never logs the secret value.
- Reads from the host's age-fernet store; the operator's age identity
  is read by the broker once at start-time and held in process
  memory; never persisted to a writable filesystem location the
  container can reach.

**Container-side client (`src/aho/secrets_client.py`).** Connects to
the bind-mounted socket (`AHO_SECRETS_SOCKET`, default
`/run/host-services/aho-secrets.sock`), JSON line request/response,
no caching across container restarts, no on-disk persistence. The
client authenticates as the in-container UID (mapped through podman's
user namespace); the broker-side `SO_PEERCRED` check resolves to the
host-side UID the container's UID maps to, which must be in the
broker's registered set.

**Wrapper (`src/aho/host/run_container.py`).** The
`aho host run-container` wrapper registers the calling UID with the
broker before invoking `podman run`, mounts the broker socket
read-only at `/run/host-services/aho-secrets.sock`, and unregisters on
exit. The wrapper is the canonical surface; raw `podman run`
invocations bypass the registration step and the SO_PEERCRED check
fails closed (correct behavior - the container cannot reach secrets
if launched outside the wrapper).

### Per-engineer onboarding

Each engineer runs `aho host install` once on their workstation:

1. Generates their own age identity via the age binary.
2. Populates their own fernet store with project secrets (encrypted
   under the age identity).
3. Starts their own broker (systemd-user service, or foreground for
   debugging) against their own socket path.

The image is identical across engineers. Mounts differ per host:
each engineer's container mounts that engineer's
`${XDG_RUNTIME_DIR}/aho-secrets.sock`. The broker authenticates only
that engineer's registered UIDs. There is no shared keystore between
engineers; there is no broker-to-broker secret exchange.

Cross-engineer secret sharing - when two engineers need access to the
same upstream credential - is solved out-of-band by the upstream
provider (each engineer holds their own copy of the credential under
their own age identity). aho does not synchronize secrets across
engineers and does not need to, because the same upstream credential
encrypted to two age identities under two fernet stores resolves
identically when the container asks the broker for it.

### Implementation evidence

W1 D3 implementation landed at acceptance archive sha256
`e4d076eec6c1e703635e9befb98bc46c7bf171c7fec3a4c3f64161ec60725a6e`.
Modules and shas at W1 D3 close (recorded in W1 acceptance archive
`changed_files` block):

| Module | Path | sha256 (W1 close) |
|---|---|---|
| Host broker | `src/aho/host/secrets_broker.py` | `4cff78274f587e4781663f0755407a4eb8b4a96d839c8a481bdc5273d6171019` |
| Container client | `src/aho/secrets_client.py` | `e9b305f7db831a267fd8a013185ae2549a1b6cc88cdd6b4fe0f5327043f5a04e` |
| Run-container wrapper | `src/aho/host/run_container.py` | `036a267f43772f2da2c5995b0d5c233d8af319fca90505ae254b9963b6856bfd` |

W1 D3 acceptance gates:

- **Gate 1 (round-trip, correct project):** pass - broker returns
  decrypted value to authorized container, exit 0.
- **Gate 2 (project mismatch):** pass - broker rejects with
  `AUTH_FAIL: project_mismatch`, exit 4.
- **Gate 3 (missing key):** pass - broker returns `MISSING`, exit 5.
- **Gate 4 (unregistered UID, SO_PEERCRED):** pass - broker rejects
  with `AUTH_FAIL: uid_not_registered`, exit 4. Verified via
  `podman run --userns=keep-id` mapping the in-container UID to a
  host-visible subuid (~100999) the broker has not registered.
- **Gate 5 (broker log inspection):** operator-pending at W1 close -
  broker writes only request shape by design, never the value, but
  only the operator can confirm on the foreground broker terminal.

### F-0.2.17-W1-003 - worked example

The W1 plan-doc specified a Gate-1 implementation that printed the
decrypted value to stdout to verify broker round-trip equivalence
with direct host-side `get_secret()`. Executing this gate caused the
agent (Claude Code) to read the bytes of `ahomw:telegram_bot_token`
via Bash tool stdout - a direct contradiction of CLAUDE.md hard rule
"No reading secrets."

This is the **worked example of why the hash-fingerprint contract
exists**. The plan-doc design was wrong on Pillar 11 grounds: any
acceptance gate that surfaces a decrypted secret to any agent stdout
is a Pillar 11 violation by construction, regardless of how
short-lived the surface is or how careful the agent is about not
reproducing the value downstream.

The remediation pattern - generalizing from the W2 broker test
redesign work - is that broker round-trip equivalence is verified
**without** the value crossing the agent boundary. Two designs are
acceptable:

1. **Hash-fingerprint comparison.** Host-side caller computes
   `sha256(get_secret(project, name))`; broker independently computes
   `sha256(decrypt(broker-side-store[project][name]))`; both hashes
   are compared. The hashes are non-secret; the values never leave
   their respective process spaces.

2. **Broker-side equality boolean.** Broker accepts a hash from the
   caller, computes its own value's hash, returns only the boolean
   match result across the socket. Even more conservative: no hash
   is exposed; only `true` / `false`.

The W2 plan-doc pinned the final design (hash-fingerprint per option
1). F-0.2.17-W1-003 carries operator-side token rotation as a hard
gate before any 0.3.x work begins; F-0.2.17-W1-001 carries the
production-image subcommand removal (W6 scope).

The drafter's plan-doc design was the root-cause defect (chat-side
design responsibility, not executor implementation). The drafter-side
gotcha that prevents recurrence: any acceptance gate that surfaces a
decrypted secret to any agent stdout is a Pillar 11 violation by
construction. This ADR makes that gotcha repo-resident and binding
on future broker work.

## Rationale

> Authentication binds to the operating-system boundary, not to a
> credential the container holds.

The unix-socket + SO_PEERCRED design is the simplest mechanism that
achieves the three rules without giving the container any credential
that could leak through registry publishing or container runtime
config. Three forces drive the choice:

1. **The container holds nothing.** Any credential the container
   holds is a credential that either ships in image layers (Pillar
   11 violation) or is wired in at runtime via env or mount config
   (broader leak surface, harder to enumerate). SO_PEERCRED's check
   reads the connecting peer's kernel-side UID; nothing the
   container can lie about.

2. **Per-engineer onboarding is symmetric.** The image is
   bit-identical across engineers; the host-side broker is per-host;
   the registered-UID set is per-broker. Adding an engineer is `aho
   host install` on their workstation. Removing an engineer is
   stopping their broker - their fernet store and age identity stay
   on their workstation, never replicated.

3. **No SSH agent forward closes the git write surface entirely.**
   Pillar 11's binding constraint ("no agent writes to git") is
   structurally enforced by the absence of any host-side identity
   the container could borrow. The container has no SSH key, no git
   credential helper, no token. It cannot write to git because the
   primitive is unreachable, not because the container chooses not
   to use it.

The alternative - a long-lived bearer token in the container,
authenticated against the broker - would require either baking the
token into image layers (Pillar 11 violation) or generating it at
container start and passing it via env (env-based credential, harder
to audit, leaks through process inspection on shared hosts). The
unix-socket + SO_PEERCRED design has neither of those surfaces.

## Consequences

### Positive

- Pillar 11's "no credential material in image layers" invariant
  becomes structurally enforced. The image is bit-identical across
  hosts and engineers; the registry is publish-safe.
- Per-engineer onboarding scales: each engineer's workstation is
  self-contained; no shared keystore; no operator-cross-pollution.
- Authentication is OS-grounded: SO_PEERCRED resolves the connecting
  peer's UID at the kernel layer; nothing the container can spoof.
- Container has zero git write capability. SSH agent socket is not
  forwarded; no host-side credential is reachable. The Pillar 11
  invariant ("no agent writes to git") is mechanically true, not
  policy-true.
- The broker socket lives in `${XDG_RUNTIME_DIR}` (host-volatile,
  per-user, mode 0600) - no concerns about world-readable socket
  paths or socket persistence across reboots.
- The hash-fingerprint contract (W2 redesign) keeps the
  round-trip-equivalence acceptance gate exercisable by an agent
  without surfacing the secret value, generalizing the F-0.2.17-W1-003
  lesson into a reusable pattern.

### Negative

- The wrapper (`aho host run-container`) becomes load-bearing for
  any container invocation that needs secrets. Raw `podman run`
  invocations cannot reach the broker; the registration step is
  wrapper-only. Mitigation: documented in the wrapper's help text
  and in the deployment doc; bypass produces a clean SO_PEERCRED
  rejection rather than a silent fallback.
- Each engineer holding their own copy of upstream credentials
  shifts the cross-engineer secret-sharing problem to the upstream
  provider (each engineer needs their own copy provisioned). For
  shared-credential cases (e.g., a single shared external API key
  used by multiple engineers' aho instances), the upstream provider
  must mint per-engineer credentials or the engineers coordinate
  out-of-band. aho does not solve this and does not need to.
- The W1 incident (F-0.2.17-W1-003) burned one Telegram bot token -
  operator-side rotation is the hard gate for closure. Drafter-side
  process gotcha (any acceptance gate surfacing decrypted secrets to
  agent stdout violates Pillar 11) is documented here as
  authoritative.
- The broker is a per-host single point of failure: if the broker is
  down, the container cannot fetch secrets. Mitigation: the broker
  is a systemd-user service with restart-on-failure; container-side
  client returns clean error rather than hanging.

### Neutral

- The image is identical across operators and across hosts; container
  registries do not need per-host artifact mirroring.
- 0.3.x partial-tier and full-tier deployment inherits this ADR
  unchanged. The broker shape is independent of GPU tier; only the
  container's bundled model surface changes per tier.
- Cloud-tier deployment (Phase C, GCP intranet target) substitutes a
  cloud-native secret store (e.g., GCP Secret Manager via Workload
  Identity) for the host-side broker. The container-side client
  abstraction is the same; the broker's transport changes from
  unix-socket to Workload-Identity-backed REST. Out of scope for
  this ADR.

## Out of Scope

- **Cloud-tier broker substitution.** GCP Secret Manager via Workload
  Identity (or analogous) for cloud deployment is Phase C work.
- **Cross-engineer secret sharing.** Any shared-credential case
  resolves out-of-band; aho does not orchestrate cross-operator
  secret distribution.
- **Hardware-backed identity (TPM, YubiKey).** Each engineer's age
  identity is a software file on their workstation today.
  Hardware-backed identity is a future hardening pass, not in scope
  for the boundary mechanism this ADR fixes.
- **Secret rotation automation.** The 0.2.17 incident
  (F-0.2.17-W1-003) requires Kyle to manually rotate the burned
  Telegram bot token. Automated rotation infrastructure is post-0.3.x.
- **Audit log retention for broker requests.** Broker logs request
  shape but does not persist logs to a durable surface beyond
  operator-skim of foreground stdout or systemd-user journal.
  Long-term audit retention is post-0.3.x.

## Alternatives Considered

### Bearer token in image at build time

Bake a long-lived bearer token into image layers; broker authenticates
against the token.

**Rejected.** Token in image layers is a Pillar 11 violation. Image
publishing requires per-host re-encryption or per-image rebuild.
Per-engineer onboarding collapses (every engineer gets the same
baked-in token, or every engineer needs a different image).

### Bearer token at runtime via env

Container is launched with the bearer token in `--env`; broker
authenticates against the env value.

**Rejected.** Env-based credentials leak through `/proc/<pid>/environ`
on shared hosts, complicate logging hygiene, and require runtime
config to be distinct per host. The SO_PEERCRED mechanism achieves
the same authentication outcome with no credential material at all.

### Mount the host's age identity directly into the container

Read-only bind-mount of `~/.local/share/aho/age/identity.txt` into the
container; container-side `aho.secrets_client` decrypts directly.

**Rejected.** Container becomes per-engineer (each engineer's
identity is mounted; bypassing the broker means the container has the
key material in its filesystem view, which is recoverable from a
running container's process memory). The broker keeps the age
identity in the broker process's memory only, never reachable from
the container.

### TLS over a TCP socket on localhost

Broker listens on `127.0.0.1:NNNN` with mTLS; container connects with
its own client cert.

**Rejected.** Client cert in image layers is a Pillar 11 violation;
client cert at runtime via env or mount has the same leak surface as
bearer tokens. SO_PEERCRED on a unix socket achieves the same
authentication property with no transport credential at all.

### Forward SSH agent into container for "convenience"

Bind-mount `$SSH_AUTH_SOCK` into the container so the container can
sign for the operator's SSH identity.

**Rejected. Hard.** This is the canonical Pillar 11 violation. Any
agent inside the container with access to `$SSH_AUTH_SOCK` can sign
git pushes under the operator's identity. The container must not
have this surface, ever. Rule 3 ("no SSH agent socket forwarded") is
absolute, not soft-deferred.

## Revisit Triggers

This ADR is amended (not necessarily replaced) when any of the
following become true:

1. **Cloud-tier deployment lands (Phase C).** The broker substitution
   for GCP Secret Manager via Workload Identity is decided; the
   container-side client abstraction is preserved but the broker
   transport changes. Amendment captures the cloud-side decision.

2. **A second engineer onboards.** The per-engineer onboarding shape
   gets exercised under operator-count-of-two; any unanticipated
   friction surfaces a small amendment to the onboarding section.

3. **Hardware-backed identity (TPM, YubiKey) lands.** The age
   identity moves from a file to a hardware-backed signer; the
   broker reads from the hardware signer rather than from a file.
   Amendment captures the file → hardware transition.

4. **An additional rule becomes binding.** If a future iteration
   surfaces a fourth Pillar 11 invariant the present three rules
   don't cover, the rule list is amended explicitly. Until then,
   the three rules are exhaustive of the boundary.

## References

- `artifacts/adrs/0007-containerization-architecture.md` §Secrets
  model - the *what* (host-side, never in image); this ADR fixes
  the *how*.
- `artifacts/adrs/0007-containerization-architecture.md` §Council
  roles - describes the in-container model fleet that consumes the
  broker for project secrets when needed.
- `artifacts/iterations/0.2.17/W1-plan-doc.md` line 63 - the
  plan-doc design defect that surfaced as F-0.2.17-W1-003 (the
  drafter-side gotcha on agent-stdout-surfacing-secret-values).
- `artifacts/iterations/0.2.17/acceptance/W1.json` (sha256
  `e4d076eec6c1e703635e9befb98bc46c7bf171c7fec3a4c3f64161ec60725a6e`)
  D3 evidence block - gates 1–4 pass, gate 5 operator-pending at W1
  close.
- `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`
  F-0.2.17-W1-003 entry - operator-side token rotation as
  pre-0.3.x hard gate.
- `artifacts/harness/base.md` §Pillar 11 ("the human holds the keys")
  - binding constraint on the boundary.
- `src/aho/host/secrets_broker.py` - host-side broker implementation
  (W1 D3 close sha
  `4cff78274f587e4781663f0755407a4eb8b4a96d839c8a481bdc5273d6171019`).
- `src/aho/secrets_client.py` - container-side client (W1 D3 close
  sha
  `e9b305f7db831a267fd8a013185ae2549a1b6cc88cdd6b4fe0f5327043f5a04e`).
- `src/aho/host/run_container.py` - wrapper that registers the
  calling UID before invoking `podman run` (W1 D3 close sha
  `036a267f43772f2da2c5995b0d5c233d8af319fca90505ae254b9963b6856bfd`).
