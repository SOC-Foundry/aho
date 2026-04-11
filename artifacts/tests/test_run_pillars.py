"""Verify run.py reads the eleven pillars from base.md, not a hardcoded list."""
from pathlib import Path
import pytest


def test_get_pillars_returns_eleven():
    from aho.feedback.run import get_pillars
    pillars = get_pillars()
    assert len(pillars) == 11, f"expected 11 pillars, got {len(pillars)}"


def test_pillar_1_is_delegate():
    from aho.feedback.run import get_pillars
    pillars = get_pillars()
    assert "Delegate everything delegable" in pillars[0], \
        f"Pillar 1 does not contain Delegate everything delegable: {pillars[0][:80]}"


def test_pillar_11_is_human_holds_keys():
    from aho.feedback.run import get_pillars
    pillars = get_pillars()
    assert "human holds the keys" in pillars[10], \
        f"Pillar 11 does not contain human holds the keys: {pillars[10][:80]}"


def test_no_retired_naming_leaked():
    from aho.feedback.run import get_pillars
    pillars = get_pillars()
    for i, p in enumerate(pillars, 1):
        assert "ahomw-Pillar-" not in p, \
            f"retired naming leaked in pillar {i}: {p[:100]}"


def test_cache_returns_same_object():
    from aho.feedback.run import get_pillars
    a = get_pillars()
    b = get_pillars()
    assert a is b, "pillar cache not stable across calls"


def test_missing_base_md_raises():
    from aho.feedback.run import _load_pillars_from_base
    with pytest.raises(RuntimeError, match="base harness not found"):
        _load_pillars_from_base(Path("/nonexistent/base.md"))
