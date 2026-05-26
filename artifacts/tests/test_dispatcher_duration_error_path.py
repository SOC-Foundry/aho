"""Error-path dispatch.duration_ms measurement consistency (0.2.17 W0 - W2-AF004).

Success path (dispatcher.py line ~466) reads dispatch.duration_ms from
result['wall_clock_seconds'] * 1000 - same source as the event log,
zero drift by construction. Error path (line ~458-461) reads it from
(time.monotonic() - span_start) * 1000 - a different measurement site.

The 0.2.16 carry-forward measured success-path drift at 0.11ms (rounding).
Error-path drift was unmeasured. This test measures it and asserts <1ms.
If this assertion ever fails the measurement sites should be unified -
that is a larger refactor than this test, so the bound here is the
trip-wire that surfaces the need.
"""
from __future__ import annotations

import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from aho.pipeline import dispatcher


class _TracerHarness:
    def __init__(self):
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer = self.provider.get_tracer("test.aho.pipeline.dispatcher.duration")

    def spans(self):
        return list(self.exporter.get_finished_spans())


def _raising_urlopen(*_a, **_kw):
    raise urllib.error.URLError("simulated connection refused")


class TestErrorPathDurationConsistency(unittest.TestCase):
    """Drift between span-end-minus-span-start and the dispatcher's reported
    dispatch.duration_ms attribute, measured on the error path with retries
    exhausted. Bound: <1.0ms - exceeding it means the measurement sites have
    diverged enough that unification is warranted.
    """

    def setUp(self):
        self.harness = _TracerHarness()
        self._tracer_patch = patch.object(dispatcher, "_tracer", self.harness.tracer)
        self._tracer_patch.start()
        # Skip backoff sleeps so the test runs in microseconds.
        self._sleep_patch = patch("time.sleep", lambda *a, **k: None)
        self._sleep_patch.start()

    def tearDown(self):
        self._tracer_patch.stop()
        self._sleep_patch.stop()

    def test_error_path_duration_attribute_set_and_consistent(self):
        with patch("urllib.request.urlopen", side_effect=_raising_urlopen):
            with self.assertRaises(dispatcher.DispatchError):
                dispatcher.dispatch(
                    "qwen3.5:9b",
                    "hi",
                    max_retries=0,
                    raise_on_error=True,
                )

        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]

        attrs = dict(span.attributes)
        self.assertIn("dispatch.duration_ms", attrs)
        reported_ms = float(attrs["dispatch.duration_ms"])
        self.assertGreaterEqual(reported_ms, 0.0)

        # Span end - start is the ground truth wall-clock; convert ns → ms.
        actual_ms = (span.end_time - span.start_time) / 1e6
        drift_ms = abs(reported_ms - actual_ms)
        self.assertLess(
            drift_ms,
            1.0,
            f"error-path drift {drift_ms:.3f}ms exceeds 1ms tolerance "
            f"(reported={reported_ms:.3f}ms, actual={actual_ms:.3f}ms). "
            f"W2-AF004 trip-wire: unify measurement site in dispatcher.py.",
        )

    def test_error_path_duration_with_retries_grows_with_attempts(self):
        """Sanity: with max_retries=2, the reported duration should still
        reflect the wall-clock span duration (not stay near zero from the
        first attempt only)."""
        with patch("urllib.request.urlopen", side_effect=_raising_urlopen):
            with self.assertRaises(dispatcher.DispatchError):
                dispatcher.dispatch(
                    "qwen3.5:9b",
                    "hi",
                    max_retries=2,
                    backoff_base=0.001,
                    raise_on_error=True,
                )
        spans = self.harness.spans()
        self.assertEqual(len(spans), 1)
        attrs = dict(spans[0].attributes)
        reported_ms = float(attrs["dispatch.duration_ms"])
        actual_ms = (spans[0].end_time - spans[0].start_time) / 1e6
        # With retries the actual duration is non-trivial; reported must track it.
        self.assertLess(abs(reported_ms - actual_ms), 1.0)


if __name__ == "__main__":
    unittest.main()
