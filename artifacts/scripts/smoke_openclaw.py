"""Smoke test OpenClaw — Ollama-native, no open-interpreter."""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aho.agents.openclaw import OpenClawSession


def main():
    print("Creating OpenClawSession...", flush=True)
    session = OpenClawSession(role="assistant")
    print(f"Session ID: {session.session_id}", flush=True)

    print("\nTest 1: chat", flush=True)
    response = session.chat("What is 2+2? Answer with just the number.")
    print(f"Response: {response[:200]}", flush=True)
    assert "4" in response, f"Expected '4' in response, got: {response[:100]}"
    print("PASS", flush=True)

    print("\nTest 2: execute_code", flush=True)
    result = session.execute_code("print(2+2)", language="python")
    print(f"Result: {result}", flush=True)
    assert result["exit_code"] == 0
    assert "4" in result["stdout"]
    print("PASS", flush=True)

    session.close()
    print("\nAll OpenClaw smoke tests passed", flush=True)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
