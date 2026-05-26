# aho-plan-0.2.18

**Iteration:** 0.2.18
**Theme:** Base-tier aho on a second physical host - a8geekomCos via
Tailscale, cross-host OTEL collection, per-host secrets broker
**Phase:** 0 (Clone-to-Deploy)

---

## Iteration deliverable

> **0.2.18 ships base-tier aho to a8geekomCos as a second physical
> host via Tailscale (100.74.161.116).** The iteration cuts
> `aho:0.2.18` baking the cross-host OTLP endpoint default into the
> image (NZXTcos's Tailscale-resolvable name on port 4317);
> install.fish runs cleanly on fresh a8geekomCos hardware, classifies
> the host as base tier (no nvidia-smi → base per ADR 0007), pulls
> the base bundle, and prompts the operator to provision a host-local
> secrets broker - no cross-host secret tunneling. The Adversarial
> Authorship harness exercises end-to-end inside the container on
> a8geekomCos with the in-container `llama3.2:3b` auditor seat,
> advancing the ADR-0010 materiality data counter from N=5 to N≥6
> (still below the N≥8 full-validation threshold). NZXTcos's
> existing OTEL collector is rebound from `localhost:4317` to its
> Tailscale interface; a8geekomCos OTLP traffic lands there with
> `host.name=a8geekomCos` as a resource attribute distinguishing
> per-host signal flows. The 0.3 charter is untouched -
> partial-tier on tsP3 remains 0.3.1, full-tier cloud serving plane
> remains 0.3.2.

## Graduation criterion (Form 1: runnable test)

0.2.18 graduates when the following sequence completes cleanly. Steps
1–6 run on a8geekomCos; step 7 runs on NZXTcos (or via SSH from
a8geekomCos to NZXTcos); step 8 runs on either host with the repo
checked out.

```fish
# 1. install.fish ran cleanly on a8geekomCos
test -f ~/.config/aho/tier.json
and jq -e '.tier == "base" and .host_id == "a8geekomCos" and .deployment_mode == "production"' \
    ~/.config/aho/tier.json

# 2. Image built (or pulled) and tagged
podman images aho:0.2.18 | grep -q '0.2.18'

# 3. Image carries the cross-host OTLP endpoint default
podman run --rm aho:0.2.18 sh -c 'echo $OTEL_EXPORTER_OTLP_ENDPOINT' \
    | grep -qE '4317$'
podman run --rm aho:0.2.18 sh -c 'echo $OTEL_EXPORTER_OTLP_ENDPOINT' \
    | grep -vqE '^https?://localhost'

# 4. Host-local secrets broker reachable on a8geekomCos
test -S ~/.local/share/aho/broker/broker.sock

# 5. Container starts cleanly with secrets + tier mounts; aho doctor full passes
podman run --rm --name aho-smoke \
    -v ~/.config/aho:/etc/aho:ro \
    -v ~/.local/share/aho/age/identity.txt:/opt/aho/secrets/age/identity.txt:ro \
    -v ~/.local/share/aho/secrets/bundle.enc:/opt/aho/secrets/bundle.enc:ro \
    -v ~/.local/share/aho/broker/broker.sock:/run/aho-broker.sock \
    -e AHO_ITERATION=0.2.18 \
    -e AHO_WORKSTREAM=W3 \
    aho:0.2.18 \
    aho doctor full

# 6. Smoke dispatch against in-bundle base-tier family from inside the container
podman run --rm \
    -v ~/.config/aho:/etc/aho:ro \
    aho:0.2.18 \
    aho dispatch --family llama3 --prompt "ping"
# expected: completes; emits a span with host.name=a8geekomCos resource attr

# 7. Cross-host OTEL signal landed at NZXTcos collector with correct host attribution
# (run on NZXTcos)
grep -F '"host.name":"a8geekomCos"' ~/.local/share/aho/logs/*.jsonl | head -1
grep -F '"host.name":"a8geekomCos"' ~/.local/share/aho/traces/*.jsonl | head -1
grep -F '"aho.iteration":"0.2.18"' ~/.local/share/aho/metrics/*.jsonl | head -1

# 8. Acceptance + audit archives present for each workstream; materiality recorded
for n in 0 1 2 3 4
    if not test -f artifacts/iterations/0.2.18/acceptance/W$n.json
        echo "FAIL: acceptance/W$n.json missing"
        exit 1
    end
    if not test -f artifacts/iterations/0.2.18/audit/W$n.json
        echo "FAIL: audit/W$n.json missing"
        exit 1
    end
end
# W3 (harness-cycle workstream) records the materiality data point
jq -e '.materiality.deployment_count >= 6 and .materiality.auditor_seat == "in-container-llama3.2-3b"' \
    artifacts/iterations/0.2.18/acceptance/W3.json
```

Each step is hard pass/fail. The graduation criterion is the runnable
equivalent of the deliverable paragraph: image exists with cross-host
OTLP baked, install.fish + broker provisioning landed cleanly,
container runs end-to-end on the new host, and the OTEL plumbing
proves a8geekomCos signals reach NZXTcos's collector with correct
resource attribution. The fish sequence is the canonical close-time
check.

---

## Plan amendments (pre-W0)

None. Plan-doc drafted in this session and surfaced to operator for
sign-off before any `workstream_start` event fires.

---

## Role assignment for 0.2.18 (deviation from 0.2.17 pattern)

0.2.17 settled the four roles as:

| Role | Agent |
|---|---|
| drafter | claude-web |
| executor | claude-code |
| auditor | in-container `llama3.2:3b` (with W3 RAG enrichment + W4 deterministic post-hoc filter) |
| operator | Kyle |

0.2.18 deviates on the drafter slot: **drafter = claude-code (this
session)**. Operator-explicit choice - see chat record at plan-doc
authoring time. Other slots unchanged.

**Pillar 7 implications.** Generation/evaluation separation (Pillar 7)
is between drafter+executor (generation) and auditor (evaluation).
Drafter+executor sameness in 0.2.18 does not violate Pillar 7 because
the auditor is a distinct model (`llama3.2:3b`) with a distinct
prompt and a distinct wrapper. The deviation is from the
0.2.17-settled Adversarial Authorship pattern's drafter/executor
split, not from Pillar 7 itself. Recorded for auditability;
W0 CLAUDE.md rewrite makes the deviation explicit in the harness
contract.

---

## Workstream summary

| N | Theme | Gate |
|---|---|---|
| W0 | 0.2.17 carry-forward closure + CLAUDE.md rewrite (0.2.16 → 0.2.18) + a8geekomCos hardware/network probe | F-0.2.17-W6-003 gitignore gap closed; CLAUDE.md reflects 0.2.18 iteration + revised role assignment; a8geekomCos OS family + Tailscale reachability + podman-availability + iGPU profile probed and recorded |
| W1 | `aho:0.2.18` image build with cross-host OTLP endpoint default baked + push to ghcr.io | Image builds clean; size delta vs `aho:0.2.17-rc2` recorded; `OTEL_EXPORTER_OTLP_ENDPOINT` default points at NZXTcos's Tailscale name; smoke `aho --version` works; Kyle pushes to `ghcr.io/soc-foundry/aho:0.2.18` (Pillar 11 - agents prepare, operator pushes) |
| W2 | install.fish on a8geekomCos + host-local secrets broker provisioning prompt + NZXTcos collector rebind | install.fish runs cleanly on a8geekomCos; tier manifest written with `host_id=a8geekomCos`, `tier=base`, `deployment_mode=production`; broker socket present at `~/.local/share/aho/broker/broker.sock`; NZXTcos collector binds Tailscale interface (config change recorded as artifact); a8geekomCos→NZXTcos OTLP reachability verified |
| W3 | Adversarial Authorship harness cycle on a8geekomCos + materiality data point | One drafter→executor→auditor cycle runs end-to-end inside container; auditor deployment count advances to N≥6; `acceptance/W3.json` records materiality fields per ADR-0010 |
| W4 | Telemetry verification + close package | Cross-host OTEL flow verified per graduation criterion step 7; retrospective applies ADR 0006 deliverable + criterion; carry-forward register lands; iteration close package per current `aho iteration close --confirm` semantics |

---

## W0 - 0.2.17 carry-forward closure + CLAUDE.md rewrite + a8geekomCos probe

**Scope:** Three coordinated buckets - close 0.2.17 carry-forwards
that target 0.2.18 / early-base-tier-hygiene, refresh CLAUDE.md to
0.2.18 contract, and probe a8geekomCos so W1/W2 launch with hardware
facts in hand rather than assumptions.

### Bucket 1 - Carry-forward closures from 0.2.17

1. **F-0.2.17-W6-003 - gitignore gap.** `.aho-checkpoint.json` and
   `.claude/settings.json` were tracked despite being in
   `.dockerignore`. Operator-side remediation already executed at
   0.2.17 close per `iteration-close-0.2.17.md`; W0 verifies the
   `.gitignore` mirrors `.dockerignore`'s working-state list and
   that no working-state file is still tracked. If still tracked,
   surface to Kyle for `git rm --cached` (Pillar 11 - agent
   surfaces, operator executes).
2. **F-0.2.17-W5-002 - plan-doc / repo-convention path drift.** This
   plan-doc itself is the first 0.2.18 artifact authored under the
   carry-forward; verify `artifacts/adrs/` (not `docs/adr/`) and
   `artifacts/iterations/0.2.18/` (not `docs/iterations/`) are the
   conventions used throughout. Add a one-paragraph
   convention-anchor note to `artifacts/harness/prompt-conventions.md`
   so future plan-docs inherit the correction at the convention
   layer, not via repeated drafter-side correction.
3. **F-0.2.17-W6-002 - council embed timeout default too tight.**
   Bump default `AHO_COUNCIL_EMBED_TIMEOUT_S` from 30s to 120s in
   `src/aho/council/embed.py`. Single-line change with a unit-test
   amendment. NZXTcos 8GB VRAM substrate condition does not
   manifest on a8geekomCos (no GPU contention there) but the fix
   is repo-wide and lands here for completeness.
4. **F-0.2.17-W5-001 + F-0.2.17-W6-001 deferred.** Both target
   audit-time machinery refinements (structural pre-check JSON path
   exclusion; opaque-ID metadata indexing). Neither blocks
   a8geekomCos deployment. Carry forward to 0.3.x or a dedicated
   audit-machinery iteration. Recorded explicitly in W4
   carry-forward register.

### Bucket 2 - CLAUDE.md rewrite (0.2.16 → 0.2.18)

5. **CLAUDE.md content refresh.** Current CLAUDE.md still asserts
   "Current Iteration: 0.2.16" and casts Claude Code as "primary
   drafter under Adversarial Authorship (modified)" - both stale.
   W0 rewrites:
   - Iteration label: 0.2.16 → 0.2.18.
   - Role assignment: explicit four-role table per §Role assignment
     above; document the drafter=claude-code deviation with
     rationale.
   - 0.2.17 inheritance: cite `iteration-close-0.2.17.md`,
     `docs/retrospectives/0.2.17.md`, ADR 0007 amended,
     ADRs 0009 + 0010 new.
   - Materiality counter: N=5/N≥8 per ADR-0010, with the note that
     0.2.18 W3 advances the counter.
   - OTEL environment: cross-host `OTEL_EXPORTER_OTLP_ENDPOINT`
     default points at NZXTcos's Tailscale name; per-host
     `host.name` resource attribute distinguishes signal flows.
   - Pillar 11 monitored-invariant section: unchanged from 0.2.16
     wording; carry forward.
   - Cross-project contamination vigilance: unchanged; carry
     forward (zero contamination across 0.2.14, 0.2.15, 0.2.16,
     0.2.17 - the discipline works).
6. **GEMINI.md content refresh (if applicable).** GEMINI.md exists
   per 0.2.17 W0 rename pass; if 0.2.18 keeps Gemini available
   only as fallback (per Kyle's plan-time decision), GEMINI.md
   gains a §Fallback role section noting Gemini is installed on
   a8geekomCos but is not the canonical auditor seat. If
   GEMINI.md does not exist as a live governance file in
   0.2.18, the bullet is no-op.

### Bucket 3 - a8geekomCos probe

7. **Tailscale reachability.** From NZXTcos:
   ```fish
   tailscale ping 100.74.161.116
   tailscale status | grep a8geekomCos
   ```
   Record latency, MagicDNS name, and tailnet identity. The
   MagicDNS name is the value baked into the W1 image's OTLP
   endpoint default; record it now.
8. **OS family + base packages.** From NZXTcos via Tailscale SSH:
   ```fish
   ssh a8geekomCos 'cat /etc/os-release ; uname -r ; which podman ; which fish ; which ollama'
   ```
   Decision gate: if not Arch/CachyOS, the install.fish
   portability assumptions from 0.2.17 may not hold. Document
   what the OS is and whether install.fish needs adaptation
   in W2. If significant adaptation is required, surface to
   Kyle as a scope-amendment trigger (ADR 0006 hard meta-rule)
   before proceeding - do not silently expand W2 scope.
9. **CPU/iGPU profile.** From a8geekomCos:
   ```fish
   lscpu | head -20
   command -q nvidia-smi ; or echo "no nvidia-smi (expected for base tier)"
   lspci | grep -iE 'vga|3d|display'
   ```
   Confirm base-tier classification: no `nvidia-smi` → install.fish
   tier-detection block returns `base`. Record actual silicon for
   `tier.json`'s `vram_mb` field (likely 0 or the iGPU's shared
   memory cap).
10. **Disk capacity.** From a8geekomCos:
    ```fish
    df -h ~ /
    ```
    Confirm at least ~5GB free for image + base bundle (llama3.2:3b
    ~2GB + nomic-embed-text ~270MB + image ~1.5GB).

### Carry-forwards potentially closed by W0

- F-0.2.17-W6-003 closed (gitignore mirror verified).
- F-0.2.17-W5-002 closed at the convention layer (prompt-conventions
  anchor note).
- F-0.2.17-W6-002 closed (embed timeout bump).

### Acceptance

- `.gitignore` mirrors `.dockerignore` working-state list; no working
  state files tracked.
- `artifacts/harness/prompt-conventions.md` carries the path-convention
  anchor note.
- `src/aho/council/embed.py` default timeout bumped to 120s; tests
  pass.
- CLAUDE.md is at 0.2.18 with the role-assignment deviation explicit.
- a8geekomCos probe artifact lives at
  `artifacts/iterations/0.2.18/probes/a8geekomCos-baseline.md` -
  Tailscale latency + MagicDNS name + OS family + CPU/iGPU profile +
  disk capacity recorded.
- If install.fish portability adaptation is required, scope-amendment
  surfaced to Kyle before W1 launches.

### Estimated budget

3 hours. Carry-forward closures are mechanical (~30min); CLAUDE.md
rewrite is contained (~45min); a8geekomCos probe wall-clock depends
on Tailscale-SSH responsiveness and how much install.fish adaptation
the OS family requires (~1.5h).

---

## W1 - `aho:0.2.18` image build with cross-host OTLP endpoint baked + push

**Scope:** Cut a new image that bakes NZXTcos's MagicDNS name as the
default OTLP collector. Image is otherwise the 0.2.17-rc2 carry-over
plus the embed-timeout fix from W0 Bucket 1.

1. **Dockerfile delta from 0.2.17.** Compare against the 0.2.17
   Dockerfile (path determined at execution time - likely
   `containers/Dockerfile` per W1 0.2.17 disposition); the only
   intentional changes for 0.2.18 are:
   - `OTEL_EXPORTER_OTLP_ENDPOINT` default in entrypoint shell
     points at `<nzxtcos-magicdns>:4317` (value from W0 probe).
   - `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` baked as default.
   - Source layer pulls in W0's embed-timeout fix.
   - `aho` package version bumped to `0.2.18` in source.
   No other intentional content changes. Multi-stage layout +
   image size discipline carry from 0.2.17.
2. **Image-size delta budget.** ≤ 50 MB delta vs `aho:0.2.17-rc2`.
   If delta exceeds, surface and investigate - image size
   regression is a substrate signal, not a budget rounding.
3. **Smoke test (host-side build).** On NZXTcos:
   ```fish
   podman build -t aho:0.2.18 -f containers/Dockerfile .
   podman images aho:0.2.18 | grep -q '0.2.18'
   podman run --rm aho:0.2.18 aho --version
   # expected: "0.2.18"
   podman run --rm aho:0.2.18 sh -c 'echo $OTEL_EXPORTER_OTLP_ENDPOINT'
   # expected: contains the nzxtcos magicdns name + ":4317"
   ```
4. **Registry push (Pillar 11 - operator-executed).** Agents
   prepare the push command; Kyle runs:
   ```fish
   gh auth token | podman login ghcr.io -u <kyle-user> --password-stdin
   podman tag aho:0.2.18 ghcr.io/soc-foundry/aho:0.2.18
   podman push ghcr.io/soc-foundry/aho:0.2.18
   ```
   Manifest digest recorded in `acceptance/W1.json` after push.
5. **k8s-readiness regression check.** Per ADR 0007's k8s-readiness
   five (config from env, secrets from mounts, logs to stdout +
   sinks, SIGTERM handling, health endpoint), `aho:0.2.18` must
   still satisfy all five. The 0.2.17 W1 test
   (`artifacts/tests/test_container_k8s_readiness.py`) re-runs
   against the new image. If any test fails, image is rejected
   and the Dockerfile regression is fixed before push.

### Carry-forwards potentially closed by W1

None. Image build is forward-motion work.

### Acceptance

- `aho:0.2.18` exists locally on NZXTcos and at
  `ghcr.io/soc-foundry/aho:0.2.18`.
- Manifest digest recorded.
- Image carries cross-host OTLP endpoint default pointing at
  NZXTcos's Tailscale name.
- k8s-readiness five tests pass against the new image.
- Image-size delta vs 0.2.17-rc2 ≤ 50 MB.

### Estimated budget

2 hours. Mostly mechanical Dockerfile edit + rebuild + push wait.
The W0 probe should have surfaced any portability surprises that
would extend W1.

---

## W2 - install.fish on a8geekomCos + host-local broker + NZXTcos collector rebind

**Scope:** Bring a8geekomCos to deployable state. install.fish runs
cleanly, secrets broker provisions host-locally, NZXTcos's collector
accepts inbound Tailscale traffic.

1. **Image transfer to a8geekomCos.** Two patterns from 0.2.17
   close-out apply (operator chooses):
   - **Operator-immediate (recommended for a8geekomCos):**
     `podman save aho:0.2.18 -o /tmp/aho-0218.tar` on NZXTcos →
     `scp /tmp/aho-0218.tar a8geekomCos:/tmp/` over Tailscale →
     `podman load -i /tmp/aho-0218.tar` on a8geekomCos. Avoids
     ghcr.io credential dance on a fresh box. Tailscale bandwidth
     to a8geekomCos is the variable; W0 latency probe informs the
     wall-clock estimate.
   - **Canonical (engineer-onboarding pattern):** `gh auth token
     | podman login ghcr.io -u <user> --password-stdin` then
     `podman pull ghcr.io/soc-foundry/aho:0.2.18` on a8geekomCos.
     Requires `gh` CLI authenticated on a8geekomCos.
2. **install.fish on a8geekomCos.**
   ```fish
   # On a8geekomCos
   git clone <aho-repo> ~/dev/projects/aho
   cd ~/dev/projects/aho
   ./install.fish --container --host-id a8geekomCos --deployment-mode production
   ```
   Behavior expectations:
   - Tier detection returns `base` (no nvidia-smi present).
   - Tier manifest written to `~/.config/aho/tier.json` with
     `host_id=a8geekomCos`, `tier=base`,
     `deployment_mode=production`, `families=["llama3", "nomic"]`,
     `bundle=["llama3.2:3b", "nomic-embed-text"]`.
   - Base-tier model bundle pulled into
     `~/.local/share/aho/models/`.
   - Mount-path skeleton created with correct ownership:
     `~/.config/aho/`, `~/.local/share/aho/{age,secrets,models,broker,logs,metrics,traces}`.
3. **Host-local secrets broker provisioning prompt.** install.fish
   reaches a checkpoint after tier-manifest write where it
   prompts the operator:

   > "Provision host-local secrets broker on a8geekomCos? Per
   > ADR 0009, each host runs its own broker - no cross-host
   > tunneling. Operator action required to seed the broker
   > with local secrets. [y/N]"

   On `y`: install.fish provisions the broker socket at
   `~/.local/share/aho/broker/broker.sock`, sets ownership,
   and prints follow-up instructions for the operator to
   seed secrets via the existing `aho secret add` flow. On
   `N`: install.fish exits with a non-zero code and a clear
   message that the install is not complete.

   No agent reads or writes secret values during this
   workstream - broker provisioning is structural setup;
   secret seeding is operator-only.
4. **NZXTcos collector rebind to Tailscale interface.** On
   NZXTcos:
   - Locate the otelcol-contrib config file (likely
     `~/.config/otelcol-contrib/config.yaml` or
     `/etc/otelcol-contrib/config.yaml` per ADR 0003 §Substrate
     posture).
   - Receivers' `endpoint` value: `localhost:4317` →
     `0.0.0.0:4317` (or specifically the Tailscale interface
     IP if firewalled).
   - Restart collector. Verify with:
     ```fish
     ss -ltnp | grep 4317
     # expected: bound on tailscale interface, not just loopback
     ```
   - **Pillar 11 alert channel surface.** The 0.2.16 W3
     alert engine (if live) fires on collector reachability
     change events. W2 is expected to produce one - Kyle
     acknowledges in close-note.
5. **a8geekomCos → NZXTcos OTLP reachability test.** From
   a8geekomCos:
   ```fish
   nc -zv <nzxtcos-magicdns> 4317
   # expected: connection succeeds
   ```
   If this fails, surface immediately - NZXTcos collector bind
   change did not take, or Tailscale firewall blocks 4317.
6. **install.fish portability disposition.** If W0 surfaced
   non-Arch OS family on a8geekomCos, W2 carries the
   adaptation work. Adaptation acceptance: install.fish
   completes without manual intervention beyond the
   broker-provisioning prompt. If adaptation requires
   substantive new code (>50 lines of OS-family-specific
   branching), surface as scope amendment.

### Carry-forwards potentially closed by W2

- 0.2.17 carry - install.fish second-host portability (was
  implicit until exercised on a different host; now empirically
  tested).
- ADR 0007 §Registry choice deferral surface - partial
  exercise. W2 demonstrates ghcr.io pull works from a second
  host; full registry-choice resolution remains 0.3.2 scope.

### Acceptance

- `aho:0.2.18` present on a8geekomCos (load or pull verified).
- `~/.config/aho/tier.json` on a8geekomCos matches expected
  shape with `host_id=a8geekomCos`, `tier=base`,
  `deployment_mode=production`.
- Host-local broker socket exists at
  `~/.local/share/aho/broker/broker.sock`.
- NZXTcos collector accepts inbound Tailscale traffic on 4317.
- a8geekomCos → NZXTcos reachability verified via `nc`.
- install.fish portability disposition recorded
  (clean-Arch / adapted / scope-amendment).

### Estimated budget

4 hours. Image transfer ~30min depending on bandwidth.
install.fish wall-clock is the variable - clean Arch run is
~45min including model pulls; portability adaptation could
extend to 2h+. Collector rebind is ~30min. Reachability +
disposition record is ~30min.

---

## W3 - Adversarial Authorship harness cycle on a8geekomCos + materiality data point

**Scope:** Exercise the harness end-to-end inside the container on
a8geekomCos. Drafter→executor→auditor cycle runs once with measured
materiality fields, advancing the ADR-0010 counter from N=5 to N≥6.

1. **Workstream-shaped exercise.** Use a synthetic small
   workstream (e.g., a 3-5 line code change in a non-load-bearing
   utility module, or a documentation-only change) as the cycle's
   target. The exercise validates the harness machinery, not the
   specific code change. Selection criterion: the change must
   have a non-trivial audit surface - registered anchor IDs
   present, structural pre-checks fire-eligible - so the auditor
   has something to assess. Pure-noop changes don't generate
   materiality signal.
2. **Drafter** (claude-code, this session pattern carried
   forward): authors the change description and acceptance
   archive shape.
3. **Executor** (claude-code, separate session, AHO_ITERATION=0.2.18,
   AHO_WORKSTREAM=W3): runs the change inside the container on
   a8geekomCos. All work happens in-container; file edits go
   through host-mounted source via the W2 mount layout.
4. **Auditor** (in-container `llama3.2:3b` with W3 0.2.17 RAG
   enrichment + W4 0.2.17 deterministic post-hoc filter
   inherited): reads the acceptance archive and emits an audit
   archive. The W4-001 RAG re-index hook + audit-finding-filter
   are inherited from 0.2.17 W6 closure; W3 of 0.2.18 verifies
   they continue to behave correctly on a different host.
5. **Materiality fields recorded in `acceptance/W3.json`:**
   - `auditor_seat`: `"in-container-llama3.2-3b"`
   - `deployment_count`: integer ≥ 6 (cumulative count
     post-this-deployment)
   - `host`: `"a8geekomCos"`
   - `filter_eligible`: boolean
   - `registered_id_count`: integer
   - `suppressed_count`: integer
   - `audit_finding_count`: integer
   - `pre_check_fires`: list of structural pre-check fires (if any)
6. **Cross-host OTEL trace continuity.** The W3 harness cycle
   emits OTLP signals from a8geekomCos. They land at NZXTcos's
   collector. The acceptance archive records the trace ID and
   confirms `host.name=a8geekomCos` resource attr is present in
   each emitted record (one per pipeline: logs, metrics, traces).
   This is the empirical proof of the cross-host OTEL
   plumbing working, not a separate W4 verification.

### Carry-forwards potentially closed by W3

None. W3 is forward-motion materiality-data-generation work.

### Acceptance

- One full Adversarial Authorship cycle ran on a8geekomCos with
  measured materiality fields populated.
- `deployment_count` ≥ 6 recorded in `acceptance/W3.json`.
- `host=a8geekomCos` recorded in materiality fields.
- Cross-host OTEL trace ID captured and `host.name=a8geekomCos`
  resource attr confirmed in NZXTcos collector records.
- Audit archive emitted with `audit_status` ∈
  {`pass`, `pass_with_findings`}; halt-and-surface invariant
  preserved if any pre-check fires.

### Estimated budget

3 hours. Exercise selection (~30min); drafter+executor cycle
(~1h); auditor cycle + arbitration (~30min); OTEL trace
verification + materiality fields (~1h).

---

## W4 - Telemetry verification + close package

**Scope:** Verify cross-host OTEL flow per the graduation criterion's
step 7, assemble close artifacts, run iteration close.

1. **Cross-host telemetry verification.** Graduation criterion
   step 7 - re-run as part of W4 acceptance with explicit
   evidence captured:
   - `~/.local/share/aho/logs/*.jsonl` on NZXTcos contains
     `host.name=a8geekomCos` records.
   - `~/.local/share/aho/traces/*.jsonl` on NZXTcos contains
     spans with `host.name=a8geekomCos` resource attr.
   - `~/.local/share/aho/metrics/*.jsonl` on NZXTcos contains
     metric records tagged `aho.iteration=0.2.18`.
   - Trace from W3 (with cross-host OTEL trace ID) is reachable
     in Jaeger if Jaeger is operational.
2. **Iteration retrospective.** `docs/retrospectives/0.2.18.md`
   (note: per 0.2.17 W5 D6 convention, retrospective lives at
   `docs/retrospectives/<iter>.md`, not under
   `artifacts/iterations/`). Honest retrospective per ADR 0006
   and the operating-stance discipline. The deliverable
   paragraph + graduation criterion are copy-from-this-plan,
   not derived. §Graduation criterion section asserts each
   numbered fish step against current state.
3. **Carry-forward register.**
   `artifacts/iterations/0.2.18/carry-forwards-0.2.18.md` -
   items not closed by 0.2.18, with target iteration recorded.
   Expected: F-0.2.17-W5-001, F-0.2.17-W6-001, F-0.2.17-W1-003
   (token rotation if not done by Kyle pre-iteration), plus
   any new findings surfaced during 0.2.18.
4. **Iteration bundle.**
   `artifacts/iterations/0.2.18/aho-bundle-0.2.18.md` - standard
   9-section bundle per the 0.2.15-established convention.
   Counts internally consistent (avoid the 0.2.15 AF001
   recurrence).
5. **Sign-off sheet.** Per ADR 0004's redesigned `--confirm`
   semantics - auto-generated post-close from audit archives
   if the redesign is live, or manual checkbox-tick per legacy
   convention.
6. **`aho iteration close --confirm`.** Run with
   `AHO_ITERATION=0.2.18`. State machine advances per the
   current `cli.py` semantics.
7. **Iteration-close note crowning.**
   `artifacts/iterations/0.2.18/iteration-close-0.2.18.md`
   crowns the W0–W4 close-note chain (does not duplicate it),
   with sealed-archive inventory + operator sign-off
   attestation per the 0.2.17 pattern.

### Hard gate blocker (graduation criterion)

The §Graduation criterion fish sequence at the top of this plan
is the close gate. All 8 steps pass, or the iteration does not
close.

### Estimated budget

3 hours. Telemetry verification (~30min); retrospective +
carry-forwards + bundle (~1.5h); close mechanics (~30min);
iteration-close note (~30min).

---

## Cross-iteration carry tracking

Inheriting from 0.2.17 (5 carrying-forward items + 1 hard gate per
`iteration-close-0.2.17.md`):

**Folded into 0.2.18 W0 (closed in this iteration if W0 lands
clean):**

- F-0.2.17-W6-003 - gitignore gap (W0 Bucket 1)
- F-0.2.17-W6-002 - council embed timeout default (W0 Bucket 1)
- F-0.2.17-W5-002 - plan-doc / repo-convention path drift (W0 Bucket
  1, convention-layer fix)

**Not folded - remain open for 0.3.x or audit-machinery iteration:**

- F-0.2.17-W5-001 - structural pre-check self-referential pattern
  (audit-machinery refinement; not a8geekomCos-blocker)
- F-0.2.17-W6-001 - audit-time lookup ranking opaque-ID misses
  (audit-machinery refinement; not a8geekomCos-blocker)

**Operator-side hard gate (pre-deployment, non-blocking iteration
plan but blocks W2 launch):**

- F-0.2.17-W1-003 - `ahomw:telegram_bot_token` rotation. Kyle
  rotates pre-W2 using the W6 D1 hash-fingerprint contract.
  Verification artifact (pre/post fingerprint differ) lands in
  `artifacts/iterations/0.2.18/probes/`. If not done by W2
  launch, W2 halts and surfaces.

**Materiality counter (ADR-0010):**

- 0.2.17 closed at N=5. 0.2.18 W3 advances to N≥6. Three more
  iterations of auditor-seat data are required after 0.2.18 for
  full validation (N≥8); 0.3.1 + 0.3.2 + 0.3.3 are the likely
  candidates per `iteration-close-0.2.17.md` §Forward-looking note.

---

## Process discipline

Same as 0.2.17 close, plus:

- ADR 0006 deliverable paragraph + graduation criterion are
  authoritative - the retrospective reads from this plan, not from
  derived gate-summaries.
- ADR 0007 binds W1/W2 - single image, install.fish tier detection,
  host-mounted secrets per the layout 0.2.17 W2 settled.
- ADR 0008 binds the dispatcher behavior inside the container; W3's
  harness cycle exercises in-bundle base-tier dispatches only -
  hybrid-mode and on_missing= behavior are unchanged from 0.2.17.
- ADR 0009 binds the secrets broker boundary - host-local on
  a8geekomCos, no cross-host tunneling, operator-provisioned.
- ADR 0010 binds the materiality measurement - W3 records the
  per-deployment materiality fields, advancing the counter.
- Pillar 11 monitored invariant continues - agents do not commit,
  push, merge, or surface git operations. W1 image push is
  operator-executed. F-0.2.17-W1-003 token rotation is
  operator-executed pre-W2.
- Cross-project contamination vigilance per CLAUDE.md continues -
  a8geekomCos is the second physical host aho deploys to and the
  first non-NZXTcos box; this is an elevated contamination-risk
  surface (other-project conventions could leak). Discipline holds.
- Adversarial Authorship state machine: `workstream_start` →
  `pending_audit` → `audit_complete` → `workstream_complete` per
  CLAUDE.md. No agent emits `workstream_complete` before
  `audit_complete` exists. Audit archive overwrites forbidden;
  re-audits create `audit/W{N}-v2.json` etc.

---

*Plan doc 0.2.18. Authored by claude-code (Opus 4.7, 1M context) as
this iteration's drafter - deviation from the 0.2.17 pattern
recorded in §Role assignment. Companion artifacts: ADR 0006
(deliverable discipline), ADR 0007 amended (containerization +
council roles), ADR 0009 (secrets broker boundary), ADR 0010
(materiality measurement). ADR numbers for any new 0.2.18 ADRs
determined at execution time from
`artifacts/adrs/` enumeration - not pre-fabricated here. The 0.3
charter at `artifacts/iterations/0.3/iteration-3-charter.md`
remains in force; 0.2.18 inserts ahead of 0.3.1 and does not
amend the charter.*
