"""Tests for logslice.pipeline_fold.apply_fold."""
import pytest
from logslice.pipeline_fold import apply_fold


def _run(lines, **kwargs):
    return list(apply_fold(lines, **kwargs))


class TestApplyFoldDisabled:
    def test_disabled_passes_all_lines(self):
        lines = ["a", "a", "b"]
        assert _run(lines) == lines

    def test_disabled_empty_input(self):
        assert _run([]) == []

    def test_disabled_preserves_duplicates(self):
        lines = ["dup"] * 5
        assert _run(lines) == lines


class TestApplyFoldEnabled:
    def test_unique_lines_unchanged(self):
        lines = ["foo", "bar", "baz"]
        result = _run(lines, enabled=True)
        assert result == ["foo", "bar", "baz"]

    def test_consecutive_duplicates_folded(self):
        lines = ["err", "err", "err"]
        result = _run(lines, enabled=True)
        assert result == ["err (x3)"]

    def test_non_consecutive_not_folded(self):
        lines = ["a", "b", "a"]
        result = _run(lines, enabled=True)
        assert result == ["a", "b", "a"]

    def test_custom_min_repeats(self):
        lines = ["x", "x"]  # only 2 repeats
        result = _run(lines, enabled=True, min_repeats=3)
        assert result == ["x", "x"]  # not folded

    def test_custom_label(self):
        lines = ["msg", "msg"]
        result = _run(lines, enabled=True, label="[x{count}]")
        assert result == ["msg [x2]"]

    def test_empty_input_returns_empty(self):
        assert _run([], enabled=True) == []

    def test_mixed_stream(self):
        lines = ["a", "b", "b", "c", "c", "c", "d"]
        result = _run(lines, enabled=True)
        assert result == ["a", "b (x2)", "c (x3)", "d"]
