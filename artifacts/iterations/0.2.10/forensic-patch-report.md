# Forensic Patch Report — 0.2.10

**Date:** 2026-04-12
**Trigger:** Post-close forensic by Kyle — 3 unverified claims + repo hygiene
**Scope:** Verification only. No version bump. No postflight re-run.

---

## Item 1: Socket Location (W5)

**Claim:** OpenClaw socket at `/run/user/1000/openclaw.sock`

**Verification commands and output:**

```
$ ss -xlp | grep openclaw
u_str LISTEN 0  5  /run/user/1000/openclaw.sock 6095559 * 0
  users:(("python",pid=3545867,fd=6))

$ systemctl --user cat aho-openclaw | grep -iE 'listen|socket|exec'
ExecStart=/usr/bin/python -m aho.agents.openclaw --serve

$ ls -la /run/user/1000/openclaw.sock
srwxr-xr-x 1 kthompson kthompson 0 Apr 11 22:35 /run/user/1000/openclaw.sock
```

**Result:** VERIFIED. Socket exists at claimed path. aho-openclaw PID 3545867 is listening. No fix needed.

---

## Item 2: OTEL → Jaeger Pipeline (W9)

**Claim:** No connection-refused errors; exporter correctly configured.

**Verification commands and output:**

```
$ journalctl --user -u aho-otel-collector --since "22:45" -n 50 | grep -iE 'jaeger|refused|error|warn'
(no output — zero errors since 22:45)

$ cat ~/.config/aho/otel-collector.yaml | grep -A5 -iE 'exporter|jaeger'
exporters:
  file:
    path: /home/kthompson/.local/share/aho/traces/traces.jsonl
  otlp/jaeger:
    endpoint: 127.0.0.1:14317
    tls:
      insecure: true
...
      exporters: [file, otlp/jaeger]

$ ss -tlnp | grep jaeger
LISTEN 0 4096  127.0.0.1:16686  0.0.0.0:*  users:(("jaeger-all-in-o",pid=3546197,...))
LISTEN 0 4096  127.0.0.1:14318  0.0.0.0:*  users:(("jaeger-all-in-o",...))
LISTEN 0 4096  127.0.0.1:14317  0.0.0.0:*  users:(("jaeger-all-in-o",...))
```

**Result:** VERIFIED. Zero errors since 22:45. Exporter `otlp/jaeger` targets `127.0.0.1:14317`. Jaeger PID 3546197 listening on 14317 (gRPC), 14318 (HTTP), 16686 (UI). No fix needed.

**Note on exporter naming:** `otlp/jaeger` is the current otelcol-contrib naming convention (exporter type `otlp` with named instance `/jaeger`). This is not deprecated. No rename needed.

---

## Item 3: aho doctor --deep (W12)

**Claim:** `aho doctor deep` returns flutter, dart, and install_completeness checks.

**Verification commands and output:**

```
$ python -m aho.cli doctor --help
usage: aho doctor [-h] {quick,preflight,postflight,full,deep} ...
  deep   Full + Flutter/Dart SDK integration checks

$ python -m aho.cli doctor deep | grep -E "flutter|dart|install_comp"
[ok]  flutter_doctor      : flutter doctor: 6/6 ok, 0 warnings
[ok]  dart_version        : Dart SDK version: 3.11.4 (stable)
[ok]  install_completeness: all 6 install directories present
```

**Result:** VERIFIED. `deep` subcommand registered, all three SDK checks execute and pass. No fix needed.

**Note:** `aho doctor deep` exits with FAIL overall due to pre-existing postflight gates (pillars_present, run_complete sign-off). These are not --deep flag issues — they're iteration-close gates that fire at any level >= postflight.

---

## Item 4: Repo Hygiene

**Before:**
```
-rw-r--r-- 1 kthompson kthompson 135M  jaeger-1.62.0-linux-amd64.tar.gz
drwxr-xr-x 2 kthompson kthompson 4096  jaeger-1.62.0-linux-amd64/
```

**Actions taken:**
- `mv jaeger-1.62.0-linux-amd64.tar.gz /tmp/` — tarball moved out of repo
- `rm -rf jaeger-1.62.0-linux-amd64/` — extracted dir deleted
- Added to `.gitignore`: `*.tar.gz` and `jaeger-*-linux-amd64/`

**After:**
```
$ ls jaeger* 2>&1
no matches found: jaeger*

$ grep -n "tar.gz\|jaeger.*linux" .gitignore
52:*.tar.gz
53:jaeger-*-linux-amd64/
```

---

## Files Modified

| File | Change |
|---|---|
| `.gitignore` | Added `*.tar.gz` and `jaeger-*-linux-amd64/` patterns |

## Scope Assessment

No item required scope beyond a fix. Items 1-3 verified clean with no code changes needed. Item 4 was a cleanup action with a .gitignore addition. No halt trigger.

## Updated Service States

| Service | PID | Listening | Status |
|---|---|---|---|
| aho-openclaw | 3545867 | /run/user/1000/openclaw.sock | active |
| aho-jaeger | 3546197 | 127.0.0.1:14317 (gRPC), :14318 (HTTP), :16686 (UI) | active |
| aho-otel-collector | (restarted) | 127.0.0.1:4317 (gRPC), :4318 (HTTP) | active |
| aho-dashboard | 3546665 | 127.0.0.1:7800 | active |
| aho-telegram | (restarted) | — | active |
| aho-harness-watcher | — | — | active |
