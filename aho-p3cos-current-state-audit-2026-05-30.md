# aho Repository Current-State Audit — p3cos Checkout

**Date of audit:** 2026-05-30  
**Checkout location:** `/home/kthompson/Development/Projects/socfoundry/aho` (p3cos)  
**Git HEAD:** `00c9264` — "KT COMPLETED 0.3.1 & updated README" (origin/main)  
**Claimed VERSION file content:** `0.2.14` (materially stale)  
**Purpose:** Objective snapshot of this working tree prior to deletion so the operator can compare against the "updated repo built together on nzxtcos" after clone. Focus is on completeness, fidelity between documentation and implementation, and risk of missing data or code.

This report is deliberately constructively critical. It treats the codebase as a governed engineering artifact under its own Pillars and Adversarial Authorship standards.

---

## 1. Git Provenance & Working Tree Integrity

| Aspect                  | Observation |
|-------------------------|-------------|
| Remote                  | `git@github.com:SOC-Foundry/aho.git` (only remote) |
| Branch                  | `main`, up-to-date with `origin/main` at start of session |
| Latest commit           | `00c9264` (0.3.1 completion + README) |
| Prior commits (this tree) | Multiple "KT completed 0.3.1" and "WIRED BEACON" commits in the last day |
| Uncommitted changes     | 2 modified (Dockerfile, GEMINI.md, some artifacts/iterations/0.3.1, src/aho/agents/roles/harness_agent.py), 1 added artifact screenshot, several untracked files (new 0.3.2 plan, beacon smoke scripts, debug txt) |
| Staged                  | Two screenshots (one in root, one in artifacts/) |
| VERSION file            | Contains `0.2.14` — inconsistent with all recent commits and docs claiming 0.3.1 |

**Critical note:** The VERSION file has not been updated in any of the 0.3.x work visible in this tree. This is a low-severity but persistent hygiene failure against the project's own "three octets" discipline.

---

## 2. Iteration & Sealed Archive State

### 0.3.1 (claimed early close at W2)
- **iteration-close-0.3.1.md** exists and is substantial.
- Sealed workstreams: W0, W1, W2 all have `acceptance/W*.json` + `audit/W*.json` + close-notes.
- **p3cos-council-port-analysis.md** (the substrate-pivot evidence document) is present and detailed.
- Carry-forward inventory is documented in the close note.
- **.aho-checkpoint.json** (on disk in tree) shows `iteration: "0.3.1"`, `current_workstream: "W2"`, both W1/W2 marked `workstream_complete`.

**Status:** The sealed artifacts for the three delivered workstreams appear complete for 0.3.1.

### 0.3.2
- Only `aho-plan-0.3.2.md` (marked DRAFT, W0 deliverable) exists.
- No acceptance/audit archives, no close notes, no W* artifacts.
- Plan correctly references the 0.3.1 substrate-pivot carry-forwards and the four deferred audit-machinery items from 0.2.18.

### Older iterations (0.2.x)
- Many plan/design/build-log/report/bundle/close artifacts present through 0.2.18.
- Only one retrospective in `docs/retrospectives/` (`0.2.17.md`).
- Several high-value internal artifacts correctly gitignored per policy (`artifacts/tt-*.md`, `artifacts/0.*-drafter-context.md`, top-level `2605*.md`, `CLAUDE.md`, `GEMINI.md`, etc.).

**Gap:** Retrospective coverage is extremely thin relative to the number of closed iterations.

---

## 3. Ollama Model Fleet & Cross-Host Wiring — The Largest Single Gap

This is the most load-bearing area of divergence between documented intent (0.3.1 close + p3cos-council-port-analysis.md) and on-disk implementation.

### Declared Fleet (authoritative)
`artifacts/harness/model-fleet.txt` (read by `bin/aho-models`):
- `qwen3.5:9b`
- `llama3.2:3b`
- `haervwe/GLM-4.6V-Flash-9B:latest`
- `nemotron-mini:4b`
- `nomic-embed-text` (added in tier logic)

### Actual Implementation Status of Cross-Host Transport

**The function `get_ollama_base()` described in detail in `artifacts/iterations/0.3.1/p3cos-council-port-analysis.md` §4.2 and §5.1 does not exist anywhere in the source tree.**

Confirmed zero matches for:
- `get_ollama_base`
- `AHO_OLLAMA_BASE`
- `ollama.peer`
- `ollama.base` (as config key)

All primary Ollama client surfaces still contain hard-coded localhost endpoints:

| File | Hardcoded Value | Client Role | Notes |
|------|------------------|-------------|-------|
| `src/aho/pipeline/dispatcher.py:79` | `http://127.0.0.1:11434` | Council (audit/triage/embed + model hygiene) | Used by `council.dispatch` |
| `src/aho/artifacts/qwen_client.py:22` | `http://localhost:11434/api/generate` | Producer (WorkstreamAgent / OpenClaw) | Core of `aho-conductor dispatch` |
| `src/aho/artifacts/glm_client.py:51` | `http://localhost:11434/api/generate` | Evaluator (GLM vision) | Tier ctx override exists but endpoint does not |
| `src/aho/artifacts/nemotron_client.py:67,148` | `http://localhost:11434/api/generate` | Legacy classifier | Router prefers dispatcher but this remains callable |
| `src/aho/rag/archive.py:30` | `http://localhost:11434/api/embeddings` | Old embedding path | Inconsistent with modern `/api/embed` |
| `src/aho/rag/query.py:23` | env `OLLAMA_URL` default `http://localhost:11434/api/embed` | RAG queries | Different env var than council's `OLLAMA_BASE_URL` |

Council clients (`council/_client.py`, `audit.py`, `triage.py`, `embed.py`) respect `OLLAMA_BASE_URL` env var — this helps containers but provides no cross-host story for base hosts.

### Council Dispatch Routing Table (src/aho/council/dispatch.py)

`ROUTING_TABLE` contains **only base-tier entries**:
- `("structural_audit", "audit", "base")` → `llama3.2:3b`
- Triage and embed routes for base

No entries exist for:
- `("structural_audit", "audit", "partial")` → should be `qwen3.5:9b`
- Any producer or evaluator shapes at partial tier

`ESCALATE_AT_BASE` correctly lists substantive drafting shapes, but the partial-tier positive routes are absent. The council cannot yet dispatch the 9B producer/evaluator or the partial-tier auditor seat even if the endpoint were resolved.

### Tier Bundle Inconsistencies (src/aho/tier_manifest.py:34-44)

```python
"partial": ["qwen3.5:9b", "nomic-embed-text"],           # Missing GLM + nemotron
"full":    ["qwen3.5:9b", "glm-4.6v:flash", "nomic-embed-text"],  # Wrong tag entirely
```

Real GLM tag used everywhere else: `haervwe/GLM-4.6V-Flash-9B:latest`

### Preflight / Doctor / Checks (fragile matching)

- `src/aho/preflight/checks.py:34`: `["qwen3.5:9b", "GLM-4.6V-Flash-9B", ...]` — will not reliably match the actual pulled tag.
- `src/aho/doctor.py:165`: substring `["qwen3.5", "nemotron-mini", "GLM-4", "nomic-embed-text"]` — better but still heuristic.

### Partial-Tier Auditor Seat

`src/aho/council/audit.py` hard-defaults to `llama3.2:3b`. While env `AHO_COUNCIL_AUDIT_MODEL` exists, there is no automatic tier-driven switch to `qwen3.5:9b` on partial hosts as required by CLAUDE.md and the 0.3.1 close note.

### Out-of-Band Wiring Claim vs Reality

The 0.3.1 close note and p3cos analysis repeatedly state that "council global-use wiring (6 source files + 2 docs)" was done out-of-band on a8cos. Recent commits (`00c9264`, `f6137d1`) did land:
- Project context preamble in conductor
- Tier-aware ctx helpers (already in orchestrator_config)
- Advisory routing fallback
- `_COUNCIL_ERRORS` handling
- Router prefix-near-miss fix
- Some OpenClaw / workstream_agent hardening

**The transport layer (the part that actually makes base hosts reach p3cos's Ollama for heavy models) is not among the landed changes.** The analysis doc treated this as the primary remaining deliverable for the port. It remains unimplemented.

**Risk:** Any assumption that "the council global-use wiring is done" is false for the cross-host use case that justified the early close of 0.3.1.

---

## 4. Documentation vs Implementation Fidelity

### Strong areas
- `artifacts/harness/base.md` (Pillars) and adversarial-authorship-protocol.md are treated as authoritative in code.
- Many ADRs (0007, 0009, 0010, 0011, 0012) are referenced correctly in comments and carry-forwards.
- `model-fleet.txt` + `model-fleet.md` are the correct single source for the roster.

### Significant drift
- `docs/operations/council-global-use.md` still describes localhost-only dispatch and does not mention tailnet-bound Ollama or `AHO_OLLAMA_BASE`.
- README and CLAUDE.md correctly describe the *intended* partial-tier architecture and the 0.3.1 substrate pivot, but the code does not yet deliver the transport half.
- `GEMINI.md` is present and versioned for 0.3.2, but the external-auditor contract assumes machinery (cross-host dispatch, hardened audit filter) that is only partially wired.
- Only one retrospective exists despite many closed iterations. This weakens the "harness is the contract" claim over time.
- `VERSION` file is abandoned at 0.2.14.

### Internal-only artifacts
Correctly excluded via .gitignore (tt-*, drafter-context, CLAUDE.md, GEMINI.md, top-level dated narratives). This matches the "Deployment-private content" policy in CLAUDE.md Rule 3.

---

## 5. Local-Only / Gitignored State at Risk on Folder Deletion

This checkout has **almost no runtime state** on disk:

- `~/.local/share/aho/` — does not exist
- `~/.config/aho/` (tier.json, orchestrator.json) — does not exist
- `data/chroma/` — gitignored, not present
- `data/aho_event_log.jsonl` — gitignored, not present in tree
- `.mcp.json` — gitignored, not present

Present in tree (will be lost if not copied):
- `.aho-checkpoint.json` (0.3.1 W2 complete state)
- Several untracked scripts in `bin/` (beacon smoke, snmp test)
- `artifacts/iterations/0.3.2/aho-plan-0.3.2.md` (new)
- Screenshots and debug txt

**High-value items the nzxtcos clone must be checked for:**
- Any populated `~/.config/aho/orchestrator.json` containing `ollama` peer config (even if the schema was never formalized in code)
- Any `~/.config/aho/tier.json` written by `aho install tier-manifest` on p3cos or other hosts
- Real ChromaDB collections under `/var/lib/aho/chroma` or `~/.local/share/aho/chroma`
- `~/.local/share/aho/events/aho_event_log.jsonl` and `observables.jsonl`
- `~/.local/share/aho/install-state.jsonl`
- Any age/fernet secret material (correctly never in repo)
- Custom systemd overrides for Ollama (`OLLAMA_HOST` binding on p3cos)
- Tailscale ACL notes or operator runbooks outside the tree

---

## 6. Other Concrete Issues (Prioritized by Load-Bearing)

1. **Model identity fragmentation** (high): At least four different strings are used to refer to the GLM vision model across tier_manifest, preflight, doctor, and clients. This will cause silent failures on `aho-models doctor` / preflight on a freshly installed partial host.

2. **Missing partial-tier positive routes in council dispatch** (high): The routing table only knows how to *escalate* from base. It has no definition for what a partial-tier host should actually run for audit or substantive work.

3. **Stale VERSION file** (medium): Violates the project's own versioning discipline and misleads anyone cloning.

4. **Retrospective coverage** (medium): One retrospective for 18+ iterations weakens the "efficacy is measured" Pillar and makes it harder for future operators (or auditors) to reconstruct decision history.

5. **Inconsistent embedding endpoint handling** (medium): rag/* uses different env var and old `/api/embeddings` path vs council.embed. RAG bootstrap and queries could behave differently inside vs outside container.

6. **0.3.2 plan exists only as drafter artifact** (low): No corresponding W0 acceptance archive or operator-signed close-yet. Normal for early W0, but worth noting when comparing clones.

7. **Substrate probe localhost assumptions** (low but noisy): `substrate_probes.py` hardcodes `http://localhost:11434` in the ssh probe path for remote hosts. This is incorrect for any cross-host Ollama scenario.

---

## 7. Positive Observations (for balance)

- The sealed 0.3.1 W0–W2 artifacts + p3cos analysis are high-quality and self-auditing.
- Tier detection + install.fish idempotency work (0.3.1 W1/W2) appears complete and well-instrumented.
- Anti-rubber-stamp machinery (confidence floor, deterministic post-hoc filter, G083 discipline in audit/triage) is present and has test coverage.
- The project correctly treats CLAUDE.md / GEMINI.md / harness/*.md as load-bearing contracts rather than suggestions.
- Gitignore policy for deployment-private content is consistently applied.

---

## 8. Recommended Comparison Checklist After Cloning nzxtcos Version

Run these on the fresh clone and diff against this report:

1. `cat VERSION`
2. `git log --oneline -10`
3. `git grep -l "def get_ollama_base\|AHO_OLLAMA_BASE" -- src/`
4. `git grep -E "http://(localhost|127.0.0.1):11434" -- src/aho/ | wc -l`
5. `python -c "
from aho.council.dispatch import ROUTING_TABLE
print([k for k in ROUTING_TABLE if 'partial' in str(k)])
"`
6. `cat src/aho/tier_manifest.py | grep -A 10 TIER_BUNDLES`
7. `ls -1 artifacts/iterations/0.3.2/`
8. `ls docs/retrospectives/`
9. `test -f artifacts/iterations/0.3.1/p3cos-council-port-analysis.md && echo present`
10. Check for `orchestrator.json` or `tier.json` templates / examples that mention `ollama` keys.
11. `bin/aho-models list` (if runnable) vs `cat artifacts/harness/model-fleet.txt`

Any file that exists in the nzxtcos clone but is absent here (or vice versa) in the `src/aho/` council + artifacts/ + pipeline/ surfaces is high-signal.

---

## 9. Summary Risk Assessment for This Checkout vs "Updated" Clone

**Highest risk of material divergence:**
- The cross-host Ollama transport layer (get_ollama_base + client updates + partial routing table entries) — this is the explicit justification for the 0.3.1 early close and the entire p3cos partial-tier story.
- Any per-host `orchestrator.json` peer configuration that was hand-authored on nzxtcos.
- Updated tier bundle logic or preflight model checks.
- Additional 0.3.2 W0 artifacts (acceptance/audit for the plan itself).

**Lower risk:**
- Sealed 0.3.1 archives (they are present and substantial here).
- Internal tt-* and drafter-context files (correctly excluded from both trees by policy).

This report was generated by exhaustive reading of the working tree on p3cos on 2026-05-30. It is intended as a neutral reference artifact.

**End of report.**