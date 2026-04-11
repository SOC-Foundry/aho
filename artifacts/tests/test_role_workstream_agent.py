"""Tests for WorkstreamAgent (0.2.3 W2 role split)."""
import json
import pytest
from unittest.mock import patch, MagicMock


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.logger.log_event")
def test_workstream_agent_creates_session(mock_log, mock_qwen):
    mock_qwen.return_value.generate.return_value = '{"status": "pass", "deliverables": ["test"]}'
    from aho.agents.roles.workstream_agent import WorkstreamAgent
    agent = WorkstreamAgent()
    assert agent.session.role == "workstream"
    agent.close()


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.logger.log_event")
def test_workstream_agent_execute(mock_log, mock_qwen):
    mock_qwen.return_value.generate.return_value = '{"status": "pass", "deliverables": ["artifact.md"]}'
    from aho.agents.roles.workstream_agent import WorkstreamAgent
    agent = WorkstreamAgent()
    result = agent.execute_workstream("W1", "Build the thing")
    assert result["workstream"] == "W1"
    assert result["status"] == "pass"
    agent.close()


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.logger.log_event")
def test_workstream_agent_handles_non_json(mock_log, mock_qwen):
    mock_qwen.return_value.generate.return_value = "I completed the task successfully."
    from aho.agents.roles.workstream_agent import WorkstreamAgent
    agent = WorkstreamAgent()
    result = agent.execute_workstream("W0", "Do something")
    assert result["workstream"] == "W0"
    assert result["status"] == "pass"
    assert "I completed" in result["raw"]
    agent.close()


@patch("aho.agents.openclaw.QwenClient")
@patch("aho.agents.roles.workstream_agent.log_event")
def test_workstream_agent_logs_events(mock_log, mock_qwen):
    mock_qwen.return_value.generate.return_value = "{}"
    from aho.agents.roles.workstream_agent import WorkstreamAgent
    agent = WorkstreamAgent()
    agent.execute_workstream("W2", "Test plan")
    assert mock_log.call_count >= 2  # execute + execute_complete
    agent.close()
