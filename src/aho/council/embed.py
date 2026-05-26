"""council.embed - real implementation (W2).

Calls nomic-embed-text via host Ollama. Returns a 768-dim float vector.
Raises CouncilEmbedInputError on malformed input. Emits one OTEL span per
call carrying model_id, tier, latency_ms, input_token_count, output_dim.
No `stub: true` attribute - that was a W1 marker.

Wire-up:
- OLLAMA_BASE_URL env override; default http://localhost:11434 (host) /
  http://host.containers.internal:11434 (container - set there via env).
- AHO_COUNCIL_EMBED_MODEL env override; default nomic-embed-text.
- AHO_COUNCIL_EMBED_TIMEOUT_S env override; default 120 (raised from 30
  in 0.2.18 W0 per F-0.2.17-W6-002 - 30s was too tight under cold-start
  + concurrent embed load on NZXTcos 8GB VRAM substrate).

G083 discipline: malformed model output (missing 'embeddings' / wrong dim)
raises CouncilEmbedMalformedError rather than returning a zero vector or
synthesising a degraded response.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("aho.council.embed")
except ImportError:  # pragma: no cover - opentelemetry is a hard dep
    _otel_trace = None
    _tracer = None

EMBED_DIM = 768
DEFAULT_MODEL = "nomic-embed-text"
DEFAULT_TIMEOUT_S = 120
DEFAULT_BASE_URL = "http://localhost:11434"


class CouncilEmbedInputError(ValueError):
    """Caller passed something that is not a non-empty string."""


class CouncilEmbedMalformedError(RuntimeError):
    """Ollama returned a payload that doesn't match the expected shape.

    Raised, never swallowed. G083 discipline applies - the embed primitive
    refuses to substitute a degraded vector.
    """


class CouncilEmbedTransportError(RuntimeError):
    """Network or HTTP-level failure reaching Ollama."""


def _ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _model() -> str:
    return os.environ.get("AHO_COUNCIL_EMBED_MODEL", DEFAULT_MODEL)


def _timeout_s() -> float:
    raw = os.environ.get("AHO_COUNCIL_EMBED_TIMEOUT_S")
    if raw is None:
        return float(DEFAULT_TIMEOUT_S)
    try:
        return float(raw)
    except ValueError as exc:
        raise CouncilEmbedInputError(
            f"AHO_COUNCIL_EMBED_TIMEOUT_S={raw!r} not parseable as float"
        ) from exc


def _tier() -> str:
    return os.environ.get("AHO_TIER", "base")


def _validate_input(text: Any) -> str:
    if not isinstance(text, str):
        raise CouncilEmbedInputError(
            f"text must be str, got {type(text).__name__}"
        )
    if not text.strip():
        raise CouncilEmbedInputError("text must be non-empty")
    return text


def _post_embed(text: str) -> Dict[str, Any]:
    url = f"{_ollama_base_url()}/api/embed"
    payload = json.dumps({"model": _model(), "input": [text]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_timeout_s()) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise CouncilEmbedTransportError(
            f"ollama embed POST {url} failed: {exc}"
        ) from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise CouncilEmbedMalformedError(
            f"ollama embed response not valid JSON: {body[:200]!r}"
        ) from exc


def _extract_vector(parsed: Dict[str, Any]) -> List[float]:
    embeddings = parsed.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        raise CouncilEmbedMalformedError(
            f"ollama embed response missing 'embeddings' list: {parsed!r}"
        )
    vector = embeddings[0]
    if not isinstance(vector, list):
        raise CouncilEmbedMalformedError(
            f"ollama embed first row not a list: {type(vector).__name__}"
        )
    if len(vector) != EMBED_DIM:
        raise CouncilEmbedMalformedError(
            f"ollama embed vector dim {len(vector)} != expected {EMBED_DIM}"
        )
    out: List[float] = []
    for v in vector:
        if not isinstance(v, (int, float)):
            raise CouncilEmbedMalformedError(
                f"ollama embed vector contains non-numeric value: {v!r}"
            )
        out.append(float(v))
    return out


def _emit_span(
    *,
    text_length: int,
    latency_ms: int,
    output_dim: int,
    input_token_count: Optional[int],
    error: Optional[str] = None,
) -> None:
    if _tracer is None:
        return
    with _tracer.start_as_current_span("aho.council.embed") as span:
        try:
            span.set_attribute("aho.council.role", "retrieval")
            span.set_attribute("aho.council.work_shape", "embed")
            span.set_attribute("aho.tier", _tier())
            span.set_attribute("aho.model", _model())
            span.set_attribute("aho.council.text_length", text_length)
            span.set_attribute("aho.council.output_dim", output_dim)
            span.set_attribute("aho.council.latency_ms", latency_ms)
            if input_token_count is not None:
                span.set_attribute("aho.council.input_token_count", input_token_count)
            if error is not None:
                span.set_attribute("aho.council.error", error)
        except Exception:
            pass


def embed(text: Any) -> Dict[str, Any]:
    """Embed `text` via nomic-embed-text. Returns dict with 'vector', 'dim',
    'model', 'latency_ms'. Raises on malformed input or malformed response.
    """
    validated = _validate_input(text)
    start = time.monotonic()
    try:
        parsed = _post_embed(validated)
        vector = _extract_vector(parsed)
    except (CouncilEmbedTransportError, CouncilEmbedMalformedError) as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        _emit_span(
            text_length=len(validated),
            latency_ms=latency_ms,
            output_dim=0,
            input_token_count=None,
            error=type(exc).__name__,
        )
        raise
    latency_ms = int((time.monotonic() - start) * 1000)
    input_token_count = parsed.get("prompt_eval_count")
    if not isinstance(input_token_count, int):
        input_token_count = None
    _emit_span(
        text_length=len(validated),
        latency_ms=latency_ms,
        output_dim=len(vector),
        input_token_count=input_token_count,
    )
    return {
        "vector": vector,
        "dim": len(vector),
        "model": _model(),
        "latency_ms": latency_ms,
    }
