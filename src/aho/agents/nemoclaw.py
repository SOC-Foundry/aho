"""NemoClaw — Nemotron-driven orchestrator for OpenClaw sessions.

aho 0.1.7 W8 rebuild. Routes tasks to OpenClaw sessions by role using
Nemotron classification. Replaces the 0.1.4 stub that raised NotImplementedError.
"""
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

        self.sessions = [OpenClawSession(role=r) for r in roles]
        self.roles = roles

    def dispatch(self, task: str, role: Optional[str] = None) -> str:
        if role is None:
            role = classify(task, DEFAULT_ROLES, bias="Prefer 'assistant' for general tasks. Use 'code_runner' only if the task requires executing code. Use 'reviewer' only if the task is about evaluating an artifact.")

        with _tracer.start_as_current_span(f"nemoclaw.dispatch.{role}") as span:
            span.set_attribute("role", role)
            span.set_attribute("task_length", len(task))
            log_event("agent_msg", "nemoclaw", role, "dispatch",
                      input_summary=task[:200], output_summary=f"classified_role={role}")

            matching_session = next((s for s in self.sessions if s.role == role), self.sessions[0])
            result = matching_session.chat(task)
            span.set_attribute("response_length", len(result))
            span.set_attribute("status", "ok")
            return result

    def collect(self) -> dict:
        return {s.role: s.history for s in self.sessions}

    def close_all(self):
        for s in self.sessions:
            s.close()
