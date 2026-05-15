"""Tests for logslice.diffhighlighter."""
import pytest

from logslice.diffhighlighter import ANSI_CHANGED, ANSI_RESET, DiffHighlighter


class TestDiffHighlighterInit:
    def test_default_values(self):
        dh = DiffHighlighter()
        assert dh.color is False
        assert dh.marker == "> "

    def test_custom_values(self):
        dh = DiffHighlighter(color=True, marker="+ ")
        assert dh.color is True
        assert dh.marker == "+ "

    def test_none_marker_raises(self):
        with pytest.raises(ValueError):
            DiffHighlighter(marker=None)


class TestDiffHighlighterAnnotate:
    def test_first_line_never_marked(self):
        dh = DiffHighlighter()
        result = dh.annotate("hello")
        assert result == "hello"
        assert dh.changed_count == 0

    def test_identical_line_not_marked(self):
        dh = DiffHighlighter()
        dh.annotate("hello")
        result = dh.annotate("hello")
        assert result == "hello"
        assert dh.changed_count == 0

    def test_changed_line_gets_marker(self):
        dh = DiffHighlighter()
        dh.annotate("hello")
        result = dh.annotate("world")
        assert result == "> world"
        assert dh.changed_count == 1

    def test_custom_marker_applied(self):
        dh = DiffHighlighter(marker="+ ")
        dh.annotate("a")
        result = dh.annotate("b")
        assert result.startswith("+ ")

    def test_color_wraps_changed_line(self):
        dh = DiffHighlighter(color=True)
        dh.annotate("a")
        result = dh.annotate("b")
        assert result.startswith(ANSI_CHANGED)
        assert result.endswith(ANSI_RESET)
        assert "> b" in result

    def test_color_not_applied_to_unchanged(self):
        dh = DiffHighlighter(color=True)
        dh.annotate("same")
        result = dh.annotate("same")
        assert ANSI_CHANGED not in result

    def test_trailing_newline_stripped(self):
        dh = DiffHighlighter()
        result = dh.annotate("line\n")
        assert result == "line"

    def test_changed_count_increments(self):
        dh = DiffHighlighter()
        dh.annotate("a")
        dh.annotate("b")
        dh.annotate("b")
        dh.annotate("c")
        assert dh.changed_count == 2


class TestDiffHighlighterFeed:
    def test_feed_yields_all_lines(self):
        dh = DiffHighlighter()
        lines = list(dh.feed(iter(["a", "a", "b"])))
        assert len(lines) == 3

    def test_feed_marks_changes(self):
        dh = DiffHighlighter()
        lines = list(dh.feed(iter(["x", "y", "y"])))
        assert lines[1].startswith("> ")
        assert not lines[2].startswith("> ")

    def test_feed_empty_input(self):
        dh = DiffHighlighter()
        lines = list(dh.feed(iter([])))
        assert lines == []


class TestDiffHighlighterReset:
    def test_reset_clears_prev(self):
        dh = DiffHighlighter()
        dh.annotate("hello")
        dh.reset()
        # After reset the next line is treated as first — no marker
        result = dh.annotate("world")
        assert result == "world"

    def test_reset_clears_count(self):
        dh = DiffHighlighter()
        dh.annotate("a")
        dh.annotate("b")
        dh.reset()
        assert dh.changed_count == 0
