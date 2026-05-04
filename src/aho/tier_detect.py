"""tier_detect — VRAM-based tier classification for the containerized harness.

Probes nvidia-smi at startup, classifies host as base / partial / full per
ADR 0007 thresholds (<12GB, 12-32GB, >=32GB). Honours AHO_TIER override env
for testing. Writes classification to a runtime marker file (default
/var/run/aho/tier) so downstream consumers can read it without re-probing.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal, Optional

Tier = Literal["base", "partial", "full"]

THRESHOLD_PARTIAL_MB = 12_000
THRESHOLD_FULL_MB = 32_000


class TierDetectError(RuntimeError):
    pass


def probe_vram_mb() -> Optional[int]:
    """Return total VRAM in MB on the first GPU, or None if no GPU is visible."""
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    first_line = result.stdout.strip().splitlines()
    if not first_line:
        return None
    raw = first_line[0].strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise TierDetectError(f"nvidia-smi returned non-integer VRAM: {raw!r}") from exc


def classify(vram_mb: Optional[int]) -> Tier:
    """Apply ADR 0007 thresholds. None → base (no GPU = base by definition)."""
    if vram_mb is None or vram_mb < THRESHOLD_PARTIAL_MB:
        return "base"
    if vram_mb < THRESHOLD_FULL_MB:
        return "partial"
    return "full"


def detect_tier() -> Tier:
    """Public entry: env override beats probe; otherwise classify VRAM."""
    override = os.environ.get("AHO_TIER")
    if override:
        if override not in ("base", "partial", "full"):
            raise TierDetectError(
                f"AHO_TIER={override!r} not one of base/partial/full"
            )
        return override  # type: ignore[return-value]
    return classify(probe_vram_mb())


def tier_file_path() -> Path:
    return Path(os.environ.get("AHO_TIER_FILE", "/var/run/aho/tier"))


def write_tier_file(tier: Tier, path: Optional[Path] = None) -> Path:
    target = path or tier_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{tier}\n")
    return target


def read_tier_file(path: Optional[Path] = None) -> Optional[Tier]:
    target = path or tier_file_path()
    if not target.exists():
        return None
    raw = target.read_text().strip()
    if raw not in ("base", "partial", "full"):
        raise TierDetectError(f"tier marker file {target} has invalid contents: {raw!r}")
    return raw  # type: ignore[return-value]


def detect_and_persist() -> Tier:
    """Detect tier, write marker file, emit OTEL span with aho.tier attr,
    return tier.
    """
    tier = detect_tier()
    write_tier_file(tier)
    _emit_tier_span(tier)
    return tier


def _emit_tier_span(tier: Tier) -> None:
    """Emit an OTEL span carrying aho.tier as a span attribute.

    Resource-attribute propagation lives in a future iteration's harness
    OTEL init refactor; the W1 bar is that the attribute reaches a span.
    """
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("aho.tier_detect")
        with tracer.start_as_current_span("aho.tier_detect") as span:
            span.set_attribute("aho.tier", tier)
    except Exception:
        # OTEL unavailable / not configured — soft fail; the marker file is
        # the durable record.
        pass
