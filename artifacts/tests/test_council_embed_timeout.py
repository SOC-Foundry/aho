"""Locks in the AHO_COUNCIL_EMBED_TIMEOUT_S default and env-override behaviour.

0.2.18 W0 / F-0.2.17-W6-002: default raised 30 -> 120 to align with
triage / _client (also 120) and to stop spurious timeouts under
cold-start + concurrent embed load on NZXTcos 8GB VRAM substrate.

Plan-doc anticipated a "unit-test amendment" but no prior test existed
for embed timeout resolution; this file is the new lock-in.
"""
from __future__ import annotations

import os

import pytest

from aho.council import embed


def test_default_timeout_is_120_seconds():
    assert embed.DEFAULT_TIMEOUT_S == 120


def test_timeout_resolution_uses_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("AHO_COUNCIL_EMBED_TIMEOUT_S", raising=False)
    assert embed._timeout_s() == 120.0


def test_timeout_resolution_uses_env_when_set(monkeypatch):
    monkeypatch.setenv("AHO_COUNCIL_EMBED_TIMEOUT_S", "45")
    assert embed._timeout_s() == 45.0


def test_timeout_resolution_raises_on_unparseable_env(monkeypatch):
    monkeypatch.setenv("AHO_COUNCIL_EMBED_TIMEOUT_S", "not-a-float")
    with pytest.raises(embed.CouncilEmbedInputError):
        embed._timeout_s()
