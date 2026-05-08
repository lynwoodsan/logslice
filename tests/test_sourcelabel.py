"""Tests for logslice.sourcelabel.SourceLabeler."""
import pytest
from logslice.sourcelabel import SourceLabeler


class TestSourceLabelerGetLabel:
    def test_basename_by_default(self):
        sl = SourceLabeler()
        assert sl.get_label("/var/log/app.log") == "app.log"

    def test_full_path_when_disabled(self):
        sl = SourceLabeler(use_basename=False)
        assert sl.get_label("/var/log/app.log") == "/var/log/app.log"

    def test_plain_filename_unchanged(self):
        sl = SourceLabeler()
        assert sl.get_label("app.log") == "app.log"


class TestSourceLabelerAnnotate:
    def test_annotates_line_with_basename(self):
        sl = SourceLabeler()
        result = sl.annotate("/logs/web.log", "GET /health 200")
        assert result == "web.log | GET /health 200"

    def test_custom_separator(self):
        sl = SourceLabeler(separator=" -> ")
        result = sl.annotate("app.log", "started")
        assert result == "app.log -> started"

    def test_same_path_reuses_labeler(self):
        sl = SourceLabeler()
        sl.annotate("app.log", "line 1")
        sl.annotate("app.log", "line 2")
        assert len(sl._labelers) == 1

    def test_different_paths_create_separate_labelers(self):
        sl = SourceLabeler()
        sl.annotate("a.log", "line")
        sl.annotate("b.log", "line")
        assert len(sl._labelers) == 2


class TestSourceLabelerFeedSource:
    def test_all_lines_labeled(self):
        sl = SourceLabeler()
        lines = ["alpha", "beta"]
        result = list(sl.feed_source("svc.log", iter(lines)))
        assert result == ["svc.log | alpha", "svc.log | beta"]

    def test_empty_source_yields_nothing(self):
        sl = SourceLabeler()
        assert list(sl.feed_source("x.log", iter([]))) == []


class TestSourceLabelerFeedMany:
    def test_merges_sources_in_order(self):
        sl = SourceLabeler()
        sources = [
            ("a.log", iter(["line1", "line2"])),
            ("b.log", iter(["lineA"])),
        ]
        result = list(sl.feed_many(sources))
        assert result == [
            "a.log | line1",
            "a.log | line2",
            "b.log | lineA",
        ]

    def test_total_labeled_across_sources(self):
        sl = SourceLabeler()
        sources = [
            ("a.log", iter(["x", "y"])),
            ("b.log", iter(["z"])),
        ]
        list(sl.feed_many(sources))
        assert sl.total_labeled() == 3
