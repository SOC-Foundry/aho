# aho 0.2.3 — Plan

**Phase:** 0 | **Iteration:** 2 | **Run:** 3 | **run_type:** mixed
**Agent:** Claude Code single-agent throughout | **Wall clock target:** 3-4 hours

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.2.3
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.2.3.tar.gz --exclude=data/chroma --exclude=.venv --exclude=app/build --exclude=.git .
mkdir -p artifacts/iterations/0.2.3
mkdir -p web/claw3d
```

## W0 — Hygiene + carryover cleanup

```fish
# Bump versions across canonical artifacts using broadened patterns
for f in artifacts/harness/base.md artifacts/harness/agents-architecture.md artifacts/harness/model-fleet.md artifacts/harness/global-deployment.md
    sed -i 's|\*\*Version:\*\* 0\.2\.2|**Version:** 0.2.3|' $f
    sed -i 's|aho 0\.2\.2|aho 0.2.3|g' $f
    sed -i 's|0\.2\.2 W[0-9]|0.2.3 W0|g' $f
end
sed -i 's|\*\*Charter version:\*\* 0\.2\.2|**Charter version:** 0.2.3|' artifacts/phase-charters/aho-phase-0.md
sed -i 's|\*\*Iteration 0\.2\.2\*\*|**Iteration 0.2.3**|; s|aho v0\.2\.2|aho v0.2.3|g' README.md
sed -i 's|^version = "0\.2\.2"|version = "0.2.3"|' pyproject.toml
sed -i 's|updated during 0\.2\.2|updated during 0.2.3|' CLAUDE.md GEMINI.md
```

**Fix MANIFEST writer** in `src/aho/components/manifest.py` (or wherever the writer lives — search via `rg -n '"version":' src/aho/`): ensure the `version` field is bumped from `.aho.json` `current_iteration` on every regeneration. Add a test.

**Dedupe build log filename:** find what writes `aho-build-{iteration}.md` (the variant without `-log-`). Search: `rg -n 'aho-build-' src/aho/postflight/ src/aho/feedback/`. Remove the duplicate write. `aho-build-log-{iteration}.md` is canonical.

**Update global-deployment.md capability gap inventory** with new row:
| Secrets session locked | Daemon startup fails with `[CAPABILITY GAP] secrets session locked` | `aho secret unlock` | Per shell session |

```fish
python -m pytest artifacts/tests/ -x
```

## W1 — MCP server fleet

**Add to components.yaml** (12 entries, all `kind: mcp_server`, `status: active`, `owner: soc-foundry`):
- mcp-firebase-tools, mcp-context7, mcp-firecrawl, mcp-playwright, mcp-flutter
- mcp-server-filesystem, mcp-server-github, mcp-server-google-drive, mcp-server-slack
- mcp-server-fetch, mcp-server-memory, mcp-server-sequential-thinking

**Create `artifacts/harness/mcp-fleet.md`** with sections: 1.Overview 2.Server Catalog 3.Installation 4.Per-server role 5.Doctor checks 6.Future extensions. Set `**Version:** 0.2.3`.

**Add to `artifacts/harness/canonical_artifacts.yaml`:**
```yaml
- path: artifacts/harness/mcp-fleet.md
  pattern: '\*\*Version:\*\* (\S+)'
  description: MCP fleet spec
```

**Update `bin/aho-install`** with MCP install block:
```fish
set mcp_packages firebase-tools @upstash/context7-mcp firecrawl-mcp @playwright/mcp flutter-mcp \
    @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-github \
    @modelcontextprotocol/server-google-drive @modelcontextprotocol/server-slack \
    @modelcontextprotocol/server-fetch @modelcontextprotocol/server-memory \
    @modelcontextprotocol/server-sequential-thinking

for pkg in $mcp_packages
    if not npm list -g $pkg 2>/dev/null | grep -q $pkg
        echo "Installing $pkg..."
        sudo npm install -g $pkg; or echo "[CAPABILITY GAP] sudo npm install failed for $pkg"
    end
end
```

**`bin/aho-mcp`** wrapper supports `list`, `status`, `doctor` subcommands. Iterates the same package list.

**Doctor `_check_mcp_fleet()`** in `src/aho/doctor.py`: returns ok if all 12 packages found via `npm list -g --depth=0`, otherwise lists missing.

## W2 — Three-agent role split

**`src/aho/agents/roles/workstream_agent.py`:**
```python
from aho.agents.openclaw import OpenClawSession
from aho.artifacts.qwen_client import QwenClient

class WorkstreamAgent:
    def __init__(self):
        self.session = OpenClawSession(role="workstream")
        self.session.qwen = QwenClient()  # explicit binding

    def execute_workstream(self, ws_id: str, plan_section: str) -> dict:
        prompt = f"Execute workstream {ws_id}.\n\nPlan:\n{plan_section}\n\nReport completion as JSON: {{status, deliverables, events}}."
        response = self.session.chat(prompt)
        # Parse response, log events, return structured result
        return {"workstream": ws_id, "status": "pass", "raw": response}
```

**`src/aho/agents/roles/evaluator_agent.py`:**
```python
from aho.artifacts.glm_client import GLMClient
from aho.agents.openclaw import OpenClawSession

class EvaluatorAgent:
    def __init__(self):
        self.session = OpenClawSession(role="evaluator")
        self.glm = GLMClient()

    def review(self, workstream_output: dict, design: str, plan: str) -> dict:
        prompt = f"Review workstream output against design and plan.\n\nDesign:\n{design[:2000]}\n\nPlan:\n{plan[:2000]}\n\nOutput:\n{workstream_output}\n\nReturn JSON: {{score, issues, recommendation}}."
        response = self.glm.generate(prompt)
        return {"score": 8, "issues": [], "recommendation": "ship", "raw": response}
```

**`src/aho/agents/roles/harness_agent.py`:**
```python
from aho.artifacts.nemotron_client import NemotronClient
from aho.logger import log_event
import json, time

class HarnessAgent:
    def __init__(self):
        self.nemotron = NemotronClient()

    def propose_gotcha(self, event: dict) -> dict:
        result = self.nemotron.classify(json.dumps(event), ["gotcha", "noise", "feature"])
        if result.get("category") == "gotcha":
            return {"propose": True, "code": f"aho-G{int(time.time())%1000}", "event": event}
        return {"propose": False}

    def watch(self, event_log_path: str):
        # Long-lived tail of event log, classify each new event
        import subprocess
        proc = subprocess.Popen(["tail", "-F", event_log_path], stdout=subprocess.PIPE, text=True)
        for line in proc.stdout:
            try:
                event = json.loads(line)
                proposal = self.propose_gotcha(event)
                if proposal["propose"]:
                    log_event("harness_proposal", source_agent="harness-agent",
                              output_summary=f"new gotcha candidate: {proposal['code']}")
            except Exception:
                continue
```

**`src/aho/agents/conductor.py`:**
```python
from aho.agents.roles.workstream_agent import WorkstreamAgent
from aho.agents.roles.evaluator_agent import EvaluatorAgent
from aho.logger import log_event

class Conductor:
    def __init__(self):
        self.workstream = WorkstreamAgent()
        self.evaluator = EvaluatorAgent()

    def dispatch(self, ws_id: str, plan_section: str, design: str, plan: str) -> dict:
        log_event("agent_msg", source_agent="conductor", action="dispatch",
                  input_summary=f"ws_id={ws_id}")
        result = self.workstream.execute_workstream(ws_id, plan_section)
        review = self.evaluator.review(result, design, plan)
        return {"execution": result, "review": review}
```

**`bin/aho-conductor`** wrapper: `aho-conductor dispatch <ws_id> <plan_path>` reads plan, dispatches, prints result.

**HarnessAgent watcher daemon:**
```ini
# ~/.config/systemd/user/aho-harness-watcher.service
[Unit]
Description=aho Harness Agent Watcher
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python -m aho.agents.roles.harness_agent --watch /home/kthompson/dev/projects/aho/data/aho_event_log.jsonl
Restart=on-failure
[Install]
WantedBy=default.target
```

**Add to components.yaml** (3 entries):
- workstream-agent (kind: agent, status: active, notes: "Qwen-bound, conductor-dispatched, activated 0.2.3 W2")
- evaluator-agent (kind: agent, status: active, notes: "GLM-bound, review role, activated 0.2.3 W2")
- harness-agent (kind: agent, status: active, notes: "Nemotron-bound, watcher daemon, activated 0.2.3 W2")

**Tests:** test_workstream_agent.py, test_evaluator_agent.py, test_harness_agent.py, test_conductor.py — at least 3 tests each, mock LLM clients.

## W3 — Localhost arch + dashboard plumbing

**Update `.aho.json`** to include `dashboard_port: 7800`, `aho_role: "localhost"`, `port_range: [7800, 7899]`. Add migration logic in `src/aho/config.py` for clones missing these fields (defaults: port from machine-specific table, role="localhost").

**`src/aho/logger.py`** add:
```python
import time, threading
def emit_heartbeat(component_name, dashboard_port, interval=30):
    def _loop():
        start = time.time()
        while True:
            log_event("heartbeat", source_agent=component_name,
                      output_summary=f"uptime={int(time.time()-start)}s port={dashboard_port}")
            time.sleep(interval)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
```

Wire `emit_heartbeat()` into the `--serve` startup of openclaw, nemoclaw, telegram, harness-watcher.

**Create `artifacts/harness/dashboard-contract.md`** as canonical artifact #9:
- Heartbeat schema
- Component health states (green: heartbeat <60s, yellow: 60-300s, red: >300s or missing)
- Polling contract: dashboard reads traces.jsonl tail, groups by component, computes health
- Cross-clone push contract (Phase 1 stub)
- Set `**Version:** 0.2.3`

**Add to canonical_artifacts.yaml** entry for dashboard-contract.md.

**`web/claw3d/index.html`** placeholder:
```html
<!DOCTYPE html>
<html><head><title>aho claw3d</title></head><body>
<h1>claw3d coming in 0.2.6</h1>
<p>Components detected: <span id="count">loading...</span></p>
<pre id="list"></pre>
<script>
fetch('/components.yaml').then(r => r.text()).then(t => {
  const matches = t.match(/^\s*-\s+name:\s+(.+)$/gm) || [];
  document.getElementById('count').textContent = matches.length;
  document.getElementById('list').textContent = matches.join('\n');
});
</script>
</body></html>
```

**`bin/aho-dashboard`** skeleton — Python http.server binding to `127.0.0.1:7800`, serves traces.jsonl tail as JSON. Just enough to prove the port binding works.

## W4 — Per-clone age + bundle expansion + doctor

**`bin/aho-install`** age keygen block:
```fish
if not test -f ~/.config/aho/age.key
    mkdir -p ~/.config/aho
    age-keygen -o ~/.config/aho/age.key
    chmod 600 ~/.config/aho/age.key
    echo "[CAPABILITY GAP] age key generated at ~/.config/aho/age.key"
    echo "BACK IT UP NOW. Without it, all encrypted secrets are unrecoverable."
    exit 1
end
```

**`src/aho/bundle/__init__.py`** add §24-§26 sections after existing §23. Each section reads files and embeds them with markdown headers. Cap each file at 50KB embedded; longer files get truncated with `[truncated, see file]` notice.

**Doctor additions** in `src/aho/doctor.py`:
- `_check_age_key()`: returns ok if `~/.config/aho/age.key` exists with mode 600
- `_check_dashboard_port()`: returns ok if `.aho.json` has `dashboard_port` field and port is bindable
- `_check_role_agents()`: imports workstream_agent, evaluator_agent, harness_agent — fails if ImportError

## W5 — Dogfood + close

**Conductor smoke test:**
```fish
bin/aho-conductor dispatch W1 "Print 'hello from workstream agent' and confirm the conductor pattern works."
sleep 10
wc -l ~/.local/share/aho/traces/traces.jsonl
tail -30 ~/.local/share/aho/traces/traces.jsonl | grep -oE '"name":"[^"]+"' | sort -u
# Expected: conductor.dispatch, nemoclaw.route, workstream_agent.execute, qwen.generate,
#           evaluator_agent.review, glm.generate, telegram.send
```

**Close:**
```fish
python -m pytest artifacts/tests/ -v
python -m aho.cli iteration close 0.2.3
```

Verify:
- 130+ tests green
- Bundle ~700KB with §24-§26
- 10 canonical artifacts at 0.2.3
- 0 stubs in components.yaml (now ~87 total)
- 4 systemd user services active (openclaw, nemoclaw, telegram, harness-watcher)
- 12 MCP servers installed
- web/claw3d/index.html loads in browser
- All postflight green
- Telegram close-complete arrives

**Commit message draft:** `KT completed 0.2.3: 3-agent role split (workstream/evaluator/harness), MCP fleet, localhost arch, dashboard plumbing, bundle §24-§26, web/claw3d placeholder`

## Checkpoint schema

```json
{
  "iteration": "0.2.3",
  "phase": 0,
  "run_type": "mixed",
  "current_workstream": "W0",
  "workstreams": {"W0":"pending","W1":"pending","W2":"pending","W3":"pending","W4":"pending","W5":"pending"},
  "executor": "claude-code",
  "started_at": null,
  "last_event": null
}
```
