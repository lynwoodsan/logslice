"""Tests for logslice.stats module."""

import pytest
from logslice.stats import LogStats


class TestLogStatsRecordLine:
    def test_initial_state(self):
        s = LogStats()
        assert s.total_lines == 0
        assert s.matched_lines == 0
        assert s.skipped_lines == 0

    def test_matched_line_increments_matched(self):
        s = LogStats()
        s.record_line("some line", matched=True, level="INFO", timestamp="2024-01-01")
        assert s.total_lines == 1
        assert s.matched_lines == 1
        assert s.skipped_lines == 0

    def test_unmatched_line_increments_skipped(self):
        s = LogStats()
        s.record_line("some line", matched=False, level=None, timestamp=None)
        assert s.total_lines == 1
        assert s.matched_lines == 0
        assert s.skipped_lines == 1

    def test_level_counts_accumulated(self):
        s = LogStats()
        s.record_line("", matched=True, level="info", timestamp=None)
        s.record_line("", matched=True, level="INFO", timestamp=None)
        s.record_line("", matched=True, level="ERROR", timestamp=None)
        assert s.level_counts["INFO"] == 2
        assert s.level_counts["ERROR"] == 1

    def test_level_none_not_counted(self):
        s = LogStats()
        s.record_line("", matched=True, level=None, timestamp=None)
        assert len(s.level_counts) == 0

    def test_first_and_last_timestamp(self):
        s = LogStats()
        s.record_line("", matched=True, level=None, timestamp="2024-01-01 00:00:00")
        s.record_line("", matched=True, level=None, timestamp="2024-01-02 00:00:00")
        assert s.first_timestamp == "2024-01-01 00:00:00"
        assert s.last_timestamp == "2024-01-02 00:00:00"

    def test_timestamp_not_updated_for_unmatched(self):
        s = LogStats()
        s.record_line("", matched=False, level=None, timestamp="2024-01-01")
        assert s.first_timestamp is None


class TestMatchRate:
    def test_zero_lines_returns_zero(self):
        s = LogStats()
        assert s.match_rate == 0.0

    def test_half_matched(self):
        s = LogStats()
        s.record_line("", matched=True, level=None, timestamp=None)
        s.record_line("", matched=False, level=None, timestamp=None)
        assert s.match_rate == pytest.approx(0.5)

    def test_all_matched(self):
        s = LogStats()
        for _ in range(4):
            s.record_line("", matched=True, level=None, timestamp=None)
        assert s.match_rate == pytest.approx(1.0)


class TestFormatReport:
    def test_report_contains_totals(self):
        s = LogStats()
        s.record_line("line", matched=True, level="WARN", timestamp="2024-06-01")
        report = s.format_report()
        assert "Total lines read" in report
        assert "1" in report

    def test_report_contains_level_counts(self):
        s = LogStats()
        s.record_line("", matched=True, level="DEBUG", timestamp=None)
        report = s.format_report()
        assert "DEBUG=1" in report

    def test_report_contains_timestamps(self):
        s = LogStats()
        s.record_line("", matched=True, level=None, timestamp="2024-01-15 08:00:00")
        report = s.format_report()
        assert "2024-01-15 08:00:00" in report

    def test_report_no_levels_omits_level_line(self):
        s = LogStats()
        s.record_line("", matched=True, level=None, timestamp=None)
        report = s.format_report()
        assert "Levels matched" not in report
