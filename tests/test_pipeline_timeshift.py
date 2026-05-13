"""Integration: TimeShifter wired into a minimal pipeline."""

from typing import Iterator, List

from logslice.timeshift import TimeShifter


def _run(lines: List[str], hours: int = 0, minutes: int = 0) -> List[str]:
    """Run lines through a TimeShifter and return the results."""
    shifter = TimeShifter(hours=hours, minutes=minutes)
    return list(shifter.feed(iter(lines)))


class TestPipelineTimeShift:
    def test_zero_shift_preserves_lines(self):
        lines = [
            "2024-01-01T10:00:00 INFO boot",
            "2024-01-01T10:01:00 DEBUG tick",
        ]
        result = _run(lines, hours=0)
        assert result[0].startswith("2024-01-01T10:00:00")
        assert result[1].startswith("2024-01-01T10:01:00")

    def test_positive_shift_advances_time(self):
        lines = ["2024-01-01T10:00:00 INFO event"]
        result = _run(lines, hours=5)
        assert "2024-01-01T15:00:00" in result[0]

    def test_negative_shift_reverses_time(self):
        lines = ["2024-01-01T10:00:00 INFO event"]
        result = _run(lines, hours=-3)
        assert "2024-01-01T07:00:00" in result[0]

    def test_lines_without_timestamps_pass_through(self):
        lines = ["startup complete", "--- separator ---"]
        result = _run(lines, hours=6)
        assert result == lines

    def test_mixed_lines_all_returned(self):
        lines = [
            "2024-01-01T08:00:00 INFO start",
            "raw text line",
            "2024-01-01T08:05:00 ERROR fail",
        ]
        result = _run(lines, hours=2)
        assert len(result) == 3
        assert "2024-01-01T10:00:00" in result[0]
        assert result[1] == "raw text line"
        assert "2024-01-01T10:05:00" in result[2]

    def test_shifted_count_reflects_only_ts_lines(self):
        shifter = TimeShifter(hours=1)
        lines = [
            "2024-01-01T08:00:00 INFO a",
            "plain",
            "2024-01-01T09:00:00 WARN b",
        ]
        list(shifter.feed(iter(lines)))
        assert shifter.shifted_count == 2
