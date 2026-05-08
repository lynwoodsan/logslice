"""Summarizer: produce a concise summary report from processed log lines."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class Summarizer:
    """Collect statistics and emit a summary block at the end of a stream."""

    top_n: int = 5
    label: str = "=== Log Summary ==="

    _total: int = field(default=0, init=False, repr=False)
    _matched: int = field(default=0, init=False, repr=False)
    _level_counts: Counter = field(default_factory=Counter, init=False, repr=False)
    _error_samples: List[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1")
        if not self.label:
            raise ValueError("label must be a non-empty string")

    def feed(
        self,
        lines: Iterable[str],
        *,
        matched_flags: Optional[Iterable[bool]] = None,
        levels: Optional[Iterable[Optional[str]]] = None,
    ) -> Iterator[str]:
        """Pass lines through unchanged while accumulating statistics."""
        flags_iter = iter(matched_flags) if matched_flags is not None else None
        levels_iter = iter(levels) if levels is not None else None

        for line in lines:
            self._total += 1
            matched = next(flags_iter, True) if flags_iter is not None else True
            if matched:
                self._matched += 1
            level = next(levels_iter, None) if levels_iter is not None else None
            if level:
                self._level_counts[level.upper()] += 1
                if level.upper() in ("ERROR", "CRITICAL") and len(self._error_samples) < self.top_n:
                    self._error_samples.append(line.rstrip())
            yield line

    def format_summary(self) -> List[str]:
        """Return summary lines suitable for printing."""
        lines: List[str] = [
            self.label,
            f"  Total lines   : {self._total}",
            f"  Matched lines : {self._matched}",
        ]
        if self._level_counts:
            lines.append("  Level counts  :")
            for lvl, cnt in sorted(self._level_counts.items()):
                lines.append(f"    {lvl:<10} {cnt}")
        if self._error_samples:
            lines.append(f"  Top {self.top_n} errors  :")
            for sample in self._error_samples[: self.top_n]:
                lines.append(f"    {sample}")
        return lines

    @property
    def total(self) -> int:
        return self._total

    @property
    def matched(self) -> int:
        return self._matched

    @property
    def level_counts(self) -> Counter:
        return Counter(self._level_counts)
