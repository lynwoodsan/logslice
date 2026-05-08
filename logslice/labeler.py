"""Tag/label lines with a custom prefix based on source file or pattern match."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class Labeler:
    """Prepend a label to each line, optionally only when a pattern matches."""

    label: str
    pattern: Optional[str] = None
    separator: str = " | "
    _labeled: int = field(default=0, init=False, repr=False)
    _skipped: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("label must be a non-empty string")
        if self.separator is None:
            raise ValueError("separator must not be None")
        self._compiled = None
        if self.pattern:
            import re
            self._compiled = re.compile(self.pattern)

    def annotate(self, line: str) -> str:
        """Return the line with the label prepended if conditions are met."""
        if self._compiled is not None:
            if not self._compiled.search(line):
                self._skipped += 1
                return line
        self._labeled += 1
        return f"{self.label}{self.separator}{line}"

    def feed(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield annotated lines from an iterable."""
        for line in lines:
            yield self.annotate(line)

    @property
    def labeled_count(self) -> int:
        return self._labeled

    @property
    def skipped_count(self) -> int:
        return self._skipped
