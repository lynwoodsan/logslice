"""Tests for logslice.formatter module."""

import io
import pytest
from logslice.formatter import (
    colorize_line,
    format_line,
    supports_color,
    write_output,
    COLORS,
)


class TestSupportsColor:
    def test_stringio_has_no_color(self):
        stream = io.StringIO()
        assert supports_color(stream) is False


class TestColorizeLine:
    def test_no_color_returns_line_unchanged(self):
        assert colorize_line("some log", "INFO", use_color=False) == "some log"

    def test_none_level_returns_line_unchanged(self):
        assert colorize_line("some log", None, use_color=True) == "some log"

    def test_info_level_applies_green(self):
        result = colorize_line("msg", "INFO", use_color=True)
        assert result.startswith(COLORS["INFO"])
        assert result.endswith(COLORS["RESET"])

    def test_error_level_applies_red(self):
        result = colorize_line("msg", "ERROR", use_color=True)
        assert result.startswith(COLORS["ERROR"])

    def test_unknown_level_returns_line_unchanged(self):
        result = colorize_line("msg", "VERBOSE", use_color=True)
        assert result == "msg"

    def test_warn_alias(self):
        result = colorize_line("msg", "WARN", use_color=True)
        assert result.startswith(COLORS["WARN"])


class TestFormatLine:
    def test_strips_trailing_newline(self):
        result = format_line("hello\n", None, use_color=False)
        assert result == "hello"

    def test_applies_prefix(self):
        result = format_line("hello", None, use_color=False, prefix=">> ")
        assert result == ">> hello"

    def test_color_and_prefix_together(self):
        result = format_line("hello", "ERROR", use_color=True, prefix=">> ")
        assert ">> " in result
        assert COLORS["ERROR"] in result


class TestWriteOutput:
    def test_returns_count(self):
        stream = io.StringIO()
        count = write_output(["line1", "line2", "line3"], stream=stream)
        assert count == 3

    def test_writes_lines_to_stream(self):
        stream = io.StringIO()
        write_output(["alpha", "beta"], stream=stream)
        stream.seek(0)
        content = stream.read()
        assert "alpha" in content
        assert "beta" in content

    def test_empty_list_returns_zero(self):
        stream = io.StringIO()
        count = write_output([], stream=stream)
        assert count == 0
