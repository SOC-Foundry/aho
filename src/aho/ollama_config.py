#!/usr/bin/env python3
"""Ollama default configuration for all IAO scripts. Generalized from kjtcom."""

# Centralized Gemini Flash model string for all litellm calls.
GEMINI_MODEL = "gemini/gemini-2.5-flash"

# Centralized Qwen model for local artifact generation.
QWEN_MODEL = "qwen3.5:9b"

OLLAMA_DEFAULTS = {
    "stream": False,
    "think": False,
    "options": {
        "num_predict": 512,
    },
}

OLLAMA_EVAL_DEFAULTS = {
    "stream": False,
    "think": False,
    "options": {
        "num_predict": 2048,
    },
}

OLLAMA_BATCH_DEFAULTS = {
    "stream": False,
    "think": False,
    "options": {
        "num_predict": 2048,
    },
    "timeout": 2700,  # 45 minutes for batch ops
}


def _merge(defaults, payload):
    """Internal merge: defaults dict + caller payload, caller wins."""
    merged = dict(defaults)
    merged.update(payload)
    if "options" in defaults and "options" in payload:
        merged_opts = dict(defaults["options"])
        merged_opts.update(payload["options"])
        merged["options"] = merged_opts
    return merged


def merge_defaults(payload, evaluation=False):
    """Merge OLLAMA_DEFAULTS into a request payload. Caller values take priority."""
    defaults = OLLAMA_EVAL_DEFAULTS if evaluation else OLLAMA_DEFAULTS
    return _merge(defaults, payload)


def merge_batch_defaults(payload):
    """Merge OLLAMA_BATCH_DEFAULTS into a request payload. For long-running batch ops."""
    return _merge(OLLAMA_BATCH_DEFAULTS, payload)
