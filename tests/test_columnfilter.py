"""Tests for logslice.columnfilter."""
import pytest
from logslice.columnfilter import ColumnFilter


def _feed(cf: ColumnFilter, lines):
    return list(cf.feed(iter(lines)))


# ---------------------------------------------------------------------------
# Init / validation
# ---------------------------------------------------------------------------

class TestColumnFilterInit:
    def test_default_values(self):
        cf = ColumnFilter()
        assert cf.columns is None
        assert cf.delimiter is None
        assert cf.min_columns == 0

    def test_custom_values(self):
        cf = ColumnFilter(columns=[1, 3], delimiter=",", min_columns=2)
        assert cf.columns == [1, 3]
        assert cf.delimiter == ","
        assert cf.min_columns == 2

    def test_invalid_min_columns_raises(self):
        with pytest.raises(ValueError, match="min_columns"):
            ColumnFilter(min_columns=-1)

    def test_zero_column_index_raises(self):
        with pytest.raises(ValueError, match="1-based"):
            ColumnFilter(columns=[0])

    def test_negative_column_index_raises(self):
        with pytest.raises(ValueError, match="1-based"):
            ColumnFilter(columns=[-1])


# ---------------------------------------------------------------------------
# extract()
# ---------------------------------------------------------------------------

class TestExtract:
    def test_no_columns_returns_line_unchanged(self):
        cf = ColumnFilter()
        assert cf.extract("a b c") == "a b c"

    def test_single_column_extracted(self):
        cf = ColumnFilter(columns=[2])
        assert cf.extract("alpha beta gamma") == "beta"

    def test_multiple_columns_joined_by_space(self):
        cf = ColumnFilter(columns=[1, 3])
        assert cf.extract("alpha beta gamma") == "alpha gamma"

    def test_out_of_range_column_yields_empty_string(self):
        cf = ColumnFilter(columns=[1, 5])
        assert cf.extract("only two cols") == "only "

    def test_csv_delimiter(self):
        cf = ColumnFilter(columns=[2], delimiter=",")
        assert cf.extract("a,b,c") == "b"

    def test_csv_multiple_columns_joined_by_comma(self):
        cf = ColumnFilter(columns=[1, 3], delimiter=",")
        assert cf.extract("x,y,z") == "x,z"

    def test_min_columns_skips_short_line(self):
        cf = ColumnFilter(min_columns=4)
        assert cf.extract("a b c") is None

    def test_min_columns_passes_long_enough_line(self):
        cf = ColumnFilter(min_columns=3)
        assert cf.extract("a b c") == "a b c"


# ---------------------------------------------------------------------------
# feed()
# ---------------------------------------------------------------------------

class TestFeed:
    def test_all_lines_pass_with_no_filters(self):
        cf = ColumnFilter()
        lines = ["INFO server started", "DEBUG connecting"]
        assert _feed(cf, lines) == lines

    def test_column_extracted_from_each_line(self):
        cf = ColumnFilter(columns=[1])
        lines = ["INFO msg1", "ERROR msg2"]
        assert _feed(cf, lines) == ["INFO", "ERROR"]

    def test_short_lines_skipped_and_counted(self):
        cf = ColumnFilter(min_columns=3)
        lines = ["a b c", "x y", "1 2 3"]
        result = _feed(cf, lines)
        assert result == ["a b c", "1 2 3"]
        assert cf.skipped_count == 1
        assert cf.emitted_count == 2

    def test_empty_input_yields_nothing(self):
        cf = ColumnFilter(columns=[1])
        assert _feed(cf, []) == []

    def test_emitted_and_skipped_counts_accumulate(self):
        cf = ColumnFilter(min_columns=2)
        _feed(cf, ["a", "b c", "d", "e f g"])
        assert cf.emitted_count == 2
        assert cf.skipped_count == 2
