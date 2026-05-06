"""Tests for logslice.tailwatcher."""
import os
import pytest

from logslice.tailwatcher import tail_with_rotation, _open_safe


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("alpha\nbeta\n")
    return p


class TestOpenSafe:
    def test_returns_file_object_for_existing_file(self, log_file):
        fh = _open_safe(str(log_file))
        assert fh is not None
        fh.close()

    def test_returns_none_for_missing_file(self, tmp_path):
        result = _open_safe(str(tmp_path / "nope.log"))
        assert result is None


class TestTailWithRotation:
    def test_reads_existing_lines(self, log_file):
        lines = list(tail_with_rotation(str(log_file), poll_interval=0, max_iterations=1))
        assert "alpha" in lines
        assert "beta" in lines

    def test_strips_newlines(self, log_file):
        lines = list(tail_with_rotation(str(log_file), poll_interval=0, max_iterations=1))
        for line in lines:
            assert "\n" not in line

    def test_missing_file_yields_nothing(self, tmp_path):
        path = str(tmp_path / "ghost.log")
        lines = list(tail_with_rotation(path, poll_interval=0, max_iterations=1))
        assert lines == []

    def test_detects_new_lines_across_iterations(self, log_file):
        """Second iteration should pick up lines appended after first poll."""
        collected = []
        # Simulate: iter 1 reads existing; between iter 1 and 2 append a line.
        # We achieve this by monkey-patching time.sleep to append.
        import logslice.tailwatcher as tw
        original_sleep = tw.time.sleep
        call_count = [0]

        def fake_sleep(t):
            call_count[0] += 1
            if call_count[0] == 1:
                with open(str(log_file), "a") as f:
                    f.write("gamma\n")

        tw.time.sleep = fake_sleep
        try:
            collected = list(
                tail_with_rotation(str(log_file), poll_interval=0, max_iterations=2)
            )
        finally:
            tw.time.sleep = original_sleep

        assert "gamma" in collected

    def test_rotation_causes_reread_from_start(self, log_file):
        """After rotation, lines from the new file are yielded."""
        import logslice.tailwatcher as tw
        original_sleep = tw.time.sleep
        call_count = [0]

        def fake_sleep(t):
            call_count[0] += 1
            if call_count[0] == 1:
                # Simulate rotation: truncate/replace file content.
                log_file.write_text("delta\n")

        tw.time.sleep = fake_sleep
        try:
            lines = list(
                tail_with_rotation(str(log_file), poll_interval=0, max_iterations=2)
            )
        finally:
            tw.time.sleep = original_sleep

        assert "delta" in lines
