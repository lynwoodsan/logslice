"""Compose the full processing pipeline for a single log stream."""

from typing import Iterable, Iterator, Tuple

from logslice.context import ContextBuffer
from logslice.deduplicator import Deduplicator
from logslice.filters import matches_level, matches_pattern, matches_time_range
from logslice.highlighter import highlight_matches
from logslice.sampler import Sampler


def _apply_filters(
    lines: Iterable[str],
    *,
    start=None,
    end=None,
    level=None,
    pattern=None,
) -> Iterator[Tuple[str, bool]]:
    """Yield *(line, is_match)* pairs after applying time/level/pattern filters."""
    for line in lines:
        stripped = line.rstrip("\n")
        match = (
            matches_time_range(stripped, start, end)
            and matches_level(stripped, level)
            and matches_pattern(stripped, pattern)
        )
        yield stripped, match


def build_pipeline(
    lines: Iterable[str],
    *,
    start=None,
    end=None,
    level: str | None = None,
    pattern: str | None = None,
    before: int = 0,
    after: int = 0,
    dedupe_window: int = 0,
    every_n: int = 1,
    fraction: float = 1.0,
    color: bool = False,
) -> Iterator[str]:
    """Run *lines* through the full logslice pipeline and yield output strings."""

    pairs = _apply_filters(lines, start=start, end=end, level=level, pattern=pattern)

    # --- optional deduplication ---
    if dedupe_window > 0:
        deduplicator = Deduplicator(window=dedupe_window)
        pairs = deduplicator.feed(pairs)

    # --- optional sampling ---
    if every_n > 1 or fraction < 1.0:
        sampler = Sampler(every_n=every_n, fraction=fraction)
        pairs = sampler.feed(pairs)

    # --- context buffering ---
    ctx_buf = ContextBuffer(before=before, after=after)
    ctx_pairs = ctx_buf.apply_context(pairs)

    # --- highlight & emit ---
    for line, is_match in ctx_pairs:
        if color and pattern and is_match:
            line = highlight_matches(line, pattern, color=True)
        yield line
