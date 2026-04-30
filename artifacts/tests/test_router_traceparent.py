"""Unit tests for router TRACEPARENT propagation (0.2.16 W2).

- test_absent: no TRACEPARENT → router emits a root aho.route.classify span.
- test_present: TRACEPARENT set → router emits a child span inheriting trace_id.

Mocks `aho.pipeline.router.dispatch` so the Ollama HTTP layer is out-of-band.
Mocks `router._tracer` with an in-memory-exporting tracer to inspect spans.
"""
import os
import unittest
from unittest.mock import patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from aho.pipeline import router


PARENT_TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
PARENT_TRACE_ID_INT = int("0af7651916cd43dd8448eb211c80319c", 16)
PARENT_SPAN_ID_INT = int("b7ad6b7169203331", 16)


class _TracerHarness:
    def __init__(self):
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer = self.provider.get_tracer("test.aho.pipeline.router")

    def spans(self):
        return list(self.exporter.get_finished_spans())


def _dispatch_result(response: str) -> dict:
    return {
        "response": response,
        "error": None,
        "wall_clock_seconds": 0.1,
        "model": "nemotron-mini:4b",
        "family": "nemotron",
        "total_duration_ms": 100.0,
        "retries_used": 0,
        "tokens_eval": 3,
        "tokens_prompt": 10,
    }


class TestRouterTraceparentAbsent(unittest.TestCase):

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(router, "_tracer", self.harness.tracer)
        self._tracer_patch.start()
        os.environ.pop("TRACEPARENT", None)

    def tearDown(self):
        self._tracer_patch.stop()

    def test_absent_emits_root_span(self):
        with patch.object(router, "dispatch", return_value=_dispatch_result("code")):
            category = router.classify_task(
                "write a fibonacci function",
                ["code", "prose", "other"],
            )

        self.assertEqual(category, "code")
        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertIsNone(span.parent)
        self.assertEqual(span.name, "aho.route.classify")
        attrs = dict(span.attributes)
        self.assertEqual(attrs["aho.classifier_model"], router.DEFAULT_CLASSIFIER_MODEL)
        self.assertEqual(attrs["aho.category"], "code")
        self.assertIn("aho.duration_ms", attrs)
        # Input excerpt present and bounded
        self.assertIn("aho.input_excerpt", attrs)
        self.assertLessEqual(len(attrs["aho.input_excerpt"]), router.INPUT_EXCERPT_MAX_CHARS)


class TestRouterTraceparentPresent(unittest.TestCase):

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(router, "_tracer", self.harness.tracer)
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
        with patch.object(router, "dispatch", return_value=_dispatch_result("prose")):
            category = router.classify_task(
                "once upon a time there was a function",
                ["code", "prose", "other"],
            )

        self.assertEqual(category, "prose")
        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.context.trace_id, PARENT_TRACE_ID_INT)
        self.assertIsNotNone(span.parent)
        self.assertEqual(span.parent.span_id, PARENT_SPAN_ID_INT)


class TestRouterTraceparentExcerptTruncation(unittest.TestCase):

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(router, "_tracer", self.harness.tracer)
        self._tracer_patch.start()
        os.environ.pop("TRACEPARENT", None)

    def tearDown(self):
        self._tracer_patch.stop()

    def test_long_input_truncated_to_named_constant(self):
        long_task = "x" * (router.INPUT_EXCERPT_MAX_CHARS * 3)
        with patch.object(router, "dispatch", return_value=_dispatch_result("code")):
            router.classify_task(long_task, ["code", "prose"])

        attrs = dict(self.harness.spans()[0].attributes)
        self.assertEqual(len(attrs["aho.input_excerpt"]), router.INPUT_EXCERPT_MAX_CHARS)


if __name__ == "__main__":
    unittest.main()
