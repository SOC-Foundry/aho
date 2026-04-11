import unittest
from aho.artifacts.repetition_detector import RepetitionDetector, DegenerateGenerationError

class TestDegenerateReproduction(unittest.TestCase):
    def test_wait_checking_loop(self):
        detector = RepetitionDetector(window_size=200, similarity_threshold=0.70)
        
        # A semi-variable loop that might evade a strict exact match but is non-productive
        pattern = "Wait, checking... I need to verify the artifact requirements. Let me look at the schema again. "
        
        tokens = []
        # Simulate a few hundred tokens of this loop
        for i in range(20):
            # Add some slight variation to simulate evasion
            variation = f" (Attempt {i}) "
            for char in (pattern + variation):
                tokens.append(char)
                if len(tokens) % 50 == 0:
                    detector.add_tokens(tokens[-50:])
                    if detector.check():
                        print(f"Detected degenerate loop at iteration {i}")
                        return
        
        self.fail("Repetition detector failed to catch the semi-variable loop")

if __name__ == "__main__":
    unittest.main()
