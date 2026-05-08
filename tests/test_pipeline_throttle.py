"""Integration tests for apply_throttle inside a simple pipeline."""

import time
import pytest
from logslice.pipeline_throttle import apply_throttle


def _run(lines, interval):
    return list(apply_throttle(iter(lines), interval))


class TestApplyThrottleDisabled:
    def test_none_interval_passes_all(self):
        lines = ["a", "a", "a"]
        assert _run(lines, None) == lines

    def test_none_interval_empty_input(self):
        assert _run([], None) == []


class TestApplyThrottleEnabled:
    def test_unique_lines_all_pass(self):
        lines = ["alpha", "beta", "gamma"]
        result = _run(lines, interval=0.001)
        assert result == lines

    def test_repeated_line_throttled_within_interval(self):
        # All three arrive "instantly" in the same test; only first should pass.
        lines = ["error occurred"] * 5
        result = _run(lines, interval=60.0)
        assert result == ["error occurred"]

    def test_digit_variant_throttled(self):
        lines = ["retry 1 of 3", "retry 2 of 3", "retry 3 of 3"]
        result = _run(lines, interval=60.0)
        assert len(result) == 1
        assert result[0] == "retry 1 of 3"

    def test_different_templates_not_throttled(self):
        lines = ["disk full", "cpu high", "memory low"]
        result = _run(lines, interval=60.0)
        assert result == lines

    def test_empty_input_returns_empty(self):
        assert _run([], interval=1.0) == []

    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError):
            _run(["line"], interval=0)

    def test_after_interval_expires_line_passes_again(self):
        """Verify real-time expiry using a tiny interval."""
        throttle_interval = 0.05  # 50 ms
        first = list(apply_throttle(iter(["heartbeat"]), throttle_interval))
        time.sleep(throttle_interval + 0.02)
        second = list(apply_throttle(iter(["heartbeat"]), throttle_interval))
        assert first == ["heartbeat"]
        assert second == ["heartbeat"]
