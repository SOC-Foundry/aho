# 0.2.16 W2 — Trace Integration Notes

Design decisions, observed behavior, and posture notes captured during W2
implementation of W3C `TRACEPARENT` propagation across
`aho.pipeline.dispatcher` and `aho.pipeline.router`.

## Span Parent Resolution

`_resolve_span_parent_context()` (present in both dispatcher and router)
resolves the parent context with this precedence:

1. If a span is already active in the Python OTEL context, return `None` —
   `start_as_current_span` uses the active context as parent. This makes
   `dispatch()` nest correctly under `aho.route.classify` when invoked from
   inside `classify_task`.
2. Otherwise, read the `TRACEPARENT` env var. Present → extract via
   `TraceContextTextMapPropagator`, return the extracted context. Absent
   or malformed → return `None`, span becomes root.

This was tightened after the first probe run produced `aho.dispatch` and
`aho.route.classify` spans as *siblings* under the Claude Code
`tool.execution` span (both re-parenting to env TRACEPARENT, ignoring the
active Python context). The fix preserves the "root span for non-OTEL
callers" backward-compat guarantee while giving correct in-process nesting
when the stack includes multiple aho entries.

## Duration Attribute Source

`dispatch.duration_ms` is populated from `result["wall_clock_seconds"] *
1000` on success paths, and from `(time.monotonic() - span_start) * 1000`
on typed-error paths. Using the result dict's wall-clock on the happy path
guarantees the span attribute matches the same timing that flows into the
event log and stage artifacts — no drift between two measurement sites.
Probe confirmed: `dispatch.internal_timing_ms=7430.11` → span attr
`dispatch.duration_ms=7430`.

## Dispatcher Return Shape

Extended additively with `tokens_eval` and `tokens_prompt` keys (sourced
from Ollama's `eval_count` and `prompt_eval_count` on `/api/chat` success
responses). Needed to populate `dispatch.tokens_eval` and
`dispatch.tokens_prompt` span attrs without re-parsing the Ollama body.
No existing caller reads either key; the contract change is purely
additive.

## Input Excerpt Truncation (Router)

`router.INPUT_EXCERPT_MAX_CHARS = 200`. `aho.input_excerpt` span attr is
`task[:INPUT_EXCERPT_MAX_CHARS]`. Trace payloads stay lean — the excerpt is
a debug breadcrumb, not a full record of classifier input.

## Truncation — `OTEL_LOG_TOOL_CONTENT=1` Posture

The published behavior is: `OTEL_LOG_TOOL_CONTENT=1` enables tool
call/result content logging; content above ~60KB is truncated. Observation
from this session's `~/.local/share/aho/logs/logs.jsonl`:

| Event type                    | Count | Biggest record |
|-------------------------------|------:|---------------:|
| `claude_code.api_request`     |   530 |         1730 B |
| `claude_code.api_request_body`|   523 |         1356 B |
| `claude_code.api_response_body`|  521 |         1430 B |
| `claude_code.tool_decision`   |   491 |         1244 B |
| `claude_code.tool_result`     |   491 |         6162 B |
| `claude_code.user_prompt`     |    32 |        12004 B |

Even when `tool_result_size_bytes` reports 259568 B (~253KB, observed on
an mcp_tool call), the corresponding OTEL log record in `logs.jsonl` stays
at 1766 bytes. The full content is not inlined in the OTLP log stream; it
flows to `~/.local/share/aho/api-bodies/` via
`OTEL_LOG_RAW_API_BODIES=file:...`, which is the configured sink in this
harness.

Consequence: in this pipeline the 60KB cut never materializes visibly in
logs.jsonl, because content is routed to a file sink rather than inlined
in OTLP logs. For the Mercor export pack, customers running without
`OTEL_LOG_RAW_API_BODIES` should expect inlined content up to 60KB and
truncation markers beyond that; customers using the file sink will see
`tool_result_size_bytes` metadata only in OTLP logs and full content in
the sink directory.

This is a posture observation, not a failure. No test asserts the
truncation point — the pipeline configuration determines where the cut
materializes.

## Backward Compatibility

Existing dispatcher tests (`test_dispatcher_hardening.py`,
`test_dispatcher_chat_api.py`, `test_dispatcher_template_leak.py`) and
router tests (`test_pipeline_router.py`) — **83/83 pass unchanged** with
no `TRACEPARENT` present. The `_tracer is None` fallback path is exercised
whenever the OTEL SDK can't import or the tracer provider was never set.

## Gemini CLI Asymmetry

See `artifacts/adrs/0005-gemini-otel-asymmetry.md` (next sequential aho-
internal ADR number at W2 execution time, per `command ls artifacts/adrs/`). Gemini CLI has no
first-class OTEL support; harness-watcher event wrappers capture
wall-clock only. Audit cost attribution remains drafter-only in the
Pillar 8 dashboard. No timing-wrapper half-measures — partial
observability that looks like coverage it isn't is worse than clear
documented asymmetry.
