"""Verify evaluator baseline reloads on every evaluate_text call (aho-G060)."""
from pathlib import Path
from aho.artifacts.evaluator import evaluate_text


def test_newly_created_script_is_recognized():
    """A script created after module import must not be flagged as hallucinated."""
    new_script = Path("artifacts/scripts/aho_g060_reload_test.py")
    new_script.write_text("# reload test\n")
    try:
        result = evaluate_text(
            "This run uses artifacts/scripts/aho_g060_reload_test.py to verify reload.",
            artifact_type="test",
        )
        error_text = " ".join(result.get("errors", []))
        assert "aho_g060_reload_test.py" not in error_text, (
            f"New script flagged as hallucinated: {result['errors']}"
        )
    finally:
        new_script.unlink(missing_ok=True)
