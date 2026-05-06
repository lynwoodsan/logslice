"""Integration tests: rate-limiting inside the pipeline via BurstReporter."""

from __future__ import annotations

from logslice.burst_reporter import BurstReporter


def _run_burst(lines, max_lines=100, window_seconds=1.0, timestamps=None):
    """Feed *lines* through a BurstReporter and collect output."""
    br = BurstReporter(max_lines=max_lines, window_seconds=window_seconds)
    if timestamps is None:
        timestamps = [float(i) for i in range(len(lines))]
    out = []
    for line, ts in zip(lines, timestamps):
        out.extend(br.feed(line, now=ts))
    out.extend(br.flush())
    return out


class TestPipelineRateLimit:
    def test_no_suppression_all_lines_present(self):
        lines = [f"line {i}" for i in range(5)]
        out = _run_burst(lines, max_lines=10)
        assert out == lines

    def test_burst_suppresses_excess_lines(self):
        lines = [f"line {i}" for i in range(10)]
        # All at the same timestamp → only first 3 pass
        ts = [0.0] * 10
        out = _run_burst(lines, max_lines=3, window_seconds=1.0, timestamps=ts)
        # 3 real lines + 1 warning from flush
        real = [l for l in out if not l.startswith("[logslice]")]
        warnings = [l for l in out if l.startswith("[logslice]")]
        assert len(real) == 3
        assert len(warnings) == 1
        assert "7 line(s) suppressed" in warnings[0]

    def test_warning_appears_in_stream_on_resume(self):
        lines = ["a", "b", "c", "resume"]
        ts = [0.0, 0.0, 0.0, 5.0]  # first 3 at t=0, resume at t=5
        out = _run_burst(lines, max_lines=1, window_seconds=1.0, timestamps=ts)
        assert out[0] == "a"
        # warning injected before 'resume'
        assert any("suppressed" in l for l in out)
        assert "resume" in out

    def test_empty_input_produces_no_output(self):
        out = _run_burst([], max_lines=5)
        assert out == []

    def test_single_line_no_suppression(self):
        out = _run_burst(["only"], max_lines=1)
        assert out == ["only"]
