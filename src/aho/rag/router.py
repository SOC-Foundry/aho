#!/usr/bin/env python3
"""LLM intent router for dual retrieval path. Generalized from kjtcom."""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

from aho.paths import find_project_root
from aho.logger import log_event
# Note: ollama_config should be migrated to aho top-level
try:
    from aho.ollama_config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = os.environ.get("IAO_ROUTING_MODEL", "haervwe/GLM-4.6V-Flash-9B")

# Configuration
try:
    PROJECT_ROOT = find_project_root()
    PROJECT_NAME = os.environ.get("AHO_PROJECT_NAME", os.environ.get("IAO_PROJECT_NAME", PROJECT_ROOT.name)
except Exception:
    PROJECT_ROOT = Path.cwd()
    PROJECT_NAME = "unknown"

_SCHEMA_REF = None
_SCHEMA_PATH = PROJECT_ROOT / "data" / "schema_reference.json"

def _load_schema():
    global _SCHEMA_REF
    if _SCHEMA_REF is None:
        if _SCHEMA_PATH.exists():
            with open(_SCHEMA_PATH) as f:
                _SCHEMA_REF = json.load(f)
        else:
            _SCHEMA_REF = {"entity_count": 0, "pipelines": []}
    return _SCHEMA_REF


def build_routing_prompt(question: str) -> str:
    """Build the routing prompt with schema context."""
    schema = _load_schema()
    schema_str = json.dumps(schema, separators=(',', ':'))

    return f"""You are a query router for the {PROJECT_NAME} database.

Given a user question, return ONLY a JSON object with one of these structures:

For entity/data questions (items, records, or structured data in the database):
{{"route": "firestore", "filters": {{"field": "value"}}, "intent": "count|list|detail"}}

For development/project history questions ({PROJECT_NAME} iterations, gotchas, builds, agents):
{{"route": "chromadb", "query": "search terms"}}

For external/internet questions (companies, news, general knowledge, things NOT in the database):
{{"route": "web", "query": "search terms"}}

SCHEMA REFERENCE:
{schema_str}

Rules:
- If unsure whether entity or dev question, default to firestore
- Return ONLY valid JSON, no markdown, no explanation

USER QUESTION: {question}"""


def route_question(question: str) -> Dict[str, Any]:
    """Route a question via LLM. Returns parsed routing dict."""
    from litellm import completion

    prompt = build_routing_prompt(question)
    start = time.time()
    agent = os.environ.get("AHO_AGENT", os.environ.get("IAO_AGENT", "aho-cli"))

    try:
        response = completion(
            model=GEMINI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=1024,
        )
        content = response.choices[0].message.content.strip()
        latency = int((time.time() - start) * 1000)

        # Token usage from response
        usage = getattr(response, 'usage', None)
        tokens = {
            "prompt": getattr(usage, 'prompt_tokens', 0) if usage else 0,
            "eval": getattr(usage, 'completion_tokens', 0) if usage else 0,
            "total": getattr(usage, 'total_tokens', 0) if usage else 0,
        }

        log_event("llm_call", agent, GEMINI_MODEL, "route",
                  input_summary=f"route: {question}"[:200],
                  output_summary=content[:200],
                  tokens=tokens, latency_ms=latency, status="success")

        # Parse JSON - strip markdown fences if present
        cleaned = content
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        # Validate structure
        if "route" not in parsed:
            raise ValueError("Missing 'route' key")
        if parsed["route"] not in ("firestore", "chromadb", "web"):
            raise ValueError(f"Unknown route: {parsed['route']}")
        if parsed["route"] == "firestore" and "filters" not in parsed:
            parsed["filters"] = {}
        if parsed["route"] == "firestore" and "intent" not in parsed:
            parsed["intent"] = "list"
        if parsed["route"] == "web" and "query" not in parsed:
            parsed["query"] = question

        return parsed

    except Exception as e:
        latency = int((time.time() - start) * 1000)
        log_event("llm_call", agent, GEMINI_MODEL, "route",
                  input_summary=f"route: {question}"[:200],
                  status="error", error=str(e), latency_ms=latency)
        # Fallback to ChromaDB
        return {"route": "chromadb", "query": question}


if __name__ == '__main__':
    q = sys.argv[1] if len(sys.argv) > 1 else "tell me about the last iteration"
    result = route_question(q)
    print(json.dumps(result, indent=2))
