"""Tests for MCP smoke infrastructure (W8 Part B).

3+ cases: readiness doc exists, protocol_smoke column, smoke data exists.
"""
from pathlib import Path


def test_mcp_readiness_doc_exists():
    """mcp-readiness.md exists in harness."""
    p = Path("artifacts/harness/mcp-readiness.md")
    assert p.exists(), "mcp-readiness.md missing"


def test_mcp_readiness_has_protocol_smoke_column():
    """mcp-readiness.md contains protocol_smoke column."""
    content = Path("artifacts/harness/mcp-readiness.md").read_text()
    assert "protocol_smoke" in content


def test_mcp_readiness_lists_all_servers():
    """mcp-readiness.md lists at least 9 MCP servers."""
    content = Path("artifacts/harness/mcp-readiness.md").read_text()
    # Count table rows (lines starting with | that aren't headers)
    rows = [l for l in content.splitlines()
            if l.strip().startswith("|") and "---" not in l and "Server" not in l]
    assert len(rows) >= 9, f"Only {len(rows)} server rows found"


def test_mcp_smoke_data_source_exists():
    """data/mcp_readiness.json exists as smoke data source."""
    assert Path("data/mcp_readiness.json").exists()
