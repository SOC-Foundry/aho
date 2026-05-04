# aho-plan-0.2.17

**Iteration:** 0.2.17
**Theme:** Containerized aho — base-tier image, install-time tier
detection, host-mounted secrets and tier manifest, hybrid-mode
dispatcher
**Phase:** 0 (Clone-to-Deploy)

---

## Iteration deliverable

> **0.2.17 ships aho as a runnable container image on NZXTcos.** The
> image is single-tier-aware (one image, install-time tier detection
> via `install.fish` polling `nvidia-smi`), portable across Podman as
> the default runtime and Docker as the fallback, and assembled with
> Pillar 11 secrets posture preserved (host-mounted age identity and
> fernet-encrypted bundle, never baked in). install.fish writes
> `~/.config/aho/tier.json` on the host; the container mounts
> `~/.config/aho/` read-only and reads tier + deployment-mode from
> the manifest. The dispatcher gains hard-error semantics on missing
> model families in production deployment; an env-gated hybrid mode
> routes partial-tier dispatches to the host's native Ollama for
> development on NZXTcos. OTEL telemetry continues across the
> container boundary — the existing host-side collector at
> `localhost:4317` ingests metric, log, and trace signals from the
> containerized harness, with the new `aho.deployment.mode` resource
> attribute distinguishing development from production at every
> emitted signal.

## Graduation criterion (Form 1: runnable test)

0.2.17 graduates when the following sequence completes cleanly on
NZXTcos:

```fish
# 1. Fresh install on host
./install.fish --container

# 2. Tier manifest present and well-formed
test -f ~/.config/aho/tier.json
and jq -e '.tier == "base" and .deployment_mode == "development" and (.families | length) >= 3' \
    ~/.config/aho/tier.json

# 3. Image built and tagged
podman images aho:0.2.17 | grep -q '0.2.17'

# 4. Container starts cleanly with secrets and tier mount
podman run --rm --name aho-smoke \
    -v ~/.config/aho:/etc/aho:ro \
    -v ~/.local/share/aho/age/identity.txt:/opt/aho/secrets/age/identity.txt:ro \
    -v ~/.local/share/aho/secrets/bundle.enc:/opt/aho/secrets/bundle.enc:ro \
    -v ~/.local/share/aho/models:/var/lib/ollama:ro \
    -e AHO_ITERATION=0.2.17 \
    -e AHO_WORKSTREAM=W4 \
    aho:0.2.17 \
    aho doctor full

# 5. Hybrid-mode dispatch works (partial-tier on base-tier container)
podman run --rm \
    -v ~/.config/aho:/etc/aho:ro \
    -e AHO_DISPATCH_HYBRID_MODE=1 \
    --network host \
    aho:0.2.17 \
    aho dispatch --family qwen --prompt "ping"
# expected: completes without ModelNotAvailableError, returns content,
# emits aho.dispatch.hybrid=true span attribute

# 6. Production-mode dispatch fails loudly on missing family
podman run --rm \
    -v ~/.config/aho:/etc/aho:ro \
    aho:0.2.17 \
    aho dispatch --family qwen --prompt "ping"
# expected: exits non-zero with ModelNotAvailableError, no silent fallback

# 7. OTEL signals from container land in host collector with deployment.mode tagged
grep -F '"aho.deployment.mode":"development"' ~/.local/share/aho/logs/logs.jsonl | head -1
grep -F '"aho.deployment.mode":"development"' ~/.local/share/aho/metrics/metrics.jsonl | head -1
grep -F '"aho.deployment.mode":"development"' ~/.local/share/aho/traces/traces.jsonl | head -1

# 8. Acceptance + audit archives present for each workstream
for n in 0 1 2 3 4
    if not test -f artifacts/iterations/0.2.17/acceptance/W$n.json
        echo "FAIL: acceptance/W$n.json missing"
        exit 1
    end
    if not test -f artifacts/iterations/0.2.17/audit/W$n.json
        echo "FAIL: audit/W$n.json missing"
        exit 1
    end
end
```

Each step is a hard pass/fail. The graduation criterion is the
runnable equivalent of the deliverable paragraph: it asserts that
the image exists, the tier manifest is correct, hybrid mode works in
development, production mode hard-errors as designed, and telemetry
attributes the new resource attribute correctly. The fish test
sequence is the canonical close-time check.

---

## Plan amendments (pre-W0)

Three pre-launch amendments applied 2026-05-02 before W0 launched:

1. **Graduation criterion step 4 mount paths corrected.** Original
   draft had two `-v` flags that both mounted under
   `/opt/aho/secrets`, shadowing each other. Replaced with
   file-level binds matching W2's mount-layout documentation.
   Pre-launch fix; no scope change.

2. **Graduation criterion step 8 fish for-loop syntax corrected.**
   Original draft used `and test ...` inside a for-loop block,
   which does not propagate failure as expected in fish. Replaced
   with explicit if-not / exit-1 form for hard-pass-fail behavior.
   Pre-launch fix; no scope change.

3. **W0 Bucket 2 hardened with two pre-flight verifications.**
   Added registry writability pre-flight (gates W1 launch) and
   nvidia-container-toolkit package-name resolution (replaces
   guess with live pacman query). Both surfaced from plan review
   against 0.2.16 W3-alert-engine-class infrastructure-assumption
   discipline.

4. **k8s-readiness constraint added to ADR 0007 + W1 acceptance.**
   Kyle decided 0.2.17 ships an OCI image that is k8s-deployable in
   principle (configuration, secrets, logs, SIGTERM, health checks)
   without shipping k8s manifests in this iteration. ADR 0007 amended
   in place; W1 acceptance gate added. Premature manifests calcify
   decisions before there is a cluster; image properties survive that
   gap. Pre-launch scope addition to a not-yet-started workstream
   (W1) — not iteration-scope drift.

Plan-time amendment per ADR 0006: 0.2.17 has not yet started;
pre-launch scoping is not iteration-scope amendment. Hard meta-rule
treatment does not apply.

---

## Workstream summary

| N | Theme | Gate |
|---|---|---|
| W0 | Substrate carry-forward closure + Podman/runtime decision + hello-world container + Adversarial Authorship rename | AF004/AF005 closed; F-W0-004 conftest brittleness fixed; Podman runs hello-world container on NZXTcos OR Docker fallback engaged with rationale; "Pattern C" find/replaced to "Adversarial Authorship" across live governance docs (sealed acceptance archives untouched) |
| W1 | Dockerfile + image build + local registry push | `Dockerfile` builds clean; `aho:0.2.17-rc1` pushed to local registry; image size under 2 GB excluding models; `podman run aho:0.2.17-rc1 aho --version` returns expected string |
| W2 | install.fish tier detection + tier manifest + secrets mount layout | install.fish detects NZXTcos as base tier (8 GB → < 12 GB threshold); writes `~/.config/aho/tier.json` with correct shape (per ADR 0008); secrets host-mount layout documented and tested |
| W3 | aho CLI in container + hybrid-mode dispatcher + `ModelNotAvailableError` | dispatcher reads tier manifest from `/etc/aho/tier.json`; hard-errors on missing family in production mode; routes to `host.containers.internal:11434` in hybrid mode; `on_missing=` parameter implemented; tests cover all four parameter values (error/hybrid/fallback/cloud — fallback and cloud raise NotImplementedError) |
| W4 | Telemetry from container + close package | OTEL signals from container land in host collector with `aho.deployment.mode` resource attribute; retrospective applies ADR 0006 deliverable + criterion (no retroactive section needed); carry-forward register lands; iteration close package per ADR 0004's redesigned `--confirm` semantics if 0.2.x close-confirm cleanup landed by then, otherwise per legacy semantics |

---

## W0 — Substrate carry-forward closure + Podman/runtime decision + hello-world container

**Scope:** Three coordinated buckets — close out 0.2.16 carry-forwards
that target 0.2.17, decide and verify the container runtime, and
prove the runtime works with a hello-world container before any aho-
specific work begins.

### Bucket 1 — Substrate carry-forward closure

1. **AF004 — `api_error_count` aliasing in `otel_aggregator.py`.**
   Decide: alias intentionally, missing event mapping, or remove dead
   field. Implement the decision; update tests; update
   `otel_aggregator.py` doctring to reflect the contract.
2. **AF005 — `api_retries_exhausted_count` dead field.** Same shape.
   Either map to a real ingestion site for `claude_code.api_retries_exhausted` events
   or remove from the aggregator output. Decision should be
   one-line: if Claude Code emits this event today, map it; if not,
   remove the field rather than ship dead state.
3. **F-W0-004 (third recurrence) — conftest allowlist brittleness.**
   The `test_workstream_events.py` fixture has corrupted the
   checkpoint three times. The 0.2.16 W0 fix added an allowlist in
   `artifacts/tests/conftest.py`; the underlying fragility is that
   any new test author who emits workstream events outside the
   allowlist re-introduces the failure mode. Two real options:
   (a) bind `find_project_root()` to a context manager that all
   workstream-event-emitting test code must enter explicitly;
   (b) emit a clear-test-error if `find_project_root()` is invoked
   from a path that is not under `tmp_path`. Pick one and implement.
4. **W2-AF004 — `dispatch.duration_ms` error-path measurement
   gap.** Add a unit test that asserts error-path duration on
   `DispatchError` is consistent with success-path duration
   accounting. If the test surfaces material drift (>1ms), unify the
   measurement site.
5. **F-W1-001 — `${VAR}` expansion wrapper.** Implement `bin/aho
   workstream init W{N}` (or equivalent) that writes literal values
   into `.claude/settings.json` env block at workstream boundary.
   Remove the literal-value manual-update overhead identified in
   ADR 0003's carry-forward.

### Bucket 2 — Runtime decision + hello-world

6. **Podman install + first hello-world.** `pacman -S podman` on
   NZXTcos (already CachyOS-supported); verify rootless config
   correct; `podman run --rm hello-world` succeeds.
7. **Podman GPU passthrough probe.**

   Pre-step: confirm the actual package name on CachyOS:

   ```fish
   pacman -Ss nvidia-container
   ```

   Use the resolved package name (likely `nvidia-container-toolkit`
   upstream, possibly `nvidia-container-toolkit-base` or similar in
   a CachyOS-specific repo). Install the resolved package; do not
   assume the name. If no matching package exists in pacman repos,
   document the AUR or source-install path used and surface to Kyle
   before proceeding.

   Then run:

   ```fish
   podman run --rm --device nvidia.com/gpu=all nvidia/cuda:12.0-base nvidia-smi
   ```

   Verify GPU passthrough works under rootless Podman.

   - **Decision gate:** if GPU passthrough fails under rootless
     Podman after reasonable troubleshooting, fall back to Docker
     and update ADR 0007's §Runtime choice with empirical reason.
     No invented workarounds — measure, decide, document.
8. **`host.containers.internal` reachability probe.** From inside a
   minimal container, `curl http://host.containers.internal:11434/api/version`
   should hit the host's Ollama. This is the wire that ADR 0008's
   hybrid mode rides.
9. **Registry writability pre-flight (gates W1 launch).** Before W0
   closes, verify the registry chosen in ADR 0007 (default proposal:
   `ghcr.io/socfoundry/aho`) is writable from NZXTcos:

   ```fish
   gh auth status
   echo "test" | podman login ghcr.io -u <username> --password-stdin
   podman pull hello-world
   podman tag hello-world ghcr.io/socfoundry/aho-pretest:smoke
   podman push ghcr.io/socfoundry/aho-pretest:smoke
   podman rmi ghcr.io/socfoundry/aho-pretest:smoke
   ```

   If push fails (permissions, missing namespace, missing PAT,
   org-policy block), surface to Kyle and either: (a) fix the
   credential/permission issue, (b) amend ADR 0007 §registry-choice
   to a working alternative (self-hosted Harbor on the tailnet, local
   Docker-Distribution, or other). Do NOT proceed to W1 with an
   unverified registry — W1 spends 3 hours building the real
   Dockerfile, and discovering registry friction at push time costs
   all of that work.

   Pre-test image (`aho-pretest:smoke`) is deleted from the registry
   after verification. This step does not consume a real image tag.

### Bucket 3 — Aho-internal hello-world container

9. **Minimal Dockerfile (throwaway).** Single layer, base image
   (debian:stable-slim or equivalent), `aho` Python package
   `pip install`-ed, entrypoint `aho --version`. Builds clean.
   `podman run --rm aho:hello aho --version` returns the expected
   version string.

### Bucket 4 — Adversarial Authorship rename (find/replace pass)

10. **"Pattern C" → "Adversarial Authorship" rename.** Find/replace
    across live governance docs only:
    - `CLAUDE.md` (project instructions — primary drafter doc).
    - `GEMINI.md` (auditor instructions).
    - `artifacts/adrs/0006-iteration-deliverable-discipline.md`
      (references the workstream-level analog as "pattern-c-protocol";
      replace narrative occurrences, leave file-path references in
      §References as-is until the protocol file is itself renamed).
    - `artifacts/harness/adversarial-authorship-protocol.md` — was
      `artifacts/harness/pattern-c-protocol.md` before 0.2.17 W0;
      file renamed plus content rename; inbound references updated.
    - `artifacts/harness/base.md` — narrative occurrences only.
    - `artifacts/iterations/0.2.17/aho-plan-0.2.17.md` (this file —
      the rename pass updates this plan's own "Pattern C" mentions if
      any are added between now and W0 execution).
    - The iteration-plan-doc template (whatever artifact serves as
      the next-iteration boilerplate; if no formal template exists,
      no-op).
    - `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` — narrative
      mentions only; entry text from sealed acceptance archives is
      not edited even where carry-forwards quote those archives.

    **Rationale.** "Pattern C" was an arbitrary label that accreted
    load-bearing meaning by repetition. "Adversarial Authorship"
    describes the pattern's actual structural property — drafter and
    auditor are constitutionally adversarial, with human as sole
    signing authority — and is externally distinctive enough to own
    in IR materials, README revisions, and conversation. The verbal
    rename is already in flight per Kyle's 0.2.16 close-time decision;
    this bucket performs the codebase-wide find/replace pass.

    **Out of scope.** Sealed acceptance archives in
    `artifacts/iterations/0.2.16/acceptance/W{0..4}.json` and
    `acceptance/W{1,2,3,4}-audit-dispositions.md` retain "Pattern C"
    verbatim — sealed-archive discipline forbids retroactive content
    edits. The 0.2.16 retrospective and `iteration-close-0.2.16.md`
    flag the rename for future readers; that pointer is the link from
    historical "Pattern C" archive content to current "Adversarial
    Authorship" governance language. Audit archives in
    `artifacts/iterations/0.2.16/audit/W{0..4}.json` are also sealed
    and retain "Pattern C". Pre-0.2.17 ADRs and pre-0.2.17 retrospectives
    are similarly historical and stay as-written.

### Carry-forwards potentially closed by W0

- AF004, AF005 closed (or explicitly removed-as-dead).
- F-W0-004 closed (conftest brittleness — bind-to-tmp_path
  enforcement).
- W2-AF004 closed (dispatch.duration_ms error-path test added).
- F-W1-001 closed (settings.json env-var expansion wrapper).
- Adversarial Authorship rename — codebase-wide find/replace lands
  (live governance docs only; sealed acceptance + audit archives
  retain "Pattern C" verbatim).

### Acceptance

- All five carry-forwards in scope are closed or explicitly
  reclassified.
- Podman runs clean rootless containers including GPU passthrough,
  OR Docker is engaged with rationale recorded as ADR-0007
  amendment.
- Hello-world aho container builds and runs; baseline runtime is
  confirmed before W1 builds the real Dockerfile.

### Estimated budget

3 hours. Carry-forward closures are mechanical; Podman runtime
verification + GPU passthrough is the variable wall-clock sink.

---

## W1 — Dockerfile + image build + local registry push

**Scope:** Build the real `aho:0.2.17` image and publish to the
local registry.

1. **Dockerfile authoring.** Layer order from ADR 0007's
   informational layering:
   - base layer: debian:stable-slim (or ubuntu:22.04) + Python 3.11+
   - system-deps layer: curl, git, build-essential, NVIDIA Container
     Toolkit runtime libs, ollama binary
   - python-deps layer: aho's pyproject.toml dependencies via uv
   - aho-source layer: `src/aho/`, `bin/`, `artifacts/harness/`
     installed to `/opt/aho/`
   - entrypoint layer: shell script that respects host secrets mount,
     host models mount, host config mount, and `AHO_DISPATCH_HYBRID_MODE`
     env
2. **Image size discipline.** Target: under 2 GB excluding models.
   Use multi-stage build to drop build-time dependencies; use
   `--squash` if it does not break Podman's layer caching.
3. **Local registry choice.** ADR 0007 says local-first — either a
   home-network Harbor/Docker-Distribution or `ghcr.io` namespace.
   W1 picks one and pushes; the ADR amendment (if needed) records
   the choice. Default proposal: `ghcr.io/socfoundry/aho` to keep
   per-host registry infra at zero. Kyle confirms.
4. **Image tagging.** `aho:0.2.17-rc1` for the W1 build.
   `aho:0.2.17` is the iteration-close tag (W4).
5. **Smoke test.** `podman run --rm aho:0.2.17-rc1 aho --version`
   returns the expected version. `podman run --rm aho:0.2.17-rc1
   aho doctor full` runs cleanly (subject to mount provisioning —
   may fail without secrets/models mounts, which is fine for W1; W2
   adds the mounts).

### Carry-forwards potentially closed by W1

None — image build is novel work, not carry-forward closure.

### Acceptance

- `aho:0.2.17-rc1` exists in local registry.
- Image size under 2 GB.
- Smoke `aho --version` works.
- Dockerfile lives at repo root (or `containers/Dockerfile` —
  decided in W1 based on repo convention).
- Image satisfies the k8s-readiness five (per ADR 0007 §k8s-readiness
  amendment). Each of the five is independently testable; tests live
  in `artifacts/tests/test_container_k8s_readiness.py` (created in W1).

### Estimated budget

3 hours. Dockerfile authoring + multi-stage build optimization is
the bulk; registry push is mechanical.

---

## W2 — install.fish tier detection + tier manifest + secrets mount layout

**Scope:** install.fish gains its tier-detection block (per ADR 0007),
writes the tier manifest to `~/.config/aho/tier.json` (per ADR 0008
amendment), and the container mount layout is documented and
verified.

1. **Tier detection block.** Per ADR 0007 §install.fish behavior:
   ```fish
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
2. **Tier manifest write.** install.fish writes
   `~/.config/aho/tier.json` with full ADR 0008 shape:
   ```json
   {
     "tier": "base",
     "vram_mb": 8192,
     "bundle": ["nemotron-mini:4b", "nomic-embed-text", "llama3.2:3b"],
     "families": ["nemotron", "nomic", "llama3"],
     "host_id": "NZXTcos",
     "deployment_mode": "development",
     "installed_at": "<RFC3339 timestamp>"
   }
   ```
   `deployment_mode` is detected per ADR 0008 §Deployment-mode
   resource attribute: TTY-check + `AHO_INSTALL_PRODUCTION` env +
   explicit `--production` flag. Default on a developer workstation
   is `development`.
3. **Tier-conditional model pull.** Based on detected tier,
   install.fish pulls the appropriate model bundle into
   `~/.local/share/aho/models/` (host volume; ollama-runtime layer
   in container reads from this mount). Re-running install.fish on
   unchanged tier is a no-op for already-pulled models.
4. **Secrets mount layout — documentation.** Document the canonical
   bind-mount layout:
   - `~/.config/aho/` → `/etc/aho/` (read-only) — tier manifest +
     any future config
   - `~/.local/share/aho/age/identity.txt` →
     `/opt/aho/secrets/age/identity.txt` (read-only) — age identity
   - `~/.local/share/aho/secrets/bundle.enc` →
     `/opt/aho/secrets/bundle.enc` (read-only) — encrypted bundle
   - `~/.local/share/aho/models/` → `/var/lib/ollama/` (read-only)
     — model weights
   - `~/.local/share/aho/{logs,metrics,traces,api-bodies}/` →
     `/var/log/aho/{...}/` (read-write) — telemetry sinks
5. **`aho install --container` flag.** New install.fish option that
   produces a host fully-prepared for container deployment: tier
   detected, manifest written, models pulled, secrets-mount-paths
   created (with correct ownership), telemetry-sink-paths created.
   Bare-host install path (existing) preserved for through-0.2.x
   compatibility.

### Carry-forwards potentially closed by W2

- 0.2.15 carry — Tier 1 hardware requirements documentation
  (ADR 0007's tier table is now the canonical version).
- 0.2.15 carry — Ollama service layer documentation (subset:
  containerized Ollama via mounted models is documented in W2's
  mount layout).

### Acceptance

- `install.fish --container` runs cleanly on NZXTcos.
- `~/.config/aho/tier.json` matches the ADR 0008 schema with
  correct values for NZXTcos (tier=base, vram_mb=8192, families
  match base bundle, deployment_mode=development).
- Mount-layout documentation lives in
  `artifacts/iterations/0.2.17/container-mount-layout.md`.
- All four mount points exist on the host with correct ownership
  after install.fish runs.

### Estimated budget

3 hours. Fish-shell logic + JSON authoring + mount-path provisioning
+ documentation. install.fish editing is the wall-clock sink.

---

## W3 — aho CLI in container + hybrid-mode dispatcher + `ModelNotAvailableError`

**Scope:** Dispatcher reads the tier manifest, gains hard-error and
hybrid-mode behavior per ADR 0008, and the override parameter is
implemented end-to-end.

1. **Tier manifest reader.** Add
   `src/aho/pipeline/tier_manifest.py`:
   - `load_tier_manifest(path: Path = Path('/etc/aho/tier.json')) -> TierManifest`
   - `TierManifest` dataclass with `tier`, `vram_mb`, `bundle`,
     `families`, `host_id`, `deployment_mode`, `installed_at`
   - SIGHUP-triggered reload supported.
   - Unit tests: load valid manifest, raise on malformed, reload on
     SIGHUP.
2. **`ModelNotAvailableError(DispatchError)`.** Add to dispatcher's
   typed-exception hierarchy. Includes payload: requested family,
   host tier, bundle contents, deployment mode.
3. **Family validation in `dispatch()`.** At entry, validate
   requested family against tier manifest's `families` list. Branch
   on `AHO_DISPATCH_HYBRID_MODE` env + `on_missing` parameter:
   - production (env unset, parameter default): hard-error.
   - hybrid (env set OR `on_missing='hybrid'`): route to
     `${AHO_DISPATCH_HYBRID_HOST_URL}/api/chat`, default
     `http://host.containers.internal:11434`.
   - `on_missing='error'`: explicit hard-error regardless of env.
   - `on_missing='fallback'` / `on_missing='cloud'`: raise
     `NotImplementedError`. Tests assert this.
4. **OTEL attribute emission.** When hybrid-mode routing fires, the
   dispatcher's span carries `aho.dispatch.hybrid=true`; the event
   log entry is `dispatch_hybrid_routed` with requested family +
   routing decision. The `aho.deployment.mode` resource attribute
   (set by the harness's OTEL init from the tier manifest's
   `deployment_mode` field) flows through automatically — no
   per-call code needed.
5. **`aho` CLI in container.** Verify the CLI works inside the
   container against the mounted tier manifest:
   - `aho dispatch --family nemotron --prompt "..."` succeeds
     (in-bundle).
   - `aho dispatch --family qwen --prompt "..."` (no env) hard-
     errors with `ModelNotAvailableError`.
   - `AHO_DISPATCH_HYBRID_MODE=1 aho dispatch --family qwen
     --prompt "..."` succeeds via host's native Ollama.
6. **Tests.**
   - `tests/test_tier_manifest.py`: load/validate/SIGHUP-reload.
   - `tests/test_dispatcher_missing_model.py`: covers all four
     `on_missing` parameter values + env-var-default behavior +
     hybrid-routing OTEL attributes.

### Carry-forwards potentially closed by W3

None — net-new behavior, not carry-forward closure.

### Acceptance

- All tests pass.
- `aho dispatch` against missing family hard-errors in production
  mode.
- `aho dispatch` against missing family in hybrid mode reaches the
  host's Ollama and returns a real response.
- OTEL spans from hybrid-mode dispatches carry
  `aho.dispatch.hybrid=true`.

### Estimated budget

4 hours. Dispatcher modification + tier manifest module + tests +
end-to-end-in-container verification.

---

## W4 — Telemetry from container + close package

**Scope:** Verify OTEL telemetry flows from the container to the
host collector with the new `aho.deployment.mode` resource attribute,
assemble the close package, run iteration close.

1. **Container → host collector wiring.** The container points its
   OTEL exporter at `host.containers.internal:4317` (Podman) or
   equivalent docker-host alias. Verify all three pipelines (logs,
   metrics, traces) reach the host's collector.
2. **Resource attribute verification.** Every emitted signal carries
   `aho.deployment.mode` with the value from the tier manifest.
   Verify in `~/.local/share/aho/{logs,metrics,traces}/*.jsonl` —
   one record per pipeline, per signal class.
3. **Cross-container session smoke.** Run a Claude Code session
   from inside the container (if applicable to W4 scope — may be
   later iteration). Verify `aho.workstream=W4` resource attr flows
   from container → collector.
4. **Iteration retrospective.** `retrospective-0.2.17.md` —
   honest retrospective per ADR 0006 (deliverable paragraph +
   graduation criterion are copy-from-plan, not derived).
5. **Carry-forward register.** `carry-forwards-0.2.17.md` — items
   not completed, grouped by target iteration.
6. **Bundle.** `aho-bundle-0.2.17.md` — standard 9-section bundle
   per the convention 0.2.15 established. Counts internally
   consistent (avoid the 0.2.15 AF001 recurrence; ADR 0004's
   redesign should make this mechanical if it ships in 0.2.x
   close-confirm cleanup before 0.2.17 close).
7. **Sign-off sheet.** Per ADR 0004's redesign — if landed,
   sign-off sheet is auto-generated post-close from audit archives.
   If not landed, manual checkbox-tick per legacy 0.2.x convention.
8. **`aho iteration close --confirm`.** Run with
   `AHO_ITERATION=0.2.17`. Behavior follows the version of
   `cli.py` that ships at close time.

### Hard gate blocker (graduation criterion)

The §Graduation criterion fish sequence at the top of this plan is
the close gate. All eight steps pass, or the iteration does not
close.

### Estimated budget

4 hours. Telemetry verification (1h), retrospective + carry-forwards
+ bundle (2h), iteration close mechanics (1h).

---

## Cross-iteration carry tracking

Inherited from 0.2.16 (8 items targeted to 0.2.17 or paired with
engine-selection ADR; see `artifacts/iterations/0.2.16/
carry-forwards-0.2.16.md`):

**Folded into 0.2.17 W0–W4 workstreams above:**

- AF004 / AF005 — otel_aggregator dead/alias fields (W0 Bucket 1)
- F-W0-004 — conftest allowlist brittleness (W0 Bucket 1)
- W2-AF004 — dispatch.duration_ms error-path measurement gap (W0
  Bucket 1)
- F-W1-001 — `${VAR}` expansion wrapper (W0 Bucket 1)

**Not folded — remain open carry-forwards for 0.2.18+ or specific
iterations:**

- W3-AF001 — Rule 3 expression repair (paired with engine-selection
  ADR)
- W3-AF002 — Rule 5 baseline larger n
- W3-AF003 — Rule 5 metric-source gap
- W3-CF1 — synthetic alert delivery test (engine-blocked)
- W3-CF2 — engine selection ADR (its own iteration)
- W3-CF3 — bridge live wire-up (engine-blocked)
- W3-CF4 — dedicated alerts-channel secrets (Kyle action; bridge-
  blocked)
- W3-CF5 — pillar-11-monitoring-notes as forward-pointer
- Cross-model cascade re-run (Pillar 7 verdict — its own iteration)
- Mercor reference pack assembly (its own iteration when needed)
- OTLP alias deprecation warning (next collector config touch)
- Historical trend graphs (separate iteration when metric retention
  backend is decided)
- Dashboard polling cadence unification (one-line tweak; folds into
  any UI-touch iteration)
- Classifier category drift probe (separate quality-probe iteration
  if recurring)
- Closure-capture span-attribute pattern (folds into any iteration
  that tightens the dispatcher return contract)

---

## Process discipline

Same as 0.2.16 close, plus:

- ADR 0006 deliverable paragraph + graduation criterion are
  authoritative — the retrospective reads from this plan, not from
  derived gate-summaries.
- ADR 0007 binds W1/W2 — single image, tier-conditional bundle,
  Podman default, host-mounted secrets.
- ADR 0008 binds W3 — hard-error production, hybrid-mode
  development, `on_missing=` parameter, tier manifest at
  `~/.config/aho/tier.json` (host) → `/etc/aho/tier.json`
  (container).
- `AHO_DISPATCH_HYBRID_MODE` is a development affordance only —
  the iteration's own deployment mode is `development`; production
  use of hybrid mode would be the violation alert rule fires on.
- Cross-project contamination vigilance per CLAUDE.md continues —
  zero contamination across 0.2.14, 0.2.15, 0.2.16; the discipline
  works.

---

*Plan doc 0.2.17. Companion artifacts: `aho-design-0.2.17.md`
(authored at iteration-open time), ADRs 0006 / 0007 / 0008 under
`artifacts/adrs/`. ADR numbers for any new 0.2.17 ADRs determined
at execution time from disk enumeration — not pre-fabricated here.*
