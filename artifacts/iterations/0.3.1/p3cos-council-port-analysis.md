# p3cos council-port analysis (drafter review)

**Author:** claude-code (a8cos session, out-of-band council global-use wiring)
**Date:** 2026-05-27
**Audience:** drafter (claude-web), for fold-in to 0.3.1 plan-doc and ADR-0007 W6 amendment
**Status:** evidence-grounded recommendation. Operator approves architecture; drafter authors plan-doc amendment; operator commits.

---

## TL;DR

The council producer (qwen3.5:9b) and evaluator (GLM-4.6V-Flash-9B) cannot complete a dispatch on a8cos. The hardware ceiling - Ryzen iGPU, no discrete GPU, vram_gb=0 - is the binding constraint, not the wiring. Three empirical runs at progressively-tighter substrate budgets all failed at the producer stage. The architecturally honest fix, already captured as a 0.3.1 carry-forward, is to route the council's substantive produce/assess stages to p3cos (partial tier, RTX 2000 Ada 16 GB), keep base-tier hosts as orchestrators only, and make `aho-conductor dispatch` from any host reach p3cos's Ollama over the tailnet.

This document gives the drafter what they need to write the plan-doc workstream: evidence, scope, code changes, infra changes, transport decision, risks, and acceptance criteria. It also inventories what was applied out-of-band on a8cos so the drafter does not double-bill it.

---

## §1 Background: why this analysis exists

A new global rule landed in `~/.claude/CLAUDE.md` directing every Claude Code session, in every project, to route work through `aho-conductor dispatch "<task>"`. This made "the council reachable from any cwd, on a fresh login" the new acceptance bar. The work was out-of-band from 0.3.1's W0-W7 structure (no W covers it; the plan-doc has no mention of `aho-conductor`, `orchestrator.json`, or "global use").

The handoff prompt assumed pulling the council models on the local host would close the gap. Empirically, on a8cos it does not.

---

## §2 Evidence: three runs, three failure modes converging on the same finding

All three runs from `/tmp` (outside the repo), models pulled into host Ollama, council router fixes applied (router substring -> prefix-near-miss match; advisory-routing fallback in `conductor.dispatch`).

| # | Substrate budget | Outcome | Time | Failure mode |
|---|------------------|---------|------|--------------|
| 1 | qwen num_ctx 16384, GLM modelfile default (65 K), cold load | **TIMEOUT** | 900 s ceiling hit | Process killed by outer `timeout`; smoke stdout buffered + lost |
| 2 | qwen num_ctx 4096 + GLM num_ctx 4096 (tier-aware tuning applied) | **FAIL** | 15 m 36 s, exit 1 | `DegenerateGenerationError: Thinking repetition detected at token 2650, 924 s elapsed`. Uncaught -> traceback. |
| 3 | qwen num_ctx 4096 + GLM num_ctx 4096 + tier-gated `/no_think` prefix + `_COUNCIL_ERRORS` catches | **FAIL** | 13 m 38 s, exit 1 | `DegenerateGenerationError: Thinking repetition detected at token 2500, 808 s elapsed`. Clean one-line message via new exception handling. `/no_think` directive **ignored** by this Ollama qwen3.5:9b variant. |

### §2.1 Per-stage warm probe (isolation)

To separate "wiring works" from "hardware fits," I ran each stage in isolation on warm models, short prompt, num_ctx 4096:

| Stage | Model | Time | Output |
|-------|-------|------|--------|
| route | nemotron-mini:4b | 3.5 s | `'reviewer'` (correct after router prefix-match fix) |
| produce | qwen3.5:9b | 110.0 s | `'This is my one-sentence confirmation.'` (correct) |
| assess | GLM-4.6V-Flash-9B | 64.8 s | `'{"score": 8, "recommendation": "approve", "issues": []}'` (correct) |

**Total warm = ~178 s.** Each model loads and produces correct, parseable output on toy prompts. The functional wiring is correct. The producer falls over only when given the conductor's real workstream prompt (workstream wrapper + project-context preamble + JSON request), because qwen3.5 engages thinking mode and the CPU + iGPU substrate cannot drive it to convergence before the thinking detector fires.

### §2.2 Why this is a hardware ceiling, not a tuning gap

- a8cos: AMD Ryzen 9 8945HS, Radeon 780M iGPU. `~/.config/aho/tier.json` reports `tier=base, vram_gb=0`. Ollama runs all inference on CPU.
- 9 B parameter model on CPU runs at roughly 3 tokens/second on this class of silicon.
- qwen3.5 with thinking mode wants to emit 1000-3000 thinking tokens before opening producer output. 1000 tokens * 0.3 s/token = 300 s just for the thinking pass, with enough wall-clock to drift into repetition before convergence.
- `/no_think` is documented in `dispatcher.py` `MODEL_FAMILY_CONFIG["qwen"]` comments and `artifacts/council-models-0.2.14.md` as a contingency lever. This Ollama community build (`qwen3.5:9b`, ID `6488c96fa5fa`) does not honor it.
- GLM never had a chance to fail or succeed in the full flow; qwen blocked the path. Per the isolated probe, GLM at 4096 ctx returns 65 s. Unknown whether GLM on the conductor's actual eval prompt (with design + plan + output payloads) fits in any reasonable budget on this CPU; almost certainly not within today's 180 s hardcoded glm_client timeout once cold-load cost is included.

### §2.3 What this evidence does NOT support

- It does not show the council code is broken. The wiring is correct, the models compatible, the structured-output contract works (GLM returned valid JSON, score 8, recommendation approve).
- It does not show qwen3.5 / GLM are broken models. They are documented in `council-models-0.2.14.md` as appropriate for partial-tier compute (and GLM is calibrated for an 8 GB discrete GPU via `num_gpu=30` partial offload in `dispatcher.py`).
- It does not show the global-use rule was a bad idea. The rule's contract ("council produces work; orchestrating agent integrates") is sound; the council just needs to live where it can produce.

---

## §3 Target: why p3cos

Per CLAUDE.md (project-instructions section "Deployment hosts" and "Auditor seat per host"):

- p3cos: Lenovo ThinkStation P3 Ultra SFF G2, Intel Core Ultra 9 285, NVIDIA RTX 2000 Ada **16 GB**. `tier=partial`. **`qwen3.5:9b` is already its declared auditor seat.**
- a8cos: base tier, vram_gb=0. Declared auditor seat `llama3.2:3b`. Already on disk.
- x9cos: base tier, intermittent. Same posture as a8cos.

The carry-forward this analysis is grounded in (CLAUDE.md, "Arising in 0.3.1, architectural, important, fold into ADR-0007 W6 amendment") makes this orthogonality explicit: **base hosts orchestrate, partial hosts produce/evaluate.** p3cos is not a new dependency; it is the documented partial-tier compute and 0.3.1 W3 already scopes its deployment.

What p3cos brings:
- 16 GB VRAM. qwen3.5:9b at Q4_K_M occupies ~9 GB; GLM at ~8.5 GB. Both fit simultaneously with margin only if loaded carefully (or sequentially via Ollama's keep_alive eviction). At 16 GB, expect either single-model-at-a-time, or partial offload for one of them.
- GPU tokens/sec roughly 10x CPU on this model class. qwen3.5 with full thinking pass becomes seconds, not minutes.
- Ollama keep_alive can keep the working set warm between dispatches; cold-load cost amortizes across requests.

What p3cos does not yet have (drafter to confirm against p3cos's own state):
- Confirmed `~/.config/aho/tier.json` shape on p3cos (W2 install.fish refactor is supposed to have written this; W3 should verify).
- Council models pulled. CLAUDE.md declares `qwen3.5:9b` as the seat; the full council roster (qwen + GLM + nemotron + llama3.2) may or may not be pulled. The drafter should add a verification step to the W3 plan-doc.
- Ollama HTTP API bound on the tailnet interface (default Ollama binds 127.0.0.1).

---

## §4 The port itself: scope, in plain terms

Two paths converge:

### §4.1 Tailnet-bound Ollama on p3cos (RECOMMENDED transport)

Standard pattern. p3cos's `ollama.service` is overridden to set `OLLAMA_HOST=0.0.0.0:11434` (or, narrower, the tailscale0 interface). Tailscale ACL restricts which tags can reach `p3cos:11434`. a8cos / x9cos / future engineer hosts post to `http://<p3cos-tailnet-fqdn>:11434/api/chat` and `/api/generate` exactly as the existing client code does today against 127.0.0.1.

Why this beats the alternatives:
- **Versus a custom "council gateway" daemon on p3cos:** zero new protocol, zero new code to maintain. The three Ollama client files (`dispatcher.py`, `qwen_client.py`, `glm_client.py`) already speak the right HTTP shape; they just need a configurable endpoint.
- **Versus extending the unix-socket nemoclaw/openclaw daemons across hosts:** unix sockets do not cross hosts. Would need a TCP wrapper plus protocol. Higher surface area.
- **Versus Beacon:** Beacon is notification + remote trigger, not the data plane.

### §4.2 Endpoint configurability in the three client files

All three Ollama clients currently hardcode the endpoint:

| File | Constant | Value |
|------|----------|-------|
| `src/aho/pipeline/dispatcher.py` | `OLLAMA_BASE` | `"http://127.0.0.1:11434"` |
| `src/aho/artifacts/qwen_client.py` | `OLLAMA_URL` | `"http://localhost:11434/api/generate"` |
| `src/aho/artifacts/glm_client.py` | inline literal | `"http://localhost:11434/api/generate"` |

Replace each with a single source of truth in `aho.orchestrator_config`:

```python
# orchestrator_config.py - sketch, drafter to ratify
def get_ollama_base() -> str:
    """Resolve the Ollama HTTP endpoint for this host's council role.

    Precedence:
      1. AHO_OLLAMA_BASE env var (operator override; wins always)
      2. orchestrator.json `ollama.base` (per-host config)
      3. tier-derived default: base-tier hosts return the partial-tier
         peer's tailnet endpoint (from orchestrator.json `ollama.peer`);
         partial/full-tier hosts return http://127.0.0.1:11434.
      4. Hard fallback: http://127.0.0.1:11434
    """
    ...
```

This keeps the cross-host route configurable per deployment (a8cos points at p3cos; x9cos points at p3cos; p3cos points at itself), and falls back to local for any host that does not have a peer configured (e.g., NZXTcos, partial+ hosts).

### §4.3 Tier-aware client behavior already on a8cos (keep)

The same-day tuning that landed on a8cos out-of-band stays in - it is the **right behavior for a base-tier host running an embedded auditor (llama3.2:3b)**, even after the producer/evaluator route moves to p3cos:

- `aho.orchestrator_config.get_host_tier()` - reads tier.json.
- `aho.orchestrator_config.get_tier_num_ctx()` - base-tier context cap for the auditor.
- `aho.orchestrator_config.get_tier_glm_ctx_override()` - keep for completeness; on base hosts the evaluator routes off-host post-port, so this becomes inert on base. Do not remove; partial hosts keep `None` (modelfile default), which is correct.
- `aho.agents.openclaw.OpenClawSession.__init__(..., num_ctx=...)` - same.
- `aho.artifacts.glm_client.generate(..., num_ctx=...)` - same.
- `aho.agents.roles.workstream_agent.WorkstreamAgent.execute_workstream` tier-gated `/no_think` prefix - **inert on partial hosts** (thinking returns), inert on a8cos once routing to p3cos lands (the producer is no longer local). Safe to keep as a substrate-conscious default; drafter may choose to remove the `/no_think` line in the W6 ADR amendment since it did not work and may mislead.

### §4.4 What the drafter should NOT undo

These shipped out-of-band on a8cos this session and are independent of the port:

1. Router prefix-near-miss matching in `_match_category` (`src/aho/pipeline/router.py`). Fixes "review" -> "reviewer" classifier near-misses generally, not specific to this port.
2. Advisory-routing fallback in `conductor.dispatch` (catches `DispatchError` from `nemoclaw.route`, falls back to default role, continues to produce+assess). Defends against any future classifier flake.
3. Project-context-aware dispatch: cwd / `.aho.json` / git-status captured, prompt-prefixed, artifact written to `<cwd>/aho-output/council-dispatch-<ts>.json`. This is the actual "global routing mechanism between project folders" deliverable. **Survives the port unchanged** - the only change is where the HTTP calls land.
4. `smoke()` rewritten to assert on real pipeline output (role, non-empty producer, parseable score+rec, written artifact, event-log spans). The marker-file assertion in the old smoke was impossible (workstream is chat-only). Survives port unchanged.
5. Clean `_COUNCIL_ERRORS` exception handling in `smoke()` and `main()`. Survives port unchanged.
6. `docs/operations/council-global-use.md` - operations doc. Needs **update** post-port (a section on cross-host transport + how to configure the endpoint) but the structure stays.
7. CLAUDE.md carry-forward entry under "Arising in 0.3.1." Status updates from "carry-forward" to "in-flight" when W3 picks this up; closes when smoke green on p3cos.

---

## §5 Required changes, categorized

### §5.1 Code changes (drafter authors plan-doc; operator commits)

| Change | File(s) | Effort | Notes |
|--------|---------|--------|-------|
| Add `get_ollama_base()` and per-host endpoint config | `src/aho/orchestrator_config.py` | S | New function; env > config > tier-derived |
| Replace `OLLAMA_BASE` hardcode | `src/aho/pipeline/dispatcher.py` | S | Read from `get_ollama_base()` at module load or per-call |
| Replace `OLLAMA_URL` hardcode | `src/aho/artifacts/qwen_client.py` | S | Same |
| Replace inline endpoint | `src/aho/artifacts/glm_client.py` | S | Same |
| Add `peer` field to orchestrator.json shape | `src/aho/orchestrator_config.py` `_DEFAULTS` | S | New schema field |
| `aho council status` to surface the resolved endpoint | `src/aho/council/status.py` | S | Health-check shows where dispatch lands |
| Tier-aware default fallback (base -> peer endpoint required, fail fast if unset) | `orchestrator_config.get_ollama_base()` | S | Prevents silent fall-through to a CPU-only loopback |
| Smoke assertion that the dispatch landed off-host on base | `src/aho/agents/conductor.py` `smoke()` | S | Optional; assert resolved endpoint differs from 127.0.0.1 when tier=base |

All small. None of these are architectural rewrites; they're moving a hardcoded constant behind a helper with a clear precedence.

### §5.2 Configuration changes (per-host, operator)

| Host | File | Change |
|------|------|--------|
| a8cos | `~/.config/aho/orchestrator.json` | add `"ollama": {"base": null, "peer": "http://<p3cos-tailnet-fqdn>:11434"}` (peer becomes the default base on base-tier) |
| x9cos | `~/.config/aho/orchestrator.json` | same |
| p3cos | `~/.config/aho/orchestrator.json` | add `"ollama": {"base": "http://127.0.0.1:11434"}` (local) |
| p3cos | `~/.config/aho/tier.json` | verify `tier=partial`, `bundle` includes the council roster |

Drafter to decide whether to ship a `bin/aho-orchestrator-config` subcommand that writes these declaratively, or leave them as manual edits documented in `docs/operations/council-global-use.md`.

### §5.3 Infrastructure changes (operator + hardware-side; Pillar 11)

These are **operator actions**, not agent actions. Drafter to list them in the W3 plan-doc as graduation gates so they get tracked.

| Action | Host | Operator action |
|--------|------|-----------------|
| Set `OLLAMA_HOST` to bind tailscale interface | p3cos | systemd override on `/etc/systemd/system/ollama.service.d/override.conf`; `Environment=OLLAMA_HOST=0.0.0.0:11434` (or narrower: just the tailscale0 IP). Restart. |
| Tailscale ACL | tailnet admin | Grant `tag:engineer-host` -> `tag:council-host:11434`. Tag p3cos as `tag:council-host`. |
| WARP exclusion if needed | p3cos | Verify CloudflareWARP does not intercept the tailscale0 path (recurrence surface for F-0.2.16-host-001 / 0.2.17 W0). |
| Pull council models on p3cos | p3cos | `ollama pull qwen3.5:9b nemotron-mini:4b haervwe/GLM-4.6V-Flash-9B:latest llama3.2:3b nomic-embed-text` (latter two confirm; may already be present). |
| Verify VRAM headroom | p3cos | Run `aho-models vet` on p3cos; confirm all four respond. Document Ollama keep_alive behavior under the 16 GB VRAM ceiling (qwen + GLM together exceeds 16 GB; expect serial loading or partial offload). |
| `aho council status` from a8cos shows p3cos endpoint healthy | a8cos | After above, `aho council status` from a8cos should report ollama_models reachable. |

### §5.4 Plan-doc / iteration discipline (drafter)

- This work folds into **W3** ("p3cos partial-tier deployment + qwen3.5:9b auditor seat") as either a sub-deliverable ("council remote dispatch from base hosts") or a new W (e.g., W3.5 "Council global-use cross-host routing").
- Update CLAUDE.md carry-forward status from "applied out-of-band on a8cos" to "in flight as W3 sub-deliverable" when the drafter writes the plan-doc amendment.
- ADR-0007 W6 amendment adds the **tier-role orthogonality**: VRAM tier and council-role tier are not the same axis. Base hosts can orchestrate without producing; partial hosts can produce without orchestrating.
- Acceptance archive (`acceptance/W3.json`) gets a new evidence field for council remote-dispatch verification: `aho-conductor smoke` from a base host succeeds, with the resolved Ollama endpoint logged.

---

## §6 Cross-host transport: details for the drafter

### §6.1 Endpoint resolution precedence (proposed)

```
AHO_OLLAMA_BASE env var         (operator one-shot override)
  -> orchestrator.json `ollama.base`   (per-host explicit)
  -> orchestrator.json `ollama.peer`   (tier-derived: base hosts use this)
  -> http://127.0.0.1:11434             (last-resort local fallback)
```

On base-tier hosts, `peer` is the operative knob. If unset, the dispatch fails cleanly at `get_ollama_base()` (raise an explicit `ConfigError` or fall back to local with a loud warning - drafter to choose; I lean toward fail-fast on base to prevent the silent-CPU-fallback that wasted a8cos cycles today).

### §6.2 Authentication / authorization

Per operator's standing direction on the Beacon thread (in this session, reinforced): **Tailscale ACL + WARP posture compliance are the auth gates.** No app-layer bearer tokens. Ollama's HTTP API does not have native auth, which is normally a problem; it is fine here because the tailnet is the perimeter.

This means:
- Ollama on p3cos binds to the tailscale interface, not the public LAN.
- Tailscale ACL restricts which tags can reach `p3cos:11434`.
- No `OLLAMA_API_KEY` or equivalent in code or config.

### §6.3 Latency expectation

a8cos (Tailnet IP `100.124.234.113`) and p3cos (`100.84.122.100`) are both on `tail8492.ts.net`. Same-LAN RTT on a wired tailnet is typically <2 ms; even if WARP rewraps, single-digit ms. Compared to a >100 s on-CPU inference, transport overhead is rounding error.

### §6.4 Failure modes to handle gracefully

| Failure | Behavior |
|---------|----------|
| p3cos offline | `requests.ConnectionError` from `qwen_client` / `glm_client`. Already caught by `_COUNCIL_ERRORS` (`requests.RequestException`). Smoke / dispatch return clean message. |
| Tailscale degraded | Same as above. |
| Ollama on p3cos unreachable (running on wrong interface) | Same. |
| p3cos VRAM exhausted (qwen + GLM together exceed 16 GB) | Ollama serializes loads; partial offload for GLM (already calibrated via `num_gpu=30` for an 8 GB GPU; drafter to recalibrate for 16 GB). |
| First dispatch cold-load | p3cos loads from disk; expect a one-time cold-load overhead per model. `aho-conductor smoke` warm path becomes the SLO measurement. |

### §6.5 Cross-host audit dispatch (out of scope here)

Distinct from "council producer/evaluator routing to p3cos." Cross-host audit dispatch (executor on p3cos dispatches audit calls against another partial-tier host's Ollama) is a 0.3.2+ candidate per CLAUDE.md. This port does not preempt that work; both can coexist.

---

## §7 Risks and open questions for the drafter

1. **VRAM headroom on p3cos under concurrent qwen + GLM.** 16 GB is below the sum of the two models. Ollama's keep_alive + serial-load behavior should handle this, but the per-dispatch latency on p3cos with eviction churn is unknown until measured. Drafter should add a measured-latency probe to the W3 acceptance archive (`route + produce + assess` warm and cold on p3cos).
2. **Does the existing GLM `num_gpu=30` partial-offload calibration in `dispatcher.py` still apply at 16 GB?** The comment dates from 8 GB-GPU work; almost certainly suboptimal at 16 GB. Drafter to add a recalibration probe to W3.
3. **p3cos online availability.** If p3cos is rebooted / disconnected, every Claude Code session on a8cos loses the council. Document this in the operations doc, and consider whether to fall back to local llama3.2:3b for trivial dispatches as a degraded mode (drafter to decide; I lean against to preserve the contract honesty - degraded != council).
4. **Identity / lane discipline for the cross-host call.** The HTTP client on a8cos has no per-call identity. Ollama on p3cos sees only the source tailnet IP. That is acceptable under the Tailscale-as-perimeter posture; document it in the operations doc so it does not look like an oversight later.
5. **`bin/aho-models` `install` reads `tier.json.bundle`.** On base hosts the bundle does not include qwen + GLM. **This is correct** (a8cos should not host them in the architecture end state). For the same-day unblock we have them on a8cos; the drafter should decide whether to keep them pulled (useful for dev/test fall-back) or unpull (storage hygiene + tier-purity). I lean toward keep-pulled-but-unused for the duration of W3; remove from a8cos at W3 close.
6. **`/no_think` is dead code on base hosts** after the port (producer no longer runs on base). Decision: drop the WorkstreamAgent tier-gated prefix in the W6 ADR amendment, or keep it for future base-tier dev/test scenarios. Either is defensible.
7. **OTLP collector at 127.0.0.1:4317.** On a8cos, the collector is not running, so every dispatch from any project folder spews `Failed to export traces` warnings on stderr. Not blocking, but ugly for global use. Out of scope for this port; flag for an operations follow-up: either run the collector locally or set `AHO_OTEL_DISABLED=1` per-deployment.

---

## §8 Acceptance criteria for "council ports to p3cos"

Per `aho-conductor smoke` running from `/tmp` on a8cos:

1. **Routing landed off-host.** `get_ollama_base()` resolves to a p3cos tailnet endpoint, not 127.0.0.1.
2. **Smoke exit 0** within a 600 s ceiling (vs the 1800 s budget we needed on a8cos's CPU). Warm dispatch should be <30 s on GPU.
3. **Structured assertions hold:** role classified, workstream produced non-empty output, evaluator returned a parseable numeric score + recommendation, artifact written to `/tmp` (or, for `aho-conductor dispatch`, into `<cwd>/aho-output/`), event-log recorded the spans.
4. **Failure mode tested.** With p3cos network-isolated (operator pulls the tailscale interface or stops the unit), `aho-conductor smoke` from a8cos returns a clean one-line `FAIL:` message via `_COUNCIL_ERRORS`, exit 1, no traceback.
5. **`aho council status` from a8cos** reports the resolved Ollama endpoint and that it is reachable. Drafter adds a new field if not present.
6. **Sealed in `acceptance/W3.json`** (or wherever the workstream lands) with cold + warm latency measurements and the resolved-endpoint evidence.

---

## §9 What was applied out-of-band on a8cos this session (inventory)

So the drafter can fold these into the plan-doc amendment without re-billing or re-justifying:

**Source files modified (uncommitted; operator commits):**
- `src/aho/pipeline/router.py` - `_match_category` now handles prefix-near-miss in addition to substring. Resolves the "review" -> "reviewer" classifier flake. Used only by `nemoclaw.route`; blast radius contained.
- `src/aho/agents/conductor.py` - `dispatch()` is project-context-aware (cwd, .aho.json, git, artifact writeback); routing is advisory (falls back to `assistant` on `DispatchError` instead of aborting); `smoke()` rewritten to assert on real pipeline output; `_COUNCIL_ERRORS` tuple for clean exception handling in `smoke()` / `main()`.
- `src/aho/orchestrator_config.py` - added `get_host_tier()`, `get_tier_num_ctx()`, `get_tier_glm_ctx_override()`. Reads `~/.config/aho/tier.json`.
- `src/aho/agents/openclaw.py` - `OpenClawSession.__init__` accepts `num_ctx`; defaults to tier-derived.
- `src/aho/artifacts/glm_client.py` - `generate()` accepts `num_ctx`; defaults to tier-derived (base sets 4096, partial/full leaves modelfile default in place).
- `src/aho/agents/roles/workstream_agent.py` - tier-gated `/no_think` prefix on base hosts (empirically ineffective; drafter to decide whether to keep or drop in W6).

**Documentation added (uncommitted):**
- `docs/operations/council-global-use.md` - new operations doc. What runs, how it starts at login, model requirements, health-check. Tier-aware context-window section was appended.
- `CLAUDE.md` - new carry-forward entry under "Arising in 0.3.1 (architectural, severity: important; fold into ADR-0007 W6 three-axis amendment)." Captures the empirical finding and points at this analysis.

**Substrate state changed on a8cos (no rollback needed):**
- Council models pulled into host Ollama: `qwen3.5:9b` (6.6 GB), `nemotron-mini:4b` (2.7 GB), `haervwe/GLM-4.6V-Flash-9B:latest` (8.0 GB). `llama3.2:3b` was already present. Disk impact ~17 GB; 800+ GB still free. Drafter may decide to unpull after W3.

**Nothing committed.** Pillar 11 holds. Operator commits if/when the drafter folds these into the W3 plan-doc amendment.

---

## §10 Sensitive content posture

This document references hostnames (a8cos, p3cos, x9cos), tailnet (`tail8492.ts.net`), Tailscale IPs, hardware specifics (RTX 2000 Ada, Ryzen 9 8945HS), and tier facts. Per CLAUDE.md Rule 3, it lives in `artifacts/iterations/0.3.1/`, which is `.gitignore`'d under "Iteration record." It must not be copied into public-repo files (README, ADRs in `artifacts/adrs/`, `docs/`, source code, install.fish) without scrubbing to generic role-shaped identifiers.

The public-facing operations doc (`docs/operations/council-global-use.md`) intentionally uses generic language ("the host," "partial-tier hosts") rather than the names here.

---

## §11 Asks of the drafter

1. **Decision: fold this work into W3 directly, or open a new W (e.g., W3.5 / W3-followup) for council global-use cross-host routing.** Both are defensible; I lean toward a new W because the global-use rule is itself out-of-band and W3's current scope is partial-tier deployment + auditor seat, not cross-host dispatch wiring.
2. **Decision on `/no_think` line in `workstream_agent.py`:** keep as future-proof default, or remove since it does not work on this Ollama variant.
3. **Decision on a8cos model retention:** keep qwen + GLM pulled on a8cos for dev / test fall-back, or unpull as part of W3 close.
4. **Decision on the failure-mode posture:** if p3cos is unreachable, dispatch returns a clean error (current behavior). Should there ever be a base-local degraded fall-back? My recommendation: no.
5. **ADR-0007 W6 amendment scope:** confirm that "tier-role orthogonality" (VRAM tier vs council-role tier as separate axes) is the right framing, or refine.
6. **Plan-doc amendment authoring:** drafter takes this report, writes the W3 (or W3.5) plan-doc paragraph + graduation criteria + acceptance gates + halt-and-surface conditions, per ADR-0006.

---

## §12 One sentence for the operator's signature line, when the drafter is ready

"Council producer/evaluator dispatch routes to p3cos partial-tier compute via tailnet-bound Ollama; a8cos and x9cos stay base-tier orchestrators with the llama3.2:3b auditor seat; `aho-conductor` resolves the Ollama endpoint via `orchestrator.json` peer with `AHO_OLLAMA_BASE` env override; Tailscale ACL is the auth boundary, no app-layer auth."

---

End of analysis.
