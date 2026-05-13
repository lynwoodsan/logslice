"""Tests for logslice.timeshift."""

from datetime import timedelta

import pytest

from logslice.timeshift import TimeShifter, shift_line


# ---------------------------------------------------------------------------
# shift_line helpers
# ---------------------------------------------------------------------------

class TestShiftLine:
    def test_iso_t_separator_shifted(self):
        line = "2024-03-10T08:00:00 INFO starting"
        result = shift_line(line, timedelta(hours=2))
        assert "2024-03-10T10:00:00" in result

    def test_space_separator_shifted(self):
        line = "2024-03-10 08:00:00 INFO starting"
        result = shift_line(line, timedelta(hours=-1))
        assert "2024-03-10T07:00:00" in result

    def test_subseconds_preserved(self):
        line = "2024-03-10T08:00:00.123 INFO msg"
        result = shift_line(line, timedelta(hours=1))
        assert "2024-03-10T09:00:00.123" in result

    def test_no_timestamp_unchanged(self):
        line = "no timestamp here"
        assert shift_line(line, timedelta(hours=5)) == line

    def test_negative_shift_crosses_hour_boundary(self):
        line = "2024-03-10T00:30:00 DEBUG tick"
        result = shift_line(line, timedelta(hours=-1))
        assert "2024-03-09T23:30:00" in result

    def test_minute_shift(self):
        line = "2024-03-10T08:00:00 WARN slow"
        result = shift_line(line, timedelta(minutes=90))
        assert "2024-03-10T09:30:00" in result

    def test_zero_delta_unchanged(self):
        line = "2024-03-10T08:00:00 INFO noop"
        result = shift_line(line, timedelta(0))
        assert "2024-03-10T08:00:00" in result

    def test_multiple_timestamps_in_line(self):
        line = "2024-03-10T08:00:00 to 2024-03-10T09:00:00"
        result = shift_line(line, timedelta(hours=1))
        assert "2024-03-10T09:00:00" in result
        assert "2024-03-10T10:00:00" in result


# ---------------------------------------------------------------------------
# TimeShifter dataclass
# ---------------------------------------------------------------------------

class TestTimeShifterInit:
    def test_default_values(self):
        ts = TimeShifter()
        assert ts.hours == 0
        assert ts.minutes == 0
        assert ts.shifted_count == 0

    def test_custom_hours(self):
        ts = TimeShifter(hours=3)
        assert ts.hours == 3

    def test_custom_minutes(self):
        ts = TimeShifter(minutes=30)
        assert ts.minutes == 30


class TestTimeShifterProcess:
    def test_shifted_count_increments_on_change(self):
        ts = TimeShifter(hours=1)
        ts.process("2024-03-10T08:00:00 INFO msg")
        assert ts.shifted_count == 1

    def test_shifted_count_unchanged_for_no_ts(self):
        ts = TimeShifter(hours=1)
        ts.process("no timestamp")
        assert ts.shifted_count == 0

    def test_process_returns_shifted_line(self):
        ts = TimeShifter(hours=2)
        result = ts.process("2024-03-10T06:00:00 INFO boot")
        assert "2024-03-10T08:00:00" in result


class TestTimeShifterFeed:
    def test_feed_yields_all_lines(self):
        ts = TimeShifter(hours=1)
        lines = [
            "2024-03-10T08:00:00 INFO a",
            "2024-03-10T09:00:00 INFO b",
            "no timestamp",
        ]
        results = list(ts.feed(iter(lines)))
        assert len(results) == 3

    def test_feed_shifts_timestamps(self):
        ts = TimeShifter(hours=1)
        lines = ["2024-03-10T08:00:00 INFO hello"]
        result = list(ts.feed(iter(lines)))[0]
        assert "2024-03-10T09:00:00" in result

    def test_feed_accumulates_shifted_count(self):
        ts = TimeShifter(hours=1)
        lines = [
            "2024-03-10T08:00:00 INFO a",
            "plain line",
            "2024-03-10T09:00:00 DEBUG b",
        ]
        list(ts.feed(iter(lines)))
        assert ts.shifted_count == 2
