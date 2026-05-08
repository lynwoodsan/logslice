"""Tests for logslice.merger.Merger."""
from logslice.merger import Merger


class TestMergerInit:
    def test_default_separator(self):
        m = Merger()
        assert m.label_separator == " | "

    def test_custom_separator(self):
        m = Merger(label_separator=" :: ")
        assert m.label_separator == " :: "

    def test_initial_merged_count_zero(self):
        m = Merger()
        assert m.merged_count == 0


class TestMergerMerge:
    def test_empty_sources_yields_nothing(self):
        m = Merger()
        result = list(m.merge([]))
        assert result == []

    def test_single_source_yields_all_lines(self):
        m = Merger()
        lines = ["2024-01-01T00:00:01 INFO a", "2024-01-01T00:00:02 INFO b"]
        result = list(m.merge([("src", iter(lines))], prepend_label=False))
        assert result == lines

    def test_prepend_label_adds_prefix(self):
        m = Merger()
        lines = ["2024-01-01T00:00:01 INFO hello"]
        result = list(m.merge([("app", iter(lines))], prepend_label=True))
        assert result[0].startswith("app | ")

    def test_no_prepend_label_no_prefix(self):
        m = Merger()
        lines = ["2024-01-01T00:00:01 INFO hello"]
        result = list(m.merge([("app", iter(lines))], prepend_label=False))
        assert not result[0].startswith("app")

    def test_two_sources_merged_chronologically(self):
        m = Merger()
        a = ["2024-01-01T00:00:01 INFO first", "2024-01-01T00:00:03 INFO third"]
        b = ["2024-01-01T00:00:02 INFO second"]
        result = list(m.merge([("a", iter(a)), ("b", iter(b))], prepend_label=False))
        assert "first" in result[0]
        assert "second" in result[1]
        assert "third" in result[2]

    def test_merged_count_incremented(self):
        m = Merger()
        a = ["2024-01-01T00:00:01 INFO x"]
        b = ["2024-01-01T00:00:02 INFO y", "2024-01-01T00:00:03 INFO z"]
        list(m.merge([("a", iter(a)), ("b", iter(b))], prepend_label=False))
        assert m.merged_count == 3

    def test_lines_without_timestamps_still_emitted(self):
        m = Merger()
        lines = ["no timestamp here", "also no timestamp"]
        result = list(m.merge([("x", iter(lines))], prepend_label=False))
        assert len(result) == 2

    def test_label_separator_respected(self):
        m = Merger(label_separator=" >> ")
        lines = ["2024-01-01T00:00:01 INFO msg"]
        result = list(m.merge([("svc", iter(lines))], prepend_label=True))
        assert result[0].startswith("svc >> ")

    def test_stable_ordering_same_timestamp(self):
        """Lines with identical timestamps are ordered by label name."""
        m = Merger()
        a = ["2024-01-01T00:00:01 INFO from-a"]
        b = ["2024-01-01T00:00:01 INFO from-b"]
        result = list(m.merge([("a", iter(a)), ("b", iter(b))], prepend_label=True))
        assert result[0].startswith("a | ")
        assert result[1].startswith("b | ")
