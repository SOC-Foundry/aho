# 0.2.17 W1 plan doc

**Workstream:** W1 — base container image build + secrets broker + k8s-readiness
**Iteration:** 0.2.17
**Phase boundary:** 0.2.17 ships base container on NZXTcos. W1 produces the image. W2 wires the feedback loop. W3 instruments materiality. W4 consolidates ADRs and runs retrospective.
**Executor:** Claude Code (`claude --dangerously-skip-permissions`). Codified per resolved open-question 2 from architecture artifact: capability ceiling for code-heavy work, drafter family overlap acceptable because llama3.2 auditor sits structurally between.
**Drafter:** Claude web (Kyle's project folder, persistent across chat sessions).
**Auditor:** Gemini CLI (`gemini --yolo`) for W1 audit. Note: this is the *iteration audit role*, not the in-container audit role — that's llama3.2 once W2 lands. W1 ships the runtime that hosts llama3.2; the auditor seat for W1 itself is still external.
**Time budget:** ~1 hour executor wall-time. Accept up to 90 min if a deliverable snags but stays in scope. If anything crosses 90 min, halt and surface — no architectural debugging mid-flight, scope clarification post-W1.
**Adversarial Authorship contract:** Drafter (me) drafts plan + executor prompt. Executor (Claude Code) implements. Auditor (Gemini CLI) audits. Operator (Kyle) signs. Pillar 11 holds throughout — zero git operations by drafter, executor, or auditor; no commits; no PRs; no secret reads outside the broker contract being implemented.

---

## Scope

W1 ships an OCI image at `ghcr.io/soc-foundry/aho:0.2.17-rc1` that:

1. Boots cleanly on NZXTcos via `podman run`.
2. Auto-detects tier as "base" via nvidia-smi VRAM probe.
3. Hosts council component stubs (`aho.council.triage`, `.audit`, `.embed`, `.dispatch`) that pass healthcheck but do not yet do real work — real implementations land in W2.
4. Talks to the host-side secrets broker over a unix socket for `get_secret(project, name)` round-trips, authenticating by container UID. No SSH agent forwarding, no `~/.ssh/`, no `~/.config/gh/`, no age identity in image layers.
5. Talks to the host's native Ollama via `host.containers.internal:11434` per ADR 0008 hybrid mode. Ollama bind from W0 (`0.0.0.0:11434` per F-host-002) is firewalled at the host to localhost + `169.254.0.0/16` container gateway only.
6. Exposes `/healthz` and `/readyz` on port 8080.
7. Handles SIGTERM with ≤30s drain budget, flushes OTEL before exit.
8. Reads runtime config from env vars and mounted volumes only — no baked credentials, no baked tier config, no baked ChromaDB volume.

W1 does NOT include: real council wrapper implementations (W2), ChromaDB integration (W2), materiality four-bucket telemetry (W3), claw3d bricks (W3), ADR documents (W4).

## Deliverables

### D1 — Dockerfile + image build

**Path:** `Dockerfile` at repo root (or `docker/Dockerfile` if executor prefers — flag in surface).

**Shape:** Multistage build. Final image based on a minimal Python 3.14 image (slim or distroless equivalent — executor's call, document choice in build comment). Install `aho` package via `pip install -e .` from the repo source. Bake council wrapper stub modules under `src/aho/council/`. Bake `aho.cli`, `aho.dispatcher`, `aho.workstream`, `aho.adversarial`, `aho.secrets_client`, `aho.artifact_writer`, `aho.health`, `aho.signal`, `aho.otel` per architecture artifact §Component decomposition. Set `ENTRYPOINT` to `aho` CLI, default `CMD` to a "ready and waiting" mode that holds the container alive after `/readyz` returns 200. No `~/.ssh/`, no `~/.config/gh/`, no `.gitconfig`, no age identity, no fernet passphrase in any image layer.

**Acceptance gate:**
- `podman build -t aho:0.2.17-rc1-local .` succeeds with no errors.
- `podman image inspect aho:0.2.17-rc1-local` shows zero credential-shaped paths in any layer (verified via `podman image inspect ... --format '{{.RootFS.Layers}}'` cross-checked against a regex sweep of layer contents for `id_ed25519|id_rsa|gh_token|age-identity|fernet`).
- Image size under 800MB target. Above that, halt and surface — image bloat is a real concern for engineer-onboarding ergonomics.

### D2 — Tier auto-detection at startup

**Module:** `src/aho/tier_detect.py` (new).

**Shape:** At `aho` CLI startup, probe nvidia-smi for GPU VRAM. Classify per ADR 0007 thresholds: `<12GB → base`, `12–32GB → partial`, `≥32GB → full`. Write classification to runtime OTEL resource attribute `aho.tier`. Also write to a tier marker file at `/var/run/aho/tier` for downstream consumers. NZXTcos with RTX 2080 SUPER 8GB MUST classify as "base"; any other classification on NZXTcos is a fail.

**Acceptance gate:**
- `podman run --rm --device nvidia.com/gpu=all aho:0.2.17-rc1-local aho tier-detect` outputs `base` on stdout and exits 0.
- OTEL trace from the run shows `resource.attributes["aho.tier"] = "base"`.
- `/var/run/aho/tier` inside the container contains `base\n`.

### D3 — Secrets broker (host + container halves)

**Host-side module:** `src/aho/host/secrets_broker.py` (new). Standalone process started by `aho host install` (or already-running systemd user service — executor's call). Listens on `${XDG_RUNTIME_DIR}/aho-secrets.sock` (unix socket). Authenticates incoming connection by reading `SO_PEERCRED` and verifying the connecting UID matches a container UID registered with the broker at container-launch time (via `aho host register-container <uid> <project-label>`). On `get_secret(project, name)` request: validates `project` matches the registered project label, then calls existing `get_secret(project, name)` from `src/aho/secrets/store.py:62`, returns the decrypted value over the socket. Never enumerates, never returns the keystore, never logs the secret value. Logs the request shape (`project`, `name`, requesting UID) only.

**Container-side module:** `src/aho/secrets_client.py` (new — replaces direct `get_secret` import with a broker round-trip). Connects to `/run/host-services/aho-secrets.sock` (host socket bind-mounted into container at this path). Sends `{"project": "...", "name": "..."}` JSON line, reads response. No caching across container restarts. Same `get_secret(project, name)` signature as the existing host-side function so call sites don't change shape.

**Wiring:** `podman run` invocation includes `-v ${XDG_RUNTIME_DIR}/aho-secrets.sock:/run/host-services/aho-secrets.sock:ro` and `--user <container_uid>:<container_gid>`. The container UID is registered with the broker before `podman run` launches, via a wrapper script `aho host run-container` that handles the registration → launch → unregister-on-exit flow.

**Acceptance gate:**
- Host broker starts successfully via `aho host secrets-broker --start` and shows `LISTENING` on the socket.
- `aho host run-container -- aho secrets-test ahomw telegram_bot_token` (test-only command, removed before image push) returns the same value that `get_secret("ahomw", "telegram_bot_token")` returns when called directly on the host.
- `aho host run-container -- aho secrets-test wrong_project telegram_bot_token` returns auth-fail exit code (project label mismatch).
- Broker logs show request shape but never the secret value (verified via `journalctl --user -u aho-secrets-broker | grep -i token` — should match request lines but no token-shaped strings).
- Container-side process running as the registered UID has read access to the socket; same image running as a different UID is denied at SO_PEERCRED check.

### D4 — k8s-readiness 5 properties

Per ADR 0007 §k8s-readiness:

1. **Env-var config:** All runtime config from env vars. Tier override via `AHO_TIER=base|partial|full` (overrides nvidia-smi probe — useful for testing). Ollama hybrid-mode endpoint via `OLLAMA_HOST=host.containers.internal:11434`. Secrets broker socket path via `AHO_SECRETS_SOCKET=/run/host-services/aho-secrets.sock`.
2. **Mounted secrets:** Broker socket mount per D3. ChromaDB volume mount declared in image but not wired in W1 — `VOLUME /var/lib/aho/chroma` declaration only; W2 wires the actual ChromaDB client.
3. **Stdout/stderr logs:** All Python logging configured to stdout (`INFO`+) and stderr (`ERROR`+). No file-based logs in container. OTEL traces still go to OTLP endpoint per existing aho config.
4. **Graceful SIGTERM:** `aho.signal` handler catches SIGTERM, sets a `shutdown_initiated` flag readable by all components, allows up to 30s for in-flight work to complete, flushes OTEL via `force_flush()`, exits 0. Verified by `podman kill -s TERM <container>` followed by `podman wait <container>` showing exit code 0 within 30s.
5. **Health endpoints:** `aho.health` exposes `GET /healthz` (returns 200 if process is alive) and `GET /readyz` (returns 200 only after tier-detect completes, secrets broker socket is reachable, and council component stubs report ready). Both on port 8080.

**Acceptance gate:**
- All five properties verified per the spec above. Failure on any one fails W1.
- `curl http://localhost:8080/healthz` from inside the container returns 200.
- `curl http://localhost:8080/readyz` returns 503 during tier-detect, transitions to 200 within ~10s of container start.
- SIGTERM drain test: `podman kill -s TERM` followed by `podman wait` exits 0 in ≤30s.

### D5 — Ollama firewall mitigation

**Shape:** Land the deferred firewall mitigation from F-host-002 (W0 Bucket 2.4). Add `firewalld` or `iptables` rules limiting Ollama port 11434 to localhost (`127.0.0.0/8`) and the container gateway range (`169.254.0.0/16`). Drop from all other interfaces. Verify rule via `nft list ruleset` (or `iptables -L -n` if `firewalld` not engaged).

**Acceptance gate:**
- From NZXTcos host: `curl http://localhost:11434/api/version` returns Ollama version JSON (still works for host-local callers).
- From inside the W1 container: `curl http://host.containers.internal:11434/api/version` returns Ollama version JSON (still works via container gateway).
- From auraX9cos over tailnet (or simulated tailnet peer): `curl http://nzxtcos:11434/api/version` times out or connection-refused (exposure removed from tailnet).
- F-host-002 carry-forward updated with mitigation-applied disposition; not removed (keep historical record), but status flipped from `mitigation_deferred_to_w3` to `mitigation_landed_in_w1`.

### D6 — Council component stubs

**Modules:**
- `src/aho/council/dispatch.py` — exposes `dispatch(work_shape, role)` function. W1 implementation: returns a stub model_id string per role + tier. Logs OTEL span per call with `model_id`, `role`, `work_shape`, `tier_decision`, `stub: true`. No actual model invocation.
- `src/aho/council/triage.py` — exposes `classify(artifact)` function. W1 implementation: returns a stub classification dict `{category: "stub", confidence: 0.0, stub: true}`. Logs OTEL span. No nemotron-mini invocation.
- `src/aho/council/audit.py` — exposes `audit(claims, artifacts)` function. W1 implementation: returns a stub disposition dict `{disposition: "stub", confidence: 0.0, findings: [], stub: true}`. Logs OTEL span. No llama3.2 invocation. Confidence floor logic NOT yet wired (W2).
- `src/aho/council/embed.py` — exposes `embed(text)` function. W1 implementation: returns a fixed-length zero vector. Logs OTEL span. No nomic-embed-text invocation.

All stubs respond to `/readyz` participation by returning ready=true. All stubs are import-clean (no Ollama API connection at import time — connections happen lazily in W2 implementations).

**Acceptance gate:**
- `python3 -c "from aho.council import dispatch, triage, audit, embed; print('imports clean')"` runs inside the container with exit 0.
- Each stub function callable, returns the stub-shaped dict, emits OTEL span. Verified via OTLP capture of a single test invocation per stub.
- `/readyz` includes council component stubs in its readiness check; transitions to 200 only after all four stubs report ready.

### D7 — Push to ghcr.io

**Shape:** Tag final image as `ghcr.io/soc-foundry/aho:0.2.17-rc1`, `podman push` via `gh auth token | podman login --password-stdin` per F-host-002 / W0 Bucket 2.5 pattern. Verify `gh api /orgs/soc-foundry/packages/container/aho/versions` returns the new version. Token consumed via pipe only — never displayed, never written to a repo path, never read back into context.

**Acceptance gate:**
- Image visible at `ghcr.io/soc-foundry/aho:0.2.17-rc1`.
- `podman pull ghcr.io/soc-foundry/aho:0.2.17-rc1` from a clean local tag store succeeds.
- Pulled image runs healthcheck-clean per D4 acceptance gate.
- Pillar 11 invariant: zero git operations executed by executor; gh token consumed via pipe to podman login only.

## Cross-references

- **Architecture artifact:** `aho-base-container-architecture.md` (chat-side memory, not yet repo-resident — converts to ADR-0007 amendment + ADR-0009 + ADR-0010 in W4).
- **ADR 0007:** containerization architecture; W1 amendments: §council-roles subsection (base-tier seat assignments only — partial/full noted as 0.3.x roadmap), §secrets-broker pointer (full spec lands as ADR-0009 in W4), §firewall-rule-applied (transitions F-host-002 from deferred to landed).
- **ADR 0008:** dispatcher missing-model handling. W1 inherits hybrid-mode `host.containers.internal:11434`; production-mode dispatch (full model service URL) deferred to 0.3.x.
- **F-host-002:** Ollama bind on `0.0.0.0:11434` with deferred firewall mitigation. D5 lands the mitigation; carry-forward status flips to `mitigation_landed_in_w1`.
- **F-0.2.17-W0-003:** GitHub Packages last-tag DELETE behavior. D7 push targets a real version tag, so this constraint doesn't trip — but the push wrapper should defensively handle it if W1 needs to delete and re-push during debugging.
- **F-0.2.17-W0-004:** CLI argparse `--status` choices missing `pass_with_findings`. Recommend executor land a small fix in the same iteration if low-effort, otherwise punt to W4 retrospective. Not a W1 acceptance gate.
- **F-0.2.17-W0-005:** registry tag drift in pre-flight scripts. Not a W1 concern (W1 produces a tag, doesn't validate against external NVIDIA tag scheme), but flagged so executor doesn't repeat the same shape.
- **G001:** fish-pure shell, no heredocs, `printf` not heredoc syntax. All operator-side commands in executor prompt and surfaces must be fish-clean.
- **G022:** `command ls` not `ls`. Applies to any operator-facing surface output.
- **G081:** no celebratory framing in any close note, surface, or commit-shape output. Banned phrases: "clean close," "landed beautifully," "all green."
- **Pillar 11:** zero git operations by drafter, executor, or auditor. Operator (Kyle) holds all git add/commit/push.
- **G083:** silent rubber-stamp gotcha (GLM `{score:8, "ship"}`, nemotron-mini `categories[-1]` fallback). Not directly W1 work — W1 stubs don't yet invoke models — but the audit/triage stubs MUST be raise-on-malformed-shaped from the start. No `categories[-1]` fallback in stub code; no hardcoded "ship" disposition.

## Acceptance archive shape

Per ADR 0006, W1 acceptance archive at `artifacts/iterations/0.2.17/acceptance/W1.json` with:

- `audit_status: "pending_audit"` at write time.
- One entry per deliverable D1–D7 with `result: pass | fail | pass_with_findings | deferred`, `evidence: <verification record>`, `notes: <historical or contextual>`.
- `carry_forwards_added` list with any new F-0.2.17-W1-NNN entries (likely zero if W1 lands clean — possibly one if image-size or build-time gotcha surfaces).
- `pillar_11_invariant_check: "pass"` with executor-side evidence (no `git` invocations in executor session log).
- Sealed sha recorded; no in-place amendments without a separate amendment artifact (W0 pattern).

## Halt-and-surface conditions

Executor halts and surfaces (does not architectural-debug, does not relitigate scope) on any of:

- Image build fails after 3 retries with same error.
- Image size exceeds 800MB.
- Secrets broker round-trip fails reproducibly with no clear bug surface.
- k8s-readiness gate fails on any of the 5 properties.
- Firewall mitigation breaks legitimate host-local Ollama callers (existing aho codebase paths).
- Push to ghcr.io fails with non-tag-drift error.
- Wall-time crosses 90 min with deliverables incomplete.

On halt, executor writes a partial W1 acceptance archive with `audit_status: "blocked"` and surfaces the specific failure to operator. Drafter (me) re-engages in chat to refine scope or unblock.

## Out of scope (deferred)

- **Real council wrapper implementations** (nemotron-mini, llama3.2, nomic real invocations) → W2.
- **ChromaDB integration** → W2.
- **Materiality four-bucket telemetry** → W3.
- **claw3d brick rendering** → W3.
- **Per-component bricks (per architecture artifact §claw3d)** → W3.
- **Anti-rubber-stamp hardening verification across all three failure modes** → W2 (where the real implementations exist to harden) and W3 (where the trip-wires emit).
- **ADR 0007 amendment, ADR 0009 secrets broker, ADR 0010 materiality** as repo-resident docs → W4.
- **Component decomposition doc + claw3d brick spec** as repo-resident → W4.
- **Per-engineer onboarding ergonomics** (smooth `aho host install` flow, multiple-engineer multi-keystore docs) → W4 or 0.3.1 launch readiness.
- **Container-resident model bundling** (image-baked Ollama models) → 0.3.x.
- **Production-mode dispatch (non-hybrid)** → 0.3.x.

## Executor prompt

(Lands as separate artifact at `artifacts/iterations/0.2.17/prompts/W1-executor.md` after this plan doc is reviewed and signed.)
