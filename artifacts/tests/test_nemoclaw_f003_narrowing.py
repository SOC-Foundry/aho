"""Tests for nemoclaw.py F003 exception narrowing (0.2.16 W0).

0.2.15 W3 F003 left two broad `except Exception` sites in nemoclaw.py:
  - line 77 (NemoClawOrchestrator.dispatch, around matching_session.chat)
  - line 134 (NemoClawHandler.handle, dispatch cmd branch)

0.2.16 W0 narrows both. Observed transport failures (connection, timeout,
decode) are caught and returned as error results; programmer errors and
classification failures now propagate rather than being silently swallowed.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from aho.pipeline.router import ClassificationError, DispatchError


# ---------------------------------------------------------------------------
# NemoClawOrchestrator.dispatch — line 77 narrowing
# ---------------------------------------------------------------------------

@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_dispatch_catches_connection_error(mock_qwen_cls, mock_classify):
    """ConnectionError during chat → returns '[error] ...' string."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.side_effect = ConnectionError("conn refused")
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=1, roles=["assistant"])
    result = orch.dispatch("task text")
    assert result.startswith("[error]")
    assert "conn refused" in result
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_dispatch_catches_timeout_error(mock_qwen_cls, mock_classify):
    """TimeoutError during chat → returns '[error] ...' string."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.side_effect = TimeoutError("request timed out")
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=1, roles=["assistant"])
    result = orch.dispatch("task text")
    assert result.startswith("[error]")
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_dispatch_catches_json_decode_error(mock_qwen_cls, mock_classify):
    """json.JSONDecodeError during chat → returns '[error] ...' string."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.side_effect = json.JSONDecodeError("bad", "doc", 0)
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=1, roles=["assistant"])
    result = orch.dispatch("task text")
    assert result.startswith("[error]")
    orch.close_all()


@patch("aho.agents.nemoclaw.classify_task")
@patch("aho.agents.openclaw.QwenClient")
def test_dispatch_does_not_catch_attribute_error(mock_qwen_cls, mock_classify):
    """Programmer error (AttributeError) propagates — no longer masked."""
    mock_classify.return_value = "assistant"
    mock_client = MagicMock()
    mock_client.generate.side_effect = AttributeError("missing method")
    mock_qwen_cls.return_value = mock_client
    from aho.agents.nemoclaw import NemoClawOrchestrator
    orch = NemoClawOrchestrator(session_count=1, roles=["assistant"])
    with pytest.raises(AttributeError):
        orch.dispatch("task text")
    orch.close_all()


# ---------------------------------------------------------------------------
# NemoClawHandler.handle — line 134 narrowing
# ---------------------------------------------------------------------------

def _make_handler_for_cmd(cmd_req: dict, orch_mock) -> tuple[MagicMock, MagicMock]:
    """Build a NemoClawHandler with a mock request file and mock orchestrator."""
    from aho.agents.nemoclaw import NemoClawHandler

    rfile = MagicMock()
    rfile.readline.return_value = (json.dumps(cmd_req) + "\n").encode("utf-8")
    wfile = MagicMock()

    handler = NemoClawHandler.__new__(NemoClawHandler)
    handler.rfile = rfile
    handler.wfile = wfile
    return handler, wfile


@patch("aho.agents.nemoclaw._get_orchestrator")
def test_handler_dispatch_catches_classification_error(mock_get_orch):
    """ClassificationError from implicit route → structured error reply."""
    orch = MagicMock()
    orch.dispatch.side_effect = ClassificationError("no category", raw_response="garbage")
    mock_get_orch.return_value = orch

    handler, wfile = _make_handler_for_cmd(
        {"cmd": "dispatch", "task": "ambiguous"}, orch
    )
    handler.handle()

    written = wfile.write.call_args[0][0].decode("utf-8")
    reply = json.loads(written)
    assert reply["ok"] is False
    assert reply["error_type"] == "classification_error"
    assert reply["raw_response"] == "garbage"


@patch("aho.agents.nemoclaw._get_orchestrator")
def test_handler_dispatch_catches_dispatch_error(mock_get_orch):
    """DispatchError from router → structured error reply."""
    orch = MagicMock()
    orch.dispatch.side_effect = DispatchError("router down")
    mock_get_orch.return_value = orch

    handler, wfile = _make_handler_for_cmd(
        {"cmd": "dispatch", "task": "x"}, orch
    )
    handler.handle()

    written = wfile.write.call_args[0][0].decode("utf-8")
    reply = json.loads(written)
    assert reply["ok"] is False
    assert reply["error_type"] == "DispatchError"


@patch("aho.agents.nemoclaw._get_orchestrator")
def test_handler_dispatch_does_not_catch_value_error(mock_get_orch):
    """Unhandled ValueError propagates — F003 no longer swallows."""
    orch = MagicMock()
    orch.dispatch.side_effect = ValueError("unexpected")
    mock_get_orch.return_value = orch

    handler, wfile = _make_handler_for_cmd(
        {"cmd": "dispatch", "task": "x"}, orch
    )
    with pytest.raises(ValueError):
        handler.handle()
