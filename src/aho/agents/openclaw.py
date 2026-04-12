"""OpenClaw — Qwen/Ollama-native execution primitive.

aho 0.1.7 W8 rebuild, 0.2.2 W1 global daemon.
NO dependency on open-interpreter, tiktoken, or Rust.
Pure Python stdlib + aho's existing QwenClient.

If anyone asks you to `pip install open-interpreter`, the request is wrong.
See artifacts/harness/base.md ahomw-ADR-040.
"""
import json
import os
import shutil
import socketserver
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

from opentelemetry import trace

from datetime import datetime, timezone

from aho.artifacts.qwen_client import QwenClient
from aho.logger import log_event

_tracer = trace.get_tracer("aho.openclaw")


def _detect_and_truncate_repetition(text: str, threshold: float = 0.3, min_phrase_len: int = 20) -> str:
    """Detect and truncate repetitive LLM output.

    If any phrase of min_phrase_len+ chars appears enough times to constitute
    threshold% of the output, truncate at the second occurrence.
    """
    if len(text) < min_phrase_len * 3:
        return text

    # Check for repeated lines
    lines = text.split("\n")
    if len(lines) > 5:
        from collections import Counter
        line_counts = Counter(line.strip() for line in lines if len(line.strip()) >= min_phrase_len)
        for line_text, count in line_counts.most_common(3):
            repeated_chars = count * len(line_text)
            if repeated_chars / len(text) > threshold:
                # Truncate: keep up to second occurrence
                first_idx = text.find(line_text)
                second_idx = text.find(line_text, first_idx + len(line_text))
                if second_idx > 0:
                    truncated = text[:second_idx].rstrip()
                    log_event("repetition_detected", "openclaw", "qwen", "truncate",
                              output_summary=f"truncated at {second_idx}/{len(text)} chars")
                    return truncated + "\n\n[output truncated — repetition detected]"

    return text


class OpenClawSession:
    def __init__(
        self,
        model: str = None,
        role: str = "assistant",
        system_prompt: Optional[str] = None,
    ):
        if model is None:
            from aho.orchestrator_config import get_openclaw_model
            model = get_openclaw_model()
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
            # Repetition detector: truncate if >30% of response is repeated phrases
            response = _detect_and_truncate_repetition(response)
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

def _get_sock_path():
    """Socket at /run/user/$UID/openclaw.sock (XDG_RUNTIME_DIR)."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return Path(runtime_dir) / "openclaw.sock"

SOCK_PATH = _get_sock_path()

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


def _read_cwd_context(cwd: Path, max_files: int = 10, max_file_size: int = 8192) -> str:
    """Read key files from cwd to build context for the agent.

    Scans for common file types, reads up to max_files files,
    truncates each to max_file_size bytes. Returns a formatted context string.
    """
    if not cwd.is_dir():
        return f"[CWD not found: {cwd}]"

    context_parts = [f"Working directory: {cwd}\n"]
    # List directory contents
    try:
        entries = sorted(cwd.iterdir())
        listing = []
        for e in entries[:50]:  # cap listing
            kind = "dir" if e.is_dir() else "file"
            size = e.stat().st_size if e.is_file() else 0
            listing.append(f"  {e.name} ({kind}, {size}b)")
        context_parts.append("Directory listing:\n" + "\n".join(listing))
    except PermissionError:
        context_parts.append("[Permission denied reading directory]")

    # Read text files
    text_extensions = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
                       ".cfg", ".ini", ".sh", ".fish", ".rs", ".go", ".js", ".ts",
                       ".html", ".css", ".dart", ".xml", ".csv"}
    files_read = 0
    for entry in sorted(cwd.iterdir()):
        if files_read >= max_files:
            break
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in text_extensions:
            continue
        if entry.name.startswith("."):
            continue
        try:
            content = entry.read_text(errors="replace")[:max_file_size]
            if len(content) == max_file_size:
                content += "\n[... truncated]"
            context_parts.append(f"\n--- {entry.name} ---\n{content}")
            files_read += 1
        except (PermissionError, OSError):
            continue

    return "\n".join(context_parts)


def _get_run_instructions() -> str:
    """Load persona 3 agent instructions from installed location."""
    # Try installed location first, then repo
    for base in [
        Path.home() / ".local/share/aho/agents",
        Path(__file__).resolve().parent.parent.parent.parent,  # repo root
    ]:
        run_md = base / "CLAUDE-run.md"
        if run_md.exists():
            return run_md.read_text()
    return "You are a helpful assistant. Execute the task concisely."


def _write_run_output(cwd: Path, task: str, response: str, model: str) -> Path:
    """Write structured output to $CWD/aho-output/run-<ts>.md."""
    output_dir = cwd / "aho-output"
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output_path = output_dir / f"run-{ts}.md"
    content = (
        f"# aho run output\n\n"
        f"**Task:** {task}\n"
        f"**CWD:** {cwd}\n"
        f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}\n"
        f"**Agent:** {model}\n\n"
        f"---\n\n"
        f"{response}\n"
    )
    output_path.write_text(content)
    return output_path


def _route_agent(task: str, agent_hint: str = None) -> str:
    """Route task to appropriate model per Q1 decision.

    Size-based: Qwen local for tasks under 2000 tokens, Claude API above.
    agent_hint overrides if provided.
    """
    if agent_hint:
        return agent_hint
    # Rough token estimate: ~4 chars per token
    estimated_tokens = len(task) // 4
    if estimated_tokens < 2000:
        from aho.orchestrator_config import get_openclaw_model
        return get_openclaw_model()
    return "claude"  # Would need API dispatch; for now returns model name


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
        except ConnectionResetError:
            # Errno 104: client disconnected before we could read
            return
        except OSError as e:
            if e.errno == 11:  # EAGAIN — non-blocking socket not ready
                import time as _time
                _time.sleep(0.1)
                try:
                    raw = self.rfile.readline().decode("utf-8").strip()
                    if not raw:
                        return
                    req = json.loads(raw)
                except Exception:
                    return
            else:
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
        elif cmd == "run":
            try:
                task = req.get("task", "")
                cwd = Path(req.get("cwd", os.getcwd()))
                agent_hint = req.get("agent_hint")

                # Build context from cwd files
                file_context = _read_cwd_context(cwd)

                # Load persona 3 instructions
                instructions = _get_run_instructions()

                # Route to appropriate model
                model = _route_agent(task + file_context, agent_hint)

                # Create session with file-aware system prompt
                session = OpenClawSession(
                    model=model if model != "claude" else None,
                    role="run",
                    system_prompt=instructions,
                )

                # Compose message with file context
                full_message = (
                    f"Task: {task}\n\n"
                    f"Files in working directory:\n{file_context}"
                )

                response = session.chat(full_message)

                # Write output file
                output_path = _write_run_output(cwd, task, response, session.model)

                self._reply({
                    "ok": True,
                    "response": response,
                    "output_path": str(output_path),
                    "model": session.model,
                    "session": session.session_id,
                })
                session.close()
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
        try:
            self.wfile.write((json.dumps(data) + "\n").encode("utf-8"))
        except (ConnectionResetError, BrokenPipeError, OSError):
            # Errno 104 / EPIPE: client disconnected before response sent
            pass


def serve():
    """Start the OpenClaw daemon listening on a Unix socket."""
    from aho.logger import emit_heartbeat
    SOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SOCK_PATH.exists():
        SOCK_PATH.unlink()
    emit_heartbeat("openclaw")
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
