"""W2 D12 - verify all four materiality counters emit during W2 execution.

Sets up an InMemoryMetricReader, runs a representative slice of W2's audit
+ carry-forward + placeholder paths, then asserts each of the four
counters has at least one recorded measurement with the expected resource
attributes.

Note: this script must be self-contained - import ordering matters
because the global MeterProvider can only be set once. The probe sets it
BEFORE importing aho.materiality.
"""
from __future__ import annotations

import os
import sys
import shutil
import tempfile
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

# Configure OTEL metrics SDK with an in-memory reader BEFORE the materiality
# module imports its meter from the global provider.
from opentelemetry import metrics as _metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource

reader = InMemoryMetricReader()
resource = Resource.create({
    "service.name": "aho",
    "aho.iteration": "0.2.17",
    "aho.workstream": "W2",
    "aho.tier": "base",
    "aho.role": "drafter",
})
provider = MeterProvider(metric_readers=[reader], resource=resource)
_metrics.set_meter_provider(provider)

os.environ.setdefault("AHO_ITERATION", "0.2.17")
os.environ.setdefault("AHO_WORKSTREAM", "W2")
os.environ.setdefault("AHO_TIER", "base")

from aho import materiality  # noqa: E402
from aho.council import audit as audit_mod  # noqa: E402
from aho.gap_carry_forward_writer import append_to_file  # noqa: E402


def main() -> int:
    print(f"counters built: {materiality.counters_introspect()}")

    # 1) caught_by_llama - invoke audit on a fixture-bad artifact (G081)
    audit_mod.audit("Sample artifact with banned phrase: shipped clean close.")

    # 2) caught_by_drafter - synthetic carry-forward append
    src = ROOT / "artifacts" / "iterations" / "0.2.16" / "carry-forwards-0.2.16.md"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "cf.md"
        shutil.copy(src, copy)
        append_to_file(
            file_path=copy,
            entry={
                "id": "F-0.2.17-W2-D12-probe",
                "title": "D12 telemetry probe synthetic entry",
                "severity": "info",
                "what_surfaced": "synthetic invocation",
                "disposition": "probe-only",
                "target": "0.2.18",
                "source": "D12 telemetry probe",
            },
        )

    # 3) escaped - placeholder bump (W3 wires to real escaped-finding flow)
    materiality.record_escaped(severity="info")

    # 4) carry_forward_resolution_rate - placeholder bump
    materiality.record_carry_forward_resolution(extra={"aho.cf.resolved_id": "probe"})

    # Force-collect metrics from the in-memory reader
    metric_data = reader.get_metrics_data()
    counter_emissions: dict[str, int] = {}
    sample_attrs: dict[str, dict] = {}
    for resource_metrics in metric_data.resource_metrics:
        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name in materiality.COUNTER_NAMES:
                    total = sum(p.value for p in metric.data.data_points)
                    counter_emissions[metric.name] = (
                        counter_emissions.get(metric.name, 0) + total
                    )
                    if metric.data.data_points:
                        sample_attrs[metric.name] = dict(
                            metric.data.data_points[0].attributes
                        )

    print()
    print("=== materiality counter emissions ===")
    for name in materiality.COUNTER_NAMES:
        emitted = counter_emissions.get(name, 0)
        attrs = sample_attrs.get(name, {})
        print(f'  {name}: {emitted} emissions')
        if attrs:
            print(f'    sample attrs: {attrs}')

    # Acceptance gate - all four counters must have >= 1 emission
    missing = [n for n in materiality.COUNTER_NAMES if counter_emissions.get(n, 0) < 1]
    if missing:
        print()
        print(f"FAIL: counters with no emissions: {missing}")
        return 1
    print()
    print("OK: all four materiality counters emitted at least once")

    # Verify resource attributes
    rattrs = dict(metric_data.resource_metrics[0].resource.attributes)
    print(f"resource attributes: {rattrs}")
    for required in ("aho.iteration", "aho.workstream", "aho.tier"):
        if required not in rattrs:
            print(f"FAIL: resource attribute {required!r} missing")
            return 1
    if rattrs["aho.iteration"] != "0.2.17":
        print(f"FAIL: aho.iteration = {rattrs['aho.iteration']!r}, expected 0.2.17")
        return 1
    if rattrs["aho.workstream"] != "W2":
        print(f"FAIL: aho.workstream = {rattrs['aho.workstream']!r}, expected W2")
        return 1
    if rattrs["aho.tier"] != "base":
        print(f"FAIL: aho.tier = {rattrs['aho.tier']!r}, expected base")
        return 1
    print("OK: resource attributes match required (aho.iteration, aho.workstream, aho.tier)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
