"""Tests for logslice.reader module."""

import gzip
import os
import tempfile

import pytest

from logslice.reader import count_lines, open_log_file, stream_lines


SAMPLE_LINES = [
    "2024-01-15 10:00:00 INFO  Application started",
    "2024-01-15 10:01:00 DEBUG Processing request",
    "2024-01-15 10:02:00 ERROR Something went wrong",
]


@pytest.fixture
def plain_log_file(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text("\n".join(SAMPLE_LINES) + "\n", encoding="utf-8")
    return str(log_file)


@pytest.fixture
def gzip_log_file(tmp_path):
    log_file = tmp_path / "app.log.gz"
    with gzip.open(log_file, "wt", encoding="utf-8") as f:
        f.write("\n".join(SAMPLE_LINES) + "\n")
    return str(log_file)


class TestOpenLogFile:
    def test_opens_plain_file(self, plain_log_file):
        fh = open_log_file(plain_log_file)
        content = fh.read()
        fh.close()
        assert "Application started" in content

    def test_opens_gzip_file(self, gzip_log_file):
        fh = open_log_file(gzip_log_file)
        content = fh.read()
        fh.close()
        assert "Application started" in content

    def test_raises_for_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Log file not found"):
            open_log_file("/nonexistent/path/app.log")


class TestStreamLines:
    def test_streams_all_lines(self, plain_log_file):
        lines = list(stream_lines(plain_log_file))
        assert lines == SAMPLE_LINES

    def test_streams_gzip_lines(self, gzip_log_file):
        lines = list(stream_lines(gzip_log_file))
        assert lines == SAMPLE_LINES

    def test_strips_newlines(self, plain_log_file):
        for line in stream_lines(plain_log_file):
            assert not line.endswith("\n")

    def test_empty_file_yields_nothing(self, tmp_path):
        empty = tmp_path / "empty.log"
        empty.write_text("", encoding="utf-8")
        lines = list(stream_lines(str(empty)))
        assert lines == []


class TestCountLines:
    def test_counts_plain_file(self, plain_log_file):
        assert count_lines(plain_log_file) == 3

    def test_counts_gzip_file(self, gzip_log_file):
        assert count_lines(gzip_log_file) == 3

    def test_empty_file_returns_zero(self, tmp_path):
        empty = tmp_path / "empty.log"
        empty.write_text("", encoding="utf-8")
        assert count_lines(str(empty)) == 0
