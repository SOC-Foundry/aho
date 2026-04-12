# D3 Diagnosis: harness-watcher Daemon

**Iteration:** 0.2.8 W8
**Date:** 2026-04-11
**Diagnosis type:** Discovery + code (Branch A fix)

---

## 5-Step Diagnosis

### Step 1: systemctl status
```
○ aho-harness-watcher.service
   Loaded: loaded (enabled; preset: enabled)
   Active: inactive (dead)
```
Enabled but never started. No crash, no failure — just never ran.

### Step 2: service file review
```ini
[Service]
Type=simple
ExecStart=/usr/bin/python -m aho.agents.roles.harness_agent --watch %h/dev/projects/aho/data/aho_event_log.jsonl
Restart=on-failure
RestartSec=5
```
Service file is correct. Uses `%h` for home directory expansion. `Restart=on-failure` means it would restart on crash, but it was never started in the first place.

### Step 3: journal logs
```
-- No entries --
```
Zero journal entries. Confirms the service was never started, not that it started and crashed.

### Step 4: module test
```
$ python -m aho.agents.roles.harness_agent --help
Usage: python -m aho.agents.roles.harness_agent --watch <event_log_path>
```
Module exists at `src/aho/agents/roles/harness_agent.py`, responds to --help. No import errors.

### Step 5: manual start
```
$ systemctl --user start aho-harness-watcher.service
$ systemctl --user status aho-harness-watcher.service
● Active: active (running) since ...
  Main PID: 3327658 (python)
  Memory: 80.4M
```
Daemon starts cleanly and runs. Tails the event log and monitors for harness events. No runtime errors.

## Root Cause

**Branch A: Installer fix.** `bin/aho-systemd install` runs `systemctl --user enable` but not `systemctl --user start`. The enable step sets the service to start on next boot/login, but does not start it immediately. The other three daemons (openclaw, nemoclaw, telegram) were started manually by Kyle during development. harness-watcher was never manually started.

## Fix Applied

Added `systemctl --user start aho-$d.service` after the enable line in `bin/aho-systemd`. All four daemons now get enabled AND started on install. Idempotent — starting an already-running service is a no-op.

## Current State

harness-watcher is now running on NZXTcos. Dashboard daemon health card should show green. The daemon will survive reboots (enabled + linger).

---

*harness-watcher-diagnosis.md — 0.2.8 W8. Branch A executed. 5 minutes total.*
