# aho 0.2.5 — Decisions

**Captured:** 2026-04-11 W0
**Source:** Kyle's responses to design doc §Open Questions

---

## 1. Pacman subset — approved with 2 additions

Final list: fish, tmux, git, base-devel, python, python-pip, age, nodejs, npm, jq, ripgrep, fd, htop, **ollama**, **libsecret**.

W1 flags:
- Confirm ollama is in pacman on CachyOS. If not, move to AUR (W2 picks it up).
- Confirm libsecret is the right keyring backend on CachyOS. If gnome-keyring is the default, swap it.

## 2. AUR subset — empty for aho proper

Header comment only in `aur-packages.txt`. `bin/aho-aur` still bootstraps yay if missing.

## 3. bin/aho-install rename — rename to bin/aho-bootstrap

Reason: install.fish is now top-level entry point. "bootstrap" accurately describes one-time setup. W4 absorbs age keygen logic into `bin/aho-secrets-init`. If after W4 `bin/aho-bootstrap` has nothing left to do, delete it. Do not keep an empty wrapper for symmetry.

Sweep all references. Add aho-G066 if any are missed.

## 4. Telegram scaffolding — confirmed, no interactive prompts

First-run flow:
1. Create `~/.config/aho/telegram/` (mode 700) if missing
2. Create placeholder zero-byte files: `bot_token.age`, `chat_id.age`
3. Write `README.md` with age encryption instructions
4. Halt with `[CAPABILITY GAP]` message, exit non-zero
5. On subsequent runs: detect non-zero size on both `.age` files, skip halt

No prompts. No stdin reads.

## 5. Smoke test path — Path B

`bin/aho-conductor smoke` subcommand. Generate marker file, dispatch task, assert file + content + 7 spans in event log.
