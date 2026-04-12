"""Tests for pillars_present gate — §3 Trident verification.

Minimum 6 cases per W6 plan:
1. Valid Trident passes all checks
2. Missing heading fails
3. Missing mermaid fence fails
4. Missing graph BT fails
5. Missing classDef shaft fails
6. Missing edge arrows fails
"""
from aho.postflight.pillars_present import _check_trident


_VALID_TRIDENT = """
## §3 Trident

```mermaid
graph BT
    classDef shaft fill:#0D9488,stroke:#0D9488,color:#fff
    classDef prong fill:#161B22,stroke:#4ADE80,color:#4ADE80

    Shaft[0.2.11<br/>Theme]:::shaft
    P1[Prong 1]:::prong
    P2[Prong 2]:::prong

    P1 --> Shaft
    P2 --> Shaft
```

## §4 Non-goals
"""


def test_valid_trident_passes_all_checks():
    """Complete valid Trident passes all 6 checks."""
    checks = _check_trident(_VALID_TRIDENT)
    assert all(c.status == "ok" for c in checks), [f"{c.name}={c.status}" for c in checks if c.status != "ok"]
    assert len(checks) == 6


def test_missing_heading_fails():
    """No §3 Trident heading → heading check fails, rest skipped."""
    content = "## §2 Goals\n\nSome content\n\n## §4 Non-goals\n"
    checks = _check_trident(content)
    assert checks[0].name == "trident_heading"
    assert checks[0].status == "fail"
    assert "missing" in checks[0].message.lower()


def test_missing_mermaid_fence_fails():
    """§3 heading present but no mermaid fence."""
    content = "## §3 Trident\n\nJust text, no diagram.\n\n## §4 Non-goals\n"
    checks = _check_trident(content)
    mermaid_check = next(c for c in checks if c.name == "trident_mermaid_fence")
    assert mermaid_check.status == "fail"


def test_missing_graph_bt_fails():
    """Mermaid fence present but wrong direction."""
    content = """## §3 Trident

```mermaid
graph LR
    classDef shaft fill:#0D9488
    classDef prong fill:#161B22
    A --> B
```

## §4 Non-goals
"""
    checks = _check_trident(content)
    bt_check = next(c for c in checks if c.name == "trident_graph_bt")
    assert bt_check.status == "fail"
    assert "bottom-to-top" in bt_check.message.lower()


def test_missing_classdef_shaft_fails():
    """No classDef shaft."""
    content = """## §3 Trident

```mermaid
graph BT
    classDef prong fill:#161B22
    A --> B
```

## §4 Non-goals
"""
    checks = _check_trident(content)
    shaft_check = next(c for c in checks if c.name == "trident_classdef_shaft")
    assert shaft_check.status == "fail"


def test_missing_edges_fails():
    """No edge arrows."""
    content = """## §3 Trident

```mermaid
graph BT
    classDef shaft fill:#0D9488
    classDef prong fill:#161B22
    A:::shaft
    B:::prong
```

## §4 Non-goals
"""
    checks = _check_trident(content)
    edge_check = next(c for c in checks if c.name == "trident_edges")
    assert edge_check.status == "fail"


def test_gate_returns_gate_result_dict():
    """Full gate returns dict with status, message, checks."""
    from aho.postflight.pillars_present import check
    result = check()
    assert isinstance(result, dict)
    assert "status" in result
    assert "message" in result
    assert "checks" in result
    assert len(result["checks"]) >= 6


def test_real_design_doc_passes():
    """0.2.11 design doc passes all Trident checks."""
    from pathlib import Path
    design = Path("artifacts/iterations/0.2.11/aho-design-0.2.11.md")
    content = design.read_text()
    checks = _check_trident(content)
    assert all(c.status == "ok" for c in checks), [f"{c.name}={c.status}: {c.message}" for c in checks if c.status != "ok"]
