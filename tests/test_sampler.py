"""Tests for logslice.sampler."""

import pytest
from logslice.sampler import Sampler


class TestSamplerInit:
    def test_default_values(self):
        s = Sampler()
        assert s.every_n == 1
        assert s.fraction == 1.0

    def test_custom_values(self):
        s = Sampler(every_n=5, fraction=0.5)
        assert s.every_n == 5
        assert s.fraction == 0.5

    def test_invalid_every_n_raises(self):
        with pytest.raises(ValueError, match="every_n"):
            Sampler(every_n=0)

    def test_invalid_fraction_zero_raises(self):
        with pytest.raises(ValueError, match="fraction"):
            Sampler(fraction=0.0)

    def test_invalid_fraction_over_one_raises(self):
        with pytest.raises(ValueError, match="fraction"):
            Sampler(fraction=1.1)

    def test_initial_counts_zero(self):
        s = Sampler()
        assert s.total == 0
        assert s.emitted == 0


class TestShouldEmit:
    def test_every_1_always_emits(self):
        s = Sampler(every_n=1)
        results = [s.should_emit() for _ in range(10)]
        assert all(results)

    def test_every_n_emits_first_of_each_block(self):
        s = Sampler(every_n=3)
        results = [s.should_emit() for _ in range(9)]
        # positions 1,4,7 (1-indexed) should emit
        assert results == [True, False, False, True, False, False, True, False, False]

    def test_fraction_1_always_emits(self):
        s = Sampler(fraction=1.0, seed=42)
        results = [s.should_emit() for _ in range(20)]
        assert all(results)

    def test_fraction_deterministic_with_seed(self):
        s1 = Sampler(fraction=0.5, seed=0)
        s2 = Sampler(fraction=0.5, seed=0)
        r1 = [s1.should_emit() for _ in range(20)]
        r2 = [s2.should_emit() for _ in range(20)]
        assert r1 == r2

    def test_total_increments_always(self):
        s = Sampler(every_n=2)
        for _ in range(6):
            s.should_emit()
        assert s.total == 6

    def test_emitted_increments_only_when_true(self):
        s = Sampler(every_n=2)
        for _ in range(6):
            s.should_emit()
        assert s.emitted == 3


class TestFeed:
    def _pairs(self, n: int, matched: bool = True):
        return [(f"line {i}", matched) for i in range(n)]

    def test_no_sampling_passes_all_matched(self):
        s = Sampler()
        pairs = self._pairs(5)
        result = list(s.feed(pairs))
        assert result == pairs

    def test_every_n_skips_matched_lines(self):
        s = Sampler(every_n=2)
        pairs = self._pairs(6)
        result = list(s.feed(pairs))
        assert len(result) == 3

    def test_non_matched_lines_always_pass_through(self):
        s = Sampler(every_n=10)
        pairs = [(f"ctx {i}", False) for i in range(5)]
        result = list(s.feed(pairs))
        assert result == pairs

    def test_mixed_matched_and_context(self):
        s = Sampler(every_n=2)
        pairs = [("m0", True), ("c1", False), ("m2", True), ("c3", False), ("m4", True)]
        result = list(s.feed(pairs))
        # m0 emitted (1st), c1 passes, m2 skipped (2nd), c3 passes, m4 emitted (3rd)
        assert ("m0", True) in result
        assert ("c1", False) in result
        assert ("m2", True) not in result
        assert ("c3", False) in result
        assert ("m4", True) in result


class TestDropRate:
    def test_no_lines_is_zero(self):
        s = Sampler()
        assert s.drop_rate == 0.0

    def test_all_emitted_is_zero(self):
        s = Sampler(every_n=1)
        for _ in range(5):
            s.should_emit()
        assert s.drop_rate == 0.0

    def test_half_dropped(self):
        s = Sampler(every_n=2)
        for _ in range(6):
            s.should_emit()
        assert abs(s.drop_rate - 0.5) < 1e-9

    def test_format_report_contains_counts(self):
        s = Sampler(every_n=2)
        for _ in range(4):
            s.should_emit()
        report = s.format_report()
        assert "2/4" in report
        assert "50.0%" in report
