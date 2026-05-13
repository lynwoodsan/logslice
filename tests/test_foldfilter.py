"""Tests for logslice.foldfilter."""
import pytest
from logslice.foldfilter import FoldFilter


def _feed_all(lines):
    ff = FoldFilter()
    out = []
    for ln in lines:
        out.extend(ff.feed(ln))
    out.extend(ff.finalize())
    return out


class TestFoldFilterInit:
    def test_default_min_repeats(self):
        ff = FoldFilter()
        assert ff.min_repeats == 2

    def test_custom_min_repeats(self):
        ff = FoldFilter(min_repeats=3)
        assert ff.min_repeats == 3

    def test_invalid_min_repeats_raises(self):
        with pytest.raises(ValueError, match="min_repeats"):
            FoldFilter(min_repeats=1)

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            FoldFilter(label="")

    def test_initial_folded_count_zero(self):
        assert FoldFilter().folded_count == 0


class TestFoldFilterFeed:
    def test_unique_lines_pass_through(self):
        result = _feed_all(["alpha", "beta", "gamma"])
        assert result == ["alpha", "beta", "gamma"]

    def test_single_occurrence_not_folded(self):
        result = _feed_all(["only once"])
        assert result == ["only once"]

    def test_two_repeats_folded(self):
        result = _feed_all(["dup", "dup"])
        assert result == ["dup (x2)"]

    def test_five_repeats_folded(self):
        result = _feed_all(["msg"] * 5)
        assert result == ["msg (x5)"]

    def test_non_consecutive_not_folded(self):
        result = _feed_all(["a", "b", "a"])
        assert result == ["a", "b", "a"]

    def test_mixed_consecutive_and_unique(self):
        lines = ["x", "x", "x", "y", "z", "z"]
        result = _feed_all(lines)
        assert result == ["x (x3)", "y", "z (x2)"]

    def test_custom_label_format(self):
        ff = FoldFilter(label="[repeated {count} times]")
        out = []
        for ln in ["hi", "hi", "hi"]:
            out.extend(ff.feed(ln))
        out.extend(ff.finalize())
        assert out == ["hi [repeated 3 times]"]

    def test_min_repeats_three_keeps_two_separate(self):
        ff = FoldFilter(min_repeats=3)
        out = []
        for ln in ["a", "a"]:
            out.extend(ff.feed(ln))
        out.extend(ff.finalize())
        assert out == ["a", "a"]

    def test_min_repeats_three_folds_three(self):
        ff = FoldFilter(min_repeats=3)
        out = []
        for ln in ["a", "a", "a"]:
            out.extend(ff.feed(ln))
        out.extend(ff.finalize())
        assert out == ["a (x3)"]

    def test_folded_count_tracks_suppressed(self):
        ff = FoldFilter()
        out = []
        for ln in ["x"] * 4:
            out.extend(ff.feed(ln))
        out.extend(ff.finalize())
        # 4 lines folded to 1 => 3 suppressed
        assert ff.folded_count == 3

    def test_trailing_newline_stripped(self):
        result = _feed_all(["line\n", "line\n"])
        assert result == ["line (x2)"]

    def test_empty_stream_returns_empty(self):
        result = _feed_all([])
        assert result == []
