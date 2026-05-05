"""Tests for logslice.filters module."""

import pytest
from datetime import datetime
from logslice.filters import (
    extract_timestamp,
    extract_level,
    matches_time_range,
    matches_level,
    matches_pattern,
    apply_filters,
)


SAMPLE_LINES = {
    "iso": "2024-03-15T12:30:00 ERROR Something went wrong",
    "space": "2024-03-15 12:30:00 INFO Service started",
    "us_date": "03/15/2024 12:30:00 DEBUG Debugging info",
    "no_ts": "WARNING No timestamp here",
    "plain": "Just a plain log line with no metadata",
}


class TestExtractTimestamp:
    def test_iso_format(self):
        ts = extract_timestamp(SAMPLE_LINES["iso"])
        assert ts == datetime(2024, 3, 15, 12, 30, 0)

    def test_space_format(self):
        ts = extract_timestamp(SAMPLE_LINES["space"])
        assert ts == datetime(2024, 3, 15, 12, 30, 0)

    def test_us_date_format(self):
        ts = extract_timestamp(SAMPLE_LINES["us_date"])
        assert ts == datetime(2024, 3, 15, 12, 30, 0)

    def test_no_timestamp_returns_none(self):
        assert extract_timestamp(SAMPLE_LINES["plain"]) is None


class TestExtractLevel:
    def test_error_level(self):
        assert extract_level(SAMPLE_LINES["iso"]) == "ERROR"

    def test_info_level(self):
        assert extract_level(SAMPLE_LINES["space"]) == "INFO"

    def test_debug_level(self):
        assert extract_level(SAMPLE_LINES["us_date"]) == "DEBUG"

    def test_no_level_returns_none(self):
        assert extract_level(SAMPLE_LINES["plain"]) is None

    def test_case_insensitive(self):
        assert extract_level("2024-01-01 00:00:00 warning low disk") == "WARNING"


class TestMatchesTimeRange:
    def test_within_range(self):
        start = datetime(2024, 3, 15, 12, 0, 0)
        end = datetime(2024, 3, 15, 13, 0, 0)
        assert matches_time_range(SAMPLE_LINES["iso"], start, end) is True

    def test_before_start(self):
        start = datetime(2024, 3, 15, 13, 0, 0)
        assert matches_time_range(SAMPLE_LINES["iso"], start=start) is False

    def test_after_end(self):
        end = datetime(2024, 3, 15, 11, 0, 0)
        assert matches_time_range(SAMPLE_LINES["iso"], end=end) is False

    def test_no_range_always_true(self):
        assert matches_time_range(SAMPLE_LINES["plain"]) is True

    def test_no_timestamp_with_range_false(self):
        start = datetime(2024, 1, 1)
        assert matches_time_range(SAMPLE_LINES["plain"], start=start) is False


class TestMatchesLevel:
    def test_matching_level(self):
        assert matches_level(SAMPLE_LINES["iso"], ["ERROR"]) is True

    def test_non_matching_level(self):
        assert matches_level(SAMPLE_LINES["iso"], ["INFO", "DEBUG"]) is False

    def test_no_levels_always_true(self):
        assert matches_level(SAMPLE_LINES["plain"]) is True

    def test_case_insensitive_filter(self):
        assert matches_level(SAMPLE_LINES["space"], ["info"]) is True


class TestMatchesPattern:
    def test_matching_pattern(self):
        assert matches_pattern(SAMPLE_LINES["iso"], r"went wrong") is True

    def test_non_matching_pattern(self):
        assert matches_pattern(SAMPLE_LINES["iso"], r"started") is False

    def test_no_pattern_always_true(self):
        assert matches_pattern(SAMPLE_LINES["plain"]) is True

    def test_regex_pattern(self):
        assert matches_pattern(SAMPLE_LINES["iso"], r"ERROR.*wrong") is True


class TestApplyFilters:
    def test_all_filters_pass(self):
        result = apply_filters(
            SAMPLE_LINES["iso"],
            start=datetime(2024, 3, 15, 12, 0, 0),
            end=datetime(2024, 3, 15, 13, 0, 0),
            levels=["ERROR"],
            pattern=r"went wrong",
        )
        assert result is True

    def test_level_filter_fails(self):
        result = apply_filters(SAMPLE_LINES["iso"], levels=["INFO"])
        assert result is False

    def test_no_filters_always_true(self):
        assert apply_filters(SAMPLE_LINES["plain"]) is True
