"""Tests for logslice.splitter.Splitter."""
import os
import pytest

from logslice.splitter import Splitter


@pytest.fixture()
def split_dir(tmp_path):
    return str(tmp_path / "split_out")


class TestSplitterInit:
    def test_creates_output_dir(self, split_dir):
        Splitter(output_dir=split_dir)
        assert os.path.isdir(split_dir)

    def test_empty_output_dir_raises(self):
        with pytest.raises(ValueError, match="output_dir"):
            Splitter(output_dir="")

    def test_default_separator(self, split_dir):
        s = Splitter(output_dir=split_dir)
        assert s.separator == " | "

    def test_custom_separator(self, split_dir):
        s = Splitter(output_dir=split_dir, separator=" :: ")
        assert s.separator == " :: "


class TestSplitterFeed:
    def test_unlabeled_line_returned_unchanged(self, split_dir):
        s = Splitter(output_dir=split_dir)
        result = s.feed("no separator here")
        assert result == "no separator here"

    def test_unlabeled_line_creates_no_file(self, split_dir):
        s = Splitter(output_dir=split_dir)
        s.feed("plain line")
        assert os.listdir(split_dir) == []

    def test_labeled_line_creates_file(self, split_dir):
        s = Splitter(output_dir=split_dir)
        s.feed("app.log | ERROR something failed")
        s.close()
        assert "app.log.log" in os.listdir(split_dir)

    def test_labeled_line_content_written(self, split_dir):
        s = Splitter(output_dir=split_dir)
        s.feed("app.log | ERROR something failed")
        s.close()
        path = os.path.join(split_dir, "app.log.log")
        content = open(path).read()
        assert "ERROR something failed" in content

    def test_feed_returns_original_line(self, split_dir):
        s = Splitter(output_dir=split_dir)
        line = "app.log | INFO started"
        assert s.feed(line) == line
        s.close()

    def test_multiple_labels_create_separate_files(self, split_dir):
        s = Splitter(output_dir=split_dir)
        s.feed("a.log | line one")
        s.feed("b.log | line two")
        s.close()
        files = os.listdir(split_dir)
        assert "a.log.log" in files
        assert "b.log.log" in files

    def test_line_counts_tracked(self, split_dir):
        s = Splitter(output_dir=split_dir)
        s.feed("a.log | first")
        s.feed("a.log | second")
        s.feed("b.log | only")
        s.close()
        counts = s.line_counts()
        assert counts["a.log"] == 2
        assert counts["b.log"] == 1

    def test_feed_all_yields_all_lines(self, split_dir):
        s = Splitter(output_dir=split_dir)
        lines = ["a.log | one", "plain", "b.log | two"]
        result = list(s.feed_all(lines))
        s.close()
        assert result == lines


class TestSplitterContextManager:
    def test_context_manager_closes_handles(self, split_dir):
        with Splitter(output_dir=split_dir) as s:
            s.feed("x.log | hello")
        # After __exit__, handles dict should be empty
        assert s._handles == {}
