"""Tests for logslice.truncator."""

import pytest
from logslice.truncator import Truncator, DEFAULT_MAX_LENGTH, DEFAULT_SUFFIX


class TestTruncatorInit:
    def test_default_values(self):
        t = Truncator()
        assert t.max_length == DEFAULT_MAX_LENGTH
        assert t.suffix == DEFAULT_SUFFIX

    def test_custom_values(self):
        t = Truncator(max_length=50, suffix=">>>")
        assert t.max_length == 50
        assert t.suffix == ">>>"

    def test_invalid_max_length_zero_raises(self):
        with pytest.raises(ValueError, match="max_length must be at least 1"):
            Truncator(max_length=0)

    def test_invalid_max_length_negative_raises(self):
        with pytest.raises(ValueError, match="max_length must be at least 1"):
            Truncator(max_length=-5)

    def test_suffix_too_long_raises(self):
        with pytest.raises(ValueError, match="suffix length"):
            Truncator(max_length=3, suffix="...")

    def test_initial_counts_zero(self):
        t = Truncator()
        assert t.truncated_count == 0
        assert t.total_count == 0


class TestTruncatorTruncate:
    def test_short_line_unchanged(self):
        t = Truncator(max_length=20)
        assert t.truncate("hello world") == "hello world"

    def test_exact_length_unchanged(self):
        t = Truncator(max_length=10, suffix="...")
        line = "1234567890"
        assert t.truncate(line) == line

    def test_long_line_truncated(self):
        t = Truncator(max_length=10, suffix="...")
        result = t.truncate("abcdefghijk")
        assert result == "abcdefg..."
        assert len(result) == 10

    def test_truncated_line_ends_with_suffix(self):
        t = Truncator(max_length=15, suffix="[cut]")
        result = t.truncate("a" * 30)
        assert result.endswith("[cut]")

    def test_empty_suffix(self):
        t = Truncator(max_length=5, suffix="")
        result = t.truncate("abcdefgh")
        assert result == "abcde"

    def test_empty_line_unchanged(self):
        t = Truncator(max_length=10)
        assert t.truncate("") == ""


class TestTruncatorCounts:
    def test_total_count_increments(self):
        t = Truncator(max_length=10)
        t.truncate("short")
        t.truncate("also short")
        assert t.total_count == 2

    def test_truncated_count_increments_only_on_long(self):
        t = Truncator(max_length=10, suffix="...")
        t.truncate("short")
        t.truncate("this is too long for the limit")
        assert t.truncated_count == 1
        assert t.total_count == 2

    def test_drop_rate_zero_when_no_truncation(self):
        t = Truncator(max_length=100)
        t.truncate("line one")
        t.truncate("line two")
        assert t.drop_rate == 0.0

    def test_drop_rate_correct(self):
        t = Truncator(max_length=5, suffix=".")
        t.truncate("hi")
        t.truncate("hello world")
        assert t.drop_rate == pytest.approx(0.5)

    def test_drop_rate_no_lines_is_zero(self):
        t = Truncator()
        assert t.drop_rate == 0.0

    def test_feed_is_alias_for_truncate(self):
        t = Truncator(max_length=10, suffix="...")
        result = t.feed("this is way too long")
        assert result == "this is..."
        assert t.total_count == 1
