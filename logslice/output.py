"""Process and output filtered log lines, optionally collecting stats."""

from typing import Iterable, Iterator, Optional, TextIO

from logslice.filters import (
    extract_level,
    extract_timestamp,
    matches_level,
    matches_pattern,
    matches_time_range,
)
from logslice.formatter import format_line, write_output
from logslice.stats import LogStats


def process_lines(
    lines: Iterable[str],
    output: TextIO,
    *,
    start_time=None,
    end_time=None,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    color: bool = False,
    collect_stats: bool = False,
) -> Optional[LogStats]:
    """Filter *lines* and write matching ones to *output*.

    Returns a :class:`LogStats` instance when *collect_stats* is True,
    otherwise returns None.
    """
    stats = LogStats() if collect_stats else None

    for line in lines:
        line = line.rstrip("\n")

        timestamp = extract_timestamp(line)
        line_level = extract_level(line)

        matched = (
            matches_time_range(timestamp, start_time, end_time)
            and matches_level(line_level, level)
            and matches_pattern(line, pattern)
        )

        if stats is not None:
            stats.record_line(line, matched=matched, level=line_level, timestamp=timestamp)

        if matched:
            formatted = format_line(line, line_level, use_color=color)
            write_output(formatted, output)

    return stats
