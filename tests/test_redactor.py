"""Tests for logslice.redactor."""

import pytest
from logslice.redactor import Redactor


class TestRedactorBuiltin:
    def test_password_param_redacted(self):
        r = Redactor()
        assert r.redact("login?password=hunter2") == "login?password=***"

    def test_token_param_redacted(self):
        r = Redactor()
        assert r.redact("auth token=abc123xyz") == "auth token=***"

    def test_api_key_redacted(self):
        r = Redactor()
        assert r.redact("api_key=supersecret") == "api_key=***"

    def test_credit_card_redacted(self):
        r = Redactor()
        result = r.redact("card: 4111 1111 1111 1111 charged")
        assert "4111" not in result
        assert "****-****-****-****" in result

    def test_email_redacted(self):
        r = Redactor()
        assert r.redact("user alice@example.com logged in") == "user [email] logged in"

    def test_clean_line_unchanged(self):
        r = Redactor()
        line = "INFO server started on port 8080"
        assert r.redact(line) == line

    def test_redacted_count_increments(self):
        r = Redactor()
        r.redact("password=secret")
        r.redact("nothing sensitive")
        r.redact("token=abc")
        assert r.redacted_count == 2

    def test_redacted_count_starts_zero(self):
        r = Redactor()
        assert r.redacted_count == 0


class TestRedactorBuiltinDisabled:
    def test_builtin_off_leaves_password(self):
        r = Redactor(builtin=False)
        line = "password=secret"
        assert r.redact(line) == line

    def test_custom_pattern_applied(self):
        r = Redactor(patterns=[(r'\bSSN:\s*\d{3}-\d{2}-\d{4}\b', 'SSN:***')], builtin=False)
        assert r.redact("SSN: 123-45-6789") == "SSN:***"


class TestRedactorCustomPatterns:
    def test_extra_pattern_combined_with_builtin(self):
        r = Redactor(patterns=[(r'\bSSN:\s*\d{3}-\d{2}-\d{4}\b', 'SSN:***')])
        line = "SSN: 123-45-6789 password=x"
        result = r.redact(line)
        assert "SSN:***" in result
        assert "password=***" in result

    def test_invalid_regex_raises_on_init(self):
        with pytest.raises(re.error):
            Redactor(patterns=[(r'[invalid', 'x')])


class TestRedactorFeed:
    def test_feed_returns_redacted_line(self):
        r = Redactor()
        result = r.feed("token=secret")
        assert result == "token=***"

    def test_feed_returns_clean_line_unchanged(self):
        r = Redactor()
        line = "INFO all good"
        assert r.feed(line) == line

    def test_feed_never_returns_none(self):
        r = Redactor()
        assert r.feed("anything") is not None


import re  # noqa: E402  (needed for the raises check above)
