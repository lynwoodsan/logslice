"""Merge multiple log file iterables into a single chronological stream."""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.filters import extract_timestamp


@dataclass
class _Entry:
    """Heap entry carrying a timestamp key, source label, and line text."""

    sort_key: str
    label: str
    line: str

    def __lt__(self, other: "_Entry") -> bool:  # noqa: D105
        return (self.sort_key, self.label) < (other.sort_key, other.label)


@dataclass
class Merger:
    """Merge labelled log streams into one chronological sequence."""

    label_separator: str = " | "
    _merged_count: int = field(default=0, init=False, repr=False)

    def merge(
        self,
        sources: List[Tuple[str, Iterable[str]]],
        prepend_label: bool = True,
    ) -> Iterator[str]:
        """Yield lines from *sources* in timestamp order.

        Args:
            sources: List of (label, line_iterable) pairs.
            prepend_label: If True, prefix each line with ``label + separator``.
        """
        heap: List[_Entry] = []
        iters = [(label, iter(it)) for label, it in sources]

        def _push(label: str, it: Iterator[str]) -> None:
            try:
                line = next(it).rstrip("\n")
                ts = extract_timestamp(line) or ""
                heapq.heappush(heap, _Entry(sort_key=ts, label=label, line=line))
            except StopIteration:
                pass

        for label, it in iters:
            _push(label, it)

        iter_map = {label: it for label, it in iters}

        while heap:
            entry = heapq.heappop(heap)
            self._merged_count += 1
            out = (
                f"{entry.label}{self.label_separator}{entry.line}"
                if prepend_label
                else entry.line
            )
            yield out
            _push(entry.label, iter_map[entry.label])

    @property
    def merged_count(self) -> int:
        """Total number of lines emitted so far."""
        return self._merged_count
