"""Tests for logslice.rotationwatcher."""
import os
import pytest

from logslice.rotationwatcher import RotationWatcher


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("line1\n")
    return p


class TestRotationWatcherInit:
    def test_invalid_empty_path_raises(self):
        with pytest.raises(ValueError, match="path"):
            RotationWatcher("")

    def test_nonexistent_file_does_not_raise(self, tmp_path):
        watcher = RotationWatcher(str(tmp_path / "missing.log"))
        assert watcher._last_inode is None

    def test_existing_file_captures_inode(self, log_file):
        watcher = RotationWatcher(str(log_file))
        assert watcher._last_inode == os.stat(str(log_file)).st_ino

    def test_rotation_count_starts_at_zero(self, log_file):
        watcher = RotationWatcher(str(log_file))
        assert watcher.rotation_count == 0


class TestRotationWatcherCheck:
    def test_no_change_returns_false(self, log_file):
        watcher = RotationWatcher(str(log_file))
        assert watcher.check() is False

    def test_no_change_does_not_increment_count(self, log_file):
        watcher = RotationWatcher(str(log_file))
        watcher.check()
        assert watcher.rotation_count == 0

    def test_size_growth_returns_false(self, log_file):
        watcher = RotationWatcher(str(log_file))
        log_file.write_text("line1\nline2\n")
        assert watcher.check() is False

    def test_truncation_detected(self, log_file):
        log_file.write_text("line1\nline2\nline3\n")
        watcher = RotationWatcher(str(log_file))
        log_file.write_text("")  # truncate
        assert watcher.check() is True

    def test_truncation_increments_count(self, log_file):
        log_file.write_text("some content\n")
        watcher = RotationWatcher(str(log_file))
        log_file.write_text("")
        watcher.check()
        assert watcher.rotation_count == 1

    def test_file_disappears_returns_true(self, log_file):
        watcher = RotationWatcher(str(log_file))
        log_file.unlink()
        assert watcher.check() is True

    def test_file_disappears_increments_count(self, log_file):
        watcher = RotationWatcher(str(log_file))
        log_file.unlink()
        watcher.check()
        assert watcher.rotation_count == 1

    def test_missing_from_start_returns_false(self, tmp_path):
        watcher = RotationWatcher(str(tmp_path / "ghost.log"))
        assert watcher.check() is False

    def test_multiple_rotations_counted(self, log_file):
        watcher = RotationWatcher(str(log_file))
        for _ in range(3):
            log_file.write_text("")
            watcher.check()
            log_file.write_text("new content\n")
            watcher.check()  # size grew, not a rotation
        assert watcher.rotation_count == 1  # only first truncation


class TestRotationWatcherReset:
    def test_reset_clears_rotation_state(self, log_file):
        watcher = RotationWatcher(str(log_file))
        log_file.write_text("")
        watcher.check()  # detects truncation
        log_file.write_text("fresh start\n")
        watcher.reset()
        assert watcher.check() is False

    def test_reset_updates_size(self, log_file):
        watcher = RotationWatcher(str(log_file))
        log_file.write_text("much longer content here\n")
        watcher.reset()
        assert watcher._last_size == os.stat(str(log_file)).st_size
