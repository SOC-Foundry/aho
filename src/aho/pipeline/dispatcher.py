"""Pipeline dispatcher — thin wrapper around Ollama HTTP API (0.2.14 W1.5).

Direct Ollama dispatch for cascade pipeline via /api/chat endpoint.
Uses proper message structure to avoid chat-template token leakage.
Sets num_ctx for adequate context and stop tokens for clean termination.

W1.5 repair: switched from /api/generate to /api/chat to fix template
leakage (auditor double-output, indexer truncation, producer persona
drift). See audit/W1.json dispatcher_bugs findings.

Future: swap to Nemoclaw once model_id routing is added (0.2.15).
See dispatch-decision.md.
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional

OLLAMA_BASE = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 3600  # 60 minutes per stage cap

# 32K chosen for initial repair baseline, not native 256K, because:
# (a) VRAM considerations at Q4_K_M on 2080 SUPER may OOM at full 256K
# (b) Qwen's effective-useful-context may be smaller than advertised
# If 32K causes OOM or instability, fall back to 16K and document.
DEFAULT_NUM_CTX = 32768

# Qwen 3.5 chat template stop tokens. Without these, /api/generate
# produced multi-turn hallucinated conversations in a single response.
STOP_TOKENS = ["<|endoftext|>", "<|im_end|>"]


def dispatch(model_id: str, prompt: str, system: Optional[str] = None,
             timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Send a prompt to an Ollama model via /api/chat and return the response.

    Uses the chat API with proper message structure to ensure the model's
    chat template is applied server-side (preventing token leakage).

    Returns dict with keys: response, total_duration_ms, model, error (if any).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_id,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": DEFAULT_NUM_CTX,
            "stop": STOP_TOKENS,
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            elapsed = time.monotonic() - start
            # /api/chat returns response in body.message.content
            message = body.get("message", {})
            return {
                "response": message.get("content", ""),
                "total_duration_ms": body.get("total_duration", 0) / 1e6,
                "model": body.get("model", model_id),
                "error": None,
                "wall_clock_seconds": round(elapsed, 2),
            }
    except urllib.error.URLError as e:
        elapsed = time.monotonic() - start
        return {
            "response": "",
            "total_duration_ms": 0,
            "model": model_id,
            "error": f"connection_error: {e}",
            "wall_clock_seconds": round(elapsed, 2),
        }
    except TimeoutError:
        elapsed = time.monotonic() - start
        return {
            "response": "",
            "total_duration_ms": 0,
            "model": model_id,
            "error": f"timeout after {timeout}s",
            "wall_clock_seconds": round(elapsed, 2),
        }
