"""aho.firestore_writer.bootstrap - initial schema seed (0.3.1 W2 D5).

Writes initial schema markers to a tenant's canonical collection: a schema
version marker plus one schema-definition document per anticipated
`t_log_type`. Idempotent (keyed on document_id via write_or_update).

Execution gates on the tenant Firestore being live + the service-account key
materialized into the broker-retrieved path (Track B). `--dry-run` reports the
planned writes without touching any backend and runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from aho.firestore_writer.client import (
    resolve_config,
    write_or_update,
    FirestoreWriterConfigError,
)


# Minimum-viable t_log_type set + the t_any_* fields valid for each.
SCHEMA_DEFINITIONS: Dict[str, List[str]] = {
    "gotcha": ["t_any_iteration", "t_any_workstream", "t_any_severity", "t_any_gotcha_id"],
    "audit_disposition": ["t_any_iteration", "t_any_workstream", "t_any_disposition", "t_any_confidence"],
    "iteration_metadata": ["t_any_iteration", "t_any_status", "t_any_materiality_n"],
    "telemetry_summary": ["t_any_iteration", "t_any_metric_name", "t_any_window"],
    "substrate_observable": ["t_any_fact_id", "t_any_host", "t_any_probe_outcome"],
}

SCHEMA_VERSION = "1.0.0"


def planned_writes(iteration: str = "0.3.1", workstream: str = "W2") -> List[Dict[str, Any]]:
    """Return the list of documents the bootstrap will write (marker + defs).

    Payloads carry no wall-clock timestamp of their own - write provenance is
    captured by write_or_update's `t_any_written_utc` field. Keeping payloads
    timestamp-free makes the bootstrap idempotent: re-running produces
    identical document state (modulo the provenance timestamp).
    """
    writes: List[Dict[str, Any]] = []
    # schema version marker
    writes.append({
        "document_id": "_schema_v1",
        "log_type": "schema_marker",
        "document_data": {
            "schema_version": SCHEMA_VERSION,
            "log_types": sorted(SCHEMA_DEFINITIONS.keys()),
        },
        "indicator_fields": {
            "t_any_iteration": iteration,
            "t_any_workstream": workstream,
            "t_any_schema_version": SCHEMA_VERSION,
        },
    })
    # one schema_definition doc per t_log_type
    for log_type, fields in sorted(SCHEMA_DEFINITIONS.items()):
        writes.append({
            "document_id": f"_schema_def_{log_type}",
            "log_type": "schema_definition",
            "document_data": {
                "defines_log_type": log_type,
                "valid_indicator_fields": fields,
            },
            "indicator_fields": {
                "t_any_iteration": iteration,
                "t_any_workstream": workstream,
                "t_any_schema_version": SCHEMA_VERSION,
            },
        })
    return writes


def bootstrap(*, dry_run: bool = False, iteration: str = "0.3.1",
              workstream: str = "W2", client: Any = None) -> Dict[str, Any]:
    """Execute (or dry-run) the schema seed. Returns a summary dict."""
    writes = planned_writes(iteration=iteration, workstream=workstream)

    if dry_run:
        # Resolve config only to surface a clear message if env is incomplete,
        # but do not require a live backend.
        tenant = None
        try:
            cfg = resolve_config()
            tenant = cfg.tenant_id
        except FirestoreWriterConfigError as e:
            tenant = f"<unresolved: {e}>"
        return {
            "mode": "dry_run",
            "tenant": tenant,
            "planned_write_count": len(writes),
            "documents": [w["document_id"] for w in writes],
            "log_types_defined": sorted(SCHEMA_DEFINITIONS.keys()),
        }

    cfg = resolve_config()  # raises if env incomplete / backend unconfigured
    results = []
    for w in writes:
        r = write_or_update(
            cfg.tenant_id,
            w["log_type"],
            w["document_id"],
            w["document_data"],
            w["indicator_fields"],
            client=client,
        )
        results.append({"document_id": r.document_id, "operation": r.operation})
    return {
        "mode": "execute",
        "tenant": cfg.tenant_id,
        "project": cfg.project,
        "database": cfg.database,
        "collection": cfg.collection,
        "written_count": len(results),
        "results": results,
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Seed initial schema markers into the tenant's canonical Firestore collection. Closes 0.3.1 W2 D5."
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Report planned writes without touching any backend.")
    ap.add_argument("--iteration", default="0.3.1")
    ap.add_argument("--workstream", default="W2")
    ap.add_argument("--json", action="store_true", help="Emit result as JSON.")
    args = ap.parse_args(argv)

    try:
        result = bootstrap(dry_run=args.dry_run, iteration=args.iteration,
                           workstream=args.workstream)
    except FirestoreWriterConfigError as e:
        print(f"[aho-firestore-bootstrap] config/substrate not ready: {e}", file=sys.stderr)
        print("[aho-firestore-bootstrap] this is the Track B gate - tenant Firestore "
              "+ service-account key must be provisioned before execute.", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"aho-firestore-bootstrap ({result['mode']})  tenant={result.get('tenant')}")
        if result["mode"] == "dry_run":
            print(f"  planned writes: {result['planned_write_count']}")
            for d in result["documents"]:
                print(f"    - {d}")
        else:
            print(f"  project={result['project']} database={result['database']} collection={result['collection']}")
            print(f"  written: {result['written_count']}")
            for r in result["results"]:
                print(f"    {r['operation']:8s} {r['document_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
