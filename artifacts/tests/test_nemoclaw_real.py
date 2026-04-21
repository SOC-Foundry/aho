"""Tests for NemoClaw real implementation — routing, dispatch, daemon."""
import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_route_returns_role(mock_qwen_cls, mock_classify_task):
    """Route classifies task into a role."""
    from aho.agents.nemoclaw import NemoClawOrchestrator
    mock_classify_task.return_value = "code_runner"
    mock_qwen_cls.return_value = MagicMock()
    orch = NemoClawOrchestrator(session_count=3, roles=["assistant", "code_runner", "reviewer"])
    role = orch.route("write a python script to sort a list")
    assert role == "code_runner"
    mock_classify_task.assert_called_once()
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_dispatch_routes_and_chats(mock_qwen_cls, mock_classify):
    """Dispatch classifies then sends to correct session."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.return_value = "Here is the answer."
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=2, roles=["assistant", "code_runner"])
    result = orch.dispatch("explain the eleven pillars")
    assert result == "Here is the answer."
    assert len(orch.sessions[0].history) == 2  # user + assistant
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_dispatch_with_explicit_role(mock_qwen_cls, mock_classify):
    """Dispatch with explicit role skips classification."""
    mock_client = MagicMock()
    mock_client.generate.return_value = "Code result."
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=2, roles=["assistant", "code_runner"])
    result = orch.dispatch("run this code", role="code_runner")
    assert result == "Code result."
    mock_classify.assert_not_called()
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_session_reuse(mock_qwen_cls, mock_classify):
    """Second dispatch to same role reuses session."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.side_effect = ["First.", "Second."]
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=1, roles=["assistant"])
    orch.dispatch("first question")
    orch.dispatch("second question")
    # Same session should have 4 history entries (2 user + 2 assistant)
    assert len(orch.sessions[0].history) == 4
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_collect_returns_histories(mock_qwen_cls, mock_classify):
    """Collect returns all session histories."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.return_value = "ok"
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=2, roles=["assistant", "reviewer"])
    orch.dispatch("test", role="assistant")
    collected = orch.collect()
    assert "assistant" in collected
    assert len(collected["assistant"]) == 2
    orch.close_all()


# --- Daemon protocol tests ---

@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_daemon_status(mock_qwen_cls, mock_classify):
    """Daemon responds to status command."""
    from aho.agents.nemoclaw import NemoClawHandler, _orchestrator
    import aho.agents.nemoclaw as nemoclaw_mod
    import socketserver

    mock_qwen_cls.return_value = MagicMock()
    # Reset global orchestrator
    nemoclaw_mod._orchestrator = None

    sock_path = Path(tempfile.mkdtemp()) / "test-nemoclaw.sock"
    server = socketserver.UnixStreamServer(str(sock_path), NemoClawHandler)
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    time.sleep(0.1)

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(sock_path))
    client.sendall(b'{"cmd":"status"}\n')
    resp = client.recv(4096).decode()
    client.close()
    data = json.loads(resp)
    assert data["ok"] is True
    assert "session_count" in data

    # Cleanup
    if nemoclaw_mod._orchestrator:
        nemoclaw_mod._orchestrator.close_all()
    nemoclaw_mod._orchestrator = None
    server.server_close()
    sock_path.unlink(missing_ok=True)
    sock_path.parent.rmdir()
