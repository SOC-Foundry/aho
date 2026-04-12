"""W8 acceptance: workstream_start sets in_progress in checkpoint."""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from aho.paths import find_project_root

root = find_project_root()
ckpt_path = root / ".aho-checkpoint.json"
orig = ckpt_path.read_text()

log_path = tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False)
log_path.close()
try:
    with patch("aho.workstream_events.LOG_PATH", log_path.name), \
         patch("aho.logger.LOG_PATH", log_path.name):
        from aho.workstream_events import emit_workstream_start
        emit_workstream_start("W_IP_CHECK")
    ckpt = json.loads(ckpt_path.read_text())
    assert ckpt["workstreams"].get("W_IP_CHECK") == "in_progress"
    print("ok")
finally:
    ckpt_path.write_text(orig)
    os.unlink(log_path.name)
