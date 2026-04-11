"""Tests for HarnessAgent (0.2.3 W2 role split)."""
import json
import pytest
from unittest.mock import patch, MagicMock


@patch("aho.agents.roles.harness_agent.classify")
@patch("aho.logger.log_event")
def test_harness_agent_propose_gotcha(mock_log, mock_classify):
    mock_classify.return_value = "gotcha"
    from aho.agents.roles.harness_agent import HarnessAgent
    agent = HarnessAgent()
    result = agent.propose_gotcha({"event_type": "error", "error": "timeout"})
    assert result["propose"] is True
    assert result["code"].startswith("aho-G")


@patch("aho.agents.roles.harness_agent.classify")
@patch("aho.logger.log_event")
def test_harness_agent_propose_noise(mock_log, mock_classify):
    mock_classify.return_value = "noise"
    from aho.agents.roles.harness_agent import HarnessAgent
    agent = HarnessAgent()
    result = agent.propose_gotcha({"event_type": "heartbeat"})
    assert result["propose"] is False
    assert result["category"] == "noise"


@patch("aho.agents.roles.harness_agent.classify")
@patch("aho.logger.log_event")
def test_harness_agent_propose_adr(mock_log, mock_classify):
    mock_classify.return_value = "adr"
    from aho.agents.roles.harness_agent import HarnessAgent
    agent = HarnessAgent()
    result = agent.propose_adr("Observed pattern: agents retry 3 times before failing")
    assert result["propose"] is True


@patch("aho.agents.roles.harness_agent.classify")
@patch("aho.logger.log_event")
def test_harness_agent_propose_component(mock_log, mock_classify):
    mock_classify.return_value = "new_component"
    from aho.agents.roles.harness_agent import HarnessAgent
    agent = HarnessAgent()
    result = agent.propose_component("detected new LLM client: deepseek")
    assert result["propose"] is True
