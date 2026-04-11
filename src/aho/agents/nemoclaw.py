"""NemoClaw — Nemotron-driven orchestrator for OpenClaw sessions.

aho 0.1.7 W8 rebuild, 0.2.2 W2 global daemon.
Routes tasks to OpenClaw sessions by role using Nemotron classification.
"""
import json
import socketserver
import sys
from pathlib import Path
from typing import Optional

from opentelemetry import trace

from aho.agents.openclaw import OpenClawSession
from aho.artifacts.nemotron_client import classify
from aho.logger import log_event

_tracer = trace.get_tracer("aho.nemoclaw")


DEFAULT_ROLES = ["assistant", "code_runner", "reviewer"]


class NemoClawOrchestrator:
    def __init__(self, session_count: int = 1, roles: Optional[list[str]] = None):
        if roles is None:
            roles = ["assistant"] * session_count
        else:
            roles = roles[:session_count] + ["assistant"] * max(0, session_count - len(roles))

        from aho.orchestrator_config import get_openclaw_model
        model = get_openclaw_model()
        self.sessions = [OpenClawSession(model=model, role=r) for r in roles]
        self.roles = roles

    def route(self, task: str) -> str:
        """Classify a task into a role using Nemotron."""
        with _tracer.start_as_current_span("nemoclaw.route") as span:
            span.set_attribute("task_length", len(task))
            role = classify(
                task, DEFAULT_ROLES,
                bias="Prefer 'assistant' for general tasks. Use 'code_runner' only if the task requires executing code. Use 'reviewer' only if the task is about evaluating an artifact.",
            )
            span.set_attribute("classified_role", role)
            log_event("agent_msg", "nemoclaw", "nemotron", "route",
                      input_summary=task[:200], output_summary=f"role={role}")
            return role

    def dispatch(self, task: str, role: Optional[str] = None) -> str:
        if role is None:
            role = self.route(task)

        with _tracer.start_as_current_span(f"nemoclaw.dispatch") as span:
            span.set_attribute("role", role)
            span.set_attribute("task_length", len(task))
            log_event("agent_msg", "nemoclaw", role, "dispatch",
                      input_summary=task[:200], output_summary=f"classified_role={role}")

            matching_session = next((s for s in self.sessions if s.role == role), self.sessions[0])
            try:
                result = matching_session.chat(task)
            except Exception as e:
                span.set_attribute("status", "error")
                span.record_exception(e)
                return f"[error] {e}"
            span.set_attribute("response_length", len(result))
            span.set_attribute("status", "ok")
            return result

    def collect(self) -> dict:
        return {s.role: s.history for s in self.sessions}

    def close_all(self):
        for s in self.sessions:
            s.close()


# --- Global daemon (--serve mode) ---

SOCK_PATH = Path.home() / ".local/share/aho/nemoclaw.sock"

# Global orchestrator instance for the daemon
_orchestrator: Optional[NemoClawOrchestrator] = None


def _get_orchestrator() -> NemoClawOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NemoClawOrchestrator(session_count=3, roles=DEFAULT_ROLES)
    return _orchestrator


class NemoClawHandler(socketserver.StreamRequestHandler):
    """Handle one request on the NemoClaw Unix socket.

    Protocol: one line of JSON in, one line of JSON out.
    Commands: dispatch, route, status
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
        orch = _get_orchestrator()

        if cmd == "dispatch":
            try:
                task = req.get("task", "")
                role = req.get("role")
                result = orch.dispatch(task, role=role)
                self._reply({"ok": True, "response": result})
            except Exception as e:
                self._reply({"ok": False, "error": str(e)})
        elif cmd == "route":
            try:
                task = req.get("task", "")
                role = orch.route(task)
                self._reply({"ok": True, "role": role})
            except Exception as e:
                self._reply({"ok": False, "error": str(e)})
        elif cmd == "status":
            sessions = {s.role: s.session_id for s in orch.sessions}
            history_counts = {s.role: len(s.history) for s in orch.sessions}
            self._reply({
                "ok": True,
                "sessions": sessions,
                "session_count": len(orch.sessions),
                "history": history_counts,
            })
        else:
            self._reply({"error": f"unknown command: {cmd}"})

    def _reply(self, data: dict):
        self.wfile.write((json.dumps(data) + "\n").encode("utf-8"))


def serve():
    """Start the NemoClaw daemon listening on a Unix socket."""
    from aho.logger import emit_heartbeat
    SOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SOCK_PATH.exists():
        SOCK_PATH.unlink()
    emit_heartbeat("nemoclaw")
    print(f"[nemoclaw] listening on {SOCK_PATH}", flush=True)
    server = socketserver.UnixStreamServer(str(SOCK_PATH), NemoClawHandler)
    try:
        server.serve_forever()
    finally:
        if _orchestrator:
            _orchestrator.close_all()
        if SOCK_PATH.exists():
            SOCK_PATH.unlink()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    else:
        print("Usage: python -m aho.agents.nemoclaw --serve")
        sys.exit(1)
