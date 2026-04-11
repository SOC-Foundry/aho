"""Smoke test for streaming QwenClient and RepetitionDetector.
"""
import sys
import os

# Add src to path if not installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aho.artifacts.qwen_client import QwenClient
from aho.artifacts.repetition_detector import RepetitionDetector, DegenerateGenerationError


def test_repetition_detector_logic():
    print("\n=== RepetitionDetector Logic Test ===", file=sys.stderr)
    detector = RepetitionDetector(window_size=10, similarity_threshold=0.8)
    
    # Normal tokens
    detector.add_tokens(list("This is a normal sentence that should not trigger."))
    assert not detector.check(), "Triggered on normal text"
    
    # Repetitive tokens
    repetitive = "ABCDEFGHIJ" * 3
    detector.add_tokens(list(repetitive))
    assert detector.check(), "Failed to trigger on repetitive text"
    print("[TEST] RepetitionDetector logic OK", file=sys.stderr)


def test_normal_generation():
    # Use nemotron-mini:4b for speed and reliability in smoke test
    client = QwenClient(model="nemotron-mini:4b", verbose=True)
    prompt = "Write 'Hello World' once."
    print(f"\n=== Normal generation test ===", file=sys.stderr)
    text = client.generate(prompt)
    assert "Hello World" in text
    print(f"\n[TEST] Normal generation OK", file=sys.stderr)


if __name__ == "__main__":
    test_repetition_detector_logic()
    test_normal_generation()
    sys.exit(0)
