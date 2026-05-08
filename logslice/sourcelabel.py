"""Attach a source filename label to each line from a named log source."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterator, List, Tuple

from logslice.labeler import Labeler


@dataclass
class SourceLabeler:
    """Wrap multiple Labelers keyed by source path."""

    use_basename: bool = True
    separator: str = " | "
    _labelers: dict = field(default_factory=dict, init=False, repr=False)

    def get_label(self, path: str) -> str:
        """Return the display label for a given file path."""
        return os.path.basename(path) if self.use_basename else path

    def _get_or_create(self, path: str) -> Labeler:
        if path not in self._labelers:
            self._labelers[path] = Labeler(
                label=self.get_label(path),
                separator=self.separator,
            )
        return self._labelers[path]

    def annotate(self, path: str, line: str) -> str:
        """Return line prefixed with the source label."""
        return self._get_or_create(path).annotate(line)

    def feed_source(self, path: str, lines: Iterator[str]) -> Iterator[str]:
        """Yield labeled lines from a single source."""
        labeler = self._get_or_create(path)
        yield from labeler.feed(lines)

    def feed_many(
        self, sources: List[Tuple[str, Iterator[str]]]
    ) -> Iterator[str]:
        """Interleave labeled lines from multiple sources in order."""
        for path, lines in sources:
            yield from self.feed_source(path, lines)

    def total_labeled(self) -> int:
        return sum(lb.labeled_count for lb in self._labelers.values())
