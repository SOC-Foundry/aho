"""Regression test: the 0.1.7 build log synthesis contained split-agent language.
The W3 evaluator did not catch it because it wasn't wired to the synthesis pass.
After 0.1.8 W4, the evaluator runs on synthesis outputs and rejects this paragraph.
"""
from aho.artifacts.evaluator import evaluate_text
from aho.paths import find_project_root


PROJECT_ROOT = find_project_root()


SPLIT_AGENT_PARAGRAPH = """
The iteration followed the bounded sequential pattern with split-agent execution
(Gemini W0-W5, Claude W6-W7). Wall clock time was within the soft cap of ~12 hours.
No rollback was necessary.
"""


def test_split_agent_rejected_in_synthesis():
    result = evaluate_text(SPLIT_AGENT_PARAGRAPH, project_root=PROJECT_ROOT,
                           artifact_type="build_log_synthesis")
    assert result["severity"] == "reject", \
        f"expected reject, got {result['severity']}; errors: {result['errors']}"
    errors_text = " ".join(str(e).lower() for e in result["errors"])
    assert "split-agent" in errors_text or "split agent" in errors_text, \
        f"split-agent not in errors: {result['errors']}"


def test_split_agent_warn_without_synthesis_type():
    """Without artifact_type=synthesis, same text is only warn (<=3 errors)."""
    result = evaluate_text(SPLIT_AGENT_PARAGRAPH, project_root=PROJECT_ROOT)
    assert result["severity"] == "warn", \
        f"expected warn without synthesis type, got {result['severity']}"


def test_clean_paragraph_accepted():
    clean = """
    The iteration executed all nine workstreams sequentially. Wall clock time was
    within the soft cap. No discrepancies were observed.
    """
    result = evaluate_text(clean, project_root=PROJECT_ROOT,
                           artifact_type="build_log_synthesis")
    assert result["severity"] != "reject", \
        f"clean paragraph unexpectedly rejected: {result['errors']}"
