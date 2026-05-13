"""Integration tests for MaskFilter wired into a simple pipeline."""

from __future__ import annotations

from typing import Iterator, List, Optional

from logslice.maskfilter import MaskFilter


def _run(
    lines: List[str],
    fields: Optional[List[str]] = None,
    mask: str = "***",
) -> List[str]:
    """Run lines through MaskFilter when fields are provided."""
    if not fields:
        return list(lines)
    mf = MaskFilter(fields=fields, mask=mask)
    return list(mf.feed(iter(lines)))


class TestPipelineMaskDisabled:
    def test_no_fields_returns_all_lines(self):
        lines = ["password=secret", "user=alice"]
        result = _run(lines, fields=None)
        assert result == lines

    def test_empty_fields_returns_all_lines(self):
        lines = ["token=abc123"]
        result = _run(lines, fields=[])
        assert result == lines


class TestPipelineMaskEnabled:
    def test_single_field_masked(self):
        lines = ["user=alice password=hunter2 status=ok"]
        result = _run(lines, fields=["password"])
        assert "hunter2" not in result[0]
        assert "user=alice" in result[0]
        assert "status=ok" in result[0]

    def test_multiple_fields_masked(self):
        lines = ["password=abc token=xyz user=bob"]
        result = _run(lines, fields=["password", "token"])
        assert "abc" not in result[0]
        assert "xyz" not in result[0]
        assert "user=bob" in result[0]

    def test_custom_mask_string(self):
        lines = ["apikey=supersecret"]
        result = _run(lines, fields=["apikey"], mask="[MASKED]")
        assert "[MASKED]" in result[0]
        assert "supersecret" not in result[0]

    def test_line_count_preserved(self):
        lines = ["a=1", "b=2", "password=x", "c=3"]
        result = _run(lines, fields=["password"])
        assert len(result) == 4

    def test_unrelated_lines_unchanged(self):
        lines = ["INFO server started", "DEBUG listening on 8080"]
        result = _run(lines, fields=["password"])
        assert result == lines
