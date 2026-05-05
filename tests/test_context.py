"""Tests for logslice.context module."""

import pytest
from logslice.context import ContextBuffer, apply_context


class TestContextBuffer:
    def test_no_context_match_emits_line(self):
        buf = ContextBuffer(before=0, after=0)
        results = buf.feed("ERROR line", matched=True)
        assert results == [("ERROR line", False)]

    def test_no_context_no_match_emits_nothing(self):
        buf = ContextBuffer(before=0, after=0)
        results = buf.feed("DEBUG line", matched=False)
        assert results == []

    def test_before_context_emitted_on_match(self):
        buf = ContextBuffer(before=2, after=0)
        buf.feed("line1", matched=False)
        buf.feed("line2", matched=False)
        results = buf.feed("ERROR", matched=True)
        lines = [r[0] for r in results]
        assert "line1" in lines
        assert "line2" in lines
        assert "ERROR" in lines

    def test_before_context_marked_as_context(self):
        buf = ContextBuffer(before=1, after=0)
        buf.feed("pre", matched=False)
        results = buf.feed("match", matched=True)
        ctx_flags = {line: is_ctx for line, is_ctx in results}
        assert ctx_flags["pre"] is True
        assert ctx_flags["match"] is False

    def test_after_context_emitted(self):
        buf = ContextBuffer(before=0, after=2)
        buf.feed("match", matched=True)
        r1 = buf.feed("post1", matched=False)
        r2 = buf.feed("post2", matched=False)
        r3 = buf.feed("ignored", matched=False)
        assert r1 == [("post1", True)]
        assert r2 == [("post2", True)]
        assert r3 == []

    def test_pre_buffer_limited_to_before(self):
        buf = ContextBuffer(before=2, after=0)
        for i in range(5):
            buf.feed(f"line{i}", matched=False)
        results = buf.feed("match", matched=True)
        lines = [r[0] for r in results]
        assert "line2" in lines
        assert "line3" in lines
        assert "line4" not in lines  # maxlen=2 keeps last 2 before match

    def test_reset_clears_state(self):
        buf = ContextBuffer(before=2, after=2)
        buf.feed("pre", matched=False)
        buf.feed("match", matched=True)
        buf.reset()
        results = buf.feed("after_reset", matched=False)
        assert results == []


class TestApplyContext:
    def _pairs(self, matched_indices, total=5):
        return [(f"line{i}", i in matched_indices) for i in range(total)]

    def test_no_context_yields_only_matches(self):
        pairs = self._pairs({2})
        out = list(apply_context(pairs, before=0, after=0))
        assert len(out) == 1
        assert out[0] == ("line2", False)

    def test_after_context_includes_following_lines(self):
        pairs = self._pairs({1}, total=5)
        out = list(apply_context(pairs, before=0, after=2))
        out_lines = [line for line, _ in out]
        assert "line1" in out_lines
        assert "line2" in out_lines
        assert "line3" in out_lines
        assert "line4" not in out_lines

    def test_before_context_includes_preceding_lines(self):
        pairs = self._pairs({3}, total=5)
        out = list(apply_context(pairs, before=2, after=0))
        out_lines = [line for line, _ in out]
        assert "line1" in out_lines
        assert "line2" in out_lines
        assert "line3" in out_lines

    def test_context_lines_flagged_correctly(self):
        pairs = [("pre", False), ("match", True), ("post", False)]
        out = list(apply_context(pairs, before=1, after=1))
        flags = {line: is_ctx for line, is_ctx in out}
        assert flags["pre"] is True
        assert flags["match"] is False
        assert flags["post"] is True
