"""Tests for logslice.pipeline_template."""
from logslice.pipeline_template import apply_template


def _run(lines, template=None):
    return list(apply_template(iter(lines), template=template))


class TestApplyTemplateDisabled:
    def test_none_template_passes_all(self):
        lines = ["line one", "line two", "line three"]
        assert _run(lines, template=None) == lines

    def test_empty_string_passes_all(self):
        lines = ["a", "b"]
        assert _run(lines, template="") == lines

    def test_none_template_empty_input(self):
        assert _run([], template=None) == []


class TestApplyTemplateEnabled:
    def test_raw_template_preserves_content(self):
        lines = ["hello world", "foo bar"]
        result = _run(lines, template="{raw}")
        assert result == lines

    def test_prefix_added_to_every_line(self):
        lines = ["alpha", "beta"]
        result = _run(lines, template="LOG: {message}")
        assert result == ["LOG: alpha", "LOG: beta"]

    def test_level_extracted_into_template(self):
        lines = ["2024-01-01 12:00:00 ERROR disk full"]
        result = _run(lines, template="[{level}] {message}")
        assert result[0].startswith("[ERROR]")

    def test_unknown_placeholder_falls_back_to_line(self):
        lines = ["some line"]
        result = _run(lines, template="{nonexistent}")
        assert result == ["some line"]

    def test_empty_lines_handled(self):
        result = _run([], template="{raw}")
        assert result == []

    def test_multiple_lines_all_formatted(self):
        lines = ["a", "b", "c"]
        result = _run(lines, template=">{message}<")
        assert result == [">a<", ">b<", ">c<"]

    def test_literal_template_same_for_all(self):
        lines = ["x", "y", "z"]
        result = _run(lines, template="FIXED")
        assert result == ["FIXED", "FIXED", "FIXED"]
