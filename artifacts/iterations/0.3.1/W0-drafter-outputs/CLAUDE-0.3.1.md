# CLAUDE.md — aho 0.3.1

**Version:** 0.3.1
**Last rewritten:** 2026-05-23 (0.3.1 W0)
**Cross-references:** `aho-plan-0.3.1.md`, `artifacts/tt-scot-overview-v3.md`, `artifacts/tt-multi-vault-setup-v2.md`

---

## What aho is

aho (Agentic Harness Orchestration) is the **L5 Workload layer of the Tachtech Chain of Trust** (see `artifacts/tt-scot-overview-v3.md`), defending against host-root memory access and tampered runtimes via container substrate + secrets broker boundary + Adversarial Authorship audit trail. Customer engagements rely on aho to attest that LLM-driven engineering work is provably honest and end-to-end auditable.

Current state: unattested unix-socket fernet broker substrate (ADR-0009) with in-container auditor (ADR-0007 tier framework). Trajectory: AMD SEV-SNP hardware attestation with 1Password Connect-gated secret release (ADR-0012 §Trajectory). aho is not yet attested; 0.3.1 ships the partial-tier substrate that future attestation work will build on.

Internally, aho is also the engineering discipline that produces Tachtech's customer deliverables: Adversarial Authorship pairs drafter (Claude web), executor (Claude Code or Gemini CLI), auditor (in-container llama3.2:3b at base tier; **qwen3.5:9b at partial tier in 0.3.1+**), and operator (Kyle) in a state machine that produces sealed acceptance + audit archives per iteration.

## Deployment hosts

Three production-ready hosts in the aho fleet as of 0.3.1:

| Host | Chassis | Tier | OS | Tailnet IP | LAN segment | Role |
|---|---|---|---|---|---|---|
| **a8cos** | GEEKOM A8 MAX (AMD Ryzen 9 8945HS, Radeon 780M iGPU, no discrete GPU) | base | CachyOS 7.0.9-1 | 100.124.234.113 | 172.31.255.128/26 (KT Lab) | L3 universal subnet router; primary workstation |
| **p3cos** | Lenovo ThinkStation P3 Ultra SFF G2 (Intel Core Ultra 9 285, RTX 2000 Ada 16GB) | **partial** | CachyOS 7.0.8-1 | 100.84.122.100 | 172.31.255.134/26 | **Partial-tier substrate; qwen3.5:9b auditor seat** |
| **x9cos** | Lenovo ThinkPad X9-14 Gen 1 (Intel Core Ultra 7 268V, Arc 130V/140V iGPU) | base | CachyOS 7.0.9-1 | 100.89.115.76 | 172.31.255.178/26 (USB Ethernet) + 172.31.255.226/26 (wifi, Eng4 Lab range) | Mobile workstation; intermittently online |

NZXTcos remains the OTLP collector + ChromaDB substrate host but is no longer the only execution surface. 0.3.1 W3+ runs claude-code executor sessions on p3cos directly.

Per-host substrate facts:
- All four CachyOS x86_64 (NZXTcos, a8cos, p3cos, x9cos)
- All fish shell default; G001 absolute (no heredocs, no `printf '\n...\n...\n' >> file`; multi-line file appends use one separate `echo "line" >> file` per line)
- All on tailnet `tail8492.ts.net` (replaced `tail78a311.ts.net` after the F-0.2.18-W1-004 rebuild)
- All enrolled in CloudflareWARP under the tachtech tenant — **WARP intercepts DNS and is the recurrence surface for the F-0.2.16-host-001 / 0.2.17 W0 Tailscale-split-DNS-hijack pattern**; any iteration touching cross-host DNS must probe WARP's MagicDNS exclusions
- All have 1Password agent at `~/.1password/agent.sock` (a8cos, x9cos verified; p3cos to confirm during W3 onboarding)
- All on the `projects` syncthing share at `~/Development/Projects` (sendreceive, fsWatcher 10s debounce, v1.30.0 mandated per SCoT — version drift to v2.x trips an `aho doctor` probe in 0.3.1 W2)

## Identity discipline

aho lives in `~/Development/Projects/socfoundry/` per the multi-tenant workspace layout documented in `artifacts/tt-multi-vault-setup-v2.md`. **Every executor session must verify lane via `git config user.email` at startup.** Lane verification:

- aho work: `*@socfoundry.com` only (sovereign domain lane)
- Rosenthal/Tachtech corporate work: `*@tachtech.net` (corporate lane)
- Customer engagement work (Cintas, Mercor, etc.): `*@tachtech.net` with customer-namespaced SSH alias (`github.com-customers`)

`~/.gitconfig` is a routing engine — blank `[user]` block + `includeIf` blocks per lane. Repos outside a lane fail closed at commit time. 1Password `agent.toml` scopes presented SSH keys per lane. Inside `socfoundry/`, `ssh-add -l` shows exactly two keys (one corporate anchor for cross-org GitHub if needed, one socfoundry-specific). No customer or foreign-node keys leak into aho work.

**Cross-lane contamination vigilance is binding throughout 0.3.1.** Historically the discipline was kjtcom-vs-aho (project-level). It now expands to **corporate-vs-sovereign-vs-customer at the lane level**, with higher stakes (customer data exposure if cross-lane references leak into customer-namespaced artifacts).

## Adversarial Authorship roles (restored to 0.2.17 split in 0.3.1)

- **Drafter:** claude-web (this session, persistent across the iteration via the project folder). Authors plan-docs, ADRs, CLAUDE.md, retrospective. Reviews audit dispositions pre-sign. Arbitrates auditor false positives against ground-truth artifacts.
- **Executor:** claude-code on NZXTcos for substrate work; **claude-code on p3cos for partial-tier deployment workstreams** (W3/W4 of 0.3.1). Gemini CLI available as alternative executor for audit slots. Executor never commits; operator does.
- **Auditor:** `llama3.2:3b` in-container at base tier (NZXTcos, a8cos, x9cos); **`qwen3.5:9b` in-container at partial tier (p3cos)**. Audit primitive: RAG enrichment (W3 of 0.2.17) + deterministic post-hoc filter on findings (W4 of 0.2.17) + anti-rubber-stamp extensions (0.2.18 W0). Disposition shape `clean | halt | surface_to_drafter` with confidence floor 0.85 structurally enforced.
- **Operator:** Kyle. Sign-off on close notes. **All git operations.** All secret reads. All hardware-side actions (image transfers, host reboots, hardware procurement).

0.2.18 collapsed drafter+executor to claude-code per operator-explicit deviation. 0.3.1 restores the split to extract a clean comparison data point on the deviation's protocol-level cost.

## Pillar 11 (absolute, binding)

Zero git operations by drafter, executor, or auditor. Ever. The Adversarial Authorship contract is: **agents propose; the operator commits.** This includes:

- No `git add`, `git commit`, `git push`, `git merge`, `git rebase`, `git tag` by any agent
- No `gh pr create`, `gh pr merge`, or other GitHub CLI operations that modify repo state
- No agent reads secret material from disk, ssh-agent, 1Password, fernet store, or any other credential surface — the broker contract (ADR-0009) is the only sanctioned credential path, and even there the agent receives hash-fingerprints, not raw values (per W6 D1 of 0.2.17, `aho secrets-test` returns SHA-256 first-8-hex + length, never the decrypted value)
- No agent triggers hardware-side actions (reboots, GPU passthrough config changes, systemd unit installs at root)

Pillar 11 violations are halt-and-surface conditions with the same severity as F-0.2.17-W1-003 (the canonical incident: drafter-side design specification of value-printing in `aho secrets-test` violated the boundary; executor surfaced voluntarily). Operator + drafter arbitrate before resume.

## L5 container hardening contract (acknowledged carry-forward, not 0.3.1 deliverable)

Tachtech-tenant deployment requires these L5 invariants per `artifacts/tt-scot-overview-v3.md` §Workload Isolation. 0.3.1 does NOT yet enforce these structurally; they're documented as forward-looking carry-forwards:

- [ ] **Read-only root filesystem** — image runs with `--read-only` flag; writable scratch via explicit tmpfs mounts. Currently aho image runs writable; enforcement deferred.
- [ ] **Full capability drop** — `cap_drop: [ALL]` with explicit `cap_add` per service need. Currently aho image runs with default caps; enforcement deferred.
- [ ] **SHA256 digest pinning** — all image references in manifests use `@sha256:<digest>` not mutable tags. Currently mixed; canonical enforcement deferred to Kyverno (full-tier cloud).
- [ ] **Kyverno admission controllers** — reject unsigned or non-digest-pinned images at pod admission. Requires Kubernetes; full-tier cloud deployment scope.
- [ ] **Tailscale0 binding** — containers bind exclusively to `tailscale0` interface to prevent host network leaks. Currently aho image runs with host networking in some paths; review pending.

Each of these is a 0.4.x+ candidate. Documented here so they don't get forgotten when SEV-SNP work begins.

## Secrets boundary trajectory (ADR-0009 + ADR-0012)

**Current state (0.3.1):** unix-socket fernet broker at `$XDG_RUNTIME_DIR/aho-secrets.sock` (canonical path per ADR-0009 amendment landing in 0.3.1 W6; F-0.2.18-W2-005 closure). SO_PEERCRED authenticates the connecting peer's UID. Per-project label scoping. Container fetches via `aho.secrets_client`; no plaintext keys in image layers; no SSH agent socket forwarded into containers.

**Trajectory:**
1. **0.3.1 (now):** broker is per-user systemd unit on every aho host (F-0.2.18-W2-004 closure in W2). Three rules from ADR-0009 verbatim: no credential material in image layers, per-user secret access via host-side broker, no SSH agent socket forwarded.
2. **0.3.2 candidate:** L5 hardening probes in `aho doctor` (warn on missing read-only root, cap_drop, SHA256 pinning).
3. **0.4.x+ candidate:** AMD SEV-SNP attestation chain replacing the unix-socket bridge. 1Password Connect releases decryption secrets only after the attestation service validates the workload's measured state. Hardware procurement is a prerequisite (no SEV-SNP-capable silicon in current fleet).

## Substrate freshness (ADR-0011, new in 0.3.1)

The F-0.2.18-W1-004 incident (stale tailnet FQDN baked into image) motivates **substrate-fact freshness as first-class telemetry**. 0.3.1 W1 ships the lightweight tier: 10 substrate facts emit `aho.observable.last_verified_age_seconds` OTEL gauge with per-fact `warning_age_seconds` thresholds. Dashboard surfaces numeric ages + summary count of stale facts.

Lightweight tier does NOT yet ship the formal decoherence model from `aho-quantum.md` (mid-tier 0.3.2+) or coherence-driven iteration close (full-tier 0.4.x+). It does close F-0.2.18-W1-004 with bounded scope: any stale fact older than its threshold surfaces visibly on the dashboard, operator-driven response.

The 10 facts in 0.3.1 W1 scope: tailnet domain, NZXTcos OTLP collector bind, image FQDN, per-host SSH host keys, per-host podman availability + version, per-host broker socket presence, ChromaDB collection mount, per-host Ollama API endpoint, per-host 1Password agent socket, per-host CloudflareWARP DNS state.

## Tier orthogonality (ADR-0007 amendment in 0.3.1 W6)

Two independent axes describe aho deployment readiness:

1. **VRAM tier** (ADR-0007): `base` (<12GB VRAM), `partial` (12-32GB), `full` (≥32GB or multi-GPU). Determines auditor model and substantive-work model bundle. 0.3.1 ships `base` (a8cos, x9cos, NZXTcos) + `partial` (p3cos).

2. **Attestation tier** (ADR-0012): `unattested` (current substrate; no hardware attestation), `SEV-SNP-attested` (long-arc end state per ADR-0012 trajectory). 0.3.1 ships `unattested` across all hosts.

Naming the orthogonality prevents conflation: a base-tier-attested deployment is feasible (small VRAM but with SEV-SNP); a full-tier-unattested deployment is feasible (large VRAM but no attestation). 0.3.1 ships partial-tier-unattested on p3cos. Future iterations may move along either axis independently.

## Auditor seat per host

- **NZXTcos** (base): `llama3.2:3b` with RAG + filter + W0-0.2.18 anti-rubber-stamp extensions
- **a8cos** (base): `llama3.2:3b` (same primitive)
- **x9cos** (base): `llama3.2:3b` (same primitive, intermittent online)
- **p3cos** (partial): **`qwen3.5:9b`** with RAG + filter (anti-rubber-stamp extensions inherited; per-model calibration may surface during W3-W4 dogfooding)

`aho.council.dispatch` reads `~/.config/aho/tier.json` (0.3.1 W2 deliverable per F-0.2.18-W2-003 closure) and routes audit calls accordingly. Cross-host audit dispatch is operator-orchestrated (executor on p3cos dispatches against local qwen3.5:9b; cross-host dispatch via Tailscale Ollama API is partial-tier-to-partial-tier work, 0.3.2+ candidate).

## Iteration discipline (ADR-0006 binding)

Per-iteration shape:
- **Plan-doc** at `artifacts/iterations/<version>/aho-plan-<version>.md` — drafter authors as chat artifact, executor places, operator signs
- **Per-workstream:** plan-doc deliverable paragraph, graduation criterion, acceptance gates, halt-and-surface conditions
- **Acceptance archive** at `acceptance/W<N>.json` — sealed at workstream completion, `audit_status: pending_drafter_review` post-W-self-audit
- **Audit archive** at `audit/W<N>.json` — sealed at audit emit, never modified post-emit (drafter arbitration lands in acceptance archive's `drafter_review_note` field)
- **Close note** at `artifacts/iterations/<version>/W<N>-close-note.md` — operator-signed; references sealed shas
- **workstream_complete event** to `~/.local/share/aho/events/aho_event_log.jsonl` — direct python emit per F-0.2.17-W0-004 CLI argparse workaround (carry-forward to 0.3.x)
- **Iteration-close note** at `artifacts/iterations/<version>/iteration-close-<version>.md` — crowns the workstream chain; not a state-machine event itself

## Carry-forwards binding from prior iterations

**Open in 0.3.1 scope (closing):**
- F-0.2.18-W1-004 → W1 substrate freshness
- F-0.2.18-W2-002/003/004 → W2 install.fish tier-aware refactor
- F-0.2.18-W2-005/007 → W7 code-change closures
- pacman.conf IgnorePkg pin + syncthing v1.30.0 doctor probe → W2

**Open and deferred to 0.3.2 audit-machinery iteration:**
- F-0.2.18-W0-008 (narrative-lift)
- F-0.2.18-W2-009 (prompt-instruction echo)
- F-0.2.17-W5-001 (audit structural pre-check self-referential)
- F-0.2.17-W6-001 (audit-time RAG lookup ranking on opaque IDs)

**Open and deferred to 0.4.x+ charter-level work:**
- L5 hardening invariants (read-only root, cap_drop, SHA256 pinning, Kyverno)
- AMD SEV-SNP attestation chain
- 1Password Connect substrate substitution
- aho-quantum mid-tier (`aho posture` subcommand) and full-tier (coherence-driven iteration close)

## Gotcha registry (binding throughout)

- **G001 (absolute):** Fish shell on NZXTcos / a8cos / p3cos / x9cos. NEVER use `printf` with `\n` escapes for multi-line content. NEVER use heredocs. NEVER use multi-line shell content with backslash escapes. Multi-line file appends use one `echo "line" >> file` per line OR write via Python.
- **G022:** Use `command ls` not `ls` in fish (alias-free).
- **G045:** Query editor cursor (kjtcom-side, not aho but cross-referenced) — replace `TextField` with `flutter_code_editor`. Not aho scope.
- **G059:** Canvas texture approach for chip labels (kjtcom-side). Not aho scope.
- **G073:** The Eleven Pillars of aho must be quoted verbatim from `artifacts/harness/base.md` — never paraphrased.
- **G081:** Celebratory framing banned in all aho artifacts. No "clean close," "landed beautifully," "all green," "shipped" in plan-docs, close notes, ADRs, retrospective, or evidence prose.
- **G083:** Anti-rubber-stamp hardening. No `categories[-1]` fallback in audit primitives. No silent rubber-stamp. Confidence floor 0.85 locked. Deterministic post-hoc filter on RAG-aware findings (only suppresses `registered anchor + fake-ID phrase` combinations; never silently drops on uncertainty).

## What to do at the start of each session

1. Verify lane: `git config user.email` → expect `*@socfoundry.com` for aho work
2. Verify ssh-add scope: `ssh-add -l` → expect exactly the lane-appropriate keys (no customer keys, no cross-org keys)
3. Verify host: `hostname` → expect one of NZXTcos / a8cos / p3cos / x9cos
4. Verify tier: `cat ~/.config/aho/tier.json` (0.3.1 W2+ only) → expect tier matching the host
5. Verify broker: `systemctl --user status aho-secrets-broker.service` → expect `active (running)` (0.3.1 W2+ only)
6. Verify substrate freshness: `bin/aho-probe-substrate --summary` → expect zero facts older than warning threshold (0.3.1 W1+ only)
7. Read the relevant iteration plan-doc end-to-end before writing any code, ADR, or close note

## Cross-references

- `aho-plan-0.3.1.md` — current iteration plan
- `artifacts/tt-scot-overview-v3.md` — Tachtech Chain of Trust canonical
- `artifacts/tt-multi-vault-setup-v2.md` — Identity discipline canonical
- `artifacts/aho-quantum.md` — substrate freshness three-tier ambition (input doc, not authoritative)
- `artifacts/council-models-0.2.14.md` — model identity + structured output (still applicable; per-model facts substantively current)
- `artifacts/adrs/0006-iteration-deliverable-discipline.md` — plan-doc shape
- `artifacts/adrs/0007-containerization-architecture.md` — VRAM tier framework (tier-orthogonality amendment in 0.3.1 W6)
- `artifacts/adrs/0009-secrets-broker-boundary.md` — secrets posture (canonicalization amendment in 0.3.1 W6)
- `artifacts/adrs/0010-materiality-measurement.md` — materiality counter (N≥8 falsifiability)
- `artifacts/adrs/0011-substrate-freshness.md` — substrate freshness (new in 0.3.1)
- `artifacts/adrs/0012-chain-of-trust-l5.md` — Chain of Trust L5 placement (new in 0.3.1)
- `artifacts/harness/base.md` §The Eleven Pillars — operating contract
