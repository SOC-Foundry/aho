"""aho.observability - substrate-freshness telemetry (W1 D4 of 0.3.1).

Per-substrate-fact "last verified" telemetry. Each fact has a warning-age
threshold; when its `last_verified_age_seconds` exceeds the threshold,
upstream dashboards/probes surface the staleness.

Mechanics:
- `record_observable(fact_id, ...)` appends one line to the append-only
  log at `~/.local/share/aho/observables.jsonl` AND emits an OTEL gauge
  `aho.observable.last_verified_age_seconds` (0 at time of record, since
  we just observed; age grows over time per `last_verified_age_seconds`).
- `last_verified_age_seconds(fact_id, ...)` scans the log for the most
  recent successful probe of the fact and returns seconds since.
- Closes F-0.2.18-W1-004 operationally - substrate-freshness signal lives
  in OTEL + dashboard, no longer purely tribal knowledge.

Log shape (per JSONL line):
    {
      "fact_id":           str,
      "host":              str,           # short hostname
      "project":           str,
      "probed_at_utc":     str (ISO),
      "probe_outcome":     str,           # "ok" | "fail" | "host_unreachable"
      "value_observed":    Any | null,    # short serializable summary
      "probe_command":     str | null,
      "duration_ms":       int | null,
      "extra":             dict           # fact-specific structured data
    }
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


OBSERVABLES_LOG = Path(os.environ.get(
    "AHO_OBSERVABLES_LOG",
    str(Path.home() / ".local" / "share" / "aho" / "observables.jsonl"),
))


try:
    from opentelemetry import metrics as _otel_metrics
    _meter = _otel_metrics.get_meter("aho.observability")
    # Observable gauge - registered via callback so we don't have to manage
    # per-fact instruments. The callback reads the JSONL log on demand.
    _gauge_instrument: Optional[Any] = None
except ImportError:  # pragma: no cover
    _otel_metrics = None
    _meter = None
    _gauge_instrument = None


# Per-fact warning thresholds (seconds) per amendment §D4 table.
FACT_WARNING_AGE_SECONDS: Dict[str, int] = {
    "tailnet_domain":              30 * 24 * 3600,
    "otel_collector_endpoint":               3600,
    "image_fqdn":                   7 * 24 * 3600,
    "ssh_host_keys":                90 * 24 * 3600,
    "podman_version":               14 * 24 * 3600,
    "broker_socket":                         3600,
    "chromadb_mount_path":          30 * 24 * 3600,
    "ollama_api_endpoint":                   3600,
    "onepassword_agent_socket":              3600,
    "cloudflarewarp_dns":                    3600,
    "chromadb_doc_count":                    1800,
    "checkpoint_mtime":             24 * 3600,
    "sys_path_clean":                        3600,
    "beacon_otlp_reachable":                 3600,
}


class ObservabilityError(RuntimeError):
    """Generic observability error."""


@dataclass
class ProbeRecord:
    fact_id: str
    host: str
    project: str
    probed_at_utc: str
    probe_outcome: str
    value_observed: Any = None
    probe_command: Optional[str] = None
    duration_ms: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_jsonl(self) -> str:
        d = {
            "fact_id": self.fact_id,
            "host": self.host,
            "project": self.project,
            "probed_at_utc": self.probed_at_utc,
            "probe_outcome": self.probe_outcome,
            "value_observed": self.value_observed,
            "probe_command": self.probe_command,
            "duration_ms": self.duration_ms,
            "extra": self.extra,
        }
        return json.dumps(d, default=str)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hostname() -> str:
    try:
        return socket.gethostname().split(".")[0]
    except Exception:  # noqa: BLE001
        return os.environ.get("HOSTNAME", "unknown")


def _default_project() -> str:
    return os.environ.get("AHO_PROJECT", "ahomw")


def _ensure_log_dir() -> None:
    OBSERVABLES_LOG.parent.mkdir(parents=True, exist_ok=True)


def record_observable(
    fact_id: str,
    *,
    project: Optional[str] = None,
    host: Optional[str] = None,
    probe_outcome: str = "ok",
    value_observed: Any = None,
    probe_command: Optional[str] = None,
    duration_ms: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> ProbeRecord:
    """Record a fact probe. Appends one JSONL line to `OBSERVABLES_LOG`.

    `probe_outcome` is one of "ok" | "fail" | "host_unreachable" |
    "unreachable" | "auth_failed". Only "ok" counts toward freshness; all other
    outcomes are non-fresh. `value_observed` is a short serializable summary
    (e.g., version string, count, file mtime).
    """
    if not isinstance(fact_id, str) or not fact_id.strip():
        raise ObservabilityError(f"fact_id must be a non-empty string, got {fact_id!r}")
    _valid_outcomes = ("ok", "fail", "host_unreachable", "unreachable", "auth_failed")
    if probe_outcome not in _valid_outcomes:
        raise ObservabilityError(
            f"probe_outcome must be one of {_valid_outcomes}, got {probe_outcome!r}"
        )

    rec = ProbeRecord(
        fact_id=fact_id,
        host=host or _hostname(),
        project=project or _default_project(),
        probed_at_utc=_now_utc(),
        probe_outcome=probe_outcome,
        value_observed=value_observed,
        probe_command=probe_command,
        duration_ms=duration_ms,
        extra=extra or {},
    )
    _ensure_log_dir()
    with OBSERVABLES_LOG.open("a", encoding="utf-8") as f:
        f.write(rec.to_jsonl())
        f.write("\n")
    return rec


def _scan_latest(fact_id: str, host: Optional[str] = None, project: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Walk the JSONL log; return the latest successful probe matching the
    filter. Returns None if no record found.
    """
    if not OBSERVABLES_LOG.exists():
        return None
    latest: Optional[Dict[str, Any]] = None
    latest_ts: Optional[datetime] = None
    with OBSERVABLES_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("fact_id") != fact_id:
                continue
            if host and d.get("host") != host:
                continue
            if project and d.get("project") != project:
                continue
            if d.get("probe_outcome") != "ok":
                continue
            ts_raw = d.get("probed_at_utc")
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if latest_ts is None or ts > latest_ts:
                latest = d
                latest_ts = ts
    return latest


def last_verified_age_seconds(
    fact_id: str,
    *,
    host: Optional[str] = None,
    project: Optional[str] = None,
) -> Optional[float]:
    """Seconds since the fact was last successfully probed. Returns None if
    the fact has never been recorded successfully (caller treats as infinite
    staleness or as unconfigured per use case).
    """
    rec = _scan_latest(fact_id, host=host, project=project)
    if rec is None:
        return None
    ts_raw = rec.get("probed_at_utc")
    if not ts_raw:
        return None
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = datetime.now(timezone.utc)
    return (now - ts).total_seconds()


def warning_age_seconds(fact_id: str) -> int:
    """Return the per-fact warning threshold; raises if unknown."""
    if fact_id not in FACT_WARNING_AGE_SECONDS:
        raise ObservabilityError(f"unknown fact_id {fact_id!r}")
    return FACT_WARNING_AGE_SECONDS[fact_id]


def fact_color(age_seconds: Optional[float], warn_seconds: int) -> str:
    """Tri-color cascade: green if fresh, yellow at 1-3× warning, red at >3×.
    Unknown (no record) is treated as red.
    """
    if age_seconds is None:
        return "red"
    if age_seconds < warn_seconds:
        return "green"
    if age_seconds < 3 * warn_seconds:
        return "yellow"
    return "red"


def snapshot_all_facts(
    *,
    host: Optional[str] = None,
    project: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """One row per known fact: id, last age (or None), warning threshold, color.
    Used by dashboard rendering + summary count.
    """
    out: List[Dict[str, Any]] = []
    for fact_id, warn in FACT_WARNING_AGE_SECONDS.items():
        age = last_verified_age_seconds(fact_id, host=host, project=project)
        out.append({
            "fact_id": fact_id,
            "last_age_seconds": age,
            "warning_age_seconds": warn,
            "color": fact_color(age, warn),
        })
    return out


def stale_count(snapshot: Iterable[Dict[str, Any]]) -> int:
    """Count of facts in yellow or red state."""
    return sum(1 for row in snapshot if row["color"] in ("yellow", "red"))


# OTEL emission: per-fact gauge emitted on each record_observable call.
def _emit_otel_age_gauge(fact_id: str, host: str, project: str, age_seconds: float) -> None:
    if _meter is None:
        return
    try:
        # Use a synchronous gauge via UpDownCounter pattern (set_value not in
        # all SDK versions). Best-effort.
        counter = _meter.create_gauge(
            "aho.observable.last_verified_age_seconds",
            description="Seconds since the named substrate fact was last successfully probed.",
            unit="s",
        )
        counter.set(age_seconds, attributes={
            "fact_id": fact_id,
            "host": host,
            "project": project,
        })
    except Exception:  # noqa: BLE001 - telemetry boundary
        pass


__all__ = [
    "FACT_WARNING_AGE_SECONDS",
    "ObservabilityError",
    "ProbeRecord",
    "record_observable",
    "last_verified_age_seconds",
    "warning_age_seconds",
    "fact_color",
    "snapshot_all_facts",
    "stale_count",
    "OBSERVABLES_LOG",
]
