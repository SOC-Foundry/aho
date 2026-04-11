"""Tests for OpenClaw real implementation — session, chat, execute, daemon."""
import json
import os
import shutil
import socket
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# --- Session unit tests ---

@patch("aho.agents.openclaw.QwenClient")
def test_session_creation(mock_qwen_cls):
    """Session creates workspace and initializes history."""
    from aho.agents.openclaw import OpenClawSession
    mock_qwen_cls.return_value = MagicMock()
    s = OpenClawSession(role="assistant")
    assert s.session_id
    assert s.workdir.exists()
    assert s.history == []
    assert s.role == "assistant"
    s.close()
    assert not s.workdir.exists()


@patch("aho.agents.openclaw.QwenClient")
def test_session_chat(mock_qwen_cls):
    """Chat appends to history and returns response."""
    from aho.agents.openclaw import OpenClawSession
    mock_client = MagicMock()
    mock_client.generate.return_value = "Hello from Qwen"
    mock_qwen_cls.return_value = mock_client
    s = OpenClawSession(role="assistant")
    resp = s.chat("say hello")
    assert resp == "Hello from Qwen"
    assert len(s.history) == 2
    assert s.history[0]["role"] == "user"
    assert s.history[1]["role"] == "assistant"
    s.close()


@patch("aho.agents.openclaw.QwenClient")
def test_session_execute_code(mock_qwen_cls):
    """Code execution runs in subprocess and captures output."""
    from aho.agents.openclaw import OpenClawSession
    mock_qwen_cls.return_value = MagicMock()
    s = OpenClawSession(role="code_runner")
    result = s.execute_code("print('hello')", language="python")
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]
    assert result["timed_out"] is False
    s.close()


@patch("aho.agents.openclaw.QwenClient")
def test_session_execute_timeout(mock_qwen_cls):
    """Code execution handles timeout."""
    from aho.agents.openclaw import OpenClawSession
    mock_qwen_cls.return_value = MagicMock()
    s = OpenClawSession()
    result = s.execute_code("import time; time.sleep(10)", language="python", timeout=1)
    assert result["timed_out"] is True
    assert result["exit_code"] == -1
    s.close()


@patch("aho.agents.openclaw.QwenClient")
def test_session_cleanup_idempotent(mock_qwen_cls):
    """Calling close() twice is safe."""
    from aho.agents.openclaw import OpenClawSession
    mock_qwen_cls.return_value = MagicMock()
    s = OpenClawSession()
    s.close()
    s.close()  # Should not raise


# --- Daemon protocol tests ---

@patch("aho.agents.openclaw.QwenClient")
def test_daemon_status_command(mock_qwen_cls):
    """Daemon responds to status command over Unix socket."""
    from aho.agents.openclaw import OpenClawHandler, _sessions
    import socketserver

    mock_qwen_cls.return_value = MagicMock()
    _sessions.clear()

    sock_path = Path(tempfile.mkdtemp()) / "test-openclaw.sock"
    server = socketserver.UnixStreamServer(str(sock_path), OpenClawHandler)
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
    assert data["session_count"] == 0

    server.server_close()
    sock_path.unlink(missing_ok=True)
    sock_path.parent.rmdir()


@patch("aho.agents.openclaw.QwenClient")
def test_daemon_chat_command(mock_qwen_cls):
    """Daemon handles chat command and returns response."""
    from aho.agents.openclaw import OpenClawHandler, _sessions
    import socketserver

    mock_client = MagicMock()
    mock_client.generate.return_value = "daemon reply"
    mock_qwen_cls.return_value = mock_client
    _sessions.clear()

    sock_path = Path(tempfile.mkdtemp()) / "test-openclaw.sock"
    server = socketserver.UnixStreamServer(str(sock_path), OpenClawHandler)
    t = threading.Thread(target=server.handle_request, daemon=True)
    t.start()
    time.sleep(0.1)

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(str(sock_path))
    client.sendall(b'{"cmd":"chat","message":"test","role":"assistant"}\n')
    resp = client.recv(4096).decode()
    client.close()
    data = json.loads(resp)
    assert data["ok"] is True
    assert data["response"] == "daemon reply"

    # Clean up created session
    for s in _sessions.values():
        s.close()
    _sessions.clear()
    server.server_close()
    sock_path.unlink(missing_ok=True)
    sock_path.parent.rmdir()
