# aho Quantum Posture Page — design assessment

**Date:** 2026-05-16 (drafted overnight after 0.2.18 W2 conversation)
**Audience:** Kyle, building the Flutter version on a8cos tomorrow.
**Status:** Design exploration. Mockup at `mockup-quantum-campus.html` (sibling file). Not yet bound to an iteration.

---

## TL;DR

- **What you're building:** a campus-wide observability landing page that frames endpoint posture as an open-quantum system per the conversation in `artifacts/aho-quantum.md` + `artifacts/aho-quantum-web.md`. Operator sees a campus-aggregate `⟨H⟩ ± σ` at the top, a grid of per-host cards in the middle (each with its own miniature wave-packet), and a drill-down detail panel at the bottom when a host is selected.
- **What you're NOT building:** a Jaeger replacement or a Grafana competitor. Jaeger handles raw traces; Grafana would handle generic metrics. This page is the *posture* surface — it's the single screen an operator opens to know "is my campus coherent right now, and if not, what should I re-measure."
- **Integration target:** the existing `web/claw3d/` Flutter app. New route, not a fork. Reuses the Trident palette for chrome; the posture panels lean on the quantum demo's monospace/teal aesthetic for visual continuity with the artifact you already saved.
- **Why now:** F-0.2.18-W1-004 is the exact failure mode this page exists to prevent — substrate facts decohering between capture and use. Today we found out by trying to use a stale `tail78a311.ts.net` from a W0 probe that was 7 days old. A campus posture page surfaces that staleness *before* the attempt-to-use rebuilds the image.

---

## 1. Scope

### In scope

- Single screen / route. Loads in <1s on localhost, polls in background.
- Multi-host campus: all current tailnet members (nzxtcos, a8cos, p3cos, dkcos, x9cos, catchy-truvis). Future hosts (tsP3 in 0.3.1, future cloud nodes in 0.3.2) join without code changes — host list is data, not code.
- Per-host observable categories:
  1. **Services** — systemd units the aho substrate depends on (otel-collector, jaeger, dashboard, nemoclaw, openclaw, telegram, ollama, tailscale)
  2. **Network posture** — ufw state + rules, listening ports vs baseline, tailnet reachability, DNS/MagicDNS health
  3. **Certificates** — TLS cert expiry, gateway CA freshness, Tailscale `.ts.net` cert freshness
  4. **Secrets posture** — age key present, broker socket up, fernet bundle integrity, token-rotation freshness per token
  5. **Container substrate** — podman version present, aho image present, image FQDN matches current tailnet, broker mount path exists
  6. **OTEL meta** — collector reachable, last trace age, last metric age, ufw rule for 4317 on tailscale0
- Decoherence model per observable: `p(t) = c + (1 − c) · e^(−Δt/τ)` per the agreed math.
- Campus aggregate `⟨H⟩` and `σ` rendered as wave-packet over time (the quantum demo's centerpiece, but aggregated across hosts).
- Manual scan trigger (per-host and campus-wide).
- Synthetic drift injector for demo / training.

### Out of scope

- Real OTLP trace exploration (Jaeger already does this; the page links to it).
- Generic metric exploration (cost.usage, token counts — already handled by `/api/otel`).
- Configuration mutation. The page is read + measure, never write. Pillar 11 is unchanged: it doesn't run git, push to ghcr, set secrets, or close iterations.
- Auth UI. Tailscale Serve at `https://nzxtcos.tail8492.ts.net/` is the privacy envelope. If we ever Funnel-expose this page publicly, *then* we add auth — and that's a separate ADR.

### Pointer to source thinking

- `artifacts/aho-quantum.md` — my prior summary of where the quantum framing maps cleanly and where it doesn't.
- `artifacts/aho-quantum-web.md` — the longer mentor-style write-up with the original HTML demo embedded. Read sections "State representation," "The score as an expectation value," "Be honest about what kind of uncertainty this is," and "Decoherence is the part that genuinely fits" — those four are the load-bearing claims this page commits to.

---

## 2. Domain model

### The campus

Six tailnet members, distinct roles:

| Host | Role | Container target? | Auditor seat? | Notes |
|---|---|---|---|---|
| `nzxtcos` | central collector, dashboard, Jaeger, OTLP receiver | yes (substrate today) | yes (W0/W1 audits) | The hub. Highest criticality weight. |
| `a8cos` | second container host (0.2.18 W2) | yes (deployment in progress) | yes (planned W3) | Mid weight. New substrate. |
| `p3cos` | ThinkStation P3, future partial-tier (0.3.1) | yes (future) | yes (qwen3.5:9b candidate) | Future weight; today, monitoring-only. |
| `dkcos` | David's machine | no | no | External / collaborator. Visibility-only. |
| `x9cos` | tagged-device | unknown | no | Low weight in posture, presence-tracked. |
| `catchy-truvis` | Travis's machine | no | no | Often offline; weight ~0 when offline. |

The page must handle three host classes:
- **Substrate hosts** (nzxtcos, a8cos, p3cos): full observable set + heavy weight in campus aggregate.
- **Peer hosts** (dkcos, x9cos): presence + reachability + tailscale-side metadata only. Light weight.
- **Offline / sparse hosts** (catchy-truvis): visible but greyed; not aggregated into `⟨H⟩` while offline.

Host list is data, populated from `tailscale status --json` parse. New hosts auto-appear when they join the tailnet.

### Observable structure

Each observable carries (recap from the quantum artifacts):

| Field | Meaning |
|---|---|
| `id` | stable identifier |
| `nm` | human label |
| `host` | which host it lives on |
| `category` | services / network / certs / secrets / container / otel |
| `w` | criticality weight |
| `τ` (tau) | coherence time — how fast belief decays back to base rate |
| `c` | equilibrium base rate (steady-state compliance probability) |
| `last_outcome` | last *measured* value (0/1) |
| `last_scan_t` | timestamp of last measurement |

Live belief: `p(t) = c + (last_outcome − c) · e^(−(t − last_scan_t) / τ)`

Per-host aggregate:
- `⟨H⟩_host = Σ wᵢ · pᵢ / Σ wᵢ` (for observables on this host)
- `σ_host = √(Σ wᵢ² · pᵢ(1−pᵢ)) / Σ wᵢ`

Campus aggregate (weighted by host class):
- `⟨H⟩_campus = Σ Wh · ⟨H⟩_host / Σ Wh` (host weights Wh)
- `σ_campus = √(Σ Wh² · σ_host²)` (Wh-weighted RSS of host variances)

Aggregating variances as RSS treats hosts as independent — fine for now; if we ever model shared-CA or shared-config dependencies as correlation, the math changes. Not needed for v1.

### Observable catalog — concrete starting set

This is the v1 set the mockup uses. Real τ values are hand-set per the quantum artifact's two-extensions note ("natural extension if you want them: ... wiring the model to real telemetry where each check's τ is fit from its observed flip rate rather than hand-set"). Tune later.

**Services** (per host, weight 8–10 for substrate hosts):

| id | nm | τ | c | notes |
|---|---|---|---|---|
| `svc.otel-collector` | otel-collector service active | 45s | 0.98 | systemd polling fast |
| `svc.jaeger` | jaeger-all-in-one active | 60s | 0.97 | |
| `svc.dashboard` | aho-dashboard active | 60s | 0.96 | |
| `svc.nemoclaw` | aho-nemoclaw active | 60s | 0.95 | |
| `svc.openclaw` | aho-openclaw active | 60s | 0.95 | |
| `svc.telegram` | aho-telegram active | 90s | 0.90 | tokens can rot |
| `svc.tailscale` | tailscaled active | 30s | 0.99 | foundation |
| `svc.ollama` | ollama active (if installed) | 60s | 0.92 | absent on hosts that don't run it |

**Network** (per host, weight 7–9):

| id | nm | τ | c | notes |
|---|---|---|---|---|
| `net.ufw` | ufw enabled | 600s | 0.98 | rarely changes |
| `net.ports-baseline` | listening ports match baseline | 90s | 0.92 | drift-sensitive |
| `net.tailnet` | tailnet reachable from this host | 30s | 0.99 | fast probe |
| `net.magicdns` | MagicDNS resolves canonical names | 180s | 0.95 | NM/resolved can break |
| `net.ufw-otlp-rule` | inbound 4317/tcp on tailscale0 allowed (collector hosts only) | 600s | 0.99 | nzxtcos-specific |

**Certificates** (per host, weight 6–8):

| id | nm | τ | c | notes |
|---|---|---|---|---|
| `cert.system-tls-bundle` | /etc/ssl/certs CA bundle intact | 1800s | 0.99 | very stable |
| `cert.ts-net-cert` | tailscale serve `.ts.net` cert not expired | 3600s | 0.98 | LE auto-renews |
| `cert.gateway-ca` | Cloudflare Gateway CA present (tachtech hosts only) | 1200s | 0.97 | env-specific |

**Secrets posture** (per host, weight 9–10):

| id | nm | τ | c | notes |
|---|---|---|---|---|
| `sec.age-key` | age identity at expected path | 1200s | 0.99 | stable |
| `sec.broker-socket` | SO_PEERCRED broker socket up | 120s | 0.95 | per ADR-0009 |
| `sec.fernet-bundle` | encrypted bundle present + decryptable | 600s | 0.97 | |
| `sec.tg-token-rotation` | telegram bot token rotated <90 days | 86400s | 0.85 | slow decay; F-0.2.17-W1-003 lesson |
| `sec.ssh-keys-on-disk` | SSH private keys only at expected paths | 1800s | 0.99 | grep-scan for `BEGIN OPENSSH/RSA/EC PRIVATE KEY` outside `~/.ssh` |

**Container substrate** (substrate hosts only, weight 7–9):

| id | nm | τ | c | notes |
|---|---|---|---|---|
| `ctr.podman-present` | podman binary on PATH | 300s | 0.99 | the gap that bit us on a8cos rebuild |
| `ctr.image-present` | `aho:0.2.18` loaded | 600s | 0.95 | |
| `ctr.image-fqdn-coherent` | image OTEL endpoint FQDN matches current tailnet | 300s | 0.90 | **catches F-0.2.18-W1-004** |
| `ctr.broker-mount-path` | broker mount path exists | 600s | 0.98 | |
| `ctr.tier-json` | `~/.config/aho/tier.json` matches host_id + tier | 600s | 0.95 | |

**OTEL meta** (substrate hosts, weight 5–7):

| id | nm | τ | c | notes |
|---|---|---|---|---|
| `otel.collector-bind` | collector binds Tailscale interface, not loopback | 300s | 0.95 | **what we just fixed in W2** |
| `otel.last-trace-age` | newest trace <60s old | 30s | 0.92 | flow heartbeat |
| `otel.last-metric-age` | newest metric <60s old | 30s | 0.92 | |
| `otel.last-log-age` | newest log <120s old | 60s | 0.90 | |

**Total v1 set:** ~30 observables × 6 hosts = ~180 observables, but many are host-class-specific (peer hosts only have a handful). Realistic count: ~80–100 live observables campus-wide.

### Probe responsibility

Each observable has a probe — the code that determines its current value. Three patterns:

- **Self-probe (local):** the host runs its own probe via `aho posture probe <id>` (planned subcommand) and emits the outcome as an OTEL event. Most network / service / container observables fit here.
- **Central probe (NZXTcos reaches out):** NZXTcos's posture-aggregator runs the probe against the remote host via Tailscale-SSH or HTTP. Useful for reachability + cert validation from another vantage. Few observables, but important for "is this host actually reachable" coverage.
- **Synthetic (no probe):** for the mockup. Computed from a hidden ground-truth flag that drifts on its own.

The page itself is **render-only** — it never runs probes. It reads outcomes from a posture state document.

---

## 3. Layout options

Three concrete layouts to consider, with tradeoffs. Recommended at end is a hybrid.

### Option A: Matrix / Periodic-table

```
┌──────────────────────────────────────────────────────────────────┐
│  HOST       │ SVCS │ NET  │ CERT │ SEC  │ CTR  │ OTEL │ ⟨H⟩ host │
├─────────────┼──────┼──────┼──────┼──────┼──────┼──────┼──────────┤
│  nzxtcos    │ ████ │ ████ │ ███▒ │ ████ │ ████ │ ████ │  97 ±1.2 │
│  a8cos      │ ███▒ │ ████ │ ████ │ ██▓░ │ ▓▓░░ │ ▓░░░ │  62 ±8.4 │
│  p3cos      │ ████ │ ████ │ ████ │ ████ │  —   │ ████ │  94 ±2.0 │
│  dkcos      │  —   │ ███▒ │  —   │  —   │  —   │  —   │  88 ±5.1 │
│  x9cos      │  —   │ ████ │  —   │  —   │  —   │  —   │  92 ±3.0 │
│  catchy     │  —   │ ░░░░ │  —   │  —   │  —   │  —   │  offline │
├─────────────┴──────┴──────┴──────┴──────┴──────┴──────┴──────────┤
│  campus ⟨H⟩ 89.4 ±5.2  •  coherence 73%  •  next scan in 18s     │
└──────────────────────────────────────────────────────────────────┘
```

**Pros:** dense, scannable, all hosts and all categories visible at once. Click a cell → drill into the (host, category)'s observables. Scales linearly with hosts.

**Cons:** static. The quantum framing is reduced to a number per cell — the wave-packet visualization (the whole reason we're doing this) is invisible. Time-decoherence isn't shown unless the cell color animates.

### Option B: Constellation / Hub-and-spoke

```
                            ╭────────╮
                            │ a8cos  │
                            │ ⟨H⟩ 62 │
                            ╰───┬────╯
                                │ rx 4724 tx 5860
              ╭────────╮        │
              │ p3cos  │────────┤        ╭────────╮
              │ ⟨H⟩ 94 │        │        │ x9cos  │
              ╰────────╯  ╭─────┴─────╮  │ ⟨H⟩ 92 │
                          │  nzxtcos  │──╯ ⟨H⟩
                          │  HUB      │
                          │  ⟨H⟩ 97   │
              ╭────────╮  ╰─────┬─────╯  ╭────────╮
              │ dkcos  │────────┤        │ catchy │
              │ ⟨H⟩ 88 │        │        │ offline│
              ╰────────╯        │        ╰────────╯
                                │ tailscale relay
                            ╭───┴────╮
                            │ tsP3   │
                            │ future │
                            ╰────────╯
```

**Pros:** visually arresting, conveys "campus" topology, makes the collector's hub-role legible. Per-host orbs can pulse / glow to indicate posture. Good demo-mode aesthetic.

**Cons:** lower information density than the matrix; no time-decoherence visible without overlaying mini wave-packets on each orb; harder to scan many hosts. Burns pixels on the negative space between orbs.

### Option C: Stacked wave-packets

```
┌──────────────────────────────────────────────────────────────────┐
│  CAMPUS    ⟨H⟩  ●●●●●●▒▒▒▒▒▒░░░░░▒▒▒▒▒▒●●●●●●●●●●●●●▒▒▒▒▒▒░░░    │
│            89.4 ±5.2                                              │
├──────────────────────────────────────────────────────────────────┤
│  nzxtcos   ⟨H⟩  ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●  │
│            97 ±1.2                              [observables ▶]   │
├──────────────────────────────────────────────────────────────────┤
│  a8cos     ⟨H⟩  ●●●●●●▒▒▒▒▒▒▓▓▓▓▒▒▒░░░░▒▒▒▓▓▒▒▒▒▒░░░░░░░░░░░░    │
│            62 ±8.4   ⚠ degrading                [observables ▶]   │
├──────────────────────────────────────────────────────────────────┤
│  p3cos     ⟨H⟩  ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●▒▒▒  │
│            94 ±2.0                              [observables ▶]   │
├──────────────────────────────────────────────────────────────────┤
│  ...                                                              │
└──────────────────────────────────────────────────────────────────┘
```

**Pros:** direct extension of the quantum demo. Time-decoherence visible per host. Wave-packets are the centerpiece. Vertical scanning maps to host inventory.

**Cons:** vertical scroll for many hosts; doesn't show topology relationships; large pixel cost per host card. Harder to spot which host owns which broken observable without expanding each card.

### Recommended: Hybrid

The matrix is best for triage ("which (host, category) is amber?"). The constellation is best for narrative ("show me a campus"). The stacked wave-packets are best for the quantum framing ("show me coherence over time"). A good single screen has all three at different scopes.

```
┌─────────────────────────────────────────────────────────────────────┐
│  CAMPUS  ⟨H⟩ 89.4 ±5.2  •  coherence 73%  •  hosts 5/6 online       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  [wave-packet — campus ⟨H⟩ ± σ over the last 2 min]         │    │
│  │  ground-truth dotted line • measurement collapse markers    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  [● RUN CAMPUS SCAN] [⚡ INJECT DRIFT] [⏸ PAUSE] [cadence 25s]      │
├─────────────────────────────────────────────────────────────────────┤
│  HOSTS                                                              │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐      │
│  │ nzxtcos │ a8cos   │ p3cos   │ dkcos   │ x9cos   │ catchy  │      │
│  │  ⟨H⟩ 97 │  ⟨H⟩ 62 │  ⟨H⟩ 94 │  ⟨H⟩ 88 │  ⟨H⟩ 92 │ OFFLINE │      │
│  │  ±1.2   │  ±8.4 ⚠ │  ±2.0   │  ±5.1   │  ±3.0   │  17h    │      │
│  │ [mini wave-packet per host — 60s window]                          │
│  │ [coherence ring around ⟨H⟩ number — 1.0 = freshly measured]      │
│  └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘      │
│  [selected: a8cos]                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  a8cos OBSERVABLES                                  [● SCAN HOST]   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ SERVICES (Σw 38, ⟨H⟩ 0.81, σ 0.08)                    [▼]   │   │
│  │  • otel-collector   ████████████░░░░  78%   Δ 12s            │   │
│  │  • jaeger           ███████████████░  92%   Δ  8s            │   │
│  │  • dashboard        ░░░░░░░░░░░░░░░░  12%   Δ 45s   ⚠ stale  │   │
│  │  • nemoclaw         ███████████████░  93%   Δ 12s            │   │
│  │  ...                                                          │   │
│  │ NETWORK (Σw 35, ⟨H⟩ 0.94, σ 0.04)                      [▶]  │   │
│  │ CERTIFICATES (Σw 18, ⟨H⟩ 0.97, σ 0.01)                 [▶]  │   │
│  │ SECRETS (Σw 42, ⟨H⟩ 0.42, σ 0.18) ⚠                   [▼]  │   │
│  │  • age-key         ███████████████░  99%   Δ 120s            │   │
│  │  • broker-socket   ░░░░░░░░░░░░░░░░   8%   Δ 240s   ⚠ broken │   │
│  │  • fernet-bundle   ███████████████░  97%   Δ 120s            │   │
│  │  • tg-token-rotn   ████████████░░░░  76%   Δ 8h              │   │
│  │  ...                                                          │   │
│  │ CONTAINER SUBSTRATE (Σw 28, ⟨H⟩ 0.55, σ 0.12) ⚠       [▼]  │   │
│  │  • podman-present  ████████████████  99%                     │   │
│  │  • image-present   ████████████████  99%                     │   │
│  │  • image-fqdn-coh  ████░░░░░░░░░░░░  28%   Δ 7d  ⚠ STALE     │   │
│  │  ...                                                          │   │
│  │ OTEL META (Σw 22, ⟨H⟩ 0.88, σ 0.06)                    [▶]  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Why this works:**

- The **campus aggregate** at top is the singular "how am I doing right now" number plus its uncertainty. The wave-packet makes time-decoherence load-bearing visually.
- The **host grid** acts as an attention router. Color + size of the per-host card pulls the eye to whichever host is in trouble. Mini wave-packets per host preserve the quantum framing at a glance.
- The **observable drill-down** is the actionable layer. Grouped by category (collapsible), shows the per-observable belief decoherence, surfaces the stale ones (Δ time-since-scan) as warning glyphs.
- The constellation idea is preserved as a *style* choice on the host grid — orbs / glow / pulse can be applied to host cards rather than going full hub-and-spoke.

The matrix is recoverable from the host grid via "expand all" or a separate route at `/campus/matrix` — keeps it available without dominating the landing.

---

## 4. Data flow architecture

### Phase A — Mockup (today)

Everything synthetic. In-browser JS computes `p(t)` per observable, drives the visualization. Hidden ground truth drifts on its own. INJECT DRIFT button breaks a random observable. Scan button collapses observables back to their true state. No backend, no aho dependencies — open the HTML and it works.

This is the mockup at `mockup-quantum-campus.html`.

### Phase B — Real backend, single-host first

New endpoint on the existing dashboard: `GET /api/posture`. Returns:

```json
{
  "generated_at": "2026-05-17T03:30:00Z",
  "campus": {"agg_h": 0.894, "sigma": 0.052, "coherence": 0.73},
  "hosts": [
    {
      "id": "nzxtcos",
      "online": true,
      "host_weight": 10,
      "agg_h": 0.97, "sigma": 0.012, "coherence": 0.91,
      "observables": [
        {
          "id": "svc.otel-collector",
          "nm": "otel-collector service active",
          "category": "services",
          "w": 9, "tau": 45, "c": 0.98,
          "last_outcome": 1,
          "last_scan_t": "2026-05-17T03:29:45Z"
        },
        ...
      ]
    },
    ...
  ]
}
```

The backend reads from a **posture state document** at `~/.local/share/aho/posture/state.json`, written by per-host posture-emitters (Phase C). Until emitters exist, dashboard backend synthesizes from existing signals:

- Services: parse `systemctl --user list-units` output
- Network: parse `ufw status` (sudo) + `ss -tlnp` + `tailscale status`
- Container: `podman images`, `podman inspect aho:0.2.18`, check FQDN env vs current `tailnet status` MagicDNS suffix
- OTEL meta: tail `~/.local/share/aho/{traces,metrics,logs}/*.jsonl` for age
- Secrets posture: file-existence checks on broker socket, fernet bundle path; token-rotation needs a separate "last rotated at" record (TBD)

Single-host backend lands first. Cross-host (Phase C) follows.

### Phase C — Posture emitters per host

Each substrate host runs `aho posture daemon` (new subcommand, planned). Daemon:

1. Reads `~/.config/aho/posture-probes.json` (declarative probe list).
2. Runs each probe at its declared cadence (cadence ≤ τ/3 typically).
3. Emits each outcome as a structured OTEL log record:
   ```
   event_name = "aho.posture.observable"
   attributes = {
     host: <hostname>, observable.id, observable.category,
     observable.weight, observable.tau, observable.c,
     observable.outcome (0/1), observable.measured_at (epoch s)
   }
   ```
4. Records flow through the OTEL collector (which we just opened to the tailnet in 0.2.18 W2).

NZXTcos's dashboard backend tails the collector's logs file, builds the campus state document, exposes it at `/api/posture`. Page polls every 2s.

This is the **right place** for the existing collector substrate to do real work — the OTLP path we proved end-to-end tonight is what carries posture signals between hosts.

### Phase D — Density-matrix fleet view (the "natural extension")

The quantum artifact called this out as a future extension. Concretely: replace per-host state-vector aggregation with a density matrix `ρ` that captures correlations between hosts (e.g., shared CA, shared config-management source, common ISP). Diagonal of ρ is the classical host postures we already aggregate; off-diagonals encode correlated-failure-mode estimates. UI changes: an additional pane showing ρ as a heatmap, where bright off-diagonals mean "if these two go red together, it's because of the same root cause." This is 0.4.x or later. Mockup doesn't include it.

---

## 5. Integration with the existing `web/claw3d/` Flutter app

### What's there now

- `web/claw3d/lib/main.dart` — 602 lines, single-file. Polls `/api/state` every 5s and `/api/otel` every 2s. Renders components, daemons, traces. Material 3 dark theme with the Trident palette (`kBackground #161B22`, `kShaft #0D9488 teal`, `kAccent #4ADE80 green`).
- Built artifacts at `web/claw3d/build/web/`. Dashboard server serves these for `/`.
- Single-route app — no `MaterialApp.routes`, no go_router.

### Integration plan

**Add a route, don't replace.** The existing dashboard view is valuable for the per-host current-iteration / per-workstream view. Posture is a new page.

1. **Add go_router** (or just plain `Navigator` with named routes) — `web/claw3d/lib/main.dart` is currently single-page. Adding a router is a 30-line change.
2. **Top nav bar** (existing, looks like the dashboard title — extend to a `Row` of three nav buttons):
   - `Substrate` (current dashboard at `/`)
   - `Posture` (new at `/posture`)
   - `Traces ↗` (link out to `https://nzxtcos.tail8492.ts.net/` — opens Jaeger in new tab)
3. **`lib/posture/posture_page.dart`** — the new page. Three widgets:
   - `CampusHeroPanel` — aggregate `⟨H⟩ ± σ` + wave-packet (custom `CustomPainter`)
   - `HostGrid` — `Wrap` of `HostCard` widgets
   - `HostDetailPanel` — observable categories as `ExpansionTile`s
4. **`lib/posture/posture_model.dart`** — the decoherence math, pure Dart. Mirror of the HTML mockup's `prob(ck)` / `posture()` / `coherence()`.
5. **`lib/posture/posture_api.dart`** — `Future<CampusPosture> fetchPosture()` hits `/api/posture`. Until backend exists, returns synthetic data with the same shape (a `mockBackend` flag).
6. **Reuse Trident palette** for chrome (nav, surfaces). **Borrow quantum demo palette** (`#39e6cf` teal, `#9d8cff` violet for ground-truth, `#f4b145` amber for warnings) for the wave-packet and posture-specific accents. The mockup file shows the blend.

### Flutter-specific implementation notes

- **`CustomPainter` for the wave-packet.** Direct port of the canvas math in `mockup-quantum-campus.html`. Use `Path` for the band + estimate trace + truth dotted line. ~200 lines of Dart.
- **State management:** for v1, `ChangeNotifier` + `Provider` is enough. The model is a single `CampusPostureState` with a tick timer; widgets `Consumer<CampusPostureState>` and rebuild on tick. No need for Riverpod / BLoC at this size.
- **Polling vs streaming:** Phase B polls `/api/posture` every 2s — same cadence as `/api/otel` today. Phase C can move to WebSocket if we want sub-second updates, but 2s is fine for posture (the decoherence τ values are seconds-to-hours; 2s polling is well-resolved).
- **Synthetic mode:** the model layer should accept either a real `/api/posture` response OR a synthetic generator. The mockup shows the generator behavior. Wire `kMockBackend = true` for local dev without the backend live.

### File layout (suggested)

```
web/claw3d/lib/
├── main.dart                      # nav setup + route table
├── theme.dart                     # palette consts (extracted from main.dart)
├── dashboard/                     # the existing page, move from main.dart
│   ├── dashboard_page.dart
│   └── ...
└── posture/                       # new
    ├── posture_page.dart          # top-level page widget
    ├── posture_model.dart         # decoherence math
    ├── posture_api.dart           # /api/posture client + synthetic fallback
    ├── widgets/
    │   ├── campus_hero_panel.dart
    │   ├── host_grid.dart
    │   ├── host_card.dart
    │   ├── host_detail_panel.dart
    │   ├── observable_row.dart
    │   └── wave_packet_painter.dart
    └── ...
```

---

## 6. Phasing

| Milestone | Deliverable | Time | Blocking? |
|---|---|---|---|
| **M0 (done)** | This design doc + the HTML mockup at `mockup-quantum-campus.html` | — | review tomorrow morning |
| **M1** | Flutter `/posture` route with synthetic backend; renders the layout end-to-end with the decoherence math live | ~1 day on a8cos (your build session) | non-blocking — runs against synthetic data |
| **M2** | `GET /api/posture` endpoint on the dashboard backend; nzxtcos-only (single host) probes against existing signals (systemctl, ss, tailscale, podman, file checks) | ~1 workstream | needs M1 deployed |
| **M3** | `aho posture daemon` per-host emitter + multi-host aggregation in dashboard backend | ~1 iteration | needs OTEL collector cross-host (done in W2) + M2 |
| **M4** | Density-matrix fleet view (correlation-aware aggregation) | 0.4.x charter | needs M3 stable + correlation model |

The page is **shippable at M1 with synthetic data** — it's already useful as a training tool and a vision document, even before real signals flow. Real signals come incrementally in M2/M3.

---

## 7. Open questions to decide before coding

1. **Per-host τ values: hand-set vs observed.** The quantum artifact called out "wiring the model to real telemetry where each check's τ is fit from its observed flip rate." Initial v1 should hand-set (the catalog above). Auto-tuning is a 0.4.x consideration once we have enough probe history.

2. **What goes in the host weight Wh?** The campus aggregate weights hosts by `Wh`. Some options:
   - All hosts equal: simplest, but a `dkcos` problem matters as much as an `nzxtcos` problem
   - Substrate hosts heavy: `nzxtcos = 10, a8cos = 8, p3cos = 6, others = 2` — preserves the "what matters for aho is what's running aho"
   - Role-derived: derive Wh from the role tag in tailscale's metadata
   - **Recommendation:** substrate-heavy (option 2) for v1. Document as a tunable.

3. **Posture state document format.** JSON at `~/.local/share/aho/posture/state.json` (single source of truth, atomically rewritten by the aggregator) vs append-only JSONL (history-preserving, larger). **Recommendation:** atomic JSON for current state + a separate JSONL for the historical observation log. Two files, two purposes.

4. **Authentication when funnel-exposed.** Today the page is tailnet-only via `tailscale serve`. If we ever Funnel-expose it (public internet), we need auth. The quantum demo's lack of auth isn't a regression — it's a feature of the tailnet-only deployment. Worth a sentence in the README, not blocking.

5. **What counts as a "campus scan"?** A manual scan in the demo collapses all observables instantly. In reality, a real campus scan would dispatch probes to every host in parallel, wait for results (or timeout), and collapse what came back. The UI needs to handle partial results (some hosts probed, others timed out → coherence ring half-filled). **Recommendation:** v1 button issues per-host probes in parallel via a single POST `/api/posture/scan` with `{hosts: ["nzxtcos", "a8cos", ...]}`. Backend returns immediately; observable updates flow via the normal polling.

6. **Where do probes physically live?** Two options:
   - **In the aho python package:** `aho.posture.probes.<id>` modules implementing a `probe() -> bool` interface. Easy to test, standard layout.
   - **As shell scripts in `bin/posture-probes/`:** Operator-readable, OS-coupled, easier to add ad-hoc probes.
   - **Recommendation:** Python modules for the canonical set + a wrapper that can shell out to `bin/posture-probes/<id>.fish` for ad-hoc additions. Both paths return the same `(outcome: bool, measured_at: float)` shape.

7. **Integration with iteration close.** Should iteration close trigger a campus posture probe + record the coherence in the iteration close-package? **Strong yes** — this is the F-0.2.18-W1-004 lesson made structural. If iteration close requires `campus_coherence ≥ 0.85`, you can't close on stale facts. Worth its own ADR after M2 lands.

---

## 8. How to review

1. Read this doc top-to-bottom (~15 min).
2. Open the mockup: `xdg-open artifacts/observability/mockup-quantum-campus.html` (or load via `file://` in your browser). 
3. **Try this sequence in the mockup:**
   - Watch for 30s — the wave-packet band is tight after the initial scan
   - Hit `INJECT DRIFT` — a random observable breaks. The campus `⟨H⟩` stays flat, the σ band widens. (This is the F-0.2.18-W1-004 mode visible.)
   - Wait another 30s — the band keeps widening, the per-host card with the broken observable starts to show staleness markers
   - Click the affected host — the observable category that's degrading expands; you can see which specific observable is drifting
   - Hit `RUN CAMPUS SCAN` — band collapses to a node, all observables show their current true state
4. Reactions / disagreements / what's missing — open the questions in §7. The mockup is a discussion artifact; the design is intentionally flexible.

## 9. Followup actions for tomorrow (a8 build session)

- **Decide:** layout = hybrid (recommended) vs one of the pure options A/B/C
- **Decide:** §7 questions 1–7 above (most have a recommended answer; just confirm or counter)
- **Build:** M1 — Flutter route + synthetic backend. Should compile + render end-to-end. Use the mockup as the visual contract.
- **Defer:** real backend (M2) and per-host emitters (M3) — those are subsequent workstreams, not the morning's a8 work.

---

*Drafted overnight 2026-05-16. Mockup file is the sibling at `mockup-quantum-campus.html`.*
