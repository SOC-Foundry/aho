import re

with open("src/aho/acceptance.py", "r") as f:
    code = f.read()

# 1. Update imports
old_imports = """from dataclasses import dataclass, asdict
from pathlib import Path"""
new_imports = """from typing import Any
from dataclasses import dataclass
from pydantic import BaseModel, model_validator
from pathlib import Path"""
code = code.replace(old_imports, new_imports)

# 2. Update AcceptanceResult
old_class = """@dataclass
class AcceptanceResult:
    check_name: str
    passed: bool
    actual_exit: int
    actual_output: str
    matched: bool | None
    duration_seconds: float
    error: str | None = None"""

new_class = """class AcceptanceResult(BaseModel):
    check_name: str
    passed: bool
    actual_exit: int
    actual_output: str
    matched: bool | None
    duration_seconds: float
    error: str | None = None

    def __init__(self, *args, **kwargs):
        if args:
            fields = ["check_name", "passed", "actual_exit", "actual_output", "matched", "duration_seconds", "error"]
            for i, arg in enumerate(args):
                if i < len(fields):
                    kwargs[fields[i]] = arg
        super().__init__(**kwargs)

    @model_validator(mode="before")
    @classmethod
    def normalize_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "check_name" not in data and "name" in data:
                data["check_name"] = data.pop("name")
        return data"""
code = code.replace(old_class, new_class)

# 3. Update serialize_results
old_serialize = """def serialize_results(results: list[AcceptanceResult], path: str | Path) -> None:
    \"\"\"Write AcceptanceResult list to JSON file.\"\"\"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(r) for r in results]
    p.write_text(json.dumps(data, indent=2) + "\\n")"""

new_serialize = """def serialize_results(results: list[AcceptanceResult], path: str | Path) -> None:
    \"\"\"Write AcceptanceResult list to JSON file.\"\"\"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump() for r in results]
    p.write_text(json.dumps(data, indent=2) + "\\n")"""
code = code.replace(old_serialize, new_serialize)

# 4. Append baseline_regression_check
baseline_helper = """
def baseline_regression_check(pytest_cmd: str = "pytest artifacts/tests/ -q --tb=short") -> AcceptanceCheck:
    \"\"\"Factory returning an AcceptanceCheck that runs pytest and asserts zero NEW failures vs baseline.
    Reads test-baseline.json to ignore known regressions and logs fixed ones.
    \"\"\"
    script = f\"\"\"
import json, subprocess, re, sys, os
baseline_path = 'artifacts/harness/test-baseline.json'
baseline = set()
if os.path.exists(baseline_path):
    b_data = json.load(open(baseline_path))
    baseline = {{f.get('test_id') for f in b_data.get('baseline_failures', []) if f.get('test_id')}}

r = subprocess.run('{pytest_cmd}', shell=True, capture_output=True, text=True)
out = r.stdout + r.stderr
failed_matches = re.findall(r'^FAILED\\\\s+([^\\\\s]+)', out, re.MULTILINE)
current_failures = set(failed_matches)
new_failures = current_failures - baseline
fixed_failures = baseline - current_failures

if fixed_failures:
    print(f'Fixed baseline failures (consider removing from baseline): {{fixed_failures}}')

if new_failures:
    print(f'NEW regressions found: {{new_failures}}')
    sys.exit(1)

print('baseline-stable')
sys.exit(0)
\"\"\"
    import base64
    b64_script = base64.b64encode(script.encode('utf-8')).decode('utf-8')
    cmd = f"python -c \\\"import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))\\\""

    return AcceptanceCheck(
        name="baseline_regression_check",
        command=cmd,
        expected_exit=0,
        expected_pattern=r"baseline-stable",
        timeout_seconds=120
    )
"""
code += baseline_helper

with open("src/aho/acceptance.py", "w") as f:
    f.write(code)
