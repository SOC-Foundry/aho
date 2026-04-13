"""Tests for EvaluatorAgent (0.2.3 W2 role split)."""
import json
import pytest
from unittest.mock import patch, MagicMock


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.logger.log_event")
def test_evaluator_agent_creates_session(mock_log, mock_glm, mock_qwen):
    mock_qwen.return_value.generate.return_value = ""
    mock_glm.return_value = '{"score": 9, "issues": [], "recommendation": "ship"}'
    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    assert agent.session.role == "evaluator"
    agent.close()


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.logger.log_event")
def test_evaluator_agent_review(mock_log, mock_glm, mock_qwen):
    mock_qwen.return_value.generate.return_value = ""
    mock_glm.return_value = '{"score": 9, "issues": [], "recommendation": "ship"}'
    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    result = agent.review(
        {"workstream": "W1", "status": "pass"},
        "design text",
        "plan text",
    )
    assert result["score"] == 9
    assert result["recommendation"] == "ship"
    agent.close()


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.logger.log_event")
def test_evaluator_agent_raises_on_non_json(mock_log, mock_glm, mock_qwen):
    mock_qwen.return_value.generate.return_value = ""
    mock_glm.return_value = "Looks good to me, ship it."
    from aho.agents.roles.evaluator_agent import EvaluatorAgent, GLMParseError
    agent = EvaluatorAgent()
    with pytest.raises(GLMParseError):
        agent.review(
            {"workstream": "W0", "status": "pass"},
            "design",
            "plan",
        )
    agent.close()


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.agents.roles.evaluator_agent.log_event")
def test_evaluator_agent_logs_events(mock_log, mock_glm, mock_qwen):
    mock_qwen.return_value.generate.return_value = ""
    mock_glm.return_value = '{"score": 7}'
    from aho.agents.roles.evaluator_agent import EvaluatorAgent
    agent = EvaluatorAgent()
    agent.review({"workstream": "W1"}, "", "")
    assert mock_log.call_count >= 2
    agent.close()
