"""Verify workstream summary table populates agent from IAO_EXECUTOR when checkpoint is empty."""
import os
import pytest


def test_agent_from_env_var(monkeypatch):
    monkeypatch.setenv("IAO_EXECUTOR", "gemini-cli")
    from aho.feedback.run import build_workstream_summary

    # Minimal checkpoint with no per-workstream agent fields
    checkpoint = {
        "iteration": "0.1.8",
        "workstreams": {
            "W0": {"status": "complete"},
            "W1": {"status": "complete"},
        },
    }
    rows = build_workstream_summary(checkpoint)
    for row in rows:
        assert row.get("agent") != "unknown", \
            f"workstream {row.get('id')} has unknown agent; expected gemini-cli"
        assert row["agent"] == "gemini-cli"


def test_agent_from_checkpoint_preferred(monkeypatch):
    monkeypatch.setenv("IAO_EXECUTOR", "gemini-cli")
    from aho.feedback.run import build_workstream_summary

    checkpoint = {
        "iteration": "0.1.8",
        "workstreams": {
            "W0": {"status": "complete", "agent": "claude-code"},
        },
    }
    rows = build_workstream_summary(checkpoint)
    w0 = next((r for r in rows if r.get("id") == "W0"), None)
    assert w0 is not None
    assert w0["agent"] == "claude-code", \
        f"expected checkpoint value claude-code, got {w0['agent']}"


def test_no_unknown_agents_with_env_set(monkeypatch):
    monkeypatch.setenv("IAO_EXECUTOR", "claude-code")
    from aho.feedback.run import build_workstream_summary

    # Simulate mixed checkpoint: some with agent, some without
    checkpoint = {
        "iteration": "0.1.8",
        "workstreams": {
            "W0": {"status": "complete", "agent": "gemini-cli"},
            "W1": {"status": "complete"},
            "W2": {"status": "complete", "agent": None},
            "W3": {"status": "complete", "executor": "gemini-cli"},
        },
    }
    rows = build_workstream_summary(checkpoint)
    for row in rows:
        assert row["agent"] != "unknown", \
            f"workstream {row['id']} has unknown agent"
