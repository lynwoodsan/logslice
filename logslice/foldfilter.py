"""Fold (collapse) consecutive repeated lines into a single line with a count."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class FoldFilter:
    """Collapse consecutive duplicate lines, appending a repeat count."""

    min_repeats: int = 2
    label: str = "(x{count})"

    def __post_init__(self) -> None:
        if self.min_repeats < 2:
            raise ValueError("min_repeats must be >= 2")
        if not self.label:
            raise ValueError("label must be a non-empty string")
        self._last: Optional[str] = None
        self._count: int = 0
        self._folded_count: int = 0

    # ------------------------------------------------------------------
    def _emit(self) -> Iterator[str]:
        """Yield the buffered line, annotated if it was repeated."""
        if self._last is None:
            return
        if self._count >= self.min_repeats:
            suffix = self.label.format(count=self._count)
            yield f"{self._last} {suffix}"
            self._folded_count += self._count - 1
        else:
            for _ in range(self._count):
                yield self._last

    def feed(self, line: str) -> Iterator[str]:
        """Feed a line; yields zero or more output lines."""
        stripped = line.rstrip("\n")
        if stripped == self._last:
            self._count += 1
        else:
            yield from self._emit()
            self._last = stripped
            self._count = 1

    def finalize(self) -> Iterator[str]:
        """Flush any buffered line at end of stream."""
        yield from self._emit()
        self._last = None
        self._count = 0

    @property
    def folded_count(self) -> int:
        """Number of lines suppressed by folding."""
        return self._folded_count
