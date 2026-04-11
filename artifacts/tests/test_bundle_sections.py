"""Tests for bundle §24-§26 expansion (0.2.3 W4)."""
import pytest
from unittest.mock import patch


def test_bundle_spec_has_26_sections():
    from aho.bundle import BUNDLE_SPEC
    assert len(BUNDLE_SPEC) == 26
    assert BUNDLE_SPEC[-3].number == 24
    assert BUNDLE_SPEC[-3].title == "Infrastructure"
    assert BUNDLE_SPEC[-2].number == 25
    assert BUNDLE_SPEC[-2].title == "Harnesses"
    assert BUNDLE_SPEC[-1].number == 26
    assert BUNDLE_SPEC[-1].title == "Configuration"


def test_bundle_contains_infrastructure_section():
    from aho.bundle import build_bundle
    path = build_bundle("0.2.3")
    content = path.read_text()
    assert "## §24. Infrastructure" in content
    assert ".aho.json" in content


def test_bundle_contains_harnesses_section():
    from aho.bundle import build_bundle
    path = build_bundle("0.2.3")
    content = path.read_text()
    assert "## §25. Harnesses" in content
    assert "base.md" in content


def test_bundle_contains_configuration_section():
    from aho.bundle import build_bundle
    path = build_bundle("0.2.3")
    content = path.read_text()
    assert "## §26. Configuration" in content
    assert "components.yaml" in content
