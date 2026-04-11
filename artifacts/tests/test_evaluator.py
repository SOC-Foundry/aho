"""Test anti-hallucination evaluator against known-bad and known-good corpora."""
from pathlib import Path
import pytest

from aho.artifacts.evaluator import evaluate_text, extract_references
from aho.paths import find_project_root


PROJECT_ROOT = find_project_root()


def test_extract_references_finds_file_paths():
    text = "See src/iao/cli.py and artifacts/scripts/smoke_streaming_qwen.py for details."
    refs = extract_references(text)
    assert "src/iao/cli.py" in refs["file_paths"]
    # script_names might capture the .py part depending on regex
    assert any("smoke_streaming_qwen.py" in s for s in refs.get("script_names", []))


def test_retired_pillar_naming_caught_by_anti_hallucination():
    text = "Per ahomw-Pillar-1 (Trident) and ahomw-Pillar-7 we retry up to 3 times."
    result = evaluate_text(text, project_root=PROJECT_ROOT)
    error_text = " ".join(result["errors"]).lower()
    assert "ahomw-pillar-1" in error_text, "retired pillar naming not caught"
    assert "ahomw-pillar-7" in error_text, "retired pillar naming not caught"


def test_evaluate_rejects_hallucinated_0_1_4_design():
    path = PROJECT_ROOT / "artifacts" / "iterations" / "0.1.4" / "iao-design-0.1.4.md"
    if not path.exists():
        pytest.skip("0.1.4 design not present")
    text = path.read_text()
    result = evaluate_text(text, project_root=PROJECT_ROOT)
    # Reality check: 0.1.4 actually has MANY hallucinations (50+)
    assert result["severity"] == "reject"
    assert len(result["errors"]) > 10


def test_evaluate_rejects_0_1_5_design_hallucinations():
    path = PROJECT_ROOT / "artifacts" / "iterations" / "0.1.5" / "iao-design-0.1.5.md"
    if not path.exists():
        pytest.skip("0.1.5 design not present")
    text = path.read_text()
    result = evaluate_text(text, project_root=PROJECT_ROOT)
    # 0.1.5 has at least a few identified hallucinations
    assert result["severity"] in ("reject", "warn")
    error_text = " ".join(result["errors"]).lower()
    assert "query_registry" in error_text or "phase mismatch" in error_text
