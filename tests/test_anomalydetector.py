"""Tests for logslice.anomalydetector."""
import pytest
from logslice.anomalydetector import AnomalyDetector


class TestAnomalyDetectorInit:
    def test_default_values(self):
        d = AnomalyDetector()
        assert d.window == 60
        assert d.threshold == 3.0
        assert d.marker == "[ANOMALY]"

    def test_custom_values(self):
        d = AnomalyDetector(window=10, threshold=2.0, marker="!!")
        assert d.window == 10
        assert d.threshold == 2.0
        assert d.marker == "!!"

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            AnomalyDetector(window=0)

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="threshold"):
            AnomalyDetector(threshold=0)

    def test_empty_marker_raises(self):
        with pytest.raises(ValueError, match="marker"):
            AnomalyDetector(marker="")

    def test_initial_flagged_count_zero(self):
        assert AnomalyDetector().flagged_count == 0


class TestMeanStddev:
    def test_mean_empty(self):
        d = AnomalyDetector()
        assert d._mean() == 0.0

    def test_mean_single_bucket(self):
        d = AnomalyDetector()
        d.record_bucket(10)
        assert d._mean() == 10.0

    def test_stddev_single_bucket_is_zero(self):
        d = AnomalyDetector()
        d.record_bucket(10)
        assert d._stddev() == 0.0

    def test_stddev_multiple_buckets(self):
        d = AnomalyDetector()
        for v in [10, 10, 10, 10]:
            d.record_bucket(v)
        assert d._stddev() == 0.0

    def test_window_evicts_old_buckets(self):
        d = AnomalyDetector(window=3)
        for v in [1, 2, 3, 4]:
            d.record_bucket(v)
        assert len(d._counts) == 3
        assert list(d._counts) == [2, 3, 4]


class TestIsAnomalous:
    def test_no_history_not_anomalous(self):
        d = AnomalyDetector()
        assert not d.is_anomalous(1000)

    def test_uniform_history_not_anomalous(self):
        d = AnomalyDetector(threshold=2.0)
        for _ in range(10):
            d.record_bucket(5)
        assert not d.is_anomalous(5)

    def test_spike_is_anomalous(self):
        d = AnomalyDetector(threshold=2.0)
        for _ in range(20):
            d.record_bucket(5)
        # mean=5, stddev=0 after uniform — add variance first
        d2 = AnomalyDetector(threshold=1.5)
        for v in [5, 5, 5, 5, 5, 5, 5, 5, 5, 6]:
            d2.record_bucket(v)
        assert d2.is_anomalous(50)


class TestAnnotate:
    def test_non_anomaly_unchanged(self):
        d = AnomalyDetector()
        assert d.annotate("hello", False) == "hello"

    def test_anomaly_prepends_marker(self):
        d = AnomalyDetector(marker="[X]")
        assert d.annotate("hello", True) == "[X] hello"

    def test_flagged_count_increments(self):
        d = AnomalyDetector()
        d.annotate("a", True)
        d.annotate("b", True)
        d.annotate("c", False)
        assert d.flagged_count == 2


class TestFeed:
    def _feed(self, lines, **kwargs):
        d = AnomalyDetector(**kwargs)
        return list(d.feed(iter(lines)))

    def test_empty_input_returns_empty(self):
        assert self._feed([]) == []

    def test_all_lines_returned(self):
        lines = ["a", "b", "c"]
        result = self._feed(lines)
        assert len(result) == 3

    def test_no_anomaly_lines_unchanged(self):
        lines = [f"line {i}" for i in range(5)]
        result = self._feed(lines, threshold=3.0)
        # no history → stddev=0 → no anomaly
        assert all(not ln.startswith("[ANOMALY]") for ln in result)
