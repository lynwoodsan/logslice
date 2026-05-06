"""Integration tests: redaction wired into the pipeline."""

from __future__ import annotations

from typing import List

from logslice.pipeline import build_pipeline


def _run(lines: List[str], **kwargs) -> List[str]:
    """Run lines through the pipeline and return collected output."""
    pipeline = build_pipeline(**kwargs)
    out: List[str] = []
    for line in lines:
        result = pipeline(line)
        if result is not None:
            out.append(result)
    return out


class TestPipelineRedact:
    _LINES = [
        "INFO  request started",
        "DEBUG password=hunter2 supplied",
        "ERROR token=abc123 rejected",
        "INFO  all clear",
    ]

    def test_no_redact_preserves_secrets(self):
        out = _run(self._LINES)
        assert any("password=hunter2" in l for l in out)

    def test_redact_flag_hides_password(self):
        out = _run(self._LINES, redact=True)
        assert not any("hunter2" in l for l in out)
        assert any("password=***" in l for l in out)

    def test_redact_flag_hides_token(self):
        out = _run(self._LINES, redact=True)
        assert not any("abc123" in l for l in out)
        assert any("token=***" in l for l in out)

    def test_redact_leaves_clean_lines_intact(self):
        out = _run(self._LINES, redact=True)
        assert any("INFO  request started" in l for l in out)
        assert any("INFO  all clear" in l for l in out)

    def test_redact_combined_with_level_filter(self):
        out = _run(self._LINES, level="ERROR", redact=True)
        assert len(out) == 1
        assert "token=***" in out[0]
        assert "abc123" not in out[0]
