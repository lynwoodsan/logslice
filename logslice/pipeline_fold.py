"""Pipeline integration for FoldFilter — collapse consecutive duplicate lines."""
from __future__ import annotations

from typing import Iterable, Iterator, Optional

from logslice.foldfilter import FoldFilter


def apply_fold(
    lines: Iterable[str],
    *,
    enabled: bool = False,
    min_repeats: int = 2,
    label: str = "(x{count})",
) -> Iterator[str]:
    """Wrap *lines* with fold-filter behaviour when *enabled* is True.

    Parameters
    ----------
    lines:
        Input line iterable.
    enabled:
        When False the lines pass through unchanged.
    min_repeats:
        Minimum consecutive occurrences before a run is folded.
    label:
        Format string for the repeat annotation; ``{count}`` is replaced.
    """
    if not enabled:
        yield from lines
        return

    ff = FoldFilter(min_repeats=min_repeats, label=label)
    for line in lines:
        yield from ff.feed(line)
    yield from ff.finalize()
