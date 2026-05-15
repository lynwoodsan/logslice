"""Integration-style tests for DiffHighlighter wired into a simple pipeline."""
from __future__ import annotations

from typing import Iterator, List

from logslice.diffhighlighter import ANSI_CHANGED, ANSI_RESET, DiffHighlighter


def _run(lines: List[str], color: bool = False, marker: str = "> ") -> List[str]:
    """Feed *lines* through DiffHighlighter and return collected output."""
    dh = DiffHighlighter(color=color, marker=marker)
    return list(dh.feed(iter(lines)))


class TestDiffHighlightPipelineNoColor:
    def test_all_same_no_markers(self):
        out = _run(["INFO msg", "INFO msg", "INFO msg"])
        assert all(not l.startswith("> ") for l in out)

    def test_first_change_marked(self):
        out = _run(["INFO start", "ERROR boom"])
        assert out[1].startswith("> ")

    def test_unchanged_after_change_not_marked(self):
        out = _run(["a", "b", "b"])
        assert out[2] == "b"

    def test_empty_pipeline(self):
        out = _run([])
        assert out == []

    def test_single_line_no_marker(self):
        out = _run(["only line"])
        assert out == ["only line"]

    def test_alternating_lines_all_marked(self):
        out = _run(["a", "b", "a", "b"])
        # index 0 never marked; 1, 2, 3 all differ from predecessor
        assert not out[0].startswith("> ")
        assert out[1].startswith("> ")
        assert out[2].startswith("> ")
        assert out[3].startswith("> ")


class TestDiffHighlightPipelineColor:
    def test_changed_line_has_ansi(self):
        out = _run(["x", "y"], color=True)
        assert ANSI_CHANGED in out[1]
        assert ANSI_RESET in out[1]

    def test_unchanged_line_no_ansi(self):
        out = _run(["x", "x"], color=True)
        assert ANSI_CHANGED not in out[1]

    def test_custom_marker_in_color_output(self):
        out = _run(["a", "b"], color=True, marker=">> ")
        assert ">> b" in out[1]
