"""Tests for EvaluatorAgent score parsing and normalization."""
import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_deps():
    """Mock GLM and OTEL so we can test score parsing in isolation."""
    with patch("aho.agents.roles.evaluator_agent.glm_generate") as mock_glm, \
         patch("aho.agents.roles.evaluator_agent._tracer") as mock_tracer:
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_glm, mock_span


def test_score_0_to_1_scale_normalized(mock_deps):
    """GLM returning 0-1 scale score should be multiplied by 10."""
    mock_glm, mock_span = mock_deps
    mock_glm.return_value = json.dumps({
        "score": 0.8,
        "issues": [],
        "recommendation": "The output meets all requirements."
    })

    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review({"workstream": "W1"}, "design", "plan")

    assert result["score"] == 8
    assert result["raw_score"] == 0.8
    assert result["raw_recommendation"] == "The output meets all requirements."


def test_score_0_to_10_scale_unchanged(mock_deps):
    """GLM returning 0-10 scale score should pass through."""
    mock_glm, mock_span = mock_deps
    mock_glm.return_value = json.dumps({
        "score": 7,
        "issues": ["minor formatting"],
        "recommendation": "ship with notes"
    })

    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review({"workstream": "W2"}, "design", "plan")

    assert result["score"] == 7
    assert result["raw_score"] == 7


def test_score_1_0_float_normalized(mock_deps):
    """GLM returning 1.0 (perfect on 0-1 scale) becomes 10."""
    mock_glm, mock_span = mock_deps
    mock_glm.return_value = json.dumps({
        "score": 1.0,
        "issues": [],
        "recommendation": "perfect"
    })

    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review({"workstream": "W3"}, "design", "plan")

    assert result["score"] == 10
    assert result["raw_score"] == 1.0


def test_malformed_json_raises_glm_parse_error(mock_deps):
    """Malformed GLM response should raise GLMParseError, not fall back."""
    mock_glm, mock_span = mock_deps
    mock_glm.return_value = "this is not json at all"

    from aho.agents.roles.evaluator_agent import EvaluatorAgent, GLMParseError
    agent = EvaluatorAgent()
    with pytest.raises(GLMParseError) as exc_info:
        agent.review({"workstream": "W4"}, "design", "plan")
    assert exc_info.value.raw_response == "this is not json at all"


def test_raw_recommendation_preserved(mock_deps):
    """Raw recommendation text from GLM should be preserved."""
    mock_glm, mock_span = mock_deps
    mock_glm.return_value = json.dumps({
        "score": 0.6,
        "issues": ["incomplete coverage"],
        "recommendation": "The workstream needs additional test coverage before shipping."
    })

    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review({"workstream": "W5"}, "design", "plan")

    assert result["score"] == 6
    assert result["raw_recommendation"] == "The workstream needs additional test coverage before shipping."
