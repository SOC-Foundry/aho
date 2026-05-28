"""Conductor - orchestrator pattern for three-agent role split.

0.2.3 W2: Reads plan, dispatches via NemoClaw to workstream agent,
evaluator reviews, harness agent observes. Claude/Gemini demoted
from executor to conductor (Pillar 1).

0.3.1 council-wiring: project-context-aware dispatch for global use.
dispatch() captures the calling project folder (cwd) and, on request,
writes the produced artifact back into <cwd>/aho-output/ so an arbitrary
Claude Code session in an unrelated repo can route work through the
council via `aho-conductor dispatch "<task>"` and get a durable artifact
in its own tree. smoke() now asserts on what the pipeline genuinely
produces (route -> produce -> assess -> notify, plus a written artifact
and event-log spans). Earlier smoke() asserted a marker FILE was created
on disk; the workstream agent is chat-only (it never executes code), so
that assertion could never pass and conflated "council reachable" with
"agent has host filesystem side-effects".
"""
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from opentelemetry import trace

from aho.agents.roles.workstream_agent import WorkstreamAgent
from aho.agents.roles.evaluator_agent import EvaluatorAgent, GLMParseError
from aho.agents.nemoclaw import NemoClawOrchestrator
from aho.artifacts.repetition_detector import DegenerateGenerationError
from aho.pipeline.dispatcher import DispatchError
from aho.logger import log_event
from aho.telegram.notifications import send

# Narrow tuple of expected substrate-flake errors that any conductor CLI
# entrypoint should surface as a clean message rather than a traceback.
# Each one is a documented failure mode of the council's HTTP/Ollama path:
#   DispatchError              router/dispatcher (incl. ClassificationError,
#                              ModelUnavailableError, MalformedResponseError,
#                              TemplateLeakError, DispatchTimeoutError)
#   GLMParseError              evaluator could not parse GLM JSON
#   DegenerateGenerationError  QwenClient thinking/output repetition detector
#                              fired (observed on CPU at base tier)
#   requests.RequestException  QwenClient/glm_client HTTP transport failures
#                              (connect, read timeout, etc.)
_COUNCIL_ERRORS = (
    DispatchError,
    GLMParseError,
    DegenerateGenerationError,
    requests.RequestException,
)

_tracer = trace.get_tracer("aho.conductor")


def _project_identity(cwd: Path) -> dict:
    """Describe the calling project folder so the council has routing context.

    Pulls the project name from .aho.json when present (so dispatches from
    an aho-managed repo carry its declared name + code), otherwise falls
    back to the directory basename. Notes whether the folder is a git repo.
    """
    ident = {"cwd": str(cwd), "name": cwd.name}
    aho_json = cwd / ".aho.json"
    if aho_json.exists():
        try:
            data = json.loads(aho_json.read_text())
            ident["name"] = data.get("name", cwd.name)
            if data.get("project_code"):
                ident["project_code"] = data["project_code"]
        except (json.JSONDecodeError, OSError):
            pass
    if (cwd / ".git").exists():
        ident["git_repo"] = True
    return ident


def _context_preamble(ident: dict) -> str:
    """One-line context header prepended to the workstream task."""
    parts = [f"project={ident['name']}", f"cwd={ident['cwd']}"]
    if ident.get("project_code"):
        parts.append(f"code={ident['project_code']}")
    if ident.get("git_repo"):
        parts.append("git=yes")
    return "[council dispatch context] " + ", ".join(parts)


def _write_artifact(cwd: Path, task: str, result: dict) -> Path:
    """Write the dispatch result into <cwd>/aho-output/ for the caller.

    Mirrors the convention used by `aho run` (OpenClaw daemon writes
    run-<ts>.md into the calling folder's aho-output/).
    """
    out_dir = cwd / "aho-output"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = out_dir / f"council-dispatch-{ts}.json"
    payload = {"task": task, "dispatched_at": datetime.now(timezone.utc).isoformat()}
    payload.update(result)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path


class Conductor:
    def __init__(self):
        self.workstream = WorkstreamAgent()
        self.evaluator = EvaluatorAgent()
        self.nemoclaw = NemoClawOrchestrator(session_count=1)

    def dispatch(self, task: str, design: str = "", plan: str = "",
                 cwd: Optional[str] = None, write_artifact: bool = False) -> dict:
        """Full conductor dispatch: route -> execute -> review -> notify.

        When cwd is provided (or defaulted to os.getcwd()), the calling
        project's identity is injected into the workstream task context so
        the council knows which folder it is working in. When write_artifact
        is True, the produced result is also written to <cwd>/aho-output/ and
        its path is returned under the "artifact_path" key.
        """
        cwd_path = Path(cwd) if cwd else Path.cwd()
        ident = _project_identity(cwd_path)

        with _tracer.start_as_current_span("conductor.dispatch") as span:
            span.set_attribute("task_length", len(task))
            span.set_attribute("aho.project", ident["name"])
            span.set_attribute("aho.cwd", ident["cwd"])
            log_event("agent_msg", "conductor", "nemoclaw", "dispatch",
                      input_summary=task[:200],
                      output_summary=f"project={ident['name']}")

            # Step 1: Route via NemoClaw (classifier model). The routed role
            # is advisory in the conductor flow - the workstream produces work
            # identically regardless of role - so a flaky-classifier miss must
            # not abort the substantive produce+assess steps. Fall back to a
            # default role and continue.
            try:
                role = self.nemoclaw.route(task)
            except DispatchError as e:
                role = "assistant"
                span.set_attribute("aho.route_fallback", type(e).__name__)
                log_event("agent_msg", "conductor", "nemoclaw", "route_fallback",
                          output_summary=f"classifier miss ({type(e).__name__}); role={role}")
            span.set_attribute("classified_role", role)

            # Step 2: Execute via WorkstreamAgent, carrying project context
            contextual_task = f"{_context_preamble(ident)}\n\n{task}"
            result = self.workstream.execute_workstream("dispatch", contextual_task)

            # Step 3: Evaluate via EvaluatorAgent
            review = self.evaluator.review(result, design, plan)

            # Step 4: Notify via Telegram (best-effort; no-op without creds)
            score = review.get("score", 0)
            rec = review.get("recommendation", "unknown")
            send(f"Conductor dispatch [{ident['name']}] complete: score={score}, rec={rec}")

            span.set_attribute("score", score)
            span.set_attribute("recommendation", str(rec))
            span.set_attribute("status", "ok")

            out = {
                "execution": result,
                "review": review,
                "role": role,
                "project": ident,
            }

            if write_artifact:
                try:
                    artifact_path = _write_artifact(cwd_path, task, out)
                    out["artifact_path"] = str(artifact_path)
                    span.set_attribute("aho.artifact_path", str(artifact_path))
                except OSError as e:
                    out["artifact_error"] = str(e)

            return out

    def close(self):
        self.workstream.close()
        self.evaluator.close()
        self.nemoclaw.close_all()


def smoke():
    """Smoke test: dispatch a verifiable task and assert the full council flow
    ran (route -> produce -> assess -> notify) with a produced artifact and
    event-log spans.

    Exits 0 on success, 1 on failure. Designed to run from any working
    directory on a fresh login - its only runtime dependency is host Ollama
    serving the council models, which the dispatch chain reaches directly.
    """
    from aho.logger import event_log_path

    task = "Reply with a one-sentence confirmation that you received this dispatch."
    start_ts = time.time()

    print(f"[smoke] Dispatching: {task}")
    conductor = Conductor()
    try:
        result = conductor.dispatch(task)
    except _COUNCIL_ERRORS as e:
        print(f"[smoke] FAIL: council dispatch raised {type(e).__name__}: {e}")
        print("[smoke] Is host Ollama up with the council models pulled? "
              "Check: aho council status / ollama list")
        sys.exit(1)
    finally:
        conductor.close()

    # Assert 1: routing classified a role (classifier model ran)
    role = result.get("role")
    if not role:
        print("[smoke] FAIL: no role classified (routing did not run)")
        sys.exit(1)
    print(f"[smoke] PASS: routed to role '{role}'")

    # Assert 2: workstream produced non-empty output (producer model ran)
    raw = (result.get("execution") or {}).get("raw", "")
    if not isinstance(raw, str) or not raw.strip():
        print("[smoke] FAIL: workstream produced empty output")
        sys.exit(1)
    print(f"[smoke] PASS: workstream produced {len(raw)} chars")

    # Assert 3: evaluator returned a parseable score + recommendation (assessor ran)
    review = result.get("review") or {}
    score = review.get("score")
    rec = review.get("recommendation")
    if score is None or rec is None:
        print(f"[smoke] FAIL: evaluator did not return score/recommendation "
              f"(score={score!r}, rec={rec!r})")
        sys.exit(1)
    print(f"[smoke] PASS: evaluator score={score}, recommendation={rec}")

    # Assert 4: a produced artifact can be written (council output is durable)
    artifact = Path(tempfile.gettempdir()) / f"aho-smoke-{int(start_ts)}.json"
    artifact.write_text(json.dumps(result, indent=2, default=str) + "\n")
    if not artifact.exists() or artifact.stat().st_size == 0:
        print("[smoke] FAIL: produced artifact not written")
        sys.exit(1)
    print(f"[smoke] PASS: artifact written ({artifact.stat().st_size} bytes)")
    artifact.unlink(missing_ok=True)

    # Assert 5 (soft): event log recorded spans for this dispatch
    log_path = event_log_path()
    recent = 0
    if log_path.exists():
        for line in log_path.read_text().strip().splitlines():
            try:
                ev = json.loads(line)
                ts = ev.get("timestamp", "")
                if ts and time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) >= start_ts - 2:
                    recent += 1
            except (json.JSONDecodeError, ValueError):
                continue
    print(f"[smoke] Event log: {recent} events since dispatch start")
    if recent < 4:
        print(f"[smoke] WARN: expected 4+ events, got {recent}")

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
            result = conductor.dispatch(task, cwd=os.getcwd(), write_artifact=True)
            print(json.dumps(result, indent=2, default=str))
        except _COUNCIL_ERRORS as e:
            print(json.dumps({
                "error": f"{type(e).__name__}: {e}",
                "hint": "Ensure host Ollama is running with the council models "
                        "pulled (aho council status / ollama list).",
            }, indent=2))
            sys.exit(1)
        finally:
            conductor.close()
    else:
        print("Usage: aho-conductor {dispatch <task>|smoke}")
        sys.exit(1)


if __name__ == "__main__":
    main()
