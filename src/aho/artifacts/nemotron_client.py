"""Nemotron-mini client for lightweight classification tasks.

Uses nemotron-mini:4b via Ollama.

0.2.13 W2: Parse fix — raise NemotronParseError on unparseable classification,
raise NemotronConnectionError on Ollama connection failure, instead of
silently returning categories[-1] (G083).
"""
import json
import requests
from opentelemetry import trace
from aho.logger import log_event

_tracer = trace.get_tracer("aho.nemotron_client")


class NemotronParseError(Exception):
    """Raised when Nemotron response cannot be matched to any known category."""

    def __init__(self, message: str, raw_response: str = ""):
        super().__init__(message)
        self.raw_response = raw_response


class NemotronConnectionError(Exception):
    """Raised when Ollama/Nemotron endpoint is unreachable or returns an HTTP error."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


def classify(text: str, categories: list[str], bias: str = None) -> str:
    """Classify text into one of the provided categories.

    Optional bias string (e.g. 'prefer UNIVERSAL') is added to the system prompt.
    """
    with _tracer.start_as_current_span("nemotron.classify") as span:
        span.set_attribute("model", "nemotron-mini:4b")
        span.set_attribute("input_length", len(text))
        span.set_attribute("category_count", len(categories))
        result = _classify_impl(text, categories, bias)
        span.set_attribute("result", result)
        span.set_attribute("status", "ok")
        return result


def _classify_impl(text: str, categories: list[str], bias: str = None) -> str:
    system_prompt = (
        "You are a precise classifier. Categorize the input text into EXACTLY ONE "
        f"of these categories: {', '.join(categories)}. "
        "Respond with ONLY the category name."
    )
    if bias:
        system_prompt += f" Bias: {bias}"

    prompt = f"Text to classify:\n{text}\n\nCategory:"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "nemotron-mini:4b",
                "prompt": f"{system_prompt}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 20,
                }
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json().get("response", "").strip().strip("'\"")
        
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="classify",
            input_summary=text,
            output_summary=result,
            status="success"
        )

        # Exact match check
        for cat in categories:
            if cat.lower() in result.lower():
                return cat
        raise NemotronParseError(
            f"Nemotron response '{result}' does not match any category: {categories}",
            raw_response=result,
        )
    except requests.ConnectionError as e:
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="classify",
            input_summary=text,
            status="error",
            error=str(e)
        )
        raise NemotronConnectionError(
            f"Cannot reach Ollama at localhost:11434: {e}",
            original_error=e,
        ) from e
    except requests.HTTPError as e:
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="classify",
            input_summary=text,
            status="error",
            error=str(e)
        )
        raise NemotronConnectionError(
            f"Ollama returned HTTP error: {e}",
            original_error=e,
        ) from e
    except requests.Timeout as e:
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="classify",
            input_summary=text,
            status="error",
            error=str(e)
        )
        raise NemotronConnectionError(
            f"Ollama request timed out: {e}",
            original_error=e,
        ) from e


def _call(prompt: str, system: str = None) -> str:
    """Internal raw call for evaluator/agents."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "nemotron-mini:4b",
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.0}
            },
            timeout=30
        )
        response.raise_for_status()
        res = response.json().get("response", "").strip()
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="raw_call",
            input_summary=prompt,
            output_summary=res,
            status="success"
        )
        return res
    except Exception as e:
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="raw_call",
            input_summary=prompt,
            status="error",
            error=str(e)
        )
        return f"Error: {e}"
