"""Burst reporter: summarise suppressed bursts and emit warning lines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from logslice.ratelimiter import RateLimiter

_WARN_TEMPLATE = "[logslice] rate-limit: {n} line(s) suppressed in last window"


@dataclass
class BurstReporter:
    """Wrap a RateLimiter and inject summary warnings into the output stream."""

    max_lines: int = 100
    window_seconds: float = 1.0
    warn_template: str = _WARN_TEMPLATE

    _limiter: RateLimiter = field(init=False, repr=False)
    _pending_suppressed: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._limiter = RateLimiter(
            max_lines=self.max_lines,
            window_seconds=self.window_seconds,
        )

    def feed(self, line: str, now: float | None = None) -> Iterator[str]:
        """Yield output lines, injecting a warning whenever a burst ends."""
        allowed = self._limiter.allow(now=now)
        if allowed:
            if self._pending_suppressed:
                yield self.warn_template.format(n=self._pending_suppressed)
                self._pending_suppressed = 0
            yield line
        else:
            self._pending_suppressed += 1

    def flush(self) -> Iterator[str]:
        """Emit any remaining suppression warning at end of stream."""
        if self._pending_suppressed:
            yield self.warn_template.format(n=self._pending_suppressed)
            self._pending_suppressed = 0

    @property
    def suppressed_count(self) -> int:
        return self._limiter.suppressed_count

    @property
    def total_count(self) -> int:
        return self._limiter.total_count
