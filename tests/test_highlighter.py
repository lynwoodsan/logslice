"""Tests for logslice.highlighter module."""

import pytest
from logslice.highlighter import (
    highlight_matches,
    count_matches,
    strip_highlights,
    HIGHLIGHT_COLOR,
    RESET_COLOR,
)


class TestHighlightMatches:
    def test_no_pattern_returns_line_unchanged(self):
        line = "ERROR something went wrong"
        assert highlight_matches(line, None) == line

    def test_empty_pattern_returns_line_unchanged(self):
        line = "ERROR something went wrong"
        assert highlight_matches(line, "") == line

    def test_no_color_returns_line_unchanged(self):
        line = "ERROR something went wrong"
        assert highlight_matches(line, "ERROR", use_color=False) == line

    def test_pattern_wraps_match_with_color(self):
        line = "ERROR something went wrong"
        result = highlight_matches(line, "ERROR")
        assert HIGHLIGHT_COLOR in result
        assert RESET_COLOR in result
        assert "ERROR" in result

    def test_multiple_matches_all_highlighted(self):
        line = "ERROR retry ERROR again"
        result = highlight_matches(line, "ERROR")
        assert result.count(HIGHLIGHT_COLOR) == 2
        assert result.count(RESET_COLOR) == 2

    def test_invalid_regex_returns_line_unchanged(self):
        line = "some log line"
        result = highlight_matches(line, "[invalid")
        assert result == line

    def test_partial_word_match_highlighted(self):
        line = "Connection timeout occurred"
        result = highlight_matches(line, "time")
        assert f"{HIGHLIGHT_COLOR}time{RESET_COLOR}" in result

    def test_no_match_returns_line_unchanged(self):
        line = "INFO everything is fine"
        result = highlight_matches(line, "ERROR")
        assert result == line


class TestCountMatches:
    def test_no_pattern_returns_zero(self):
        assert count_matches("ERROR ERROR", None) == 0

    def test_empty_pattern_returns_zero(self):
        assert count_matches("ERROR ERROR", "") == 0

    def test_single_match_returns_one(self):
        assert count_matches("ERROR something", "ERROR") == 1

    def test_multiple_matches_counted(self):
        assert count_matches("ERROR retry ERROR again ERROR", "ERROR") == 3

    def test_no_match_returns_zero(self):
        assert count_matches("INFO all good", "ERROR") == 0

    def test_invalid_regex_returns_zero(self):
        assert count_matches("some line", "[invalid") == 0

    def test_regex_group_match(self):
        assert count_matches("foo123 bar456", r"\d+") == 2


class TestStripHighlights:
    def test_plain_line_unchanged(self):
        line = "plain log line"
        assert strip_highlights(line) == line

    def test_removes_highlight_codes(self):
        highlighted = f"{HIGHLIGHT_COLOR}ERROR{RESET_COLOR} something"
        assert strip_highlights(highlighted) == "ERROR something"

    def test_removes_multiple_highlight_codes(self):
        highlighted = f"{HIGHLIGHT_COLOR}A{RESET_COLOR} and {HIGHLIGHT_COLOR}B{RESET_COLOR}"
        assert strip_highlights(highlighted) == "A and B"

    def test_empty_string(self):
        assert strip_highlights("") == ""
