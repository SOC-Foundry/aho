"""acceptance.py — AcceptanceCheck primitive for verifiable workstream completion.

Replaces prose acceptance claims with executable assertions. Each check
specifies a shell command, expected exit code, and optional stdout regex.
run_check() executes via subprocess and returns a typed result.

Introduced 0.2.11 W1 to structurally eliminate the "overstated completion"
failure mode identified in 0.2.10 forensic.
"""
import json
import re
import subprocess
import time
from typing import Any
from dataclasses import dataclass
from pydantic import BaseModel, model_validator
from pathlib import Path


@dataclass
class AcceptanceCheck:
    name: str
    command: str
    expected_exit: int = 0
    expected_pattern: str | None = None
    timeout_seconds: int = 30


class AcceptanceResult(BaseModel):
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
        return data


MAX_OUTPUT_BYTES = 4096


def run_check(check: AcceptanceCheck) -> AcceptanceResult:
    """Execute a single AcceptanceCheck and return the result."""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            check.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=check.timeout_seconds,
        )
        duration = time.monotonic() - start
        stdout = proc.stdout[:MAX_OUTPUT_BYTES] if proc.stdout else ""
        stderr = proc.stderr[:MAX_OUTPUT_BYTES] if proc.stderr else ""
        actual_output = stdout if stdout else stderr
        actual_exit = proc.returncode

        exit_ok = actual_exit == check.expected_exit

        if check.expected_pattern is not None:
            matched = bool(re.search(check.expected_pattern, stdout))
        else:
            matched = None

        passed = exit_ok and (matched is None or matched)

        return AcceptanceResult(
            check_name=check.name,
            passed=passed,
            actual_exit=actual_exit,
            actual_output=actual_output,
            matched=matched,
            duration_seconds=round(duration, 3),
        )

    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return AcceptanceResult(
            check_name=check.name,
            passed=False,
            actual_exit=-1,
            actual_output="",
            matched=None,
            duration_seconds=round(duration, 3),
            error="timeout",
        )

    except FileNotFoundError as e:
        duration = time.monotonic() - start
        return AcceptanceResult(
            check_name=check.name,
            passed=False,
            actual_exit=-1,
            actual_output="",
            matched=None,
            duration_seconds=round(duration, 3),
            error=f"command_not_found: {e}",
        )

    except Exception as e:
        duration = time.monotonic() - start
        return AcceptanceResult(
            check_name=check.name,
            passed=False,
            actual_exit=-1,
            actual_output="",
            matched=None,
            duration_seconds=round(duration, 3),
            error=str(e),
        )


def daemon_healthy(unit_name: str,
                   min_tasks: int = 2,
                   min_memory_mb: int = 20) -> AcceptanceCheck:
    """Factory returning an AcceptanceCheck that verifies a systemd --user unit
    is not in the inert-zombie state (active but not actually running).

    Parses `systemctl --user status <unit>` output for Tasks: and Memory: fields.
    Unit must be active, Tasks >= min_tasks, Memory >= min_memory_mb.
    """
    # Build a self-contained check command that parses systemctl status output
    cmd = (
        f"python -c \""
        f"import subprocess, re, sys; "
        f"r = subprocess.run(['systemctl', '--user', 'status', '{unit_name}'], "
        f"capture_output=True, text=True); "
        f"out = r.stdout + r.stderr; "
        f"active = 'Active: active (running)' in out; "
        f"tasks_m = re.search(r'Tasks:\\\\s+(\\\\d+)', out); "
        f"mem_m = re.search(r'Memory:\\\\s+([\\\\d.]+)(\\\\w)', out); "
        f"tasks = int(tasks_m.group(1)) if tasks_m else 0; "
        f"mem_val = float(mem_m.group(1)) if mem_m else 0; "
        f"mem_unit = mem_m.group(2) if mem_m else 'B'; "
        f"mem_mb = mem_val * 1024 if mem_unit == 'G' else mem_val if mem_unit == 'M' else mem_val / 1024; "
        f"ok = active and tasks >= {min_tasks} and mem_mb >= {min_memory_mb}; "
        f"print(f'active={{active}} tasks={{tasks}} mem_mb={{mem_mb:.1f}} ok={{ok}}'); "
        f"sys.exit(0 if ok else 1)\""
    )
    return AcceptanceCheck(
        name=f"daemon_healthy_{unit_name}",
        command=cmd,
        expected_exit=0,
        expected_pattern=r"ok=True",
    )


def serialize_results(results: list[AcceptanceResult], path: str | Path) -> None:
    """Write AcceptanceResult list to JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump() for r in results]
    p.write_text(json.dumps(data, indent=2) + "\n")

def baseline_regression_check(pytest_cmd: str = "pytest artifacts/tests/ -q --tb=short") -> AcceptanceCheck:
    """Factory returning an AcceptanceCheck that runs pytest and asserts zero NEW failures vs baseline.
    Reads test-baseline.json to ignore known regressions and logs fixed ones.
    """
    script = f"""
import json, subprocess, re, sys, os
baseline_path = 'artifacts/harness/test-baseline.json'
baseline = set()
if os.path.exists(baseline_path):
    b_data = json.load(open(baseline_path))
    baseline = {{f.get('test_id') for f in b_data.get('baseline_failures', []) if f.get('test_id')}}

r = subprocess.run('{pytest_cmd}', shell=True, capture_output=True, text=True)
out = r.stdout + r.stderr
failed_matches = re.findall(r'^FAILED\\s+([^ ]+)', out, re.MULTILINE)
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
"""
    import base64
    b64_script = base64.b64encode(script.encode('utf-8')).decode('utf-8')
    cmd = f"python -c \"import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))\""

    return AcceptanceCheck(
        name="baseline_regression_check",
        command=cmd,
        expected_exit=0,
        expected_pattern=r"baseline-stable",
        timeout_seconds=120
    )

def baseline_regression_check(pytest_cmd: str = "pytest artifacts/tests/ -q --tb=short") -> AcceptanceCheck:
    """Factory returning an AcceptanceCheck that runs pytest and asserts zero NEW failures vs baseline.
    Reads test-baseline.json to ignore known regressions and logs fixed ones.
    """
    script = f"""
import json, subprocess, re, sys, os
baseline_path = 'artifacts/harness/test-baseline.json'
baseline = set()
if os.path.exists(baseline_path):
    b_data = json.load(open(baseline_path))
    baseline = {{f.get('test_id') for f in b_data.get('baseline_failures', []) if f.get('test_id')}}

r = subprocess.run('{pytest_cmd}', shell=True, capture_output=True, text=True)
out = r.stdout + r.stderr
failed_matches = re.findall(r'^FAILED\\s+([^\\s]+)', out, re.MULTILINE)
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
"""
    import base64
    b64_script = base64.b64encode(script.encode('utf-8')).decode('utf-8')
    cmd = f"python -c \"import base64; exec(base64.b64decode('{b64_script}').decode('utf-8'))\""

    return AcceptanceCheck(
        name="baseline_regression_check",
        command=cmd,
        expected_exit=0,
        expected_pattern=r"baseline-stable",
        timeout_seconds=120
    )
