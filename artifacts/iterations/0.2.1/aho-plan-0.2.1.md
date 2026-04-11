# aho 0.2.1 — Plan

**Phase:** 0 | **Iteration:** 2 | **Run:** 1 | **run_type:** mixed
**Agent:** Claude Code single-agent throughout

## Launch

```fish
cd ~/dev/projects/aho
set -x AHO_ITERATION 0.2.1
mkdir -p ~/dev/backups
tar czf ~/dev/backups/aho-pre-0.2.1.tar.gz --exclude=data/chroma --exclude=.venv --exclude=app/build --exclude=.git .
printf '{"aho_version":"0.1","name":"aho","project_code":"ahomw","artifact_prefix":"aho","current_iteration":"0.2.1","phase":0,"mode":"active","created_at":"2026-04-08T12:00:00+00:00","bundle_format":"bundle","last_completed_iteration":"0.1.16"}\n' > .aho.json
mkdir -p artifacts/iterations/0.2.1
tmux new-session -d -s aho-0.2.1 -c ~/dev/projects/aho
tmux send-keys -t aho-0.2.1 'cd ~/dev/projects/aho; claude --dangerously-skip-permissions' Enter
```

## W0 — Hygiene + carryovers

```fish
# .gitignore additions
printf '\ndata/chroma/\napp/build/\n__pycache__/\n*.pyc\n.venv/\n' >> .gitignore

# pyproject version bump
sed -i 's|^version = "0\.1\.16"|version = "0.2.1"|' pyproject.toml

# Verify 0.15.1 directory absent
test -d artifacts/iterations/0.15.1; and echo "STILL EXISTS — investigate"; or echo "OK clean"

# build_log_complete fix
rg -n "design.*path\|design_path" src/aho/postflight/build_log_complete.py
```

Edit `src/aho/postflight/build_log_complete.py` — locate the design doc path computation and replace with:
```python
from aho.paths import get_artifacts_root
design_path = get_artifacts_root() / "iterations" / iteration / f"aho-design-{iteration}.md"
```

Bump 7 canonical artifacts to 0.2.1:
```fish
sed -i 's|\*\*Version:\*\* 0\.1\.16|**Version:** 0.2.1|' artifacts/harness/base.md
sed -i 's|aho 0\.1\.16 W0 — close sequence repair|aho 0.2.1 W0 — global deployment|' artifacts/harness/base.md

sed -i 's|\*\*Version:\*\* 0\.1\.16|**Version:** 0.2.1|' artifacts/harness/agents-architecture.md
sed -i 's|^# Agents Architecture — aho 0\.1\.16|# Agents Architecture — aho 0.2.1|' artifacts/harness/agents-architecture.md
sed -i 's|Iteration 0\.1\.13 marks the final realignment|Iteration 0.2.1 begins global deployment phase|' artifacts/harness/agents-architecture.md

sed -i 's|\*\*Version:\*\* 0\.1\.16|**Version:** 0.2.1|' artifacts/harness/model-fleet.md

sed -i 's|\*\*Charter version:\*\* 0\.1\.16|**Charter version:** 0.2.1|' artifacts/phase-charters/aho-phase-0.md

sed -i 's|\*\*Iteration 0\.1\.16\*\*|**Iteration 0.2.1**|' README.md
sed -i 's|aho v0\.1\.16|aho v0.2.1|' README.md

sed -i 's|updated during 0\.1\.16|updated during 0.2.1|' CLAUDE.md
sed -i 's|updated during 0\.1\.16|updated during 0.2.1|' GEMINI.md
```

Refresh MANIFEST:
```fish
python -c "
import json, hashlib, pathlib
root = pathlib.Path('src/aho')
files = {}
for p in sorted(root.rglob('*.py')):
    if p.name == '__init__.py': continue
    files[str(p)] = hashlib.blake2b(p.read_bytes(), digest_size=8).hexdigest()
manifest = {'package': 'aho', 'version': '0.2.1', 'files': files}
pathlib.Path('MANIFEST.json').write_text(json.dumps(manifest, indent=2))
print(f'MANIFEST refreshed: {len(files)} files')
"
```

**W0 Gate:**
```fish
python -c "from aho.postflight.canonical_artifacts_current import check; r = check(); assert r['status'] == 'ok', r"
python -m pytest artifacts/tests/ -x
```

## W1 — Global install architecture design

Create `artifacts/harness/global-deployment.md` with the seven sections from the design doc: hybrid systemd model, install paths table, component lifecycle (install/enable/start/status/stop/restart/uninstall), capability gap inventory, uninstall safety contract, idempotency contract, P3 prereqs.

Add to canonical artifacts list (`artifacts/harness/canonical_artifacts.yaml`) — this becomes the 8th canonical artifact, version-tracked from now on.

**W1 Gate:** file exists, canonical artifacts gate updated to 8 entries, gate runs green.

## W2 — `bin/aho-install` real implementation

```fish
# Backup existing skeleton
cp bin/aho-install bin/aho-install.0.1.13.skeleton.bak
```

Replace `bin/aho-install` with idempotent fish script. Steps from design doc W2. Key sections:
1. Platform check (`/etc/arch-release`, `which fish`)
2. XDG dir creation (`mkdir -p`, idempotent)
3. `pip install -e . --break-system-packages` from project root
4. Create `~/.config/systemd/user/` if absent
5. Linger verification: `loginctl show-user $USER --property=Linger | grep -q Linger=yes; or echo "[CAPABILITY GAP] run: sudo loginctl enable-linger $USER"`
6. Print install summary

Create `bin/aho-uninstall` per design doc spec. Both wrappers `chmod +x`.

Wire both into `src/aho/doctor.py` quick checks.

Smoke test: 
```fish
bin/aho-install 2>&1 | tee /tmp/aho-install.log
bin/aho-install 2>&1 | tee /tmp/aho-install-2.log  # idempotency check
diff /tmp/aho-install.log /tmp/aho-install-2.log  # should show only timestamps
```

**W2 Gate:** install runs idempotently, uninstall script exists, doctor wires both.

## W3 — Native OTEL collector as systemd user service

```fish
# Latest stable detection
set OTEL_VERSION (curl -s https://api.github.com/repos/open-telemetry/opentelemetry-collector-releases/releases/latest | grep '"tag_name"' | sed -E 's/.*"v([^"]+)".*/\1/')
echo "OTEL collector version: $OTEL_VERSION"

# Download
set OTEL_TARBALL "otelcol-contrib_${OTEL_VERSION}_linux_amd64.tar.gz"
set OTEL_URL "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v${OTEL_VERSION}/${OTEL_TARBALL}"
mkdir -p /tmp/aho-otel-install
cd /tmp/aho-otel-install
curl -fsSL -o $OTEL_TARBALL $OTEL_URL
tar xzf $OTEL_TARBALL
mkdir -p ~/.local/bin
mv otelcol-contrib ~/.local/bin/aho-otel-collector
chmod +x ~/.local/bin/aho-otel-collector
cd ~/dev/projects/aho
rm -rf /tmp/aho-otel-install
```

Create `~/.config/aho/otel-collector.yaml` with the YAML from design doc W3.

Create `~/.config/systemd/user/aho-otel-collector.service` with the unit file from design doc W3.

```fish
mkdir -p ~/.local/share/aho/traces
systemctl --user daemon-reload
systemctl --user enable --now aho-otel-collector.service
systemctl --user status aho-otel-collector --no-pager
```

Update `src/aho/logger.py`:
- Default `OTLP endpoint = 127.0.0.1:4317`
- Change gating from `AHO_OTEL_ENABLED=1` (opt-in) to `AHO_OTEL_DISABLED=1` (opt-out)
- Default behavior: always emit OTEL when collector reachable, fall back silently on connection failure

Smoke send:
```fish
python -c "
from aho.logger import log_event
log_event(event_type='smoke', source_agent='claude-code', target='otel-collector', action='verify', iteration='0.2.1')
"
sleep 2
test -s ~/.local/share/aho/traces/traces.jsonl; and echo "TRACE OK"; or echo "TRACE MISSING"
```

Create `bin/aho-otel-status`:
```fish
#!/usr/bin/env fish
systemctl --user status aho-otel-collector --no-pager
echo "---"
echo "Last trace: $(stat -c %y ~/.local/share/aho/traces/traces.jsonl 2>/dev/null || echo 'none')"
echo "Trace count: $(wc -l < ~/.local/share/aho/traces/traces.jsonl 2>/dev/null || echo 0)"
```

`chmod +x bin/aho-otel-status`

**W3 Gate:** collector running as user service, smoke send appears in traces.jsonl, logger defaults to always-on.

## W4 — Global Ollama + model fleet pre-pull

```fish
which ollama
or echo "[CAPABILITY GAP] Ollama not installed. Run: curl -fsSL https://ollama.com/install.sh | sh"
```

If gap: halt, write checkpoint, notify Kyle. Otherwise:

```fish
systemctl status ollama --no-pager
sudo systemctl enable --now ollama  # capability gap if not enabled, agent halts
```

Pre-pull models:
```fish
for model in qwen3.5:9b nemotron-mini:4b haervwe/GLM-4.6V-Flash-9B nomic-embed-text
    if ollama list | grep -q $model
        echo "✓ $model present"
    else
        echo "Pulling $model..."
        ollama pull $model
        or begin; echo "[CAPABILITY GAP] Pull failed for $model"; exit 1; end
    end
end
ollama list
```

Create `bin/aho-models-status`:
```fish
#!/usr/bin/env fish
curl -s http://localhost:11434/api/tags | python -c "
import json, sys
data = json.loads(sys.stdin.read())
print(f'{\"NAME\":<40} {\"SIZE\":<10} {\"MODIFIED\"}')
for m in data.get('models', []):
    size_gb = m['size'] / (1024**3)
    print(f'{m[\"name\"]:<40} {size_gb:>6.2f}GB  {m[\"modified_at\"][:19]}')
"
```

`chmod +x bin/aho-models-status`

Add to `src/aho/doctor.py` quick checks: query `localhost:11434/api/tags`, verify all 4 models present, FAIL if any missing.

**W4 Gate:** all 4 models present, doctor check green, models-status wrapper works.

## W5 — Component instrumentation pass

For each of 6 files, wrap primary methods in OTEL spans. Pattern (qwen_client.py example):

```python
from opentelemetry import trace
tracer = trace.get_tracer("aho.qwen_client")

def generate(self, prompt: str, **kwargs):
    with tracer.start_as_current_span("qwen.generate") as span:
        span.set_attribute("model", "qwen3.5:9b")
        span.set_attribute("prompt_length", len(prompt))
        span.set_attribute("temperature", kwargs.get("temperature", 0.7))
        span.set_attribute("streaming", kwargs.get("stream", False))
        try:
            result = self._do_generate(prompt, **kwargs)
            span.set_attribute("completion_tokens", result.get("eval_count", 0))
            span.set_attribute("prompt_tokens", result.get("prompt_eval_count", 0))
            span.set_attribute("latency_ms", result.get("total_duration", 0) / 1e6)
            span.set_attribute("status", "ok")
            return result
        except Exception as e:
            span.set_attribute("status", "error")
            span.record_exception(e)
            raise
```

Apply same pattern (with appropriate attributes) to:
- `src/aho/artifacts/nemotron_client.py` — `classify()` method
- `src/aho/artifacts/glm_client.py` — `analyze()` and `vision()` methods
- `src/aho/agents/openclaw.py` — `dispatch()` and `execute_code()` methods
- `src/aho/agents/nemoclaw.py` — `route()` and `dispatch()` methods
- `src/aho/telegram/notifications.py` — `send()` method (stub still emits span)

Create `artifacts/tests/test_otel_instrumentation.py` with mock OTLP receiver verifying span emission for each of the 6 components.

**W5 Gate:** new test file passes, smoke sends produce 6 distinct span types in traces.jsonl.

## W6 — Dogfood + close

```fish
python -m pytest artifacts/tests/ -v
aho doctor
```

Smoke synthetic iteration:
```fish
python -c "
from aho.artifacts.qwen_client import QwenClient
from aho.artifacts.nemotron_client import NemotronClient
from aho.agents.openclaw import OpenClaw
from aho.telegram.notifications import send
qwen = QwenClient()
qwen.generate('Say hello in 5 words')
nemo = NemotronClient()
nemo.classify('test', ['a', 'b'])
oc = OpenClaw()
oc.dispatch('test task')
send('smoke test', priority='low')
"
sleep 3
wc -l ~/.local/share/aho/traces/traces.jsonl
```

Run iteration close:
```fish
python -m aho.cli iteration close 0.2.1
```

Verify:
- Bundle exists at `artifacts/iterations/0.2.1/aho-bundle-0.2.1.md`
- Run file shows agent attribution and component section
- All postflight gates green
- `.aho.json` shows `last_completed_iteration: 0.2.1`
- Checkpoint closed

Print git commit message draft for Kyle:
```
Echo "
COMMIT MESSAGE DRAFT (Kyle pushes manually):
---
KT completed 0.2.1: global deployment architecture, native OTEL collector, model fleet pre-pull, component instrumentation
---
"
```

**W6 Gate:** zero false-positive postflight failures, smoke trace count > 6 spans, all artifacts present, ready for Kyle git push.

## Capability gaps expected

- **W2:** Linger verification — should pass (already enabled)
- **W4:** Ollama install (if absent), model pulls (if disk/network constrained), `sudo systemctl enable ollama`
- **W6:** Kyle manual git add/commit/push (Pillar 11)

## Checkpoint schema

```json
{
  "iteration": "0.2.1",
  "phase": 0,
  "run_type": "mixed",
  "current_workstream": "W0",
  "workstreams": {"W0":"pending","W1":"pending","W2":"pending","W3":"pending","W4":"pending","W5":"pending","W6":"pending"},
  "executor": "claude-code",
  "started_at": null,
  "last_event": null
}
```
