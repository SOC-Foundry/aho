# W1 plan-doc amendment (post-W0-close, post-handoff-brief)

**Iteration:** 0.3.1
**Workstream:** W1
**Status:** plan-doc amendment, supersedes original W1 scope in `aho-plan-0.3.1.md` §W1
**Authored:** 2026-05-25 (post-W0-close, post-handoff-brief, post-beacon-review)
**Authoring agent:** drafter (claude-web)

## What changed from original W1 plan-doc

Original W1 (sealed at W0 D2 plan-doc): "Substrate freshness telemetry (F-0.2.18-W1-004 closure)" — 10 substrate facts, OTEL gauge, `bin/aho-probe-substrate`, dashboard, install.fish integration. Five deliverables, 4-8h.

Three reshape inputs post-W0-close:

1. **W0 D9 carry-forwards** F-0.3.1-W0-001 (drafter substrate-prerequisite gap) + F-0.3.1-W0-002 (ChromaDB collection empty post-install) need W1 structural closure.
2. **Handoff brief observations 1-3** (canonical-root checkpoint absent, OTEL collector endpoint unreachable post-NZXTcos-decommission, legacy sys.path drift) need disposition. Per drafter arbitration: capture each as a new W0-closing carry-forward (F-0.3.1-W0-003/004/005) and assign closure per amendment.
3. **install.fish idempotency reframing.** install.fish becomes the canonical pre-flight surface across every workstream's D0. Idempotency property is load-bearing: running install.fish on a healthy host completes in seconds with "all steps already satisfied," remediates only on drift, produces structured per-step output that `bin/aho-doctor` parses for halt-or-proceed. `--check` flag becomes read-only escape hatch for debugging, not the canonical pre-flight surface.

Scope grows: 8 deliverables, 8-10h overnight, hard ceiling 12h. Two new carry-forwards close (F-0.3.1-W0-001/002), three new from W0 close (W0-003/004/005), plus F-0.2.18-W1-004 from prior iteration.

## Arbitration decisions pinned (operator, this morning)

1. **OTEL collector endpoint (handoff observation 2):** Option A — local collector on a8cos during W1, migrate to Beacon-as-aggregator in W2.
2. **Canonical-root checkpoint absent (handoff observation 1):** D1 install.fish work, not D4 telemetry. install.fish becomes a step that writes initial `.aho-checkpoint.json` at canonical root if absent.
3. **Legacy sys.path drift (handoff observation 3):** W1 substrate probe (W1 D4 fact #13 covers it); W2 install.fish refactor includes the editable re-install (`pip install --user --break-system-packages -e ~/Development/Projects/socfoundry/aho`) that closes structurally.
4. **New carry-forwards W0-003/004/005:** capture as IDs at W0-amendment-time so W1 can close them with explicit traceability. F-0.3.1-W0-003 (OTEL endpoint post-NZXTcos-decommission), F-0.3.1-W0-004 (canonical-root checkpoint absent), F-0.3.1-W0-005 (legacy sys.path drift in editable-install metadata).
5. **Wrapper naming:** `bin/aho-doctor` (executor's preference, closer to existing conventions). 0.3.2 extracts to `bin/tteos-doctor` on p3cos.
6. **Beacon integration scope:** β — W1 ships local-only telemetry (a8cos-local collector OR jsonl-log fallback). W2 expands install.fish to write Beacon-OTLP configuration as part of tier-aware install.

## Updated deliverables (8 total)

### D1 — install.fish idempotency hardening + structured per-step output

**Module:** Existing `install.fish` is already a step-resumable orchestrator (per W0 D4 fact-grep evidence: `~/.local/state/aho/install.state` step-file shape). D1 hardens idempotency across every step + emits structured JSON per step (default mode, not behind a `--check` flag) so any consumer (`bin/aho-doctor`, executor D0 step, future tooling) can parse step state.

**Shape changes to install.fish:**

- Every step's check command runs first; if pass, step exits with "satisfied" status without remediating. If fail, step remediates, re-checks, and either exits with "remediated" or "remediation_failed" status.
- Per-step output to stdout (human-readable) AND structured JSON appended to `~/.local/share/aho/install-state.jsonl` (append-only). Per-line: `{step_id, step_name, check_command, expected_state, observed_state, action_taken, final_status, started_at_utc, completed_at_utc, duration_ms, remediation_command_if_any}`.
- `--check` flag added as read-only mode: runs every step's check command, emits per-step status, NEVER remediates. For drafter/operator debugging when you want to see drift without remediation cascade.
- `--step <step_id>` flag added: runs only the named step (check + optionally remediate). For surgical re-runs during development.

**Step set additions in D1 scope** (closing W0 handoff observations):

- New step: `canonical_checkpoint_present` — writes `.aho-checkpoint.json` at `~/Development/Projects/socfoundry/aho/.aho-checkpoint.json` if absent. Initial content per existing checkpoint schema; iteration = `0.3.1`, workstream = current-active-or-W0. Closes F-0.3.1-W0-004 structurally.
- New step: `python_sys_path_clean` — probes `sys.path` for legacy `/home/kthompson/dev/projects/aho/src` entry, reports as fail if present, remediation = re-install editable (defers actual `pip install` to W2 scope; W1 reports the drift, W2 fixes it). Closes F-0.3.1-W0-005 partially in W1 (probe surfaces the drift), fully in W2 (re-install closes the drift).
- New step: `chromadb_collection_populated` — probes per-project ChromaDB collection for non-zero document count, reports as fail if empty, remediation = invoke `aho rag bootstrap`. Pairs with D2.

**Acceptance gates:**
- `install.fish` (no flags) on current a8cos state completes in <30s with all steps reporting "satisfied" or "remediated" (W0 D9 already installed chromadb; idempotent re-run reports satisfied).
- `install.fish` on synthetic drift state (e.g., temporarily `mv ~/.config/aho/tier.json{,.bak}`) detects tier_json_present fail, remediates by writing tier.json, exits clean.
- `install.fish --check` produces same per-step status output without any mutations (verifiable via pre/post sha of `~/.config/aho/`, `~/.local/share/aho/`, etc.).
- Output JSON validates against documented schema in W1 acceptance evidence.
- Re-running `install.fish` immediately after a successful run produces identical per-step status (all "satisfied").

**This is the load-bearing deliverable.** D3 (bin/aho-doctor wrapper) and W2+ workstream pre-flight all build on this.

### D2 — `aho rag bootstrap` (closes F-0.3.1-W0-002)

**Module:** `bin/aho-rag-bootstrap` fish wrapper + `src/aho/rag/bootstrap.py` Python implementation. install.fish gets a new step `chromadb_collection_populated` (per D1) that invokes `aho rag bootstrap` on detected empty collection.

**Canonical artifact set ingested:**
- `artifacts/iterations/*/carry-forwards-*.md` (all iteration carry-forward files in active set)
- `artifacts/iterations/*/aho-plan-*.md` (all plan-docs)
- `artifacts/iterations/*/W*-close-note.md` (all workstream close notes)
- `artifacts/iterations/*/iteration-close-*.md` (all iteration-final close notes)
- `artifacts/adrs/*.md` (all ADRs)
- `docs/retrospectives/*.md` (retrospectives)

Chunks via existing `aho.rag` chunking (W2-of-0.2.17 implementation, unchanged). Embeds via `nomic-embed-text` on local ollama. Writes to per-project ChromaDB collection. Idempotent (chunk-level dedup by content hash).

**Subcommands:**
- `aho rag bootstrap --dry-run` — reports planned ingestion shape (file count, chunk count estimate, embedding dimension, estimated wall-clock).
- `aho rag bootstrap` (no flag) — executes ingestion, reports actuals.
- `aho rag bootstrap --rebuild` — drops collection + re-ingests (escape hatch for collection corruption; not invoked by install.fish).

**Acceptance gates:**
- `--dry-run` reports non-zero file count + chunk estimate (~200 artifacts × ~5-15 chunks each).
- Default invocation populates collection successfully on a8cos post-D1 install run.
- Post-bootstrap, `aho.council.audit_ref_lookup` query on `F-0.2.17-W1-003` returns `status=registered` with non-null `top_source_artifact_path` pointing to a relevant W1-close-note or carry-forwards-file source.
- Post-bootstrap query on `F-0.2.18-W2-004` also returns `status=registered`.
- Re-running `aho rag bootstrap` produces same collection state (idempotency: same chunk count, same chunk shas).
- install.fish integration: `chromadb_collection_populated` step on empty collection invokes `aho rag bootstrap` automatically, returns "remediated" status.

**Closes F-0.3.1-W0-002 structurally.**

### D3 — `bin/aho-doctor` wrapper

**Module:** New fish wrapper at `bin/aho-doctor`. Invokes `install.fish --check`, parses per-step JSON output, evaluates required-steps list for the calling workstream, exits 0 if all required pass, non-zero with structured surface otherwise.

**Signature:**
```
aho-doctor [--workstream W1|W2|...] [--required-steps step_id_list] [--remediate]
```

`--remediate` flag (default false): if any required step fails, invoke `install.fish --step <failed_step_id>` to attempt remediation, then re-probe. Defaults to "report-only" so executor sees the drift before deciding whether remediation is in-scope.

Per-workstream required-step lists documented in plan-docs going forward. Examples:
- W1 required: `chromadb_importable`, `ollama_running`, `llama_3_2_3b_present`, `nomic_embed_present`, `broker_socket_present`, `canonical_checkpoint_present`, `python_sys_path_clean`, `chromadb_collection_populated`
- W2 required: above + `tier_json_present`, `broker_service_template_installed`, `pacman_ignorepkg_syncthing`, `syncthing_version_1_30_0`
- W3 required (on p3cos): above + `qwen3_5_9b_present`, `nvidia_smi_present`, `vram_gb_ge_12`

**Acceptance gates:**
- `aho-doctor --workstream W1` on current a8cos post-D1+D2 returns exit 0.
- Synthetic test: `mv ~/.config/aho/tier.json{,.bak}` and invoke `aho-doctor --workstream W2`; expect non-zero exit + structured surface naming `tier_json_present` as failing step. Then `aho-doctor --workstream W2 --remediate`; expect remediation cascade + exit 0.
- Wrapper output format documented in inline comments; integration pattern for future workstream executor prompts documented in CLAUDE.md update at W6.

**Forward-only deployment per drafter arbitration:** W1 produces aho-doctor. W2 of 0.3.1 is the first workstream whose executor prompt invokes `aho-doctor --workstream W2` as D0. W1 does NOT self-dogfood (W1's substrate verification happened during W0 D9 remediation + during D1+D2 acceptance gates).

**Closes F-0.3.1-W0-001 structurally** (closure-mechanism: wrapper exists and is invokable; W2 closure-verification demonstrates it works).

### D4 — Substrate freshness telemetry (10 → 13 facts per handoff observations)

**Module:** `src/aho/observability.py` (new). `record_observable(fact_id, project, host)`, `last_verified_age_seconds(fact_id)`. Append-only log at `~/.local/share/aho/observables.jsonl`.

**13 substrate facts in W1 scope** (10 original + 3 from W0 closure mechanisms):

1. Tailnet domain (`tail8492.ts.net`)
2. **OTEL collector endpoint** (closes F-0.3.1-W0-003 partially; W1 ships a8cos-local collector reachability probe at `127.0.0.1:4317` or wherever a8cos-local collector binds; W2 migrates to Beacon-as-aggregator)
3. Image FQDN baked into install.fish or container env
4. SSH host keys per host (a8cos, p3cos, x9cos)
5. Podman availability + version per host
6. Broker socket presence per host
7. ChromaDB collection mount path
8. Ollama API endpoint per host
9. 1Password agent socket per host
10. CloudflareWARP DNS interception state per host
11. **ChromaDB collection document count** (per-project; surfaces F-0.3.1-W0-002 closure operationally — fact ages-out if collection re-empties)
12. **Canonical-root `.aho-checkpoint.json` mtime** (surfaces F-0.3.1-W0-004 closure operationally; warns if mtime drifts from current iteration)
13. **Python `sys.path` legacy-entry probe** (surfaces F-0.3.1-W0-005 closure operationally; warns if legacy entry reappears in sys.path)

OTEL gauge `aho.observable.last_verified_age_seconds` with attrs `{fact_id, host, project}`. Local-only emission in W1 (W2 wires beacon integration).

**Per-fact `warning_age_seconds` calibration:** drafter inventory below; executor refines during W1 based on real-world change frequency.

| Fact | Default warning age | Rationale |
|---|---|---|
| Tailnet domain | 30 days | DNS-style infrastructure; months-τ |
| OTEL collector endpoint | 1 hour | Service-state; must be fresh for current iteration |
| Image FQDN | 7 days | Cycle aligned with iteration cadence |
| SSH host keys | 90 days | Slow rotation in non-compliance environments |
| Podman version | 14 days | Bumped on system updates |
| Broker socket | 1 hour | Service-state; must be fresh |
| ChromaDB mount path | 30 days | Stable unless config change |
| Ollama API endpoint | 1 hour | Service-state |
| 1Password agent socket | 1 hour | Service-state per session |
| CloudflareWARP DNS | 1 hour | Active-state; quick drift signal |
| ChromaDB doc count | 30 minutes | Tight; empty collection breaks audit |
| Checkpoint mtime | 24 hours | Per-workstream cadence |
| sys.path clean | 1 hour | Re-probe per-session |

**`bin/aho-probe-substrate`** fish wrapper that probes the 13 facts, writes outcomes to observables.jsonl, integrated into install.fish as a step `substrate_facts_probed_recently`.

**Cross-host probes via Tailscale ssh:** handle `probe_outcome: "host_unreachable"` as distinct outcome class (does NOT halt). x9cos offline acceptable.

**Acceptance gates:**
- All 13 facts probable from a8cos
- F-0.2.18-W1-004 closure invariant: tailnet FQDN appears in observables.jsonl with `last_verified_age_seconds` < 1h after fresh probe
- F-0.3.1-W0-002 operational closure: ChromaDB doc count > 0 post-D2 bootstrap
- F-0.3.1-W0-004 operational closure: checkpoint mtime within 24h of current activity
- F-0.3.1-W0-005 operational closure: sys.path clean probe returns no legacy entry (or reports the drift if W2 re-install hasn't run yet — expected fail at W1 close until W2)
- Host-unreachable structurally handled

**Closes F-0.2.18-W1-004 + F-0.3.1-W0-002 operationally + W0-003 partially (W1 collector local; W2 beacon) + W0-004 operationally + W0-005 partially (W1 probes; W2 remediates).**

### D5 — Dashboard surface

**Module:** Extend existing claw3d dashboard. New panel: substrate-freshness brick grid. Each of the 13 facts renders as a brick:
- Color: green if `last_verified_age_seconds < warning_age_seconds`, yellow if 1-3× warning, red if >3× warning
- Label: fact_id + numeric age (formatted: "27s", "14m", "3d")
- Hover: probe_command + last_outcome + probe_history (last 10 probes)

Summary tile: total facts older than warning threshold (red number if non-zero).

**Acceptance gates:**
- Dashboard renders all 13 facts visually on a8cos
- Visual smoke test: trigger a stale fact (e.g., disable a probe), confirm brick turns yellow then red within 2 warning-age windows
- Summary tile reflects current substrate-freshness count accurately

### D6 — install.fish integration completeness

**Module:** install.fish step ordering reviewed end-to-end. Confirm:
- New steps from D1 (canonical_checkpoint_present, python_sys_path_clean, chromadb_collection_populated, substrate_facts_probed_recently) inserted in correct dependency order
- Step file `~/.local/state/aho/install.state` schema unchanged (backward compatible)
- Per-step JSON output schema documented in install.fish header comment block
- install.fish runs end-to-end on a8cos (current state) with all steps satisfied or remediated, completes in <60s

**Acceptance gates:**
- install.fish full run on a8cos: all steps reach "satisfied" or "remediated" final state, exit 0
- install.fish --check on a8cos: identical per-step output, exit 0, no mutations
- install.fish --step chromadb_collection_populated: invokable, exits 0 on healthy state

### D7 — Unit + integration tests

**New test files:**
- `artifacts/tests/test_install_idempotency.py` — install.fish satisfied-on-re-run, structured JSON output schema validation, --check produces no mutations
- `artifacts/tests/test_rag_bootstrap.py` — bootstrap reads canonical artifact set, chunk count deterministic, idempotency property, lookup query returns registered for known IDs
- `artifacts/tests/test_observability.py` — probe success/failure paths, age calculation, OTEL emit shape, host-unreachable handling
- `artifacts/tests/test_aho_doctor.py` — wrapper invokes install.fish --check correctly, parses output, exits per required-steps evaluation, --remediate cascade

**Acceptance gates:**
- All four test files exist and pass on a8cos post-D1-D6

### D8 — W1 self-audit

**Process:** `llama3.2:3b` on a8cos with RAG enrichment (populated post-D2) + W4-0.2.17 deterministic post-hoc filter + W0-0.2.18 anti-rubber-stamp extensions.

**Critical: this is the FIRST audit on a populated collection.** Meaningful operational test of F-0.3.1-W0-002 closure.

**Acceptance gates:**
- Self-audit emits with disposition (any of clean/halt/surface_to_drafter)
- `rag_enrichment.registered_count > 0` — collection is populated, refs resolve
- `finding_filter.filter_eligible: true` — filter is operationally meaningful (compare to W0 D9 where filter_eligible was false due to empty collection)
- No fake-ID-on-registered findings (W4-0.2.17 filter regression check passes non-vacuously for first time in 0.3.1)
- Drafter reviews D8 disposition in chat pre-sign

**Halt-and-surface:**
- If `registered_count == 0` again, D2 bootstrap is broken; halt and report
- If filter produces a fake-ID-on-registered suppression, W4-0.2.17 hardening regression; halt and report
- F-0.2.18-W0-008 narrative-lift residual expected (auditor may surface narrative-lift findings on W1's documentary prose about D9 remediation); drafter arbitrates per W0 precedent, captures pattern, does NOT halt iteration

## Carry-forwards expected at W1 close

**Closing structurally in W1:**
- F-0.2.18-W1-004 (substrate decoherence; original W1 closure target via D4 telemetry)
- F-0.3.1-W0-001 (drafter substrate-prerequisite gap; structural closure via D3 aho-doctor wrapper)
- F-0.3.1-W0-002 (ChromaDB collection empty post-install; structural closure via D2 + D6 install.fish integration)
- F-0.3.1-W0-004 (canonical-root checkpoint absent; structural closure via D1 step + D4 fact #12)

**Closing partially in W1, completing in W2:**
- F-0.3.1-W0-003 (OTEL endpoint; W1 ships local-on-a8cos, W2 migrates to Beacon-as-aggregator)
- F-0.3.1-W0-005 (legacy sys.path drift; W1 probes via D4 fact #13, W2 re-installs via `pip install -e` to remediate)

**Potentially new from D1-D8 execution surfacing:**
- TBD based on substrate gaps encountered during install.fish hardening or beacon-reachability probing

## Time budget

8-10h overnight executor wall-time. Hard ceiling 12h. Two real risks for budget overrun:

1. **D2 ingestion wall-clock.** ~200 artifacts × ~5-15 chunks each × ~3s embedding latency on Radeon 780M CPU-inference = ~30-90 min ingestion. Could be longer on ROCm/Vulkan inference path. Mitigation: acceptance is "ingestion completes" not "ingestion completes within X minutes."

2. **D4 cross-host probes.** p3cos + x9cos online dependencies. p3cos likely up; x9cos intermittent. If x9cos offline, D4 reports `host_unreachable` for x9cos facts, continues. Does NOT halt.

## Halt-and-surface conditions

- Wall-time > 10h soft / 12h hard
- D1 install.fish idempotency fails: re-run produces non-identical step status
- D2 bootstrap fails to populate collection
- D2 idempotency fails: re-run produces different chunk count or different chunk shas
- D3 aho-doctor exits non-zero on known-good state
- D8 self-audit `registered_count == 0` (D2 didn't fix the operational gap)
- D8 self-audit fake-ID-on-registered finding (W4-0.2.17 filter regression)
- Genuinely ambiguous decision requiring drafter input

## Forward-looking notes

**For W2 (install.fish tier-aware refactor + Beacon integration):**

W2 originally scoped to close F-0.2.18-W2-002/003/004 (tier-aware aho-models, tier-manifest writer, broker systemd template). Per arbitration this morning, W2 also picks up:
- Beacon integration: extract `otel/config.py` + `otel/exporter.py` + `otel/buffer.py` from beacon repo, copy into `src/aho/observability/otlp_exporter.py`. Configure OTLPSettings via `OTLP_*` env-prefixed pydantic settings. Wire aho metrics (audit dispositions, substrate freshness, council invocations) to beacon's gRPC endpoint over Tailscale. Per beacon §11 takeaways: cloud-provider detection auto-degrades on bare-metal, copying the package is the documented extraction path.
- F-0.3.1-W0-005 closure: `pip install --user --break-system-packages -e ~/Development/Projects/socfoundry/aho` to re-install editable pointing at canonical path; verify sys.path drift resolves.
- Beacon API key secret: new fernet-broker entry `beacon_otlp_api_key`; aho's OTLP exporter retrieves at startup. ADR-0009 contract path (broker fetch, never plaintext at rest).

W2 expands accordingly. Drafter authors W2 plan-doc-amendment + executor prompt after W1 close.

**For W3 (p3cos partial-tier deployment):**

Beacon integration (W2) ships before W3 — partial-tier deployment on p3cos benefits from beacon-visible telemetry from day one. p3cos joins beacon's OTLP receiver plane alongside a8cos.

**For W6 (ADR consolidation):**

ADR-0011 finalization incorporates the 13-fact substrate set + W2's beacon integration as the mid-tier-precursor. Lightweight tier ships at W1+W2; mid-tier (`aho posture` subcommand + wave-packet visualization per aho-quantum.md) defers to 0.3.3+ candidate.

ADR-0013 candidate: "Beacon as canonical OTLP aggregator." Decides between (a) leaving beacon integration as install.fish env-var configuration without ADR (operational decision) or (b) elevating to ADR for the architectural decision that Tachtech's operational telemetry plane is beacon-centric across all projects. Drafter recommends (b) — beacon-as-aggregator becomes load-bearing for TTEOS and customer engagements; ADR makes it discoverable.

Pillar amendments at W6 unchanged: Pillar 10/11 amendments + new Pillars 12/13 per drafter chat arbitration. W0 D9 chromadb halt as motivating incident.

**For 0.3.2 (TTEOS extraction + partial OCI image):**

Beacon telemetry must be baked into base AND partial OCI images. Both images include the OTLPExporter pattern from W2; both default to env-var-configurable beacon endpoint; both honor `OTLP_ENABLED=true` posture. TTEOS push includes pointer to both image SHAs.

## Cross-references

- `artifacts/iterations/0.3.1/aho-plan-0.3.1.md` §W1 — original scope this amendment supersedes
- `artifacts/iterations/0.3.1/W0-close-note.md` — F-0.3.1-W0-001/002 closure-mechanism statements
- `artifacts/iterations/0.3.1/W0-to-W1-handoff.md` — executor handoff brief; observations 1-3 source
- `artifacts/observability/260524-beacon-overview.md` — beacon architecture; W2 extraction reference
- `artifacts/adrs/0011-substrate-freshness.md` — lightweight tier ADR (W6 finalizes; W1 ships 13-fact telemetry as the lightweight tier)
- `install.fish` — substrate orchestrator hardened to idempotent + structured output in D1
- `src/aho/rag/__init__.py` — existing RAG infrastructure (W2-of-0.2.17), D2 builds on
