"""Tests for logslice.output module."""

import io
import pytest
from logslice.output import process_lines


SAMPLE_LINES = [
    "2024-01-15T08:00:00 INFO  Application started\n",
    "2024-01-15T08:01:00 DEBUG Connecting to database\n",
    "2024-01-15T08:02:00 ERROR Failed to connect: timeout\n",
    "2024-01-15T08:03:00 WARNING Retrying connection\n",
    "2024-01-15T08:04:00 INFO  Connection established\n",
]


def run_process(lines, **kwargs):
    stream = io.StringIO()
    count = process_lines(iter(lines), stream=stream, use_color=False, **kwargs)
    stream.seek(0)
    return count, stream.read()


class TestProcessLinesNoFilter:
    def test_all_lines_pass_with_no_filters(self):
        count, output = run_process(SAMPLE_LINES)
        assert count == 5

    def test_output_contains_all_messages(self):
        _, output = run_process(SAMPLE_LINES)
        assert "Application started" in output
        assert "Failed to connect" in output


class TestProcessLinesLevelFilter:
    def test_filter_by_error(self):
        count, output = run_process(SAMPLE_LINES, level_filter="ERROR")
        assert count == 1
        assert "Failed to connect" in output

    def test_filter_by_info(self):
        count, output = run_process(SAMPLE_LINES, level_filter="INFO")
        assert count == 2

    def test_no_match_returns_zero(self):
        count, output = run_process(SAMPLE_LINES, level_filter="CRITICAL")
        assert count == 0


class TestProcessLinesPattern:
    def test_pattern_filters_lines(self):
        count, output = run_process(SAMPLE_LINES, pattern="connect")
        assert count == 3

    def test_case_sensitive_pattern(self):
        count, _ = run_process(SAMPLE_LINES, pattern="CONNECT")
        assert count == 0

    def test_regex_pattern(self):
        count, _ = run_process(SAMPLE_LINES, pattern=r"08:0[12]")
        assert count == 2


class TestProcessLinesTimeRange:
    def test_start_time_filters_early_lines(self):
        count, output = run_process(SAMPLE_LINES, start_time="08:03")
        assert count >= 1
        assert "Retrying" in output or "Connection established" in output

    def test_combined_level_and_pattern(self):
        count, output = run_process(
            SAMPLE_LINES, level_filter="INFO", pattern="Connection"
        )
        assert count == 1
        assert "Connection established" in output
