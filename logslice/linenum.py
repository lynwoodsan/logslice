"""Line number annotator for logslice.

Wraps each emitted line with its original line number from the source,
optionally formatting it for display or downstream processing.
"""

from dataclasses import dataclass, field
from typing import Iterator, Tuple


@dataclass
class LineNumberAnnotator:
    """Tracks and annotates lines with their 1-based source line numbers."""

    start: int = 1
    pad_width: int = 0  # 0 means auto-size based on seen numbers
    separator: str = ":"

    _counter: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("start must be >= 1")
        if self.pad_width < 0:
            raise ValueError("pad_width must be >= 0")
        self._counter = self.start

    @property
    def current(self) -> int:
        """Return the next line number that will be assigned."""
        return self._counter

    def annotate(self, line: str) -> str:
        """Return the line prefixed with its line number."""
        num = self._counter
        self._counter += 1
        width = self.pad_width if self.pad_width > 0 else len(str(num))
        prefix = str(num).rjust(width)
        return f"{prefix}{self.separator}{line}"

    def feed(
        self, lines: Iterator[str], annotate: bool = True
    ) -> Iterator[str]:
        """Yield lines, optionally annotated with line numbers."""
        for line in lines:
            if annotate:
                yield self.annotate(line)
            else:
                self._counter += 1
                yield line

    def reset(self) -> None:
        """Reset counter back to the configured start value."""
        self._counter = self.start


def strip_line_number(line: str, separator: str = ":") -> Tuple[int, str]:
    """Parse a line number annotation, returning (number, original_line).

    Raises ValueError if the line does not start with a valid number prefix.
    """
    sep_idx = line.find(separator)
    if sep_idx == -1:
        raise ValueError(f"No separator {separator!r} found in line: {line!r}")
    num_part = line[:sep_idx].strip()
    if not num_part.isdigit():
        raise ValueError(f"Line number prefix is not numeric: {num_part!r}")
    return int(num_part), line[sep_idx + len(separator):]
