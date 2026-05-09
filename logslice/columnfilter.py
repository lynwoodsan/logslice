"""Filter or extract specific columns from structured (space/CSV-style) log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator, List, Optional


@dataclass
class ColumnFilter:
    """Extract or filter log lines based on positional columns.

    Args:
        columns: 1-based column indices to extract. None means pass all columns.
        delimiter: Field separator. Defaults to whitespace splitting.
        min_columns: Skip lines with fewer than this many columns.
    """

    columns: Optional[List[int]] = None
    delimiter: Optional[str] = None
    min_columns: int = 0
    _emitted: int = field(default=0, init=False, repr=False)
    _skipped: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_columns < 0:
            raise ValueError("min_columns must be >= 0")
        if self.columns is not None:
            for c in self.columns:
                if c < 1:
                    raise ValueError(f"Column indices are 1-based; got {c}")

    def _split(self, line: str) -> List[str]:
        if self.delimiter is None:
            return line.split()
        return line.split(self.delimiter)

    def extract(self, line: str) -> Optional[str]:
        """Return the extracted column(s) from *line*, or None to skip."""
        parts = self._split(line)
        if len(parts) < self.min_columns:
            return None
        if self.columns is None:
            return line
        selected: List[str] = []
        sep = self.delimiter if self.delimiter is not None else " "
        for idx in self.columns:
            if idx <= len(parts):
                selected.append(parts[idx - 1])
            else:
                selected.append("")
        return sep.join(selected)

    def feed(
        self, lines: Generator[str, None, None]
    ) -> Generator[str, None, None]:
        """Yield extracted/filtered lines from *lines*."""
        for line in lines:
            result = self.extract(line)
            if result is None:
                self._skipped += 1
            else:
                self._emitted += 1
                yield result

    @property
    def emitted_count(self) -> int:
        return self._emitted

    @property
    def skipped_count(self) -> int:
        return self._skipped
