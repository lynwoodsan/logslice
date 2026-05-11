"""Paginator: emit lines in pages of fixed size with optional offset."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


@dataclass
class Paginator:
    """Yield lines in pages, supporting --head / --skip style slicing."""

    page_size: int = 0          # 0 = unlimited
    skip: int = 0               # lines to skip before emitting

    _emitted: int = field(default=0, init=False, repr=False)
    _skipped: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.page_size < 0:
            raise ValueError("page_size must be >= 0")
        if self.skip < 0:
            raise ValueError("skip must be >= 0")

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def emitted(self) -> int:
        return self._emitted

    @property
    def skipped(self) -> int:
        return self._skipped

    @property
    def is_full(self) -> bool:
        """True when page_size > 0 and we have emitted page_size lines."""
        return self.page_size > 0 and self._emitted >= self.page_size

    @property
    def remaining(self) -> int | None:
        """Number of lines that can still be emitted, or None if unlimited.

        Returns ``None`` when ``page_size`` is 0 (unlimited).  Otherwise
        returns the non-negative count of lines left before the page is full.
        """
        if self.page_size == 0:
            return None
        return max(0, self.page_size - self._emitted)

    # ------------------------------------------------------------------
    # core
    # ------------------------------------------------------------------

    def feed(self, line: str) -> Iterator[str]:
        """Process one line; yield it if within the active page."""
        if self._skipped < self.skip:
            self._skipped += 1
            return
        if self.is_full:
            return
        self._emitted += 1
        yield line

    def feed_many(self, lines: Iterable[str]) -> Iterator[str]:
        """Process an iterable of lines, stopping early when page is full."""
        for line in lines:
            yield from self.feed(line)
            if self.is_full:
                break

    def reset(self) -> None:
        """Reset counters (e.g. for a new file)."""
        self._emitted = 0
        self._skipped = 0
