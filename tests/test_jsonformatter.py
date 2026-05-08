"""Tests for logslice.jsonformatter."""

from __future__ import annotations

import json

import pytest

from logslice.jsonformatter import line_to_dict, format_as_json, feed


class TestLineToDictBasic:
    def test_message_always_present(self):
        record = line_to_dict("hello world")
        assert record["message"] == "hello world"

    def test_no_timestamp_key_absent(self):
        record = line_to_dict("hello world")
        assert "timestamp" not in record

    def test_no_level_key_absent(self):
        record = line_to_dict("hello world")
        assert "level" not in record

    def test_iso_timestamp_extracted(self):
        line = "2024-03-15T10:30:00 INFO service started"
        record = line_to_dict(line)
        assert "timestamp" in record
        assert "2024-03-15" in record["timestamp"]

    def test_level_extracted(self):
        line = "2024-03-15T10:30:00 ERROR disk full"
        record = line_to_dict(line)
        assert record["level"] == "ERROR"

    def test_source_included_when_given(self):
        record = line_to_dict("msg", source="app.log")
        assert record["source"] == "app.log"

    def test_source_absent_when_none(self):
        record = line_to_dict("msg")
        assert "source" not in record

    def test_extra_fields_merged(self):
        record = line_to_dict("msg", extra_fields={"host": "web01"})
        assert record["host"] == "web01"

    def test_extra_fields_none_safe(self):
        record = line_to_dict("msg", extra_fields=None)
        assert "host" not in record


class TestFormatAsJson:
    def test_returns_valid_json_string(self):
        result = format_as_json("hello")
        parsed = json.loads(result)
        assert parsed["message"] == "hello"

    def test_no_trailing_newline(self):
        result = format_as_json("hello")
        assert not result.endswith("\n")

    def test_indent_produces_multiline(self):
        result = format_as_json("hello", indent=2)
        assert "\n" in result

    def test_source_in_output(self):
        result = format_as_json("msg", source="syslog")
        parsed = json.loads(result)
        assert parsed["source"] == "syslog"

    def test_unicode_preserved(self):
        line = "INFO \u00e9v\u00e9nement"
        result = format_as_json(line)
        parsed = json.loads(result)
        assert "\u00e9v\u00e9nement" in parsed["message"]


class TestFeed:
    def test_yields_one_json_per_line(self):
        lines = ["INFO start", "ERROR stop"]
        results = list(feed(lines))
        assert len(results) == 2

    def test_each_result_is_valid_json(self):
        lines = ["INFO start", "ERROR stop"]
        for item in feed(lines):
            parsed = json.loads(item)
            assert "message" in parsed

    def test_empty_input_yields_nothing(self):
        assert list(feed([])) == []

    def test_source_propagated_to_all(self):
        lines = ["INFO a", "INFO b"]
        for item in feed(lines, source="test.log"):
            parsed = json.loads(item)
            assert parsed["source"] == "test.log"

    def test_extra_fields_propagated(self):
        lines = ["INFO a"]
        for item in feed(lines, extra_fields={"env": "prod"}):
            parsed = json.loads(item)
            assert parsed["env"] == "prod"
