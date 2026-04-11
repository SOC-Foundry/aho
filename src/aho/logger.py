#!/usr/bin/env python3
"""Structured event logger for AHO P3 Diligence.

Logs all agent communications (LLM calls, MCP calls, API calls, commands)
to data/aho_event_log.jsonl in append-only JSONL format.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from aho.paths import find_project_root, get_iterations_dir, get_data_dir

# OTEL dual emitter — always-on by default (0.2.1). Opt-out via AHO_OTEL_DISABLED=1.
# JSONL stays authoritative. OTEL is additive.
_otel_tracer = None
_otel_disabled = os.environ.get("AHO_OTEL_DISABLED") == "1"

if not _otel_disabled:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        provider = TracerProvider()
        exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:4317", insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _otel_tracer = trace.get_tracer("aho", "0.2.1")
    except Exception as _otel_err:
        # Silently fall back — collector may not be running
        _otel_tracer = None

try:
    root = find_project_root()
    LOG_PATH = str(get_data_dir() / "aho_event_log.jsonl")
except Exception:
    # Fallback to local data dir if project root not found
    LOG_PATH = "data/aho_event_log.jsonl"

class AhoLoggerMisconfigured(RuntimeError):
    """Raised when iteration cannot be resolved from env or .aho.json."""
    pass


def _resolve_iteration():
    """Resolve current iteration with strict precedence (G102 fix, 10.68.1 W0):
    1. AHO_ITERATION or IAO_ITERATION env var (primary)
    2. .aho.json current_iteration field (fallback)
    3. Raise AhoLoggerMisconfigured (no silent default)
    """
    from aho.config import validate_iteration_version
    env_val = os.environ.get("AHO_ITERATION", os.environ.get("IAO_ITERATION"))
    if env_val:
        try:
            validate_iteration_version(env_val)
        except ValueError:
            pass # Logger might be initialized with invalid env var but we should try fallback
        return env_val
    try:
        import pathlib
        try:
            from aho.paths import find_project_root as _frp
            aho_json = _frp() / ".aho.json"
        except Exception:
            aho_json = pathlib.Path(".aho.json")
        if aho_json.exists():
            data = json.loads(aho_json.read_text())
            ci = data.get("current_iteration")
            if ci:
                validate_iteration_version(ci)
                return ci
    except Exception:
        pass
    raise AhoLoggerMisconfigured(
        "AHO_ITERATION env var not set and .aho.json has no current_iteration"
    )


try:
    _ITERATION = _resolve_iteration()
except Exception as _e:
    print(f"[aho_logger] ERROR: {_e}", file=sys.stderr)
    _ITERATION = "MISSING_ENV_VAR"


def set_attrs_from_dict(span, prefix, value):
    """Flatten a dict (or scalar) into OTEL span attributes.

    OTEL attributes must be scalar (str, int, float, bool) or sequences of
    scalars. Dicts cause 'Invalid type dict' errors. This helper flattens
    nested dicts into dotted-key scalars. aho-G064.
    """
    if isinstance(value, dict):
        for k, v in value.items():
            set_attrs_from_dict(span, f"{prefix}.{k}", v)
    elif isinstance(value, (list, tuple)):
        # OTEL accepts sequences of homogeneous scalars
        safe = [str(item) if not isinstance(item, (str, int, float, bool)) else item for item in value]
        span.set_attribute(prefix, safe)
    elif isinstance(value, (str, int, float, bool)):
        span.set_attribute(prefix, value)
    else:
        span.set_attribute(prefix, str(value))


def emit_heartbeat(component_name, dashboard_port=None, interval=30):
    """Emit heartbeat spans at regular intervals. Runs in a daemon thread.

    Call once at daemon startup in --serve mode. Thread exits when main exits.
    """
    import time
    import threading

    if dashboard_port is None:
        try:
            from aho.config import get_dashboard_port
            dashboard_port = get_dashboard_port()
        except Exception:
            dashboard_port = 7800

    def _loop():
        start = time.time()
        while True:
            try:
                uptime = int(time.time() - start)
                log_event(
                    "heartbeat",
                    source_agent=component_name,
                    target="self",
                    action="heartbeat",
                    output_summary=f"uptime={uptime}s port={dashboard_port}",
                )
            except Exception:
                pass
            time.sleep(interval)

    t = threading.Thread(target=_loop, daemon=True, name=f"heartbeat-{component_name}")
    t.start()
    return t


def log_workstream_complete(workstream_id, status, summary):
    """ADR-022: Append a structured workstream completion entry to the build log. (10.69 W3)"""
    from datetime import datetime
    import json
    
    try:
        root = find_project_root()
        aho_json = root / ".aho.json"
        
        prefix = "aho"
        if aho_json.exists():
            config = json.loads(aho_json.read_text())
            prefix = config.get("artifact_prefix") or config.get("name") or config.get("project_code") or "aho"
        
        # aho 0.1.13: build logs live in artifacts/iterations/<version>/
        iter_dir = get_iterations_dir() / _ITERATION
        build_log_path = iter_dir / f"{prefix}-build-log-{_ITERATION}.md"
        
        if not build_log_path.exists():
            # Fallback to simple name
            alt_path = iter_dir / "build-log.md"
            if alt_path.exists():
                build_log_path = alt_path

        # Update checkpoint with agent
        ckpt_path = root / ".aho-checkpoint.json"
        if ckpt_path.exists():
            try:
                ckpt = json.loads(ckpt_path.read_text())
                ws_key = workstream_id
                if ws_key not in ckpt.get("workstreams", {}):
                    ckpt.setdefault("workstreams", {})[ws_key] = {}
                agent = os.environ.get("AHO_EXECUTOR", os.environ.get("IAO_EXECUTOR", "unknown"))
                ckpt["workstreams"][ws_key]["agent"] = agent
                ckpt["workstreams"][ws_key]["executor"] = agent
                ckpt_path.write_text(json.dumps(ckpt, indent=2))
            except Exception:
                pass

        # Prepare entry
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        status_tag = status.upper()
        entry = f"\n### {workstream_id} — {status_tag}\n\n- {summary}\n- Completed: {ts}\n"
        
        if build_log_path.exists():
            with open(build_log_path, 'a') as f:
                f.write(entry)
        else:
            # If still not found, try to create it in the canonical location
            try:
                build_log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(build_log_path, 'w') as f:
                    f.write(f"# Build Log - {prefix} - {_ITERATION}\n\n")
                    f.write(entry)
            except Exception:
                pass
            
    except Exception as e:
        print(f"[aho.log] ERROR: {e}")


def log_event(event_type, source_agent, target, action,
              input_summary="", output_summary="",
              tokens=None, latency_ms=None,
              status="success", error=None, gotcha_triggered=None,
              workstream_id=None):
    """Log a structured event to the JSONL event stream."""
    ws_id = workstream_id or os.environ.get("AHO_WORKSTREAM_ID", os.environ.get("IAO_WORKSTREAM_ID"))
    
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "iteration": _ITERATION,
        "workstream_id": ws_id,
        "event_type": event_type,
        "source_agent": source_agent,
        "target": target,
        "action": action,
        "input_summary": str(input_summary)[:200],
        "output_summary": str(output_summary)[:200],
        "tokens": tokens,
        "latency_ms": latency_ms,
        "status": status,
        "error": str(error)[:500] if error else None,
        "gotcha_triggered": gotcha_triggered
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a') as f:
        f.write(json.dumps(event) + '\n')

    # OTEL span emission — additive, never load-bearing
    if _otel_tracer is not None:
        try:
            with _otel_tracer.start_as_current_span(event_type) as span:
                span.set_attribute("aho.iteration", _ITERATION)
                span.set_attribute("aho.workstream_id", ws_id or "")
                span.set_attribute("aho.event_type", event_type)
                span.set_attribute("aho.source_agent", source_agent or "")
                span.set_attribute("aho.target", target or "")
                span.set_attribute("aho.action", action or "")
                span.set_attribute("aho.status", status or "")
                if tokens is not None:
                    set_attrs_from_dict(span, "aho.tokens", tokens)
                if latency_ms is not None:
                    span.set_attribute("aho.latency_ms", latency_ms)
                if error:
                    span.set_attribute("aho.error", str(error)[:500])
                if gotcha_triggered:
                    span.set_attribute("aho.gotcha_triggered", gotcha_triggered)
        except Exception:
            pass  # OTEL failure must never break JSONL logging

    return event
