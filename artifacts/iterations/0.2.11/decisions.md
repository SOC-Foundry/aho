# Pre-Iteration Decisions — 0.2.11

**Captured:** 2026-04-12, pre-W0 chat
**Author:** Kyle (verbatim from chat)

---

## Decision 1: AUR Installer Abstraction IN SCOPE

AUR installer abstraction is in scope for 0.2.11 (W15-W16). `aur_or_binary()` helper with AUR-primary, binary-fallback pattern. otelcol-contrib and jaeger retrofitted to use it. aur-packages.txt becomes source of truth.

## Decision 2: Event Log Relocation

Event log relocates to `~/.local/share/aho/events/` with rotation (W7). Size-based rotation: 100MB rotate, keep 3. `data/aho_event_log.jsonl` deprecated. Bundle, manifest, .gitignore updated accordingly.

## Decision 3: Shim Wrapper Deletion SLIPS to 0.2.12

Shim wrapper deletion slips to 0.2.12 as part of broader tech-legacy-debt prune sweep. 0.2.11 W18 audits only — produces confidence-tagged inventory but does not execute deletions. Prunes execute in 0.2.12 after persona 2 validation confirms no silent dependencies.

## Decision 4: Task D Email Extract Assertion

Task D (email extract) assertion: exact-match sorted set against known 7-email fixture, no duplicates, no extras. This is the strictest assertion in 0.2.11 — validates AcceptanceCheck under real pattern-match load.

## Decision 5: Three-Session Execution with Per-Workstream Review ON

Three-session execution model per ADR-045 hybrid iteration shape. Per-workstream review ON throughout all 19 workstreams. Hard gate between W8 and W9 — all backstop workstreams must be green before persona 3 validation fires. No overnight execution.
