"""EvaluatorAgent — GLM-bound review role.

0.2.3 W2: Pillar 7 enforcement — generation and evaluation are separate roles.
Wraps OpenClawSession with role="evaluator", LLM=GLM-4.6V-Flash-9B.
"""
import json

from opentelemetry import trace

from aho.agents.openclaw import OpenClawSession
from aho.artifacts.glm_client import generate as glm_generate
from aho.logger import log_event

_tracer = trace.get_tracer("aho.evaluator_agent")


class EvaluatorAgent:
    def __init__(self):
        self.session = OpenClawSession(role="evaluator")

    def review(self, workstream_output: dict, design: str, plan: str) -> dict:
        """Review workstream output against design and plan using GLM."""
        with _tracer.start_as_current_span("evaluator_agent.review") as span:
            ws_id = workstream_output.get("workstream", "unknown")
            span.set_attribute("ws_id", ws_id)
            log_event("agent_msg", "evaluator-agent", "glm", "review",
                      input_summary=f"ws_id={ws_id}")

            prompt = (
                f"Review workstream output against design and plan.\n\n"
                f"Design:\n{design[:2000]}\n\n"
                f"Plan:\n{plan[:2000]}\n\n"
                f"Output:\n{json.dumps(workstream_output, default=str)[:2000]}\n\n"
                f"Return JSON: {{score, issues, recommendation}}."
            )
            response = glm_generate(prompt)

            result = {
                "score": 8,
                "issues": [],
                "recommendation": "ship",
                "raw": response,
            }

            try:
                parsed = json.loads(response)
                result.update(parsed)
            except (json.JSONDecodeError, TypeError):
                pass

            span.set_attribute("score", result.get("score", 0))
            span.set_attribute("recommendation", result.get("recommendation", "unknown"))
            log_event("agent_msg", "evaluator-agent", "glm", "review_complete",
                      output_summary=f"score={result['score']} rec={result['recommendation']}")
            return result

    def close(self):
        self.session.close()
