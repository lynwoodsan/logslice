"""Tests for logslice.bookmark."""

import json
import pytest
from pathlib import Path

from logslice.bookmark import Bookmark


@pytest.fixture
def tmp_bookmark_dir(tmp_path):
    return tmp_path / "bookmarks"


@pytest.fixture
def log_file(tmp_path):
    f = tmp_path / "app.log"
    f.write_text("line1\nline2\n")
    return str(f)


class TestBookmarkLoad:
    def test_returns_zero_when_no_bookmark(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        assert bm.load() == 0

    def test_returns_saved_offset(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.save(128)
        assert bm.load() == 128

    def test_returns_zero_on_corrupt_file(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        tmp_bookmark_dir.mkdir(parents=True, exist_ok=True)
        bm._bookmark_file.write_text("not json")
        assert bm.load() == 0

    def test_returns_zero_on_missing_offset_key(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        tmp_bookmark_dir.mkdir(parents=True, exist_ok=True)
        bm._bookmark_file.write_text(json.dumps({"log_path": log_file}))
        assert bm.load() == 0


class TestBookmarkSave:
    def test_creates_bookmark_dir(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        assert not tmp_bookmark_dir.exists()
        bm.save(42)
        assert tmp_bookmark_dir.exists()

    def test_bookmark_file_contains_offset(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.save(256)
        data = json.loads(bm._bookmark_file.read_text())
        assert data["offset"] == 256

    def test_bookmark_file_contains_log_path(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.save(0)
        data = json.loads(bm._bookmark_file.read_text())
        assert "log_path" in data

    def test_overwrite_updates_offset(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.save(10)
        bm.save(999)
        assert bm.load() == 999


class TestBookmarkClearExists:
    def test_exists_false_before_save(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        assert not bm.exists()

    def test_exists_true_after_save(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.save(1)
        assert bm.exists()

    def test_clear_removes_bookmark(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.save(1)
        bm.clear()
        assert not bm.exists()

    def test_clear_noop_when_no_bookmark(self, log_file, tmp_bookmark_dir):
        bm = Bookmark(log_file, bookmark_dir=tmp_bookmark_dir)
        bm.clear()  # should not raise
        assert not bm.exists()
