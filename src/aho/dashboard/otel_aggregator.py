"""OTEL signal aggregator for the Pillar 8 cost + token dashboard.

Reads Claude Code OTEL jsonl exports from
  ~/.local/share/aho/logs/logs.jsonl
  ~/.local/share/aho/metrics/metrics.jsonl
and groups signals by `aho.workstream` resource attribute for the
active iteration.

2s TTL cache matches the dashboard poll cadence.

PII scrubbing: no user.*/organization.id/session.id fields ever appear
in aggregator output. Only `aho.*` resource attrs are read for
filtering; numeric values and event names are the only payload.
"""
from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from aho.paths import AhoProjectNotFound, find_project_root


_DEFAULT_LOGS_PATH = Path.home() / ".local/share/aho/logs/logs.jsonl"
_DEFAULT_METRICS_PATH = Path.home() / ".local/share/aho/metrics/metrics.jsonl"

_CACHE_TTL_SECONDS = 2.0
_cache: dict[str, Any] = {"data": None, "ts": 0.0, "key": None}


def _attr_map(attrs: list[dict]) -> dict[str, Any]:
    """Collapse OTEL attribute list into a plain dict. Coerces int64 strings."""
    out: dict[str, Any] = {}
    for a in attrs:
        key = a.get("key")
        if key is None:
            continue
        v = a.get("value", {})
        if "stringValue" in v:
            out[key] = v["stringValue"]
        elif "intValue" in v:
            raw = v["intValue"]
            try:
                out[key] = int(raw)
            except (TypeError, ValueError):
                out[key] = raw
        elif "doubleValue" in v:
            out[key] = v["doubleValue"]
        elif "boolValue" in v:
            out[key] = v["boolValue"]
    return out


def _resource_scope(resource: dict) -> tuple[str, str, str]:
    attrs = _attr_map(resource.get("attributes", []))
    iteration = attrs.get("aho.iteration", "") or ""
    workstream = attrs.get("aho.workstream", "") or ""
    role = attrs.get("aho.role", "") or ""
    return iteration, workstream, role


def _iter_log_records(path: Path) -> Iterator[tuple[str, str, str, str, dict]]:
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for rl in rec.get("resourceLogs", []):
                iteration, workstream, _ = _resource_scope(rl.get("resource", {}))
                for sl in rl.get("scopeLogs", []):
                    for lr in sl.get("logRecords", []):
                        attrs = _attr_map(lr.get("attributes", []))
                        yield (
                            iteration,
                            workstream,
                            attrs.get("event.name", "") or "",
                            attrs.get("event.timestamp", "") or "",
                            attrs,
                        )


def _iter_metric_points(
    path: Path,
) -> Iterator[tuple[str, str, str, dict, float | int | None]]:
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for rm in rec.get("resourceMetrics", []):
                iteration, workstream, _ = _resource_scope(rm.get("resource", {}))
                for sm in rm.get("scopeMetrics", []):
                    for m in sm.get("metrics", []):
                        name = m.get("name", "") or ""
                        dps = (
                            m.get("sum", {}).get("dataPoints")
                            or m.get("gauge", {}).get("dataPoints")
                            or m.get("histogram", {}).get("dataPoints")
                            or []
                        )
                        for dp in dps:
                            dp_attrs = _attr_map(dp.get("attributes", []))
                            val: float | int | None = None
                            if "asDouble" in dp:
                                val = float(dp["asDouble"])
                            elif "asInt" in dp:
                                raw = dp["asInt"]
                                try:
                                    val = int(raw)
                                except (TypeError, ValueError):
                                    val = None
                            yield iteration, workstream, name, dp_attrs, val


def _empty_workstream_record(ws: str) -> dict:
    return {
        "workstream_id": ws,
        "cost_usd": 0.0,
        "tokens": {
            "input": 0,
            "output": 0,
            "cacheRead": 0,
            "cacheCreation": 0,
            "total": 0,
        },
        "cache_vs_new_ratio": {"cache_read": 0, "new_content": 0, "ratio": None},
        "active_time_seconds": 0.0,
        "api_request_count": 0,
        "api_error_count": 0,
        "api_retries_exhausted_count": 0,
        "tool_result_count": 0,
        "tool_decision_count": 0,
        "mcp_server_connection_count": 0,
        "user_prompt_count": 0,
        "internal_error_count": 0,
        "top_error_names": [],
        "first_event_ts": None,
        "last_event_ts": None,
        "wall_clock_duration_s": 0.0,
    }


def _valid_workstream_scope(iteration_rec: str, iteration_filter: str, ws: str) -> bool:
    if iteration_rec != iteration_filter:
        return False
    if not ws:
        return False
    if ws.startswith("${"):  # unexpanded placeholder from pre-restart sessions
        return False
    return True


def _compute_ratios_and_duration(rec: dict) -> None:
    cache_read = rec["tokens"]["cacheRead"]
    new_tokens = (
        rec["tokens"]["input"]
        + rec["tokens"]["output"]
        + rec["tokens"]["cacheCreation"]
    )
    rec["cache_vs_new_ratio"] = {
        "cache_read": cache_read,
        "new_content": new_tokens,
        "ratio": (cache_read / new_tokens) if new_tokens > 0 else None,
    }
    if rec.get("first_event_ts") and rec.get("last_event_ts"):
        try:
            t0 = datetime.fromisoformat(rec["first_event_ts"].replace("Z", "+00:00"))
            t1 = datetime.fromisoformat(rec["last_event_ts"].replace("Z", "+00:00"))
            rec["wall_clock_duration_s"] = max((t1 - t0).total_seconds(), 0.0)
        except (ValueError, TypeError):
            rec["wall_clock_duration_s"] = 0.0


def _rollup(workstreams: dict[str, dict]) -> dict:
    r = _empty_workstream_record("iteration")
    r.pop("workstream_id", None)
    if not workstreams:
        return {
            "cost_usd": 0.0,
            "tokens": r["tokens"],
            "cache_vs_new_ratio": r["cache_vs_new_ratio"],
            "active_time_seconds": 0.0,
            "api_request_count": 0,
            "api_error_count": 0,
            "api_retries_exhausted_count": 0,
            "tool_result_count": 0,
            "tool_decision_count": 0,
            "mcp_server_connection_count": 0,
            "user_prompt_count": 0,
            "internal_error_count": 0,
            "workstream_count": 0,
        }
    for rec in workstreams.values():
        r["cost_usd"] += rec["cost_usd"]
        for k in ("input", "output", "cacheRead", "cacheCreation", "total"):
            r["tokens"][k] += rec["tokens"][k]
        r["active_time_seconds"] += rec["active_time_seconds"]
        r["api_request_count"] += rec["api_request_count"]
        r["api_error_count"] += rec["api_error_count"]
        r["api_retries_exhausted_count"] += rec["api_retries_exhausted_count"]
        r["tool_result_count"] += rec["tool_result_count"]
        r["tool_decision_count"] += rec["tool_decision_count"]
        r["mcp_server_connection_count"] += rec["mcp_server_connection_count"]
        r["user_prompt_count"] += rec["user_prompt_count"]
        r["internal_error_count"] += rec["internal_error_count"]
    cache_read = r["tokens"]["cacheRead"]
    new_tokens = (
        r["tokens"]["input"] + r["tokens"]["output"] + r["tokens"]["cacheCreation"]
    )
    r["cache_vs_new_ratio"] = {
        "cache_read": cache_read,
        "new_content": new_tokens,
        "ratio": (cache_read / new_tokens) if new_tokens > 0 else None,
    }
    r["workstream_count"] = len(workstreams)
    # Drop fields that only make sense at the workstream level
    for k in ("first_event_ts", "last_event_ts", "wall_clock_duration_s", "top_error_names"):
        r.pop(k, None)
    return r


def aggregate(
    iteration: str,
    logs_path: Path | None = None,
    metrics_path: Path | None = None,
    force: bool = False,
) -> dict:
    """Aggregate OTEL signals scoped to the given aho iteration.

    Returns a dict with per-workstream records plus an iteration rollup.
    Filters events where `aho.workstream` is empty or an unexpanded
    `${VAR}` placeholder.
    """
    lp = logs_path or _DEFAULT_LOGS_PATH
    mp = metrics_path or _DEFAULT_METRICS_PATH
    cache_key = (iteration, str(lp), str(mp))
    now = time.time()
    if (
        not force
        and _cache["data"] is not None
        and _cache["key"] == cache_key
        and (now - _cache["ts"]) < _CACHE_TTL_SECONDS
    ):
        return _cache["data"]

    ws_rec: dict[str, dict] = {}
    ws_error_names: dict[str, Counter] = defaultdict(Counter)

    for rec_iter, ws, event_name, ts_iso, attrs in _iter_log_records(lp):
        if not _valid_workstream_scope(rec_iter, iteration, ws):
            continue
        r = ws_rec.setdefault(ws, _empty_workstream_record(ws))
        if event_name == "api_request":
            r["api_request_count"] += 1
        elif event_name == "tool_result":
            r["tool_result_count"] += 1
        elif event_name == "tool_decision":
            r["tool_decision_count"] += 1
        elif event_name == "mcp_server_connection":
            r["mcp_server_connection_count"] += 1
        elif event_name == "user_prompt":
            r["user_prompt_count"] += 1
        elif event_name == "internal_error":
            r["internal_error_count"] += 1
            r["api_error_count"] += 1
            name = attrs.get("error_name") or "UNKNOWN"
            ws_error_names[ws][name] += 1
        if ts_iso:
            if not r["first_event_ts"] or ts_iso < r["first_event_ts"]:
                r["first_event_ts"] = ts_iso
            if not r["last_event_ts"] or ts_iso > r["last_event_ts"]:
                r["last_event_ts"] = ts_iso

    for rec_iter, ws, name, dp_attrs, val in _iter_metric_points(mp):
        if not _valid_workstream_scope(rec_iter, iteration, ws) or val is None:
            continue
        r = ws_rec.setdefault(ws, _empty_workstream_record(ws))
        if name == "claude_code.cost.usage":
            r["cost_usd"] += float(val)
        elif name == "claude_code.token.usage":
            t = dp_attrs.get("type")
            if t in ("input", "output", "cacheRead", "cacheCreation"):
                r["tokens"][t] += int(val)
                r["tokens"]["total"] += int(val)
        elif name == "claude_code.active_time.total":
            r["active_time_seconds"] += float(val)

    for ws, rec in ws_rec.items():
        rec["top_error_names"] = [
            {"name": n, "count": c}
            for n, c in ws_error_names[ws].most_common(3)
        ]
        _compute_ratios_and_duration(rec)

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_files": {"logs": str(lp), "metrics": str(mp)},
        "iteration": iteration,
        "workstreams": {ws: ws_rec[ws] for ws in sorted(ws_rec)},
        "iteration_rollup": _rollup(ws_rec),
    }

    _cache["data"] = result
    _cache["ts"] = now
    _cache["key"] = cache_key
    return result


def get_active_iteration() -> str:
    """Read the active iteration label from the project checkpoint."""
    try:
        ckpt = find_project_root() / ".aho-checkpoint.json"
    except AhoProjectNotFound:
        return ""
    if not ckpt.exists():
        return ""
    try:
        return json.loads(ckpt.read_text()).get("iteration", "") or ""
    except (json.JSONDecodeError, OSError):
        return ""


def get_otel_state(force: bool = False) -> dict:
    """Dashboard entry point. Aggregates the active iteration."""
    return aggregate(iteration=get_active_iteration(), force=force)


def get_workstream_detail(workstream_id: str, force: bool = False) -> dict | None:
    state = get_otel_state(force=force)
    rec = state.get("workstreams", {}).get(workstream_id)
    if rec is None:
        return None
    return {
        "iteration": state.get("iteration"),
        "generated_at": state.get("generated_at"),
        "workstream": rec,
    }
