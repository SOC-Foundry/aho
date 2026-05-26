# 0.2.17 W0 close note

**Disposition:** pass_with_findings.

W0 acceptance archive sealed at
`artifacts/iterations/0.2.17/acceptance/W0.json`.
W0 audit archive sealed at
`artifacts/iterations/0.2.17/audit/W0.json` with
`audit_result: "pass_with_findings"`. Sealed shas (verified at
close-note authoring time):

- acceptance archive sha256:
  `cd4e3f96b6d4217f275a946be964d38ff78b8acff7cbd683002f84f4463dfebc`
- audit archive sha256:
  `1e2b2f496fbf583f9228bdd5658e72ede348bb62809fcaa6704e788ba0067d89`

The audit archive's internal `acceptance_archive_sha256` field
records `cd4e3f96…`, which matches the acceptance archive's
external sha. Drafter prompt for this close cited
`audit_archive_sha256: cd4e3f96…`; that value matches the
acceptance archive's sha rather than the audit archive's own
disk sha (`1e2b2f49…`). Disk-verified values are recorded above
as ground truth. Sealed archives untouched.

## Audit findings

Three findings dispositioned in `audit/W0.json`:

- **AF001 (info)** - F-0.2.17-W0-003 (GitHub Packages API
  per-version DELETE rejects on last-tagged packages;
  package-level DELETE via
  `/orgs/<org>/packages/container/<name>` is the correct
  fallback) was identified in B2.5 prose and acceptance archive
  notes but omitted from the formal `carry_forwards_added` list
  at acceptance-write time. Process drift, not substance drift.
  Closes via the carry-forwards list update recorded below;
  acceptance and audit archives remain sealed at their stated
  shas.
- **AF002 (info)** - Plan §B4 narrative retains 11 "Pattern C"
  residues describing the rename action itself
  (bucket title, §Rationale, §Out-of-scope sealed-archive
  pointers). Auditor accepts as intentional rename-announcement
  context. No edits required.
- **AF003 (important)** - B2.3 GPU passthrough deferred across
  the post-W0 reboot boundary (NVIDIA driver/library version
  mismatch; Plasma/Wayland prevent module reload mid-session).
  Acceptable for 0.2.17 W0 and W3 because ADR 0008 hybrid-mode
  routes dispatcher traffic to the host's native Ollama, which
  uses the host GPU directly with no container GPU passthrough
  required. Container GPU passthrough becomes load-bearing for
  0.3.x production-tier deployment. ADR 0007 already updated
  with the deferral rationale and the post-reboot one-command
  validation path
  (`sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml`
  followed by `podman run --rm --device nvidia.com/gpu=all
  docker.io/nvidia/cuda:12.0-base nvidia-smi`) (the actual
  post-reboot validation used
  `docker.io/nvidia/cuda:12.6.3-base-ubuntu24.04` because the
  `12.0-base` tag was retired in NVIDIA's
  `docker.io/nvidia/cuda` tag scheme between deferral-write
  time and post-reboot validation time; the registry-tag-drift
  surface is captured as F-0.2.17-W0-005 in
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md`, and
  the verification record lives in
  `artifacts/iterations/0.2.17/acceptance/W0-amendment-b2-3.json`
  sha256
  `41c3424f019d8d4800e56de59d17f7178daa06aecba196c2e380479ee22940a5`;
  the `12.0-base` citation in the validation-path snippet above
  is preserved as the audit-time record of the deferral state).
  Validation completed post-reboot on the Saturday timeline
  (earlier than the originally-scheduled Sunday post-SF-queue
  path); see `acceptance/W0-amendment-b2-3.json` for the
  verification record.

## Carry-forwards list update

- **F-0.2.17-W0-003 added** to
  `artifacts/iterations/0.2.16/carry-forwards-0.2.16.md` under
  the "Target: 0.2.x cleanup (future ADR candidate)" section,
  inserted between F-host-002 and W4-AF002 (the analogous
  deployment-doc-lesson position). Entry shape: GitHub Packages
  API per-version DELETE rejects the last tagged version of a
  package; package-level DELETE via
  `/orgs/<org>/packages/container/<name>` is the correct
  fallback. Source: 0.2.17 W0 Bucket 2 B2.5 cycle. Disposition:
  deployment-doc lesson - applies to any future container-build
  operation that cleans up after a registry round-trip
  pre-flight. AF001 closes by virtue of this list update;
  acceptance and audit archives are not amended.

## Coherence summary

- Audit archive recorded count_coherence_check as "26 items in
  carry-forwards-0.2.16.md matches retrospective 22 + 4 new"
  (W4-AF002 + the 0.2.17 W0 quartet F-0.2.17-W0-001,
  F-0.2.17-W0-002, F-host-001, F-host-002).
- F-0.2.17-W0-003 added at close-note-authoring time brought
  the new-from-W0 count to 5 and the total list count to 27
  (22 + 5 new).
- F-0.2.17-W0-004 added during workstream_complete emit (CLI
  argparse choices gap surfaced by the emit itself) brought
  the new-from-W0 count to 6 and the total list count to 28
  (22 + 6 new).
- **F-0.2.17-W0-005 added post-sign-pending via B2.3 verification
  amendment** (registry tag drift surfaced during NVIDIA
  `docker.io/nvidia/cuda` validation) brings the new-from-W0
  count to 7 and the total list count to 29 (22 + 7 new).
- The audit archive itself is not amended; the count
  reconciliation is recorded here in the close note rather
  than as an archive amendment, preserving the audit's sealed
  state.

### B2.3 verified post-reboot - addendum-pending

- **What changed.** B2.3 (Podman GPU passthrough probe) was
  sealed in `acceptance/W0.json` with `result=deferred` per
  ADR 0007 §GPU passthrough deferral, pending post-reboot
  validation scheduled for Sunday post-SF-queue per Kyle.
  Post-reboot validation has now run successfully:
  `sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml`
  succeeds with NVML init clean (all 595.71.05 libs resolved,
  CDI spec version 0.5.0 written) and `podman run --rm
  --device nvidia.com/gpu=all
  docker.io/nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi`
  shows the host RTX 2080 SUPER inside the container, driver
  595.71.05, 51 MiB / 8192 MiB, P8 idle - same GPU state as
  host `nvidia-smi`.
- **Where the verification record lives.** A separate
  amendment artifact at
  `artifacts/iterations/0.2.17/acceptance/W0-amendment-b2-3.json`
  (sha256
  `41c3424f019d8d4800e56de59d17f7178daa06aecba196c2e380479ee22940a5`).
  Sealed `acceptance/W0.json` (sha256 `cd4e3f96…`) and sealed
  `audit/W0.json` (sha256 `1e2b2f49…`) are not modified. The
  amendment is a fresh artifact, not a re-seal - `result=deferred`
  in the sealed acceptance archive is not retroactively
  re-classified.
- **Tag-drift surface.** Original B2.3 plan-text and ADR 0007
  §GPU passthrough deferral validation-path snippet referenced
  `docker.io/nvidia/cuda:12.0-base`, which has been retired in
  NVIDIA's `docker.io/nvidia/cuda` tag scheme. Validation used
  `12.6.3-base-ubuntu24.04` as the verified-current tag. Tag
  drift recorded as **F-0.2.17-W0-005** in
  `carry-forwards-0.2.16.md` under the 0.2.x cleanup section
  (paired with F-0.2.17-W0-003 - both are pre-flight
  automation hardening lessons).
- **Status.** Addendum-pending operator counter-sign on the
  amendment artifact. Counter-sign confirms acceptance of (a)
  B2.3 post-reboot verification outcome, (b) F-0.2.17-W0-005
  addition to the carry-forwards list, and (c) this close
  note's updated coherence-section count (28 → 29). The
  addendum does not require re-seal of acceptance or audit
  archives; the W0 close state and the W1 launch gate are
  unchanged by this amendment.

## B2.3 deferral summary

- **What is deferred:** Podman GPU passthrough probe (B2.3).
- **Why deferral is acceptable for 0.2.17:** ADR 0008
  hybrid-mode dispatcher routes to host-native Ollama, which
  uses the host GPU directly. W0 and W3 do not depend on
  container-side GPU passthrough.
- **What deferral gates:** 0.3.x production-tier deployment
  readiness - container GPU passthrough is load-bearing once
  workloads run inside the container rather than against the
  host's native Ollama.
- **Validation path:** One-command. Validation completed
  post-reboot on the Saturday timeline (earlier than the
  originally-scheduled Sunday post-SF-queue path); see
  `acceptance/W0-amendment-b2-3.json` for the verification
  record. ADR 0007 records the exact command sequence and the
  empirical NVML driver/library version-mismatch state at
  deferral time (userspace 595.71.05 vs. running kernel
  module 595.58.03), which remain historically accurate as
  the audit-time snapshot - post-reboot the kernel module
  rolled forward to 595.71.05 and NVML init went clean.

## State at close

- Acceptance archive: sealed,
  `audit_status: "pending_audit"` at write time, now
  superseded by audit archive's `pass_with_findings`.
- Audit archive: sealed.
- Carry-forwards list: updated across three close-note-era
  additions - F-0.2.17-W0-003 (added at close-note authoring,
  GitHub Packages last-tag DELETE behavior; closes audit
  AF001), F-0.2.17-W0-004 (added during workstream_complete
  emit, CLI argparse `--status` choices gap), and
  F-0.2.17-W0-005 (added post-sign-pending via the B2.3
  verification amendment, NVIDIA `docker.io/nvidia/cuda`
  registry tag drift). Effective new-from-W0 count = 7;
  effective total list count = 29 (22 + 7 new). Internally
  consistent with the Coherence summary section above.
- W1 launch gate: blocked on Kyle's signature on this
  close note. workstream_complete emit (this turn) advances
  the state machine but does not lift the W1 launch gate.
- W1 design + plan refinement: deferred to chat after
  Kyle signs and the close note lands. Chat-first
  discipline holds; no W1 launch artifacts drafted in
  this turn.

## Operator sign-off

Signed by: Kyle Thompson
Date: 2026-05-03T03:12:26Z
Disposition acknowledged: pass_with_findings
B2.3 amendment counter-signed: yes (acceptance/W0-amendment-b2-3.json sha 41c3424f019d8d4800e56de59d17f7178daa06aecba196c2e380479ee22940a5)
Carry-forwards acknowledged: F-0.2.17-W0-003, F-0.2.17-W0-004, F-0.2.17-W0-005
W1 launch gate: lifted
