# ADR-0012: Chain of Trust L5 placement

**Status:** Proposed (W0 of 0.3.1)
**Date:** 2026-05-23
**Deciders:** drafter (claude-web), operator
**Supersedes:** none
**Superseded by:** none

## Context

aho was framed throughout 0.2.x as governance infrastructure for LLM-driven engineering iterations: an Adversarial Authorship harness that produces auditable outputs with adversarial verification, deterministic post-hoc filtering, and Pillar 11 boundary-enforcement. That framing is correct but incomplete relative to where aho now sits.

The deployment-tenant Chain of Trust framework (canonical at the tenant's organizational documentation; cross-referenced via the deployment-private overview doc) names aho as an enterprise-level security control:

> **L5 — Workload — AHO + AMD SEV-SNP — Threat Defeated: Host-Root Memory Access & Tampered Runtimes**

The framework operates on three commitments: customer data is strictly the customer's own, every line of code the deployment-tenant delivers is provably honest, and the path between the two is auditable end-to-end. The "Chain of Trust" architecture decouples trust from any single vendor or credential by enforcing every link with a different vendor, evaluating against independent signals, and logging to unique audit streams.

Within this framework, aho's role is concrete and named: workload isolation defending against host-root memory access and tampered runtimes. aho is no longer (only) an internal engineering productivity tool. It is a customer-facing security capability whose container substrate, secrets broker, and Adversarial Authorship audit trail are part of the deployment-tenant's regulated-industry contract-winning capability.

This reframing is not an architectural change. The container substrate (ADR-0007), secrets broker boundary (ADR-0009), and materiality measurement protocol (ADR-0010) already operate as L5 controls. What changes is **explicit acknowledgment in the project's architectural documentation that aho sits at L5 of the Chain of Trust, with concrete trajectory toward AMD SEV-SNP attestation integration as the long-arc end state**.

## Decision

**aho 0.3.1 adopts the Chain of Trust L5 placement as a named architectural decision.** The harness's current state is acknowledged as L5-Workload-Unattested. The trajectory toward L5-Workload-SEV-SNP-Attested is documented but deferred to a later iteration (0.4.x+ candidate, charter-level rework).

### What this decision changes immediately (0.3.1 scope)

1. **CLAUDE.md reframed** (0.3.1 W0 deliverable; deployment-private file) — aho's role description shifts from "governance infrastructure for LLM engineering" to "L5 Workload layer of the deployment-tenant Chain of Trust, defending against host-root memory access and tampered runtimes (current state: unattested unix-socket secrets broker substrate; trajectory: SEV-SNP hardware attestation with 1Password Connect-gated secret release)."

2. **`docs/architecture/chain-of-trust-l5-placement.md`** (0.3.1 W5 deliverable) — repo-resident doc cross-referencing the deployment-tenant's canonical Chain of Trust description, with aho-specific scope: which L5 threats aho currently defends against, which it doesn't, and the trajectory.

3. **L5 container hardening contract acknowledged** in 0.3.1 W0 inventory — deployment-tenant requirements documented as carry-forwards (not 0.3.1 deliverables): read-only root filesystem, `cap_drop: [ALL]`, SHA256 digest pinning in manifests, Kyverno admission controllers. These are L5 hardening invariants aho should eventually enforce, named explicitly so they're not forgotten.

4. **ADR-0007 amendment (0.3.1 W6 deliverable)** — adds tier-orthogonality §: VRAM tier (base/partial/full per ADR-0007) is orthogonal to attestation tier (unattested/SEV-SNP-attested). Both axes are real. 0.3.1 ships partial-tier-unattested. Full-tier-attested is the long-arc end state. Naming both axes prevents conflation.

5. **ADR-0009 trajectory § added (0.3.1 W6 deliverable)** — current state (unix-socket fernet broker with SO_PEERCRED authentication, per ADR-0009 original) is the bridge. End state is 1Password Connect releasing decryption secrets only after the SEV-SNP attestation service validates the workload's measured state. The fernet-broker → 1Password-Connect substitution is the trajectory; both share the contract (host-side credential boundary, container fetches with cryptographic identity proof, no plaintext keys at rest).

### What this decision explicitly defers

- **AMD SEV-SNP attestation chain** — no host in the current aho fleet has SEV-SNP-capable silicon (the fleet today is a mix of consumer Intel + consumer AMD Phoenix-class + consumer Intel Core Ultra). SEV-SNP work requires EPYC-class silicon (or a future Phoenix-Pro generation if that becomes available). 0.4.x+ candidate iteration with hardware procurement as a prerequisite.

- **1Password Connect substrate** — current state (fernet+age unix socket) is the bridge. Connect is the destination. Connect substrate work depends on having SEV-SNP attestation as the gating signal; without attestation, Connect provides no additional security benefit over the current fernet broker (both depend on host-side credential boundary). Pair with the SEV-SNP work in 0.4.x+.

- **Kyverno admission controllers** — requires Kubernetes deployment. ADR-0007 commits to single-pod-on-localhost first; Kubernetes is full-tier cloud deployment scope. 0.4.x+ candidate.

- **Sigstore/Cosign image signing + SLSA Level 3 provenance** — these are Chain of Trust L7 (Supply Chain) controls, not L5. The aho container ships via private ghcr.io with image-id verification; signing infrastructure is deployment-tenant-level (operated by the security team, applied to all deployment-tenant images including aho). Out of aho-iteration scope; surface as a cross-reference only.

- **Drata evidence connector** — Chain of Trust L8 (Compliance) control. aho's sealed archives already match the Drata-consumable shape per ADR-0006. Direct integration is Phase B work; 0.4.x+ candidate.

## Consequences

**Positive:**
- aho's positioning in the larger deployment-tenant architecture is no longer implicit. Customer-facing materials, sales conversations, and engineering hiring can all reference aho's L5 role concretely.
- Engineering scope becomes clearer: aho's iteration roadmap distinguishes "L5-bridge work" (current substrate hardening, secrets broker, materiality measurement) from "L5-endstate work" (SEV-SNP attestation, Kyverno, Connect substitution).
- L5 hardening invariants (read-only root, cap_drop ALL, SHA256 pinning) become *named* carry-forwards rather than implicit assumptions.
- The Chain of Trust framework provides external accountability — aho's design decisions are evaluable against a published architectural standard, not just aho-internal logic.

**Negative:**
- Scope creep risk: framing aho as L5 invites "but L5 should also do X, Y, Z" demands. Mitigated by the explicit deferral list in this ADR.
- Documentation surface increases: now requires synchronization between aho's project docs and the deployment-tenant Chain of Trust documentation. Mitigated by treating the tenant-canonical Chain of Trust doc as the upstream reference and aho docs as downstream cross-references.
- Customer-facing implications: if aho ships as part of a deployment-tenant rollout, customer expectations are calibrated against the Chain of Trust framework, not against aho's iteration-level reality. Mitigated by explicit trajectory documentation (current-state vs end-state distinction).

## Open questions for future iterations

- **0.4.x+ SEV-SNP work:** hardware procurement (EPYC host or equivalent), attestation service design (deployment-tenant level or aho-project level?), Connect substrate substitution methodology.
- **L5 hardening invariants enforcement:** read-only root + cap_drop ALL + SHA256 pinning could be enforced at install.fish or at `aho doctor` time. Lightweight implementation (probe + warn) is a 0.3.2 candidate; full enforcement (fail-closed) requires Kyverno or equivalent.
- **Customer-tenant deployment surface:** when does aho ship as part of a customer-deliverable rather than as internal deployment-tenant tooling? This crosses from engineering-roadmap scope into product-roadmap scope; surface as a cross-reference, not an aho-iteration decision.

## Cross-references

- Deployment-tenant Chain of Trust canonical (upstream of this ADR; deployment-private)
- Deployment-tenant identity-discipline canonical (L2-Identity in Chain of Trust; orthogonal to L5 but referenced by 0.3.1 W5 docs; deployment-private)
- `artifacts/adrs/0007-containerization-architecture.md` — VRAM tier framework (independent axis from attestation tier; this ADR adds the orthogonality § at W6)
- `artifacts/adrs/0009-secrets-broker-boundary.md` — Current secrets broker substrate (this ADR adds trajectory § at W6)
- `artifacts/adrs/0010-materiality-measurement.md` — Materiality measurement (independent system; not affected by Chain of Trust placement but referenced as the falsifiability signal for L5 audit-readiness)
- `artifacts/adrs/0011-substrate-freshness.md` — Substrate freshness telemetry (independent system; not L5-specific but supports L5 audit-readiness)

## Status notes

Status will advance from **Proposed** to **Accepted** at 0.3.1 W6 (ADR finalization) once W5 (`docs/architecture/chain-of-trust-l5-placement.md`) and the ADR-0007 + ADR-0009 amendments are complete.
