"""Integrate Throttle into the logslice pipeline."""

from __future__ import annotations

from typing import Iterator, Optional

from logslice.throttle import Throttle


def apply_throttle(
    lines: Iterator[str],
    interval: Optional[float],
) -> Iterator[str]:
    """Wrap *lines* with a :class:`Throttle` if *interval* is set.

    Parameters
    ----------
    lines:
        Input line iterator.
    interval:
        Minimum seconds between emissions of the same message template.
        Pass ``None`` to disable throttling.

    Yields
    ------
    str
        Lines that pass the throttle gate.
    """
    if interval is None:
        yield from lines
        return

    throttle = Throttle(interval=interval)
    yield from throttle.feed(lines)
