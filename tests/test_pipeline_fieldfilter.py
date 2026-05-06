"""Integration tests for field-filter support in the pipeline."""

import pytest
from logslice.pipeline import build_pipeline


LINES = [
    'ts=2024-01-01 level=INFO service=web msg="request received"',
    'ts=2024-01-01 level=ERROR service=auth msg="login failed"',
    'ts=2024-01-01 level=WARN service=web msg="slow response" latency=1.5',
    'ts=2024-01-01 level=ERROR service=db msg="connection lost"',
    'plain line with no fields',
]


def _run(field_filters=None, **kwargs):
    return build_pipeline(LINES, field_filters=field_filters, **kwargs)


class TestFieldFilterNone:
    def test_no_filter_returns_all_lines(self):
        result = _run()
        assert len(result) == len(LINES)

    def test_no_filter_preserves_content(self):
        result = _run()
        assert any('login failed' in l for l in result)


class TestFieldFilterSingle:
    def test_filter_by_level_error(self):
        result = _run(field_filters=['level=ERROR'])
        assert len(result) == 2
        assert all('level=ERROR' in l for l in result)

    def test_filter_by_service_web(self):
        result = _run(field_filters=['service=web'])
        assert len(result) == 2
        assert all('service=web' in l for l in result)

    def test_filter_excludes_plain_lines(self):
        result = _run(field_filters=['level=INFO'])
        assert not any('plain line' in l for l in result)


class TestFieldFilterMultiple:
    def test_level_and_service(self):
        result = _run(field_filters=['level=ERROR', 'service=auth'])
        assert len(result) == 1
        assert 'login failed' in result[0]

    def test_no_match_returns_empty(self):
        result = _run(field_filters=['level=DEBUG'])
        assert result == []


class TestFieldFilterRegex:
    def test_regex_value_matches_multiple(self):
        result = _run(field_filters=['level=ERROR|WARN'])
        assert len(result) == 3

    def test_regex_prefix_match(self):
        result = _run(field_filters=['service=^(web|auth)$'])
        assert len(result) == 3


class TestFieldFilterCombinedWithLevel:
    def test_field_filter_and_level_filter_combined(self):
        result = _run(field_filters=['service=web'], level='WARN')
        assert len(result) == 1
        assert 'slow response' in result[0]


class TestInvalidFieldFilter:
    def test_missing_equals_raises(self):
        with pytest.raises(ValueError, match='expected'):
            _run(field_filters=['levelERROR'])

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match='key must not be empty'):
            _run(field_filters=['=ERROR'])
