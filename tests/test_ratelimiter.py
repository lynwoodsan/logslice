"""Tests for logslice.ratelimiter."""

import pytest
from logslice.ratelimiter import RateLimiter


class TestRateLimiterInit:
    def test_default_values(self):
        rl = RateLimiter()
        assert rl.max_lines == 100
        assert rl.window_seconds == 1.0

    def test_custom_values(self):
        rl = RateLimiter(max_lines=10, window_seconds=5.0)
        assert rl.max_lines == 10
        assert rl.window_seconds == 5.0

    def test_invalid_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            RateLimiter(max_lines=0)

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RateLimiter(window_seconds=0)

    def test_negative_window_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RateLimiter(window_seconds=-1.0)


class TestRateLimiterAllow:
    def test_first_line_allowed(self):
        rl = RateLimiter(max_lines=3, window_seconds=1.0)
        assert rl.allow(now=0.0) is True

    def test_lines_within_limit_allowed(self):
        rl = RateLimiter(max_lines=3, window_seconds=1.0)
        for i in range(3):
            assert rl.allow(now=float(i) * 0.1) is True

    def test_line_over_limit_suppressed(self):
        rl = RateLimiter(max_lines=3, window_seconds=1.0)
        for i in range(3):
            rl.allow(now=0.0)
        assert rl.allow(now=0.5) is False

    def test_old_timestamps_expire(self):
        rl = RateLimiter(max_lines=2, window_seconds=1.0)
        rl.allow(now=0.0)
        rl.allow(now=0.1)
        # Both slots used; but at t=1.5 the old ones are outside the window
        assert rl.allow(now=1.5) is True

    def test_suppressed_count_increments(self):
        rl = RateLimiter(max_lines=1, window_seconds=1.0)
        rl.allow(now=0.0)
        rl.allow(now=0.1)
        rl.allow(now=0.2)
        assert rl.suppressed_count == 2

    def test_total_count_increments(self):
        rl = RateLimiter(max_lines=5, window_seconds=1.0)
        for _ in range(4):
            rl.allow(now=0.0)
        assert rl.total_count == 4


class TestRateLimiterDropRate:
    def test_zero_when_no_lines(self):
        rl = RateLimiter()
        assert rl.drop_rate == 0.0

    def test_half_suppressed(self):
        rl = RateLimiter(max_lines=2, window_seconds=1.0)
        for _ in range(4):
            rl.allow(now=0.0)
        assert rl.drop_rate == pytest.approx(0.5)

    def test_none_suppressed(self):
        rl = RateLimiter(max_lines=10, window_seconds=1.0)
        for _ in range(5):
            rl.allow(now=0.0)
        assert rl.drop_rate == 0.0


class TestRateLimiterFeed:
    def test_allowed_line_not_suppressed(self):
        rl = RateLimiter(max_lines=5, window_seconds=1.0)
        results = list(rl.feed("hello", now=0.0))
        assert results == [("hello", False)]

    def test_suppressed_line_flagged(self):
        rl = RateLimiter(max_lines=1, window_seconds=1.0)
        rl.allow(now=0.0)
        results = list(rl.feed("overflow", now=0.1))
        assert results == [("overflow", True)]
