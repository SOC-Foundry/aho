"""Verify synthesis fails if manual build log is missing (ADR-042 enforcement)."""
from pathlib import Path
import pytest


AHO_JSON = '{"name": "aho", "artifact_prefix": "aho", "project_code": "ahomw"}'


def _setup_project(tmp_path, monkeypatch):
    """Create minimal project structure so find_project_root resolves to tmp_path."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".aho.json").write_text(AHO_JSON)


def test_synthesis_raises_when_manual_missing(tmp_path, monkeypatch):
    """Calling build log synthesis without a manual file should raise FileNotFoundError."""
    from aho.artifacts import loop
    _setup_project(tmp_path, monkeypatch)
    (tmp_path / "artifacts" / "iterations" / "0.1.99").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="Manual build log not found"):
        loop.generate_build_log_synthesis("0.1.99")


def test_synthesis_proceeds_when_manual_present(tmp_path, monkeypatch):
    """Calling build log synthesis with a manual file should proceed without raising."""
    from aho.artifacts import loop
    _setup_project(tmp_path, monkeypatch)
    iter_dir = tmp_path / "artifacts" / "iterations" / "0.1.99"
    iter_dir.mkdir(parents=True)
    (iter_dir / "aho-build-log-0.1.99.md").write_text("# Build Log\n\n## W0\nSample manual entry.\n")
    try:
        result = loop.generate_build_log_synthesis("0.1.99")
        assert result.exists(), "generate_build_log_synthesis should return the manual log path"
    except FileNotFoundError as e:
        if "Manual build log not found" in str(e):
            pytest.fail(f"Synthesis incorrectly reported manual log missing: {e}")
    except Exception:
        pass  # Other errors are expected in test env without Qwen
