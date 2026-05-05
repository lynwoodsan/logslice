"""Deduplication support for log lines."""

from collections import OrderedDict
from typing import Iterator, Optional


class Deduplicator:
    """Tracks seen log lines and filters out duplicates within a window."""

    def __init__(self, window: int = 100, enabled: bool = True):
        """
        Args:
            window: Number of recent lines to remember for dedup comparison.
            enabled: If False, all lines pass through unchanged.
        """
        if window < 1:
            raise ValueError("window must be at least 1")
        self.window = window
        self.enabled = enabled
        self._seen: OrderedDict = OrderedDict()
        self.total = 0
        self.duplicates = 0

    def is_duplicate(self, line: str) -> bool:
        """Return True if line has been seen within the current window."""
        if not self.enabled:
            return False
        normalized = line.rstrip("\n")
        return normalized in self._seen

    def record(self, line: str) -> None:
        """Record a line as seen, evicting oldest entry if window is full."""
        normalized = line.rstrip("\n")
        if normalized in self._seen:
            # Move to end (most recently seen)
            self._seen.move_to_end(normalized)
            return
        self._seen[normalized] = True
        if len(self._seen) > self.window:
            self._seen.popitem(last=False)

    def feed(self, line: str) -> Optional[str]:
        """Feed a line through the deduplicator.

        Returns the line if it should be emitted, or None if it is a duplicate.
        """
        self.total += 1
        if self.is_duplicate(line):
            self.duplicates += 1
            return None
        self.record(line)
        return line

    def filter(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield only non-duplicate lines from an iterable of lines."""
        for line in lines:
            result = self.feed(line)
            if result is not None:
                yield result

    @property
    def duplicate_rate(self) -> float:
        """Fraction of lines that were duplicates (0.0 to 1.0)."""
        if self.total == 0:
            return 0.0
        return self.duplicates / self.total
