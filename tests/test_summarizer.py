"""Tests for logslice.summarizer."""
import pytest
from logslice.summarizer import Summarizer


LINES = [
    "2024-01-01 INFO  service started",
    "2024-01-01 DEBUG checking config",
    "2024-01-01 ERROR disk full",
    "2024-01-01 WARNING low memory",
    "2024-01-01 ERROR network timeout",
    "2024-01-01 INFO  shutdown complete",
]

LEVELS = ["INFO", "DEBUG", "ERROR", "WARNING", "ERROR", "INFO"]
FLAGS = [True, False, True, True, True, True]


class TestSummarizerInit:
    def test_default_values(self):
        s = Summarizer()
        assert s.top_n == 5
        assert s.label == "=== Log Summary ==="

    def test_custom_values(self):
        s = Summarizer(top_n=3, label="--- Summary ---")
        assert s.top_n == 3
        assert s.label == "--- Summary ---"

    def test_invalid_top_n_raises(self):
        with pytest.raises(ValueError, match="top_n"):
            Summarizer(top_n=0)

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="label"):
            Summarizer(label="")


class TestSummarizerFeed:
    def test_lines_pass_through_unchanged(self):
        s = Summarizer()
        result = list(s.feed(LINES))
        assert result == LINES

    def test_total_incremented(self):
        s = Summarizer()
        list(s.feed(LINES))
        assert s.total == len(LINES)

    def test_matched_all_when_no_flags(self):
        s = Summarizer()
        list(s.feed(LINES))
        assert s.matched == len(LINES)

    def test_matched_respects_flags(self):
        s = Summarizer()
        list(s.feed(LINES, matched_flags=FLAGS))
        assert s.matched == sum(FLAGS)

    def test_level_counts_accumulated(self):
        s = Summarizer()
        list(s.feed(LINES, levels=LEVELS))
        assert s.level_counts["ERROR"] == 2
        assert s.level_counts["INFO"] == 2
        assert s.level_counts["DEBUG"] == 1
        assert s.level_counts["WARNING"] == 1

    def test_empty_stream(self):
        s = Summarizer()
        result = list(s.feed([]))
        assert result == []
        assert s.total == 0
        assert s.matched == 0


class TestFormatSummary:
    def test_contains_label(self):
        s = Summarizer()
        list(s.feed(LINES, levels=LEVELS))
        report = s.format_summary()
        assert report[0] == "=== Log Summary ==="

    def test_contains_total_and_matched(self):
        s = Summarizer()
        list(s.feed(LINES, levels=LEVELS, matched_flags=FLAGS))
        report = "\n".join(s.format_summary())
        assert "Total lines   : 6" in report
        assert "Matched lines : 5" in report

    def test_level_section_present(self):
        s = Summarizer()
        list(s.feed(LINES, levels=LEVELS))
        report = "\n".join(s.format_summary())
        assert "ERROR" in report
        assert "INFO" in report

    def test_error_samples_present(self):
        s = Summarizer()
        list(s.feed(LINES, levels=LEVELS))
        report = "\n".join(s.format_summary())
        assert "disk full" in report

    def test_top_n_limits_samples(self):
        errors = [f"2024-01-01 ERROR error {i}" for i in range(10)]
        error_levels = ["ERROR"] * 10
        s = Summarizer(top_n=3)
        list(s.feed(errors, levels=error_levels))
        samples = [ln for ln in s.format_summary() if "error" in ln]
        assert len(samples) == 3

    def test_no_levels_no_level_section(self):
        s = Summarizer()
        list(s.feed(LINES))
        report = "\n".join(s.format_summary())
        assert "Level counts" not in report
