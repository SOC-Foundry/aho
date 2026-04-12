# P3 Clone Runbook — aho 0.2.9 W8

**Date:** 2026-04-11
**Target machine:** tsP3-cos (ThinkStation P3, Arch Linux)
**Operator:** Kyle
**Agent role:** Standby for real-time diagnosis via chat

---

## Pre-flight (from NZXTcos or any machine with SSH access)

### Step 1: SSH access verification

```fish
ssh tsP3-cos
# Expect: login shell on P3. If timeout/refused, check:
#   - P3 powered on and on LAN
#   - ~/.ssh/config has tsP3-cos host entry
#   - sshd running on P3: systemctl status sshd
```

### Step 2: GitHub SSH key check (on P3)

```fish
# Verify the SOC-Foundry deploy key is configured
ls -la ~/.ssh/id_ed25519_sockjt
# Expect: file exists, mode 0600

# Verify SSH config has the host alias
grep -A2 "github.com-sockjt" ~/.ssh/config
# Expect:
#   Host github.com-sockjt
#     HostName github.com
#     IdentityFile ~/.ssh/id_ed25519_sockjt

# Test GitHub connectivity
ssh -T git@github.com-sockjt
# Expect: "Hi SOC-Foundry! You've successfully authenticated..."
# If permission denied: key not added to SOC-Foundry org on GitHub
```

---

## Clone + Bootstrap

### Step 3: git clone

```fish
mkdir -p ~/Development/Projects
cd ~/Development/Projects
git clone git@github.com-sockjt:SOC-Foundry/aho.git
cd aho
```

**Verify:**
```fish
cat .aho.json | python -m json.tool
# Expect: current_iteration = "0.2.9", phase = 0
ls artifacts/harness/
# Expect: base.md, agents-architecture.md, model-fleet.md, etc.
ls bin/
# Expect: aho-bootstrap, aho-pacman, aho-models, etc.
```

### Step 4: bin/aho-bootstrap

```fish
./bin/aho-bootstrap
```

**Expected sequence:**

| Step | What | Expected outcome on P3 |
|---|---|---|
| 1 | Platform check | PASS — Arch Linux + fish |
| 2 | Resolve project root | PASS — ~/Development/Projects/aho |
| 3 | Create XDG dirs | PASS — idempotent mkdir |
| 4 | Generate .mcp.json from template | PASS — .mcp.json.tpl → .mcp.json with P3 path |
| 5 | Age key | PASS if age installed, CAPABILITY GAP if not |
| 6 | pip install | PASS if python + pip present |
| 7 | Symlink bin wrappers | PASS |
| 8 | MCP server fleet (npm) | May FAIL on missing npm packages — expected |
| 9 | Systemd user services | PASS if templates exist |
| 10 | Verify linger | CAPABILITY GAP if linger not enabled |
| 11 | Fish config marker | PASS — adds AHO_PROJECT_ROOT block |
| 12 | Summary | Reached only if all above pass |

**Expected capability gaps (not failures):**
- Age key: if `age` not installed → `sudo pacman -S age`
- Linger: if not enabled → `sudo loginctl enable-linger $USER`
- npm packages: if npm not installed or packages missing

**After bootstrap completes (or halts on gap):**
```fish
# Verify .mcp.json was generated with P3 path
cat .mcp.json | python -m json.tool | grep args
# Expect: "/home/kthompson/Development/Projects/aho" (P3 path, not NZXTcos path)
```

### Step 5: install.fish

```fish
./install.fish
```

**Expected sequence (9 steps with resume support):**

| Step | Wrapper | Expected on P3 |
|---|---|---|
| 1 pacman | bin/aho-pacman install | Installs missing packages from pacman-packages.txt. Should pass if pacman works. |
| 2 aur | bin/aho-aur install | Likely no-op (aur-packages.txt is empty). |
| 3 python | bin/aho-python install | pip install -e . Should pass. |
| 4 models | bin/aho-models install | Pulls 4 Ollama models (~15GB). Requires ollama running. May take 10+ min on first run. |
| 5 secrets | bin/aho-secrets-init | CAPABILITY GAP — fernet store not initialized. Expected halt point. |
| 6 mcp | bin/aho-mcp install | npm install for 8 MCP server packages. |
| 7 systemd | bin/aho-systemd install | Installs 4 user services. P3 SKIPS telegram inbound per W0 decision 2. |
| 8 symlinks | inline | Links bin/ wrappers to ~/.local/bin/ |
| 9 doctor | aho doctor | Full preflight. Expected warnings. |

**Secrets gap resolution (if you want to proceed past step 5):**
```fish
# Unlock with a new passphrase (remember it — needed after reboots)
aho secret unlock

# Set minimum secrets for outbound-only operation
aho secret set ahomw telegram_bot_token "TOKEN"
aho secret set ahomw telegram_chat_id "CHAT_ID"
# Or skip telegram entirely — secrets-init will halt but install.fish
# resumes from step 5 on re-run

# Re-run install.fish — resumes from last failed step
./install.fish
```

**Telegram inbound skip (W0 decision 2):**
P3 must NOT run the telegram inbound daemon. getUpdates cannot race between two machines on one bot. After install.fish step 7 (systemd), disable inbound:
```fish
systemctl --user stop aho-telegram
systemctl --user disable aho-telegram
# Or: leave it enabled but don't set telegram secrets — daemon will
# print "missing credentials" and idle harmlessly
```

### Step 6: aho doctor

```fish
aho doctor full
```

**Expected results on fresh P3 install:**

| Check | Expected |
|---|---|
| project_root | ok |
| aho_json | ok |
| ollama | ok (if ollama installed + running) |
| model_fleet | ok (if models pulled) |
| install_scripts | ok |
| linger | ok (if enabled in step 4) |
| otel_collector | warn or fail (collector may not be installed) |
| dashboard_port | ok or warn (port 7800 may conflict) |
| role_agents | ok (if python package installed) |
| mcp_fleet | ok or warn (depends on npm step) |

### Step 7: Dashboard reachability

```fish
# Start dashboard if not auto-started
bin/aho-dashboard &

# From P3 browser or curl
curl -s http://127.0.0.1:7800/api/state | python -m json.tool
# Expect: JSON with system, component, daemon sections
# If connection refused: dashboard not running or port conflict
```

---

## Failure Documentation Protocol

For every failure encountered, capture:

```
FAILURE: <one-line description>
STEP: <which step number>
CATEGORY: path-hardcode | package-missing | permission | secret-missing | port-conflict | other
ERROR TEXT: <verbatim terminal output, copy-paste>
REPRODUCTION: <exact command that triggered it>
FIX APPLIED: <what you did, or "deferred to 0.2.10">
```

Report failures in chat as they occur. Agent will compile into p3-clone-findings.md after the session.

---

## Success Criteria (tonight)

- [x] git clone works
- [ ] bin/aho-bootstrap halts cleanly on capability gaps (not crashes)
- [ ] install.fish runs as far as it can with resume support
- [ ] Failures have reproduction paths documented

## NOT success criteria (0.2.10 targets)

- All 9 install.fish steps green on P3
- Dashboard fully live
- Telegram working from P3
- All doctor checks passing
