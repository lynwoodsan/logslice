"""Rate limiter: suppress bursts by capping output lines per time window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator, Tuple


@dataclass
class RateLimiter:
    """Emit at most *max_lines* lines per *window_seconds* sliding window."""

    max_lines: int = 100
    window_seconds: float = 1.0

    _timestamps: list = field(default_factory=list, repr=False)
    _suppressed: int = field(default=0, repr=False)
    _total: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.max_lines < 1:
            raise ValueError("max_lines must be >= 1")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

    def _purge_old(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def allow(self, now: float | None = None) -> bool:
        """Return True if this line should be emitted."""
        if now is None:
            now = time.monotonic()
        self._purge_old(now)
        self._total += 1
        if len(self._timestamps) < self.max_lines:
            self._timestamps.append(now)
            return True
        self._suppressed += 1
        return False

    def feed(self, line: str, now: float | None = None) -> Iterator[Tuple[str, bool]]:
        """Yield *(line, is_suppressed)* tuples."""
        if self.allow(now):
            yield line, False
        else:
            yield line, True

    @property
    def suppressed_count(self) -> int:
        return self._suppressed

    @property
    def total_count(self) -> int:
        return self._total

    @property
    def drop_rate(self) -> float:
        if self._total == 0:
            return 0.0
        return self._suppressed / self._total
