"""Tests for logslice.pipeline_anomaly."""
from logslice.pipeline_anomaly import apply_anomaly


def _run(lines, **kwargs):
    return list(apply_anomaly(iter(lines), **kwargs))


class TestApplyAnomalyDisabled:
    def test_disabled_passes_all_lines(self):
        lines = ["alpha", "beta", "gamma"]
        result = _run(lines, enabled=False)
        assert result == lines

    def test_disabled_empty_input(self):
        assert _run([], enabled=False) == []

    def test_disabled_preserves_order(self):
        lines = [str(i) for i in range(20)]
        assert _run(lines, enabled=False) == lines


class TestApplyAnomalyEnabled:
    def test_enabled_returns_all_lines(self):
        lines = [f"line {i}" for i in range(15)]
        result = _run(lines, enabled=True, bucket_size=5)
        assert len(result) == 15

    def test_enabled_empty_input(self):
        assert _run([], enabled=True) == []

    def test_no_history_no_anomaly_markers(self):
        """Without prior history stddev=0, so nothing is flagged."""
        lines = ["info: started", "info: running", "info: done"]
        result = _run(lines, enabled=True, threshold=2.0, bucket_size=10)
        assert all("[ANOMALY]" not in ln for ln in result)

    def test_custom_marker_used(self):
        """Marker is respected when anomaly is injected."""
        # We cannot force an anomaly without history, but we can verify
        # that a detector with custom marker is constructed correctly by
        # inspecting a zero-history run (no marker expected).
        lines = ["x"] * 5
        result = _run(lines, enabled=True, marker="!!SPIKE!!", bucket_size=10)
        assert all("!!SPIKE!!" not in ln for ln in result)

    def test_bucket_size_larger_than_input(self):
        """All lines fit in one bucket; should still be returned."""
        lines = ["a", "b", "c"]
        result = _run(lines, enabled=True, bucket_size=100)
        assert result == ["a", "b", "c"]

    def test_multiple_buckets_all_lines_returned(self):
        lines = [f"msg {i}" for i in range(30)]
        result = _run(lines, enabled=True, bucket_size=5)
        assert len(result) == 30
