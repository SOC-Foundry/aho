import re

with open("artifacts/tests/test_dashboard_aggregator.py", "r") as f:
    content = f.read()

new_test = '''def test_trace_state_returns_last_20(project_root, monkeypatch):
    import aho.logger
    def mock_event_log_path():
        return project_root / "data" / "aho_event_log.jsonl"
    monkeypatch.setattr(aho.logger, "event_log_path", mock_event_log_path)
    
    from aho.dashboard.aggregator import _trace_state, _cache
    _cache["data"] = None
    traces = _trace_state()
    assert len(traces) == 20
    assert "24" in traces[0]["timestamp"]'''

old_test_pattern = r'def test_trace_state_returns_last_20\(project_root, monkeypatch\):\n(?:.*\n)*?    assert "24" in traces\[0\]\["timestamp"\]'

content = re.sub(old_test_pattern, new_test, content)

with open("artifacts/tests/test_dashboard_aggregator.py", "w") as f:
    f.write(content)
