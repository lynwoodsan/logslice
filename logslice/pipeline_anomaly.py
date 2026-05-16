"""Pipeline integration for anomaly detection."""
from __future__ import annotations

from typing import Iterator, Optional

from logslice.anomalydetector import AnomalyDetector


def apply_anomaly(
    lines: Iterator[str],
    *,
    enabled: bool = False,
    window: int = 60,
    threshold: float = 3.0,
    marker: str = "[ANOMALY]",
    bucket_size: int = 10,
) -> Iterator[str]:
    """Wrap *lines* with anomaly detection when *enabled* is True.

    Parameters
    ----------
    lines:       upstream line iterator
    enabled:     pass False to skip detection entirely
    window:      number of historical buckets to retain
    threshold:   std-deviation multiplier for flagging
    marker:      prefix injected on anomalous lines
    bucket_size: lines per evaluation bucket
    """
    if not enabled:
        yield from lines
        return

    detector = AnomalyDetector(window=window, threshold=threshold, marker=marker)
    yield from detector.feed(lines, bucket_size=bucket_size)
