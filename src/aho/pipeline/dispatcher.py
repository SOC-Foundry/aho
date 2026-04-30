"""Pipeline dispatcher — Ollama HTTP API with multi-model support (0.2.15 W2).

Direct Ollama dispatch for cascade pipeline via /api/chat endpoint.
Per-model-family configuration: stop tokens, num_gpu, num_predict, and
post-processing (GLM template leak strip). Retry with exponential backoff
for transient failures. Specific error types for each failure mode.

History:
- 0.2.14 W1.5: switched from /api/generate to /api/chat (template fix)
- 0.2.15 W2: multi-model hardening — per-family config, error types,
  retry/backoff, timeout enforcement, GLM template strip, model-swap handling
- 0.2.16 W2: W3C TRACEPARENT propagation — child span off parent if
  TRACEPARENT env var is present, root span otherwise
"""
import json
import os
import time
import urllib.request
import urllib.error
from typing import Optional

# OTEL tracer — module-level. logger.py configures the global TracerProvider
# with the OTLP exporter; here we just obtain a named tracer. If the SDK is
# unavailable (AHO_OTEL_DISABLED=1, package missing) the ProxyTracer becomes a
# no-op and every `start_as_current_span` call is a cheap context manager.
try:
    from opentelemetry import trace as _otel_trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    _tracer = _otel_trace.get_tracer("aho.pipeline.dispatcher")
    _propagator = TraceContextTextMapPropagator()
except ImportError:
    _otel_trace = None
    Status = None
    StatusCode = None
    _tracer = None
    _propagator = None


# ---------------------------------------------------------------------------
# Error types (G083: no blanket except Exception)
# ---------------------------------------------------------------------------

class DispatchError(Exception):
    """Base error for all dispatcher failures."""


class MalformedResponseError(DispatchError):
    """Ollama returned a response that doesn't match expected JSON shape."""


class TemplateLeakError(DispatchError):
    """Detected template tokens in model output after post-processing."""


class ModelUnavailableError(DispatchError):
    """Model could not be loaded (OOM, missing, or Ollama down)."""


class DispatchTimeoutError(DispatchError):
    """Request exceeded configured timeout."""


class EmptyContentError(DispatchError):
    """Dispatcher returned cleanly (error=None) but with 0-char content.

    0.2.15 W4 measured this failure mode: Qwen thinking-mode consumed the full
    num_predict budget on cascade-scale prompts, yielding message.content=""
    with done_reason="length" and no error surfaced. The cascade orchestrator
    raises this so the empty content does not propagate silently to downstream
    stages as "[stage X failed: None]" markers.
    """


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OLLAMA_BASE = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 3600  # 60 minutes per stage cap

# 32K chosen for initial repair baseline, not native 256K, because:
# (a) VRAM considerations at Q4_K_M on 2080 SUPER may OOM at full 256K
# (b) Qwen's effective-useful-context may be smaller than advertised
DEFAULT_NUM_CTX = 32768

# Valid num_ctx range — Ollama silently accepts invalid values (R7 finding)
MIN_NUM_CTX = 256
MAX_NUM_CTX = 262144

DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_BASE = 1.0  # seconds

# Template tokens that indicate leakage if found in post-processed output
TEMPLATE_LEAK_TOKENS = [
    "<|begin_of_box|>", "<|end_of_box|>",
    "<|im_start|>", "<|im_end|>",
    "<|endoftext|>",
    "<|eot_id|>", "<|end_of_text|>",
    "<|start_header_id|>", "<|end_header_id|>",
]

# ---------------------------------------------------------------------------
# Per-model-family configuration
#
# Sources:
#   Qwen 3.5:9B — 0.2.14 W1.5 verified, 0.2.15 W0 regression clean
#   Llama 3.2:3B — 0.2.15 W0 probe (Llama 3.x native tokens)
#   GLM-4.6V-Flash-9B — 0.2.15 W0 probe + W1 R11 diagnostic
#   Nemotron-mini:4b — 0.2.15 W0 probe (ChatML-compatible)
# ---------------------------------------------------------------------------

MODEL_FAMILY_CONFIG = {
    "qwen": {
        "stop_tokens": ["<|endoftext|>", "<|im_end|>"],
        # 0.2.15 W4 measured thinking-mode consuming the full 2000 budget on
        # cascade-scale prompts (247K-char doc at 32K context): eval_count=2000,
        # content_chars=0, done_reason="length". 8000 gives thinking headroom
        # plus visible output. Contingency levers if still insufficient:
        # /no_think prefix, non-thinking variant, Producer pre-summarization.
        "num_predict": 8000,
        "num_gpu": None,      # full GPU offload
        "strip_prefix": None,
    },
    "llama3": {
        "stop_tokens": ["<|eot_id|>", "<|end_of_text|>"],
        "num_predict": None,  # default
        "num_gpu": None,      # full GPU offload
        "strip_prefix": None,
    },
    "glm": {
        "stop_tokens": ["<|endoftext|>", "<|end_of_box|>"],
        # GLM wraps output in <|begin_of_box|>...<|end_of_box|>.
        # Using <|end_of_box|> as stop token catches the end; we strip
        # the <|begin_of_box|> prefix from the response content.
        # Confirmed via W1 R11-diagnostic.json probe 4.
        "num_predict": None,
        "num_gpu": 30,        # partial offload — full GPU (41 layers) crashes CUDA OOM on 8GB (W1 R2)
        "strip_prefix": "<|begin_of_box|>",
    },
    "nemotron": {
        # ChatML-compatible (same stop tokens as Qwen)
        "stop_tokens": ["<|endoftext|>", "<|im_end|>"],
        "num_predict": None,
        "num_gpu": None,      # full GPU offload
        "strip_prefix": None,
    },
}

# Model ID → family mapping. Checked by prefix match, longest prefix wins.
MODEL_ID_TO_FAMILY = {
    "qwen": "qwen",
    "llama3": "llama3",
    "llama3.2": "llama3",
    "haervwe/GLM": "glm",
    "glm": "glm",
    "nemotron": "nemotron",
}


def resolve_family(model_id: str) -> str:
    """Resolve a model_id to its family key. Longest prefix match wins.

    Returns family string or 'unknown'.
    """
    model_lower = model_id.lower()
    best_match = ""
    best_family = "unknown"
    for prefix, family in MODEL_ID_TO_FAMILY.items():
        if model_lower.startswith(prefix.lower()) and len(prefix) > len(best_match):
            best_match = prefix
            best_family = family
    return best_family


def get_family_config(model_id: str) -> dict:
    """Get the config dict for a model's family. Falls back to qwen defaults."""
    family = resolve_family(model_id)
    return MODEL_FAMILY_CONFIG.get(family, MODEL_FAMILY_CONFIG["qwen"])


# ---------------------------------------------------------------------------
# Response post-processing
# ---------------------------------------------------------------------------

def _postprocess_response(content: str, family_config: dict) -> str:
    """Strip known template prefixes from model output.

    GLM wraps output in <|begin_of_box|>...<|end_of_box|>. The end token
    is caught by stop tokens; the begin token must be stripped here.
    """
    prefix = family_config.get("strip_prefix")
    if prefix and content.startswith(prefix):
        content = content[len(prefix):]
    return content


def _check_template_leak(content: str) -> "str | bool":
    """Check for residual template tokens in post-processed output.

    Returns the leaked token string if found, False if clean. Callers that
    want a bool field for JSON emission use bool() on the result — False
    stays False, non-empty string becomes True. Never returns None so
    stage JSON writers never emit null for this field (AF002 closure).
    """
    for token in TEMPLATE_LEAK_TOKENS:
        if token in content:
            return token
    return False


# ---------------------------------------------------------------------------
# Parameter validation (R7: Ollama silently accepts invalid num_ctx)
# ---------------------------------------------------------------------------

def _validate_num_ctx(num_ctx: int) -> int:
    """Validate and clamp num_ctx to safe bounds.

    Raises ValueError if num_ctx is not a positive integer.
    """
    if not isinstance(num_ctx, int) or num_ctx < 1:
        raise ValueError(f"num_ctx must be a positive integer, got {num_ctx!r}")
    if num_ctx < MIN_NUM_CTX:
        return MIN_NUM_CTX
    if num_ctx > MAX_NUM_CTX:
        return MAX_NUM_CTX
    return num_ctx


# ---------------------------------------------------------------------------
# TRACEPARENT propagation (0.2.16 W2)
# ---------------------------------------------------------------------------

def _resolve_span_parent_context():
    """Resolve the parent context for a new dispatcher span.

    Precedence: if an in-process span is already active (e.g., dispatch
    called from inside router.classify_task), use the active Python context
    so the new span nests under that caller. Only fall back to env
    TRACEPARENT at the outermost entry, where no in-process span exists yet.

    Returns an OTEL Context to pass to start_as_current_span, or None to
    signal "use default active context."
    """
    if _otel_trace is None:
        return None
    current = _otel_trace.get_current_span()
    if current.get_span_context().is_valid:
        return None  # nest under the active span
    if _propagator is None:
        return None
    traceparent = os.environ.get("TRACEPARENT")
    if not traceparent:
        return None
    return _propagator.extract(carrier={"traceparent": traceparent})


# Back-compat alias — external callers (tests) used the previous name.
_extract_parent_context = _resolve_span_parent_context


# ---------------------------------------------------------------------------
# Core dispatch
# ---------------------------------------------------------------------------

def dispatch(model_id: str, prompt: str, system: Optional[str] = None,
             timeout: int = DEFAULT_TIMEOUT,
             num_ctx: int = DEFAULT_NUM_CTX,
             max_retries: int = DEFAULT_MAX_RETRIES,
             backoff_base: float = DEFAULT_BACKOFF_BASE,
             raise_on_error: bool = False,
             stage: Optional[str] = None) -> dict:
    """Send a prompt to an Ollama model via /api/chat and return the response.

    Uses the chat API with proper message structure to ensure the model's
    chat template is applied server-side (preventing token leakage).
    Per-model-family stop tokens, num_gpu, num_predict, and post-processing
    are applied automatically based on model_id.

    Retry logic: retries on connection errors and timeouts (transient).
    Does NOT retry on template leak (systemic) or malformed response (data).

    Args:
        model_id: Ollama model name (e.g., "qwen3.5:9b", "llama3.2:3b")
        prompt: User message content
        system: Optional system prompt
        timeout: Per-request timeout in seconds
        num_ctx: Context window size (validated and clamped)
        max_retries: Max retry attempts for transient errors (default 2)
        backoff_base: Base delay for exponential backoff in seconds
        raise_on_error: If True, raise typed exceptions instead of returning error dicts

    Returns dict with keys: response, total_duration_ms, model, error,
    wall_clock_seconds, family, retries_used, tokens_eval, tokens_prompt.

    When TRACEPARENT is set on the process environment, emits an
    `aho.dispatch.{family}` span as a child of that parent context; when
    absent, emits it as a root span (preserving non-OTEL caller behavior).
    """
    num_ctx = _validate_num_ctx(num_ctx)
    family_config = get_family_config(model_id)
    family = resolve_family(model_id)

    def _run_dispatch():
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        options = {
            "num_ctx": num_ctx,
            "stop": family_config["stop_tokens"],
        }
        if family_config.get("num_predict") is not None:
            options["num_predict"] = family_config["num_predict"]
        if family_config.get("num_gpu") is not None:
            options["num_gpu"] = family_config["num_gpu"]

        payload = {
            "model": model_id,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        data = json.dumps(payload).encode("utf-8")
        last_error = None
        elapsed = 0.0

        for attempt in range(max_retries + 1):
            if attempt > 0:
                delay = backoff_base * (2 ** (attempt - 1))
                time.sleep(delay)

            req = urllib.request.Request(
                f"{OLLAMA_BASE}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
            )

            start = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw_body = resp.read()
                    elapsed = time.monotonic() - start

                try:
                    body = json.loads(raw_body)
                except (json.JSONDecodeError, ValueError) as e:
                    err = MalformedResponseError(
                        f"JSON decode failed: {e} (first 200 chars: {raw_body[:200]!r})"
                    )
                    if raise_on_error:
                        raise err
                    return _error_result(model_id, family, str(err), elapsed, attempt)

                message = body.get("message")
                if not isinstance(message, dict) or "content" not in message:
                    err = MalformedResponseError(
                        f"Missing message.content in response body keys: {list(body.keys())}"
                    )
                    if raise_on_error:
                        raise err
                    return _error_result(model_id, family, str(err), elapsed, attempt)

                content = message["content"]
                content = _postprocess_response(content, family_config)

                leaked = _check_template_leak(content)
                if leaked:
                    err = TemplateLeakError(
                        f"Template token {leaked!r} found in output after post-processing"
                    )
                    # Template leak is systemic — do NOT retry
                    if raise_on_error:
                        raise err
                    return {
                        "response": content,
                        "total_duration_ms": body.get("total_duration", 0) / 1e6,
                        "model": body.get("model", model_id),
                        "error": f"template_leak: {leaked}",
                        "wall_clock_seconds": round(elapsed, 2),
                        "family": family,
                        "retries_used": attempt,
                        "tokens_eval": body.get("eval_count"),
                        "tokens_prompt": body.get("prompt_eval_count"),
                    }

                return {
                    "response": content,
                    "total_duration_ms": body.get("total_duration", 0) / 1e6,
                    "model": body.get("model", model_id),
                    "error": None,
                    "wall_clock_seconds": round(elapsed, 2),
                    "family": family,
                    "retries_used": attempt,
                    "tokens_eval": body.get("eval_count"),
                    "tokens_prompt": body.get("prompt_eval_count"),
                }

            except urllib.error.HTTPError as e:
                elapsed = time.monotonic() - start
                if e.code == 404:
                    err = ModelUnavailableError(
                        f"Model {model_id!r} not found (HTTP 404)"
                    )
                    # Model missing is not transient — do NOT retry
                    if raise_on_error:
                        raise err
                    return _error_result(model_id, family, str(err), elapsed, attempt)
                # Other HTTP errors — retry
                last_error = f"http_{e.code}: {e.reason}"

            except urllib.error.URLError as e:
                elapsed = time.monotonic() - start
                last_error = f"connection_error: {e}"
                # Transient — will retry

            except (TimeoutError, OSError) as e:
                elapsed = time.monotonic() - start
                if isinstance(e, TimeoutError):
                    last_error = f"timeout after {timeout}s"
                else:
                    last_error = f"os_error: {e}"
                # Transient — will retry

        # All retries exhausted
        if raise_on_error:
            if "timeout" in str(last_error):
                raise DispatchTimeoutError(last_error)
            if "connection_error" in str(last_error):
                raise ModelUnavailableError(last_error)
            raise DispatchError(last_error)

        return _error_result(model_id, family, last_error, elapsed, max_retries)

    if _tracer is None:
        return _run_dispatch()

    parent_ctx = _resolve_span_parent_context()
    span_kwargs = {"context": parent_ctx} if parent_ctx is not None else {}

    span_start = time.monotonic()
    with _tracer.start_as_current_span(f"aho.dispatch.{family}", **span_kwargs) as span:
        span.set_attribute("aho.model", model_id)
        span.set_attribute("aho.family", family)
        span.set_attribute("dispatch.num_ctx", num_ctx)
        if family_config.get("num_predict") is not None:
            span.set_attribute("dispatch.num_predict", family_config["num_predict"])
        if stage is not None:
            span.set_attribute("aho.stage", stage)

        try:
            result = _run_dispatch()
        except DispatchError as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
            span.set_attribute(
                "dispatch.duration_ms",
                round((time.monotonic() - span_start) * 1000.0, 2),
            )
            raise

        span.set_attribute(
            "dispatch.duration_ms",
            float(result.get("wall_clock_seconds") or 0.0) * 1000.0,
        )
        if result.get("tokens_eval") is not None:
            span.set_attribute("dispatch.tokens_eval", result["tokens_eval"])
        if result.get("tokens_prompt") is not None:
            span.set_attribute("dispatch.tokens_prompt", result["tokens_prompt"])
        if result.get("error"):
            span.set_status(Status(StatusCode.ERROR, str(result["error"])[:200]))
        return result


def _error_result(model_id: str, family: str, error: str,
                  elapsed: float, retries_used: int) -> dict:
    """Build a standardized error result dict."""
    return {
        "response": "",
        "total_duration_ms": 0,
        "model": model_id,
        "error": error,
        "wall_clock_seconds": round(elapsed, 2),
        "family": family,
        "retries_used": retries_used,
    }


# ---------------------------------------------------------------------------
# Model management helpers (W1 findings: Nemotron auto-load, GLM OOM crash)
# ---------------------------------------------------------------------------

def unload_model(model_id: str, timeout: int = 10) -> bool:
    """Explicitly unload a model from Ollama VRAM via keep_alive=0.

    W1 R3: keep_alive:0 unloads within 5s grace period.
    W1 F004: Nemotron auto-loads — call before loading large models.
    W1 F007: GLM CUDA OOM crash kills ALL loaded models.

    Returns True if unload request succeeded, False on error.
    """
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "unload"}],
        "stream": False,
        "keep_alive": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def list_loaded_models(timeout: int = 5) -> list[dict]:
    """Query /api/ps for currently loaded models.

    Returns list of dicts with model name and VRAM info, or empty list on error.
    """
    req = urllib.request.Request(f"{OLLAMA_BASE}/api/ps")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            return body.get("models", [])
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []


def ensure_model_ready(model_id: str, evict_first: list[str] | None = None,
                       timeout: int = 30) -> bool:
    """Ensure a model is ready for inference, optionally evicting others first.

    Use before dispatching to a large model (GLM, Qwen) to avoid CUDA OOM.
    W1 F004: Nemotron auto-loads and contends for VRAM.
    W1 F006: GLM CUDA OOM crash kills ALL loaded models.

    Returns True if model responds to a minimal probe, False otherwise.
    """
    if evict_first:
        for m in evict_first:
            unload_model(m)
        time.sleep(2)  # grace period for unload (W1 R3: within 5s)

    # Minimal probe to trigger model load
    result = dispatch(
        model_id, "ok", timeout=timeout,
        max_retries=0, raise_on_error=False,
    )
    return result.get("error") is None


# Backward compatibility — old code references the module-level constant
STOP_TOKENS = MODEL_FAMILY_CONFIG["qwen"]["stop_tokens"]
