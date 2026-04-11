"""OpenClaw — Qwen/Ollama-native execution primitive.

aho 0.1.7 W8 rebuild, 0.2.2 W1 global daemon.
NO dependency on open-interpreter, tiktoken, or Rust.
Pure Python stdlib + aho's existing QwenClient.

If anyone asks you to `pip install open-interpreter`, the request is wrong.
See artifacts/harness/base.md ahomw-ADR-040.
"""
import json
import shutil
import socketserver
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

from opentelemetry import trace

from aho.artifacts.qwen_client import QwenClient
from aho.logger import log_event

_tracer = trace.get_tracer("aho.openclaw")


class OpenClawSession:
    def __init__(
        self,
        model: str = "qwen3.5:9b",
        role: str = "assistant",
        system_prompt: Optional[str] = None,
    ):
        self.model = model
        self.role = role
        self.system_prompt = system_prompt or f"You are a helpful {role}. Be concise."
        self.client = QwenClient(model=model, verbose=False)
        self.history: list[dict] = []
        self.session_id = str(uuid.uuid4())[:8]
        self.workdir = Path(f"/tmp/openclaw-{self.session_id}")
        self.workdir.mkdir(parents=True, exist_ok=True)
        log_event("session_start", "openclaw", model, "init",
                  output_summary=f"session={self.session_id} role={role}")

    def chat(self, message: str) -> str:
        with _tracer.start_as_current_span("openclaw.chat") as span:
            span.set_attribute("model", self.model)
            span.set_attribute("role", self.role)
            span.set_attribute("message_length", len(message))
            log_event("llm_call", "openclaw", self.model, "chat",
                      input_summary=message[:200])
            self.history.append({"role": "user", "content": message})
            conversation = "\n\n".join(
                f"{turn['role'].upper()}: {turn['content']}" for turn in self.history
            )
            prompt = f"{conversation}\n\nASSISTANT:"
            response = self.client.generate(prompt, system=self.system_prompt)
            self.history.append({"role": "assistant", "content": response})
            span.set_attribute("response_length", len(response))
            span.set_attribute("status", "ok")
            return response

    def execute_code(self, code: str, language: str = "python", timeout: int = 30) -> dict:
        with _tracer.start_as_current_span("openclaw.execute_code") as span:
            span.set_attribute("language", language)
            span.set_attribute("code_length", len(code))
            log_event("command", "openclaw", language, "execute_code",
                      input_summary=code[:200])
            if language == "python":
                cmd = ["python3", "-c", code]
            elif language == "bash":
                cmd = ["bash", "-c", code]
            else:
                span.set_attribute("status", "error")
                return {"stdout": "", "stderr": f"unsupported language: {language}", "exit_code": -1, "timed_out": False}

            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.workdir),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env={"PATH": "/usr/bin:/bin", "HOME": str(self.workdir)},
                )
                span.set_attribute("exit_code", result.returncode)
                span.set_attribute("status", "ok" if result.returncode == 0 else "error")
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "timed_out": False,
                }
            except subprocess.TimeoutExpired:
                span.set_attribute("status", "timeout")
                return {"stdout": "", "stderr": f"timeout after {timeout}s", "exit_code": -1, "timed_out": True}

    def close(self):
        """Clean up workdir."""
        try:
            shutil.rmtree(self.workdir, ignore_errors=True)
        except Exception:
            pass


# --- Global daemon (--serve mode) ---

SOCK_PATH = Path.home() / ".local/share/aho/openclaw.sock"

# Session pool: keyed by role name
_sessions: dict[str, OpenClawSession] = {}
_MAX_SESSIONS = 5


def get_or_create_session(role: str = "assistant") -> OpenClawSession:
    """Get an existing session for a role, or create one (capped)."""
    if role in _sessions:
        return _sessions[role]
    if len(_sessions) >= _MAX_SESSIONS:
        oldest_key = next(iter(_sessions))
        _sessions[oldest_key].close()
        del _sessions[oldest_key]
    session = OpenClawSession(role=role)
    _sessions[role] = session
    return session


class OpenClawHandler(socketserver.StreamRequestHandler):
    """Handle one request on the Unix socket.

    Protocol: one line of JSON in, one line of JSON out.
    Commands: chat, execute, status, close
    """

    def handle(self):
        try:
            raw = self.rfile.readline().decode("utf-8").strip()
            if not raw:
                return
            req = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._reply({"error": "invalid JSON"})
            return

        cmd = req.get("cmd", "")
        role = req.get("role", "assistant")

        if cmd == "chat":
            try:
                session = get_or_create_session(role)
                text = session.chat(req.get("message", ""))
                self._reply({"ok": True, "response": text, "session": session.session_id})
            except Exception as e:
                self._reply({"ok": False, "error": str(e)})
        elif cmd == "execute":
            try:
                session = get_or_create_session(role)
                result = session.execute_code(
                    req.get("code", ""),
                    language=req.get("language", "python"),
                    timeout=req.get("timeout", 30),
                )
                self._reply({"ok": True, **result, "session": session.session_id})
            except Exception as e:
                self._reply({"ok": False, "error": str(e)})
        elif cmd == "status":
            info = {
                "ok": True,
                "sessions": {r: s.session_id for r, s in _sessions.items()},
                "session_count": len(_sessions),
            }
            self._reply(info)
        elif cmd == "close":
            if role in _sessions:
                _sessions[role].close()
                del _sessions[role]
            self._reply({"ok": True, "closed": role})
        else:
            self._reply({"error": f"unknown command: {cmd}"})

    def _reply(self, data: dict):
        self.wfile.write((json.dumps(data) + "\n").encode("utf-8"))


def serve():
    """Start the OpenClaw daemon listening on a Unix socket."""
    SOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SOCK_PATH.exists():
        SOCK_PATH.unlink()
    print(f"[openclaw] listening on {SOCK_PATH}", flush=True)
    server = socketserver.UnixStreamServer(str(SOCK_PATH), OpenClawHandler)
    try:
        server.serve_forever()
    finally:
        for s in _sessions.values():
            s.close()
        _sessions.clear()
        if SOCK_PATH.exists():
            SOCK_PATH.unlink()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    else:
        print("Usage: python -m aho.agents.openclaw --serve")
        sys.exit(1)
