"""Tests for logslice.paginator."""
import pytest

from logslice.paginator import Paginator

LINES = ["line1", "line2", "line3", "line4", "line5"]


# ---------------------------------------------------------------------------
# init / validation
# ---------------------------------------------------------------------------

class TestPaginatorInit:
    def test_default_values(self):
        p = Paginator()
        assert p.page_size == 0
        assert p.skip == 0

    def test_custom_values(self):
        p = Paginator(page_size=10, skip=5)
        assert p.page_size == 10
        assert p.skip == 5

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError, match="page_size"):
            Paginator(page_size=-1)

    def test_invalid_skip_raises(self):
        with pytest.raises(ValueError, match="skip"):
            Paginator(skip=-1)


# ---------------------------------------------------------------------------
# unlimited (page_size=0)
# ---------------------------------------------------------------------------

class TestPaginatorUnlimited:
    def test_all_lines_pass_through(self):
        p = Paginator()
        result = list(p.feed_many(LINES))
        assert result == LINES

    def test_emitted_count_matches(self):
        p = Paginator()
        list(p.feed_many(LINES))
        assert p.emitted == len(LINES)

    def test_is_full_always_false(self):
        p = Paginator()
        list(p.feed_many(LINES))
        assert p.is_full is False


# ---------------------------------------------------------------------------
# page_size limit
# ---------------------------------------------------------------------------

class TestPaginatorPageSize:
    def test_limits_output(self):
        p = Paginator(page_size=3)
        result = list(p.feed_many(LINES))
        assert result == ["line1", "line2", "line3"]

    def test_is_full_after_page(self):
        p = Paginator(page_size=2)
        list(p.feed_many(LINES))
        assert p.is_full is True

    def test_emitted_equals_page_size(self):
        p = Paginator(page_size=2)
        list(p.feed_many(LINES))
        assert p.emitted == 2

    def test_page_size_larger_than_input(self):
        p = Paginator(page_size=100)
        result = list(p.feed_many(LINES))
        assert result == LINES


# ---------------------------------------------------------------------------
# skip
# ---------------------------------------------------------------------------

class TestPaginatorSkip:
    def test_skips_first_n_lines(self):
        p = Paginator(skip=2)
        result = list(p.feed_many(LINES))
        assert result == ["line3", "line4", "line5"]

    def test_skipped_count(self):
        p = Paginator(skip=2)
        list(p.feed_many(LINES))
        assert p.skipped == 2

    def test_skip_all_lines(self):
        p = Paginator(skip=10)
        result = list(p.feed_many(LINES))
        assert result == []


# ---------------------------------------------------------------------------
# skip + page_size combined
# ---------------------------------------------------------------------------

class TestPaginatorSkipAndPageSize:
    def test_skip_then_page(self):
        p = Paginator(page_size=2, skip=2)
        result = list(p.feed_many(LINES))
        assert result == ["line3", "line4"]

    def test_counts_correct(self):
        p = Paginator(page_size=2, skip=1)
        list(p.feed_many(LINES))
        assert p.skipped == 1
        assert p.emitted == 2


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

class TestPaginatorReset:
    def test_reset_clears_counters(self):
        p = Paginator(page_size=2, skip=1)
        list(p.feed_many(LINES))
        p.reset()
        assert p.emitted == 0
        assert p.skipped == 0
        assert p.is_full is False

    def test_can_reuse_after_reset(self):
        p = Paginator(page_size=2)
        list(p.feed_many(LINES))
        p.reset()
        result = list(p.feed_many(LINES))
        assert result == ["line1", "line2"]
