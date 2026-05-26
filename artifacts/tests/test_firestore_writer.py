"""test_firestore_writer.py - W2 D4 of 0.3.1.

Tests aho.firestore_writer:
- Config resolution from env (required fields, emulator vs SA-key modes)
- Cross-tenant write guard (caller tenant_id must match env)
- Indicator-field t_any_* convention enforcement
- Payload construction (discriminator + provenance + indicator fields)
- Idempotency (set overwrite keyed on document_id)
- created vs updated operation detection

Backend-level coverage uses an in-memory fake client injected via the
`client=` parameter, so these run without the Firestore emulator (which needs
a JRE not present on every host). A real-emulator integration test is included
but skips unless FIRESTORE_EMULATOR_HOST is set (Track B + tooling gate).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


# --- in-memory fake firestore client -------------------------------------

class _FakeDocSnapshot:
    def __init__(self, exists: bool, data: dict | None):
        self.exists = exists
        self._data = data or {}

    def to_dict(self):
        return dict(self._data)


class _FakeDocRef:
    def __init__(self, store: dict, doc_id: str):
        self._store = store
        self._doc_id = doc_id

    def get(self):
        if self._doc_id in self._store:
            return _FakeDocSnapshot(True, self._store[self._doc_id])
        return _FakeDocSnapshot(False, None)

    def set(self, payload):
        # full overwrite, mirroring firestore set() default behavior
        self._store[self._doc_id] = dict(payload)


class _FakeCollection:
    def __init__(self, store: dict):
        self._store = store

    def document(self, doc_id: str):
        return _FakeDocRef(self._store, doc_id)


class FakeFirestoreClient:
    """Minimal in-memory stand-in for google.cloud.firestore.Client."""

    def __init__(self):
        self._collections: dict[str, dict] = {}

    def collection(self, name: str):
        self._collections.setdefault(name, {})
        return _FakeCollection(self._collections[name])

    def dump(self, collection: str) -> dict:
        return dict(self._collections.get(collection, {}))


@pytest.fixture
def tachtech_env(monkeypatch):
    """Minimal valid tenant env in emulator-style (no SA key required)."""
    monkeypatch.setenv("AHO_TENANT_ID", "testtenant")
    monkeypatch.setenv("AHO_TENANT_FIRESTORE_PROJECT", "test-project-id")
    monkeypatch.setenv("AHO_TENANT_FIRESTORE_DATABASE", "testdb")
    monkeypatch.setenv("AHO_TENANT_FIRESTORE_COLLECTION", "t_log")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    # ensure no SA key requirement triggers
    monkeypatch.delenv("AHO_TENANT_FIRESTORE_SERVICE_ACCOUNT_KEY_PATH", raising=False)


def test_config_requires_tenant_id(monkeypatch):
    from aho.firestore_writer import resolve_config, FirestoreWriterConfigError
    monkeypatch.delenv("AHO_TENANT_ID", raising=False)
    monkeypatch.setenv("AHO_TENANT_FIRESTORE_PROJECT", "p")
    with pytest.raises(FirestoreWriterConfigError):
        resolve_config()


def test_config_requires_project(monkeypatch):
    from aho.firestore_writer import resolve_config, FirestoreWriterConfigError
    monkeypatch.setenv("AHO_TENANT_ID", "t")
    monkeypatch.delenv("AHO_TENANT_FIRESTORE_PROJECT", raising=False)
    with pytest.raises(FirestoreWriterConfigError):
        resolve_config()


def test_config_requires_sa_key_when_not_emulator(monkeypatch):
    from aho.firestore_writer import resolve_config, FirestoreWriterConfigError
    monkeypatch.setenv("AHO_TENANT_ID", "t")
    monkeypatch.setenv("AHO_TENANT_FIRESTORE_PROJECT", "p")
    monkeypatch.delenv("FIRESTORE_EMULATOR_HOST", raising=False)
    monkeypatch.delenv("AHO_TENANT_FIRESTORE_SERVICE_ACCOUNT_KEY_PATH", raising=False)
    with pytest.raises(FirestoreWriterConfigError):
        resolve_config()


def test_emulator_mode_no_sa_key_ok(tachtech_env):
    from aho.firestore_writer import resolve_config
    cfg = resolve_config()
    assert cfg.tenant_id == "testtenant"
    assert cfg.project == "test-project-id"
    assert cfg.database == "testdb"
    assert cfg.collection == "t_log"
    assert cfg.emulator_host == "localhost:8080"


def test_write_creates_then_updates(tachtech_env):
    from aho.firestore_writer import write_or_update
    fake = FakeFirestoreClient()
    r1 = write_or_update(
        "testtenant", "gotcha", "F-0.3.1-W2-TEST",
        {"title": "test gotcha", "severity": "info"},
        {"t_any_iteration": "0.3.1", "t_any_workstream": "W2"},
        client=fake,
    )
    assert r1.operation == "created"
    assert r1.collection == "t_log"
    assert r1.document_id == "F-0.3.1-W2-TEST"
    # second write to same doc id -> updated
    r2 = write_or_update(
        "testtenant", "gotcha", "F-0.3.1-W2-TEST",
        {"title": "test gotcha", "severity": "info"},
        {"t_any_iteration": "0.3.1", "t_any_workstream": "W2"},
        client=fake,
    )
    assert r2.operation == "updated"


def test_payload_has_discriminator_and_provenance(tachtech_env):
    from aho.firestore_writer import write_or_update
    fake = FakeFirestoreClient()
    write_or_update(
        "testtenant", "audit_disposition", "W2-D4-DOC",
        {"disposition": "pass_with_findings"},
        {"t_any_iteration": "0.3.1"},
        client=fake,
    )
    stored = fake.dump("t_log")["W2-D4-DOC"]
    assert stored["t_log_type"] == "audit_disposition"
    assert stored["t_log_source"] == "aho"
    assert stored["document_id"] == "W2-D4-DOC"
    assert stored["t_any_tenant_id"] == "testtenant"
    assert stored["t_any_iteration"] == "0.3.1"
    assert "t_any_written_utc" in stored
    assert stored["disposition"] == "pass_with_findings"


def test_cross_tenant_write_refused(tachtech_env):
    from aho.firestore_writer import write_or_update, FirestoreWriterConfigError
    fake = FakeFirestoreClient()
    # caller passes a tenant_id different from env AHO_TENANT_ID
    with pytest.raises(FirestoreWriterConfigError):
        write_or_update(
            "some-other-tenant", "gotcha", "X",
            {"a": 1}, {"t_any_x": "y"}, client=fake,
        )


def test_indicator_field_convention_enforced(tachtech_env):
    from aho.firestore_writer import write_or_update, FirestoreWriterConfigError
    fake = FakeFirestoreClient()
    with pytest.raises(FirestoreWriterConfigError):
        write_or_update(
            "testtenant", "gotcha", "X",
            {"a": 1},
            {"iteration": "0.3.1"},  # missing t_any_ prefix
            client=fake,
        )


def test_idempotency_identical_state(tachtech_env):
    from aho.firestore_writer import write_or_update
    fake = FakeFirestoreClient()
    args = ("testtenant", "telemetry_summary", "SUMMARY-1",
            {"count": 42}, {"t_any_iteration": "0.3.1"})
    write_or_update(*args, client=fake)
    first = dict(fake.dump("t_log")["SUMMARY-1"])
    write_or_update(*args, client=fake)
    second = dict(fake.dump("t_log")["SUMMARY-1"])
    # all fields except the write timestamp must be identical
    first.pop("t_any_written_utc", None)
    second.pop("t_any_written_utc", None)
    assert first == second


@pytest.mark.skipif(
    not os.environ.get("FIRESTORE_EMULATOR_HOST_LIVE"),
    reason="real Firestore emulator integration gates on JRE + emulator running "
           "(set FIRESTORE_EMULATOR_HOST_LIVE + FIRESTORE_EMULATOR_HOST to run)",
)
def test_real_emulator_roundtrip(tachtech_env):
    from aho.firestore_writer import write_or_update
    r = write_or_update(
        "testtenant", "schema_marker", "_it_test",
        {"hello": "world"}, {"t_any_iteration": "0.3.1"},
    )
    assert r.operation in ("created", "updated")


# --- D5 bootstrap coverage ------------------------------------------------

def test_bootstrap_dry_run_plans_six_writes():
    from aho.firestore_writer.bootstrap import bootstrap
    result = bootstrap(dry_run=True)
    assert result["mode"] == "dry_run"
    assert result["planned_write_count"] == 6  # 1 marker + 5 schema defs
    assert "_schema_v1" in result["documents"]
    assert "_schema_def_gotcha" in result["documents"]


def test_bootstrap_execute_with_fake_client(tachtech_env):
    from aho.firestore_writer.bootstrap import bootstrap
    fake = FakeFirestoreClient()
    result = bootstrap(dry_run=False, client=fake)
    assert result["mode"] == "execute"
    assert result["written_count"] == 6
    stored = fake.dump("t_log")
    assert "_schema_v1" in stored
    assert stored["_schema_v1"]["t_log_type"] == "schema_marker"
    assert stored["_schema_def_gotcha"]["defines_log_type"] == "gotcha"


def test_bootstrap_idempotent(tachtech_env):
    from aho.firestore_writer.bootstrap import bootstrap
    fake = FakeFirestoreClient()
    bootstrap(dry_run=False, client=fake)
    first = {k: dict(v) for k, v in fake.dump("t_log").items()}
    bootstrap(dry_run=False, client=fake)
    second = {k: dict(v) for k, v in fake.dump("t_log").items()}
    assert set(first.keys()) == set(second.keys())  # no new docs on re-run
    # field parity modulo write timestamp
    for k in first:
        f = {kk: vv for kk, vv in first[k].items() if kk != "t_any_written_utc"}
        s = {kk: vv for kk, vv in second[k].items() if kk != "t_any_written_utc"}
        assert f == s
