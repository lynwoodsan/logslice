"""Tests for the logslice CLI argument parsing and main entry point."""

import gzip
import os
import tempfile
import pytest
from datetime import datetime

from logslice.cli import build_parser, parse_datetime, main


# ---------------------------------------------------------------------------
# parse_datetime
# ---------------------------------------------------------------------------

class TestParseDatetime:
    def test_iso_with_time(self):
        dt = parse_datetime("2024-03-15T12:30:45")
        assert dt == datetime(2024, 3, 15, 12, 30, 45)

    def test_space_with_time(self):
        dt = parse_datetime("2024-03-15 08:00")
        assert dt == datetime(2024, 3, 15, 8, 0)

    def test_date_only(self):
        dt = parse_datetime("2024-01-01")
        assert dt == datetime(2024, 1, 1)

    def test_invalid_raises(self):
        import argparse
        with pytest.raises(argparse.ArgumentTypeError):
            parse_datetime("not-a-date")


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

class TestBuildParser:
    def setup_method(self):
        self.parser = build_parser()

    def test_defaults(self):
        args = self.parser.parse_args([])
        assert args.file is None
        assert args.start is None
        assert args.end is None
        assert args.level is None
        assert args.pattern is None
        assert args.no_color is False
        assert args.count is False

    def test_file_positional(self):
        args = self.parser.parse_args(["app.log"])
        assert args.file == "app.log"

    def test_level_flag(self):
        args = self.parser.parse_args(["--level", "ERROR"])
        assert args.level == "ERROR"

    def test_pattern_flag(self):
        args = self.parser.parse_args(["--pattern", "timeout"])
        assert args.pattern == "timeout"

    def test_no_color_flag(self):
        args = self.parser.parse_args(["--no-color"])
        assert args.no_color is True

    def test_count_flag(self):
        args = self.parser.parse_args(["--count"])
        assert args.count is True


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class TestMain:
    def _make_log(self, lines, suffix=".log"):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
        f.write("\n".join(lines) + "\n")
        f.close()
        return f.name

    def teardown_method(self):
        # cleanup handled per test
        pass

    def test_main_returns_zero(self):
        path = self._make_log(["2024-01-01 10:00:00 INFO hello"])
        try:
            rc = main([path])
            assert rc == 0
        finally:
            os.unlink(path)

    def test_main_count_flag(self, capsys):
        path = self._make_log([
            "2024-01-01 10:00:00 ERROR boom",
            "2024-01-01 10:01:00 INFO ok",
        ])
        try:
            main([path, "--level", "ERROR", "--count"])
            captured = capsys.readouterr()
            assert "1" in captured.out
        finally:
            os.unlink(path)

    def test_main_no_color_flag(self):
        path = self._make_log(["2024-01-01 10:00:00 WARNING watch out"])
        try:
            rc = main([path, "--no-color"])
            assert rc == 0
        finally:
            os.unlink(path)
