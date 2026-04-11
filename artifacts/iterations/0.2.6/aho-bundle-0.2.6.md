# aho - Bundle 0.2.6

**Generated:** 2026-04-11
**Iteration:** 0.2.6
**Project code:** ahomw
**Project root:** /home/kthompson/dev/projects/aho

---

## §1. Design

0.2.6 is a live-fire hardening iteration with no separate design doc. Scope was discovered during install.fish execution on NZXTcos after 0.2.5 close. Three defects surfaced:

1. CachyOS ollama pacman package corrupt — upstream install sufficient
2. bin/aho-secrets-init checking wrong secrets store (`.age` files vs fernet)
3. Doctor missing telegram bot identity for user verification

## §2. Plan

4-workstream single-agent iteration:
- W0: Canonical bumps
- W1: Ollama pacman fix + `_pkg_present` fallback
- W2: bin/aho-secrets-init rewrite for fernet store
- W3: Telegram bot name in doctor via cached state file
- W4: Close (reports, bundle, changelog)

## §3. Build Log

See `aho-build-log-0.2.6.md` in this directory.

## §4. Run Report

See `aho-run-0.2.6.md` in this directory.

## §5. Changed Files

| File | Change |
|---|---|
| `artifacts/harness/pacman-packages.txt` | Removed ollama (15 → 14), added comment |
| `bin/aho-pacman` | Added `_pkg_present` fallback for upstream packages |
| `bin/aho-secrets-init` | Rewritten: fernet store + telegram daemon detection |
| `src/aho/doctor.py` | Added `_get_telegram_bot_name()`, updated daemon check |
| `src/aho/telegram/notifications.py` | Added `_write_bot_state()`, `BOT_STATE_PATH` |
| `CHANGELOG.md` | Added 0.2.6 entry |
| 10 canonical artifacts | Version bumped to 0.2.6 |

## §6. Verification

### install.fish (NZXTcos)

All 9 steps pass. Second run is idempotent (all steps skip or no-op).

### Test suite

143 passed, 1 skipped, 0 failures.

### Doctor

```
aho doctor quick: CLEAN
aho doctor preflight:
  aho-telegram: aho-telegram running — @aho_run_bot
```

### bin/aho-pacman doctor

All 14 declared packages present (ollama detected via command fallback).

### bin/aho-models doctor

All 4 declared models present.

## §7. Gotcha Registry

19 entries (unchanged from 0.2.5). No new gotchas — all three issues were operational, not harness-level patterns.

## §8. Definition of Done

- [x] install.fish completes all 9 steps on NZXTcos
- [x] install.fish second run is idempotent
- [x] bin/aho-pacman doctor passes with upstream ollama
- [x] bin/aho-secrets-init detects fernet store + running telegram daemon
- [x] aho doctor preflight shows @aho_run_bot
- [x] 143 tests pass
- [x] All canonical artifacts at 0.2.6
- [ ] Kyle git commit + push
- [ ] install.fish on P3 (future iteration)

---

*aho 0.2.6 bundle — install.fish live-fire hardening.*
