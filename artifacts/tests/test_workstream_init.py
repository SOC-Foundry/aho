"""Tests for the workstream-init settings.json wrapper (0.2.17 W0 — F-W1-001).

The wrapper writes literal AHO_ITERATION + workstream values into the
.claude/settings.json env block's OTEL_RESOURCE_ATTRIBUTES csv string.
Other csv keys (service.name, aho.role, etc.) are preserved in order.
Idempotent — second invocation with same args returns False (no change).
"""
from __future__ import annotations

import json

import pytest

from aho.workstream_init import _rewrite_resource_attrs, init_settings_for_workstream


def test_rewrite_replaces_iteration_and_workstream_keeps_other_keys():
    attrs = (
        "service.name=claude-code,aho.iteration=0.2.16,aho.workstream=W4,aho.role=drafter"
    )
    out = _rewrite_resource_attrs(attrs, iteration="0.2.17", workstream_id="W0")
    parts = out.split(",")
    assert parts == [
        "service.name=claude-code",
        "aho.iteration=0.2.17",
        "aho.workstream=W0",
        "aho.role=drafter",
    ]


def test_rewrite_appends_missing_aho_keys():
    attrs = "service.name=claude-code,aho.role=drafter"
    out = _rewrite_resource_attrs(attrs, iteration="0.2.17", workstream_id="W2")
    parts = out.split(",")
    assert parts[0] == "service.name=claude-code"
    assert "aho.iteration=0.2.17" in parts
    assert "aho.workstream=W2" in parts
    assert "aho.role=drafter" in parts


def test_rewrite_handles_unexpanded_placeholder_residue():
    """The whole point of this wrapper: replace literal ${VAR} placeholders
    that Claude Code does not shell-expand. F-W1-001 closure surface."""
    attrs = (
        "service.name=claude-code,aho.iteration=${AHO_ITERATION},"
        "aho.workstream=${AHO_WORKSTREAM},aho.role=drafter"
    )
    out = _rewrite_resource_attrs(attrs, iteration="0.2.17", workstream_id="W3")
    assert "${AHO_ITERATION}" not in out
    assert "${AHO_WORKSTREAM}" not in out
    assert "aho.iteration=0.2.17" in out
    assert "aho.workstream=W3" in out


def test_init_settings_writes_and_idempotently_returns_false(tmp_path):
    settings = tmp_path / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(
        json.dumps({
            "env": {
                "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
                "OTEL_RESOURCE_ATTRIBUTES": (
                    "service.name=claude-code,aho.iteration=0.2.16,"
                    "aho.workstream=W4,aho.role=drafter"
                ),
            }
        }, indent=2) + "\n"
    )

    changed = init_settings_for_workstream(
        iteration="0.2.17",
        workstream_id="W0",
        settings_path=str(settings),
    )
    assert changed is True

    payload = json.loads(settings.read_text())
    attrs = payload["env"]["OTEL_RESOURCE_ATTRIBUTES"]
    assert "aho.iteration=0.2.17" in attrs
    assert "aho.workstream=W0" in attrs
    # Non-aho keys preserved
    assert payload["env"]["CLAUDE_CODE_ENABLE_TELEMETRY"] == "1"

    # Idempotent
    again = init_settings_for_workstream(
        iteration="0.2.17",
        workstream_id="W0",
        settings_path=str(settings),
    )
    assert again is False


def test_init_settings_raises_when_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        init_settings_for_workstream(
            iteration="0.2.17",
            workstream_id="W0",
            settings_path=str(tmp_path / "nope.json"),
        )


def test_init_settings_raises_on_malformed_env_block(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"env": ["not-a-dict"]}))
    with pytest.raises(ValueError):
        init_settings_for_workstream(
            iteration="0.2.17",
            workstream_id="W0",
            settings_path=str(settings),
        )
