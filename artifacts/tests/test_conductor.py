"""Tests for Conductor (0.2.3 W2 role split)."""
import json
import pytest
from unittest.mock import patch, MagicMock


@patch("aho.agents.conductor.send")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.nemoclaw.classify")
@patch("aho.logger.log_event")
def test_conductor_dispatch(mock_log, mock_nemo_classify, mock_qwen, mock_glm, mock_send):
    mock_nemo_classify.return_value = "assistant"
    mock_qwen.return_value.generate.return_value = '{"status": "pass"}'
    mock_glm.return_value = '{"score": 9, "recommendation": "ship"}'
    mock_send.return_value = True

    from aho.agents.conductor import Conductor
    conductor = Conductor()
    result = conductor.dispatch("explain pillar 1")
    assert "execution" in result
    assert "review" in result
    assert result["review"]["score"] == 9
    conductor.close()


@patch("aho.agents.conductor.send")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.nemoclaw.classify")
@patch("aho.logger.log_event")
def test_conductor_dispatch_with_plan(mock_log, mock_nemo_classify, mock_qwen, mock_glm, mock_send):
    mock_nemo_classify.return_value = "assistant"
    mock_qwen.return_value.generate.return_value = "Done."
    mock_glm.return_value = '{"score": 7, "issues": ["incomplete"], "recommendation": "revise"}'
    mock_send.return_value = True

    from aho.agents.conductor import Conductor
    conductor = Conductor()
    result = conductor.dispatch("run task", design="design doc", plan="plan doc")
    assert result["review"]["recommendation"] == "revise"
    conductor.close()


@patch("aho.agents.conductor.send")
@patch("aho.agents.roles.evaluator_agent.glm_generate")
@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.nemoclaw.classify")
@patch("aho.agents.conductor.log_event")
def test_conductor_logs_dispatch(mock_conductor_log, mock_nemo_classify, mock_qwen, mock_glm, mock_send):
    mock_nemo_classify.return_value = "assistant"
    mock_qwen.return_value.generate.return_value = "{}"
    mock_glm.return_value = '{"score": 8}'
    mock_send.return_value = True

    from aho.agents.conductor import Conductor
    conductor = Conductor()
    conductor.dispatch("test task")
    assert mock_conductor_log.call_count >= 1
    conductor.close()
