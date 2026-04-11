"""GLM-4.6V-Flash-9B client for vision and reasoning.

Uses GLM-4.6V-Flash-9B via Ollama.
"""
import requests
from aho.logger import log_event


def generate(prompt: str, images: list[str] = None) -> str:
    """Generate text from prompt and optional base64 images."""
    model = "haervwe/GLM-4.6V-Flash-9B:latest"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
        }
    }
    if images:
        payload["images"] = images

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        res = response.json().get("response", "").strip()
        log_event(
            event_type="llm_call",
            source_agent="glm-client",
            target=model,
            action="generate",
            input_summary=prompt,
            output_summary=res,
            status="success"
        )
        return res
    except Exception as e:
        log_event(
            event_type="llm_call",
            source_agent="glm-client",
            target=model,
            action="generate",
            input_summary=prompt,
            status="error",
            error=str(e)
        )
        return f"Error: {e}"
