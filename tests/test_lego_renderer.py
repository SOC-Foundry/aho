import pytest
import xml.etree.ElementTree as ET
from aho.council.status import collect_status, CouncilStatus, CouncilMemberStatus
from aho.dashboard.lego.renderer import render_council_svg

@pytest.fixture
def empty_council():
    return CouncilStatus(
        members=[],
        ollama_models=[],
        nemoclaw_socket=None,
        recent_dispatches=[],
        g083_density={},
        health_score=0.0
    )

@pytest.fixture
def simple_council():
    m1 = CouncilMemberStatus(name="Qwen", kind="llm", declared_capability="test", config_source="test", status="operational")
    m2 = CouncilMemberStatus(name="GLM", kind="llm", declared_capability="test", config_source="test", status="gap: testing")
    m3 = CouncilMemberStatus(name="TestMCP", kind="mcp", declared_capability="test", config_source="test", status="unknown")
    
    return CouncilStatus(
        members=[m1, m2, m3],
        ollama_models=["Qwen"],
        nemoclaw_socket="/tmp/sock",
        recent_dispatches=[],
        g083_density={},
        health_score=50.0
    )

def test_svg_generation_empty(empty_council):
    svg = render_council_svg(empty_council)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "aho Council Operations" in svg

def test_svg_generation_with_data(simple_council):
    svg = render_council_svg(simple_council)
    assert "Qwen" in svg
    assert "GLM" in svg
    assert "TestMCP" in svg

def test_color_mapping(simple_council):
    svg = render_council_svg(simple_council)
    assert "#4ade80" in svg  # Operational green
    assert "#ef4444" in svg  # Gap red
    assert "#9ca3af" in svg  # Unknown gray

def test_figure_positioning(simple_council):
    svg = render_council_svg(simple_council)
    # Just checking some rectangles are rendered
    assert "<rect x=" in svg
    
def test_line_generation():
    status = collect_status()
    svg = render_council_svg(status)
    # Check if lines (paths) are present
    assert "<path d=" in svg
