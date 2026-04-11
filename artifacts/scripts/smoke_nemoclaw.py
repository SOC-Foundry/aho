"""Smoke test NemoClaw — orchestration via Nemotron."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aho.agents.nemoclaw import NemoClawOrchestrator


def main():
    print("Creating NemoClawOrchestrator...", flush=True)
    orch = NemoClawOrchestrator(session_count=1)
    print(f"Sessions: {len(orch.sessions)}, role: {orch.sessions[0].role}", flush=True)

    print("\nDispatching task: 'What is the capital of France?'", flush=True)
    response = orch.dispatch("What is the capital of France? Answer in one word.", role="assistant")
    print(f"Response: {response[:200]}", flush=True)
    assert "paris" in response.lower(), f"Expected 'Paris' in response, got: {response[:100]}"
    print("PASS", flush=True)

    orch.close_all()
    print("\nAll NemoClaw smoke tests passed", flush=True)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
