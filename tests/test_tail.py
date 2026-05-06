"""Tests for logslice.tail."""

import pytest

from logslice.bookmark import Bookmark
from logslice.tail import read_from_bookmark, tail_file


@pytest.fixture
def log_file(tmp_path):
    f = tmp_path / "app.log"
    f.write_text("alpha\nbeta\ngamma\n")
    return f


@pytest.fixture
def tmp_bookmark_dir(tmp_path):
    return tmp_path / "bm"


class TestReadFromBookmark:
    def test_reads_all_lines_from_start(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        lines = list(read_from_bookmark(str(log_file), bm))
        assert lines == ["alpha", "beta", "gamma"]

    def test_advances_bookmark_after_read(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        list(read_from_bookmark(str(log_file), bm))
        assert bm.load() > 0

    def test_second_read_returns_only_new_lines(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        list(read_from_bookmark(str(log_file), bm))
        with open(str(log_file), "a") as fh:
            fh.write("delta\n")
        lines = list(read_from_bookmark(str(log_file), bm))
        assert lines == ["delta"]

    def test_second_read_empty_when_no_new_lines(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        list(read_from_bookmark(str(log_file), bm))
        lines = list(read_from_bookmark(str(log_file), bm))
        assert lines == []

    def test_strips_trailing_newline(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        lines = list(read_from_bookmark(str(log_file), bm))
        assert all("\n" not in line for line in lines)


class TestTailFile:
    def test_yields_existing_lines_from_start(self, log_file, tmp_path):
        lines = list(
            tail_file(str(log_file), poll_interval=0, max_iterations=1)
        )
        assert "alpha" in lines
        assert "beta" in lines
        assert "gamma" in lines

    def test_starts_from_bookmark_offset(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        # consume all lines first to advance bookmark
        list(read_from_bookmark(str(log_file), bm))
        # append a new line
        with open(str(log_file), "a") as fh:
            fh.write("epsilon\n")
        lines = list(
            tail_file(str(log_file), bookmark=bm, poll_interval=0, max_iterations=1)
        )
        assert lines == ["epsilon"]

    def test_updates_bookmark_while_tailing(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(str(log_file), bookmark_dir=tmp_bookmark_dir)
        initial = bm.load()
        list(tail_file(str(log_file), bookmark=bm, poll_interval=0, max_iterations=1))
        assert bm.load() > initial

    def test_strips_newlines(self, log_file):
        lines = list(
            tail_file(str(log_file), poll_interval=0, max_iterations=1)
        )
        assert all("\n" not in line for line in lines)
