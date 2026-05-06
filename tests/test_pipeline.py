"""Integration-style tests for logslice.pipeline.build_pipeline."""

from logslice.pipeline import build_pipeline


LINES = [
    "2024-01-01T10:00:00 INFO  server started",
    "2024-01-01T10:01:00 DEBUG request received",
    "2024-01-01T10:02:00 ERROR disk full",
    "2024-01-01T10:03:00 INFO  request handled",
    "2024-01-01T10:04:00 ERROR timeout",
    "2024-01-01T10:05:00 INFO  server stopped",
]


def _run(**kwargs):
    return list(build_pipeline(LINES, **kwargs))


class TestNoFilters:
    def test_returns_all_lines(self):
        result = _run()
        assert len(result) == len(LINES)

    def test_lines_are_stripped(self):
        lines_with_newlines = [l + "\n" for l in LINES]
        result = list(build_pipeline(lines_with_newlines))
        for r in result:
            assert not r.endswith("\n")


class TestLevelFilter:
    def test_error_only(self):
        result = _run(level="ERROR")
        assert len(result) == 2
        assert all("ERROR" in r for r in result)

    def test_info_only(self):
        result = _run(level="INFO")
        assert all("INFO" in r for r in result)


class TestPatternFilter:
    def test_pattern_filters_lines(self):
        result = _run(pattern="disk")
        assert len(result) == 1
        assert "disk full" in result[0]

    def test_no_match_returns_empty(self):
        result = _run(pattern="zzznomatch")
        assert result == []


class TestSampling:
    def test_every_n_reduces_output(self):
        result = _run(every_n=2)
        assert len(result) < len(LINES)

    def test_every_1_returns_all(self):
        result = _run(every_n=1)
        assert len(result) == len(LINES)


class TestDeduplication:
    def test_duplicate_lines_removed(self):
        duped = LINES[:2] + LINES[:2]
        result = list(build_pipeline(duped, dedupe_window=10))
        assert len(result) == 2


class TestContextLines:
    def test_before_context_included(self):
        # Pattern matches only ERROR lines; with before=1 we get the preceding INFO
        result = _run(pattern="ERROR", before=1)
        assert any("INFO" in r for r in result)

    def test_after_context_included(self):
        result = _run(pattern="ERROR", after=1)
        assert any("INFO" in r or "request" in r for r in result)


class TestCombinedFilters:
    def test_level_and_pattern(self):
        result = _run(level="ERROR", pattern="timeout")
        assert len(result) == 1
        assert "timeout" in result[0]

    def test_sampling_with_level(self):
        result = _run(level="INFO", every_n=2)
        info_lines = [l for l in LINES if "INFO" in l]
        assert len(result) <= len(info_lines)
