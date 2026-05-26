# aho 0.3.1 plan-doc

**Iteration:** 0.3.1
**Status:** plan-doc draft (W0 input)
**Authored:** 2026-05-23 (post 0.2.18 close + 0.3.0 pre-flight + SCoT remediation on a8cos)
**Authoring agent:** drafter (claude-web)
**Predecessor:** 0.2.18 (closed; image `ghcr.io/soc-foundry/aho:0.2.18` digest `sha256:9f6b5844d365…`, materiality counter advancing toward N=6 pending 0.2.18 W3)
**Pre-iteration work:** 0.3.0 was a pre-flight + SCoT remediation pass on a8cos, NOT a workstream-shaped iteration. Substrate facts captured in `artifacts/iterations/0.3.0/0.3.0-drafter-context.md`. No 0.3.0 close note exists; nothing to inherit beyond the brief.

---

## Iteration thesis

0.3.1 ships the first Adversarial Authorship workstream cycle executed end-to-end on **p3cos** (partial tier, RTX 2000 Ada 16 GB) inside the `ghcr.io/soc-foundry/aho` container, deploys **`qwen3.5:9b`** as the partial-tier auditor seat, closes the substrate-decoherence load-bearing failure surfaced as F-0.2.18-W1-004 via a **lightweight freshness telemetry layer**, lands the **Tachtech Chain of Trust L5 reframing** as a named architectural decision (ADR-0012), and folds the 0.2.18 W2 carry-forward backlog (tier-aware models, tier-manifest writer, broker systemd template) into install.fish.

Materiality counter advances from N=5/6 toward N=7. The harness contract from `artifacts/harness/base.md` holds across the host change; the auditor model changes from `llama3.2:3b` at base tier to `qwen3.5:9b` at partial tier with a clean tier-vs-model decoupling data point.

---

## Adversarial Authorship roles (restored to 0.2.17 split)

- **Drafter:** claude-web (this session, persistent project folder). 0.2.18 collapsed drafter+executor to claude-code per operator-explicit deviation; 0.3.1 restores the split to extract a clean comparison data point on the deviation's protocol-level cost.
- **Executor:** claude-code on NZXTcos for substrate work (W0/W1/W2/W5/W6/W7); claude-code on **p3cos** for the partial-tier deployment workstreams (W3/W4). Gemini CLI available for external audit slots if needed.
- **Auditor seat:** `llama3.2:3b` in-container at base tier (NZXTcos, a8cos, x9cos); **`qwen3.5:9b` in-container at partial tier (p3cos)** — W3 first deployment, W4 first dogfooded audit on cross-host workstream artifact.
- **Operator:** Kyle (sign-off, all git operations, all secret reads, all hardware-side actions). Pillar 11 binding.

## Pre-iteration carry-forward inventory

### Carrying forward from 0.2.18

**Closing in 0.3.1 scope:**
- **F-0.2.18-W1-004** — substrate decoherence: tailnet FQDN `nzxtcos.tail78a311.ts.net` baked into W1 image at 0.2.18 W0 probe → tailnet rolled (a8 rebuilt) → seven days later W2 pre-flight tripped on stale FQDN → unscheduled image rebuild. **Closure: W1 substrate freshness telemetry (ADR-0011 lightweight tier).**
- **F-0.2.18-W2-002** — `bin/aho-models` is Tier-1-only (`nvidia-smi` + ≥8GB VRAM required). Base-tier hosts (a8cos, x9cos) hit a capability gap. **Closure: W2 tier-aware refactor.**
- **F-0.2.18-W2-003** — `install.fish` writes no `~/.config/aho/tier.json`. **Closure: W2 `aho install tier-manifest` subcommand.**
- **F-0.2.18-W2-004** — no `aho-secrets-broker.service.template` in `templates/systemd/`; ADR-0009 broker-per-host mandate not realized in install.fish. **Closure: W2 broker systemd template.**
- **F-0.2.18-W2-005** — broker socket path divergence (plan-doc `~/.local/share/aho/broker/broker.sock` vs code default `$XDG_RUNTIME_DIR/aho-secrets.sock`). **Closure: W7 ADR-0009 amendment canonicalizing the XDG path.**
- **F-0.2.18-W2-007** — `bin/aho-python` fish-cache staleness at `doctor` path (already patched at `install` path). **Closure: W7.**

**Deferring to dedicated audit-machinery iteration (0.3.2 candidate):**
- **F-0.2.18-W0-008** — narrative-lift (small-model lifts prior-cycle commentary as findings).
- **F-0.2.18-W2-009** — prompt-instruction echo (model echoes auditor-prompt text as finding entry).
- **F-0.2.17-W5-001** — audit-time structural pre-check self-referential pattern.
- **F-0.2.17-W6-001** — audit-time RAG lookup ranking on opaque `F-X.Y.Z-WN-NNN` IDs.

All four are small-model semantic-discrimination limits requiring auditor-machinery rework. Cluster them in 0.3.2 (post-0.3.1).

**Already closed at 0.2.17 close or in 0.2.18:** F-0.2.17-W5-002 (plan-doc/repo-convention path drift, drafter chat-side process update), F-0.2.17-W6-002 (council embed timeout bumped 30→120 default during 0.2.18 substrate work — confirm during W0), F-0.2.17-W6-003 (working-state files gitignore + cached untrack, landed in 0.2.17 final bulk push).

### New surfaces from 0.3.0 pre-flight
- **pacman.conf `IgnorePkg = syncthing` pin** under `[options]` (not `[multilib]` or trailing comment section) on every aho host. Mechanical fix script `/tmp/fix-pacman-ignorepkg.fish` worked on x9cos this evening. **Closure: W2 — absorb as `bin/aho-pacman pin syncthing` or as a setup invariant check.**
- **Syncthing v1.30.0 mandate** as enforceable invariant — version drift to v2.x trips an `aho doctor` probe. **Closure: W2.**

---

## Workstream structure

Seven workstreams. Mix of NZXTcos-executed substrate work and p3cos-executed partial-tier deployment work. Daytime/overnight split per workstream complexity.

### W0 — Plan-doc + CLAUDE.md rewrite + ADR sketches + carry-forward fold-in inventory

**Locus:** NZXTcos
**Budget:** 2-4h daytime
**Drafter session:** Claude web (this session) authors plan-doc + ADR-0011 + ADR-0012 + CLAUDE.md rewrite as chat artifacts. Executor (claude-code on NZXTcos) places artifacts in `artifacts/iterations/0.3.1/` and writes acceptance archive.

**Deliverables:**
1. **Plan-doc** at `artifacts/iterations/0.3.1/aho-plan-0.3.1.md` (this document, after operator sign on draft)
2. **ADR-0011 (substrate freshness / decoherence telemetry, lightweight tier)** at `artifacts/adrs/0011-substrate-freshness.md` (new)
3. **ADR-0012 (Chain of Trust L5 placement)** at `artifacts/adrs/0012-chain-of-trust-l5.md` (new)
4. **CLAUDE.md rewrite** with eight deltas per 0.3.0 drafter brief §Required deltas: L5 reframing, multi-host §Deployment hosts, Identity discipline §, cross-lane contamination expansion, L5 hardening contract acknowledgment, hardware attestation tier orthogonality, secrets boundary trajectory, WARP-on-host caveat
5. **Carry-forward fold-in inventory** at `artifacts/iterations/0.3.1/carry-forward-fold-in.md` enumerating the eleven 0.2.18 + 0.2.17 entries with their target workstream + closure mechanism
6. **W0 self-audit** by `llama3.2:3b` (base-tier auditor on NZXTcos) with RAG + filter primitive from 0.2.18

**Acceptance gates:**
- Plan-doc sealed sha matches operator-signed reference
- ADR-0011 + ADR-0012 land at `artifacts/adrs/` per W5 D5-W5 path-resolution canonical convention
- CLAUDE.md rewrite addresses all eight deltas verbatim from drafter brief
- F-0.2.17-W6-002 (council embed timeout default) confirmed already-closed via codebase grep — if NOT closed, fold into W7 scope
- W0 self-audit disposition surfaced for drafter review

### W1 — Substrate freshness telemetry (F-0.2.18-W1-004 closure)

**Locus:** NZXTcos
**Budget:** 4-8h overnight
**Executor:** claude-code on NZXTcos

**Scope:** Implement the ADR-0011 lightweight tier. Per `aho-quantum.md` framing: emit `aho.observable.last_verified_age_seconds` for the ~10 substrate facts the iteration cycle bakes, surface on dashboard as numbers, no formal decoherence model in this iteration.

**Substrate facts in scope (drafter inventory; executor confirms during W0 audit pass):**
1. Tailnet domain (`tail8492.ts.net` — replaced `tail78a311.ts.net` after the F-0.2.18-W1-004 incident)
2. NZXTcos OTLP collector bind (`http://nzxtcos.tail8492.ts.net:4317`)
3. Image FQDN baked into install.fish or container env
4. SSH host keys per host (a8cos, p3cos, x9cos, NZXTcos)
5. Podman availability + version on each host
6. Broker socket presence (`$XDG_RUNTIME_DIR/aho-secrets.sock`) per host
7. ChromaDB collection mount path
8. Ollama API endpoint per host
9. 1Password agent socket (`~/.1password/agent.sock`) per host
10. CloudflareWARP DNS interception state (per the F-0.2.16-host-001 / 0.2.17 W0 hijack pattern)

**Deliverables:**
1. **`src/aho/observability.py`** (new) — `record_observable(fact_id, project, host)`, `last_verified_age_seconds(fact_id)`, append-only log at `~/.local/share/aho/observables.jsonl`
2. **OTEL gauge `aho.observable.last_verified_age_seconds`** with attrs `{fact_id, host, project}`
3. **`bin/aho-probe-substrate`** (new) — fish wrapper that probes the 10 facts, writes outcomes to observables.jsonl, runs on every iteration W0
4. **Dashboard surface** — claw3d brick rendering numeric `last_verified_age_seconds` per fact + summary count of facts older than τ-warning threshold (configurable per fact; default 7 days)
5. **install.fish integration** — `bin/aho-probe-substrate` runs at install step Pre-W0 and emits to observables.jsonl
6. **Unit tests** at `artifacts/tests/test_observability.py` — probe success, probe failure, age calculation, OTEL emit, dashboard render
7. **W1 self-audit** by base-tier auditor

**Acceptance gates:**
- All 10 substrate facts probable from a8cos (executor verifies cross-host via Tailscale ssh + reports per-fact age)
- F-0.2.18-W1-004 closure invariant: tailnet FQDN appears in observables.jsonl with `last_verified_age_seconds` < 1h after fresh probe; appears with `last_verified_age_seconds` > 600000 (~7 days) if probe stale
- Dashboard renders the per-fact ages numerically
- W1 self-audit produces 0 fake-ID-on-registered findings (filter from 0.2.18 still working)

### W2 — install.fish tier-aware refactor + 0.2.18 W2 carry-forward closures

**Locus:** NZXTcos (executor) + a8cos + x9cos + p3cos (cross-host validation)
**Budget:** 4-8h overnight
**Executor:** claude-code on NZXTcos; operator runs cross-host validation steps

**Scope:** Close five 0.2.18 W2 carry-forwards in install.fish. All five are install.fish surface area; coherent unit.

**Deliverables:**
1. **F-0.2.18-W2-002 closure:** `bin/aho-models` tier-aware refactor. Reads `~/.config/aho/tier.json`, branches on `tier ∈ {base, partial, full}`, pulls the appropriate model bundle per ADR-0007 thresholds.
2. **F-0.2.18-W2-003 closure:** `aho install tier-manifest` subcommand (or `bin/aho-install-tier-manifest`). Detects VRAM, writes `~/.config/aho/tier.json` with `{tier, vram_gb, detected_at}`.
3. **F-0.2.18-W2-004 closure:** `templates/systemd/aho-secrets-broker.service.template` (new). `bin/aho-systemd install` installs the broker as a per-user systemd unit.
4. **pacman.conf invariant:** `bin/aho-pacman pin syncthing` subcommand absorbed from the 0.3.0 fix script. Idempotent; verifies `IgnorePkg = syncthing` line is in `[options]` section (not `[multilib]` or trailing).
5. **Syncthing v1.30.0 doctor probe:** `aho doctor` flags any syncthing != v1.30.0 as a SCoT compliance regression.
6. **install.fish runs cleanly on a8cos + p3cos + x9cos** — executor SSHes to each, runs install.fish, reports per-host completion + tier.json contents + broker service active state.
7. **W2 self-audit** by base-tier auditor.

**Acceptance gates:**
- `tier.json` exists on all three hosts with correct tier classification (`base/base/partial` for a8cos/x9cos/p3cos)
- Broker service is `active (running)` on all three hosts
- Syncthing version probe passes on all three (v1.30.0)
- pacman.conf `IgnorePkg = syncthing` in `[options]` on all three
- F-0.2.18-W2-002/003/004 closed structurally in W2 acceptance archive

### W3 — p3cos partial-tier deployment + qwen3.5:9b auditor seat

**Locus:** **p3cos (executor session runs ON p3cos)**
**Budget:** 4-8h overnight; first cross-host workstream
**Executor:** claude-code launched on p3cos via `claude --dangerously-skip-permissions`

**Scope:** First partial-tier substrate deployment. Pull image, run install.fish on p3cos, load `qwen3.5:9b` + `nomic-embed-text` + GLM-4.6V-Flash-9B candidate, validate partial-tier audit primitive end-to-end.

**Pre-launch operator checklist (NOT executor scope):**
- p3cos has `gh auth status` confirmed (write:packages scope)
- p3cos has `podman login ghcr.io` bridged from gh CLI per W6 D1 ops gotcha
- Image transfer: drafter recommends **podman save | scp | podman load over tailnet** for p3cos given the in-fleet bandwidth, **gh-registry pull as canonical pattern for future engineer onboarding** — operator picks per session
- Image pulled: `ghcr.io/soc-foundry/aho:0.2.18` (NOT a 0.3.1 image yet — 0.3.1 doesn't rebuild the image until W6 if at all)

**Deliverables:**
1. **install.fish completes on p3cos** with `tier.json: {tier: partial, vram_gb: 16, ...}` and broker service active
2. **`qwen3.5:9b` loaded in ollama on p3cos** — `ollama list` shows the model, model responds to a trivial prompt within 30s
3. **`aho.council.audit` configured to use `qwen3.5:9b` at partial tier** — tier-aware dispatcher reads `tier.json`, routes audit calls to qwen3.5:9b on partial-tier hosts, llama3.2:3b on base-tier hosts. New code in `src/aho/council/dispatch.py` or wherever the audit routing lives.
4. **First partial-tier audit dispatched** — synthetic audit target (e.g., a copy of `acceptance/W2.json` from 0.3.1), qwen3.5:9b emits disposition + findings with the RAG enrichment + filter primitive working at partial tier
5. **Cross-host OTEL** — audit's OTEL spans reach NZXTcos collector tagged `host.name=p3cos`, `auditor.model=qwen3.5:9b`, visible in dashboard
6. **W3 self-audit** by **`qwen3.5:9b` at partial tier** — first dogfooded partial-tier audit on actual partial-tier-acceptance-archive material. Bootstrap test 8 in the architecture progression.

**Acceptance gates:**
- All five primary deliverables verified
- W3 self-audit produces disposition (any of clean/halt/surface_to_drafter); drafter reviews
- **Comparison data point:** drafter compares qwen3.5:9b disposition shape against llama3.2:3b's prior dispositions on similar artifacts. Forward-looking input to materiality data — does the larger model produce qualitatively different findings, lower false-positive rate, better RAG-context utilization?

**Halt conditions:**
- VRAM contention: qwen3.5:9b + nomic-embed-text + GLM-4.6V cold-load on 16GB Ada at the same time may need careful `OLLAMA_KEEP_ALIVE` tuning. If models thrash, halt-and-surface for drafter timeout-bump arbitration.
- OTEL endpoint unreachable from p3cos: tailnet probe + W1 substrate-freshness probe should pre-empt this; halt if traces don't appear at collector within 5min of dispatch.

### W4 — Cross-host Adversarial Authorship cycle on p3cos

**Locus:** p3cos
**Budget:** 4-8h overnight
**Executor:** claude-code on p3cos

**Scope:** Exercise the full Adversarial Authorship state machine for the first time end-to-end on p3cos. Substrate is the test fixture: deploy a fake test workstream (e.g., "W4-fixture: verify cross-host harness portability") with 3 deliverables, run the full plan→executor→audit→drafter-review→sign cycle, materiality counter advances.

**Deliverables:**
1. **W4-fixture plan-doc** (drafter authors in chat; executor places in `artifacts/iterations/0.3.1/fixtures/W4-fixture-plan.md`)
2. **W4-fixture execution** — three trivial deliverables (e.g., a probe script, a tiny config file, a smoke test) that exist purely to exercise the harness
3. **W4-fixture acceptance archive** — emitted on p3cos, OTLP'd to NZXTcos collector
4. **W4-fixture audit by qwen3.5:9b** — disposition emitted, drafter reviews
5. **Materiality counter advances** — N goes from 6 (post-0.2.18 W3, assumed) to 7
6. **Comparison narrative:** drafter notes any partial-tier-specific patterns in qwen3.5:9b dispositions vs base-tier llama3.2:3b
7. **W4 self-audit** by qwen3.5:9b

**Acceptance gates:**
- Full state machine completes end-to-end on p3cos
- Materiality counter increments correctly
- No regressions in audit primitive (filter still running, RAG enrichment populated, no fake-ID-on-registered false positives)

**Notes:** W4 is deliberately scope-thin. The point is to *exercise* the harness on partial-tier substrate, not to ship anything substantive. A successful W4 is a data point that the harness works on p3cos. A failed W4 is a load-bearing finding for whatever broke.

### W5 — Repo-resident docs reframing (Chain of Trust L5 framing + multi-host deployment hosts + identity discipline)

**Locus:** NZXTcos
**Budget:** 2-4h daytime
**Executor:** claude-code on NZXTcos

**Scope:** Convert chat-side Chain of Trust + multi-vault framing into repo-resident docs per 0.3.0 drafter brief §Required deltas. CLAUDE.md rewrite already landed in W0; W5 lands the *companion* repo-resident docs that CLAUDE.md cross-references.

**Deliverables:**
1. **`docs/architecture/chain-of-trust-l5-placement.md`** (new) — repo-resident version of the Chain of Trust framing as it applies to aho specifically. References `artifacts/tt-scot-overview-v3.md` as canonical Tachtech-level doc.
2. **`docs/operations/multi-host-deployment.md`** (new) — per-host setup runbook with a8cos / p3cos / x9cos as worked examples. Cross-references `install.fish` + `bin/aho-systemd` + `aho install tier-manifest`.
3. **`docs/operations/identity-discipline.md`** (new) — repo-resident version of multi-vault setup. Cross-references `artifacts/tt-multi-vault-setup-v2.md` as canonical Tachtech-level doc. aho-specific guidance: socfoundry lane for aho dev, executor pre-flight checks (`git config user.email` per session start).
4. **`docs/operations/warp-coexistence-caveats.md`** (new) — CloudflareWARP DNS interception recurrence pattern documented (F-0.2.16-host-001 / 0.2.17 W0 split-DNS pattern). Surface for any iteration touching cross-host DNS.
5. **0.3.1 retrospective so far** at `docs/retrospectives/0.3.1.md` — W0 through W4 narrative.
6. **W5 self-audit** by base-tier auditor on NZXTcos.

**Acceptance gates:**
- Four new docs exist at the canonical `docs/` paths
- Each cross-references appropriate Tachtech-level canonical artifacts
- Retrospective so far captures the materiality progression W0-W4
- W5 self-audit disposition surfaces; drafter reviews

### W6 — ADR consolidation + final 0.3.1 retrospective

**Locus:** NZXTcos
**Budget:** 2-4h daytime
**Executor:** claude-code on NZXTcos

**Scope:** Finalize ADR-0011 and ADR-0012 (W0 sketches refined post-W1-W5 evidence), amend ADR-0007 for tier-orthogonality (attestation axis sketch), amend ADR-0009 for XDG broker socket path canonicalization, complete retrospective.

**Deliverables:**
1. **ADR-0011 finalization** — incorporate W1 evidence (10 substrate facts implemented, dashboard surface live, F-0.2.18-W1-004 closure verified), document the lightweight-tier framing explicitly with mid-tier (0.4.x) and full-tier (0.5.x+) deferred as future scope per aho-quantum.md three-tier ambition table.
2. **ADR-0012 finalization** — incorporate Chain of Trust L5 placement with concrete cross-references to W5's new docs, attestation-axis sketch deferred as future scope (no SEV-SNP work in 0.3.1).
3. **ADR-0007 amendment** — add tier-orthogonality §: tier (base/partial/full per VRAM) is orthogonal to attestation (unattested/SEV-SNP-attested per hardware capability). Both axes are real; 0.3.1 ships partial-tier-unattested. Full-tier-attested deferred to 0.4.x+ per ADR-0012 §Trajectory.
4. **ADR-0009 amendment** — F-0.2.18-W2-005 closure: canonicalize the broker socket path to `$XDG_RUNTIME_DIR/aho-secrets.sock` (code default); deprecate the plan-doc legacy path `~/.local/share/aho/broker/broker.sock` from any remaining references.
5. **0.3.1 retrospective finalization** at `docs/retrospectives/0.3.1.md` — five sections (shipped, worked, didn't, surfaced, materiality) populated.
6. **W6 self-audit** by base-tier auditor.

**Acceptance gates:**
- All four ADR documents updated per scope above
- Retrospective five-section shape per ADR-0006 convention
- W6 self-audit disposition surfaces; drafter reviews

### W7 — Final code-change closures + iteration-final self-audit

**Locus:** NZXTcos
**Budget:** 2-4h daytime
**Executor:** claude-code on NZXTcos

**Scope:** Close residual 0.2.18 W2 carry-forwards that are code-change-shaped (broker socket path canonicalization in code, fish cache staleness at `doctor` path), run the iteration-final self-audit.

**Deliverables:**
1. **F-0.2.18-W2-005 code closure** — canonicalize the broker socket path in all code paths per ADR-0009 amendment from W6. Update any hardcoded `~/.local/share/aho/broker/broker.sock` references to `$XDG_RUNTIME_DIR/aho-secrets.sock`. Verify a fresh broker start on a8cos/p3cos/x9cos picks up the canonical path.
2. **F-0.2.18-W2-007 code closure** — patch `bin/aho-python` `doctor` path to invalidate fish's `command -q` cache across pip-install boundary. Same pattern as the `install` path patch from 0.2.18 W2.
3. **Final 0.3.1 self-audit** by base-tier auditor on NZXTcos against the W7 acceptance archive itself. Bootstrap test 9 in the architecture progression (sixth W-level self-audit since the auditor primitive stabilized at W4 of 0.2.17).
4. **0.3.1 iteration-close note** at `artifacts/iterations/0.3.1/iteration-close-0.3.1.md` — seven-workstream summary table + carry-forward state + materiality data + Chain of Trust L5 reframing acknowledgment + forward-looking 0.3.2 audit-machinery iteration sketch.

**Acceptance gates:**
- F-0.2.18-W2-005 + F-0.2.18-W2-007 closed structurally
- W7 self-audit disposition surfaces; drafter reviews
- Iteration-close note covers seven workstreams + 0.2.18+0.2.17 carry-forward fold-in disposition
- Materiality counter at N=7 (or higher) at iteration close

---

## Cross-cutting invariants (apply throughout 0.3.1)

1. **Pillar 11 binding:** zero git operations by drafter/executor/auditor. Operator commits. No agent reads secret material. The broker contract (ADR-0009) is the only sanctioned credential path.
2. **G001 (fish-pure on NZXTcos / a8cos / p3cos / x9cos):** no heredocs, no `printf` with `\n` escapes, no multi-line shell content with backslash escapes. Multi-line file appends use one separate `echo "line" >> file` statement per line OR write via Python.
3. **G081:** no celebratory framing in any artifact (plan-docs, close notes, ADRs, retrospective, evidence prose).
4. **G083:** anti-rubber-stamp hardening unchanged from 0.2.18 (`_GIT_OP_ENFORCEMENT_SENTINELS`, `_RAG_STATUS_ECHO_PATTERN`, `unsupported_halt_downgrade`, the W4-0.2.17 deterministic post-hoc filter).
5. **Cross-lane contamination vigilance:** `~/Development/Projects/socfoundry/` for aho work only. No customer-namespaced material in aho artifacts; no aho material in customer-namespaced repos. Verified via `git config user.email = *@socfoundry.com` per executor session.
6. **Audit-machinery residuals deferred:** F-0.2.18-W0-008, F-0.2.18-W2-009, F-0.2.17-W5-001, F-0.2.17-W6-001 all surface during 0.3.1 audits. Operator-arbitrate when they surface (per F-0.2.17-W2-004 precedent). Do not block 0.3.1 closure on them. 0.3.2 candidate iteration target.

## Halt-and-surface conditions (cross-iteration)

Per-workstream conditions documented above. Cross-iteration halt conditions:

- Substrate-freshness probe failure (W1 dashboard) on any of the 10 facts during any subsequent workstream → halt-and-surface for drafter+operator; the iteration's own substrate may have decohered mid-flight.
- Cross-host OTEL not reaching NZXTcos collector from p3cos during W3/W4 → halt-and-surface; the partial-tier deployment claim depends on the collector path.
- Pillar 11 incident (any agent attempting git operation or secret read) → immediate halt, drafter+operator arbitration before resume. Same severity as F-0.2.17-W1-003 Pillar 11 incident.

## Materiality data expected

- Entry N=7 at 0.3.1 close (assuming 0.2.18 W3 advances to N=6 before 0.3.1 W4 advances to N=7).
- First partial-tier auditor disposition data point (qwen3.5:9b vs llama3.2:3b on comparable artifacts).
- First cross-host workstream execution data point.
- Substrate freshness telemetry: first-ever per-fact age measurements, baseline for future iteration trend analysis.

Threshold for full materiality validation (per ADR-0010) remains N≥8. 0.3.1 advances toward but does not cross this threshold. Forward-looking note: 0.3.2 audit-machinery iteration likely crosses N=8 if scoped to advance the counter (vs purely auditor-machinery rework that may not run a full Adversarial Authorship cycle).

---

## Forward-looking notes for 0.3.2

The dedicated audit-machinery iteration that closes the four deferred carry-forwards (F-0.2.18-W0-008, F-0.2.18-W2-009, F-0.2.17-W5-001, F-0.2.17-W6-001). All four are small-model semantic-discrimination limits requiring structural fixes:

- **F-0.2.17-W6-001** → ID-keyed metadata field at ChromaDB index time (avoid cosine entirely for opaque alphanumeric IDs)
- **F-0.2.17-W5-001** → JSON path exclusion in structural pre-check scan (skip fields tagged as compliance-evidence prose)
- **F-0.2.18-W0-008** → narrative-lift suppression (tag each finding with last_active_at; auditor reads coherence-weighted reference set per aho-quantum mid-tier §3)
- **F-0.2.18-W2-009** → verbatim-substring suppression filter for prompt-instruction echo

0.3.2 is the natural home because all four share the auditor-prompt-construction + RAG-retrieval surface. Bundling them avoids three separate ADR amendments to the same primitive.

The aho-quantum mid-tier (`aho posture` subcommand + dashboard wave-packet visualization) is a 0.3.2 or 0.4.x candidate depending on how 0.3.2 audit-machinery work scopes. Mid-tier needs the substrate-freshness primitive from 0.3.1 W1 as foundation.

The aho-quantum full-tier (coherence-driven iteration close with per-fact freshness ages-out before close-package writes; acceptance archives carry per-fact coherence metadata; audits read coherence-weighted reference sets) is charter-level rework deferred to 0.4.x+ with SEV-SNP attestation as a parallel axis per ADR-0007 amendment.

---

## Cross-references

- `artifacts/iterations/0.2.18/aho-plan-0.2.18.md` — predecessor iteration plan
- `artifacts/iterations/0.2.17/iteration-close-0.2.17.md` — substrate state at iteration handoff (pre-0.3.0-preflight)
- `artifacts/iterations/0.3.0/0.3.0-drafter-context.md` — pre-flight + SCoT remediation findings, host fleet inventory
- `artifacts/tt-scot-overview-v3.md` — Tachtech Chain of Trust canonical
- `artifacts/tt-multi-vault-setup-v2.md` — Multi-vault identity discipline canonical
- `artifacts/aho-quantum.md` — substrate-freshness three-tier ambition framing (chat-side input doc)
- `artifacts/aho-quantum-web.md` — companion web framing
- `artifacts/council-models-0.2.14.md` — model identity + structured-output reference (current-applicable)
- `artifacts/adrs/0006-iteration-deliverable-discipline.md` — binds plan-doc shape
- `artifacts/adrs/0007-containerization-architecture.md` — VRAM tier thresholds
- `artifacts/adrs/0009-secrets-broker-boundary.md` — secrets posture (current)
- `artifacts/adrs/0010-materiality-measurement.md` — N≥8 falsifiability threshold
- `artifacts/harness/base.md` §The Eleven Pillars — operating contract
