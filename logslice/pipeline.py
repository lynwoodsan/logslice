"""Build and run the logslice processing pipeline."""

from typing import Iterator, List, Optional

from logslice.filters import matches_level, matches_pattern, matches_time_range
from logslice.highlighter import highlight_matches
from logslice.context import ContextBuffer
from logslice.deduplicator import Deduplicator
from logslice.sampler import Sampler
from logslice.truncator import Truncator
from logslice.ratelimiter import RateLimiter
from logslice.burst_reporter import BurstReporter
from logslice.fieldextractor import FieldExtractor, parse_field_filters


def _apply_filters(
    lines: List[str],
    *,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    start=None,
    end=None,
    field_filters: Optional[List[str]] = None,
) -> Iterator[str]:
    """Yield lines that pass all active filters."""
    fe: Optional[FieldExtractor] = None
    if field_filters:
        fe = FieldExtractor(required_fields=parse_field_filters(field_filters))

    for line in lines:
        stripped = line.rstrip("\n")
        if level and not matches_level(stripped, level):
            continue
        if pattern and not matches_pattern(stripped, pattern):
            continue
        if (start or end) and not matches_time_range(stripped, start, end):
            continue
        if fe and not fe.matches(stripped):
            continue
        yield stripped


def build_pipeline(
    lines: List[str],
    *,
    level: Optional[str] = None,
    pattern: Optional[str] = None,
    start=None,
    end=None,
    color: bool = False,
    before_context: int = 0,
    after_context: int = 0,
    deduplicate: bool = False,
    sample_every_n: Optional[int] = None,
    sample_fraction: Optional[float] = None,
    max_line_length: Optional[int] = None,
    max_lines_per_window: Optional[int] = None,
    rate_window: int = 60,
    field_filters: Optional[List[str]] = None,
) -> List[str]:
    """Run lines through the full pipeline and return output lines."""
    filtered = list(
        _apply_filters(
            lines,
            level=level,
            pattern=pattern,
            start=start,
            end=end,
            field_filters=field_filters,
        )
    )

    if deduplicate:
        dedup = Deduplicator()
        filtered = dedup.feed(filtered)

    if sample_every_n is not None or sample_fraction is not None:
        kwargs = {}
        if sample_every_n is not None:
            kwargs["every_n"] = sample_every_n
        if sample_fraction is not None:
            kwargs["fraction"] = sample_fraction
        sampler = Sampler(**kwargs)
        filtered = sampler.feed(filtered)

    if max_line_length is not None:
        truncator = Truncator(max_length=max_line_length)
        filtered = truncator.feed(filtered)

    if max_lines_per_window is not None:
        rl = RateLimiter(max_lines=max_lines_per_window, window=rate_window)
        reporter = BurstReporter(rate_limiter=rl)
        result: List[str] = []
        for line in filtered:
            result.extend(reporter.feed(line))
        result.extend(reporter.flush())
        filtered = result

    if color and pattern:
        filtered = [highlight_matches(line, pattern, color=True) for line in filtered]

    if before_context > 0 or after_context > 0:
        buf = ContextBuffer(before=before_context, after=after_context)
        ctx_out: List[str] = []
        all_lines = [l.rstrip("\n") for l in lines]
        for entry in all_lines:
            ctx_out.extend(buf.feed(entry, entry in filtered))
        filtered = ctx_out

    return filtered
