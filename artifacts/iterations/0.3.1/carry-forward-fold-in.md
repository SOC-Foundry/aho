# Carry-Forward Fold-In Inventory — 0.3.1

**Iteration:** 0.3.1
**Authored:** W0 (2026-05-23)
**Author:** executor (claude-code on a8cos) per W0 D6 deliverable
**Cross-reference:** `aho-plan-0.3.1.md` §Pre-iteration carry-forward inventory

This artifact enumerates every carry-forward entry inherited at 0.3.1 launch with its 0.3.1 disposition: closing-in-scope, deferred-to-0.3.2-audit-machinery, deferred-to-0.4.x+-charter, or closed-pre-0.3.1. Severity labels are best-effort drafter-derived per source plan-doc / acceptance-archive framing; subject to drafter arbitration on review.

Per-entry shape: `id | severity | source | target | closure mechanism`

---

## Closing in 0.3.1 scope

| ID | Severity | Source | Target | Closure mechanism |
|---|---|---|---|---|
| F-0.2.18-W1-004 | load-bearing | 0.2.18 W1 (image pre-flight; stale tailnet FQDN baked into image surface after tailnet rolled) | W1 | Substrate freshness telemetry — ADR-0011 lightweight tier: 10 facts emit `aho.observable.last_verified_age_seconds` OTEL gauge; dashboard renders per-fact ages + summary count of stale facts |
| F-0.2.18-W2-002 | important | 0.2.18 W2 (`bin/aho-models` Tier-1-only; base-tier hosts hit capability gap) | W2 | `bin/aho-models` tier-aware refactor — reads `~/.config/aho/tier.json`, branches on `tier ∈ {base, partial, full}`, pulls bundle per ADR-0007 thresholds |
| F-0.2.18-W2-003 | important | 0.2.18 W2 (`install.fish` writes no `~/.config/aho/tier.json`) | W2 | `aho install tier-manifest` subcommand — detects VRAM, writes tier.json with `{tier, vram_gb, detected_at}` |
| F-0.2.18-W2-004 | important | 0.2.18 W2 (no broker systemd template; ADR-0009 broker-per-host mandate not realized in install.fish) | W2 | `templates/systemd/aho-secrets-broker.service.template` + `bin/aho-systemd install` installs per-user systemd unit |
| F-0.2.18-W2-005 | cosmetic | 0.2.18 W2 (broker socket path divergence: plan-doc `~/.local/share/aho/broker/broker.sock` vs code default `$XDG_RUNTIME_DIR/aho-secrets.sock`) | W7 (code) + W6 (ADR amendment) | ADR-0009 amendment canonicalizing XDG path + code closure updating any hardcoded `~/.local/share/aho/broker/broker.sock` references |
| F-0.2.18-W2-007 | important | 0.2.18 W2 (`bin/aho-python` fish-cache staleness at `doctor` path; already patched at `install` path) | W7 | Same patch pattern as `install` path — invalidate fish's `command -q` cache across pip-install boundary at `doctor` path |
| pacman.conf `IgnorePkg = syncthing` pin | operational (substrate hygiene) | 0.3.0 pre-flight + SCoT remediation on a8cos | W2 | `bin/aho-pacman pin syncthing` subcommand absorbed from `/tmp/fix-pacman-ignorepkg.fish` — idempotent; verifies `IgnorePkg = syncthing` in `[options]` section (not `[multilib]` or trailing comment) |
| syncthing v1.30.0 mandate | operational (substrate hygiene) | 0.3.0 pre-flight; SCoT mandate | W2 | `aho doctor` flags any syncthing != v1.30.0 as SCoT compliance regression |

## Deferring to 0.3.2 audit-machinery iteration

All four are small-model semantic-discrimination limits requiring auditor-machinery rework. Cluster avoids three-plus separate ADR amendments to the same primitive.

| ID | Severity | Source | Target | Closure mechanism (forward-looking) |
|---|---|---|---|---|
| F-0.2.18-W0-008 | important | 0.2.18 W0 audit (narrative-lift: small-model lifts prior-cycle commentary as findings) | 0.3.2 | Narrative-lift suppression — tag each finding with `last_active_at`; auditor reads coherence-weighted reference set per aho-quantum mid-tier §3 |
| F-0.2.18-W2-009 | important | 0.2.18 W2 audit (prompt-instruction echo: model echoes auditor-prompt text as finding) | 0.3.2 | Verbatim-substring suppression filter for prompt-instruction echo |
| F-0.2.17-W5-001 | important | 0.2.17 W5 audit (structural pre-check self-referential pattern) | 0.3.2 | JSON path exclusion in structural pre-check scan — skip fields tagged as compliance-evidence prose |
| F-0.2.17-W6-001 | important | 0.2.17 W6 audit (RAG lookup ranking on opaque `F-X.Y.Z-WN-NNN` IDs via cosine) | 0.3.2 | ID-keyed metadata field at ChromaDB index time — avoid cosine entirely for opaque alphanumeric IDs |

## Deferring to 0.4.x+ charter-level work

These items require hardware procurement (SEV-SNP-capable silicon), substrate substitution (1Password Connect), or structural rework (aho-quantum mid/full tier framing applied at iteration-close primitive). All deferred from 0.3.1 documentary scope but acknowledged as forward-looking carry-forwards per CLAUDE.md §L5 container hardening contract + §Secrets boundary trajectory.

| Item | Severity | Source | Target | Closure mechanism (forward-looking) |
|---|---|---|---|---|
| L5 hardening invariants: read-only root FS | structural | ADR-0012 / `artifacts/tt-scot-overview-v3.md` §Workload Isolation | 0.4.x+ | Container image runs with `--read-only` flag; writable scratch via explicit tmpfs mounts |
| L5 hardening invariants: full capability drop | structural | same | 0.4.x+ | `cap_drop: [ALL]` with explicit `cap_add` per service need |
| L5 hardening invariants: SHA256 digest pinning | structural | same | 0.4.x+ | All image references in manifests use `@sha256:<digest>` not mutable tags |
| L5 hardening invariants: Kyverno admission controllers | structural | same | 0.4.x+ (full-tier cloud) | Reject unsigned or non-digest-pinned images at pod admission (requires Kubernetes) |
| L5 hardening invariants: Tailscale0 binding | structural | same | 0.4.x+ | Containers bind exclusively to `tailscale0` interface to prevent host network leaks |
| AMD SEV-SNP attestation chain | structural (hardware-dependent) | ADR-0012 §Trajectory | 0.4.x+ | Hardware attestation chain replacing unix-socket bridge; requires SEV-SNP-capable silicon (not in current fleet) |
| 1Password Connect substrate substitution | structural | ADR-0012 §Trajectory | 0.4.x+ | 1Password Connect releases decryption secrets only after attestation service validates workload's measured state |
| aho-quantum mid-tier (`aho posture` subcommand + dashboard wave-packet visualization) | structural | `artifacts/aho-quantum.md` §three-tier ambition | 0.4.x (or 0.3.2 if audit-machinery scope permits) | Formula in `aho.observability`; `aho posture` reads `~/.local/share/aho/observables.jsonl` and prints `<H>±σ` |
| aho-quantum full-tier (coherence-driven iteration close) | structural | same | 0.4.x+ | Per-fact freshness ages-out before close-package writes; acceptance archives carry per-fact coherence metadata; audits read coherence-weighted reference sets |

## Closed pre-0.3.1 (recorded for completeness)

| ID | Severity | Source | Closed In | Evidence |
|---|---|---|---|---|
| F-0.2.17-W5-002 | cosmetic (process) | 0.2.17 W5 audit (plan-doc-vs-repo-convention path drift: docs/adr vs artifacts/adrs) | 0.2.17 close (drafter chat-side process update) | Plan-doc preserves `artifacts/adrs/` as canonical convention; W0 D3/D4 ADR placement at `artifacts/adrs/` confirms |
| F-0.2.17-W6-002 | important | 0.2.17 W6 audit (council embed timeout 30s too tight under cold-start + concurrent embed load on NZXTcos 8GB VRAM) | 0.2.18 W0 (default 30→120 raise) | D7 grep confirmation: `src/aho/council/embed.py:38` `DEFAULT_TIMEOUT_S = 120`; docstring lines 12-14 explicit F-0.2.17-W6-002 attribution |
| F-0.2.17-W6-003 | cosmetic | 0.2.17 W6 (working-state files not gitignored) | 0.2.17 final bulk push (gitignore + cached untrack) | Per plan-doc §Pre-iteration carry-forward inventory |

---

## Summary

- **Closing in 0.3.1 scope:** 8 entries (6 F-IDs from 0.2.18 W1/W2; 2 SCoT/substrate-hygiene from 0.3.0 pre-flight)
- **Deferring to 0.3.2 audit-machinery:** 4 entries (F-0.2.18-W0-008, F-0.2.18-W2-009, F-0.2.17-W5-001, F-0.2.17-W6-001)
- **Deferring to 0.4.x+ charter:** 9 items (5 L5 hardening invariants + SEV-SNP + 1Password Connect + aho-quantum mid + full)
- **Closed pre-0.3.1 (recorded):** 3 entries (F-0.2.17-W5-002, F-0.2.17-W6-002, F-0.2.17-W6-003)

**Total inventoried:** 24 entries across closing / deferring / closed categories.

---

## Notes on severity-label provenance

Severity labels in this inventory are best-effort drafter-derived from source plan-doc framing and acceptance-archive context. Where source artifacts label severity explicitly (e.g., 0.2.16 carry-forwards file uses "cosmetic / important / load-bearing"), labels are quoted verbatim. Where 0.2.18 plan-doc framing names a closure mechanism without an explicit severity tag, this artifact assigns the lowest severity consistent with the closure-target scope (e.g., F-0.2.18-W2-005 socket-path divergence is `cosmetic` because the code works under either path, only inconsistency surfaces; F-0.2.18-W1-004 is `load-bearing` because it triggered an unscheduled image rebuild).

Drafter arbitration welcome on any severity assignment that mis-frames the entry's actual blast radius.
