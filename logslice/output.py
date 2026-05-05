"""Output processing: apply filters, context, formatting, and stats."""

from typing import IO, Iterable, Optional
import re

from logslice.filters import matches_level, matches_pattern, matches_time_range
from logslice.formatter import format_line, write_output
from logslice.stats import LogStats
from logslice.context import apply_context


def process_lines(
    lines: Iterable[str],
    output: IO[str],
    start=None,
    end=None,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    color: bool = False,
    before: int = 0,
    after: int = 0,
    stats: Optional[LogStats] = None,
) -> None:
    """
    Stream log lines through filters and write matching lines to output.

    Args:
        lines:   Iterable of raw log line strings.
        output:  File-like object to write results to.
        start:   Optional datetime lower bound for time filtering.
        end:     Optional datetime upper bound for time filtering.
        level:   Optional minimum log level string (e.g. "WARNING").
        pattern: Optional regex pattern string to match against lines.
        color:   Whether to emit ANSI color codes.
        before:  Number of context lines to include before each match.
        after:   Number of context lines to include after each match.
        stats:   Optional LogStats instance to record match statistics.
    """
    compiled = re.compile(pattern) if pattern else None

    def is_match(line: str) -> bool:
        if start is not None or end is not None:
            if not matches_time_range(line, start, end):
                return False
        if level is not None:
            if not matches_level(line, level):
                return False
        if compiled is not None:
            if not matches_pattern(line, compiled):
                return False
        return True

    tagged = ((line, is_match(line)) for line in lines)

    use_context = before > 0 or after > 0

    if use_context:
        pairs = apply_context(tagged, before=before, after=after)
    else:
        pairs = ((line, False) for line, matched in tagged if matched)

    for line, is_context in pairs:
        matched = not is_context
        if stats is not None:
            stats.record_line(line, matched=matched)
        formatted = format_line(line, color=color, pattern=compiled)
        write_output(formatted, output)
