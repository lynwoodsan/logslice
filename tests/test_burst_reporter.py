"""Tests for logslice.burst_reporter."""

from logslice.burst_reporter import BurstReporter


class TestBurstReporterFeed:
    def test_allowed_lines_pass_through(self):
        br = BurstReporter(max_lines=5, window_seconds=1.0)
        out = list(br.feed("hello", now=0.0))
        assert out == ["hello"]

    def test_suppressed_line_not_emitted(self):
        br = BurstReporter(max_lines=1, window_seconds=1.0)
        list(br.feed("first", now=0.0))
        out = list(br.feed("overflow", now=0.1))
        assert out == []

    def test_warning_injected_after_burst(self):
        br = BurstReporter(max_lines=1, window_seconds=1.0)
        list(br.feed("first", now=0.0))
        list(br.feed("overflow", now=0.1))
        # t=2.0 is outside the window — burst ends
        out = list(br.feed("resume", now=2.0))
        assert len(out) == 2
        assert "1 line(s) suppressed" in out[0]
        assert out[1] == "resume"

    def test_warning_counts_multiple_suppressed(self):
        br = BurstReporter(max_lines=1, window_seconds=1.0)
        list(br.feed("first", now=0.0))
        for i in range(5):
            list(br.feed(f"overflow-{i}", now=0.1 + i * 0.01))
        out = list(br.feed("resume", now=2.0))
        assert "5 line(s) suppressed" in out[0]

    def test_no_warning_when_no_suppression(self):
        br = BurstReporter(max_lines=10, window_seconds=1.0)
        results = []
        for i in range(5):
            results.extend(br.feed(f"line-{i}", now=float(i) * 0.01))
        assert all("suppressed" not in r for r in results)

    def test_custom_warn_template(self):
        br = BurstReporter(
            max_lines=1,
            window_seconds=1.0,
            warn_template="WARN: {n} dropped",
        )
        list(br.feed("first", now=0.0))
        list(br.feed("overflow", now=0.1))
        out = list(br.feed("resume", now=2.0))
        assert out[0] == "WARN: 1 dropped"


class TestBurstReporterFlush:
    def test_flush_emits_pending_warning(self):
        br = BurstReporter(max_lines=1, window_seconds=1.0)
        list(br.feed("first", now=0.0))
        list(br.feed("overflow", now=0.1))
        out = list(br.flush())
        assert len(out) == 1
        assert "1 line(s) suppressed" in out[0]

    def test_flush_clears_pending(self):
        br = BurstReporter(max_lines=1, window_seconds=1.0)
        list(br.feed("first", now=0.0))
        list(br.feed("overflow", now=0.1))
        list(br.flush())
        assert list(br.flush()) == []

    def test_flush_no_pending_emits_nothing(self):
        br = BurstReporter(max_lines=5, window_seconds=1.0)
        list(br.feed("hello", now=0.0))
        assert list(br.flush()) == []


class TestBurstReporterCounts:
    def test_suppressed_count_delegates(self):
        br = BurstReporter(max_lines=1, window_seconds=1.0)
        list(br.feed("first", now=0.0))
        list(br.feed("overflow", now=0.1))
        assert br.suppressed_count == 1

    def test_total_count_delegates(self):
        br = BurstReporter(max_lines=5, window_seconds=1.0)
        for i in range(3):
            list(br.feed(f"line-{i}", now=float(i)))
        assert br.total_count == 3
