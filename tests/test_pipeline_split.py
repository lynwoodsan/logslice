"""Integration tests for Splitter wired into the pipeline."""
import os
import pytest

from logslice.splitter import Splitter


@pytest.fixture()
def split_dir(tmp_path):
    return str(tmp_path / "out")


def _run_with_split(lines, split_dir, separator=" | "):
    """Feed lines through Splitter and return (output_lines, splitter)."""
    splitter = Splitter(output_dir=split_dir, separator=separator)
    output = list(splitter.feed_all(lines))
    splitter.close()
    return output, splitter


class TestPipelineSplit:
    def test_all_lines_pass_through(self, split_dir):
        lines = ["svc-a | INFO boot", "svc-b | WARN slow", "bare line"]
        output, _ = _run_with_split(lines, split_dir)
        assert output == lines

    def test_split_files_contain_correct_content(self, split_dir):
        lines = ["svc-a | INFO boot", "svc-a | ERROR crash", "svc-b | WARN slow"]
        _run_with_split(lines, split_dir)
        a_path = os.path.join(split_dir, "svc-a.log")
        b_path = os.path.join(split_dir, "svc-b.log")
        a_content = open(a_path).read()
        b_content = open(b_path).read()
        assert "INFO boot" in a_content
        assert "ERROR crash" in a_content
        assert "WARN slow" in b_content
        assert "INFO" not in b_content

    def test_unlabeled_lines_not_written_to_any_file(self, split_dir):
        lines = ["just a plain log line", "another plain line"]
        _run_with_split(lines, split_dir)
        assert os.listdir(split_dir) == []

    def test_custom_separator_respected(self, split_dir):
        lines = ["worker :: DEBUG task done", "worker :: INFO idle"]
        _run_with_split(lines, split_dir, separator=" :: ")
        path = os.path.join(split_dir, "worker.log")
        assert os.path.exists(path)
        content = open(path).read()
        assert "DEBUG task done" in content
        assert "INFO idle" in content

    def test_line_counts_match_written_lines(self, split_dir):
        lines = ["a | x", "a | y", "b | z", "plain"]
        _, splitter = _run_with_split(lines, split_dir)
        counts = splitter.line_counts()
        assert counts.get("a") == 2
        assert counts.get("b") == 1
        assert "plain" not in counts
