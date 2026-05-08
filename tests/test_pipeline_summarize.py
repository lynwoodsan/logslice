"""Integration tests: Summarizer wired into the pipeline."""
from __future__ import annotations

from typing import List, Optional

from logslice.summarizer import Summarizer


LOG_LINES = [
    "2024-03-01 10:00:00 INFO  app started\n",
    "2024-03-01 10:00:01 DEBUG loading config\n",
    "2024-03-01 10:00:02 ERROR failed to connect\n",
    "2024-03-01 10:00:03 WARNING retry attempt 1\n",
    "2024-03-01 10:00:04 INFO  connected\n",
]

LEVELS = ["INFO", "DEBUG", "ERROR", "WARNING", "INFO"]


def _run(
    lines: List[str],
    levels: Optional[List[str]] = None,
    matched_flags: Optional[List[bool]] = None,
    top_n: int = 5,
) -> tuple:
    """Run lines through Summarizer; return (output_lines, summary_lines)."""
    s = Summarizer(top_n=top_n)
    output = list(s.feed(lines, levels=levels, matched_flags=matched_flags))
    summary = s.format_summary()
    return output, summary


class TestPipelineSummarize:
    def test_all_lines_pass_through(self):
        output, _ = _run(LOG_LINES)
        assert output == LOG_LINES

    def test_summary_total_correct(self):
        _, summary = _run(LOG_LINES, levels=LEVELS)
        joined = "\n".join(summary)
        assert f"Total lines   : {len(LOG_LINES)}" in joined

    def test_summary_matched_with_flags(self):
        flags = [True, False, True, False, True]
        _, summary = _run(LOG_LINES, matched_flags=flags)
        joined = "\n".join(summary)
        assert "Matched lines : 3" in joined

    def test_summary_error_sample_captured(self):
        _, summary = _run(LOG_LINES, levels=LEVELS)
        joined = "\n".join(summary)
        assert "failed to connect" in joined

    def test_empty_input_summary_zeros(self):
        _, summary = _run([])
        joined = "\n".join(summary)
        assert "Total lines   : 0" in joined
        assert "Matched lines : 0" in joined

    def test_custom_label_appears_in_summary(self):
        s = Summarizer(label="--- REPORT ---")
        list(s.feed(LOG_LINES, levels=LEVELS))
        summary = s.format_summary()
        assert summary[0] == "--- REPORT ---"
