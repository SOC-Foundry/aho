"""HarnessAgent — Nemotron-bound harness watcher.

0.2.3 W2: Long-lived daemon that monitors the event log and proposes
gotchas, ADRs, and component registrations. LLM=nemotron-mini:4b.
"""
import json
import subprocess
import sys
import time

from opentelemetry import trace

from aho.artifacts.nemotron_client import classify
from aho.logger import log_event

_tracer = trace.get_tracer("aho.harness_agent")


class HarnessAgent:
    def __init__(self):
        pass

    def propose_gotcha(self, event: dict) -> dict:
        """Classify an event as gotcha, noise, or feature."""
        with _tracer.start_as_current_span("harness_agent.classify") as span:
            result = classify(
                json.dumps(event, default=str)[:500],
                ["gotcha", "noise", "feature"],
            )
            span.set_attribute("category", result)

            if result == "gotcha":
                code = f"aho-G{int(time.time()) % 1000:03d}"
                log_event("agent_msg", "harness-agent", "nemotron", "propose_gotcha",
                          output_summary=f"new gotcha candidate: {code}")
                return {"propose": True, "code": code, "event": event}
            return {"propose": False, "category": result}

    def propose_adr(self, observation: str) -> dict:
        """Classify an observation as adr-worthy or not."""
        result = classify(observation[:500], ["adr", "pattern", "noise"])
        if result == "adr":
            return {"propose": True, "observation": observation}
        return {"propose": False, "category": result}

    def propose_component(self, detected: str) -> dict:
        """Classify a detection as a new component or not."""
        result = classify(detected[:500], ["new_component", "existing", "noise"])
        if result == "new_component":
            return {"propose": True, "detected": detected}
        return {"propose": False, "category": result}

    def watch(self, event_log_path: str):
        """Long-lived tail of event log, classify each new event."""
        from aho.logger import emit_heartbeat
        emit_heartbeat("harness-watcher")
        log_event("agent_msg", "harness-agent", "event-log", "watch_start",
                  input_summary=f"path={event_log_path}")
        proc = subprocess.Popen(
            ["tail", "-F", event_log_path],
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            for line in proc.stdout:
                try:
                    event = json.loads(line.strip())
                    proposal = self.propose_gotcha(event)
                    if proposal["propose"]:
                        log_event("harness_proposal", "harness-agent", "registry", "gotcha_candidate",
                                  output_summary=f"new gotcha candidate: {proposal['code']}")
                except (json.JSONDecodeError, KeyError):
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            proc.terminate()
            proc.wait()


def main():
    """Entry point for --watch mode."""
    if "--watch" in sys.argv:
        idx = sys.argv.index("--watch")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
        if not path:
            print("Usage: python -m aho.agents.roles.harness_agent --watch <event_log_path>")
            sys.exit(1)
        agent = HarnessAgent()
        agent.watch(path)
    else:
        print("Usage: python -m aho.agents.roles.harness_agent --watch <event_log_path>")
        sys.exit(1)


if __name__ == "__main__":
    main()
