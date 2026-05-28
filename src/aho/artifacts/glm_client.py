"""GLM-4.6V-Flash-9B client for vision and reasoning.

Uses GLM-4.6V-Flash-9B via Ollama.
"""
import requests
from opentelemetry import trace
from aho.logger import log_event

_tracer = trace.get_tracer("aho.glm_client")


def generate(prompt: str, images: list[str] = None, num_ctx: int = None) -> str:
    """Generate text from prompt and optional base64 images.

    num_ctx: when None, base-tier hosts cap GLM at 4096 so the 65K modelfile
    default does not blow CPU memory + latency; partial/full-tier hosts keep
    the modelfile default. Pass an explicit int to override.
    """
    model = "haervwe/GLM-4.6V-Flash-9B:latest"
    if num_ctx is None:
        from aho.orchestrator_config import get_tier_glm_ctx_override
        num_ctx = get_tier_glm_ctx_override()
    with _tracer.start_as_current_span("glm.generate") as span:
        span.set_attribute("model", model)
        span.set_attribute("prompt_length", len(prompt))
        span.set_attribute("image_count", len(images) if images else 0)
        if num_ctx is not None:
            span.set_attribute("num_ctx", num_ctx)
        result = _generate_impl(prompt, images, model, num_ctx)
        span.set_attribute("status", "ok" if not result.startswith("Error:") else "error")
        return result


def _generate_impl(prompt: str, images: list[str] = None,
                   model: str = "haervwe/GLM-4.6V-Flash-9B:latest",
                   num_ctx: int = None) -> str:
    options = {"temperature": 0.2}
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
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
