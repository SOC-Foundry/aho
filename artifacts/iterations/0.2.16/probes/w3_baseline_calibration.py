#!/usr/bin/env python3
"""W3 bucket 6 - calibration probe for ToolDurationOutlier rule (rule 5).

Computes the p99 of ``claude_code.tool_result`` ``duration_ms`` event
attributes recorded in ``~/.local/share/aho/logs/logs.jsonl``, filtered to
``aho.workstream`` resource attrs in the configured set (default: W1, W2).

Why an event-log probe rather than a metrics histogram:
The plan §W3 row 5 expression names ``claude_code_tool_result_duration_ms_bucket``,
which would be a Prometheus-style histogram metric. Survey of the live
``metrics.jsonl`` (W3 bucket 6 baseline survey) found the current Claude Code
emission set is ``claude_code.{active_time.total, cost.usage, token.usage,
session.count, lines_of_code.count, code_edit_tool.decision}`` - no
``tool_result.duration_ms`` histogram. The duration value is present only as
a ``duration_ms`` attribute on the ``claude_code.tool_result`` log event. The
rule's metric reference is therefore aspirational against the current
emission; this probe computes the calibration from the truth source (the
event attribute) so the rule's substituted threshold is honest.

Re-runnable: usage ``python3 w3_baseline_calibration.py [logs.jsonl path]``.
Default path is the canonical ``~/.local/share/aho/logs/logs.jsonl``.
Workstream filter is configurable via ``--workstreams W1,W2,W3``; default
``W1,W2`` per plan §W3 bucket 6.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def _attr_value(attr: dict) -> object:
    val = attr.get("value") or {}
    if "stringValue" in val:
        return val["stringValue"]
    if "intValue" in val:
        return int(val["intValue"])
    if "doubleValue" in val:
        return float(val["doubleValue"])
    if "boolValue" in val:
        return val["boolValue"]
    return None


def _resource_workstream(resource: dict) -> str | None:
    for a in resource.get("attributes", []):
        if a.get("key") == "aho.workstream":
            return _attr_value(a)
    return None


def _record_duration_ms(record: dict) -> int | None:
    body = record.get("body") or {}
    if body.get("stringValue") != "claude_code.tool_result":
        return None
    for a in record.get("attributes", []):
        if a.get("key") == "duration_ms":
            v = _attr_value(a)
            if v is None:
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None
    return None


def _record_time_unix_nano(record: dict) -> int | None:
    t = record.get("timeUnixNano") or record.get("observedTimeUnixNano")
    try:
        return int(t) if t is not None else None
    except (TypeError, ValueError):
        return None


def collect(path: Path, workstreams: set[str]) -> dict:
    """Walk logs.jsonl and return durations + workstream counts + time bounds."""
    durations: list[int] = []
    ws_counts: dict[str, int] = {}
    found_workstreams: set[str] = set()
    earliest = None
    latest = None
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            for rl in doc.get("resourceLogs", []):
                ws = _resource_workstream(rl.get("resource", {}))
                if ws is None:
                    continue
                found_workstreams.add(ws)
                if ws not in workstreams:
                    continue
                for sl in rl.get("scopeLogs", []):
                    for rec in sl.get("logRecords", []):
                        d = _record_duration_ms(rec)
                        if d is None:
                            continue
                        durations.append(d)
                        ws_counts[ws] = ws_counts.get(ws, 0) + 1
                        t = _record_time_unix_nano(rec)
                        if t is not None:
                            earliest = t if earliest is None or t < earliest else earliest
                            latest = t if latest is None or t > latest else latest
    return {
        "durations": durations,
        "workstream_counts": ws_counts,
        "found_workstreams": sorted(found_workstreams),
        "earliest_unix_nano": earliest,
        "latest_unix_nano": latest,
    }


def percentile(values: list[int], q: float) -> float:
    """q in [0,1]. Linear interpolation between sorted values (statistics.quantiles flavour)."""
    if not values:
        raise ValueError("cannot compute percentile of empty list")
    s = sorted(values)
    if len(s) == 1:
        return float(s[0])
    rank = q * (len(s) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(s) - 1)
    frac = rank - lo
    return s[lo] + frac * (s[hi] - s[lo])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "logs_path",
        nargs="?",
        default=str(Path.home() / ".local" / "share" / "aho" / "logs" / "logs.jsonl"),
        help="Path to logs.jsonl (default: canonical XDG path).",
    )
    parser.add_argument(
        "--workstreams",
        default="W1,W2",
        help="Comma-separated workstream filter (default: W1,W2).",
    )
    parser.add_argument(
        "--multiplier",
        type=float,
        default=3.0,
        help="Threshold multiplier on p99 (default: 3.0 per plan §W3).",
    )
    args = parser.parse_args(argv)

    path = Path(args.logs_path)
    if not path.exists():
        print(f"ERROR: logs file not found: {path}", file=sys.stderr)
        return 2

    target_ws = {w.strip() for w in args.workstreams.split(",") if w.strip()}
    result = collect(path, target_ws)
    durations = result["durations"]

    print(f"logs file:         {path}")
    print(f"target workstreams: {sorted(target_ws)}")
    print(f"workstreams found in file: {result['found_workstreams']}")
    print(f"matched-workstream tool_result events: {len(durations)}")
    print(f"per-workstream counts: {result['workstream_counts']}")
    if result["earliest_unix_nano"] is not None:
        from datetime import datetime, timezone
        e = datetime.fromtimestamp(result["earliest_unix_nano"] / 1e9, tz=timezone.utc)
        l = datetime.fromtimestamp(result["latest_unix_nano"] / 1e9, tz=timezone.utc)
        print(f"time range: {e.isoformat()}  →  {l.isoformat()}")

    if not durations:
        print()
        print("no samples in target workstreams - cannot calibrate", file=sys.stderr)
        return 1

    durations.sort()
    p50 = percentile(durations, 0.50)
    p95 = percentile(durations, 0.95)
    p99 = percentile(durations, 0.99)
    p999 = percentile(durations, 0.999)
    threshold = p99 * args.multiplier

    print()
    print("duration_ms distribution (event attribute, ground truth):")
    print(f"  min:    {durations[0]}")
    print(f"  p50:    {p50:.1f}")
    print(f"  p95:    {p95:.1f}")
    print(f"  p99:    {p99:.1f}")
    print(f"  p99.9:  {p999:.1f}")
    print(f"  max:    {durations[-1]}")
    print(f"  mean:   {statistics.fmean(durations):.1f}")
    print()
    print(f"calibrated baseline_p99_ms = {p99:.0f}")
    print(f"threshold (multiplier × {args.multiplier}) = {threshold:.0f} ms")
    print()
    print("substitute TODO_BASELINE_P99_MS in")
    print("  artifacts/iterations/0.2.16/alerts/anomaly-rules.yaml")
    print(f"with: {threshold:.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
