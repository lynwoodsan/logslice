"""Detect anomalous lines based on deviation from expected log rate or pattern frequency."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class AnomalyDetector:
    """Flag lines that arrive in bursts or match rarely-seen patterns."""

    window: int = 60          # seconds of history to consider
    threshold: float = 3.0    # std-deviation multiplier to flag anomaly
    marker: str = "[ANOMALY]"
    _counts: deque = field(default_factory=deque, init=False, repr=False)
    _flagged: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.window <= 0:
            raise ValueError("window must be a positive integer")
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")
        if not self.marker:
            raise ValueError("marker must be a non-empty string")

    # ------------------------------------------------------------------
    def _mean(self) -> float:
        if not self._counts:
            return 0.0
        return sum(self._counts) / len(self._counts)

    def _stddev(self) -> float:
        if len(self._counts) < 2:
            return 0.0
        m = self._mean()
        variance = sum((x - m) ** 2 for x in self._counts) / len(self._counts)
        return variance ** 0.5

    def record_bucket(self, count: int) -> None:
        """Record the number of lines seen in the latest time bucket."""
        self._counts.append(count)
        if len(self._counts) > self.window:
            self._counts.popleft()

    def is_anomalous(self, count: int) -> bool:
        """Return True if *count* exceeds mean + threshold * stddev."""
        mean = self._mean()
        sd = self._stddev()
        return sd > 0 and count > mean + self.threshold * sd

    @property
    def flagged_count(self) -> int:
        return self._flagged

    def annotate(self, line: str, is_anomaly: bool) -> str:
        if is_anomaly:
            self._flagged += 1
            return f"{self.marker} {line}"
        return line

    def feed(self, lines: Iterator[str], bucket_size: int = 10) -> Iterator[str]:
        """Yield lines, prepending *marker* to those in anomalous buckets."""
        bucket: list[str] = []
        for line in lines:
            bucket.append(line)
            if len(bucket) >= bucket_size:
                anomaly = self.is_anomalous(len(bucket))
                self.record_bucket(len(bucket))
                for ln in bucket:
                    yield self.annotate(ln, anomaly)
                bucket = []
        if bucket:
            anomaly = self.is_anomalous(len(bucket))
            self.record_bucket(len(bucket))
            for ln in bucket:
                yield self.annotate(ln, anomaly)
