"""aho.firestore_writer - tenant-aware Firestore writer (0.3.1 W2 D4).

Public API:
    write_or_update(tenant_id, log_type, document_id, document_data, indicator_fields)
        -> WriteResult

Tenant routing is env-driven (AHO_TENANT_* + FIRESTORE_EMULATOR_HOST). No
tenant identifiers or project ids are hardcoded; configuration is the
boundary. See client.py for the full configuration contract.
"""
from aho.firestore_writer.client import (
    FirestoreWriterConfigError,
    FirestoreWriterError,
    TenantConfig,
    WriteResult,
    resolve_config,
    write_or_update,
)

__all__ = [
    "write_or_update",
    "WriteResult",
    "TenantConfig",
    "resolve_config",
    "FirestoreWriterConfigError",
    "FirestoreWriterError",
]
