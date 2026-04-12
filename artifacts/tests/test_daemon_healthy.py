"""Tests for daemon_healthy() AcceptanceCheck factory.

4+ cases: healthy unit passes, Tasks below threshold fails,
Memory below threshold fails, missing unit fails with clear error.
"""
from aho.acceptance import daemon_healthy, run_check, AcceptanceCheck


def test_healthy_unit_passes():
    """A running daemon (aho-telegram) passes the health check."""
    check = daemon_healthy("aho-telegram")
    assert isinstance(check, AcceptanceCheck)
    assert check.name == "daemon_healthy_aho-telegram"
    result = run_check(check)
    assert result.passed is True
    assert "ok=True" in result.actual_output


def test_tasks_below_threshold_fails():
    """Setting min_tasks impossibly high causes failure."""
    check = daemon_healthy("aho-telegram", min_tasks=99999)
    result = run_check(check)
    assert result.passed is False


def test_memory_below_threshold_fails():
    """Setting min_memory_mb impossibly high causes failure."""
    check = daemon_healthy("aho-telegram", min_memory_mb=999999)
    result = run_check(check)
    assert result.passed is False


def test_missing_unit_fails():
    """A nonexistent unit fails with clear error."""
    check = daemon_healthy("aho-nonexistent-unit-xyz")
    result = run_check(check)
    assert result.passed is False
    assert "active=False" in result.actual_output or result.error is not None
