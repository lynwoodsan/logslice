"""Throttle output by emitting at most one line per N seconds per unique message template."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Iterator, Optional

_DIGITS_RE = re.compile(r"\d+")


def _normalize(line: str) -> str:
    """Replace digit runs with a placeholder to group similar messages."""
    return _DIGITS_RE.sub("#", line.strip())


@dataclass
class Throttle:
    """Emit a line only if the same template has not been emitted within *interval* seconds."""

    interval: float = 1.0
    _last_seen: dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _throttled_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.interval <= 0:
            raise ValueError(f"interval must be positive, got {self.interval!r}")

    def should_emit(self, line: str, now: Optional[float] = None) -> bool:
        """Return True if *line* should be emitted, False if it is throttled."""
        ts = now if now is not None else time.monotonic()
        key = _normalize(line)
        last = self._last_seen.get(key)
        if last is None or (ts - last) >= self.interval:
            self._last_seen[key] = ts
            return True
        self._throttled_count += 1
        return False

    @property
    def throttled_count(self) -> int:
        """Total number of lines suppressed by throttling."""
        return self._throttled_count

    def feed(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield lines that pass the throttle check."""
        for line in lines:
            if self.should_emit(line):
                yield line

    def reset(self) -> None:
        """Clear all throttle state."""
        self._last_seen.clear()
        self._throttled_count = 0
