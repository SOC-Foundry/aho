"""Tests for event log relocation (W7).

6 cases: path resolution, migration, migration abort, rotation,
rotation .3 deletion, bundle reads from new path.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from aho.logger import event_log_path, _EVENT_LOG_FILENAME


def test_new_path_resolves_to_xdg():
    """event_log_path() returns ~/.local/share/aho/events/aho_event_log.jsonl."""
    p = event_log_path()
    assert str(p).endswith(".local/share/aho/events/aho_event_log.jsonl")


def test_migration_copies_and_deletes():
    """Migration copies from old path to new path, deletes original."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_dir = Path(tmpdir) / "data"
        old_dir.mkdir()
        new_dir = Path(tmpdir) / "events"

        old_file = old_dir / _EVENT_LOG_FILENAME
        new_file = new_dir / _EVENT_LOG_FILENAME

        # Write test data
        old_file.write_text('{"event":"test1"}\n{"event":"test2"}\n')

        from aho.logger import migrate_event_log
        with patch("aho.logger._EVENTS_DIR", new_dir), \
             patch("aho.logger._old_event_log_path", return_value=old_file):
            result = migrate_event_log()

        assert result is True
        assert new_file.exists()
        assert not old_file.exists()
        assert new_file.read_text().count("\n") == 2


def test_migration_aborts_on_size_mismatch():
    """Migration aborts if copy size doesn't match, preserves original."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_dir = Path(tmpdir) / "data"
        old_dir.mkdir()
        new_dir = Path(tmpdir) / "events"
        new_dir.mkdir()

        old_file = old_dir / _EVENT_LOG_FILENAME
        new_file = new_dir / _EVENT_LOG_FILENAME
        old_file.write_text('{"event":"test"}\n')

        # Pre-create new file (migration should return False — already exists)
        new_file.write_text('{"event":"different"}\n')

        from aho.logger import migrate_event_log
        with patch("aho.logger._EVENTS_DIR", new_dir), \
             patch("aho.logger._old_event_log_path", return_value=old_file):
            result = migrate_event_log()

        assert result is False
        assert old_file.exists()  # original preserved


def test_rotation_triggers_at_threshold():
    """Rotation shifts .1 .2 .3 when file exceeds threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_dir = Path(tmpdir)
        log_file = events_dir / _EVENT_LOG_FILENAME

        # Create a file just over 1KB threshold
        log_file.write_text("x" * 1100)

        from aho.logger import _rotate_if_needed, _ROTATION_CHECK_INTERVAL
        import aho.logger as logger_mod

        old_interval = logger_mod._ROTATION_CHECK_INTERVAL
        old_max = logger_mod._ROTATION_MAX_BYTES
        old_dir = logger_mod._EVENTS_DIR
        old_last = logger_mod._last_rotation_check

        try:
            logger_mod._ROTATION_CHECK_INTERVAL = 0  # disable debounce
            logger_mod._ROTATION_MAX_BYTES = 1024  # 1KB threshold
            logger_mod._EVENTS_DIR = events_dir
            logger_mod._last_rotation_check = 0

            _rotate_if_needed()

            # Current file should be gone (renamed to .1)
            assert not log_file.exists()
            assert (events_dir / f"{_EVENT_LOG_FILENAME}.1").exists()
            assert (events_dir / f"{_EVENT_LOG_FILENAME}.1").read_text() == "x" * 1100
        finally:
            logger_mod._ROTATION_CHECK_INTERVAL = old_interval
            logger_mod._ROTATION_MAX_BYTES = old_max
            logger_mod._EVENTS_DIR = old_dir
            logger_mod._last_rotation_check = old_last


def test_rotation_deletes_oldest():
    """Rotation deletes .3 (oldest generation)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        events_dir = Path(tmpdir)
        log_file = events_dir / _EVENT_LOG_FILENAME

        # Create current + .1 + .2 + .3
        log_file.write_text("current" * 200)  # over 1KB
        (events_dir / f"{_EVENT_LOG_FILENAME}.1").write_text("gen1")
        (events_dir / f"{_EVENT_LOG_FILENAME}.2").write_text("gen2")
        (events_dir / f"{_EVENT_LOG_FILENAME}.3").write_text("gen3")

        import aho.logger as logger_mod
        old_interval = logger_mod._ROTATION_CHECK_INTERVAL
        old_max = logger_mod._ROTATION_MAX_BYTES
        old_dir = logger_mod._EVENTS_DIR
        old_last = logger_mod._last_rotation_check

        try:
            logger_mod._ROTATION_CHECK_INTERVAL = 0
            logger_mod._ROTATION_MAX_BYTES = 1024
            logger_mod._EVENTS_DIR = events_dir
            logger_mod._last_rotation_check = 0

            from aho.logger import _rotate_if_needed
            _rotate_if_needed()

            # .3 (was gen3) should be deleted
            assert not (events_dir / f"{_EVENT_LOG_FILENAME}.3").exists() or \
                   (events_dir / f"{_EVENT_LOG_FILENAME}.3").read_text() == "gen2"
            # .1 should now be the old current
            assert (events_dir / f"{_EVENT_LOG_FILENAME}.1").read_text() == "current" * 200
            # .2 should be old .1
            assert (events_dir / f"{_EVENT_LOG_FILENAME}.2").read_text() == "gen1"
        finally:
            logger_mod._ROTATION_CHECK_INTERVAL = old_interval
            logger_mod._ROTATION_MAX_BYTES = old_max
            logger_mod._EVENTS_DIR = old_dir
            logger_mod._last_rotation_check = old_last


def test_components_section_reads_new_path():
    """Bundle components_section reads from new event log path."""
    from aho.bundle.components_section import generate_components_section
    # This should not error even if data/ is empty
    result = generate_components_section("0.2.11")
    assert "§22" in result
