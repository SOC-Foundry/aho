"""Tests for OTEL dual emitter in logger.py."""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_jsonl_written_without_otel(tmp_path):
    """JSONL logging works when OTEL is disabled."""
    log_path = tmp_path / "events.jsonl"

    with patch("aho.logger.LOG_PATH", str(log_path)), \
         patch("aho.logger._otel_tracer", None):
        from aho.logger import log_event
        ev = log_event(
            event_type="test_event",
            source_agent="test",
            target="test_target",
            action="smoke",
            workstream_id="W0",
        )

    assert log_path.exists()
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event_type"] == "test_event"
    assert data["source_agent"] == "test"


def test_otel_span_emitted_when_enabled(tmp_path):
    """When OTEL tracer is set, a span should be started."""
    log_path = tmp_path / "events.jsonl"

    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
    mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

    with patch("aho.logger.LOG_PATH", str(log_path)), \
         patch("aho.logger._otel_tracer", mock_tracer):
        from aho.logger import log_event
        log_event(
            event_type="otel_test",
            source_agent="test",
            target="target",
            action="verify",
            tokens=100,
            latency_ms=50,
        )

    # JSONL still written
    assert log_path.exists()
    data = json.loads(log_path.read_text().strip())
    assert data["event_type"] == "otel_test"

    # OTEL span started
    mock_tracer.start_as_current_span.assert_called_once_with("otel_test")
    mock_span.set_attribute.assert_any_call("aho.event_type", "otel_test")
    mock_span.set_attribute.assert_any_call("aho.tokens", 100)
    mock_span.set_attribute.assert_any_call("aho.latency_ms", 50)


def test_otel_dict_tokens_flattened_to_scalars(tmp_path):
    """Dict tokens must be flattened to scalar attributes (aho-G064)."""
    log_path = tmp_path / "events.jsonl"

    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
    mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

    with patch("aho.logger.LOG_PATH", str(log_path)), \
         patch("aho.logger._otel_tracer", mock_tracer):
        from aho.logger import log_event
        log_event(
            event_type="dict_tokens_test",
            source_agent="test",
            target="target",
            action="verify",
            tokens={"total": 56, "input": 30, "output": 26},
        )

    # Should set individual scalar attributes, not a single dict
    mock_span.set_attribute.assert_any_call("aho.tokens.total", 56)
    mock_span.set_attribute.assert_any_call("aho.tokens.input", 30)
    mock_span.set_attribute.assert_any_call("aho.tokens.output", 26)
    # Must NOT have set the raw dict
    for call in mock_span.set_attribute.call_args_list:
        if call[0][0] == "aho.tokens":
            pytest.fail("aho.tokens set as dict instead of flattened scalars")


def test_set_attrs_from_dict_nested(tmp_path):
    """set_attrs_from_dict handles nested dicts and scalars (aho-G064)."""
    from aho.logger import set_attrs_from_dict
    mock_span = MagicMock()
    set_attrs_from_dict(mock_span, "test", {"a": 1, "b": {"c": "deep"}})
    mock_span.set_attribute.assert_any_call("test.a", 1)
    mock_span.set_attribute.assert_any_call("test.b.c", "deep")


def test_set_attrs_from_dict_scalar(tmp_path):
    """set_attrs_from_dict handles plain scalar values."""
    from aho.logger import set_attrs_from_dict
    mock_span = MagicMock()
    set_attrs_from_dict(mock_span, "test.count", 42)
    mock_span.set_attribute.assert_called_once_with("test.count", 42)


def test_otel_failure_does_not_break_jsonl(tmp_path):
    """If OTEL tracer raises, JSONL must still be written."""
    log_path = tmp_path / "events.jsonl"

    mock_tracer = MagicMock()
    mock_tracer.start_as_current_span.side_effect = RuntimeError("OTEL boom")

    with patch("aho.logger.LOG_PATH", str(log_path)), \
         patch("aho.logger._otel_tracer", mock_tracer):
        from aho.logger import log_event
        ev = log_event(
            event_type="resilience_test",
            source_agent="test",
            target="target",
            action="crash",
        )

    assert log_path.exists()
    data = json.loads(log_path.read_text().strip())
    assert data["event_type"] == "resilience_test"
