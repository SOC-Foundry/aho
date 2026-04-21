"""Cross-model cascade integration test runner — 0.2.15 W4.

Executes the 5-stage cascade with distinct models in distinct roles. This is
the Pillar 7 restoration attempt: Producer (Qwen) is not the same model as
Auditor (GLM). Baseline comparison: 0.2.14 W1.5 run-2 (Qwen-solo) = 14,725
total chars across 5 stages, 1867.34s wall clock.

Stage order is canonical (per src/aho/pipeline/orchestrator.py): indexer_in ->
producer -> auditor -> indexer_out -> assessor. The launch prompt's textual
"Producer -> Indexer-in" reading would require re-drafting system prompts and
would invalidate the baseline comparison; canonical order is preserved.

VRAM management: the 4-model roster totals 19.3GB on 8GB VRAM. Stages serialize.
Between stages we explicitly unload the previous model to avoid Ollama's
auto-load behaviour (W1 F004) and GLM's OOM-crash-kills-all (W1 F007).

Per-stage artifact schema (extended beyond 0.2.14 orchestrator):
  stage, stage_index, role, model, family, wall_clock_s, output_chars,
  tokens_eval, tokens_prompt, errors, template_leak_detected,
  thinking_field_present, thinking_chars, thinking_excerpt,
  raw_response, processed_output
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from aho.logger import log_event
from aho.pipeline.dispatcher import (
    DEFAULT_TIMEOUT,
    OLLAMA_BASE,
    MODEL_FAMILY_CONFIG,
    TEMPLATE_LEAK_TOKENS,
    _postprocess_response,
    _check_template_leak,
    _validate_num_ctx,
    get_family_config,
    list_loaded_models,
    resolve_family,
    unload_model,
)
from aho.pipeline.orchestrator import (
    STAGE_ORDER,
    STAGE_SYSTEM_PROMPTS,
    _build_stage_prompt,
)


ROLE_ASSIGNMENT = {
    "indexer_in":  "llama3.2:3b",
    "producer":    "qwen3.5:9b",
    "auditor":     "haervwe/GLM-4.6V-Flash-9B:latest",
    "indexer_out": "llama3.2:3b",
    "assessor":    "nemotron-mini:4b",
}

STAGE_TIMEOUT = 1800  # 30 min per stage; GLM at num_gpu=30 is ~36s base but prompt is long
DEFAULT_NUM_CTX = 32768


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dispatch_capture(model_id: str, prompt: str, system: str,
                      timeout: int, num_ctx: int) -> dict:
    """Single-attempt dispatch that captures raw body + thinking field.

    Mirrors dispatcher.dispatch() core logic but returns richer metadata.
    No retries — cascade stages are long-running and a failure is a failure.
    """
    num_ctx = _validate_num_ctx(num_ctx)
    family_config = get_family_config(model_id)
    family = resolve_family(model_id)

    messages = [{"role": "system", "content": system},
                {"role": "user", "content": prompt}]
    options = {
        "num_ctx": num_ctx,
        "stop": family_config["stop_tokens"],
    }
    if family_config.get("num_predict") is not None:
        options["num_predict"] = family_config["num_predict"]
    if family_config.get("num_gpu") is not None:
        options["num_gpu"] = family_config["num_gpu"]

    payload = {
        "model": model_id,
        "messages": messages,
        "stream": False,
        "options": options,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )

    start = time.monotonic()
    raw_body_text = ""
    error = None
    body = {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
        raw_body_text = raw_bytes.decode("utf-8", errors="replace")
        body = json.loads(raw_body_text)
    except urllib.error.HTTPError as e:
        error = f"http_{e.code}: {e.reason}"
    except urllib.error.URLError as e:
        error = f"connection_error: {e}"
    except TimeoutError:
        error = f"timeout after {timeout}s"
    except OSError as e:
        error = f"os_error: {e}"
    except (json.JSONDecodeError, ValueError) as e:
        error = f"json_decode: {e}"

    elapsed = time.monotonic() - start

    message = body.get("message") or {}
    raw_content = message.get("content", "")
    thinking = message.get("thinking", "")

    processed = _postprocess_response(raw_content, family_config)
    leak = _check_template_leak(processed)

    return {
        "family": family,
        "wall_clock_s": round(elapsed, 2),
        "raw_response": raw_content,
        "processed_output": processed,
        "output_chars": len(processed),
        "thinking_field_present": bool(thinking),
        "thinking_chars": len(thinking),
        "thinking_excerpt": thinking[:500] if thinking else "",
        "tokens_eval": body.get("eval_count"),
        "tokens_prompt": body.get("prompt_eval_count"),
        "total_duration_ms": body.get("total_duration", 0) / 1e6 if body.get("total_duration") else None,
        "template_leak_detected": leak,
        "errors": error,
        "raw_body_keys": list(body.keys()),
    }


def _vram_snapshot() -> list[dict]:
    models = list_loaded_models()
    return [
        {
            "model": m.get("model"),
            "size_vram_mib": (m.get("size_vram") or 0) // (1024 * 1024),
            "context_length": m.get("context_length"),
        }
        for m in models
    ]


def run() -> dict:
    output_dir = Path("artifacts/iterations/0.2.15/cascade")
    output_dir.mkdir(parents=True, exist_ok=True)

    doc_path = output_dir / "nosql-manual-text.txt"
    document_text = doc_path.read_text()

    run_id = f"w4-cross-model-{int(time.time())}"

    summary = {
        "run_id": run_id,
        "started_at": _now_iso(),
        "role_assignment": ROLE_ASSIGNMENT,
        "document_path": str(doc_path),
        "document_chars": len(document_text),
        "baseline_run_2_qwen_solo_chars": 14725,
        "baseline_run_2_wall_clock_s": 1867.34,
        "stages": [],
        "vram_snapshots": [],
    }

    summary["vram_snapshots"].append(
        {"label": "pre-run", "models": _vram_snapshot()}
    )

    prior_outputs: dict[str, str] = {}
    pipeline_start = time.monotonic()

    for idx, stage in enumerate(STAGE_ORDER, start=1):
        model_id = ROLE_ASSIGNMENT[stage]
        system = STAGE_SYSTEM_PROMPTS[stage]
        user_prompt = _build_stage_prompt(stage, document_text, prior_outputs)

        # VRAM hygiene: unload everything currently loaded, grace period.
        # Handles W1 F004 (Nemotron auto-load) and W1 F007 (GLM OOM kills all).
        currently_loaded = list_loaded_models()
        for m in currently_loaded:
            mid = m.get("model")
            if mid and mid != model_id:
                unload_model(mid)
        if currently_loaded:
            time.sleep(3)

        log_event(
            event_type="pipeline_handoff",
            source_agent="w4-cross-model-cascade",
            target=stage,
            action="dispatch",
            input_summary=(
                f"run={run_id} stage={idx}:{stage} model={model_id} "
                f"prompt_chars={len(user_prompt)}"
            ),
            workstream_id="W4",
        )

        stage_started = _now_iso()
        result = _dispatch_capture(model_id, user_prompt, system,
                                   timeout=STAGE_TIMEOUT, num_ctx=DEFAULT_NUM_CTX)
        stage_ended = _now_iso()

        result.update({
            "stage": stage,
            "stage_index": idx,
            "role": stage,
            "model": model_id,
            "started_at": stage_started,
            "completed_at": stage_ended,
        })

        # Cascade handoff: pass processed output (or error marker) to next stage
        if result["errors"] or not result["processed_output"]:
            prior_outputs[stage] = f"[stage {stage} failed: {result['errors']}]"
        else:
            prior_outputs[stage] = result["processed_output"]

        # Per-stage artifact
        stage_file = output_dir / f"stage-{idx}-{stage}.json"
        stage_file.write_text(json.dumps(result, indent=2) + "\n")

        summary["stages"].append({
            "stage_index": idx,
            "role": stage,
            "model": model_id,
            "family": result["family"],
            "wall_clock_s": result["wall_clock_s"],
            "output_chars": result["output_chars"],
            "tokens_eval": result["tokens_eval"],
            "tokens_prompt": result["tokens_prompt"],
            "errors": result["errors"],
            "template_leak_detected": result["template_leak_detected"],
            "thinking_field_present": result["thinking_field_present"],
            "thinking_chars": result["thinking_chars"],
        })
        summary["vram_snapshots"].append(
            {"label": f"post-{stage}", "models": _vram_snapshot()}
        )

        log_event(
            event_type="pipeline_handoff",
            source_agent="w4-cross-model-cascade",
            target=stage,
            action="complete",
            output_summary=(
                f"run={run_id} stage={idx}:{stage} chars={result['output_chars']} "
                f"elapsed={result['wall_clock_s']}s err={result['errors']}"
            ),
            workstream_id="W4",
        )

        print(
            f"[{stage_ended}] stage {idx}:{stage} model={model_id} "
            f"wall={result['wall_clock_s']}s chars={result['output_chars']} "
            f"err={result['errors']}",
            flush=True,
        )

    pipeline_elapsed = time.monotonic() - pipeline_start
    summary["total_wall_clock_s"] = round(pipeline_elapsed, 2)
    summary["completed_at"] = _now_iso()
    summary["total_output_chars"] = sum(s["output_chars"] for s in summary["stages"])
    summary["errors_encountered"] = [s for s in summary["stages"] if s["errors"]]
    summary["template_leaks_detected"] = [
        s for s in summary["stages"] if s["template_leak_detected"]
    ]

    trace_file = output_dir / "trace.json"
    trace_file.write_text(json.dumps(summary, indent=2) + "\n")

    print("\n=== cascade complete ===")
    print(f"total wall clock: {summary['total_wall_clock_s']}s")
    print(f"total output chars: {summary['total_output_chars']} (baseline Qwen-solo: 14725)")
    print(f"errors: {len(summary['errors_encountered'])}")
    print(f"template leaks: {len(summary['template_leaks_detected'])}")

    return summary


if __name__ == "__main__":
    run()
