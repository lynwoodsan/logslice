"""Integration tests: anomaly detection wired into the full pipeline."""
from __future__ import annotations

import io
from typing import List

from logslice.pipeline_anomaly import apply_anomaly
from logslice.pipeline import build_pipeline


def _run_pipeline(
    log_lines: List[str],
    *,
    anomaly: bool = False,
    pattern: str | None = None,
) -> List[str]:
    """Run lines through build_pipeline then apply_anomaly."""
    out = io.StringIO()
    args_dict = dict(
        start=None,
        end=None,
        level=None,
        pattern=pattern,
        color=False,
        context_before=0,
        context_after=0,
        field_filters=None,
        redact=False,
        json_out=False,
        line_numbers=False,
        label=None,
        label_sep=" | ",
        template=None,
        mask_fields=None,
        fold=False,
        diff=False,
        timeshift=0,
    )

    class _FakeArgs:
        def __getattr__(self, name):
            return args_dict.get(name)

    pipeline_out = list(build_pipeline(iter(log_lines), _FakeArgs()))
    result = list(apply_anomaly(iter(pipeline_out), enabled=anomaly, bucket_size=5))
    return result


class TestAnomalyIntegration:
    def test_anomaly_disabled_lines_unchanged(self):
        lines = ["INFO starting", "DEBUG loop", "ERROR crash"]
        result = _run_pipeline(lines, anomaly=False)
        assert result == lines

    def test_anomaly_enabled_returns_same_count(self):
        lines = [f"INFO event {i}" for i in range(12)]
        result = _run_pipeline(lines, anomaly=True)
        assert len(result) == 12

    def test_anomaly_with_pattern_filter(self):
        lines = ["INFO keep this", "DEBUG skip", "INFO keep too"]
        result = _run_pipeline(lines, anomaly=True, pattern="keep")
        assert len(result) == 2
        assert all("keep" in ln for ln in result)

    def test_no_false_anomaly_on_uniform_stream(self):
        lines = ["INFO heartbeat"] * 20
        result = _run_pipeline(lines, anomaly=True)
        assert all("[ANOMALY]" not in ln for ln in result)
