import pytest
import json
from aho.acceptance import baseline_regression_check, run_check

def get_real_baseline_id():
    with open("artifacts/harness/test-baseline.json", "r") as f:
        data = json.load(f)
    return data["baseline_failures"][0]["test_id"]

def test_baseline_helper_no_failures():
    check = baseline_regression_check(pytest_cmd="echo \\\"100 passed\\\"")
    result = run_check(check)
    assert result.passed is True
    assert "baseline-stable" in result.actual_output
    assert "Fixed baseline failures" in result.actual_output

def test_baseline_helper_exact_baseline_failure():
    tid = get_real_baseline_id()
    check = baseline_regression_check(pytest_cmd=f"echo \\\"FAILED {tid} - details\\\"")
    result = run_check(check)
    assert result.passed is True
    assert "baseline-stable" in result.actual_output

def test_baseline_helper_new_failure():
    check = baseline_regression_check(pytest_cmd="echo \\\"FAILED new_test_not_in_baseline.py::test_fail\\\"")
    result = run_check(check)
    assert result.passed is False
    assert "NEW regressions found" in result.actual_output
    assert "new_test_not_in_baseline.py::test_fail" in result.actual_output

def test_baseline_helper_mixed_failures():
    tid = get_real_baseline_id()
    check = baseline_regression_check(pytest_cmd=f"echo -e \\\"FAILED {tid}\\\\nFAILED another_new_test\\\"")
    result = run_check(check)
    assert result.passed is False
    assert "NEW regressions found" in result.actual_output
    assert "another_new_test" in result.actual_output

def test_baseline_helper_regex_extraction():
    check = baseline_regression_check(pytest_cmd="echo \\\"FAILED path/to/test.py::test_feature - AssertionError\\\"")
    result = run_check(check)
    assert result.passed is False
    assert "path/to/test.py::test_feature" in result.actual_output
    assert "- AssertionError" not in result.actual_output

def test_baseline_helper_fixed_baseline():
    check = baseline_regression_check(pytest_cmd="echo \\\"100 passed\\\"")
    result = run_check(check)
    assert result.passed is True
    assert "Fixed baseline failures" in result.actual_output
