"""W8 acceptance: schema v3 emit with efficacy fields."""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from aho.workstream_events import emit_workstream_complete

log_path = tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False)
log_path.close()
try:
    with patch("aho.workstream_events.LOG_PATH", log_path.name), \
         patch("aho.workstream_events._ITERATION", "0.2.11"), \
         patch("aho.logger.LOG_PATH", log_path.name), \
         patch("aho.logger._ITERATION", "0.2.11"):
        emit_workstream_complete(
            "W_V3_ACC", "pass",
            agents_involved=["claude-code"],
            token_count=50000,
            harness_contributions=["daemon_healthy"],
            ad_hoc_forensics_minutes=5,
        )
    events = [json.loads(l) for l in Path(log_path.name).read_text().splitlines() if l.strip()]
    ev = events[0]
    assert ev["schema_version"] == 3
    assert ev["agents_involved"] == ["claude-code"]
    assert ev["token_count"] == 50000
    assert ev["harness_contributions"] == ["daemon_healthy"]
    assert ev["ad_hoc_forensics_minutes"] == 5
    print("ok")
finally:
    os.unlink(log_path.name)
