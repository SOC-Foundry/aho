"""Qwen Producer probe with num_predict=8000 — 0.2.16 W0 substrate fix.

Reproduces the 0.2.15 W4 Producer scenario exactly: same 247K-char NoSQL
manual, same system prompt, same model, same num_ctx=32768. Only change:
dispatcher.MODEL_FAMILY_CONFIG["qwen"]["num_predict"] is now 8000 (was 2000).

Hard gate: content_chars >= 500 AND done_reason != "length". If either
condition fails, halt and surface — do not move to next contingency lever
without Kyle input.
"""
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# Put repo src on path so we can import dispatcher helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from aho.pipeline.dispatcher import (
    OLLAMA_BASE, MODEL_FAMILY_CONFIG, get_family_config, resolve_family,
    _validate_num_ctx, _postprocess_response, _check_template_leak,
)
from aho.pipeline.orchestrator import STAGE_SYSTEM_PROMPTS


PROBE_OUT = Path(__file__).resolve().parent.parent / "qwen-num-predict-probe.json"
DOC_PATH = (Path(__file__).resolve().parents[2] / "0.2.15" / "cascade"
            / "nosql-manual-text.txt")

MODEL_ID = "qwen3.5:9b"
NUM_CTX = 32768
TIMEOUT = 1800  # 30 min hard cap


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    family_config = get_family_config(MODEL_ID)
    family = resolve_family(MODEL_ID)

    document_text = DOC_PATH.read_text()

    # Producer stage per orchestrator.STAGE_SYSTEM_PROMPTS["producer"]; user
    # prompt mirrors the cascade's producer input (doc + empty indexer_in
    # since this is a stand-alone probe, not a cascade).
    system = STAGE_SYSTEM_PROMPTS["producer"]
    user_prompt = f"## Input Document\n\n{document_text}"

    options = {
        "num_ctx": _validate_num_ctx(NUM_CTX),
        "stop": family_config["stop_tokens"],
    }
    if family_config.get("num_predict") is not None:
        options["num_predict"] = family_config["num_predict"]
    if family_config.get("num_gpu") is not None:
        options["num_gpu"] = family_config["num_gpu"]

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": options,
    }

    started_at = _now_iso()
    wall_start = time.monotonic()
    raw_body_text = ""
    body = {}
    error = None

    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw_body_text = resp.read().decode("utf-8", errors="replace")
        body = json.loads(raw_body_text)
    except urllib.error.HTTPError as e:
        error = f"http_{e.code}: {e.reason}"
    except urllib.error.URLError as e:
        error = f"connection_error: {e}"
    except TimeoutError:
        error = f"timeout after {TIMEOUT}s"
    except OSError as e:
        error = f"os_error: {e}"
    except (json.JSONDecodeError, ValueError) as e:
        error = f"json_decode: {e}"

    wall_elapsed = round(time.monotonic() - wall_start, 2)
    completed_at = _now_iso()

    message = body.get("message") or {}
    raw_content = message.get("content", "")
    thinking = message.get("thinking", "")
    processed = _postprocess_response(raw_content, family_config)
    leak = _check_template_leak(processed)

    # Hard-gate determination
    content_chars = len(processed)
    done_reason = body.get("done_reason")
    gate_content_min = content_chars >= 500
    gate_not_length = done_reason is not None and done_reason != "length"
    gate_passed = bool(gate_content_min and gate_not_length and error is None)

    result = {
        "probe_id": "0.2.16-W0-qwen-num-predict-8000",
        "started_at": started_at,
        "completed_at": completed_at,
        "wall_clock_s": wall_elapsed,
        "model": MODEL_ID,
        "family": family,
        "num_ctx": NUM_CTX,
        "num_predict": options.get("num_predict"),
        "document_path": str(DOC_PATH),
        "document_chars": len(document_text),
        "error": error,
        "raw_response_content": raw_content,
        "processed_output": processed,
        "content_chars": content_chars,
        "thinking_field_present": bool(thinking),
        "thinking_chars": len(thinking),
        "thinking_excerpt": thinking[:500] if thinking else "",
        "tokens_eval": body.get("eval_count"),
        "tokens_prompt": body.get("prompt_eval_count"),
        "total_duration_ms": (
            body.get("total_duration", 0) / 1e6
            if body.get("total_duration") else None
        ),
        "done_reason": done_reason,
        "template_leak_detected": bool(leak),
        "template_leak_token": leak if isinstance(leak, str) else None,
        "raw_body_keys": list(body.keys()),
        "hard_gate": {
            "content_chars_ge_500": gate_content_min,
            "done_reason_not_length": gate_not_length,
            "no_error": error is None,
            "passed": gate_passed,
        },
        "baseline_reference": {
            "iteration": "0.2.15 W4",
            "content_chars": 0,
            "thinking_chars": 8026,
            "done_reason": "length",
            "eval_count": 2000,
            "wall_clock_s": 151.7,
        },
    }

    PROBE_OUT.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(f"probe complete: wall={wall_elapsed}s content_chars={content_chars} "
          f"thinking_chars={result['thinking_chars']} "
          f"done_reason={done_reason} gate_passed={gate_passed}")
    print(f"written: {PROBE_OUT}")
    return 0 if gate_passed else 1


if __name__ == "__main__":
    sys.exit(main())
