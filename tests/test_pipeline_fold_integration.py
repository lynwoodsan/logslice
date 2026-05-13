"""Integration test: fold filter wired into the main pipeline."""
from __future__ import annotations

from logslice.pipeline import build_pipeline


def _run_pipeline(lines, **kwargs):
    """Run lines through build_pipeline and return collected output."""
    out = []

    def _writer(line: str) -> None:
        out.append(line)

    cfg = dict(
        color=False,
        pattern=None,
        level=None,
        start=None,
        end=None,
        context_before=0,
        context_after=0,
        dedup_window=0,
        sample_every=None,
        sample_fraction=None,
        max_line_length=None,
        fields=None,
        field_filters=None,
        multiline_pattern=None,
        redact=False,
        json_output=False,
        line_numbers=False,
        label=None,
        template=None,
        mask_fields=None,
        fold=kwargs.get("fold", False),
        fold_min_repeats=kwargs.get("fold_min_repeats", 2),
        fold_label=kwargs.get("fold_label", "(x{count})"),
    )

    pipeline = build_pipeline(iter(lines), writer=_writer, **cfg)
    for _ in pipeline:
        pass
    return out


class TestFoldIntegration:
    def test_fold_disabled_preserves_all(self):
        lines = ["dup", "dup", "dup"]
        result = _run_pipeline(lines, fold=False)
        assert result == ["dup", "dup", "dup"]

    def test_fold_enabled_collapses_repeats(self):
        lines = ["err", "err", "err", "ok"]
        result = _run_pipeline(lines, fold=True)
        assert "err (x3)" in result
        assert "ok" in result
        assert len(result) == 2

    def test_fold_with_level_filter(self):
        lines = [
            "2024-01-01 ERROR boom",
            "2024-01-01 ERROR boom",
            "2024-01-01 INFO  fine",
        ]
        result = _run_pipeline(lines, fold=True, level="ERROR")
        # INFO line filtered out; two ERROR lines folded
        assert any("boom" in r and "x2" in r for r in result)
        assert not any("fine" in r for r in result)
