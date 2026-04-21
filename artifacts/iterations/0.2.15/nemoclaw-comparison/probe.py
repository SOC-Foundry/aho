"""W3 empirical comparison: Nemoclaw vs direct dispatch for classification.

Compares two paths on identical inputs, same model (nemotron-mini:4b):
- Path A (Nemoclaw): nemotron_client.classify() — what NemoClawOrchestrator.route()
  calls internally; uses /api/generate.
- Path B (Direct dispatch): dispatcher.dispatch() with the hardened /api/chat path
  (stop tokens, retry, template leak detection).

Also measures one socket roundtrip via the running Nemoclaw daemon on the
hardwired [assistant, code_runner, reviewer] categories to isolate the IPC
cost of the daemon layer independent of the classifier endpoint.

Raw responses, wall clock per call, and correctness recorded.
"""
import json
import os
import socket
import sys
import time
from pathlib import Path

# Ensure src on path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from aho.artifacts.nemotron_client import classify, NemotronParseError
from aho.pipeline import dispatcher


TASKS_BUG_FEATURE = [
    ("The login button doesn't respond when clicked on Safari.", "bug"),
    ("Add dark mode support to the settings page.", "feature"),
    ("API returns 500 when user has more than 10 groups.", "bug"),
    ("Users should be able to export data as CSV.", "feature"),
    ("Memory leak in the image uploader after 2 minutes of use.", "bug"),
]
CATEGORIES = ["bug", "feature"]

DAEMON_ROLE_TASKS = [
    "Explain what the eleven pillars of AHO are.",
    "Write a python function that sorts a list of dicts by a key.",
    "Review this code for G083 compliance.",
    "What's the difference between remediation and discovery iterations?",
    "Run the test suite and report which tests fail.",
]
DAEMON_CATEGORIES = ["assistant", "code_runner", "reviewer"]


# ---------------------------------------------------------------------------
# Path A: Nemoclaw in-process (nemotron_client.classify — what route() calls)
# ---------------------------------------------------------------------------

def path_a_classify(text, categories):
    start = time.monotonic()
    error = None
    raw = None
    try:
        result = classify(text, categories)
        raw = result
    except NemotronParseError as e:
        result = None
        raw = getattr(e, "raw_response", "")
        error = f"parse_error: {e}"
    elapsed = time.monotonic() - start
    return {
        "classification": result,
        "raw_response": raw,
        "wall_clock_seconds": round(elapsed, 3),
        "error": error,
    }


# ---------------------------------------------------------------------------
# Path B: Direct dispatcher — manual prompt, parse raw content
# ---------------------------------------------------------------------------

def path_b_classify(text, categories):
    system = (
        "You are a precise classifier. Categorize the input text into EXACTLY ONE "
        f"of these categories: {', '.join(categories)}. "
        "Respond with ONLY the category name."
    )
    prompt = f"Text to classify:\n{text}\n\nCategory:"
    start = time.monotonic()
    result = dispatcher.dispatch(
        "nemotron-mini:4b", prompt, system=system,
        timeout=30, num_ctx=2048, max_retries=0,
    )
    elapsed = time.monotonic() - start

    raw_content = result.get("response", "")
    # Same parse rule as nemotron_client.classify
    normalized = raw_content.strip().strip("'\"").strip()
    matched = None
    for cat in categories:
        if cat.lower() in normalized.lower():
            matched = cat
            break

    return {
        "classification": matched,
        "raw_response": raw_content,
        "wall_clock_seconds": round(elapsed, 3),
        "dispatcher_wall_clock_seconds": result.get("wall_clock_seconds"),
        "family": result.get("family"),
        "error": result.get("error"),
        "total_duration_ms": result.get("total_duration_ms"),
        "retries_used": result.get("retries_used"),
    }


# ---------------------------------------------------------------------------
# Path C: Nemoclaw socket (daemon IPC) — role routing for [assistant, code_runner, reviewer]
# ---------------------------------------------------------------------------

SOCK_PATH = str(Path.home() / ".local/share/aho/nemoclaw.sock")


def path_c_daemon_route(task):
    payload = json.dumps({"cmd": "route", "task": task}) + "\n"
    start = time.monotonic()
    error = None
    role = None
    raw = ""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(30)
        s.connect(SOCK_PATH)
        s.sendall(payload.encode("utf-8"))
        buf = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n"):
                break
        s.close()
        raw = buf.decode("utf-8").strip()
        parsed = json.loads(raw)
        if parsed.get("ok"):
            role = parsed.get("role")
        else:
            error = parsed.get("error", "daemon reported not ok")
    except (OSError, json.JSONDecodeError) as e:
        error = f"{type(e).__name__}: {e}"
    elapsed = time.monotonic() - start
    return {
        "classification": role,
        "raw_response": raw,
        "wall_clock_seconds": round(elapsed, 3),
        "error": error,
    }


def path_b_classify_roles(text, categories):
    return path_b_classify(text, categories)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    out_dir = Path(__file__).parent / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)

    bug_feature_results = []
    print("=== Bug/Feature classification ===")
    for i, (task, expected) in enumerate(TASKS_BUG_FEATURE, 1):
        print(f"[{i}] task: {task[:60]} (expected: {expected})")
        a = path_a_classify(task, CATEGORIES)
        b = path_b_classify(task, CATEGORIES)
        bug_feature_results.append({
            "task": task,
            "expected": expected,
            "path_a_nemotron_client": a,
            "path_b_direct_dispatch": b,
        })
        print(f"    A={a['classification']} ({a['wall_clock_seconds']}s) "
              f"B={b['classification']} ({b['wall_clock_seconds']}s)")

    role_results = []
    print("\n=== Daemon role classification (daemon IPC overhead probe) ===")
    for i, task in enumerate(DAEMON_ROLE_TASKS, 1):
        print(f"[{i}] task: {task[:60]}")
        c = path_c_daemon_route(task)
        b = path_b_classify_roles(task, DAEMON_CATEGORIES)
        role_results.append({
            "task": task,
            "path_c_daemon_socket": c,
            "path_b_direct_dispatch": b,
        })
        print(f"    C(socket)={c['classification']} ({c['wall_clock_seconds']}s) "
              f"B={b['classification']} ({b['wall_clock_seconds']}s)")

    # Error handling comparison — unknown model
    print("\n=== Error handling: unknown model ===")
    err_cases = []

    # Path A: call classify with model hardcoded to nemotron-mini:4b; can only
    # provoke error by stopping ollama — skip destructive test. Instead, check
    # the error type taxonomy by reading the code (see report).

    # Path B: request an unknown model via dispatcher
    b_err = dispatcher.dispatch(
        "nonexistent-model:99b", "hello", system=None,
        timeout=10, num_ctx=2048, max_retries=0,
    )
    err_cases.append({
        "case": "unknown_model",
        "path_b_direct_dispatch": {
            "error": b_err.get("error"),
            "wall_clock_seconds": b_err.get("wall_clock_seconds"),
            "retries_used": b_err.get("retries_used"),
        },
    })
    print(f"    B unknown_model error={b_err.get('error')}")

    output = {
        "probe_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": "nemotron-mini:4b",
        "dispatcher_module": "aho.pipeline.dispatcher (W2 hardened, /api/chat)",
        "nemotron_client_module": "aho.artifacts.nemotron_client (/api/generate)",
        "nemoclaw_socket": SOCK_PATH,
        "bug_feature_task_count": len(TASKS_BUG_FEATURE),
        "role_task_count": len(DAEMON_ROLE_TASKS),
        "bug_feature_results": bug_feature_results,
        "role_results": role_results,
        "error_handling": err_cases,
    }

    (out_dir / "probe-results.json").write_text(
        json.dumps(output, indent=2) + "\n"
    )
    print(f"\nResults written to {out_dir / 'probe-results.json'}")
    return output


if __name__ == "__main__":
    run()
