"""Tests for logslice.templateformatter."""
import pytest
from logslice.templateformatter import (
    render_template,
    validate_template,
    TemplateFormatter,
)


class TestRenderTemplate:
    def test_empty_template_returns_line(self):
        assert render_template("", "hello world") == "hello world"

    def test_raw_placeholder(self):
        result = render_template("{raw}", "some log line")
        assert result == "some log line"

    def test_message_placeholder(self):
        result = render_template("MSG: {message}", "some log line")
        assert result == "MSG: some log line"

    def test_level_placeholder_with_level(self):
        line = "2024-01-01 10:00:00 ERROR something failed"
        result = render_template("[{level}] {message}", line)
        assert "[ERROR]" in result

    def test_level_placeholder_no_level(self):
        line = "plain line without level"
        result = render_template("[{level}] {message}", line)
        assert result.startswith("[]")

    def test_timestamp_placeholder_with_ts(self):
        line = "2024-06-15T12:30:00 INFO started"
        result = render_template("{timestamp} | {message}", line)
        assert "2024-06-15" in result
        assert " | " in result

    def test_timestamp_placeholder_no_ts(self):
        line = "no timestamp here"
        result = render_template("{timestamp}:{message}", line)
        assert result.startswith(":")

    def test_unknown_placeholder_returns_line(self):
        result = render_template("{unknown_field}", "hello")
        assert result == "hello"

    def test_mixed_known_unknown_returns_line(self):
        result = render_template("{level} {bogus}", "INFO msg")
        assert result == "INFO msg"

    def test_literal_template_no_placeholders(self):
        result = render_template("FIXED OUTPUT", "anything")
        assert result == "FIXED OUTPUT"


class TestValidateTemplate:
    def test_all_known_returns_empty(self):
        assert validate_template("{timestamp} {level} {message}") == []

    def test_unknown_field_detected(self):
        unknown = validate_template("{host} {message}")
        assert "host" in unknown

    def test_raw_is_known(self):
        assert validate_template("{raw}") == []

    def test_no_placeholders_returns_empty(self):
        assert validate_template("plain text") == []

    def test_multiple_unknowns(self):
        result = validate_template("{foo} {bar} {level}")
        assert set(result) == {"foo", "bar"}


class TestTemplateFormatterInit:
    def test_empty_template_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            TemplateFormatter(template="")

    def test_valid_template_created(self):
        tf = TemplateFormatter(template="{level}: {message}")
        assert tf.template == "{level}: {message}"

    def test_initial_count_zero(self):
        tf = TemplateFormatter(template="{raw}")
        assert tf.formatted_count == 0


class TestTemplateFormatterFeed:
    def test_feed_increments_count(self):
        tf = TemplateFormatter(template="{raw}")
        list(tf.feed(["a", "b", "c"]))
        assert tf.formatted_count == 3

    def test_feed_applies_template(self):
        tf = TemplateFormatter(template=">> {message}")
        results = list(tf.feed(["hello", "world"]))
        assert results == [">> hello", ">> world"]

    def test_feed_empty_input(self):
        tf = TemplateFormatter(template="{raw}")
        assert list(tf.feed([])) == []
        assert tf.formatted_count == 0

    def test_feed_is_lazy_iterator(self):
        tf = TemplateFormatter(template="{raw}")
        gen = tf.feed(iter(["x"]))
        assert tf.formatted_count == 0
        next(gen)
        assert tf.formatted_count == 1
