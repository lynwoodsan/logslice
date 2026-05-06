"""Tests for logslice.multiline."""

from __future__ import annotations

from typing import List

import pytest

from logslice.multiline import MultilineAssembler, assemble_multiline


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _feed_all(assembler: MultilineAssembler, lines: List[str]) -> List[str]:
    out: List[str] = []
    for line in lines:
        out.extend(assembler.feed(line))
    out.extend(assembler.finalize())
    return out


# ---------------------------------------------------------------------------
# MultilineAssembler
# ---------------------------------------------------------------------------

class TestMultilineAssembler:
    def test_single_line_emitted_on_next_header(self):
        asm = MultilineAssembler()
        result = _feed_all(asm, ["INFO start\n", "INFO end\n"])
        assert result[0] == "INFO start"
        assert result[1] == "INFO end"

    def test_continuation_joined_to_header(self):
        asm = MultilineAssembler()
        lines = ["ERROR boom\n", "    at Foo.bar(Foo.java:10)\n", "INFO next\n"]
        result = _feed_all(asm, lines)
        assert len(result) == 2
        assert "at Foo.bar" in result[0]
        assert result[0].startswith("ERROR boom")

    def test_multiple_continuations_joined(self):
        asm = MultilineAssembler()
        lines = [
            "ERROR multi\n",
            "    line2\n",
            "    line3\n",
            "INFO done\n",
        ]
        result = _feed_all(asm, lines)
        assert len(result) == 2
        assert "line2" in result[0]
        assert "line3" in result[0]

    def test_finalize_flushes_last_entry(self):
        asm = MultilineAssembler()
        lines = ["ERROR last\n", "    trace\n"]
        result = _feed_all(asm, lines)
        assert len(result) == 1
        assert "trace" in result[0]

    def test_custom_separator(self):
        asm = MultilineAssembler(separator="|")
        lines = ["WARN head\n", "    cont\n", "INFO end\n"]
        result = _feed_all(asm, lines)
        assert "|" in result[0]

    def test_no_continuations_returns_all_lines(self):
        asm = MultilineAssembler()
        lines = ["INFO a\n", "INFO b\n", "INFO c\n"]
        result = _feed_all(asm, lines)
        assert result == ["INFO a", "INFO b", "INFO c"]

    def test_empty_input_returns_empty(self):
        asm = MultilineAssembler()
        result = _feed_all(asm, [])
        assert result == []


# ---------------------------------------------------------------------------
# assemble_multiline convenience wrapper
# ---------------------------------------------------------------------------

class TestAssembleMultiline:
    def test_default_pattern_joins_indented(self):
        lines = ["ERROR x\n", "  trace\n", "INFO y\n"]
        result = list(assemble_multiline(iter(lines)))
        assert len(result) == 2
        assert "trace" in result[0]

    def test_custom_pattern(self):
        lines = ["START a\n", "CONT b\n", "START c\n"]
        result = list(assemble_multiline(iter(lines), pattern=r"^CONT"))
        assert len(result) == 2
        assert "CONT b" in result[0]

    def test_no_pattern_match_all_separate(self):
        lines = ["A\n", "B\n", "C\n"]
        # pattern that never matches → every line is a header
        result = list(assemble_multiline(iter(lines), pattern=r"^NEVER"))
        assert result == ["A", "B", "C"]
