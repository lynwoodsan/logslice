"""End-to-end integration tests for the logslice CLI."""

import os
import subprocess
import sys
import tempfile

import pytest


def run_cli(*args, input_text=None):
    """Run the logslice CLI as a subprocess and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "logslice"] + list(args)
    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def sample_log(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2024-05-01 09:00:00 INFO  Service started\n"
        "2024-05-01 09:05:00 DEBUG Checking config\n"
        "2024-05-01 09:10:00 WARNING High memory usage\n"
        "2024-05-01 09:15:00 ERROR  Connection refused\n"
        "2024-05-01 09:20:00 INFO  Retrying connection\n"
    )
    return str(log_file)


class TestCLIIntegration:
    def test_no_filters_returns_all_lines(self, sample_log):
        rc, out, err = run_cli(sample_log, "--no-color")
        assert rc == 0
        assert "Service started" in out
        assert "Connection refused" in out
        assert out.count("\n") == 5

    def test_level_filter_error(self, sample_log):
        rc, out, _ = run_cli(sample_log, "--level", "ERROR", "--no-color")
        assert rc == 0
        assert "Connection refused" in out
        assert "Service started" not in out

    def test_pattern_filter(self, sample_log):
        rc, out, _ = run_cli(sample_log, "--pattern", "connect", "--no-color")
        assert rc == 0
        assert "Connection refused" in out
        assert "Retrying connection" in out
        assert "Service started" not in out

    def test_time_range_filter(self, sample_log):
        rc, out, _ = run_cli(
            sample_log,
            "--start", "2024-05-01T09:10:00",
            "--end", "2024-05-01T09:15:00",
            "--no-color",
        )
        assert rc == 0
        assert "High memory usage" in out
        assert "Connection refused" in out
        assert "Service started" not in out
        assert "Retrying connection" not in out

    def test_count_flag(self, sample_log):
        rc, out, _ = run_cli(sample_log, "--count", "--no-color")
        assert rc == 0
        assert "5" in out

    def test_count_with_level_filter(self, sample_log):
        rc, out, _ = run_cli(sample_log, "--level", "INFO", "--count", "--no-color")
        assert rc == 0
        assert "2" in out

    def test_stdin_input(self):
        log_data = (
            "2024-05-01 10:00:00 ERROR  Disk full\n"
            "2024-05-01 10:01:00 INFO  Cleanup done\n"
        )
        rc, out, _ = run_cli("--level", "ERROR", "--no-color", input_text=log_data)
        assert rc == 0
        assert "Disk full" in out
        assert "Cleanup done" not in out
