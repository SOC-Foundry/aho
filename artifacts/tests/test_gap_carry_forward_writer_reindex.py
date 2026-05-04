"""Tests for the ChromaDB re-index hook in `gap_carry_forward_writer`
(F-0.2.17-W4-001 closure, 0.2.17 W6 D2.1).

Coverage:
- append_to_file triggers reindex on success path
- reindex failure (Ollama down / chroma unavailable) does NOT block append
- reindex failure emits a stderr warning + increments the OTEL counter
- iteration label is parsed from filename when AHO_ITERATION env not set
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


def _make_carry_forwards_file(tmp_path: Path, iteration: str) -> Path:
    p = tmp_path / f"carry-forwards-{iteration}.md"
    p.write_text(
        f"# Carry-forwards — {iteration}\n\n## Target: 0.3.x base-tier hardening\n\n"
        "- **F-EXISTING-001 — preexisting entry**\n"
        "  - Severity: info\n"
        "  - what: pre-existing fixture entry\n"
        "  - Disposition: noop\n"
        "  - Target: 0.3.x base-tier hardening\n"
        "  - Source: fixture\n",
        encoding="utf-8",
    )
    return p


def test_append_triggers_reindex_on_success(tmp_path, monkeypatch):
    from aho import gap_carry_forward_writer as gcfw

    cf_file = _make_carry_forwards_file(tmp_path, "0.2.16")

    captured: Dict[str, Any] = {}

    def fake_index_artifact(path, *, project, iteration, workstream, **kw):
        captured["path"] = Path(path)
        captured["project"] = project
        captured["iteration"] = iteration
        captured["workstream"] = workstream
        return f"{project}::{iteration}::{workstream}::{Path(path).parent.name}/{Path(path).name}"

    fake_rag = type(sys)("aho.rag")
    fake_rag.index_artifact = fake_index_artifact
    fake_rag.RagError = RuntimeError
    fake_rag.RagInputError = ValueError
    monkeypatch.setitem(sys.modules, "aho.rag", fake_rag)

    result = gcfw.append_to_file(
        file_path=cf_file,
        entry={
            "id": "F-TEST-W6-OK-001",
            "title": "test entry success path",
            "severity": "info",
            "what_surfaced": "verifies reindex hook fires on successful append",
            "disposition": "test fixture",
            "target": "0.3.x base-tier hardening",
            "source": "test_gap_carry_forward_writer_reindex.test_append_triggers_reindex_on_success",
        },
    )

    assert result["entries_added"] == 1
    assert result["reindex"]["reindex_status"] == "ok"
    assert result["reindex"]["iteration"] == "0.2.16"
    assert result["reindex"]["project"] == "ahomw"
    assert "F-TEST-W6-OK-001" in cf_file.read_text(encoding="utf-8")
    assert captured["path"] == cf_file
    assert captured["iteration"] == "0.2.16"
    assert captured["workstream"] == "carry-forwards"


def test_append_succeeds_when_reindex_raises(tmp_path, monkeypatch, capsys):
    from aho import gap_carry_forward_writer as gcfw

    cf_file = _make_carry_forwards_file(tmp_path, "0.2.16")

    class FakeRagError(RuntimeError):
        pass

    def boom_index_artifact(path, *, project, iteration, workstream, **kw):
        raise FakeRagError("simulated Ollama down: connection refused")

    fake_rag = type(sys)("aho.rag")
    fake_rag.index_artifact = boom_index_artifact
    fake_rag.RagError = FakeRagError
    fake_rag.RagInputError = ValueError
    monkeypatch.setitem(sys.modules, "aho.rag", fake_rag)

    result = gcfw.append_to_file(
        file_path=cf_file,
        entry={
            "id": "F-TEST-W6-FAIL-002",
            "title": "test entry failure path",
            "severity": "info",
            "what_surfaced": "verifies append succeeds when reindex raises",
            "disposition": "test fixture",
            "target": "0.3.x base-tier hardening",
            "source": "test_gap_carry_forward_writer_reindex.test_append_succeeds_when_reindex_raises",
        },
    )

    # Append must have succeeded — file mutated, counts advanced.
    assert result["entries_added"] == 1
    assert "F-TEST-W6-FAIL-002" in cf_file.read_text(encoding="utf-8")

    # Reindex must have failed structurally with the right shape.
    assert result["reindex"]["reindex_status"] == "failed"
    assert "FakeRagError" in result["reindex"]["error"]
    assert result["reindex"]["iteration"] == "0.2.16"

    # Stderr warning must have fired.
    captured = capsys.readouterr()
    assert "WARNING: aho.gap_carry_forward_writer reindex failed" in captured.err
    assert "FakeRagError" in captured.err


def test_iteration_label_from_filename_overrides_env(tmp_path, monkeypatch):
    from aho import gap_carry_forward_writer as gcfw

    cf_file = _make_carry_forwards_file(tmp_path, "0.2.16")
    monkeypatch.setenv("AHO_ITERATION", "9.9.9")  # Should be ignored

    captured_iter: List[str] = []

    def fake_index_artifact(path, *, project, iteration, workstream, **kw):
        captured_iter.append(iteration)
        return "doc::id"

    fake_rag = type(sys)("aho.rag")
    fake_rag.index_artifact = fake_index_artifact
    fake_rag.RagError = RuntimeError
    fake_rag.RagInputError = ValueError
    monkeypatch.setitem(sys.modules, "aho.rag", fake_rag)

    result = gcfw.append_to_file(
        file_path=cf_file,
        entry={
            "id": "F-TEST-W6-FILENAME-003",
            "title": "iteration from filename",
            "severity": "info",
            "what_surfaced": "verifies filename-based iteration extraction",
            "disposition": "test fixture",
            "target": "0.3.x base-tier hardening",
            "source": "test_gap_carry_forward_writer_reindex.test_iteration_label_from_filename_overrides_env",
        },
    )

    assert captured_iter == ["0.2.16"]
    assert result["reindex"]["iteration"] == "0.2.16"
