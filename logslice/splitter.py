"""Split merged log streams by source file or label into separate output files."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, IO, Iterable, Optional, Tuple


@dataclass
class Splitter:
    """Route lines to per-source output files based on a label prefix."""

    output_dir: str
    separator: str = " | "
    _handles: Dict[str, IO[str]] = field(default_factory=dict, init=False, repr=False)
    _line_counts: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.output_dir:
            raise ValueError("output_dir must be a non-empty string")
        os.makedirs(self.output_dir, exist_ok=True)

    def _parse_label(self, line: str) -> Tuple[Optional[str], str]:
        """Return (label, rest) if the line starts with a known separator, else (None, line)."""
        if self.separator in line:
            label, _, rest = line.partition(self.separator)
            return label.strip(), rest
        return None, line

    def _get_handle(self, label: str) -> IO[str]:
        if label not in self._handles:
            safe = label.replace(os.sep, "_").replace(" ", "_")
            path = os.path.join(self.output_dir, f"{safe}.log")
            self._handles[label] = open(path, "a", encoding="utf-8")  # noqa: WPS515
        return self._handles[label]

    def feed(self, line: str) -> str:
        """Write line to the appropriate split file; return the line unchanged."""
        label, rest = self._parse_label(line)
        if label:
            handle = self._get_handle(label)
            handle.write(rest + "\n")
            self._line_counts[label] = self._line_counts.get(label, 0) + 1
        return line

    def feed_all(self, lines: Iterable[str]) -> Iterable[str]:
        for line in lines:
            yield self.feed(line)

    def line_counts(self) -> Dict[str, int]:
        """Return a copy of per-label line counts."""
        return dict(self._line_counts)

    def close(self) -> None:
        """Flush and close all open file handles."""
        for handle in self._handles.values():
            handle.close()
        self._handles.clear()

    def __enter__(self) -> "Splitter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
