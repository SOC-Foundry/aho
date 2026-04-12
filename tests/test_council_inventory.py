import pytest
from aho.council.inventory import inventory, CouncilMember

def test_inventory_returns_min_members():
    members = inventory()
    assert len(members) >= 7

def test_inventory_members_have_required_fields():
    members = inventory()
    for member in members:
        assert isinstance(member, CouncilMember)
        assert member.name
        assert member.kind
        assert member.declared_capability
        assert member.config_source
        assert member.status

def test_inventory_status_defaults_to_unknown():
    members = inventory()
    for member in members:
        assert member.status == "unknown"

def test_inventory_config_source_exists():
    import os
    members = inventory()
    for member in members:
        assert os.path.exists(member.config_source), f"Source {member.config_source} does not exist"
