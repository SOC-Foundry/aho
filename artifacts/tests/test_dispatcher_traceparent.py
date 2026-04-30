"""Unit tests for dispatcher TRACEPARENT propagation (0.2.16 W2).

- test_absent: no TRACEPARENT env → dispatcher emits a root span.
- test_present: TRACEPARENT env set → dispatcher emits a child span whose
  trace_id matches the parent traceparent value.

Mocks urllib.request.urlopen to keep the Ollama call out-of-band. Mocks the
OTEL SDK boundary by swapping `dispatcher._tracer` for an in-memory-exporting
tracer so span contents can be inspected without touching the real OTLP
pipeline.
"""
import json
import unittest
from unittest.mock import patch, MagicMock

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from aho.pipeline import dispatcher


PARENT_TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
PARENT_TRACE_ID_INT = int("0af7651916cd43dd8448eb211c80319c", 16)
PARENT_SPAN_ID_INT = int("b7ad6b7169203331", 16)


def _chat_response(content: str = "ok", model: str = "qwen3.5:9b"):
    """Build a mock /api/chat HTTP response."""
    body = {
        "model": model,
        "message": {"role": "assistant", "content": content},
        "total_duration": 5_000_000_000,
        "eval_count": 42,
        "prompt_eval_count": 17,
        "done": True,
    }
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class _TracerHarness:
    """Isolated tracer + in-memory exporter patched onto dispatcher module."""

    def __init__(self):
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer = self.provider.get_tracer("test.aho.pipeline.dispatcher")

    def spans(self):
        return list(self.exporter.get_finished_spans())


class TestDispatcherTraceparentAbsent(unittest.TestCase):

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(dispatcher, "_tracer", self.harness.tracer)
        self._tracer_patch.start()
        # Ensure TRACEPARENT absent
        self._env_patch = patch.dict("os.environ", {}, clear=False)
        self._env_patch.start()
        import os
        os.environ.pop("TRACEPARENT", None)

    def tearDown(self):
        self._tracer_patch.stop()
        self._env_patch.stop()

    def test_absent_emits_root_span(self):
        with patch("urllib.request.urlopen", return_value=_chat_response("hello")):
            result = dispatcher.dispatch("qwen3.5:9b", "hi", max_retries=0)

        self.assertIsNone(result.get("error"))
        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        # Root span: no parent
        self.assertIsNone(span.parent)
        # Name follows aho.dispatch.{family}
        self.assertEqual(span.name, "aho.dispatch.qwen")
        # Core attrs present
        attrs = dict(span.attributes)
        self.assertEqual(attrs["aho.model"], "qwen3.5:9b")
        self.assertEqual(attrs["aho.family"], "qwen")
        self.assertIn("dispatch.num_ctx", attrs)
        self.assertIn("dispatch.duration_ms", attrs)
        self.assertEqual(attrs["dispatch.tokens_eval"], 42)
        self.assertEqual(attrs["dispatch.tokens_prompt"], 17)


class TestDispatcherTraceparentPresent(unittest.TestCase):

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(dispatcher, "_tracer", self.harness.tracer)
        self._tracer_patch.start()
        self._env_patch = patch.dict(
            "os.environ",
            {"TRACEPARENT": PARENT_TRACEPARENT},
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self):
        self._tracer_patch.stop()
        self._env_patch.stop()

    def test_present_emits_child_span_inheriting_trace_id(self):
        with patch("urllib.request.urlopen", return_value=_chat_response("hello")):
            result = dispatcher.dispatch(
                "qwen3.5:9b", "hi", max_retries=0, stage="producer"
            )

        self.assertIsNone(result.get("error"))
        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        # Child span: trace_id inherited from traceparent
        self.assertEqual(span.context.trace_id, PARENT_TRACE_ID_INT)
        # Parent span_id matches traceparent span_id
        self.assertIsNotNone(span.parent)
        self.assertEqual(span.parent.span_id, PARENT_SPAN_ID_INT)
        # aho.stage attr propagated when caller passes it
        attrs = dict(span.attributes)
        self.assertEqual(attrs.get("aho.stage"), "producer")
        self.assertEqual(attrs["aho.family"], "qwen")


class TestDispatcherTraceparentMalformed(unittest.TestCase):
    """Malformed TRACEPARENT produces root span — propagator returns an invalid
    context which OTEL treats as no parent. Dispatcher does not raise on
    parse failure because the SDK's propagator handles malformed input by
    returning a NonRecordingSpan context."""

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(dispatcher, "_tracer", self.harness.tracer)
        self._tracer_patch.start()
        self._env_patch = patch.dict(
            "os.environ",
            {"TRACEPARENT": "this-is-not-a-valid-traceparent"},
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self):
        self._tracer_patch.stop()
        self._env_patch.stop()

    def test_malformed_emits_root_span(self):
        with patch("urllib.request.urlopen", return_value=_chat_response("hello")):
            dispatcher.dispatch("qwen3.5:9b", "hi", max_retries=0)
        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        # Invalid parent context → root span
        self.assertIsNone(spans[0].parent)


if __name__ == "__main__":
    unittest.main()
