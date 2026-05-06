"""Tests for logslice.fieldextractor."""

import pytest
from logslice.fieldextractor import FieldExtractor, parse_field_filters


class TestExtract:
    def test_single_field(self):
        fe = FieldExtractor()
        assert fe.extract('level=INFO msg="hello world"') == {
            'level': 'INFO',
            'msg': 'hello world',
        }

    def test_no_fields_returns_empty(self):
        fe = FieldExtractor()
        assert fe.extract('plain log line with no kv pairs') == {}

    def test_unquoted_value(self):
        fe = FieldExtractor()
        result = fe.extract('status=200 path=/api/v1')
        assert result['status'] == '200'
        assert result['path'] == '/api/v1'

    def test_quoted_value_strips_quotes(self):
        fe = FieldExtractor()
        result = fe.extract('msg="something happened"')
        assert result['msg'] == 'something happened'

    def test_multiple_fields(self):
        fe = FieldExtractor()
        line = 'ts=2024-01-01 level=ERROR service=auth latency=0.32'
        result = fe.extract(line)
        assert result['level'] == 'ERROR'
        assert result['service'] == 'auth'
        assert result['latency'] == '0.32'


class TestMatches:
    def test_no_required_fields_always_matches(self):
        fe = FieldExtractor()
        assert fe.matches('any line at all') is True

    def test_required_field_exact_match(self):
        fe = FieldExtractor(required_fields={'level': 'ERROR'})
        assert fe.matches('level=ERROR msg=boom') is True

    def test_required_field_no_match(self):
        fe = FieldExtractor(required_fields={'level': 'ERROR'})
        assert fe.matches('level=INFO msg=ok') is False

    def test_missing_field_does_not_match(self):
        fe = FieldExtractor(required_fields={'service': 'auth'})
        assert fe.matches('level=INFO msg=ok') is False

    def test_required_field_regex_match(self):
        fe = FieldExtractor(required_fields={'status': '^5\\d{2}$'})
        assert fe.matches('status=500 path=/crash') is True
        assert fe.matches('status=200 path=/ok') is False

    def test_multiple_required_fields_all_must_match(self):
        fe = FieldExtractor(required_fields={'level': 'ERROR', 'service': 'auth'})
        assert fe.matches('level=ERROR service=auth') is True
        assert fe.matches('level=ERROR service=web') is False


class TestFeed:
    def test_feed_filters_lines(self):
        fe = FieldExtractor(required_fields={'level': 'WARN'})
        lines = [
            'level=INFO msg=a',
            'level=WARN msg=b',
            'level=WARN msg=c',
            'level=ERROR msg=d',
        ]
        assert fe.feed(lines) == ['level=WARN msg=b', 'level=WARN msg=c']

    def test_feed_no_filter_returns_all(self):
        fe = FieldExtractor()
        lines = ['line one', 'line two']
        assert fe.feed(lines) == lines


class TestMatchRate:
    def test_initial_match_rate_is_one(self):
        fe = FieldExtractor()
        assert fe.match_rate == 1.0

    def test_match_rate_after_filtering(self):
        fe = FieldExtractor(required_fields={'level': 'ERROR'})
        fe.feed(['level=ERROR', 'level=INFO', 'level=ERROR', 'level=DEBUG'])
        assert abs(fe.match_rate - 0.5) < 1e-9


class TestParseFieldFilters:
    def test_single_spec(self):
        assert parse_field_filters(['level=ERROR']) == {'level': 'ERROR'}

    def test_multiple_specs(self):
        result = parse_field_filters(['level=ERROR', 'service=auth'])
        assert result == {'level': 'ERROR', 'service': 'auth'}

    def test_missing_equals_raises(self):
        with pytest.raises(ValueError, match='expected'):
            parse_field_filters(['levelERROR'])

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match='key must not be empty'):
            parse_field_filters(['=ERROR'])

    def test_empty_list_returns_empty_dict(self):
        assert parse_field_filters([]) == {}
