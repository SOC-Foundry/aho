import unittest
from pathlib import Path
from aho.artifacts.evaluator import get_allowed_cli_commands, get_allowed_scripts, validate_references

class TestEvaluatorDynamicBaseline(unittest.TestCase):
    def test_dynamic_cli_commands(self):
        cmds = get_allowed_cli_commands()
        self.assertIn("iteration", cmds)
        self.assertIn("project", cmds)
        self.assertIn("rag", cmds)

    def test_dynamic_scripts(self):
        # Assumes rebuild_aho_archive.py was created in W4
        scripts = get_allowed_scripts(Path.cwd())
        self.assertIn("rebuild_aho_archive.py", scripts)

    def test_validate_refs_uses_dynamic(self):
        refs = {
            "cli_commands": ["iteration", "fakecmd"],
            "script_names": ["rebuild_aho_archive.py", "fakescript.py"]
        }
        result = validate_references(refs, Path.cwd())
        errors = result["errors"]
        
        # iteration and rebuild_aho_archive.py should be OK
        # fakecmd and fakescript.py should be errors
        error_text = " ".join(errors)
        self.assertIn("hallucinated CLI command: aho fakecmd", error_text)
        self.assertIn("hallucinated script: fakescript.py", error_text)
        self.assertNotIn("aho iteration", error_text)
        self.assertNotIn("rebuild_aho_archive.py", error_text)

if __name__ == "__main__":
    unittest.main()
