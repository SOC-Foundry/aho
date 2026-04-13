"""Integration test — cascade pipeline on dummy document (0.2.14 W1).

Runs end-to-end against Ollama with qwen3.5:9b.
Requires Ollama running locally with qwen3.5:9b available.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


DUMMY_DOC = """A web server has a memory leak in WebSocket handlers. The timeout default is 30s. Recommend increasing to 120s and adding a circuit breaker."""


@pytest.fixture
def integration_env(tmp_path):
    """Set up isolated environment for integration test."""
    log_file = tmp_path / "aho_event_log.jsonl"
    log_file.touch()

    doc_file = tmp_path / "dummy_doc.txt"
    doc_file.write_text(DUMMY_DOC)

    with patch("aho.logger.LOG_PATH", str(log_file)), \
         patch("aho.logger._ITERATION", "0.2.14"), \
         patch("aho.pipeline.orchestrator.log_event") as mock_log:
        yield tmp_path, doc_file, log_file, mock_log


def _ollama_available() -> bool:
    """Check if Ollama is running and qwen3.5:9b is available."""
    try:
        import urllib.request
        import json as _json
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read())
            models = [m.get("name", "") for m in data.get("models", [])]
            return any("qwen3.5" in m for m in models)
    except Exception:
        return False


@pytest.mark.skipif(
    not _ollama_available(),
    reason="Ollama not running or qwen3.5:9b not available"
)
def test_cascade_end_to_end(integration_env):
    """Full cascade on dummy document. All 5 stages must complete."""
    tmp_path, doc_file, log_file, mock_log = integration_env

    from aho.pipeline.schemas import RoleAssignment
    from aho.pipeline.orchestrator import run_cascade

    ra = RoleAssignment(
        indexer_in="qwen3.5:9b",
        producer="qwen3.5:9b",
        auditor="qwen3.5:9b",
        indexer_out="qwen3.5:9b",
        assessor="qwen3.5:9b",
    )

    output_dir = tmp_path / "run-output"
    trace = run_cascade(
        document_path=str(doc_file),
        role_assignment=ra,
        output_dir=str(output_dir),
        stage_timeout=300,
    )

    # All 5 stages completed
    assert len(trace.handoffs) == 5, f"Expected 5 handoffs, got {len(trace.handoffs)}"

    stages_seen = [h.stage for h in trace.handoffs]
    assert stages_seen == ["indexer_in", "producer", "auditor", "indexer_out", "assessor"]

    # Every stage produced non-null output
    for h in trace.handoffs:
        assert h.output_size_chars > 0, f"Stage {h.stage} produced no output"
        assert h.wall_clock_seconds > 0, f"Stage {h.stage} has zero wall clock"

    # Output artifacts written
    for stage in ["indexer_in", "producer", "auditor", "indexer_out", "assessor"]:
        stage_file = output_dir / f"{stage}.json"
        assert stage_file.exists(), f"Missing output artifact for {stage}"
        data = json.loads(stage_file.read_text())
        assert len(data["response"]) > 0, f"Empty response for {stage}"

    # Trace file written
    trace_file = output_dir / "trace.json"
    assert trace_file.exists()

    # Pipeline events emitted (10 = 5 dispatch + 5 complete)
    assert mock_log.call_count == 10, f"Expected 10 log events, got {mock_log.call_count}"

    # Total wall clock is reasonable
    assert trace.total_wall_clock_seconds > 0
