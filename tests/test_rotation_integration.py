"""Integration tests: RotationWatcher + tail_with_rotation together."""
import os
import pytest

from logslice.rotationwatcher import RotationWatcher
from logslice.tailwatcher import tail_with_rotation


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "service.log"
    p.write_text("start\n")
    return p


class TestRotationIntegration:
    def test_watcher_sees_truncation_then_tail_rereads(self, log_file):
        """RotationWatcher detects truncation; tail re-reads from byte 0."""
        watcher = RotationWatcher(str(log_file))
        # Grow the file, then truncate (simulate logrotate copytruncate).
        with open(str(log_file), "a") as f:
            f.write("middle\n")
        log_file.write_text("after_rotation\n")
        assert watcher.check() is True
        assert watcher.rotation_count == 1

        # Tail should yield the new content.
        lines = list(
            tail_with_rotation(str(log_file), poll_interval=0, max_iterations=1)
        )
        assert "after_rotation" in lines

    def test_no_rotation_watcher_stays_quiet(self, log_file):
        watcher = RotationWatcher(str(log_file))
        with open(str(log_file), "a") as f:
            f.write("extra\n")
        assert watcher.check() is False
        assert watcher.rotation_count == 0

    def test_tail_collects_all_lines_no_rotation(self, log_file):
        with open(str(log_file), "a") as f:
            f.write("second\nthird\n")
        lines = list(
            tail_with_rotation(str(log_file), poll_interval=0, max_iterations=1)
        )
        assert lines == ["start", "second", "third"]

    def test_rotation_count_accumulates(self, log_file):
        watcher = RotationWatcher(str(log_file))
        for i in range(3):
            log_file.write_text(f"cycle{i}\n")
            watcher.check()
        assert watcher.rotation_count == 3
