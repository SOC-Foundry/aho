"""aho.firestore_writer.client - tenant-aware Firestore writer (0.3.1 W2 D4).

Writes aho data (gotchas, audit dispositions, iteration metadata, telemetry
summaries, substrate observables) to a per-tenant Firestore database under a
single canonical collection keyed by a `t_log_type` discriminator and
`t_any_*` indicator fields.

Tenant routing is entirely env-driven - no tenant identifiers, project ids,
or database names are hardcoded in this module. The same build writes to the
internal tenant or any customer tenant purely by environment configuration.
This is the configuration-as-boundary property: tenant scoping lives in env,
not in code.

Configuration (all via environment):
    AHO_TENANT_ID                              tenant identifier (required)
    AHO_TENANT_FIRESTORE_PROJECT               GCP project id (required)
    AHO_TENANT_FIRESTORE_DATABASE              Firestore database id (default "(default)")
    AHO_TENANT_FIRESTORE_COLLECTION            canonical collection (default "t_log")
    AHO_TENANT_FIRESTORE_SERVICE_ACCOUNT_KEY_PATH  path to SA key json (broker-retrieved)
    FIRESTORE_EMULATOR_HOST                    if set, connect to the emulator (no creds)

Credential handling per ADR-0009: the service-account key path points at a
broker-retrieved file; the key is never committed to the repo. In emulator
mode (FIRESTORE_EMULATOR_HOST set), no credentials are required.

Idempotency: write_or_update keys on document_id and performs a full set()
(overwrite). Re-running with identical inputs produces identical document
state - no duplicates, no drift.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


CANONICAL_COLLECTION_DEFAULT = "t_log"
LOG_SOURCE = "aho"


class FirestoreWriterConfigError(RuntimeError):
    """Required tenant configuration is missing or inconsistent."""


class FirestoreWriterError(RuntimeError):
    """Write failed at the Firestore client layer."""


@dataclass
class TenantConfig:
    tenant_id: str
    project: str
    database: str
    collection: str
    service_account_key_path: Optional[str]
    emulator_host: Optional[str]


@dataclass
class WriteResult:
    document_id: str
    collection: str
    tenant_id: str
    log_type: str
    operation: str  # "created" | "updated"
    project: str
    database: str
    fields_written: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


def resolve_config() -> TenantConfig:
    """Read tenant routing from the environment. Raises FirestoreWriterConfigError
    if a required value is missing.
    """
    tenant_id = os.environ.get("AHO_TENANT_ID", "").strip()
    project = os.environ.get("AHO_TENANT_FIRESTORE_PROJECT", "").strip()
    database = os.environ.get("AHO_TENANT_FIRESTORE_DATABASE", "(default)").strip() or "(default)"
    collection = os.environ.get(
        "AHO_TENANT_FIRESTORE_COLLECTION", CANONICAL_COLLECTION_DEFAULT
    ).strip() or CANONICAL_COLLECTION_DEFAULT
    sa_key = os.environ.get("AHO_TENANT_FIRESTORE_SERVICE_ACCOUNT_KEY_PATH", "").strip() or None
    emulator = os.environ.get("FIRESTORE_EMULATOR_HOST", "").strip() or None

    if not tenant_id:
        raise FirestoreWriterConfigError("AHO_TENANT_ID is required")
    if not project:
        raise FirestoreWriterConfigError("AHO_TENANT_FIRESTORE_PROJECT is required")
    # In emulator mode, no service-account key is needed.
    if not emulator and not sa_key:
        raise FirestoreWriterConfigError(
            "AHO_TENANT_FIRESTORE_SERVICE_ACCOUNT_KEY_PATH is required "
            "when FIRESTORE_EMULATOR_HOST is not set"
        )
    if sa_key and not emulator and not os.path.isfile(sa_key):
        raise FirestoreWriterConfigError(
            f"service account key not found at {sa_key!r} "
            "(broker should materialize it before writes)"
        )
    return TenantConfig(
        tenant_id=tenant_id,
        project=project,
        database=database,
        collection=collection,
        service_account_key_path=sa_key,
        emulator_host=emulator,
    )


def _build_client(cfg: TenantConfig):
    """Construct a firestore.Client for the resolved tenant config.

    Imported lazily so the module imports cleanly on hosts without the
    google-cloud-firestore dependency (it is a substrate component installed
    per the corrected Pillar 11 scope).
    """
    try:
        from google.cloud import firestore
    except ImportError as exc:  # pragma: no cover - substrate dependency
        raise FirestoreWriterError(
            "google-cloud-firestore not importable; install via "
            "`pip install --user --break-system-packages google-cloud-firestore`"
        ) from exc

    kwargs: Dict[str, Any] = {"project": cfg.project}
    # firestore.Client honors the `database` kwarg in recent SDK versions.
    if cfg.database and cfg.database != "(default)":
        kwargs["database"] = cfg.database

    if cfg.emulator_host:
        # Emulator mode: the SDK reads FIRESTORE_EMULATOR_HOST itself and uses
        # anonymous credentials. No SA key required.
        return firestore.Client(**kwargs)

    if cfg.service_account_key_path:
        return firestore.Client.from_service_account_json(
            cfg.service_account_key_path, **kwargs
        )
    return firestore.Client(**kwargs)


def _validate_indicator_fields(indicator_fields: Dict[str, Any]) -> None:
    """All indicator fields must follow the t_any_* naming convention."""
    for k in indicator_fields:
        if not k.startswith("t_any_"):
            raise FirestoreWriterConfigError(
                f"indicator field {k!r} must use the t_any_* convention"
            )


def write_or_update(
    tenant_id: str,
    log_type: str,
    document_id: str,
    document_data: Dict[str, Any],
    indicator_fields: Optional[Dict[str, Any]] = None,
    *,
    client: Any = None,
) -> WriteResult:
    """Write or idempotently update one document in the tenant's canonical
    collection.

    The stored document is the merge of `document_data` plus discriminator +
    indicator + provenance fields:
        t_log_type      = log_type
        t_log_source    = "aho"
        document_id     = document_id
        t_any_*         = indicator_fields (validated to the t_any_ convention)
        t_any_tenant_id = tenant_id
        t_any_written_utc = ISO-8601 write timestamp

    Idempotent: keyed on document_id with a full set() overwrite. `client` may
    be injected for testing (emulator or mock); otherwise a client is built
    from the resolved tenant config.
    """
    if not isinstance(document_data, dict):
        raise FirestoreWriterConfigError("document_data must be a dict")
    indicator_fields = indicator_fields or {}
    _validate_indicator_fields(indicator_fields)

    cfg = resolve_config()
    # The caller-passed tenant_id must agree with the env-resolved tenant to
    # prevent cross-tenant writes from a mis-set caller argument.
    if tenant_id != cfg.tenant_id:
        raise FirestoreWriterConfigError(
            f"tenant_id argument {tenant_id!r} does not match env "
            f"AHO_TENANT_ID {cfg.tenant_id!r} - refusing cross-tenant write"
        )

    fs = client or _build_client(cfg)
    doc_ref = fs.collection(cfg.collection).document(document_id)

    existing = doc_ref.get()
    operation = "updated" if getattr(existing, "exists", False) else "created"

    payload: Dict[str, Any] = dict(document_data)
    payload["t_log_type"] = log_type
    payload["t_log_source"] = LOG_SOURCE
    payload["document_id"] = document_id
    payload["t_any_tenant_id"] = tenant_id
    payload["t_any_written_utc"] = datetime.now(timezone.utc).isoformat()
    for k, v in indicator_fields.items():
        payload[k] = v

    doc_ref.set(payload)  # full overwrite -> idempotent on identical inputs

    return WriteResult(
        document_id=document_id,
        collection=cfg.collection,
        tenant_id=tenant_id,
        log_type=log_type,
        operation=operation,
        project=cfg.project,
        database=cfg.database,
        fields_written=len(payload),
    )
