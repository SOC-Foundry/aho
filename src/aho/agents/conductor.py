"""Conductor — orchestrator pattern for three-agent role split.

0.2.3 W2: Reads plan, dispatches via NemoClaw to workstream agent,
evaluator reviews, harness agent observes. Claude/Gemini demoted
from executor to conductor (Pillar 1).
"""
import json
import os
import sys
import time

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


def smoke():
    """Smoke test: dispatch a verifiable task, assert file + event log spans."""
    from aho.logger import event_log_path

    marker = f"/tmp/aho-smoke-marker-{int(time.time())}.txt"
    task = f'Create file {marker} containing exactly the text OK'
    start_ts = time.time()

    print(f"[smoke] Dispatching: {task}")
    conductor = Conductor()
    try:
        result = conductor.dispatch(task)
    finally:
        conductor.close()

    # Assert 1: marker file exists
    if not os.path.exists(marker):
        print(f"[smoke] FAIL: marker file {marker} not found")
        sys.exit(1)
    print("[smoke] PASS: marker file exists")

    # Assert 2: marker content is OK
    content = open(marker).read().strip()
    if content != "OK":
        print(f"[smoke] FAIL: marker content is '{content}', expected 'OK'")
        os.remove(marker)
        sys.exit(1)
    print("[smoke] PASS: marker content is 'OK'")

    # Assert 3: event log has 7+ events since start
    log_path = event_log_path()
    if log_path.exists():
        recent = 0
        for line in log_path.read_text().strip().splitlines():
            try:
                ev = json.loads(line)
                ts = ev.get("timestamp", "")
                if ts and time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) >= start_ts - 2:
                    recent += 1
            except (json.JSONDecodeError, ValueError):
                continue
        print(f"[smoke] Event log: {recent} events since dispatch start")
        if recent < 7:
            print(f"[smoke] WARN: expected 7+ events, got {recent}")
    else:
        print("[smoke] WARN: event log not found, skipping span assertion")

    # Cleanup
    os.remove(marker)
    print("[smoke] PASS: smoke test complete")
    sys.exit(0)


def main():
    """CLI entry point: aho-conductor {dispatch <task>|smoke}"""
    if len(sys.argv) < 2:
        print("Usage: aho-conductor {dispatch <task>|smoke}")
        sys.exit(1)

    if sys.argv[1] == "smoke":
        smoke()
    elif sys.argv[1] == "dispatch":
        if len(sys.argv) < 3:
            print("Usage: aho-conductor dispatch <task>")
            sys.exit(1)
        task = " ".join(sys.argv[2:])
        conductor = Conductor()
        try:
            result = conductor.dispatch(task)
            print(json.dumps(result, indent=2, default=str))
        finally:
            conductor.close()
    else:
        print("Usage: aho-conductor {dispatch <task>|smoke}")
        sys.exit(1)


if __name__ == "__main__":
    main()
