"""Classification router — thin routing layer over the hardened dispatcher.

0.2.15 W3: supersedes `aho.artifacts.nemotron_client.classify()`. Uses
`/api/chat` (W2 hardened dispatcher) instead of `/api/generate`, so
model-family chat templates are applied server-side. This improves
classifier conformance on small models (see W3 comparison).

0.2.16 W2: W3C TRACEPARENT propagation — wraps classify_task in an
`aho.route.classify` span (child of parent when TRACEPARENT is set,
root otherwise).

Callers that need classification (Nemoclaw.route, conductor dispatch
bookkeeping, future routers) invoke `classify_task(...)`.
"""
import os
import time
from typing import Optional

from aho.pipeline.dispatcher import (
    DispatchError,
    ModelUnavailableError,
    TemplateLeakError,
    MalformedResponseError,
    DispatchTimeoutError,
    dispatch,
)

try:
    from opentelemetry import trace as _otel_trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    _tracer = _otel_trace.get_tracer("aho.pipeline.router")
    _propagator = TraceContextTextMapPropagator()
except ImportError:
    _otel_trace = None
    Status = None
    StatusCode = None
    _tracer = None
    _propagator = None


DEFAULT_CLASSIFIER_MODEL = "nemotron-mini:4b"
DEFAULT_TIMEOUT = 30
DEFAULT_NUM_CTX = 2048

# Span attribute truncation. Trace payloads should be lean — input text is
# kept only as a debug breadcrumb, not a full record of classifier input.
INPUT_EXCERPT_MAX_CHARS = 200


class ClassificationError(DispatchError):
    """Raised when the classifier response cannot be matched to any category."""

    def __init__(self, message: str, raw_response: str = "", categories=None):
        super().__init__(message)
        self.raw_response = raw_response
        self.categories = list(categories) if categories is not None else []


def _build_system_prompt(categories: list[str], bias: Optional[str]) -> str:
    prompt = (
        "You are a precise classifier. Categorize the input text into EXACTLY ONE "
        f"of these categories: {', '.join(categories)}. "
        "Respond with ONLY the category name."
    )
    if bias:
        prompt += f" Bias: {bias}"
    return prompt


def _match_category(raw: str, categories: list[str]) -> Optional[str]:
    normalized = raw.strip().strip("'\"").strip()
    for cat in categories:
        if cat.lower() in normalized.lower():
            return cat
    return None


def _resolve_span_parent_context():
    """Resolve parent context for a new router span.

    Precedence: if a span is already active in the Python context, nest
    under it. Otherwise fall back to env TRACEPARENT. Returns None to
    signal "use default active context."
    """
    if _otel_trace is None:
        return None
    current = _otel_trace.get_current_span()
    if current.get_span_context().is_valid:
        return None
    if _propagator is None:
        return None
    traceparent = os.environ.get("TRACEPARENT")
    if not traceparent:
        return None
    return _propagator.extract(carrier={"traceparent": traceparent})


_extract_parent_context = _resolve_span_parent_context


def classify_task(
    task: str,
    categories: list[str],
    *,
    model: str = DEFAULT_CLASSIFIER_MODEL,
    bias: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    num_ctx: int = DEFAULT_NUM_CTX,
) -> str:
    """Classify `task` into exactly one of `categories` using the hardened dispatcher.

    Args:
        task: The text to classify.
        categories: Non-empty list of allowed category names.
        model: Ollama model id (defaults to nemotron-mini:4b).
        bias: Optional hint appended to the system prompt
              (e.g., "Prefer 'assistant' for general tasks").
        timeout: Per-request dispatch timeout in seconds.
        num_ctx: Context window size for the classifier.

    Returns:
        The matched category name (one of `categories`).

    Raises:
        ValueError: if `categories` is empty.
        ClassificationError: if the model response does not match any category.
        DispatchError (and subclasses): propagated from the dispatcher for
            transport, timeout, malformed response, template leak, or
            model-unavailable conditions.
    """
    if not categories:
        raise ValueError("classify_task requires a non-empty categories list")

    def _run_classify():
        system = _build_system_prompt(categories, bias)
        prompt = f"Text to classify:\n{task}\n\nCategory:"

        result = dispatch(
            model, prompt, system=system,
            timeout=timeout, num_ctx=num_ctx, max_retries=0,
            raise_on_error=True,
        )

        raw = result.get("response", "")
        matched = _match_category(raw, categories)
        if matched is None:
            raise ClassificationError(
                f"Classifier response {raw!r} does not match any category: {categories}",
                raw_response=raw,
                categories=categories,
            )
        return matched

    if _tracer is None:
        return _run_classify()

    parent_ctx = _resolve_span_parent_context()
    span_kwargs = {"context": parent_ctx} if parent_ctx is not None else {}

    span_start = time.monotonic()
    with _tracer.start_as_current_span("aho.route.classify", **span_kwargs) as span:
        span.set_attribute("aho.classifier_model", model)
        span.set_attribute("aho.input_excerpt", task[:INPUT_EXCERPT_MAX_CHARS])
        try:
            matched = _run_classify()
        except DispatchError as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
            span.set_attribute(
                "aho.duration_ms",
                round((time.monotonic() - span_start) * 1000.0, 2),
            )
            raise

        span.set_attribute("aho.category", matched)
        span.set_attribute(
            "aho.duration_ms",
            round((time.monotonic() - span_start) * 1000.0, 2),
        )
        return matched


__all__ = [
    "ClassificationError",
    "classify_task",
    "DispatchError",
    "ModelUnavailableError",
    "TemplateLeakError",
    "MalformedResponseError",
    "DispatchTimeoutError",
]
