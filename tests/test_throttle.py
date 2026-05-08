"""Tests for logslice.throttle."""

import pytest
from logslice.throttle import Throttle, _normalize


# ---------------------------------------------------------------------------
# _normalize helpers
# ---------------------------------------------------------------------------

def test_normalize_replaces_digits():
    assert _normalize("retry 3 times") == "retry # times"


def test_normalize_multiple_digit_runs():
    assert _normalize("user 42 logged in from 10.0.0.1") == "user # logged in from #.#.#.#"


def test_normalize_no_digits_unchanged():
    assert _normalize("hello world") == "hello world"


# ---------------------------------------------------------------------------
# Throttle init
# ---------------------------------------------------------------------------

class TestThrottleInit:
    def test_default_interval(self):
        t = Throttle()
        assert t.interval == 1.0

    def test_custom_interval(self):
        t = Throttle(interval=5.0)
        assert t.interval == 5.0

    def test_zero_interval_raises(self):
        with pytest.raises(ValueError):
            Throttle(interval=0)

    def test_negative_interval_raises(self):
        with pytest.raises(ValueError):
            Throttle(interval=-1.0)

    def test_initial_throttled_count_zero(self):
        assert Throttle().throttled_count == 0


# ---------------------------------------------------------------------------
# should_emit
# ---------------------------------------------------------------------------

class TestShouldEmit:
    def test_first_occurrence_allowed(self):
        t = Throttle(interval=1.0)
        assert t.should_emit("error occurred", now=0.0) is True

    def test_same_template_within_interval_suppressed(self):
        t = Throttle(interval=1.0)
        t.should_emit("error occurred", now=0.0)
        assert t.should_emit("error occurred", now=0.5) is False

    def test_same_template_after_interval_allowed(self):
        t = Throttle(interval=1.0)
        t.should_emit("error occurred", now=0.0)
        assert t.should_emit("error occurred", now=1.0) is True

    def test_different_templates_both_allowed(self):
        t = Throttle(interval=1.0)
        assert t.should_emit("error A", now=0.0) is True
        assert t.should_emit("error B", now=0.0) is True

    def test_digit_variants_share_bucket(self):
        t = Throttle(interval=1.0)
        t.should_emit("retry 3 times", now=0.0)
        assert t.should_emit("retry 7 times", now=0.2) is False

    def test_throttled_count_increments(self):
        t = Throttle(interval=2.0)
        t.should_emit("msg", now=0.0)
        t.should_emit("msg", now=0.5)
        t.should_emit("msg", now=1.0)
        assert t.throttled_count == 2


# ---------------------------------------------------------------------------
# feed
# ---------------------------------------------------------------------------

class TestFeed:
    def test_feed_yields_first_of_each_template(self):
        t = Throttle(interval=10.0)
        lines = ["error 1", "error 2", "other thing"]
        # all share template "error #" except last
        result = list(t.feed(iter(lines)))
        # "error 1" and "error 2" share bucket; only first passes
        assert result[0] == "error 1"
        assert "other thing" in result
        assert len(result) == 2

    def test_feed_empty_input(self):
        t = Throttle()
        assert list(t.feed(iter([]))) == []


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_clears_state(self):
        t = Throttle(interval=10.0)
        t.should_emit("msg", now=0.0)
        t.should_emit("msg", now=1.0)  # throttled
        t.reset()
        assert t.throttled_count == 0
        assert t.should_emit("msg", now=2.0) is True
