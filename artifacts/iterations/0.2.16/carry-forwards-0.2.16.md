# Carry-Forwards — 0.2.16

Items deferred out of 0.2.16 workstreams, grouped by target. This file is
append-only as workstreams close; it folds into the 0.2.16 retrospective at
iteration close.

## Target: 0.2.16 iteration close-out drift repair

- **W1-AF003 — Baseline failure count typo in acceptance/W1.json**
  - Severity: cosmetic
  - Location: `artifacts/iterations/0.2.16/acceptance/W1.json` →
    `test_results.baseline_regression.baseline_reference_failed_count` claims
    `14`, should be `13`.
  - Disposition: accepted as typo. Sealed archive is not edited post-audit; fix
    at iteration close-out alongside any other cosmetic drift found at close.
  - Source: gemini W1 audit (`artifacts/iterations/0.2.16/audit/W1.json` — AF003).

- **W2-AF003 — Baseline test-count coherence drift (421 vs 427)**
  - Severity: cosmetic (Gemini filed "important"; Kyle's disposition downgrades
    to cosmetic since the numeric baseline is mis-labeled, not incorrect — the
    zero-new-failures signal holds and all 12 failures match baseline entries).
  - Location: `artifacts/iterations/0.2.16/acceptance/W1.json` and
    `acceptance/W2.json` → `test_results.baseline_regression.tests_collected`
    both report `421`. Independent audit collection finds 427 total; 421 matches
    only after the standard W2 ignore-set is applied.
  - Disposition: accepted as-is. Update `artifacts/harness/test-baseline.json`
    counts in the next workstream or iteration close-out to reflect the 427
    total. Do NOT edit the sealed W1/W2 acceptance archives.
  - Future workstreams should include the explicit ignore list in
    `baseline_regression` reporting to prevent this class of count drift (see
    harness-hygiene carry-forward below).
  - Source: gemini W2 audit (`artifacts/iterations/0.2.16/audit/W2.json` — AF003).

## Target: 0.2.16 W3 adjunct OR 0.2.17 harness hygiene

- **F-W1-001 — OTEL_RESOURCE_ATTRIBUTES `${VAR}` expansion wrapper**
  - Severity: important
  - Claude Code does not shell-expand `${AHO_ITERATION}` / `${AHO_WORKSTREAM}`
    in `.claude/settings.json` env values. Literal values work; placeholders
    land verbatim in logs. Aggregator filters dead `${...}` residue but the raw
    files retain it.
  - Proposed fix: `aho workstream init W{N}` bin wrapper that writes literal
    values into `.claude/settings.json` at workstream boundary (Pillar 4 surface).
  - Source: W1 acceptance archive (`acceptance/W1.json` → `findings[0]`).

- **W2 auditor-quality note — explicit ignore-set in baseline_regression reporting**
  - Severity: cosmetic (process)
  - The W2 baseline_regression block reported `tests_collected: 421` without
    enumerating the ignore-set (`test_nemoclaw_real.py`,
    `test_cascade_integration.py`, `test_live_models.py`, `test_glm_live.py`)
    that produced 421. Without the explicit list, 421 vs 427 count drift is
    opaque to future auditors.
  - Proposed fix: future `acceptance/W{N}.json` entries under
    `test_results.baseline_regression` include an `ignored_modules` array
    listing the excluded test files, or equivalent pytest `--ignore` command
    reproducer.
  - Source: W2 close (Kyle disposition on AF003 — auditor-quality related note).

## Target: 0.2.17

- **AF004 — `api_error_count` / `internal_error_count` alias in otel_aggregator.py**
  - Severity: important
  - `api_error_count` is only incremented inside the `internal_error` event
    block in `src/aho/dashboard/otel_aggregator.py`; both fields in `/api/otel`
    output will always be identical in the current implementation.
  - Disposition: clarify intent (alias, missing event mapping, or remove dead
    field). Design decision, not a W1-close decision.
  - Source: gemini W1 audit (AF004).

- **AF005 — `api_retries_exhausted_count` dead field in otel_aggregator.py**
  - Severity: important
  - Initialized and rolled up by the aggregator but never incremented at any
    event ingestion site. Will always return 0.
  - Disposition: map to an actual event, or remove. Same treatment as AF004.
  - Source: gemini W1 audit (AF005).

- **W0 F-W0-004 — conftest allowlist brittleness**
  - Severity: important
  - Carried from W0. The `test_workstream_events.py` fixture has corrupted the
    checkpoint three times across recent iterations; W0 added an allowlist in
    `artifacts/tests/conftest.py` but the underlying fragility persists for any
    future test author who emits workstream events outside the allowlist.
  - Target: 0.2.17 test isolation iteration.
  - Source: W1 acceptance archive (`carry_forward_candidates[1]`).

- **Historical trend graphs (time series of cost/tokens)**
  - Severity: info
  - `/api/otel` returns point-in-time aggregates only. Trend graphs require a
    metric backend that retains data points (Prometheus remote_write from
    otelcol, or Grafana direct scrape). Mercor Grafana reference implementation
    in the claude-otel repo may offer the template.
  - Source: W1 acceptance archive (`carry_forward_candidates[2]`).

- **Dashboard polling cadence unification (/api/state at 5s vs /api/otel at 2s)**
  - Severity: info
  - Server-side caches are 2s on both; Flutter-side 5s for `/api/state` is a
    stale-era choice. One-line tweak, not in W1 scope.
  - Source: W1 acceptance archive (`carry_forward_candidates[3]`).

- **W2-AF004 — `dispatch.duration_ms` measurement-site gap on error paths**
  - Severity: info
  - On success, `dispatch.duration_ms` is sourced from
    `result['wall_clock_seconds'] * 1000.0` (same as event log — single source
    of truth, zero drift). On `DispatchError`, it is sourced from a span-local
    monotonic delta. Happy-path drift was measured at 0.11ms; error-path drift
    is unmeasured and introduces a theoretical two-measurement-site divergence.
  - Proposed target: add test coverage for error-path duration consistency (and
    unify the measurement site if the test surfaces material drift).
  - Source: gemini W2 audit (`artifacts/iterations/0.2.16/audit/W2.json` — AF004).

- **Classifier quality probe — nemotron-mini:4b category-mapping drift**
  - Severity: info
  - W2 end-to-end probe observed nemotron-mini:4b classify "Write a Python
    function that computes fibonacci numbers." as `prose` rather than `code`.
    Orthogonal to trace-propagation scope (the W2 deliverable); captured as an
    observation only.
  - Proposed target: if classifier-conformance drift becomes a recurring theme,
    a dedicated probe + test-suite workstream is the right container — not an
    ad-hoc fix inside unrelated work.
  - Source: W2 acceptance archive (`acceptance/W2.json` →
    `otel_telemetry_evidence.classify_category_note` and
    `carry_forward_candidates[1]`).

- **Closure-capture pattern for span-attribute population**
  - Severity: info
  - Alternative to W2's additive dict-extension (`tokens_eval` /
    `tokens_prompt` keys on the dispatcher return dict). Closure-captured locals
    would keep the return contract narrow but tangle span-attribute population
    into the retry loop's many early-return points. Dict-extension won on the
    simplicity axis for W2; closure-capture stays viable if the return contract
    ever needs to tighten to a fixed schema.
  - Proposed target: any future iteration where dispatcher return contract
    tightening is in scope.
  - Source: W2 acceptance archive (`acceptance/W2.json` →
    `scope_notes.dispatcher_return_shape_delta` and `carry_forward_candidates[2]`).

## Target: engine-selection ADR + bridge live wire-up (0.2.17 or 0.3)

These items are the W3 deferral set. They cluster around the same upstream
decision (alert-engine selection) and are intentionally not actionable in
isolation. The sealed `acceptance/W3.json` and `acceptance/W3-audit-dispositions.md`
hold the full disposition text; entries below are the index.

- **W3-AF001 — Rule 3 expression repair (`rate(...) > 1` → `increase(...) > 5`)**
  - Severity: cosmetic (rule fires no differently today since neither file is
    wired to a live engine).
  - Location: `artifacts/iterations/0.2.16/alerts/anomaly-rules.yaml` AND
    `artifacts/iterations/0.2.16/export/claude-otel-reference-pack/alerts/anomaly-rules.yaml`.
    Change `expr: rate(claude_code_api_error[5m]) > 1` to
    `expr: increase(claude_code_api_error[5m]) > 5` in both files.
  - Disposition (Kyle, verbatim): "accepted. Recommended future repair: change
    `expr: rate(claude_code_api_error[5m]) > 1` to
    `expr: increase(claude_code_api_error[5m]) > 5` in BOTH ... Do NOT make this
    edit in this close-out session — sealed acceptance archive does not get
    retroactive code changes. Carry-forward target: same iteration as
    engine-selection ADR (live wire-up workstream)."
  - Target: paired with engine-selection ADR + live wire-up.
  - Source: gemini W3 audit (`audit/W3.json` — AF001); drafter W3-F002.

- **W3-AF002 — Rule 5 baseline calibration recalibration with larger n**
  - Severity: info.
  - The shipped p99=803.6 ms / threshold=2411 ms is a 21-sample (W2-only)
    starting estimate. Probe `probes/w3_baseline_calibration.py` is re-runnable
    with custom workstream filter and multiplier. Continued accumulation of
    W2/W3/future workstream metrics.jsonl gives larger n on next calibration.
  - Disposition (Kyle, verbatim): "accepted as carry-forward. Already documented
    in pillar-11-monitoring-notes.md §Baseline calibration as 'starting
    threshold only' with re-runnable probe. No new action; continued
    accumulation of W2/W3/future workstream metrics.jsonl gives larger n on
    next calibration."
  - Target: paired with live wire-up.
  - Source: gemini W3 audit (`audit/W3.json` — AF002); drafter W3-F004.

- **W3-AF003 — Rule 5 metric-source gap resolution**
  - Severity: info.
  - `claude_code_tool_result_duration_ms_bucket` does not exist in current
    Claude Code emission; `duration_ms` lives only as a log-event attribute on
    `claude_code.tool_result`. Three resolution options documented in
    `pillar-11-monitoring-notes.md` §Plan inconsistencies item 2 + rule-5 YAML
    comment: engine-side log-to-metric synthesis, OTel processor conversion,
    or rule rewrite against the non-histogram source.
  - Disposition (Kyle, verbatim): "accepted as already-documented. The
    drafter's W3-F003 finding + the three resolution options in monitoring
    notes already disposition this. Gemini's audit confirms the gap
    independently. No new action in this close. Carry-forward target: paired
    with engine-selection ADR (the resolution choice IS part of engine
    selection — engine-side log-to-metric vs OTel processor conversion vs
    rule rewrite)."
  - Target: paired with engine-selection ADR.
  - Source: gemini W3 audit (`audit/W3.json` — AF003); drafter W3-F003.

- **W3-CF1 — Bucket 5 synthetic alert delivery test**
  - Severity: info.
  - Hand-rolled OpenTelemetry-Python probe emitting a synthetic
    `claude_code.commit.count` counter increment with delta temporality,
    verifying end-to-end: rule fires → engine webhook → bridge → Telegram
    delivery in dedicated channel → event log entry. Target: <60s wall-clock.
    Probe shape documented in `pillar-11-monitoring-notes.md` §Deferred
    verification §B5. Becomes executable once an alert engine is live.
  - Target: 0.2.17 or 0.3 (paired with engine-selection ADR).
  - Blocker: engine selection.
  - Source: W3 acceptance archive (`acceptance/W3.json` →
    `carry_forward_candidates[0]`).

- **W3-CF2 — Engine selection ADR**
  - Severity: info (design work).
  - Substantive design decision (Prometheus stack vs VictoriaMetrics vs
    Grafana managed alerting vs cloud-managed vs custom evaluator) covering
    metric-source path from OTel collector, rule format, webhook receiver
    shape, and operational ownership. ADR number is NOT pre-allocated —
    assigned at iteration-execution time from disk enumeration of
    `artifacts/adrs/` (next aho-internal slot is 0006 as of W3 close, per
    `command ls artifacts/adrs/ | grep -v ahomw-`).
  - Target: 0.2.17 or 0.3.
  - Blocker: none — design work, not code.
  - Source: W3 acceptance archive (`acceptance/W3.json` →
    `carry_forward_candidates[1]`).

- **W3-CF3 — Bridge live wire-up**
  - Severity: info.
  - Once engine is selected: define webhook receiver in engine config pointing
    at `http://127.0.0.1:9095/`, create
    `~/.config/systemd/user/aho-alerts-bridge.service` running
    `python -m aho.alerts.telegram_alerts --serve`, ensure G071 daemon-restart
    hook runs after any `src/aho/alerts/` edit. The BridgeHandler implementation
    already maps every typed exception to the correct HTTP status code
    (400/500/502/503) so engine retry semantics are predictable.
  - Target: 0.2.17 or 0.3 (paired with engine-selection ADR).
  - Blocker: engine selection.
  - Source: W3 acceptance archive (`acceptance/W3.json` →
    `carry_forward_candidates[2]`).

- **W3-CF4 — Dedicated alerts-channel secrets creation (Kyle-only)**
  - Severity: info.
  - Kyle creates @aho_alerts_bot Telegram bot, creates dedicated chat, stores
    `ahomw:telegram_alerts_bot_token` and `ahomw:telegram_alerts_chat_id` via
    `aho secret add ahomw telegram_alerts_bot_token <token>` and
    `aho secret add ahomw telegram_alerts_chat_id <chat_id>`. Bridge picks the
    secrets up on next request without code changes — verified by unit test
    that the bridge raises `AlertSecretMissingError` today and would succeed
    once `get_secret` calls return non-empty values.
  - Target: 0.2.17 or 0.3 (paired with bridge live wire-up; no point
    provisioning secrets ahead of engine).
  - Blocker: Kyle action only — Pillar 11 forbids agent secret writes.
  - Source: W3 acceptance archive (`acceptance/W3.json` →
    `carry_forward_candidates[3]`).

- **W3-CF5 — pillar-11-monitoring-notes.md §Deferred verification as forward-pointer**
  - Severity: info.
  - This monitoring-notes section is itself the durable record of what was
    deferred and why. Future iteration owners reading the §Deferred verification
    section get the full disposition for B5, engine selection, bridge wire-up,
    and secrets — without having to re-derive it from the W3 acceptance archive.
    Carry-forward classification: documentation pointer, not a code task.
    Status flips from "forward-pointer" to "historical-pointer" when CF1-CF4
    close.
  - Target: 0.2.17 or 0.3 (closes when CF1-CF4 close).
  - Blocker: none — the artifact already exists and is referenced from this
    acceptance archive.
  - Source: W3 acceptance archive (`acceptance/W3.json` →
    `carry_forward_candidates[4]`).

## Target: 0.2.x cleanup (future ADR candidate)

- **F-0.2.17-W0-001 — `.aho-checkpoint.json` iteration field stale after iteration close**
  - Severity: info.
  - The 0.2.16 close-out marked `iteration_status=closed` and
    `iteration_closed_at=2026-05-01T23:36:52Z` but did not roll the
    checkpoint's `iteration` field forward from "0.2.16" to "0.2.17".
    Observed in 0.2.17 W0: `AHO_ITERATION=0.2.17` is set in env and
    OTEL telemetry attributes correctly, but reading the checkpoint
    shows `"iteration": "0.2.16"`. `aho iteration workstream start W0`
    updates workstream state but not the iteration label. There is no
    `aho iteration init <iter>` CLI surface today.
  - Disposition: pairs with W4-AF002 below — both belong to the same
    iteration / workstream state-machine cleanup. Single future ADR
    addresses iteration-init, iteration-close roll-forward, and the
    workstream-level `pending_audit` event class together. Not a 0.2.17
    fix — out of W0 scope; out of every other 0.2.17 workstream's
    scope as those are all containerization-themed.
  - Target: 0.2.x cleanup (future ADR).
  - Source: 0.2.17 W0 Bucket 1 surface (Claude drafter session, surfaced
    to Kyle, accepted as carry-forward).

- **F-0.2.17-W0-002 — daemon `_ITERATION` cached at module import time**
  - Severity: info (operational).
  - The three council daemons (telegram, openclaw, nemoclaw) capture
    `_ITERATION` from `AHO_ITERATION` at module import time in
    `src/aho/logger.py`. After an iteration roll-forward, the daemons
    keep emitting heartbeats with the previous iteration label until
    restart. Observed in 0.2.17 W0: heartbeats from all three daemons
    show `iteration: 0.2.16` while the active session attributes
    correctly to `0.2.17`. Manual `aho {telegram,openclaw,nemoclaw}
    restart` (or systemd-user equivalent) resolves it; no tooling
    automates the boundary.
  - Disposition: same future-ADR target as F-0.2.17-W0-001 above —
    daemon-restart-on-iteration-boundary belongs to the same state-
    machine cleanup. Not a 0.2.17 fix.
  - Operational note: daemons should be restarted at the end of 0.2.17
    W0 (after the Adversarial Authorship rename pass in Bucket 4) so
    any daemon picking up governance-doc changes also gets the new
    iteration label. Recorded as W0 acceptance archive operational
    note.
  - Target: 0.2.x cleanup (future ADR).
  - Source: 0.2.17 W0 Bucket 1 surface.

- **F-host-001 — Tailscale MagicDNS "Override Local DNS" hijacked CachyOS mirror hostnames; aho deployment-doc requirement: split-DNS for distro mirror domains on Tailscale-enabled hosts**
  - Severity: info (host maintenance for the immediate incident;
    important for the deployment-doc requirement, since any aho
    host that joins Tailscale without the split-DNS rules will
    silently regress into the same failure mode).
  - **Symptom observed in 0.2.17 W0 Bucket 2:** `pacman -Syyu` and
    `pacman -S podman nvidia-container-toolkit libnvidia-container`
    failed with sig-invalid errors on `cachyos-v3.db`,
    `cachyos-core-v3.db`, `cachyos-extra-v3.db`, `cachyos.db`. The
    cached files in `/var/lib/pacman/sync/` contained HTML pages
    (magic `<!DO`) rather than pacman archive databases — every
    file exactly 563638 bytes (~563 KB), every file `Last-Modified:
    2026-02-18 09:52:02` matching when Tailscale was first installed
    on this host. Removing the first-listed mirror from
    `/etc/pacman.d/cachyos-mirrorlist` did not fix it; subsequent
    syncs from other mirrors re-wrote the same HTML to the same
    paths.
  - **Root cause:** Tailscale's "Override Local DNS" setting was
    forcing *all* DNS queries through MagicDNS — including queries
    explicitly directed at upstream resolvers (`@1.1.1.1`,
    `@8.8.8.8`). MagicDNS resolved the CachyOS mirror domains
    (cachyos.org and several mirror.* subdomains under it) to
    `203.0.113.x` addresses (TEST-NET-3, RFC 5737 documentation
    block — not a real production destination). Whatever responded
    at those TEST-NET-3 addresses returned the same static HTML
    interception page for every URL: ~563 KB body, identical
    bytes, last-modified `2026-02-18` matching this host's
    Tailscale-install timing. The Arch-namespace mirrors
    (archlinux.org, pkgbuild.com, etc.) were unaffected because
    their hostnames were not in the MagicDNS hijack set.
  - **Resolution applied (Kyle, 0.2.17 W0 Bucket 2):** Tailscale
    admin-console split-DNS rules added — `cachyos.org` resolves
    via `1.1.1.1` rather than via MagicDNS. Considering adding
    `pkgbuild.com` to the same split-DNS rule next as a defense
    against future MagicDNS expansion. Post-fix,
    `pacman -S podman nvidia-container-toolkit libnvidia-container`
    succeeded on the next attempt.
  - **age-fernet exonerated.** Investigation included an exhaustive
    grep across all aho source for any contact with system
    cryptographic or DNS state: zero hits in `src/`, `bin/`, or
    `scripts/` for `pacman-key`, `/etc/pacman`, `GNUPGHOME`,
    `gpg --import`, `trustdb`, `pubring`, `/etc/ssl`,
    `/etc/ca-certificates`, `/etc/hosts`, `/etc/resolv.conf`,
    `http_proxy`, `HTTP_PROXY`, `/etc/systemd`. The age backend
    (`src/aho/secrets/backends/age.py`) invokes the `age` binary
    via subprocess with `AGE_PASSPHRASE` env — uses X25519/scrypt,
    not OpenPGP, never touches any GnuPG keyring. The fernet
    backend (`src/aho/secrets/backends/fernet.py`) is pure Python
    `cryptography.fernet` with zero subprocess calls and zero
    filesystem touches outside the caller-provided path. The four
    cryptographic ecosystems in play (aho's age, aho's fernet,
    libsecret/secret-tool for OS keyring, pacman's GnuPG) are
    architecturally isolated by file path, process, key format,
    and ownership boundary. **Keep this negative-evidence record
    as durable Pillar-11-adjacent documentation:** any future
    suspicion that aho touches host crypto state should re-run
    this grep and re-confirm the architectural separation rather
    than rely on memory.
  - **Investigation lesson.** The drafter's RCA chain went
    "sigs invalid → mirror corruption" and stopped one layer short
    of asking *why* the mirrors were returning HTML. The DNS-layer
    hijack was never explicitly considered until Kyle identified
    it. The 563-KB-identical-content + Feb-18-mtime pattern was
    visible evidence pointing upstream of the mirror, but the
    drafter read it as "broken CDN" rather than "DNS hijack".
    Future package-management debugging on any host that runs
    Tailscale (or another DNS-modifying service: pi-hole,
    AdGuard, corporate VPNs with DNS interception) should include
    a DNS-resolution sanity check (`dig +short <mirror>` from the
    host, compared against an out-of-band resolver) before
    investigating the mirror infrastructure itself.
  - **Deployment-doc carry-forward (binding for 0.3.x and beyond):**
    Any aho host joining a Tailscale tailnet (or any equivalent
    DNS-modifying overlay network) requires explicit split-DNS
    rules carving out the distro package-mirror domains the host
    syncs from. Without those rules, MagicDNS-style interception
    silently converts package-archive URLs into HTML pages, and
    pacman/yay sync against the affected namespaces fails with
    sig-invalid errors for an indeterminate period until manually
    diagnosed. Specifically, hosts running the aho install path
    on:
    - **CachyOS / Arch-derivatives:** require split-DNS for
      `cachyos.org` (and any other configured CachyOS mirror
      domains in `/etc/pacman.d/cachyos-mirrorlist`) plus the
      official Arch mirror domains (`pkgbuild.com`,
      `mirror.pkgbuild.com`, regional `mirror.*` resolvers).
    - **Future Debian/Ubuntu base-image-derived host build paths:**
      will require analogous split-DNS for `debian.org` /
      `ubuntu.com` apt mirror domains.
    install.fish should optionally probe for the hijack pattern
    on first run when Tailscale is detected — `dig +short
    cachyos.org @100.100.100.100` (Tailscale's MagicDNS
    address) returning a TEST-NET-3 (`203.0.113.0/24`) or
    other RFC-reserved address is the strong signal. The probe
    is a 0.3.x deliverable, not 0.2.17 scope; flagged here as
    the durable form of the recurrence prevention.
  - **Operational impact on 0.2.17 W0:** ~45 min of session time
    spent on the wrong RCA (mirror corruption + mirror-side
    keyring) before Kyle identified the DNS-layer cause. ADR 0007
    was tentatively amended mid-bucket to "Docker engaged" under
    the working assumption that the package-management failure was
    unrecoverable; reverted to "Podman engaged" once `pacman -S
    podman` succeeded post-DNS-fix. Bucket 2 then proceeded as
    originally planned under Path A; only B2.3 GPU passthrough is
    deferred (across a separate post-W0 reboot boundary, for
    NVIDIA driver/library version mismatch — see ADR 0007 §GPU
    passthrough deferral).
  - **Target:** host maintenance (immediate fix, applied) +
    deployment-doc requirement (binding for 0.3.x — install.fish
    Tailscale-aware split-DNS probe).
  - **Source:** 0.2.17 W0 Bucket 2 surface (Kyle identified root
    cause after Claude drafter session pursued mirror-corruption
    hypothesis to the wrong layer of the stack).

- **F-host-002 — Ollama rebound to 0.0.0.0:11434 to satisfy container→host hybrid-mode probe; firewall-rule mitigation deferred to W3**
  - Severity: info (security trade-off, accepted explicitly).
  - **What changed.** 0.2.17 W0 Bucket 2 B2.4 required a container
    inside Podman's default network to reach the host's native
    Ollama at `host.containers.internal:11434` (the ADR 0008
    hybrid-mode wire). Prior to 0.2.17 W0, Ollama was bound to
    `127.0.0.1:11434` only. The rebind was applied via systemd
    drop-in:

    ```
    /etc/systemd/system/ollama.service.d/override.conf
    [Service]
    Environment="OLLAMA_HOST=0.0.0.0:11434"
    ```

    Followed by `sudo systemctl daemon-reload && sudo systemctl
    restart ollama.service`. `ss -tlnp` post-restart confirms
    `*:11434` (all interfaces). B2.4 literal probe passes:
    `podman run --rm alpine sh -c 'curl -sf
    http://host.containers.internal:11434/api/version'` returns
    `{"version":"0.20.2"}`.
  - **Security trade-off, accepted.** Rebinding to `0.0.0.0:11434`
    exposes Ollama on `172.31.255.245:11434` (LAN, enp5s0) and on
    the Tailscale tailnet. Ollama's API has no authentication —
    any peer that can reach the port can list, pull, or run models
    on the host. Trade-off accepted as tolerable for the present
    operator-count (single, Kyle) and tailnet-trust posture
    (peers are operator-controlled).
  - **Deferred mitigation: firewall rule.** The durable shape
    binds Ollama to all interfaces but limits accept-list to
    `127.0.0.1` + the container gateway range (`169.254.0.0/16`),
    drops elsewhere. Concrete form (nftables, illustrative; final
    syntax decided at implementation time):

    ```
    nft add rule inet filter input tcp dport 11434 ip saddr 127.0.0.1 accept
    nft add rule inet filter input tcp dport 11434 ip saddr 169.254.0.0/16 accept
    nft add rule inet filter input tcp dport 11434 drop
    ```

    Deferred to **0.2.17 W3** alongside the hybrid-mode dispatcher
    implementation per ADR 0008. W3 already has scope to wire
    `AHO_DISPATCH_HYBRID_HOST_URL` defaults; adding the firewall
    rule is the natural pairing — both land together so the
    operational surface is consistent.
  - **Why not a different bind.** Considered binding directly to
    `169.254.1.2:11434` (the Podman gateway interface from the
    host's perspective). Rejected because Ollama's `OLLAMA_HOST`
    takes a single host:port; binding to `169.254.1.2` only would
    drop the `127.0.0.1` listener that existing host-side aho
    callers depend on, requiring a coordinated codebase update.
    Backward-compatible all-interfaces bind + firewall allowlist
    is strictly cheaper than a bind change + codebase update.
  - **Verification commands recorded for future re-binding work:**
    `ss -tlnp | grep 11434` on the host shows `*:11434`. Inside
    a Podman container: `curl -sf
    http://host.containers.internal:11434/api/version` returns
    valid JSON.
  - **Target:** 0.2.17 W3 (firewall mitigation + ADR 0008
    implementation pairing).
  - **Source:** 0.2.17 W0 Bucket 2 B2.4 surface; rebind authorized
    by Kyle in W0; firewall-rule mitigation deferred to W3 per
    Kyle's directive.

- **F-0.2.17-W0-003 — GitHub Packages API per-version DELETE rejects the last tagged version of a package; package-level DELETE via `/orgs/<org>/packages/container/<name>` is the correct fallback**
  - Severity: info (deployment-doc lesson).
  - **What surfaced.** 0.2.17 W0 Bucket 2 B2.5 ran a full
    push+pull round-trip against `ghcr.io/soc-foundry/aho` for
    one throwaway tag, then attempted to delete the tag via
    `gh api -X DELETE /orgs/soc-foundry/packages/container/aho/versions/<id>`.
    GitHub rejected with HTTP 400: "You cannot delete the last
    tagged version of a package. You must delete the package
    instead." Per the rejection body, package-level
    `gh api -X DELETE /orgs/soc-foundry/packages/container/aho`
    succeeded (exit 0); subsequent
    `gh api /orgs/soc-foundry/packages/container/aho` returned
    HTTP 404, confirming the package was gone.
  - **Mechanism.** GitHub's package API treats the last
    remaining tagged version of a container package as
    inseparable from the package itself. While >1 tagged
    version exists, per-version DELETEs against
    `/versions/<id>` succeed normally. Once a per-version
    DELETE would leave zero tagged versions, the API requires
    the operator to delete the entire package instead. This is
    GitHub API behavior, not a `gh` tooling issue, and is not
    documented prominently in either the API reference or the
    `gh` man pages — the rejection body is the primary
    discovery surface.
  - **Disposition (deployment-doc lesson):** Applies to any
    future container-build operation that needs to clean up
    after a registry round-trip pre-flight. Pattern: when
    pre-flight pushes a single throwaway tag for verification,
    the cleanup step must fall back from
    `/versions/<id>` DELETE to
    `/packages/container/<name>` DELETE on HTTP 400. Pipelines
    that ship multiple tags (W1's `aho:0.2.17-rc1` and
    successors) hit this rarely — only ephemeral pre-flight
    tags in isolation will need the package-level fallback.
    Recorded here so any future operator running an analogous
    pre-flight does not waste a session reconstructing the API
    behavior from error messages.
  - **Target:** deployment-doc requirement (binding for any
    future container-build pre-flight script). Future
    pre-flight automation should encode the fallback
    explicitly rather than relying on operator recall.
  - **Source:** 0.2.17 W0 Bucket 2 B2.5 cycle (registry
    pre-flight for `ghcr.io/soc-foundry/aho`).
  - **Audit traceability:** Surfaced as AF001 in
    `artifacts/iterations/0.2.17/audit/W0.json` — flagged as
    info-severity process drift because the finding existed
    in B2.5 prose and acceptance archive notes but was
    omitted from the formal `carry_forwards_added` list at
    acceptance-write time. AF001 closes via this entry being
    added to the formal list (this file). Sealed acceptance
    and audit archives are not modified.

- **F-0.2.17-W0-004 — `aho iteration workstream complete --status` argparse choices missing `pass_with_findings`**
  - Severity: info (CLI tooling gap; workaround documented).
  - **What surfaced.** The 0.2.17 W0 workstream_complete emit
    required `status="pass_with_findings"` to mirror the audit
    archive's `audit_result: "pass_with_findings"`. The CLI's
    argparse layer rejected it: `pit_ws_complete.add_argument(
    "--status", default="pass", choices=["pass", "partial",
    "fail", "deferred"], ...)` (`src/aho/cli.py:688`). The
    underlying `emit_workstream_complete()` function in
    `src/aho/workstream_events.py:132` accepts any string for
    `status` — the constraint exists only at the CLI surface.
  - **Workaround used in 0.2.17 W0 close.** Direct Python call
    to `emit_workstream_complete()` bypassing the CLI argparse
    layer. The emit succeeded, schema_version=3 record landed
    in the event log, and the checkpoint advanced to
    `W0_workstream_complete`. Workaround is documented in the
    W0 close note (`artifacts/iterations/0.2.17/W0-close-note.md`)
    under the CLI-status-choices-gap surface section.
  - **Disposition:** same shape as W4-AF002 from 0.2.16 (CLI
    gap on `pending_audit` state) — a CLI surface that lags
    the underlying schema. Recorded as a CLI hardening
    backlog item.
  - **Recommended fix.** Align the CLI `--status` choices with
    the formalized schema vocabulary (`pass` |
    `pass_with_findings` | `partial` | `fail` | `deferred`),
    or generalize the choices set so the CLI is not a
    bottleneck on schema vocabulary that the function layer
    already supports. Pairs naturally with W4-AF002's
    `pending_audit` state-machine work — both are CLI
    surface alignments against the broader Adversarial
    Authorship state machine.
  - **Target:** CLI hardening backlog; candidate for W1+ scope
    in 0.2.17 if it surfaces in containerization-themed CLI
    work, otherwise rolls into the same future ADR addressing
    the workstream-level state-machine CLI gaps.
  - **Source:** 0.2.17 W0 workstream_complete emit (drafter
    surface during close note delivery).

- **F-0.2.17-W0-005 — Registry tag drift in pre-flight validation scripts (NVIDIA `docker.io/nvidia/cuda` tag-scheme retirement)**
  - Severity: info (deployment-doc lesson).
  - **What surfaced.** Original B2.3 plan-text and ADR 0007
    §GPU passthrough deferral validation-path snippet
    referenced `docker.io/nvidia/cuda:12.0-base` for the
    one-command post-reboot validation. At post-reboot
    validation time (this addendum), that tag had been
    retired in NVIDIA's `docker.io/nvidia/cuda` tag scheme;
    the current scheme is the `12.x.y-base-ubuntu24.04`
    family. Validation used `12.6.3-base-ubuntu24.04` as the
    verified-current tag; `podman run --rm --device
    nvidia.com/gpu=all
    docker.io/nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi`
    succeeded (RTX 2080 SUPER visible inside container,
    driver 595.71.05, 51 MiB / 8192 MiB, P8 idle — same GPU
    state as host `nvidia-smi`).
  - **Mechanism.** NVIDIA periodically retires older CUDA
    base-image tag families on Docker Hub as new CUDA
    versions ship. Pre-flight scripts that pin a literal tag
    string in plan-text or ADR snippets silently rot the
    moment the upstream namespace re-shapes its tag set.
    Failure mode is `manifest unknown` from the registry on
    pull, after which the operator must hand-discover the
    current verified-current tag from NVIDIA's published
    list before validation can proceed.
  - **Disposition (deployment-doc lesson):** Pairs with
    F-0.2.17-W0-003 — both are pre-flight automation
    hardening lessons. Pre-flight automation should either
    (a) query the current tag set at runtime against the
    registry's manifest API and select the highest-version
    tag in the relevant family, or (b) pin to a
    verified-current tag and revisit the pin on a fixed
    cadence (e.g., paired with each iteration boundary
    that touches container infrastructure). Plan-text and
    ADR snippets that quote literal upstream tags should
    carry a "verified at <iteration>" marker so future
    operators can tell at a glance whether the snippet is
    likely to still resolve.
  - **Target:** 0.2.x cleanup (deployment-doc requirement,
    paired with F-0.2.17-W0-003 — both belong to the same
    pre-flight-automation hardening pass). ADR 0007's
    §GPU passthrough deferral validation-path snippet
    should be amended in a future iteration to either drop
    the literal tag or annotate it as "verified
    <iteration>"; out of scope for the present addendum
    (which records the post-reboot verification outcome,
    not an ADR amendment).
  - **Source:** 0.2.17 W0 B2.3 post-reboot validation
    (drafter surface during the addendum-pending amendment
    at `artifacts/iterations/0.2.17/acceptance/W0-amendment-b2-3.json`).

- **F-0.2.17-W1-001 — `aho secrets-test` test-only subcommand left in 0.2.17-rc1 image**
  - Severity: low (release-candidate-acceptable; production-promotion
    blocker).
  - **What surfaced.** 0.2.17 W1 D7 (image-push acceptance gate)
    pushed `ghcr.io/soc-foundry/aho:0.2.17-rc1` with the
    `aho secrets-test` subcommand still registered in
    `src/aho/cli.py`. The W1 plan-doc gate 3 specified that
    `aho secrets-test` is a test-only command that should be
    "removed before image push." For an rc1 (release-candidate)
    tag this is acceptable — rc images exist explicitly to be
    exercised in development affordances — but the subcommand
    MUST be removed before any final 0.2.17 or 0.3.x promotion.
    The subcommand also constitutes the production-image surface
    for the F-0.2.17-W1-003 Pillar 11 leakage path; removing it
    closes the production-image side of that incident even if
    the broker test redesign work is deferred.
  - **Mechanism.** `src/aho/cli.py` registers the
    `secrets-test` parser unconditionally. Any image cut from
    the current `cli.py` retains the subcommand. The plan-doc
    intent ("test-only command, removed before image push") was
    not enforced in code or in the build pipeline — relied on
    drafter/executor recall, which lapsed at the W1 image cut.
  - **Disposition (deployment-doc lesson + production-promotion
    gate):** removal required before any final 0.2.17 or 0.3.x
    promotion. Two candidate mechanisms: (a) delete the parser
    registration entirely from `src/aho/cli.py` before the next
    image cut; (b) gate the registration behind
    `AHO_DEV_BUILD=1` env var so dev builds retain the
    affordance and production images do not. Approach (b) keeps
    the affordance available for future broker-redesign work
    without re-cutting the cli surface twice; approach (a) is
    simpler and stricter. Final mechanism pinned at the W4
    image-cut point (or earlier if W2 broker redesign folds in
    the cleanup).
  - **Target:** 0.2.17 W4 (production-image cut) or earlier W2
    (if broker redesign folds in the cleanup).
  - **Source:** 0.2.17 W1 D7 image-push acceptance gate
    (`acceptance/W1.json` → `deliverables[D7].findings[0]`).
  - **Audit traceability:** Surfaced as AF-0.2.17-W1-002 in
    `audit/W1.json` (severity info). Gemini accepted as
    pass_with_findings: "Leaving 'secrets-test' in the rc1
    image contradicts the plan-doc ideal but is acceptable for
    a release candidate. Must be removed before final
    promotion to avoid production-side secret exposure risk."

- **F-0.2.17-W1-002 — Rootless podman pasta networking SNATs container→host traffic to host primary interface; firewall rules must accept by `iif lo` not source-address range**
  - Severity: moderate (resolved in-iteration via operator nft
    rule amendment; recorded as deployment-doc requirement for
    future ADR work).
  - **What surfaced.** 0.2.17 W1 D5 (Ollama firewall mitigation)
    landed nft rules accepting source `127.0.0.0/8` +
    `169.254.0.0/16` based on the apparent container-gateway
    address (`169.254.1.2`, in range). D5 Gate 2
    (container→host.containers.internal:11434 curl) timed out.
    Operator amended via
    `nft insert rule inet aho_ollama input iif lo tcp dport
    11434 accept` inserted at the top of the chain;
    container curl returned HTTP 200 immediately. Pre- and
    post-amendment exit codes recorded in
    `acceptance/W1.json` `deliverables[D5].evidence`.
  - **Mechanism.** When a rootless podman container connects to
    `host.containers.internal:NNNN`, pasta networking translates
    the traffic so it arrives at the host on the `lo` interface
    with the **host's primary IP** as source address (not the
    container-gateway address as the source). Firewall rules
    scoped by source-address ranges (`127.0.0.0/8`,
    `169.254.0.0/16`) do not cover this path because the host's
    primary IP (`172.31.255.245` in this host's case) is
    outside both ranges. The working rule pattern is
    interface-scoped (`iif lo accept`) rather than
    source-address-scoped. Documented in pasta's networking
    semantics; not idiosyncratic to this host.
  - **Disposition (deployment-doc requirement):** any future
    container-host firewall rule design that admits
    container→host traffic via `host.containers.internal` must
    accept by `iif lo` rather than by source-address range.
    ADR-0009 (secrets broker) and any future firewall-mitigation
    amendment to ADR-0007 must reference the `iif`-scoped rule
    pattern explicitly. Pairs with F-host-002 above (Ollama bind
    surface) — both are container→host networking pre-flight
    hardening lessons. The functional gates resolved
    in-iteration; the carry-forward is the documentation-binding
    restatement so future operators do not reconstruct the
    pasta-NAT discovery from timeouts.
  - **Target:** documentation lesson; lands in W4 ADR
    consolidation (ADR-0009 secrets-broker draft + any
    ADR-0007 firewall amendment). Out of scope for W1 close
    (operator nft amendment already in place); out of scope for
    W2/W3 (broker test redesign and secrets-broker hardening,
    not ADR drafting).
  - **Source:** 0.2.17 W1 D5 Ollama firewall mitigation
    (`acceptance/W1.json` → `deliverables[D5].findings[0]`,
    operator-applied amendment recorded in
    `deliverables[D5].evidence.rule_amendment_history`).
  - **Audit traceability:** Surfaced as AF-0.2.17-W1-003 in
    `audit/W1.json` (severity info, status resolved). Gemini
    accepted: "The podman pasta SNAT behavior is a valuable
    discovery. The remediation (iif lo nft rules) correctly
    addresses the connectivity gap for hybrid-mode dispatches."

- **F-0.2.17-W1-003 — `secrets-test` subcommand exposes decrypted value to caller (Pillar 11 friction)**
  - Severity: moderate (Pillar 11 friction; remediation requires
    operator-side token rotation as a hard gate).
  - **What surfaced.** 0.2.17 W1 D3 Gate 1 (host+container
    broker round-trip equivalence acceptance gate) exercised
    `aho host run-container --project ahomw --image
    aho:0.2.17-rc1-local -- secrets-test ahomw
    telegram_bot_token`. The subcommand by design prints the
    decrypted value to stdout to verify broker round-trip
    equivalence with direct host-side `get_secret()`. The
    executor (Claude Code) read the Telegram bot token's bytes
    via Bash tool stdout — a direct contradiction of CLAUDE.md
    hard rule "No reading secrets." Value not reproduced in
    any artifact, log, or downstream surface
    (`acceptance/W1.json` `pillar_11_evidence.secrets_read_by_agent`
    records the incident; the value field reads "non-MISSING
    string, length 46, format `<digits>:<base64ish>` (telegram
    bot token shape) — value not reproduced in archive per
    Pillar 11").
  - **Drafter-side design responsibility.** The W1 plan-doc
    (`artifacts/iterations/0.2.17/W1-plan-doc.md` line 63)
    specified: "`aho host run-container -- aho secrets-test
    ahomw telegram_bot_token` (test-only command, removed
    before image push) returns the same value that
    `get_secret(\"ahomw\", \"telegram_bot_token\")` returns
    when called directly on the host." That specification —
    raw-value return for a value-equality acceptance gate — was
    **wrong on Pillar 11 grounds**. The acceptance gate it
    described could not be exercised by an agent without the
    agent reading the secret. Drafter-side error in plan-doc
    design, not an executor implementation flaw. Documented
    here as a drafter-process gotcha: any acceptance gate that
    surfaces a decrypted secret to any agent stdout is a
    Pillar 11 violation by construction, regardless of how
    short-lived the surface is.
  - **Executor surfaced voluntarily.** The executor (Claude
    Code) recorded the incident as F-0.2.17-W1-003 in the
    acceptance archive at write time, called out the
    contradiction with CLAUDE.md `No reading secrets` rule
    explicitly, and recommended operator-side rotation of
    `ahomw:telegram_bot_token` as remediation. Adversarial
    Authorship protocol working as designed: executor's
    transparent self-reporting is what allowed the auditor to
    disposition the incident as pass_with_findings rather than
    fail. Gemini's AF-0.2.17-W1-001 summary explicitly credits
    this behavior: "the executor's (Claude Code) transparent
    reporting and documentation of the incident as
    F-0.2.17-W1-003 demonstrates adherence to the Adversarial
    Authorship protocol."
  - **Disposition (Pillar 11 incident closure path).** Three
    remediation steps, all required for full incident closure:
    1. **Token rotation pre-0.3.x — HARD GATE.** Operator
       (Kyle) rotates `ahomw:telegram_bot_token` before any
       0.3.x work begins. The 0.3.x launch gate cannot lift
       while the W1-exposed token remains valid. This is the
       binding operator-side action; W1 closes with the action
       outstanding and the gate carried forward.
    2. **W2 (or W3) broker test redesign for hash-fingerprint
       or length-only comparison.** Replace the value-equality
       gate with a design where the secret value never crosses
       the agent stdout boundary. Candidate designs: SHA-256
       fingerprint comparison (host computes hash, broker
       returns the same hash); broker-side equality computation
       returning only a boolean across the socket. Final
       design pinned in W2 plan-doc. F-0.2.17-W1-001
       subcommand removal closes the production-image leakage
       path even if the broker redesign work is deferred.
    3. **Subcommand removal** scheduled by F-0.2.17-W1-001
       (W4 production-image cut, or earlier W2/W3 if redesign
       folds in the cleanup).
  - **Target:** 0.2.17 W2 (broker test redesign — primary
    target) + operator (token rotation pre-0.3.x — hard gate).
    F-0.2.17-W1-001 covers the subcommand removal side.
  - **Source:** 0.2.17 W1 D3 Gate 1 host+container broker
    round-trip (`acceptance/W1.json` →
    `deliverables[D3].findings[0]` and
    `pillar_11_evidence.secrets_read_by_agent`).
  - **Audit traceability:** Surfaced as AF-0.2.17-W1-001 in
    `audit/W1.json` (severity important, status
    `remediation_pending_operator`). Gemini accepted as
    pass_with_findings: "The exposure of a Telegram bot token
    to the agent's stdout is a genuine Pillar 11 friction
    event. However, the executor's (Claude Code) transparent
    reporting and documentation of the incident as
    F-0.2.17-W1-003 demonstrates adherence to the Adversarial
    Authorship protocol. The remediation (rotating the token
    and redesigning secrets-test for hash/length comparison)
    is necessary and sufficient for W1 closure. Mark as
    pass_with_findings."

- **W4-AF002 — CLI gap on `pending_audit` state**
  - Severity: info.
  - The Adversarial Authorship state machine (referred to as "Pattern C"
    in the sealed 0.2.16 audit archive that surfaced this finding; renamed
    in 0.2.17 W0) includes `pending_audit` (drafter writes acceptance
    archive; checkpoint advances to that state pending Gemini audit), but
    `aho iteration workstream` exposes only `start` and `complete`
    subcommands. Today the state is implied by archive existence rather than
    emitted as a first-class event; the checkpoint's `last_event` therefore
    lags by one transition through every workstream's audit window.
  - Pairs with the analogous iteration-level gap observed during the 0.2.16
    iteration close itself: `aho iteration close --confirm` exists, but
    there is no pre-confirm subcommand that mechanically asserts the ADR 0006
    graduation criterion against repo state before sign-off (drafter does
    this manually in the iteration-close artifact today).
  - Disposition (Kyle, verbatim): "accepted as carry-forward. Target: 0.2.x
    cleanup (specific iteration TBD; possibly 0.2.17 if it surfaces in
    containerization work, possibly its own future iteration). Severity: info.
    Future ADR candidate."
  - Target: 0.2.x cleanup; folds into the future ADR that addresses both the
    workstream-level `pending_audit` CLI gap and the iteration-level
    graduation-criterion verification gap.
  - Source: gemini W4 audit (`artifacts/iterations/0.2.16/audit/W4.json` —
    AF002).

## Target: next collector config touch

- **Collector OTLP alias deprecation warning (tracked from W0)**
  - Severity: cosmetic
  - otelcol-contrib v0.149.0 prints "otlp alias deprecated, use otlp_grpc" on
    the `otlp/jaeger` exporter at collector startup. Unchanged through W1 and
    W2. Functional behavior unaffected.
  - Proposed fix: rename exporter key to `otlp_grpc/jaeger` (and any other
    `otlp/*` alias usages) the next time the collector config is edited.
  - Source: W2 acceptance archive (`acceptance/W2.json` →
    `carry_forward_candidates[3]`); originally surfaced in W0.

## Target: 0.2.17 W4

- **F-0.2.17-W2-001 — ChromaDB host-side dev fallback path documentation**
  - Severity: info
  - AHO_CHROMA_DIR defaults to /var/lib/aho/chroma; on hosts without operator-side sudo to create /var/lib/aho, the rag layer falls back to ~/.local/share/aho/chroma. This is correct behavior for hybrid host/container dev but is not yet documented in ADR 0007.
  - Disposition: Document the fallback in ADR 0007 amendment at W4 retrospective. No code change needed.
  - Target: 0.2.17 W4
  - Source: 0.2.17 W2 D1 implementation experience

## Target: 0.3.x

- **F-0.2.17-W2-002 — nomic-embed-text context-length cap surfaces as HTTP 400**
  - Severity: info
  - nomic-embed-text in Ollama 0.20 returns HTTP 400 'the input length exceeds the context length' above ~7000 chars for whitespace-heavy text and ~5000 for dense JSON. RAG layer chunks at 4000 chars with 500-char overlap to stay well under both limits.
  - Disposition: Documented in src/aho/rag/__init__.py docstring; future fine-grained chunking work is W3+ scope.
  - Target: 0.3.x
  - Source: 0.2.17 W2 D1 implementation experience
- **F-0.2.17-W2-003 — Llama3.2:3b mirrors source-artifact severity vocabulary**
  - Severity: info
  - Llama3.2:3b prefers severity vocabulary present in the audit target (e.g. 'moderate' from W1 carry-forward entries) over enum strings in the prompt. Required adding an explicit, exhaustive severity-synonym table to aho.council.audit. Unknown severity strings still raise (G083 preserved).
  - Mechanism: Small-model token-mimicry of source-artifact vocabulary under format=json constraint.
  - Disposition: Synonym table is documented and exhaustive in src/aho/council/audit.py SEVERITY_SYNONYMS. No further action. If a future audit target uses a severity word outside the synonym set, that's a real schema gap to surface.
  - Target: 0.3.x
  - Source: 0.2.17 W2 D10 W1 replay run

## Target: 0.2.17 W3

- **F-0.2.17-W2-006 — Auditor reference-resolution gap — llama systematically flags carry-forward / ADR / gotcha IDs as not-real-looking without registry access at audit time**
  - Severity: important
  - D9 produced novel false-positive finding (F-W0-004 not corroborated). D11 self-audit produced false-positive finding (F-0.2.17-W1-003 does not look real). Both IDs are in fact sealed and registered.
  - Mechanism: Llama at 32K context cannot fit full carry-forwards file + ADRs + gotcha registry alongside audit target. Without RAG-mediated retrieval, the auditor pattern-matches ID syntax and concludes 'looks like placeholder.'
  - Disposition: W3 must wire aho.rag.query into aho.council.audit prompt construction. Auditor retrieves 'is this ID registered?' via ChromaDB query before flagging reference-resolution issues. This is the RAG-as-context-feed for auditor seat from architecture artifact §Component decomposition (aho.rag feeds context to triage and audit).
  - Target: 0.2.17 W3
  - Source: 0.2.17 W2 D9 (W0 replay) + D11 (W2 self-audit)
  - Audit traceability: surfaced in W2 self-audit disposition (audit/W2.json sha b9c2f1bb...). Documented in W2 close note as drafter arbitration of D9 / D11 findings.
  - Status update at 0.2.17 W3 close: PARTIAL CLOSURE — stays OPEN per drafter arbitration. W3 D4 RAG-vs-non-RAG comparison (audit/replay/comparison-rag-vs-non-rag.json sha 3057c954...) closed 1 of 2 demonstrated false positives (W0 F-W0-004 closed; W2 self-audit F-0.2.17-W1-003 persisted). Architecture works in principle; small-model prompt-following inconsistency is the bottleneck. F-0.2.17-W3-001 (below) is the more-specific carry-forward that captures the residual problem and inherits as W4 work. F-0.2.17-W2-006 closes when F-0.2.17-W3-001 closes (W4 deterministic post-hoc filter — drafter-arbitrated path c).

## Target: 0.2.17 W4

- **F-0.2.17-W3-001 — Llama3.2:3b inconsistently honors the registered-references prompt rule**
  - Severity: important
  - D4 W2 self-audit re-run with RAG enrichment continued to flag F-0.2.17-W1-003 as 'ID does not look real (matches naming conventions)' even though the registered-references section listed it as `registered` with a snippet pointing to W1 acceptance archive. The W0 replay correctly stopped flagging F-W0-004; the W2 self-audit did not stop flagging F-0.2.17-W1-003. Same prompt rule, same context shape, same model, different outcome.
  - Mechanism: Small-model prompt-following inconsistency at base tier. Llama3.2:3b honors the registered-references rule on some prompts but not others — the rule is paragraph-form text at the end of a large system prompt, and the model selectively attends.
  - Disposition: Drafter selects path (c) deterministic post-hoc filter as the structural fix appropriate for base-tier auditor model. After llama emits a finding, a deterministic post-pass drops findings whose anchor IDs are listed `registered` in the prompt context AND whose description matches the fake-ID phrase set ('not real', 'looks placeholder', 'matches naming conventions', etc.). This closes the gap without relying on prompt-following on a small model. Architecture: same RAG context pipeline; new filter layer between the audit primitive's model output and the disposition return.
  - Target: 0.2.17 W4 — deterministic post-hoc filter on RAG-aware audit findings (drafter-arbitrated path c)
  - Source: 0.2.17 W3 D4 RAG-vs-non-RAG comparison
  - Audit traceability: surfaced in audit/replay/comparison-rag-vs-non-rag.json (sha 3057c954...) and consolidated in W3 D4 evidence inside acceptance/W3.json.

- **F-0.2.17-W3-002 — Plan-doc spurious-ID test token is not structurally detectable**
  - Severity: info
  - Plan doc D2 acceptance gate names `F-FAKE-9.9.9-W9-999` as the spurious test ID expected to return `unverified`. The carry_forward_full pattern requires digits after `F-`, so `F-FAKE-...` is not detected at D1 and therefore never reaches D2. F-9.9.9-W9-999 was substituted as the structurally-valid synthetic spurious token; gate semantics held.
  - Disposition: Document the substitution in any later replay. No code change needed.
  - Target: drafter awareness during W3 close-note authoring (this turn)
  - Source: 0.2.17 W3 D1/D2 implementation

## Target: 0.2.17 W5 retrospective fold-in OR 0.3.x base-tier hardening

- **F-0.2.17-W4-001 — ChromaDB iteration-context index does not auto-refresh on carry-forwards-0.2.16.md updates**
  - Severity: important
  - W4 D7 self-audit RAG enrichment showed F-0.2.17-W3-001, F-0.2.17-W3-002, F-0.2.17-W2-006 as status=unverified with top_source_artifact_path=null, despite all three being added in W2/W3 closes to carry-forwards-0.2.16.md. RAG retrieval operates against stale ChromaDB snapshot. Auditor flagged unverified-status correctly but the underlying state is misleading — those IDs ARE registered, the index just hasn't been rebuilt since W2 close indexed it.
  - Mechanism: gap_carry_forward_writer appends entries to carry-forwards-0.2.16.md but does not trigger ChromaDB re-index. The index built during W2 D1 pre-seed has not been refreshed since.
  - Disposition: Hook re-index into gap_carry_forward_writer's append path so any carry-forward addition triggers re-index of the source file. Alternative: schedule re-index pre-audit. Either approach closes the staleness.
  - Target: 0.2.17 W5 retrospective fold-in OR 0.3.x base-tier hardening
  - Source: 0.2.17 W4 D7 self-audit RAG enrichment state inspection
  - Audit traceability: Surfaced by D7 self-audit at audit/W4.json (sha 9d5ab9ec...). Three findings (F-0.2.17-W3-001, F-0.2.17-W9-999, F-0.2.17-W2-006) all show unverified status with null source path despite being registered in carry-forwards-0.2.16.md.

## Target: 0.3.x base-tier hardening

- **F-0.2.17-W5-001 — Structural pre-check self-referential pattern (third occurrence)**
  - Severity: important
  - Audit-target documentation prose that explicitly cites the regex patterns being checked (git-op tokens in Pillar 11 evidence; G081 banned phrases in celebratory-framing compliance check) gets flagged as compliance failure by the structural pre-checks. Manifests three times across the iteration (W3 D5, W4 D7, W5 D8).
  - Mechanism: Structural pre-checks scan the entire audit-target text including fields whose content is explicitly the pattern set being checked. Pre-check has no awareness that a token appearing inside a compliance-evidence field is documentation, not violation.
  - Disposition: Structural pre-checks need scope discrimination. Two implementation options: (a) JSON path exclusion in pre-check scan — skip fields tagged as compliance-evidence prose (e.g., pillar_11_invariant_check.evidence, celebratory_framing_check.banned_phrases_avoided). (b) Context-aware regex with negative lookbehind for evidence-field markers. Drafter recommends (a) — explicit and auditable. Approach (b) is fragile because lookbehind state varies with field shape.
  - Target: 0.3.x base-tier hardening
  - Source: 0.2.17 W3 D5 + W4 D7 + W5 D8 (three occurrences pattern-confirms)
  - Audit traceability: W3 D5 (audit/W3.json), W4 D7 (audit/W4.json), W5 D8 (audit/W5.json sha 5bd170e9...)
- **F-0.2.17-W6-001 — Audit-time lookup ranking misses opaque-ID matches in carry-forwards file**
  - Severity: important
  - audit_ref_lookup retrieves top-24 chunks by cosine similarity then filters to literal-ID-containing chunks. Opaque alphanumeric IDs (F-0.2.17-WN-NNN shape) carry low embedding signal; recency-weighting boosts current-iteration chunks over the 0.2.16 carry-forwards file; 158-chunk corpus has many higher-cosine competitors. The chunk containing the literal token IS in chromadb but does not rank top-24 -> status=unverified surfaces in audit RAG enrichment.
  - Mechanism: data IS in chromadb (chunk015 of carry-forwards-workstream chunks for the carry-forwards file path); lookup top-24 does not return it. Verified twice independently during W6 D2 live probe and W6 D3 halt-investigation. Empirical: lookup_references on text containing both F-0.2.17-W1-001 and F-0.2.17-W4-001 returns retrievals=3 for W1-001 (mentioned in W1-close-note.md + W2-plan-doc.md, separate artifacts) and retrievals=0 for W4-001 (mentioned only in carry-forwards file).
  - Disposition: Drafter recommends structural fix (c) - add ID-keyed metadata field at index time so direct lookup by ID-token avoids cosine entirely. Alternative options: (a) larger pool multiplier, (b) lower threshold floor - both statistical, less robust. Option (c) is structural and deterministic.
  - Target: 0.3.x base-tier hardening
  - Source: 0.2.17 W6 D3 self-audit
  - Audit traceability: W6 D3 (audit/W6.json sha bb7b1d1f...) F-0.2.17-W4-001 unverified finding + acceptance/W6.json deliverables[2].evidence.lookup_ranking_failure_mode


## Target: drafter chat-side process improvement + 0.3.x plan-doc convention notes

- **F-0.2.17-W5-002 — Plan-doc / repo-convention path drift**
  - Severity: info
  - W5 plan-doc specified docs/adr/ for new ADRs; repo convention is artifacts/adrs/. W4 close-note already pointed at artifacts/adrs/. Plan-doc D5/D6 path specs mostly aligned with existing repo convention but D1/D2/D3 did not.
  - Mechanism: Drafter (Claude web) wrote plan-doc paths from chat-side architecture-artifact convention rather than consulting actual repo state. Executor surfaced the drift in deliverable evidence (six findings during D8 audit are auditor correctly noting these surfaces).
  - Disposition: Future plan-docs should reference artifacts/adrs/ for ADRs, docs/architecture/ for architecture docs, docs/retrospectives/ for retrospectives. Drafter chat-side convention update needed. Executor surfaced rather than silent-picking — that part worked correctly.
  - Target: drafter chat-side process improvement + 0.3.x plan-doc convention notes
  - Source: 0.2.17 W5 D8 audit findings 0-5 (D1-D6 path-resolution surfaces)
  - Audit traceability: W5 D8 (audit/W5.json sha 5bd170e9...) findings indexed 0-5

## Target: 0.3.x base-tier hardening or earlier substrate fix

- **F-0.2.17-W6-002 — Council embed timeout default too tight under VRAM contention**
  - Severity: info
  - default AHO_COUNCIL_EMBED_TIMEOUT_S=30s in src/aho/council/embed.py is too short when nomic-embed-text cold-loads after qwen3.5:9b model swap on 8GB VRAM. Live probe required bump to 300s to complete chunked embedding of the 50KB carry-forwards file. Without the bump the reindex hook failure-handling path fires (warning + counter, append still succeeds) but no actual indexing occurs.
  - Mechanism: substrate condition (Ollama state hygiene + 8GB VRAM contention with co-resident large models - qwen3.5:9b at 7.4GB held by aho-nemoclaw or aho-openclaw user-service), not a council/embed defect. Same family as 0.2.15 substrate findings (cross-model cascades serialize on 8GB VRAM; Ollama state hygiene is infrastructure).
  - Disposition: Bump default in src/aho/council/embed.py from 30 -> 120 in 0.3.x or earlier substrate fix. The reindex hook degradation behavior is correct; only the default tightness is the concern.
  - Target: 0.3.x base-tier hardening or earlier substrate fix
  - Source: 0.2.17 W6 D2 live probe
  - Audit traceability: acceptance/W6.json deliverables[1].evidence.substrate_observation_during_probe_runs

## Target: 0.3.1 launch (early base-tier hygiene fix, ~5min including .gitignore edit + cached-untrack)

- **F-0.2.17-W6-003 — Working-state files tracked in git repo (gitignore gap)**
  - Severity: important
  - `.aho-checkpoint.json` and `.claude/settings.json` are git-tracked. `.dockerignore` correctly excludes them from container image layers, but `.gitignore` does not, so commits carry their state. Surfaced via `git ls-files .aho-checkpoint.json .claude` returning both paths and `git status --short` showing M flags on both during 0.2.17 iteration-close audit.
  - Mechanism: `.gitignore` lacks `.aho*` and `.claude*` patterns; only `__pycache__/`, `.venv`, and similar caught by current rules. `.dockerignore` has the full working-state exclusion list including `.aho-checkpoint.json`, `.aho.json`, `.claude`, `.claude-history`, `artifacts`, `MANIFEST.json` — `.gitignore` should mirror. Pillar 11 implication: none. No credentials, no decrypted secrets, no fernet/age material in tracked files. Build-hygiene smell, not a security incident.
  - Disposition: Add `.aho-checkpoint.json`, `.aho.json`, `.claude/`, `.claude-history`, `MANIFEST.json`, `projects.json` to `.gitignore` (mirror `.dockerignore` working-state list). Run `git rm --cached .aho-checkpoint.json .claude/settings.json` to untrack without local deletion. History scrub via `git filter-repo` optional; only meaningful if repo ever goes public — for current private SOC-Foundry/aho, scrubbing not required.
  - Target: 0.3.1 launch (early base-tier hygiene fix, ~5min including .gitignore edit + cached-untrack)
  - Source: 0.2.17 post-W6-close iteration-close audit (drafter chat-side)
  - Audit traceability: Not in any sealed audit archive — surfaced post-W6 close in chat. W6 close note signed by operator at 2026-05-04T05:12:27Z; this carry-forward post-dates the close.

## Target: 0.3.1 W1-W7 + 0.3.2+

- **F-0.3.1-W0-001 — Drafter substrate prerequisite gap — W0 prompt assumed inherited substrate without explicit pre-flight verification**
  - Severity: important
  - W0 prompt (drafter, claude-web) assumed a8cos had inherited NZXTcos's substrate via install.fish but did not include an explicit pre-flight substrate-verification step in the W0 sequence. Surfaced as chromadb-absent halt during D9 first invocation. The W0_audit.py template ported from 0.2.18 ran on NZXTcos host Python where chromadb was substrate-resident; a8cos host Python (python3.14) had no chromadb at session start.
  - Mechanism: Drafter authored W0 prompt without auditing a8cos's host Python dependency state. During arbitration, drafter retracted the W0 prompt's over-broad Pillar 11 interpretation: Pillar 11 scope is git operations only, plus secret decryption, /etc/sudoers, customer-lane crossings, hardware procurement, disruptive reboots. Substrate component installation is executor scope going forward across 0.3.1.
  - Disposition: Every future W prompt includes a D0 substrate-verification deliverable that probes required components (chromadb, ollama models present, broker socket, audit dependencies importable) before any other work. Drafter chat-side process improvement applied retroactively to remaining 0.3.1 workstreams (W1-W7) and canonical pattern for 0.3.2+. Structural closure via install.fish --check mode at W1/W2 substrate-freshness work.
  - Target: 0.3.1 W1-W7 + 0.3.2+
  - Source: 0.3.1 W0 D9 first-invocation halt (acceptance/W0.json sha ab37497914bb9b194e7434138bd88a9d3a1278185d1cb37dd11836983731a7ff deliverables[D9].initial_halt_record) + drafter arbitration 2026-05-24

## Target: 0.3.1 W1

- **F-0.3.1-W0-002 — ChromaDB iteration-context collection empty post-install; RAG enrichment returns all-unverified until bootstrap**
  - Severity: important
  - W0 D9 audit emitted with rag_enrichment.registered_count=0 against rag_enrichment.detected_count=26. ChromaDB importable (post-install) but collection contains zero documents. Every detected reference (D1-D9, ADR-0007/0009/0011/0012, F-0.2.17-* and F-0.2.18-* carry-forwards) returned status=unverified.
  - Mechanism: chromadb pip install creates the python module but does NOT ingest the canonical artifact set (carry-forwards-0.2.16.md, plan-docs, ADRs, close-notes) into the project collection. RAG enrichment in aho.council.audit_ref_lookup queries the empty collection and returns 0 hits per reference. Distinguishable from F-0.2.17-W6-001 (lookup-ranking-on-opaque-IDs) by: W6-001 returns SOME registered refs from a populated collection; W0-002 returns ZERO registered refs because the collection itself is empty.
  - Disposition: 0.3.1 W1 substrate-freshness scope expands to include `aho rag bootstrap` (or equivalent) deliverable that ingests the canonical artifact set on a fresh chromadb install. Closure verified when W1 self-audit RAG enrichment shows registered_count > 0 for known-registered IDs (e.g., F-0.2.17-W1-003).
  - Target: 0.3.1 W1
  - Source: 0.3.1 W0 D9 self-audit (audit/W0.json sha 9749cfed8fd5268e0facf36915459f616200e7c43de21ff778f75f9e83115e14 F1 finding 'ADR-0011 unverified status echo')
  - Audit traceability: audit/W0.json findings[1] id=ADR-0011 severity=important; rag_enrichment.unverified_count == rag_enrichment.detected_count == 26 (empty-collection signature)

## Target: 0.3.1 W1 (closed)

- **F-0.2.18-W1-004 — Substrate decoherence — closed by 0.3.1 W1 D4 telemetry implementation**
  - Severity: important
  - 0.2.18 W1: tailnet FQDN nzxtcos.tail78a311.ts.net baked into image at W0 probe time; tailnet rolled (a8 host rebuilt); seven days later W2 pre-flight tripped on stale FQDN; unscheduled image rebuild triggered. Closure target moved to 0.3.1 W1 substrate-freshness telemetry per ADR-0011 lightweight tier.
  - Mechanism: Closure: 0.3.1 W1 D4 ships src/aho/observability.py (record_observable, last_verified_age_seconds, snapshot_all_facts) + src/aho/substrate_probes.py (13 fact probes including tailnet_domain) + bin/aho-probe-substrate fish wrapper + OTEL gauge aho.observable.last_verified_age_seconds + dashboard /api/substrate JSON + /substrate HTML brick grid. Tailnet-FQDN closure invariant verified on a8cos: probe shows last_verified_age_seconds < 1h after fresh probe (tail8492.ts.net, the post-incident tailnet domain). install.fish step substrate_facts_probed_recently invokes the probe set when observables.jsonl mtime > 24h.
  - Disposition: Closed structurally. Re-decoherence detection now telemetry-driven: any stale fact older than its warning_age_seconds threshold surfaces in red on the dashboard brick grid + summary tile (stale_count > 0).
  - Target: 0.3.1 W1 (closed)
  - Source: 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D4] evidence
  - Audit traceability: D8 self-audit (audit/W1.json sha 3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d) rag_enrichment confirms F-0.2.18-W1-004 referenced and resolved during enrichment.
- **F-0.3.1-W0-001 — Drafter substrate-prerequisite gap — closed by 0.3.1 W1 D3 aho-doctor wrapper**
  - Severity: important
  - 0.3.1 W0 D9 first-invocation halt: drafter authored W0 prompt without auditing a8cos host Python dependency state. chromadb absent surfaced as halt-and-surface; drafter retracted over-broad Pillar 11 interpretation (git-only scope going forward) and authorized executor-side substrate component installation.
  - Mechanism: Closure: 0.3.1 W1 D3 ships bin/aho-doctor fish wrapper + bin/_aho_doctor_eval.py internal evaluator. Signature: aho-doctor --workstream W1|W2|W3 [--required-steps id_list] [--remediate] [--json]. Invokes install.fish --check, parses 19-step JSONL output, evaluates per-workstream required-step list, exits 0 if all pass / 1 if any fail / 2 if substrate-gap upstream / 3 if unknown workstream. Forward-only deployment: W2 first dogfoods at D0.
  - Disposition: Closed structurally. install.fish --check is the canonical pre-flight surface across every W's D0. Per-workstream required-step lists documented in aho-doctor source. W0 D9 chromadb-absent class of failure now caught structurally before any substantive work.
  - Target: 0.3.1 W1 (closed)
  - Source: 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D3] evidence + D8 drafter arbitration
  - Audit traceability: D8 self-audit referenced F-0.3.1-W0-001 in rag_enrichment registered set (20 of 28 detected refs resolved as registered including this one).
- **F-0.3.1-W0-004 — Canonical-root .aho-checkpoint.json absent — closed by 0.3.1 W1 D1 install.fish step**
  - Severity: important
  - 0.3.1 W0 workstream_complete emit: find_project_root() correctly returned ~/Development/Projects/socfoundry/aho but no .aho-checkpoint.json existed at that path. emit_workstream_complete's checkpoint-advance code path short-circuited on ckpt_path.exists() check (fail-soft); event landed in event log but per-workstream completion state did not advance. Legacy stale checkpoint at /home/kthompson/dev/projects/aho/.aho-checkpoint.json (mtime 2026-05-16, iteration=0.2.16, W2=in_progress) untouched.
  - Mechanism: Closure: 0.3.1 W1 D1 install.fish adds step canonical_checkpoint_present. Check: test -f $project_root/.aho-checkpoint.json. Remediation: python writer that generates initial-state checkpoint per existing schema (iteration / phase / run_type / current_workstream / workstreams / executor / auditor / started_at / status / proceed_awaited). Step runs after symlinks step; subsequent emit_workstream_complete invocations find the checkpoint and advance per-workstream state correctly.
  - Disposition: Closed structurally. .aho-checkpoint.json now present at canonical project root with current iteration (0.3.1) / current workstream (W1) / status=active. Future emit_workstream_complete invocations advance per-workstream state.
  - Target: 0.3.1 W1 (closed)
  - Source: 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D1] evidence + canonical_checkpoint_present step in install.fish


## Target: 0.3.1 W1 (closed; D8-verified)

- **F-0.3.1-W0-002 — ChromaDB collection empty post-install — closed by 0.3.1 W1 D2 bootstrap; D8-verified**
  - Severity: important
  - 0.3.1 W0 D9 self-audit emitted with rag_enrichment.registered_count=0 against detected_count=26. ChromaDB importable (post-install) but collection contained zero documents. Every detected reference returned status=unverified.
  - Mechanism: Closure: 0.3.1 W1 D2 ships bin/aho-rag-bootstrap fish wrapper + src/aho/rag/bootstrap.py Python module. Ingests canonical artifact set (carry-forwards files, plan-docs, close notes, iteration-close notes, ADRs, retrospectives) via existing aho.rag.index_artifact (upsert; idempotent). Subcommands: --dry-run / --rebuild / --json / --quiet. Bootstrap on a8cos: 52 of 53 artifacts indexed → 263 chunks; duration 175.9s; idempotent on re-run (263 → 263). install.fish step chromadb_collection_populated invokes the bootstrap as remediation.
  - Disposition: Closed structurally AND verified operationally. D8 self-audit on this very W1 acceptance archive emitted with rag_enrichment.registered_count=20 (vs 0 at W0 D9 with the same audit primitive). 20/28 detected refs resolved as registered with non-null top_source_artifact_path. F-0.2.17-W1-003 + F-0.2.18-W2-004 + F-0.3.1-W0-002 + F-0.3.1-W0-001 + F-0.2.18-W0-008 all queried directly post-bootstrap return status=registered.
  - Target: 0.3.1 W1 (closed; D8-verified)
  - Source: 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D2] evidence + D8 audit archive (sha 3a2c456d0f964ce94a26517eaf1e5b779f0521d0e0c29ce37cec1b3e79d4fe3d) rag_enrichment.registered_count=20
  - Audit traceability: D8 RAG enrichment shows 20 registered / 8 unverified out of 28 detected refs — the registered_count > 0 is the operational closure signal for this entry.

## Target: 0.3.1 W2

- **F-0.3.1-W0-003 — OTEL collector endpoint post-NZXTcos-decommission — W1 probe; W2 Beacon migration completes**
  - Severity: important
  - 0.3.1 W0 workstream_complete emit: OTLP span exports failed with StatusCode.UNAVAILABLE on 127.0.0.1:4317. NZXTcos decommissioned per CLAUDE.md §Deployment hosts; the OTEL collector substrate host moved off NZXTcos but no a8cos-local or alternate-host endpoint configured.
  - Mechanism: Partial closure in W1: D4 ships substrate fact #2 (otel_collector_endpoint) as a 1h-warn-age probe. The probe currently reports fail because no a8cos-local OTLP receiver is running yet. The probe itself is the W1 telemetry surface — visibility into endpoint-reachability state lives in observables.jsonl + dashboard. Full closure in W2 via Beacon migration.
  - Disposition: Partially closed in 0.3.1 W1 (probe + visibility). Full closure in 0.3.1 W2: extract beacon's otel/config.py + exporter.py + buffer.py pattern, copy into src/aho/observability/otlp_exporter.py, wire metrics + audit dispositions to beacon's gRPC endpoint over Tailscale per W2 plan-doc-amendment scope expansion Track 2 (Beacon integration) + Track 3 (OTEL endpoint migration). Fact #2 probe will flip from fail to ok post-W2.
  - Target: 0.3.1 W2
  - Source: 0.3.1 W0 close note + handoff brief observation 2 + 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D4] partial-closure section
- **F-0.3.1-W0-005 — Legacy sys.path drift in editable-install metadata — W1 probe; W2 pip install -e re-install completes**
  - Severity: important
  - 0.3.1 W0 D9 substrate probe surfaced sys.path includes /home/kthompson/dev/projects/aho/src (legacy pre-migration path). Editable install at ~/.local/lib/python3.14/site-packages/aho-0.2.18.dist-info direct_url.json points at file:///home/kthompson/dev/projects/aho (legacy). Imports resolve correctly because executor probe scripts do sys.path.insert(0, str(ROOT/'src')) before importing aho, but the editable-install metadata is stale.
  - Mechanism: Partial closure in W1: D4 ships substrate fact #13 (sys_path_clean) as a 1h-warn-age probe. The probe currently reports fail (legacy entry detected). install.fish step python_sys_path_clean is probe-only with no remediation defined — by design, W2 owns the remediation. Bin wrappers (aho-rag-bootstrap, aho-claw3d) work around in-band via PYTHONPATH prepending the canonical src/.
  - Disposition: Partially closed in 0.3.1 W1 (probe + visibility). Full closure in 0.3.1 W2 Track 4: pip install --user --break-system-packages -e ~/Development/Projects/socfoundry/aho re-installs editable pointing at canonical path; verify post-install sys.path no longer includes legacy /home/kthompson/dev/projects/aho/src. Fact #13 probe will flip from fail to ok post-W2; per-wrapper PYTHONPATH workarounds can be removed in a subsequent cleanup pass.
  - Target: 0.3.1 W2
  - Source: 0.3.1 W0 handoff brief observation 3 + 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D4] partial-closure section

## Target: 0.3.2 (peer to F-0.2.17-W6-001 retrieval-quality work) OR 0.3.1 W2 if chunking refinement is in scope (drafter to decide at W2 plan-doc-amendment time)

- **F-0.3.1-W1-001 — D2 ingestion skip — single artifact chunk exceeded nomic-embed-text size cap**
  - Severity: cosmetic
  - During 0.3.1 W1 D2 bootstrap, 52 of 53 canonical artifacts indexed successfully. 1 artifact skipped: artifacts/iterations/0.2.17/iteration-close-0.2.17.md chunk-5 (out of 6 chunks) failed embed with HTTP 400 Bad Request from Ollama /api/embed. Cause: chunk content exceeds nomic-embed-text effective input size cap. Other 5 chunks of the same file did index successfully.
  - Mechanism: aho.rag._chunk_text uses chunk_size=4000 with overlap=500. Per src/aho/rag/__init__.py docstring: nomic-embed-text in Ollama 0.20 caps around ~7000 chars for whitespace-heavy text and ~5000 for dense JSON. The 4000-char chunks usually fit but iteration-close-0.2.17.md chunk-5 evidently contained dense content that exceeded the embedder's tokenization budget. The bootstrap module's per-chunk try/except catches the embed failure, records the skip in result.skipped_paths, and continues — design works as intended.
  - Disposition: Cosmetic visibility item. The artifact is partially queryable (5 of 6 chunks indexed). Closure could be tighter chunk sizing (3000 with 500 overlap) at bootstrap time, OR a per-chunk size guard that splits oversized chunks further before embedding. Not a structural defect; not a blocker for D8 closure gates. Track for visibility.
  - Target: 0.3.2 (peer to F-0.2.17-W6-001 retrieval-quality work) OR 0.3.1 W2 if chunking refinement is in scope (drafter to decide at W2 plan-doc-amendment time)
  - Source: 0.3.1 W1 acceptance archive (sha 76047d7768ed98062eea421c3c9abef1ca3cdccafa40067419795c8615ccf7ba) deliverables[D2].evidence; bootstrap result.skipped_paths in run-1 JSON output
