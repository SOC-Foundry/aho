# aho Build Log — 0.2.6

**Phase:** 0 | **Iteration:** 2 | **Run:** 6
**Theme:** install.fish live-fire hardening — pacman, secrets, telegram doctor
**Executor:** claude-code (single-agent)
**Started:** 2026-04-11

---

## W0 — Canonical bumps

- Bumped all 10 canonical artifacts from 0.2.5 → 0.2.6
- Updated `.aho.json` current_iteration and last_completed_iteration
- Updated checkpoint to 0.2.6 closed

## W1 — Ollama pacman fix + _pkg_present fallback

**Problem:** CachyOS mirror served corrupt ollama package (invalid PGP signature). Ollama already installed at `/usr/local/bin/ollama` v0.20.2 via upstream script. pacman's ollama package also conflicted with upstream's `/usr/share/ollama`.

**Fix:**
- Removed `ollama` from `artifacts/harness/pacman-packages.txt` (15 → 14 packages)
- Added comment explaining upstream install path
- Added `_pkg_present` function to `bin/aho-pacman` — checks `pacman -Qi` first, falls back to `command -q` for upstream-installed packages
- Updated `_cmd_status` and `_cmd_doctor` to use `_pkg_present`

**Verification:** `bin/aho-pacman doctor` now passes — 14 pacman packages + ollama detected via command fallback.

## W2 — bin/aho-secrets-init rewrite

**Problem:** 0.2.5 `bin/aho-secrets-init` scaffolded `.age` files for telegram secrets and halted with capability gap. But telegram secrets have been in the fernet secrets store (`~/.config/aho/secrets.fish.fernet`) since 0.2.2. The scaffold was checking the wrong store.

**Fix:** Rewrote `bin/aho-secrets-init` to:
1. Check age key (unchanged)
2. Check OS keyring backend (unchanged)
3. Check fernet secrets store exists and is non-empty (`_check_secrets_store`)
4. Check telegram daemon running via `systemctl --user is-active` (`_check_telegram`)
5. Fall back to "secrets store present" if daemon not running

Removed all `.age` file scaffolding, placeholder files, and README generation. The fernet store is the source of truth.

**Verification:** `bin/aho-secrets-init` exits 0 on NZXTcos. install.fish step 5 passes.

## W3 — Telegram bot name in doctor

**Problem:** Kyle wanted `aho doctor` to display the actual bot name so users can verify the correct bot is configured.

**Fix:**
- Added `_write_bot_state()` to `src/aho/telegram/notifications.py` — calls Telegram `getMe` API on daemon startup, writes result to `~/.local/state/aho/telegram_bot.json`
- Added `_get_telegram_bot_name()` to `src/aho/doctor.py` — reads cached state file
- Updated `_check_aho_daemons()` to append `@bot_username` to telegram status line

**Verification:** `aho doctor preflight` shows `aho-telegram running — @aho_run_bot`. State file persists across daemon restarts.

## W4 — Close-out

- Run report, build log, bundle generated
- CHANGELOG updated
- All 143 tests still pass
- install.fish completes all 9 steps on NZXTcos

---

## install.fish full run on NZXTcos (idempotency verified)

```
Step 1 (pacman): 14 packages, all --needed skip
Step 2 (aur): no AUR packages declared
Step 3 (python): pip install -e . (upgrade in place)
Step 4 (models): 4 models, all already pulled
Step 5 (secrets): age key present, secrets store present, telegram daemon active
Step 6 (mcp): 9 packages, all already installed
Step 7 (systemd): 4 services installed and enabled
Step 8 (symlinks): all wrappers linked
Step 9 (doctor): CLEAN
```
