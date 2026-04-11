"""Nemotron-mini client for lightweight classification tasks.

Uses nemotron-mini:4b via Ollama.
"""
import json
import requests
from aho.logger import log_event


def classify(text: str, categories: list[str], bias: str = None) -> str:
    """Classify text into one of the provided categories.

    Optional bias string (e.g. 'prefer UNIVERSAL') is added to the system prompt.
    """
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
        return categories[-1] # Fallback to last category (often AMBIGUOUS or similar)
    except Exception as e:
        log_event(
            event_type="llm_call",
            source_agent="nemotron-client",
            target="nemotron-mini:4b",
            action="classify",
            input_summary=text,
            status="error",
            error=str(e)
        )
        return categories[-1]


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
