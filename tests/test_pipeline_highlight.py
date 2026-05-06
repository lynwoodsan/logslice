"""Tests for highlight integration inside build_pipeline."""

from logslice.pipeline import build_pipeline

ANSI_RESET = "\033[0m"

LINES = [
    "2024-01-01T10:00:00 INFO  hello world",
    "2024-01-01T10:01:00 ERROR hello error",
]


def _run(**kwargs):
    return list(build_pipeline(LINES, **kwargs))


class TestHighlightIntegration:
    def test_no_color_no_ansi(self):
        result = _run(pattern="hello", color=False)
        assert all(ANSI_RESET not in r for r in result)

    def test_color_wraps_match(self):
        result = _run(pattern="hello", color=True)
        assert any(ANSI_RESET in r for r in result)

    def test_color_without_pattern_no_ansi(self):
        result = _run(color=True)
        assert all(ANSI_RESET not in r for r in result)

    def test_only_matched_lines_highlighted(self):
        # With before context, context lines should NOT be highlighted
        result = _run(pattern="error", color=True, before=1)
        highlighted = [r for r in result if ANSI_RESET in r]
        assert all("error" in r.lower() for r in highlighted)
