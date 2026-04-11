# Investigation 9 — Telegram + OpenClaw + NemoClaw Partial State

**Date:** 2026-04-09
**Auditor:** Claude Code (Opus 4.6)

---

## W4 — Telegram Framework (Partial)

### File Inventory

```
src/iao/telegram/
├── __init__.py        (129 bytes) — imports send_message, send_iteration_complete
└── notifications.py   (1,958 bytes) — notification logic
```

Two files total. No bot framework, no handler modules, no configuration.

### Code Analysis

**`notifications.py`** contains:

- `_get_creds(project_code)` — retrieves Telegram bot token and chat ID from iao secrets store, with fallback to environment variables (`KJTCO_TELEGRAM_BOT_TOKEN`, `KJTCOM_TELEGRAM_CHAT_ID`).
- `send_message(project_code, text)` — sends a plain text message to a Telegram chat via the Bot API.
- `send_iteration_complete(project_code, iteration, bundle_path, run_report_path)` — sends a structured completion notification.

The code is clean and functional for its narrow scope. It uses the `requests` library directly (not python-telegram-bot) for simple message sending.

### CLI State

```
$ ./bin/iao telegram --help
usage: iao telegram [-h] {test} ...
```

Only one subcommand: `test`. No `init`, `status`, `start`, `stop`, or `configure` commands. The telegram CLI is minimal — it can send a test message but cannot manage a bot lifecycle.

### Dependencies

- `python-telegram-bot` v22.7 is installed but **not used** by iao's telegram module. The notifications module uses `requests` directly against the Telegram Bot API. The library is installed but appears unused by iao.
- The iao secrets store has `kjtco:TELEGRAM_BOT_TOKEN` registered.

### Missing: TelegramBotFramework

The 0.1.4 design envisioned a `TelegramBotFramework` class that would:
- Receive commands from Telegram (not just send notifications)
- Support init/test/status/start/stop lifecycle
- Act as a two-way communication channel between Kyle and the iao harness

None of this was built. What shipped is a one-way notification pipe: iao can send messages to Telegram, but cannot receive them.

### systemd status

No `kjtcom-telegram-bot` systemd user service was found (the legacy kjtcom bot is not running as a service on this machine).

---

## W5 — OpenClaw + NemoClaw (Stubs)

### File Inventory

```
src/iao/agents/
├── __init__.py      (115 bytes)
├── openclaw.py      (476 bytes) — stub
├── nemoclaw.py      (1,033 bytes) — stub
└── roles/
    ├── base_role.py    (283 bytes) — BaseRole class
    └── assistant.py    (297 bytes) — AssistantRole class
```

### Code Analysis

**`openclaw.py`:**
```python
"""Wrapper for open-interpreter (OpenClaw).

STUB: open-interpreter installation failed in iao 0.1.4 due to Python 3.14
and missing Rust compiler for tiktoken.
"""

class OpenClaw:
    def __init__(self, model: str = "qwen3.5:9b"):
        self.model = model

    def chat(self, message: str) -> str:
        raise NotImplementedError(
            "OpenClaw requires open-interpreter, which failed to install. "
            "See iao 0.1.4 build log W5 discrepancy."
        )
```

This is an explicit stub. The docstring documents why: Python 3.14 doesn't have a pre-built tiktoken wheel, and tiktoken requires a Rust compiler to build from source. Since open-interpreter depends on tiktoken, the install chain breaks.

**`nemoclaw.py`:**
```python
class NemoClawOrchestrator:
    def __init__(self, session_count: int = 1):
        self.sessions = [OpenClaw() for _ in range(session_count)]
        self.history = []

    def dispatch(self, task: str) -> str:
        # Commented out: classify task via Nemotron
        try:
            result = self.sessions[0].chat(task)
            ...
        except NotImplementedError as e:
            return f"Error: {e}"
```

NemoClaw creates OpenClaw sessions and dispatches tasks to them. Since OpenClaw is a stub, NemoClaw is effectively non-functional — every `dispatch()` call returns an error string.

The Nemotron classification step (routing tasks to appropriate sessions) is commented out with a note "In a real implementation, we would classify the task type."

**`roles/base_role.py`** and **`roles/assistant.py`** are minimal scaffolding — a base class with `name` and `instructions` fields, and a single `AssistantRole` implementation.

### Import Tests

```python
>>> from iao.agents.openclaw import OpenClaw
# Works — class is importable

>>> from iao.agents.nemoclaw import NemoClawOrchestrator
# Works — class is importable
```

Both import successfully. The imports don't fail because the stubs don't actually use open-interpreter at import time — they only fail when `.chat()` is called.

### open-interpreter Status

```python
>>> import interpreter
# Works — module imports

>>> interpreter.__version__
'unknown'
```

The `interpreter` module is importable, but its version is unknown. This suggests either a partial install or a compatibility shim. The actual open-interpreter functionality (launching an interactive coding session) is blocked by the tiktoken/Rust dependency chain.

### Missing Deliverables

| Deliverable | Status |
|---|---|
| `scripts/smoke_nemoclaw.py` | Does not exist |
| `docs/harness/agents-architecture.md` | Does not exist |
| iaomw-ADR-038 | Not in base.md |
| Functional OpenClaw session | Blocked by open-interpreter/tiktoken |
| Nemotron task routing | Commented out |
| Multi-session orchestration | Scaffolded but non-functional |

---

## Completion Assessment

| Component | Current State | What Would Complete It in 0.1.6 |
|---|---|---|
| **Telegram notifications** | Functional (send_message, send_iteration_complete) | Nothing — this works for its current scope |
| **Telegram bot framework** | Missing entirely | Build TelegramBotFramework with init/start/stop/status; add command handlers; wire to iao CLI |
| **Telegram CLI** | Only `test` subcommand | Add `init`, `status`, `configure` subcommands |
| **OpenClaw** | Stub (NotImplementedError) | Resolve tiktoken/Python 3.14 issue OR switch to an alternative to open-interpreter |
| **NemoClaw orchestrator** | Stub (delegates to broken OpenClaw) | Implement Nemotron task classification; make dispatch functional once OpenClaw works |
| **Agent roles** | Minimal scaffolding | Define role taxonomy, add specialized roles beyond AssistantRole |
| **Architecture docs** | Missing | Write `agents-architecture.md` documenting the OpenClaw→NemoClaw→Roles design |
| **ADRs** | ADR-037 (Telegram) and ADR-038 (Agents) missing | Write and add to base.md |

---

## Key Blocker: Python 3.14 + tiktoken

The fundamental blocker for OpenClaw/NemoClaw is the Python 3.14 + tiktoken incompatibility. Options:

1. **Wait for tiktoken to release a Python 3.14 wheel.** Unknown timeline.
2. **Install a Rust compiler** and build tiktoken from source. Requires `rustup` and build toolchain.
3. **Use a different code interpreter backend** that doesn't depend on tiktoken. Alternatives include direct Qwen integration via Ollama (which already works) or a custom REPL wrapper.
4. **Pin Python to 3.13** for iao. Significant environment change.

Option 3 is likely the most pragmatic for 0.1.6 — build OpenClaw as a thin Qwen-based code execution agent using Ollama directly, without depending on open-interpreter. This would bypass the tiktoken dependency entirely and leverage the model fleet that's already functional.
