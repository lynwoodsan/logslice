"""High-level output pipeline: applies filters and writes formatted results."""

import re
import sys
from typing import Iterator, Optional, TextIO

from logslice.filters import (
    extract_level,
    matches_level,
    matches_pattern,
    matches_time_range,
)
from logslice.formatter import format_line, supports_color


def process_lines(
    lines: Iterator[str],
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    level_filter: Optional[str] = None,
    pattern: Optional[str] = None,
    use_color: Optional[bool] = None,
    stream: TextIO = sys.stdout,
) -> int:
    """Filter and write log lines. Returns number of lines written."""
    compiled_pattern = re.compile(pattern) if pattern else None
    color = use_color if use_color is not None else supports_color(stream)
    count = 0

    for line in lines:
        stripped = line.rstrip("\n")

        if start_time or end_time:
            if not matches_time_range(stripped, start_time, end_time):
                continue

        if level_filter:
            if not matches_level(stripped, level_filter):
                continue

        if compiled_pattern:
            if not matches_pattern(stripped, compiled_pattern):
                continue

        level = extract_level(stripped)
        formatted = format_line(stripped, level, use_color=color)
        print(formatted, file=stream)
        count += 1

    return count
