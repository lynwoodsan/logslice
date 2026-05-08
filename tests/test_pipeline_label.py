"""Integration tests: label stage wired into pipeline."""
from __future__ import annotations

from typing import List

import pytest
from logslice.labeler import Labeler
from logslice.pipeline import build_pipeline


def _run(lines: List[str], **kwargs) -> List[str]:
    """Helper: run lines through build_pipeline with given options."""
    cfg = dict(
        start=None,
        end=None,
        level=None,
        pattern=None,
        color=False,
        context_before=0,
        context_after=0,
        dedup_window=0,
        sample_every=None,
        sample_fraction=None,
        max_line_length=None,
        field_filters=None,
        redact=False,
        json_output=False,
        line_numbers=False,
        label=None,
        label_pattern=None,
        label_separator=" | ",
    )
    cfg.update(kwargs)
    results = []
    for line, _matched in build_pipeline(iter(lines), **cfg):
        results.append(line)
    return results


class TestLabelInPipeline:
    def test_no_label_returns_lines_unchanged(self):
        lines = ["INFO hello", "DEBUG world"]
        result = _run(lines)
        assert result == ["INFO hello", "DEBUG world"]

    def test_label_prepended_to_all_lines(self):
        lines = ["INFO hello", "DEBUG world"]
        result = _run(lines, label="SVC")
        assert result == ["SVC | INFO hello", "SVC | DEBUG world"]

    def test_label_with_custom_separator(self):
        lines = ["msg"]
        result = _run(lines, label="APP", label_separator=" >> ")
        assert result == ["APP >> msg"]

    def test_label_with_pattern_only_matching(self):
        lines = ["ERROR boom", "INFO ok", "ERROR again"]
        result = _run(lines, label="ERR", label_pattern=r"ERROR")
        assert result == ["ERR | ERROR boom", "INFO ok", "ERR | ERROR again"]
