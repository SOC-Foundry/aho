# aho 0.2.2 — Plan

**Phase:** 0 | **Iteration:** 2 | **Run:** 2 | **run_type:** mixed
**Agent:** Claude Code single-agent throughout

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.2.2
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.2.2.tar.gz --exclude=data/chroma --exclude=.venv --exclude=app/build --exclude=.git .
printf '{"aho_version":"0.1","name":"aho","project_code":"ahomw","artifact_prefix":"aho","current_iteration":"0.2.2","phase":0,"mode":"active","created_at":"2026-04-08T12:00:00+00:00","bundle_format":"bundle","last_completed_iteration":"0.2.1"}\n' > .aho.json
mkdir -p artifacts/iterations/0.2.2
tmux new-session -d -s aho-0.2.2 -c ~/dev/projects/aho
tmux send-keys -t aho-0.2.2 'cd ~/dev/projects/aho; claude --dangerously-skip-permissions' Enter
tmux attach -t aho-0.2.2
```

## W0 — Carryover hygiene

```fish
sed -i 's|\*\*Version:\*\* 0\.2\.1|**Version:** 0.2.2|' artifacts/harness/base.md
sed -i 's|\*\*Version:\*\* 0\.2\.1|**Version:** 0.2.2|' artifacts/harness/agents-architecture.md
sed -i 's|\*\*Version:\*\* 0\.2\.1|**Version:** 0.2.2|' artifacts/harness/model-fleet.md
sed -i 's|\*\*Version:\*\* 0\.2\.1|**Version:** 0.2.2|' artifacts/harness/global-deployment.md
sed -i 's|\*\*Charter version:\*\* 0\.2\.1|**Charter version:** 0.2.2|' artifacts/phase-charters/aho-phase-0.md
sed -i 's|\*\*Iteration 0\.2\.1\*\*|**Iteration 0.2.2**|' README.md
sed -i 's|aho v0\.2\.1|aho v0.2.2|' README.md
sed -i 's|^version = "0\.2\.1"|version = "0.2.2"|' pyproject.toml
sed -i 's|updated during 0\.2\.1|updated during 0.2.2|' CLAUDE.md
sed -i 's|updated during 0\.2\.1|updated during 0.2.2|' GEMINI.md
```

**Update components.yaml:** bump openclaw, nemoclaw, telegram `next_iteration: "0.2.2"` (they flip to active at end of W1/W2/W3).

**Fix `build_log_complete.py`:**
```fish
rg -n "design.*path" src/aho/postflight/build_log_complete.py
```
Inspect the actual path resolution. The current bug: it's resolving to `artifacts/iterations/{iteration}/aho-design-{iteration}.md` but failing on first `.exists()` check. Add explicit existence verification + fallback search:
```python
from aho.paths import get_artifacts_root
candidates = [
    get_artifacts_root() / "iterations" / iteration / f"aho-design-{iteration}.md",
    get_artifacts_root() / "iterations" / iteration / f"design.md",
]
design_path = next((c for c in candidates if c.exists()), None)
if not design_path:
    return {"status": "warn", "message": f"design doc not found in any of: {[str(c) for c in candidates]}"}
```

**Fix `report_builder.py` wall clock:** Add per-workstream timing extraction from event log:
```python
def _wall_clock_for_ws(events, workstream_id):
    ws_events = [e for e in events if e.get("workstream_id") == workstream_id]
    if not ws_events:
        return "-"
    first = min(e["timestamp"] for e in ws_events)
    last = max(e["timestamp"] for e in ws_events)
    delta_seconds = (parse_iso(last) - parse_iso(first)).total_seconds()
    return f"{int(delta_seconds // 60)}m {int(delta_seconds % 60)}s"
```

**Investigate evaluator loop:** Add logging in `src/aho/artifacts/evaluator.py` `evaluate_text()`:
```python
import os
if os.environ.get("AHO_EVAL_DEBUG"):
    print(f"[eval] target={target} severity={result.severity} errors={result.errors}", file=sys.stderr)
```
Run close with `AHO_EVAL_DEBUG=1` and document the cause in 0.2.2 Kyle's Notes.

```fish
python -m pytest artifacts/tests/ -x
```

## W1 — OpenClaw global daemon

Read `src/aho/agents/openclaw.py`. Replace stub `OpenClawSession` with real implementation. Key methods:

```python
class OpenClawSession:
    def __init__(self, role="assistant"):
        self.session_id = uuid.uuid4().hex[:8]
        self.workspace = Path(f"/tmp/openclaw-{self.session_id}")
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.history = []
        self.role = role
        self.qwen = QwenClient()
        log_event("session_start", source_agent="openclaw", target="qwen3.5:9b",
                  output_summary=f"session={self.session_id} role={role}")

    def chat(self, message):
        self.history.append({"role": "user", "content": message})
        prompt = self._render_prompt()
        response = self.qwen.generate(prompt)
        text = response.get("response", "")
        self.history.append({"role": "assistant", "content": text})
        return text

    def execute_code(self, code, language="python"):
        if language == "python":
            script = self.workspace / f"exec_{len(self.history)}.py"
            script.write_text(code)
            result = subprocess.run(
                ["python", str(script)],
                capture_output=True, text=True, timeout=30, cwd=self.workspace
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "exit": result.returncode}

    def cleanup(self):
        shutil.rmtree(self.workspace, ignore_errors=True)
```

Add `--serve` mode:
```python
def serve():
    sock_path = Path.home() / ".local/share/aho/openclaw.sock"
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    if sock_path.exists():
        sock_path.unlink()
    server = socketserver.UnixStreamServer(str(sock_path), OpenClawHandler)
    server.serve_forever()

if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
```

**Systemd unit `~/.config/systemd/user/aho-openclaw.service`:**
```ini
[Unit]
Description=aho OpenClaw Agent Daemon
After=network.target ollama.service
[Service]
Type=simple
ExecStart=/usr/bin/python -m aho.agents.openclaw --serve
Restart=on-failure
RestartSec=5
[Install]
WantedBy=default.target
```

**Wrapper `bin/aho-openclaw`:**
```fish
#!/usr/bin/env fish
set sock $HOME/.local/share/aho/openclaw.sock
test -S $sock; or begin; echo "openclaw daemon not running"; exit 1; end
echo "$argv" | nc -U $sock
```

```fish
chmod +x bin/aho-openclaw
systemctl --user daemon-reload
systemctl --user enable --now aho-openclaw.service
systemctl --user status aho-openclaw --no-pager
bin/aho-openclaw chat "say hello in 5 words"
```

**Update components.yaml:** openclaw `status: active`, remove `next_iteration`.

**Test:** `artifacts/tests/test_openclaw_real.py` — session creation, chat round-trip, execute_code with subprocess, cleanup.

## W2 — NemoClaw global daemon

Same pattern as W1. Real `NemoClaw` class wraps `NemotronClient` for routing + session pool dict for OpenClaw instances:

```python
class NemoClaw:
    def __init__(self):
        self.nemotron = NemotronClient()
        self.sessions = {}  # role -> OpenClawSession
        self.roles = ["assistant", "code_runner", "reviewer"]

    def route(self, task):
        result = self.nemotron.classify(task, self.roles)
        return result.get("category", "assistant")

    def dispatch(self, task):
        role = self.route(task)
        if role not in self.sessions:
            self.sessions[role] = OpenClawSession(role=role)
        return self.sessions[role].chat(task)
```

Systemd unit `aho-nemoclaw.service` with `After=aho-openclaw.service`. Wrapper `bin/aho-nemoclaw`. 

**Update components.yaml:** nemoclaw `status: active`.

**Test:** `test_nemoclaw_real.py` — routing, dispatch, session reuse on second call.

## W3 — Telegram bridge real implementation

**Capability gap check:**
```fish
aho secret get telegram_bot_token > /dev/null 2>&1
or echo "[CAPABILITY GAP] Telegram bot token missing. Run: 1) Create bot via @BotFather, 2) aho secret set telegram_bot_token <token>, 3) aho secret set telegram_chat_id <id>"
```

If gap: halt cleanly, write checkpoint, notify stdout. Otherwise proceed.

**Real `notifications.py`:**
```python
import requests
from aho.secrets.session import get_secret
from aho.logger import log_event

BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"

def send(message, priority="normal", chat_id=None):
    try:
        token = get_secret("telegram_bot_token")
        cid = chat_id or get_secret("telegram_chat_id")
        prefix = {"high": "🔴", "normal": "🔵", "low": "⚪"}.get(priority, "")
        payload = {"chat_id": cid, "text": f"{prefix} {message}", "parse_mode": "Markdown"}
        resp = requests.post(BASE_URL.format(token=token), json=payload, timeout=10)
        log_event("llm_call", source_agent="telegram", target="api.telegram.org",
                  action="send", input_summary=message[:80],
                  output_summary=f"status={resp.status_code}",
                  status="success" if resp.ok else "error")
        return resp.ok
    except Exception as e:
        log_event("llm_call", source_agent="telegram", action="send",
                  status="error", error=str(e))
        return False

def send_capability_gap(gap):
    return send(f"*[CAPABILITY GAP]* {gap}", priority="high")

def send_close_complete(iteration, status):
    emoji = "✅" if status == "closed" else "⚠️"
    return send(f"{emoji} aho {iteration} {status}", priority="normal")
```

Systemd unit `aho-telegram.service` (Unix socket for inbound from other daemons, optional).

**Wire into close sequence** in `src/aho/cli.py`:
```python
# After checkpoint close
try:
    from aho.telegram.notifications import send_close_complete
    send_close_complete(iteration, "closed")
except Exception:
    pass  # never block close on telegram
```

**Wrapper `bin/aho-telegram`:**
```fish
#!/usr/bin/env fish
switch $argv[1]
    case send
        python -c "from aho.telegram.notifications import send; send('$argv[2..]')"
    case test
        python -c "from aho.telegram.notifications import send; r=send('aho 0.2.2 W3 telegram smoke test'); print('OK' if r else 'FAIL')"
    case status
        systemctl --user status aho-telegram --no-pager
end
```

**Update components.yaml:** telegram `status: active`.

**Test:** `test_telegram_real.py` with mocked `requests.post`.

## W4 — Doctor + install integration

Add to `src/aho/doctor.py` quick checks:
```python
def check_aho_daemons():
    services = ["aho-openclaw", "aho-nemoclaw", "aho-telegram"]
    results = {}
    for svc in services:
        r = subprocess.run(["systemctl", "--user", "is-active", svc],
                           capture_output=True, text=True)
        results[svc] = "ok" if r.stdout.strip() == "active" else "fail"
    return results
```

Update `bin/aho-install`:
```fish
# After OTEL collector unit installation
for daemon in openclaw nemoclaw telegram
    cp templates/systemd/aho-$daemon.service.template ~/.config/systemd/user/aho-$daemon.service
end
systemctl --user daemon-reload
systemctl --user enable --now aho-openclaw aho-nemoclaw aho-telegram
```

Update `bin/aho-uninstall`:
```fish
for daemon in openclaw nemoclaw telegram
    systemctl --user stop aho-$daemon 2>/dev/null
    systemctl --user disable aho-$daemon 2>/dev/null
    rm -f ~/.config/systemd/user/aho-$daemon.service
end
```

Update `artifacts/harness/global-deployment.md` capability gap inventory with Telegram bot creation step. Update `artifacts/harness/p3-deployment-runbook.md`.

## W5 — Dogfood + close

**End-to-end smoke:**
```fish
bin/aho-nemoclaw dispatch "summarize the eleven pillars in 3 sentences"
sleep 5
wc -l ~/.local/share/aho/traces/traces.jsonl
bin/aho-telegram test
```

Verify trace count incremented, telegram test message arrives.

**Close sequence:**
```fish
python -m pytest artifacts/tests/ -v
python -m aho.cli iteration close 0.2.2
```

Verify:
- All 95+ tests green
- All 3 daemons reporting active in doctor
- Bundle exists with §23 showing 0 stubs (was 3)
- Run file shows real wall clock per workstream (W0 fix landed)
- Telegram close-complete notification arrived
- All postflight green
- `.aho.json` shows `last_completed_iteration: 0.2.2`

**Print commit message draft:**
```
COMMIT MESSAGE DRAFT (Kyle pushes manually):
---
KT completed 0.2.2: openclaw + nemoclaw + telegram graduated from stub to active. Three global daemons running as systemd user services. Deferral debt cleared.
---
```

## Capability gaps expected

- **W3:** Telegram bot creation + secret installation by Kyle. Halt cleanly with explicit instructions if absent.
- **W5:** Manual git push by Kyle (Pillar 11)

## Checkpoint schema

```json
{
  "iteration": "0.2.2",
  "phase": 0,
  "run_type": "mixed",
  "current_workstream": "W0",
  "workstreams": {"W0":"pending","W1":"pending","W2":"pending","W3":"pending","W4":"pending","W5":"pending"},
  "executor": "claude-code",
  "started_at": null,
  "last_event": null
}
```
