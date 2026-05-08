"""Tests for logslice.linenum module."""

import pytest
from logslice.linenum import LineNumberAnnotator, strip_line_number


class TestLineNumberAnnotatorInit:
    def test_default_values(self):
        ann = LineNumberAnnotator()
        assert ann.start == 1
        assert ann.pad_width == 0
        assert ann.separator == ":"
        assert ann.current == 1

    def test_custom_start(self):
        ann = LineNumberAnnotator(start=10)
        assert ann.current == 10

    def test_invalid_start_raises(self):
        with pytest.raises(ValueError, match="start must be"):
            LineNumberAnnotator(start=0)

    def test_invalid_pad_width_raises(self):
        with pytest.raises(ValueError, match="pad_width must be"):
            LineNumberAnnotator(pad_width=-1)


class TestAnnotate:
    def test_annotates_first_line(self):
        ann = LineNumberAnnotator()
        result = ann.annotate("hello")
        assert result == "1:hello"

    def test_counter_increments(self):
        ann = LineNumberAnnotator()
        ann.annotate("a")
        ann.annotate("b")
        assert ann.current == 3

    def test_custom_separator(self):
        ann = LineNumberAnnotator(separator=" | ")
        result = ann.annotate("msg")
        assert result == "1 | msg"

    def test_pad_width_right_justifies(self):
        ann = LineNumberAnnotator(pad_width=4)
        result = ann.annotate("line")
        assert result == "   1:line"

    def test_custom_start_reflected_in_annotation(self):
        ann = LineNumberAnnotator(start=5)
        result = ann.annotate("x")
        assert result == "5:x"


class TestFeed:
    def test_feed_annotates_all_lines(self):
        ann = LineNumberAnnotator()
        lines = ["alpha", "beta", "gamma"]
        result = list(ann.feed(iter(lines)))
        assert result == ["1:alpha", "2:beta", "3:gamma"]

    def test_feed_no_annotate_passes_through(self):
        ann = LineNumberAnnotator()
        lines = ["a", "b"]
        result = list(ann.feed(iter(lines), annotate=False))
        assert result == ["a", "b"]
        assert ann.current == 3

    def test_feed_empty_iterator(self):
        ann = LineNumberAnnotator()
        result = list(ann.feed(iter([])))
        assert result == []
        assert ann.current == 1


class TestReset:
    def test_reset_restores_start(self):
        ann = LineNumberAnnotator(start=3)
        ann.annotate("x")
        ann.annotate("y")
        ann.reset()
        assert ann.current == 3


class TestStripLineNumber:
    def test_strips_number_and_text(self):
        num, text = strip_line_number("42:some message")
        assert num == 42
        assert text == "some message"

    def test_custom_separator(self):
        num, text = strip_line_number("7 | hello", separator=" | ")
        assert num == 7
        assert text == "hello"

    def test_no_separator_raises(self):
        with pytest.raises(ValueError, match="No separator"):
            strip_line_number("no separator here")

    def test_non_numeric_prefix_raises(self):
        with pytest.raises(ValueError, match="not numeric"):
            strip_line_number("abc:message")

    def test_padded_number_parsed(self):
        num, text = strip_line_number("  10:padded")
        assert num == 10
        assert text == "padded"
