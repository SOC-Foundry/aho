"""Conductor — orchestrator pattern for three-agent role split.

0.2.3 W2: Reads plan, dispatches via NemoClaw to workstream agent,
evaluator reviews, harness agent observes. Claude/Gemini demoted
from executor to conductor (Pillar 1).
"""
import json
import sys

from opentelemetry import trace

from aho.agents.roles.workstream_agent import WorkstreamAgent
from aho.agents.roles.evaluator_agent import EvaluatorAgent
from aho.agents.nemoclaw import NemoClawOrchestrator
from aho.logger import log_event
from aho.telegram.notifications import send

_tracer = trace.get_tracer("aho.conductor")


class Conductor:
    def __init__(self):
        self.workstream = WorkstreamAgent()
        self.evaluator = EvaluatorAgent()
        self.nemoclaw = NemoClawOrchestrator(session_count=1)

    def dispatch(self, task: str, design: str = "", plan: str = "") -> dict:
        """Full conductor dispatch: route → execute → review → notify."""
        with _tracer.start_as_current_span("conductor.dispatch") as span:
            span.set_attribute("task_length", len(task))
            log_event("agent_msg", "conductor", "nemoclaw", "dispatch",
                      input_summary=task[:200])

            # Step 1: Route via NemoClaw
            role = self.nemoclaw.route(task)
            span.set_attribute("classified_role", role)

            # Step 2: Execute via WorkstreamAgent
            result = self.workstream.execute_workstream("dispatch", task)

            # Step 3: Evaluate via EvaluatorAgent
            review = self.evaluator.review(result, design, plan)

            # Step 4: Notify via Telegram
            score = review.get("score", 0)
            rec = review.get("recommendation", "unknown")
            send(f"Conductor dispatch complete: score={score}, rec={rec}")

            span.set_attribute("score", score)
            span.set_attribute("recommendation", rec)
            span.set_attribute("status", "ok")

            return {
                "execution": result,
                "review": review,
                "role": role,
            }

    def close(self):
        self.workstream.close()
        self.evaluator.close()
        self.nemoclaw.close_all()


def main():
    """CLI entry point: aho-conductor dispatch <task>"""
    if len(sys.argv) < 3 or sys.argv[1] != "dispatch":
        print("Usage: aho-conductor dispatch <task>")
        sys.exit(1)

    task = " ".join(sys.argv[2:])
    conductor = Conductor()
    try:
        result = conductor.dispatch(task)
        print(json.dumps(result, indent=2, default=str))
    finally:
        conductor.close()


if __name__ == "__main__":
    main()
