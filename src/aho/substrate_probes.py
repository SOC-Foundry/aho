"""aho.substrate_probes — concrete probes for the 13 substrate facts in
W1 D4 scope. Each probe is a callable returning (probe_outcome, value_observed,
extra_dict).

The probe set is fixed at W1 D4. New facts get added here (and to
FACT_WARNING_AGE_SECONDS in aho.observability) as they're scoped.

Cross-host probes use Tailscale SSH. `host_unreachable` is a distinct outcome
class and does NOT halt. Host list configured per-deployment via the
AHO_PROBE_HOSTS env var (comma-separated; defaults to local-only probing if
unset).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from aho.observability import (
    FACT_WARNING_AGE_SECONDS,
    record_observable,
)


def _hosts_default() -> List[str]:
    """Read host list from AHO_PROBE_HOSTS env (comma-separated). Defaults
    to local hostname only when unset. Per-deployment config, never hardcoded.
    """
    env_val = os.environ.get("AHO_PROBE_HOSTS", "").strip()
    if env_val:
        return [h.strip() for h in env_val.split(",") if h.strip()]
    return [socket.gethostname().split(".")[0]]


HOSTS_DEFAULT = _hosts_default()
SSH_TIMEOUT_S = 8


# ──────────────────────────────────────────────────────────────────────────
# Probe implementations
#
# Each probe takes host kwarg (None == local) and returns
# (outcome, value, extra). outcome: "ok" | "fail" | "host_unreachable"
# ──────────────────────────────────────────────────────────────────────────


def _ssh_run(host: str, cmd: str, timeout: int = SSH_TIMEOUT_S) -> Tuple[int, str, str]:
    """Run a one-shot command on `host` via Tailscale SSH. Returns (exit, stdout, stderr).
    Returns (-1, "", "host_unreachable") if connect fails / times out.
    """
    if host == _local_hostname() or host == "localhost":
        # Run locally
        try:
            proc = subprocess.run(
                ["sh", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "local_timeout"
        except Exception as exc:  # noqa: BLE001
            return -1, "", f"local_error:{type(exc).__name__}"
    try:
        proc = subprocess.run(
            [
                "ssh",
                "-o", f"ConnectTimeout={timeout}",
                "-o", "BatchMode=yes",
                "-o", "StrictHostKeyChecking=accept-new",
                host,
                cmd,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 4,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "ssh_timeout"
    except FileNotFoundError:
        return -1, "", "ssh_not_installed"
    except Exception as exc:  # noqa: BLE001
        return -1, "", f"ssh_error:{type(exc).__name__}"


def _local_hostname() -> str:
    return socket.gethostname().split(".")[0]


def probe_tailnet_domain(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "tailscale status --json 2>/dev/null")
    if rc == -1:
        return "host_unreachable", None, {"detail": "ssh"}
    if rc != 0:
        return "fail", None, {"detail": "tailscale_status_nonzero"}
    try:
        d = json.loads(out)
        domain = d.get("MagicDNSSuffix") or d.get("CurrentTailnet", {}).get("MagicDNSSuffix")
        return "ok", domain, {"current_tailnet_name": d.get("CurrentTailnet", {}).get("Name")}
    except json.JSONDecodeError:
        return "fail", None, {"detail": "tailscale_status_parse_fail"}


def probe_otel_collector_endpoint(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
    # OTLP gRPC port 4317 — bare TCP connect probe (gRPC requires TLS+HTTP2; tcp connect tells us "is something listening").
    target = endpoint.replace("http://", "").replace("https://", "")
    if ":" in target:
        addr, port_s = target.rsplit(":", 1)
        try:
            port = int(port_s)
        except ValueError:
            return "fail", endpoint, {"detail": "endpoint_parse_fail"}
    else:
        addr, port = target, 4317
    cmd = f"timeout 3 bash -c '< /dev/tcp/{addr}/{port}' 2>/dev/null && echo OPEN || echo CLOSED"
    rc, out, err = _ssh_run(h, cmd)
    if rc == -1:
        return "host_unreachable", endpoint, {"detail": "ssh"}
    if "OPEN" in out:
        return "ok", endpoint, {"port": port, "addr": addr}
    return "fail", endpoint, {"port": port, "addr": addr, "detail": "tcp_connect_failed"}


def probe_image_fqdn(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "podman images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -E 'aho:[0-9]' | head -1")
    if rc == -1:
        return "host_unreachable", None, {}
    img = out.strip()
    if not img:
        return "fail", None, {"detail": "no_aho_image_found"}
    return "ok", img, {}


def probe_ssh_host_keys(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "ls -la /etc/ssh/ssh_host_*_key.pub 2>/dev/null | wc -l")
    if rc == -1:
        return "host_unreachable", None, {}
    try:
        n = int(out.strip())
    except ValueError:
        return "fail", None, {"detail": "parse"}
    if n < 2:
        return "fail", n, {"detail": "missing_keys"}
    return "ok", n, {}


def probe_podman_version(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "podman --version 2>/dev/null")
    if rc == -1:
        return "host_unreachable", None, {}
    if rc != 0:
        return "fail", None, {"detail": "podman_not_installed"}
    return "ok", out.strip(), {}


def probe_broker_socket(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "test -S \"$XDG_RUNTIME_DIR/aho-secrets.sock\" && echo PRESENT || echo ABSENT")
    if rc == -1:
        return "host_unreachable", None, {}
    if "PRESENT" in out:
        return "ok", "present", {}
    return "fail", "absent", {}


def probe_chromadb_mount_path(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    # Local fallback path per aho.rag.FALLBACK_CHROMA_DIR
    rc, out, _ = _ssh_run(h, "if [ -d /var/lib/aho/chroma ]; then echo /var/lib/aho/chroma; elif [ -d $HOME/.local/share/aho/chroma ]; then echo $HOME/.local/share/aho/chroma; else echo NONE; fi")
    if rc == -1:
        return "host_unreachable", None, {}
    p = out.strip()
    if p == "NONE" or not p:
        return "fail", None, {"detail": "no_chroma_dir"}
    return "ok", p, {}


def probe_ollama_api_endpoint(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "curl -sf -m 5 http://localhost:11434/api/tags > /dev/null && echo OK || echo FAIL")
    if rc == -1:
        return "host_unreachable", None, {}
    if "OK" in out:
        return "ok", "http://localhost:11434", {}
    return "fail", "http://localhost:11434", {}


def probe_onepassword_agent_socket(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "test -S ~/.1password/agent.sock && echo PRESENT || echo ABSENT")
    if rc == -1:
        return "host_unreachable", None, {}
    if "PRESENT" in out:
        return "ok", "present", {}
    return "fail", "absent", {}


def probe_cloudflarewarp_dns(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    h = host or _local_hostname()
    rc, out, _ = _ssh_run(h, "warp-cli --accept-tos status 2>/dev/null | grep -E '^Status|^Account' | head -2")
    if rc == -1:
        return "host_unreachable", None, {}
    if not out.strip():
        return "fail", None, {"detail": "warp_cli_not_responsive"}
    return "ok", out.strip().replace("\n", " | "), {}


def probe_chromadb_doc_count(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    # Local probe only — chroma collection lives on the host running aho.
    project = os.environ.get("AHO_PROJECT", "ahomw")
    try:
        # Import in function to avoid hard dependency at module load.
        from aho.rag import collection_count
        n = collection_count(project)
        if n > 0:
            return "ok", n, {"project": project}
        return "fail", n, {"project": project, "detail": "collection_empty"}
    except Exception as exc:  # noqa: BLE001
        return "fail", None, {"project": project, "detail": f"{type(exc).__name__}:{exc}"}


def probe_checkpoint_mtime(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    # Local probe — check the canonical-root .aho-checkpoint.json mtime.
    root = Path(__file__).resolve().parents[2]  # <root>/src/aho/ → <root>
    ckpt = root / ".aho-checkpoint.json"
    if not ckpt.exists():
        return "fail", None, {"detail": "checkpoint_absent"}
    try:
        mtime = ckpt.stat().st_mtime
        age_s = time.time() - mtime
        return "ok", int(age_s), {"path": str(ckpt), "mtime_epoch": mtime}
    except OSError as exc:
        return "fail", None, {"detail": str(exc)}


def probe_sys_path_clean(host: Optional[str] = None) -> Tuple[str, Any, Dict[str, Any]]:
    # Local probe — detect a legacy pre-migration path entry in sys.path. The
    # marker is configurable per deployment via AHO_SYS_PATH_LEGACY_MARKER;
    # default catches the common "/dev/projects/aho/src" editable-install drift.
    legacy_marker = os.environ.get(
        "AHO_SYS_PATH_LEGACY_MARKER", "/dev/projects/aho/src"
    )
    hits = [p for p in sys.path if legacy_marker in p]
    if hits:
        return "fail", hits, {"detail": "legacy_path_in_sys_path"}
    return "ok", "clean", {}


PROBE_REGISTRY: Dict[str, Callable[..., Tuple[str, Any, Dict[str, Any]]]] = {
    "tailnet_domain": probe_tailnet_domain,
    "otel_collector_endpoint": probe_otel_collector_endpoint,
    "image_fqdn": probe_image_fqdn,
    "ssh_host_keys": probe_ssh_host_keys,
    "podman_version": probe_podman_version,
    "broker_socket": probe_broker_socket,
    "chromadb_mount_path": probe_chromadb_mount_path,
    "ollama_api_endpoint": probe_ollama_api_endpoint,
    "onepassword_agent_socket": probe_onepassword_agent_socket,
    "cloudflarewarp_dns": probe_cloudflarewarp_dns,
    "chromadb_doc_count": probe_chromadb_doc_count,
    "checkpoint_mtime": probe_checkpoint_mtime,
    "sys_path_clean": probe_sys_path_clean,
}

# Facts that are local-only (cannot meaningfully be remoted).
LOCAL_ONLY_FACTS = {
    "chromadb_doc_count",
    "checkpoint_mtime",
    "sys_path_clean",
}


def probe_one(fact_id: str, host: Optional[str] = None) -> Dict[str, Any]:
    """Run a single probe and record it. Returns the resulting record summary."""
    if fact_id not in PROBE_REGISTRY:
        raise ValueError(f"unknown fact_id: {fact_id}")
    if fact_id in LOCAL_ONLY_FACTS:
        host = None  # force local
    fn = PROBE_REGISTRY[fact_id]
    t0 = time.monotonic()
    outcome, value, extra = fn(host=host)
    duration_ms = int((time.monotonic() - t0) * 1000)
    rec = record_observable(
        fact_id,
        host=host or _local_hostname(),
        probe_outcome=outcome,
        value_observed=value,
        probe_command=f"probe_{fact_id}(host={host or 'local'})",
        duration_ms=duration_ms,
        extra=extra,
    )
    return {
        "fact_id": rec.fact_id,
        "host": rec.host,
        "outcome": rec.probe_outcome,
        "value": rec.value_observed,
        "duration_ms": rec.duration_ms,
        "extra": rec.extra,
    }


def probe_all(hosts: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Probe all 13 facts. For each non-local-only fact, probe on each host."""
    hosts = hosts or HOSTS_DEFAULT
    results: List[Dict[str, Any]] = []
    for fact_id in PROBE_REGISTRY:
        if fact_id in LOCAL_ONLY_FACTS:
            results.append(probe_one(fact_id))
        else:
            for h in hosts:
                results.append(probe_one(fact_id, host=h))
    return results


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="aho substrate-freshness probe set")
    ap.add_argument("--fact", help="Probe one fact only by id (default: all 13)")
    ap.add_argument("--host", help="Probe one host only (default: $AHO_PROBE_HOSTS or local hostname)")
    ap.add_argument("--summary", action="store_true", help="Plain summary instead of JSON list")
    args = ap.parse_args(argv)

    if args.fact:
        out = [probe_one(args.fact, host=args.host)]
    else:
        hosts = [args.host] if args.host else None
        out = probe_all(hosts=hosts)

    if args.summary:
        n_ok = sum(1 for r in out if r["outcome"] == "ok")
        n_fail = sum(1 for r in out if r["outcome"] == "fail")
        n_unr = sum(1 for r in out if r["outcome"] == "host_unreachable")
        print(f"{len(out)} probes: ok={n_ok}, fail={n_fail}, host_unreachable={n_unr}")
        for r in out:
            tag = {"ok": "·", "fail": "X", "host_unreachable": "~"}.get(r["outcome"], "?")
            v = r["value"] if r["value"] is not None else "—"
            print(f"  {tag} {r['fact_id']:30s} host={r['host']:8s} value={v}")
    else:
        print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
