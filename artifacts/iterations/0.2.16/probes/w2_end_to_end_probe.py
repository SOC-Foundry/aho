"""0.2.16 W2 end-to-end TRACEPARENT probe.

Runs as a bash subprocess from the Claude Code session so it inherits
TRACEPARENT. Exercises dispatcher + router to emit `aho.dispatch.qwen` and
`aho.route.classify` spans off the parent trace.

Uses the already-loaded qwen3.5:9b (no model swap), tiny prompts, num_ctx=2048
to keep wall-clock and VRAM pressure minimal.
"""
import os
import sys
import time

from aho.pipeline import dispatcher, router
from aho import logger  # forces TracerProvider init with OTLP exporter


def main() -> int:
    traceparent = os.environ.get("TRACEPARENT", "<unset>")
    print(f"TRACEPARENT={traceparent}", flush=True)

    t0 = time.monotonic()
    disp = dispatcher.dispatch(
        "qwen3.5:9b",
        "Reply with exactly the word: OK",
        system="You answer in one word.",
        num_ctx=2048,
        max_retries=0,
        stage="w2-probe-producer",
    )
    t_disp = time.monotonic() - t0
    print(f"dispatch.result.error={disp.get('error')}", flush=True)
    print(f"dispatch.result.wall_clock_seconds={disp.get('wall_clock_seconds')}", flush=True)
    print(f"dispatch.result.tokens_eval={disp.get('tokens_eval')}", flush=True)
    print(f"dispatch.internal_timing_ms={t_disp * 1000:.2f}", flush=True)

    # Evict qwen before loading nemotron — 8GB VRAM won't hold both.
    # Nemotron is the canonical classifier (CLAUDE.md, 0.2.15 retrospective);
    # qwen-as-classifier blows the budget on thinking-mode.
    dispatcher.unload_model("qwen3.5:9b")
    time.sleep(2)

    t1 = time.monotonic()
    category = router.classify_task(
        "Write a Python function that computes fibonacci numbers.",
        ["code", "prose", "other"],
        model="nemotron-mini:4b",
        num_ctx=2048,
        timeout=120,
    )
    t_classify = time.monotonic() - t1
    print(f"classify.category={category}", flush=True)
    print(f"classify.internal_timing_ms={t_classify * 1000:.2f}", flush=True)

    # Force span flush before exit so BatchSpanProcessor drains over OTLP.
    from opentelemetry import trace
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush(timeout_millis=5000)
    if hasattr(provider, "shutdown"):
        provider.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
