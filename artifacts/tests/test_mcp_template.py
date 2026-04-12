"""Tests for .mcp.json.tpl template substitution (0.2.9 W1)."""
import json
from pathlib import Path


def _get_template_path() -> Path:
    """Resolve .mcp.json.tpl from the repo root."""
    cur = Path(__file__).resolve().parent
    while cur != cur.parent:
        if (cur / ".aho.json").exists():
            return cur / ".mcp.json.tpl"
        cur = cur.parent
    raise FileNotFoundError("Could not find repo root")


def test_template_exists():
    tpl = _get_template_path()
    assert tpl.exists(), ".mcp.json.tpl must exist at repo root"


def test_template_is_valid_json_after_substitution():
    tpl = _get_template_path()
    content = tpl.read_text()
    replaced = content.replace("{{PROJECT_ROOT}}", "/tmp/fake/aho")
    parsed = json.loads(replaced)
    assert "mcpServers" in parsed


def test_template_has_placeholder():
    tpl = _get_template_path()
    content = tpl.read_text()
    assert "{{PROJECT_ROOT}}" in content, "Template must contain {{PROJECT_ROOT}} placeholder"


def test_template_no_hardcoded_home():
    tpl = _get_template_path()
    content = tpl.read_text()
    assert "/home/kthompson" not in content, "Template must not contain hardcoded home path"


def test_substitution_produces_correct_filesystem_args():
    tpl = _get_template_path()
    content = tpl.read_text()
    replaced = content.replace("{{PROJECT_ROOT}}", "/opt/aho-test")
    parsed = json.loads(replaced)
    fs_args = parsed["mcpServers"]["filesystem"]["args"]
    assert fs_args == ["/opt/aho-test"]


def test_idempotent_substitution_no_leftover_placeholders():
    tpl = _get_template_path()
    content = tpl.read_text()
    replaced = content.replace("{{PROJECT_ROOT}}", "/srv/aho")
    assert "{{" not in replaced, "No unreplaced placeholders should remain"
    assert "}}" not in replaced


def test_template_has_nine_servers():
    tpl = _get_template_path()
    content = tpl.read_text()
    replaced = content.replace("{{PROJECT_ROOT}}", "/tmp/aho")
    parsed = json.loads(replaced)
    assert len(parsed["mcpServers"]) == 9, f"Expected 9 MCP servers, got {len(parsed['mcpServers'])}"
