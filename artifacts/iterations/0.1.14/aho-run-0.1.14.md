# Run File — aho 0.1.14

**Generated:** 2026-04-11
**Iteration:** 0.1.14
**Phase:** 0
**Run Type:** mixed
**Status:** Graduated

## Workstream Summary

| WS | Status | Agent | Summary |
|---|---|---|---|
| W0 | pass | gemini-cli | Version bump, MANIFEST populated, install.fish marker restored, artifacts/docs/ flattened |
| W1 | pass | gemini-cli | Terminology sweep: IAO→AHO expansion, iaomw→ahomw across active docs and source |
| W2 | pass | gemini-cli | Six canonical artifacts repaired to 0.1.14 |
| W3 | pass | gemini-cli | Build log stub generator implemented and wired |
| W4 | pass | gemini-cli | Postflight gate repair: layout variant detection, run_type floors |
| W5 | pass | gemini-cli | bin/aho-install --dry-run validated XDG paths on scratch root |
| W6 | pass | claude-code | 3 dogfood fixes, bundle 180KB §1–§22, close |

W6 fixes: `pillars_present.py` (W-based skip per-pillar enum), `iteration_complete.py` (flat string vs dict), `build_log_stub.py` (naming convention `aho-build-log-*`).

Tests: 65/65 green (1 skipped). Bundle: 180KB §1–§22 PASS. Doctor: 5 ok / 1 WARN (manifest hash) / 1 FAIL (build_gatekeeper Flutter — not aho-relevant).

---

## Agent Questions — Answered

**Q1 (MANIFEST hash mismatch on `paths.py` and `migrate_config_fish.py`).** Fix in 0.1.15 W0. Add `manifest_current` postflight gate that FAILs on stale hashes — forces refresh discipline at close, no more relying on memory.

**Q2 (`build_gatekeeper` running `flutter build web`).** Delete the file. It's a kjtcom holdover. aho gets a new `app_build_check.py` in 0.1.15 W3 that validates `flutter build web` only when `app/` is populated (after `flutter create app` lands in 0.1.15 W3). Future Flutter checks come back when the aho frontend is real, not as a kjtcom contamination of the universal harness.

---

## Kyle's Notes

0.1.14 graduated. Stub generator worked exactly as designed — §3 populated mechanically, no `(missing)` placeholder. Postflight layout variant detection landed clean. W6 caught three real bugs that would have broken 0.1.15 close. Split-agent model continues to validate.

**Phase 0 exit roadmap (3 iterations + ship gauntlet):**

- **0.1.15** — Foundation. Report repair (mechanical builder, ground-truth-driven), component manifest system (visible openclaw/nemoclaw/telegram entries), OTEL instrumentation, /app Flutter scaffold, hygiene + Phase 0 charter rewrite. No soc-foundry, no P3 — pure foundation.
- **0.1.16** — Cleanup + first soc-foundry push (run 1) + openclaw/nemoclaw global wrappers + telegram bridge real implementation + P3 clone attempt.
- **0.1.17** — claw3d scaffold, integration polish, fresh-clone P3 dogfood pass.
- **0.18.x** — multi-run ship gauntlet, third octet becomes crucial.
- **Phase 1 opens** when P3 + Alex validation lands clean.

**Component visibility — non-negotiable from 0.1.15 forward.** I have been asking for component info in run reports for several iterations and not getting it. The pattern of openclaw being installed as an ephemeral Python function during kjtcom instead of globally, and Telegram being deferred since the original 0.1.4 charter, ends now. 0.1.15 W1 makes openclaw, nemoclaw, and telegram first-class entries in `components.yaml` with status=stub and explicit `next_iteration: 0.1.16`. They become visible in every run report from 0.1.15 forward. Invisible deferrals are over.

**Today's window:** ~8 hours wall clock (morning + evening blocks, family time mid-afternoon). Multiple runs possible. 0.1.15 should be a sharp ~2-hour run, not a 12-hour sprawl. soc-foundry push and P3 clone happen in 0.1.16+, not today.

---

## Reference: The Eleven Pillars

1. Delegate everything delegable. 2. The harness is the contract. 3. Everything is artifacts. 4. Wrappers are the tool surface. 5. Three octets, three meanings. 6. Transitions are durable. 7. Generation and evaluation are separate roles. 8. Efficacy is measured in cost delta. 9. The gotcha registry is the harness's memory. 10. Runs are interrupt-disciplined. 11. The human holds the keys.

---

## Sign-off

- [x] I have reviewed the bundle
- [x] I have reviewed the build log
- [x] I have reviewed the report
- [x] I have answered all agent questions above
- [x] I am satisfied with this iteration's output

---

*Closed 2026-04-11, W6 by claude-code*
