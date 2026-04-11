"""OpenClaw — Qwen/Ollama-native execution primitive.

aho 0.1.7 W8 rebuild. NO dependency on open-interpreter, tiktoken, or Rust.
Pure Python stdlib + aho's existing QwenClient.

If anyone asks you to `pip install open-interpreter`, the request is wrong.
See artifacts/harness/base.md ahomw-ADR-040.
"""
import json
import subprocess
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
        # Clean up workdir
        try:
            import shutil
            shutil.rmtree(self.workdir, ignore_errors=True)
        except Exception:
            pass
