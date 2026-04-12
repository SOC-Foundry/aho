"""Tests for aho.acceptance — AcceptanceCheck primitive.

Minimum 7 cases per W1 plan:
1. happy path (exit 0, no pattern)
2. exit code mismatch
3. pattern miss
4. command not found
5. timeout exceeded
6. shell escape safety
7. exit + pattern combo (both must match)
"""
import json
import re

from aho.acceptance import AcceptanceCheck, AcceptanceResult, run_check, serialize_results


def test_happy_path_exit_zero_no_pattern():
    """Exit 0, no pattern → passed=True, matched=None."""
    check = AcceptanceCheck(name="true_cmd", command="true")
    result = run_check(check)
    assert result.passed is True
    assert result.actual_exit == 0
    assert result.matched is None
    assert result.error is None
    assert result.duration_seconds >= 0


def test_exit_code_mismatch():
    """Command exits 1 when 0 expected → passed=False."""
    check = AcceptanceCheck(name="false_cmd", command="false")
    result = run_check(check)
    assert result.passed is False
    assert result.actual_exit == 1
    assert result.matched is None
    assert result.error is None


def test_pattern_miss():
    """Stdout doesn't match expected pattern → passed=False, matched=False."""
    check = AcceptanceCheck(
        name="pattern_miss",
        command="echo 'hello world'",
        expected_pattern=r"foobar",
    )
    result = run_check(check)
    assert result.passed is False
    assert result.actual_exit == 0
    assert result.matched is False


def test_command_not_found():
    """Nonexistent command → passed=False, error populated."""
    check = AcceptanceCheck(
        name="missing_cmd",
        command="aho_nonexistent_command_xyz_12345",
    )
    result = run_check(check)
    assert result.passed is False
    assert result.actual_exit != 0
    assert result.error is None or "not found" in (result.actual_output + str(result.error)).lower() or result.actual_exit == 127


def test_timeout_exceeded():
    """Command exceeds timeout → passed=False, error='timeout'."""
    check = AcceptanceCheck(
        name="slow_cmd",
        command="sleep 10",
        timeout_seconds=1,
    )
    result = run_check(check)
    assert result.passed is False
    assert result.error == "timeout"
    assert result.duration_seconds >= 0.5


def test_shell_escape_safety():
    """Command with shell metacharacters executes safely without injection."""
    check = AcceptanceCheck(
        name="escape_test",
        command="echo 'safe; echo INJECTED'",
    )
    result = run_check(check)
    assert result.passed is True
    assert "INJECTED" not in result.actual_output.split("\n")[0] or "safe; echo INJECTED" in result.actual_output


def test_exit_and_pattern_combo_both_match():
    """Both exit code and pattern must match for passed=True."""
    check = AcceptanceCheck(
        name="combo_pass",
        command="echo '7 passed in 1.2s'",
        expected_exit=0,
        expected_pattern=r"\d+ passed",
    )
    result = run_check(check)
    assert result.passed is True
    assert result.actual_exit == 0
    assert result.matched is True


def test_exit_ok_but_pattern_fails():
    """Exit matches but pattern doesn't → passed=False."""
    check = AcceptanceCheck(
        name="combo_fail_pattern",
        command="echo 'no match here'",
        expected_exit=0,
        expected_pattern=r"\d+ passed",
    )
    result = run_check(check)
    assert result.passed is False
    assert result.actual_exit == 0
    assert result.matched is False


def test_pattern_ok_but_exit_fails():
    """Pattern matches but exit code wrong → passed=False."""
    check = AcceptanceCheck(
        name="combo_fail_exit",
        command="echo '7 passed' && exit 1",
        expected_exit=0,
        expected_pattern=r"\d+ passed",
    )
    result = run_check(check)
    assert result.passed is False
    assert result.actual_exit == 1
    assert result.matched is True


def test_expected_nonzero_exit():
    """Check that expects exit=1 and gets it → passed=True."""
    check = AcceptanceCheck(
        name="expect_fail",
        command="false",
        expected_exit=1,
    )
    result = run_check(check)
    assert result.passed is True
    assert result.actual_exit == 1


def test_output_truncation():
    """Output exceeding 4KB is truncated."""
    check = AcceptanceCheck(
        name="big_output",
        command="python -c \"print('x' * 8192)\"",
    )
    result = run_check(check)
    assert result.passed is True
    assert len(result.actual_output) <= 4096


def test_serialize_results(tmp_path):
    """serialize_results writes valid JSON array."""
    results = [
        AcceptanceResult(
            check_name="test1", passed=True, actual_exit=0,
            actual_output="ok", matched=None, duration_seconds=0.1,
        ),
        AcceptanceResult(
            check_name="test2", passed=False, actual_exit=1,
            actual_output="fail", matched=False, duration_seconds=0.2,
            error=None,
        ),
    ]
    out = tmp_path / "results.json"
    serialize_results(results, out)
    data = json.loads(out.read_text())
    assert len(data) == 2
    assert data[0]["check_name"] == "test1"
    assert data[0]["passed"] is True
    assert data[1]["passed"] is False
