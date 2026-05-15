"""Highlight lines that differ from the previous line (diff-style output)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional

ANSI_ADDED = "\033[32m"   # green
ANSI_CHANGED = "\033[33m"  # yellow
ANSI_RESET = "\033[0m"


@dataclass
class DiffHighlighter:
    """Emit lines annotated with a diff marker when content changes.

    Args:
        color: Wrap changed lines in ANSI colour codes.
        marker: Prefix appended to changed lines (e.g. ``'> '``).
    """

    color: bool = False
    marker: str = "> "
    _prev: Optional[str] = field(default=None, init=False, repr=False)
    _changed_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.marker is None:
            raise ValueError("marker must not be None")

    # ------------------------------------------------------------------
    # public helpers
    # ------------------------------------------------------------------

    @property
    def changed_count(self) -> int:
        """Number of lines that differed from their predecessor."""
        return self._changed_count

    def annotate(self, line: str) -> str:
        """Return *line* with diff marker/colour if it changed."""
        stripped = line.rstrip("\n")
        changed = self._prev is not None and stripped != self._prev
        self._prev = stripped
        if changed:
            self._changed_count += 1
            marked = f"{self.marker}{stripped}"
            if self.color:
                return f"{ANSI_CHANGED}{marked}{ANSI_RESET}"
            return marked
        return stripped

    def feed(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield annotated lines from *lines*."""
        for line in lines:
            yield self.annotate(line)

    def reset(self) -> None:
        """Reset internal state (previous line and counter)."""
        self._prev = None
        self._changed_count = 0
