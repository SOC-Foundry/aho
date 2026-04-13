"""EvaluatorAgent — GLM-bound review role.

0.2.3 W2: Pillar 7 enforcement — generation and evaluation are separate roles.
Wraps OpenClawSession with role="evaluator", LLM=GLM-4.6V-Flash-9B.

0.2.13 W1: Parse fix — strip markdown fences before json.loads(),
raise GLMParseError on failure instead of hardcoded fallback.
"""
import json
import re

from opentelemetry import trace

from aho.agents.openclaw import OpenClawSession
from aho.artifacts.glm_client import generate as glm_generate
from aho.logger import log_event

_tracer = trace.get_tracer("aho.evaluator_agent")


class GLMParseError(Exception):
    """Raised when GLM response cannot be parsed as valid JSON."""

    def __init__(self, message: str, raw_response: str = ""):
        super().__init__(message)
        self.raw_response = raw_response


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from GLM response text.

    Handles: ```json ... ```, bare ``` ... ```, leading/trailing whitespace,
    and partial-wrap cases where only opening or closing fence is present.
    """
    stripped = text.strip()
    # Match ```json ... ``` or ``` ... ``` (with optional language tag)
    match = re.search(r"```(?:\w+)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Partial wrap: starts with ``` but no closing fence
    if stripped.startswith("```"):
        after_fence = re.sub(r"^```\w*\s*\n?", "", stripped)
        return after_fence.strip()
    return stripped


class EvaluatorAgent:
    def __init__(self):
        self.session = OpenClawSession(role="evaluator")

    def review(self, workstream_output: dict, design: str, plan: str) -> dict:
        """Review workstream output against design and plan using GLM.

        Raises GLMParseError if the response cannot be parsed as JSON.
        """
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
            cleaned = _strip_markdown_fences(response)

            try:
                parsed = json.loads(cleaned)
            except (json.JSONDecodeError, TypeError) as exc:
                raise GLMParseError(
                    f"GLM response is not valid JSON after fence stripping: {exc}",
                    raw_response=response,
                ) from exc

            result = {
                "raw": response,
                "raw_score": parsed.get("score"),
                "raw_recommendation": parsed.get("recommendation"),
            }
            result.update(parsed)

            # Scale detection: if score <= 1.0, assume 0-1 scale and multiply by 10
            score = result.get("score", 0)
            if isinstance(score, (int, float)) and score <= 1.0:
                result["score"] = round(score * 10)

            span.set_attribute("score", result.get("score", 0))
            span.set_attribute("recommendation", str(result.get("recommendation", "unknown")))
            log_event("agent_msg", "evaluator-agent", "glm", "review_complete",
                      output_summary=f"score={result.get('score', 'unknown')} rec={result.get('recommendation', 'unknown')}")
            return result

    def close(self):
        self.session.close()
