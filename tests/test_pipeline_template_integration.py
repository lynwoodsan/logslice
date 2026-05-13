"""Integration tests: template formatting wired through the full pipeline."""
import io
from logslice.pipeline import build_pipeline


def _run_pipeline(lines, **kwargs):
    """Run lines through build_pipeline and return collected output lines."""
    buf = io.StringIO()
    defaults = dict(
        start=None,
        end=None,
        level=None,
        pattern=None,
        color=False,
        context_before=0,
        context_after=0,
        dedup_window=0,
        sample_every=None,
        sample_fraction=None,
        field_filters=None,
        max_line_length=None,
        redact=False,
        output_json=False,
        line_numbers=False,
        label=None,
        throttle_interval=None,
        template=None,
    )
    defaults.update(kwargs)
    pipeline = build_pipeline(iter(lines), output=buf, **defaults)
    list(pipeline)
    buf.seek(0)
    return [l.rstrip("\n") for l in buf.readlines() if l.strip()]


class TestTemplateIntegration:
    def test_no_template_lines_unchanged(self):
        lines = ["hello", "world"]
        result = _run_pipeline(lines, template=None)
        assert "hello" in result[0]
        assert "world" in result[1]

    def test_template_applied_to_all_lines(self):
        lines = ["alpha", "beta"]
        result = _run_pipeline(lines, template="OUT: {message}")
        assert all(r.startswith("OUT:") for r in result)

    def test_template_with_level_filter(self):
        lines = [
            "2024-01-01 INFO ok",
            "2024-01-01 ERROR bad",
            "2024-01-01 DEBUG verbose",
        ]
        result = _run_pipeline(lines, level="ERROR", template="[{level}] {message}")
        assert len(result) == 1
        assert "[ERROR]" in result[0]

    def test_template_with_pattern_filter(self):
        lines = ["apple pie", "banana split", "apple cider"]
        result = _run_pipeline(lines, pattern="apple", template=">> {raw}")
        assert len(result) == 2
        assert all(r.startswith(">>") for r in result)
