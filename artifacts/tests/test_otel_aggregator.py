"""Unit tests for src/aho/dashboard/otel_aggregator.py (0.2.16 W1).

Tests:
  - aggregation math (cost, tokens, event counts)
  - filtering by iteration + workstream (skip ${AHO_*} placeholders)
  - missing-field handling
  - 2s cache TTL (and force=True bust)
  - iteration rollup = sum of per-workstream totals
  - cache_vs_new_ratio calculation
  - wall_clock_duration_s from ISO timestamps
  - top_error_names capped at 3
  - PII scrubbing (output contains no user.*/organization.id/session.id)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from aho.dashboard import otel_aggregator as oa


# ------------------------------------------------------------------------- #
# Helpers that build the OTEL jsonl shape the aggregator consumes           #
# ------------------------------------------------------------------------- #


def _resource(iteration: str, workstream: str, role: str = "drafter") -> dict:
    return {
        "attributes": [
            {"key": "service.name", "value": {"stringValue": "claude-code"}},
            {"key": "aho.iteration", "value": {"stringValue": iteration}},
            {"key": "aho.workstream", "value": {"stringValue": workstream}},
            {"key": "aho.role", "value": {"stringValue": role}},
        ]
    }


def _log_line(
    iteration: str,
    workstream: str,
    event_name: str,
    event_timestamp: str,
    extra_attrs: list[dict] | None = None,
    body: str | None = None,
) -> str:
    attrs: list[dict] = [
        {"key": "event.name", "value": {"stringValue": event_name}},
        {"key": "event.timestamp", "value": {"stringValue": event_timestamp}},
        # PII attrs that MUST be scrubbed from aggregator output
        {"key": "user.email", "value": {"stringValue": "scrub@me.test"}},
        {"key": "user.id", "value": {"stringValue": "USER_HASH"}},
        {"key": "organization.id", "value": {"stringValue": "ORG_UUID"}},
    ]
    if extra_attrs:
        attrs.extend(extra_attrs)
    rec = {
        "resourceLogs": [
            {
                "resource": _resource(iteration, workstream),
                "scopeLogs": [
                    {
                        "logRecords": [
                            {
                                "body": {"stringValue": body or f"claude_code.{event_name}"},
                                "attributes": attrs,
                            }
                        ]
                    }
                ],
            }
        ]
    }
    return json.dumps(rec)


def _metric_line(
    iteration: str,
    workstream: str,
    metric_name: str,
    value: float | int,
    dp_attrs: list[dict] | None = None,
    as_int: bool = False,
    time_ns: str = "1776808997804000000",
) -> str:
    dp: dict = {
        "attributes": dp_attrs or [],
        "timeUnixNano": time_ns,
        # Contaminate the data-point attrs with PII so we can assert scrubbing
        # (the aggregator should never put these on output records).
    }
    if as_int:
        dp["asInt"] = str(int(value))
    else:
        dp["asDouble"] = float(value)
    rec = {
        "resourceMetrics": [
            {
                "resource": _resource(iteration, workstream),
                "scopeMetrics": [
                    {
                        "metrics": [
                            {
                                "name": metric_name,
                                "sum": {"dataPoints": [dp]},
                            }
                        ]
                    }
                ],
            }
        ]
    }
    return json.dumps(rec)


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


@pytest.fixture(autouse=True)
def _clear_aggregator_cache():
    """Each test gets a fresh cache (module-level singleton otherwise)."""
    oa._cache["data"] = None
    oa._cache["ts"] = 0.0
    oa._cache["key"] = None
    yield


# ------------------------------------------------------------------------- #
# Tests                                                                     #
# ------------------------------------------------------------------------- #


def test_cost_and_token_math(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(logs, [])
    _write_jsonl(
        metrics,
        [
            _metric_line("0.2.16", "W1", "claude_code.cost.usage", 0.25),
            _metric_line("0.2.16", "W1", "claude_code.cost.usage", 0.75),
            _metric_line(
                "0.2.16",
                "W1",
                "claude_code.token.usage",
                100,
                dp_attrs=[{"key": "type", "value": {"stringValue": "input"}}],
                as_int=True,
            ),
            _metric_line(
                "0.2.16",
                "W1",
                "claude_code.token.usage",
                50,
                dp_attrs=[{"key": "type", "value": {"stringValue": "output"}}],
                as_int=True,
            ),
            _metric_line(
                "0.2.16",
                "W1",
                "claude_code.token.usage",
                4000,
                dp_attrs=[{"key": "type", "value": {"stringValue": "cacheRead"}}],
                as_int=True,
            ),
            _metric_line(
                "0.2.16",
                "W1",
                "claude_code.token.usage",
                200,
                dp_attrs=[{"key": "type", "value": {"stringValue": "cacheCreation"}}],
                as_int=True,
            ),
        ],
    )
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    w1 = state["workstreams"]["W1"]
    assert w1["cost_usd"] == pytest.approx(1.0)
    assert w1["tokens"] == {
        "input": 100,
        "output": 50,
        "cacheRead": 4000,
        "cacheCreation": 200,
        "total": 4350,
    }


def test_event_count_aggregation(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs,
        [
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z"),
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:01Z"),
            _log_line("0.2.16", "W1", "tool_result", "2026-04-23T10:00:02Z"),
            _log_line("0.2.16", "W1", "tool_decision", "2026-04-23T10:00:03Z"),
            _log_line("0.2.16", "W1", "user_prompt", "2026-04-23T10:00:04Z"),
            _log_line("0.2.16", "W1", "mcp_server_connection", "2026-04-23T10:00:05Z"),
        ],
    )
    _write_jsonl(metrics, [])
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    w1 = state["workstreams"]["W1"]
    assert w1["api_request_count"] == 2
    assert w1["tool_result_count"] == 1
    assert w1["tool_decision_count"] == 1
    assert w1["user_prompt_count"] == 1
    assert w1["mcp_server_connection_count"] == 1


def test_filters_placeholder_and_wrong_iteration(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs,
        [
            # valid W1 record
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z"),
            # unexpanded placeholder — must be skipped
            _log_line("0.2.16", "${AHO_WORKSTREAM}", "api_request", "2026-04-23T10:00:01Z"),
            # wrong iteration — must be skipped
            _log_line("0.2.15", "W1", "api_request", "2026-04-23T10:00:02Z"),
            # empty workstream — must be skipped
            _log_line("0.2.16", "", "api_request", "2026-04-23T10:00:03Z"),
        ],
    )
    _write_jsonl(metrics, [])
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    # Only the one valid W1 record should have landed
    assert list(state["workstreams"].keys()) == ["W1"]
    assert state["workstreams"]["W1"]["api_request_count"] == 1


def test_cache_vs_new_ratio(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(logs, [])
    _write_jsonl(
        metrics,
        [
            _metric_line(
                "0.2.16", "W1", "claude_code.token.usage", 1000,
                dp_attrs=[{"key": "type", "value": {"stringValue": "cacheRead"}}],
                as_int=True,
            ),
            _metric_line(
                "0.2.16", "W1", "claude_code.token.usage", 100,
                dp_attrs=[{"key": "type", "value": {"stringValue": "input"}}],
                as_int=True,
            ),
            _metric_line(
                "0.2.16", "W1", "claude_code.token.usage", 50,
                dp_attrs=[{"key": "type", "value": {"stringValue": "output"}}],
                as_int=True,
            ),
            _metric_line(
                "0.2.16", "W1", "claude_code.token.usage", 50,
                dp_attrs=[{"key": "type", "value": {"stringValue": "cacheCreation"}}],
                as_int=True,
            ),
        ],
    )
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    ratio = state["workstreams"]["W1"]["cache_vs_new_ratio"]
    assert ratio["cache_read"] == 1000
    assert ratio["new_content"] == 200  # 100 + 50 + 50
    assert ratio["ratio"] == pytest.approx(5.0)


def test_cache_vs_new_ratio_none_when_no_new_tokens(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(logs, [])
    _write_jsonl(
        metrics,
        [
            _metric_line(
                "0.2.16", "W1", "claude_code.token.usage", 500,
                dp_attrs=[{"key": "type", "value": {"stringValue": "cacheRead"}}],
                as_int=True,
            ),
        ],
    )
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    assert state["workstreams"]["W1"]["cache_vs_new_ratio"]["ratio"] is None


def test_iteration_rollup_sums_workstreams(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs,
        [
            _log_line("0.2.16", "W0", "api_request", "2026-04-21T10:00:00Z"),
            _log_line("0.2.16", "W0", "user_prompt", "2026-04-21T10:00:01Z"),
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z"),
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:01Z"),
        ],
    )
    _write_jsonl(
        metrics,
        [
            _metric_line("0.2.16", "W0", "claude_code.cost.usage", 1.25),
            _metric_line("0.2.16", "W1", "claude_code.cost.usage", 0.75),
        ],
    )
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    rollup = state["iteration_rollup"]
    assert rollup["cost_usd"] == pytest.approx(2.0)
    assert rollup["api_request_count"] == 3
    assert rollup["user_prompt_count"] == 1
    assert rollup["workstream_count"] == 2


def test_cache_ttl_caches_and_force_busts(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs, [_log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z")]
    )
    _write_jsonl(metrics, [])

    first = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    assert first["workstreams"]["W1"]["api_request_count"] == 1

    # Append a new event
    with logs.open("a") as f:
        f.write(_log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:01Z") + "\n")

    # Non-forced call should return the cached (old) value — count still 1
    cached = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics)
    assert cached["workstreams"]["W1"]["api_request_count"] == 1

    # Forced call re-reads the file and picks up the new event
    fresh = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    assert fresh["workstreams"]["W1"]["api_request_count"] == 2


def test_cache_ttl_expires_after_2s(tmp_path, monkeypatch):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs, [_log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z")]
    )
    _write_jsonl(metrics, [])

    fake_now = [1_000_000.0]
    monkeypatch.setattr(oa.time, "time", lambda: fake_now[0])
    oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)

    with logs.open("a") as f:
        f.write(_log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:01Z") + "\n")

    # Within TTL: cached
    fake_now[0] += 1.0
    cached = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics)
    assert cached["workstreams"]["W1"]["api_request_count"] == 1

    # Past TTL: re-reads
    fake_now[0] += 2.0  # total 3s since first call
    fresh = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics)
    assert fresh["workstreams"]["W1"]["api_request_count"] == 2


def test_missing_files_return_empty_state(tmp_path):
    state = oa.aggregate(
        iteration="0.2.16",
        logs_path=tmp_path / "nope.jsonl",
        metrics_path=tmp_path / "also_nope.jsonl",
        force=True,
    )
    assert state["workstreams"] == {}
    assert state["iteration_rollup"]["cost_usd"] == 0.0
    assert state["iteration_rollup"]["workstream_count"] == 0


def test_malformed_jsonl_lines_skipped(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    logs.write_text(
        "not valid json\n"
        + _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z")
        + "\n{partial_json\n"
    )
    _write_jsonl(metrics, [])
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    assert state["workstreams"]["W1"]["api_request_count"] == 1


def test_top_error_names_capped_at_three(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    lines = []
    # Five distinct error classes with decreasing counts: ErrA x5, ErrB x4, ErrC x3, ErrD x2, ErrE x1
    for err_name, count in [("ErrA", 5), ("ErrB", 4), ("ErrC", 3), ("ErrD", 2), ("ErrE", 1)]:
        for i in range(count):
            lines.append(
                _log_line(
                    "0.2.16",
                    "W1",
                    "internal_error",
                    f"2026-04-23T10:00:{i:02d}Z",
                    extra_attrs=[{"key": "error_name", "value": {"stringValue": err_name}}],
                )
            )
    _write_jsonl(logs, lines)
    _write_jsonl(metrics, [])
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    top = state["workstreams"]["W1"]["top_error_names"]
    assert len(top) == 3
    assert [t["name"] for t in top] == ["ErrA", "ErrB", "ErrC"]
    assert [t["count"] for t in top] == [5, 4, 3]
    assert state["workstreams"]["W1"]["internal_error_count"] == 15


def test_pii_attrs_never_appear_in_output(tmp_path):
    """F-W0-003 closure: aggregator output must not leak user.*/org.id/session.id."""
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    # Every helper line already contaminates with user.email/user.id/organization.id
    _write_jsonl(
        logs,
        [_log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z")],
    )
    _write_jsonl(
        metrics,
        [
            _metric_line(
                "0.2.16", "W1", "claude_code.cost.usage", 0.10,
                dp_attrs=[
                    {"key": "user.email", "value": {"stringValue": "scrub@me.test"}},
                    {"key": "session.id", "value": {"stringValue": "SESSION_UUID"}},
                    {"key": "model", "value": {"stringValue": "claude-haiku-4-5"}},
                ],
            ),
        ],
    )
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    serialized = json.dumps(state)
    for pii_fragment in [
        "user.email",
        "user.id",
        "user.account_id",
        "user.account_uuid",
        "organization.id",
        "session.id",
        "scrub@me.test",
        "USER_HASH",
        "ORG_UUID",
        "SESSION_UUID",
    ]:
        assert pii_fragment not in serialized, f"PII leaked: {pii_fragment}"


def test_wall_clock_duration_from_iso_timestamps(tmp_path):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs,
        [
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z"),
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:05:30Z"),
            _log_line("0.2.16", "W1", "api_request", "2026-04-23T10:10:00Z"),
        ],
    )
    _write_jsonl(metrics, [])
    state = oa.aggregate(iteration="0.2.16", logs_path=logs, metrics_path=metrics, force=True)
    w1 = state["workstreams"]["W1"]
    assert w1["first_event_ts"] == "2026-04-23T10:00:00Z"
    assert w1["last_event_ts"] == "2026-04-23T10:10:00Z"
    assert w1["wall_clock_duration_s"] == pytest.approx(600.0)


def test_get_workstream_detail_returns_none_for_unknown(tmp_path, monkeypatch):
    logs = tmp_path / "logs.jsonl"
    metrics = tmp_path / "metrics.jsonl"
    _write_jsonl(
        logs, [_log_line("0.2.16", "W1", "api_request", "2026-04-23T10:00:00Z")]
    )
    _write_jsonl(metrics, [])
    monkeypatch.setattr(oa, "_DEFAULT_LOGS_PATH", logs)
    monkeypatch.setattr(oa, "_DEFAULT_METRICS_PATH", metrics)
    monkeypatch.setattr(oa, "get_active_iteration", lambda: "0.2.16")

    assert oa.get_workstream_detail("WXX", force=True) is None
    detail = oa.get_workstream_detail("W1", force=True)
    assert detail is not None
    assert detail["iteration"] == "0.2.16"
    assert detail["workstream"]["workstream_id"] == "W1"
