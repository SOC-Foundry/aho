"""NemoClaw — Nemotron-driven orchestrator for OpenClaw sessions.

aho 0.1.7 W8 rebuild. Routes tasks to OpenClaw sessions by role using
Nemotron classification. Replaces the 0.1.4 stub that raised NotImplementedError.
"""
from typing import Optional

from aho.agents.openclaw import OpenClawSession
from aho.artifacts.nemotron_client import classify
from aho.logger import log_event


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
            # Classify the task
            role = classify(task, DEFAULT_ROLES, bias="Prefer 'assistant' for general tasks. Use 'code_runner' only if the task requires executing code. Use 'reviewer' only if the task is about evaluating an artifact.")

        log_event("agent_msg", "nemoclaw", role, "dispatch",
                  input_summary=task[:200], output_summary=f"classified_role={role}")

        # Find first session with this role
        matching_session = next((s for s in self.sessions if s.role == role), self.sessions[0])
        return matching_session.chat(task)

    def collect(self) -> dict:
        return {s.role: s.history for s in self.sessions}

    def close_all(self):
        for s in self.sessions:
            s.close()
