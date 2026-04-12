"""HarnessAgent — Nemotron-bound harness watcher.

0.2.3 W2: Long-lived daemon that monitors the event log and proposes
gotchas, ADRs, and component registrations. LLM=nemotron-mini:4b.
"""
import json
import os
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
        """Long-lived tail of event log, classify each new event.

        Also monitors harness/ and data/ for file changes, triggering
        MANIFEST.json refresh with 5s debounce (0.2.10 W11).
        """
        from aho.logger import emit_heartbeat
        from aho.manifest import ManifestRefresher

        emit_heartbeat("harness-watcher")
        log_event("agent_msg", "harness-agent", "event-log", "watch_start",
                  input_summary=f"path={event_log_path}")

        # Start MANIFEST refresher
        refresher = ManifestRefresher()

        # Start inotifywait for harness/registry file changes (if available)
        self._start_file_watcher(refresher)

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
                    # Trigger manifest refresh on workstream events
                    if event.get("event_type") in ("workstream_complete", "close_complete"):
                        refresher.trigger()
                except (json.JSONDecodeError, KeyError):
                    continue
        except KeyboardInterrupt:
            pass
        finally:
            proc.terminate()
            proc.wait()

    def _start_file_watcher(self, refresher):
        """Start background thread watching harness/ and data/ for changes."""
        import threading
        from pathlib import Path

        try:
            from aho.paths import find_project_root
            root = find_project_root()
        except Exception:
            return

        watch_dirs = [
            root / "artifacts" / "harness",
            root / "data",
        ]
        existing_dirs = [str(d) for d in watch_dirs if d.is_dir()]
        if not existing_dirs:
            return

        def _poll_watcher():
            """Simple polling watcher — checks mtimes every 10s."""
            mtimes = {}
            while True:
                for watch_dir in existing_dirs:
                    for dirpath, _, filenames in os.walk(watch_dir):
                        for fname in filenames:
                            fpath = os.path.join(dirpath, fname)
                            try:
                                mtime = os.path.getmtime(fpath)
                                if fpath in mtimes and mtime > mtimes[fpath]:
                                    refresher.trigger()
                                mtimes[fpath] = mtime
                            except OSError:
                                continue
                time.sleep(10)

        t = threading.Thread(target=_poll_watcher, daemon=True)
        t.start()


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
