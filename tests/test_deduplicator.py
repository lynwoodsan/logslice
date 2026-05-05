"""Tests for logslice.deduplicator."""

import pytest
from logslice.deduplicator import Deduplicator


class TestDeduplicatorInit:
    def test_default_window(self):
        d = Deduplicator()
        assert d.window == 100

    def test_custom_window(self):
        d = Deduplicator(window=10)
        assert d.window == 10

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            Deduplicator(window=0)

    def test_initial_counts_zero(self):
        d = Deduplicator()
        assert d.total == 0
        assert d.duplicates == 0


class TestDeduplicatorFeed:
    def test_first_occurrence_passes(self):
        d = Deduplicator()
        assert d.feed("hello\n") == "hello\n"

    def test_second_occurrence_is_duplicate(self):
        d = Deduplicator()
        d.feed("hello\n")
        assert d.feed("hello\n") is None

    def test_different_lines_both_pass(self):
        d = Deduplicator()
        assert d.feed("line one\n") == "line one\n"
        assert d.feed("line two\n") == "line two\n"

    def test_total_increments_on_each_feed(self):
        d = Deduplicator()
        d.feed("a\n")
        d.feed("a\n")
        d.feed("b\n")
        assert d.total == 3

    def test_duplicates_count_increments(self):
        d = Deduplicator()
        d.feed("x\n")
        d.feed("x\n")
        d.feed("x\n")
        assert d.duplicates == 2

    def test_disabled_passes_all(self):
        d = Deduplicator(enabled=False)
        assert d.feed("same\n") == "same\n"
        assert d.feed("same\n") == "same\n"

    def test_window_eviction_allows_reappearance(self):
        d = Deduplicator(window=2)
        d.feed("a\n")  # seen: {a}
        d.feed("b\n")  # seen: {a, b}
        d.feed("c\n")  # seen: {b, c}  — 'a' evicted
        # 'a' should pass again now
        assert d.feed("a\n") == "a\n"

    def test_trailing_newline_normalized(self):
        d = Deduplicator()
        d.feed("msg\n")
        assert d.feed("msg\n") is None


class TestDeduplicatorFilter:
    def test_filter_removes_duplicates(self):
        d = Deduplicator()
        lines = ["a\n", "b\n", "a\n", "c\n", "b\n"]
        result = list(d.filter(lines))
        assert result == ["a\n", "b\n", "c\n"]

    def test_filter_empty_input(self):
        d = Deduplicator()
        assert list(d.filter([])) == []


class TestDuplicateRate:
    def test_no_lines_rate_is_zero(self):
        d = Deduplicator()
        assert d.duplicate_rate == 0.0

    def test_half_duplicates(self):
        d = Deduplicator()
        d.feed("a\n")
        d.feed("a\n")
        assert d.duplicate_rate == pytest.approx(0.5)

    def test_no_duplicates_rate_is_zero(self):
        d = Deduplicator()
        d.feed("a\n")
        d.feed("b\n")
        assert d.duplicate_rate == 0.0
