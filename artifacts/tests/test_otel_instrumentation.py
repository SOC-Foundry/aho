"""Tests for OTEL instrumentation on all 6 instrumented components.

Verifies that each component emits spans via the opentelemetry trace API.
Patches the module-level _tracer in each component to capture span creation.
"""
import pytest
from unittest.mock import patch, MagicMock, call


def _make_mock_tracer():
    """Create a mock tracer that records span creation."""
    tracer = MagicMock()
    spans = []

    class MockSpan:
        def __init__(self, name):
            self.name = name
            self.attributes = {}
            self.exceptions = []
        def set_attribute(self, key, value):
            self.attributes[key] = value
        def record_exception(self, exc):
            self.exceptions.append(exc)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def start_as_current_span(name):
        span = MockSpan(name)
        spans.append(span)
        return span

    tracer.start_as_current_span = start_as_current_span
    return tracer, spans


class TestQwenClientInstrumentation:
    def test_generate_emits_span(self):
        tracer, spans = _make_mock_tracer()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=[
            b'{"response":"hello","done":false}',
            b'{"response":" world","done":true}',
        ])
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("aho.artifacts.qwen_client._tracer", tracer), \
             patch("aho.artifacts.qwen_client.requests.post", return_value=mock_response):
            from aho.artifacts.qwen_client import QwenClient
            client = QwenClient(verbose=False)
            result = client.generate("test prompt")

        span_names = [s.name for s in spans]
        assert "qwen.generate" in span_names
        qwen_span = next(s for s in spans if s.name == "qwen.generate")
        assert qwen_span.attributes["model"] == "qwen3.5:9b"
        assert qwen_span.attributes["status"] == "ok"


class TestNemotronClientInstrumentation:
    def test_classify_emits_span(self):
        tracer, spans = _make_mock_tracer()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "category_a"}

        with patch("aho.artifacts.nemotron_client._tracer", tracer), \
             patch("aho.artifacts.nemotron_client.requests.post", return_value=mock_response):
            from aho.artifacts import nemotron_client
            result = nemotron_client.classify("test text", ["category_a", "category_b"])

        span_names = [s.name for s in spans]
        assert "nemotron.classify" in span_names
        nemo_span = next(s for s in spans if s.name == "nemotron.classify")
        assert nemo_span.attributes["model"] == "nemotron-mini:4b"


class TestGLMClientInstrumentation:
    def test_generate_emits_span(self):
        tracer, spans = _make_mock_tracer()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"response": "test output"}

        with patch("aho.artifacts.glm_client._tracer", tracer), \
             patch("aho.artifacts.glm_client.requests.post", return_value=mock_response):
            from aho.artifacts import glm_client
            result = glm_client.generate("describe this image")

        span_names = [s.name for s in spans]
        assert "glm.generate" in span_names
        glm_span = next(s for s in spans if s.name == "glm.generate")
        assert "GLM" in glm_span.attributes["model"]
        assert glm_span.attributes["image_count"] == 0


class TestOpenClawInstrumentation:
    def test_chat_emits_span(self):
        tracer, spans = _make_mock_tracer()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_lines = MagicMock(return_value=[
            b'{"response":"ok","done":true}',
        ])
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("aho.agents.openclaw._tracer", tracer), \
             patch("aho.artifacts.qwen_client.requests.post", return_value=mock_response):
            from aho.agents.openclaw import OpenClawSession
            session = OpenClawSession()
            result = session.chat("hello")
            session.close()

        span_names = [s.name for s in spans]
        assert "openclaw.chat" in span_names

    def test_execute_code_emits_span(self):
        tracer, spans = _make_mock_tracer()

        with patch("aho.agents.openclaw._tracer", tracer):
            from aho.agents.openclaw import OpenClawSession
            session = OpenClawSession()
            result = session.execute_code("print('hello')")
            session.close()

        span_names = [s.name for s in spans]
        assert "openclaw.execute_code" in span_names
        exec_span = next(s for s in spans if s.name == "openclaw.execute_code")
        assert exec_span.attributes["language"] == "python"


class TestNemoClawInstrumentation:
    def test_dispatch_emits_span(self):
        tracer, spans = _make_mock_tracer()

        mock_ollama = MagicMock()
        mock_ollama.raise_for_status = MagicMock()
        mock_ollama.iter_lines = MagicMock(return_value=[
            b'{"response":"done","done":true}',
        ])
        mock_ollama.__enter__ = MagicMock(return_value=mock_ollama)
        mock_ollama.__exit__ = MagicMock(return_value=False)

        mock_classify = MagicMock()
        mock_classify.raise_for_status = MagicMock()
        mock_classify.json.return_value = {"response": "assistant"}

        with patch("aho.agents.nemoclaw._tracer", tracer), \
             patch("aho.artifacts.qwen_client.requests.post", return_value=mock_ollama), \
             patch("aho.artifacts.nemotron_client.requests.post", return_value=mock_classify):
            from aho.agents.nemoclaw import NemoClawOrchestrator
            orch = NemoClawOrchestrator(session_count=1, roles=["assistant"])
            result = orch.dispatch("test task", role="assistant")
            orch.close_all()

        span_names = [s.name for s in spans]
        assert "nemoclaw.dispatch" in span_names


class TestTelegramInstrumentation:
    def test_send_emits_span_no_creds(self):
        """Telegram send with no creds still emits a span."""
        tracer, spans = _make_mock_tracer()

        with patch("aho.telegram.notifications._tracer", tracer), \
             patch("aho.telegram.notifications._get_creds", return_value=(None, None)):
            from aho.telegram.notifications import send_message
            result = send_message("ahomw", "test message")

        assert result is False
        span_names = [s.name for s in spans]
        assert "telegram.send" in span_names
        tg_span = next(s for s in spans if s.name == "telegram.send")
        assert tg_span.attributes["status"] == "no_creds"
