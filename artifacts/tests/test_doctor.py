"""Unit tests for aho.doctor."""
import unittest
import os
from aho.doctor import run_all

class TestDoctor(unittest.TestCase):
    def test_run_all_quick(self):
        results = run_all(level="quick")
        self.assertIsInstance(results, dict)
        self.assertIn("project_root", results)
        self.assertIn("aho_json", results)
        
        for name, (status, msg) in results.items():
            self.assertIn(status, ["ok", "warn", "fail", "deferred"])
            self.assertIsInstance(msg, str)

    def test_run_all_preflight(self):
        # This might fail if ollama is down, but we just check the structure
        results = run_all(level="preflight")
        self.assertIsInstance(results, dict)
        self.assertIn("ollama", results)
        self.assertIn("python_deps", results)

if __name__ == "__main__":
    unittest.main()
