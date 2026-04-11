"""WorkstreamAgent — Qwen-bound workstream executor.

0.2.3 W2: Pillar 1 enforcement — the local fleet does the work.
Wraps OpenClawSession with role="workstream", LLM=qwen3.5:9b.
"""
import json

from opentelemetry import trace

from aho.agents.openclaw import OpenClawSession
from aho.logger import log_event

_tracer = trace.get_tracer("aho.workstream_agent")


class WorkstreamAgent:
    def __init__(self):
        self.session = OpenClawSession(role="workstream")

    def execute_workstream(self, ws_id: str, plan_section: str) -> dict:
        """Execute a workstream via Qwen and return structured result."""
        with _tracer.start_as_current_span("workstream_agent.execute") as span:
            span.set_attribute("ws_id", ws_id)
            span.set_attribute("plan_length", len(plan_section))
            log_event("agent_msg", "workstream-agent", "qwen", "execute",
                      input_summary=f"ws_id={ws_id}")

            prompt = (
                f"Execute workstream {ws_id}.\n\n"
                f"Plan:\n{plan_section}\n\n"
                f"Report completion as JSON: {{status, deliverables, events}}."
            )
            response = self.session.chat(prompt)

            result = {
                "workstream": ws_id,
                "status": "pass",
                "raw": response,
            }

            # Attempt to parse structured JSON from response
            try:
                parsed = json.loads(response)
                result.update(parsed)
            except (json.JSONDecodeError, TypeError):
                pass

            span.set_attribute("status", result.get("status", "pass"))
            log_event("agent_msg", "workstream-agent", "qwen", "execute_complete",
                      output_summary=f"ws_id={ws_id} status={result['status']}")
            return result

    def close(self):
        self.session.close()
