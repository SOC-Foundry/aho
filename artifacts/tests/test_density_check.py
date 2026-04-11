import unittest
from aho.artifacts.repetition_detector import RepetitionDetector

class TestDensityCheck(unittest.TestCase):
    def test_low_density_loop(self):
        detector = RepetitionDetector()
        
        # 500 tokens of very low variety
        words = ["wait", "checking", "verify", "artifact", "requirements", "look", "schema"]
        tokens = []
        for _ in range(100):
            tokens.extend(words)
            
        detector.add_tokens(tokens)
        self.assertTrue(detector.check(), "Should have detected low density loop (0.01 density)")
        
    def test_normal_density(self):
        detector = RepetitionDetector()
        
        # Normal text with higher variety
        text = """
        The rolling-window repetition detector is a crucial component of the agentic harness.
        It prevents the model from wasting tokens and compute time on non-productive loops.
        By combining character-level sequence matching with word-level information density
        analysis, we can catch a wide variety of degenerate behaviors.
        This iteration specifically targets the 'Wait, checking' pattern observed in
        previous runs, which tended to have enough slight variations to evade the
        simpler structural checks but lacked the semantic variety of real engineering output.
        We have tuned the threshold to 10% unique words over a 500-token window,
        which should be safe for normal technical documentation while aggressive enough
        to stop loops before they consume too much of the iteration's time budget.
        """
        # Add 500 words of "normal-ish" unique content to avoid structural repetition triggers
        tokens = text.split()
        for i in range(500):
            tokens.append(f"unique_word_{i}")
            
        detector.add_tokens(tokens)
        self.assertFalse(detector.check(), "Should NOT have detected low density in normal text")

if __name__ == "__main__":
    unittest.main()
