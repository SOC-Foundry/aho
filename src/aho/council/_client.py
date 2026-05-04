"""council._client — shared HTTP client helpers for council components.

Thin layer over Ollama's /api/chat. Council components share a single
client surface so timeout, base URL, and error taxonomy live in one place.
G083: malformed responses raise; we never substitute a degraded reply.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_S = 120.0


class CouncilTransportError(RuntimeError):
    """Network or HTTP-level failure reaching Ollama."""


class CouncilModelOutputMalformedError(RuntimeError):
    """Ollama responded but the payload doesn't match expected shape.

    Subclasses live in each component for caller-specific error taxonomy
    (e.g. CouncilTriageMalformedError). This base class is what _client
    raises before the per-component layer adds its own context.
    """


def ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def chat(
    model: str,
    messages: List[Dict[str, str]],
    *,
    options: Optional[Dict[str, Any]] = None,
    format_json: bool = False,
    timeout_s: Optional[float] = None,
) -> Dict[str, Any]:
    """Invoke /api/chat synchronously. Returns the parsed Ollama response.

    `format_json=True` sets Ollama's `format: "json"` constraint, which makes
    the model emit JSON-shaped output. Still validate the parse on the
    caller side — Ollama's json mode is best-effort, not contractual.
    """
    url = f"{ollama_base_url()}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if options:
        payload["options"] = options
    if format_json:
        payload["format"] = "json"

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            req, timeout=timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S
        ) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise CouncilTransportError(
            f"ollama chat POST {url} model={model} failed: {exc}"
        ) from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CouncilModelOutputMalformedError(
            f"ollama chat response not valid JSON envelope: {raw[:200]!r}"
        ) from exc
    return parsed


def extract_message_content(parsed: Dict[str, Any]) -> str:
    """Extract message.content from /api/chat response. Raises on missing."""
    message = parsed.get("message")
    if not isinstance(message, dict):
        raise CouncilModelOutputMalformedError(
            f"ollama chat response missing 'message' object: {parsed!r}"
        )
    content = message.get("content")
    if not isinstance(content, str):
        raise CouncilModelOutputMalformedError(
            f"ollama chat 'message.content' not a string: {type(content).__name__}"
        )
    return content


def parse_json_strict(raw: str) -> Any:
    """Parse JSON. Strips a leading ```json fence if present (some models add
    one despite format:'json'). Raises CouncilModelOutputMalformedError on
    parse failure. Never returns None as a fallback shape.
    """
    text = raw.strip()
    if text.startswith("```"):
        # Drop the first line ("```json" or "```") and the trailing fence.
        lines = text.split("\n")
        if len(lines) >= 2:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CouncilModelOutputMalformedError(
            f"model output not valid JSON: {raw[:200]!r}"
        ) from exc
