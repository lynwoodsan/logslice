"""Tests for logslice.labeler.Labeler."""
import pytest
from logslice.labeler import Labeler


class TestLabelerInit:
    def test_default_separator(self):
        lb = Labeler(label="APP")
        assert lb.separator == " | "

    def test_custom_separator(self):
        lb = Labeler(label="APP", separator=" >> ")
        assert lb.separator == " >> "

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            Labeler(label="")

    def test_none_separator_raises(self):
        with pytest.raises(ValueError, match="separator"):
            Labeler(label="APP", separator=None)

    def test_initial_counts_zero(self):
        lb = Labeler(label="APP")
        assert lb.labeled_count == 0
        assert lb.skipped_count == 0


class TestLabelerAnnotate:
    def test_no_pattern_labels_every_line(self):
        lb = Labeler(label="SVC")
        result = lb.annotate("hello world")
        assert result == "SVC | hello world"

    def test_custom_separator_used(self):
        lb = Labeler(label="SVC", separator=":")
        assert lb.annotate("msg") == "SVC:msg"

    def test_pattern_match_labels_line(self):
        lb = Labeler(label="ERR", pattern=r"ERROR")
        result = lb.annotate("2024-01-01 ERROR something")
        assert result.startswith("ERR | ")

    def test_pattern_no_match_returns_unchanged(self):
        lb = Labeler(label="ERR", pattern=r"ERROR")
        result = lb.annotate("2024-01-01 INFO something")
        assert result == "2024-01-01 INFO something"

    def test_labeled_count_increments(self):
        lb = Labeler(label="APP")
        lb.annotate("line one")
        lb.annotate("line two")
        assert lb.labeled_count == 2

    def test_skipped_count_increments_on_no_match(self):
        lb = Labeler(label="ERR", pattern=r"ERROR")
        lb.annotate("INFO line")
        lb.annotate("DEBUG line")
        assert lb.skipped_count == 2
        assert lb.labeled_count == 0

    def test_mixed_match_and_skip(self):
        lb = Labeler(label="ERR", pattern=r"ERROR")
        lb.annotate("ERROR boom")
        lb.annotate("INFO ok")
        lb.annotate("ERROR again")
        assert lb.labeled_count == 2
        assert lb.skipped_count == 1


class TestLabelerFeed:
    def test_feed_labels_all_lines_no_pattern(self):
        lb = Labeler(label="SVC")
        lines = ["alpha", "beta", "gamma"]
        result = list(lb.feed(iter(lines)))
        assert result == ["SVC | alpha", "SVC | beta", "SVC | gamma"]

    def test_feed_filters_by_pattern(self):
        lb = Labeler(label="E", pattern=r"err")
        lines = ["err: bad", "ok line", "err: worse"]
        result = list(lb.feed(iter(lines)))
        assert result == ["E | err: bad", "ok line", "E | err: worse"]

    def test_feed_empty_input(self):
        lb = Labeler(label="X")
        assert list(lb.feed(iter([]))) == []
