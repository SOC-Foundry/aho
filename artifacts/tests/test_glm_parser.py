"""W1 tests — GLM evaluator parser fix (0.2.13).

Three test cases:
1. Verified-good: clean JSON -> parser returns real dict
2. Verified-bad (markdown-wrapped): fenced JSON -> parser strips and returns real dict
3. Verified-bad (malformed): unparseable -> parser RAISES GLMParseError
"""
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_deps():
    """Mock GLM client and OTEL tracer for isolated parser testing."""
    with patch("aho.agents.roles.evaluator_agent.glm_generate") as mock_glm, \
         patch("aho.agents.roles.evaluator_agent._tracer") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_glm, mock_span


def test_verified_good_clean_json(mock_deps):
    """Clean JSON response parses to real dict with actual scores."""
    mock_glm, _ = mock_deps
    mock_glm.return_value = json.dumps({
        "score": 6,
        "issues": ["missing edge-case coverage"],
        "recommendation": "rework"
    })

    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review({"workstream": "W1"}, "design", "plan")

    assert result["score"] == 6
    assert result["issues"] == ["missing edge-case coverage"]
    assert result["recommendation"] == "rework"
    assert result["raw_score"] == 6
    assert result["raw_recommendation"] == "rework"


def test_verified_bad_markdown_wrapped(mock_deps):
    """Markdown-fenced JSON response is stripped and parsed to real dict."""
    mock_glm, _ = mock_deps
    mock_glm.return_value = (
        "```json\n"
        '{"score": 4, "issues": ["critical regression"], "recommendation": "halt"}\n'
        "```"
    )

    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review({"workstream": "W1"}, "design", "plan")

    assert result["score"] == 4
    assert result["issues"] == ["critical regression"]
    assert result["recommendation"] == "halt"
    assert result["raw_score"] == 4


def test_verified_bad_malformed_raises(mock_deps):
    """Unparseable response raises GLMParseError, not a fallback."""
    mock_glm, _ = mock_deps
    mock_glm.return_value = "I think the code looks great! Ship it immediately."

    from aho.agents.roles.evaluator_agent import EvaluatorAgent, GLMParseError
    agent = EvaluatorAgent()
    with pytest.raises(GLMParseError) as exc_info:
        agent.review({"workstream": "W1"}, "design", "plan")

    assert exc_info.value.raw_response == "I think the code looks great! Ship it immediately."
