"""Shift timestamps in log lines by a fixed offset (e.g. to normalise timezones)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator, Optional

# Matches ISO-8601-ish timestamps: 2024-01-15T12:34:56 or 2024-01-15 12:34:56
_TS_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:?\d{2})?"
)


def _parse_ts(raw: str) -> Optional[datetime]:
    """Parse a timestamp string into a datetime (naive or aware)."""
    fmt_variants = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    base = raw[:19].replace("T", " ")
    for fmt in fmt_variants:
        try:
            return datetime.strptime(base, fmt)
        except ValueError:
            continue
    return None


def shift_line(line: str, delta: timedelta) -> str:
    """Return *line* with every recognised timestamp shifted by *delta*."""
    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        ts = _parse_ts(m.group(1))
        if ts is None:
            return m.group(0)
        shifted = ts + delta
        replacement = shifted.strftime("%Y-%m-%dT%H:%M:%S")
        if m.group(2):
            replacement += m.group(2)  # preserve sub-seconds
        if m.group(3):
            replacement += m.group(3)  # preserve tz suffix
        return replacement

    return _TS_RE.sub(_replace, line)


@dataclass
class TimeShifter:
    """Stream processor that shifts timestamps in every line by *hours* and *minutes*."""

    hours: int = 0
    minutes: int = 0
    shifted_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._delta = timedelta(hours=self.hours, minutes=self.minutes)

    def process(self, line: str) -> str:
        """Shift the line and return the result."""
        result = shift_line(line, self._delta)
        if result != line:
            self.shifted_count += 1
        return result

    def feed(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield shifted lines from *lines*."""
        for line in lines:
            yield self.process(line)
