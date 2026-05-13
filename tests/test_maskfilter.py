"""Tests for logslice.maskfilter."""

import pytest
from logslice.maskfilter import MaskFilter


class TestMaskFilterInit:
    def test_empty_fields_raises(self):
        with pytest.raises(ValueError, match="fields"):
            MaskFilter(fields=[])

    def test_empty_mask_raises(self):
        with pytest.raises(ValueError, match="mask"):
            MaskFilter(fields=["password"], mask="")

    def test_default_mask_is_stars(self):
        mf = MaskFilter(fields=["token"])
        assert mf.mask == "***"

    def test_custom_mask(self):
        mf = MaskFilter(fields=["token"], mask="[REDACTED]")
        assert mf.mask == "[REDACTED]"


class TestMaskFilterApply:
    def test_masks_simple_kv(self):
        mf = MaskFilter(fields=["password"])
        result = mf.apply("login user=alice password=secret123")
        assert "secret123" not in result
        assert "password=***" in result

    def test_masks_quoted_value(self):
        mf = MaskFilter(fields=["token"])
        result = mf.apply('auth token="abc.def.ghi" ok')
        assert "abc.def.ghi" not in result
        assert 'token="***"' in result

    def test_unrelated_fields_untouched(self):
        mf = MaskFilter(fields=["password"])
        result = mf.apply("user=alice status=ok")
        assert result == "user=alice status=ok"

    def test_case_insensitive_field_match(self):
        mf = MaskFilter(fields=["Password"])
        result = mf.apply("PASSWORD=hunter2")
        assert "hunter2" not in result

    def test_multiple_fields_masked(self):
        mf = MaskFilter(fields=["password", "token"])
        result = mf.apply("password=abc token=xyz user=bob")
        assert "abc" not in result
        assert "xyz" not in result
        assert "user=bob" in result

    def test_no_match_returns_line_unchanged(self):
        mf = MaskFilter(fields=["secret"])
        line = "INFO server started on port 8080"
        assert mf.apply(line) == line

    def test_custom_mask_used(self):
        mf = MaskFilter(fields=["apikey"], mask="<hidden>")
        result = mf.apply("apikey=mykey123")
        assert "<hidden>" in result
        assert "mykey123" not in result


class TestMaskFilterMaskedCount:
    def test_initial_count_zero(self):
        mf = MaskFilter(fields=["password"])
        assert mf.masked_count == 0

    def test_count_increments_per_masked_field(self):
        mf = MaskFilter(fields=["password", "token"])
        mf.apply("password=x token=y")
        assert mf.masked_count == 2

    def test_count_accumulates_across_calls(self):
        mf = MaskFilter(fields=["password"])
        mf.apply("password=a")
        mf.apply("password=b")
        assert mf.masked_count == 2


class TestMaskFilterFeed:
    def test_feed_yields_masked_lines(self):
        mf = MaskFilter(fields=["password"])
        lines = ["password=abc", "user=alice", "password=xyz"]
        result = list(mf.feed(iter(lines)))
        assert result[0] == "password=***"
        assert result[1] == "user=alice"
        assert result[2] == "password=***"

    def test_feed_empty_input(self):
        mf = MaskFilter(fields=["token"])
        assert list(mf.feed(iter([]))) == []
