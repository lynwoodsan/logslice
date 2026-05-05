"""Collect and report statistics about processed log lines."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LogStats:
    """Accumulates statistics while processing log lines."""

    total_lines: int = 0
    matched_lines: int = 0
    skipped_lines: int = 0
    level_counts: Counter = field(default_factory=Counter)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None

    def record_line(self, line: str, matched: bool, level: Optional[str], timestamp: Optional[str]) -> None:
        """Update stats for a single processed line."""
        self.total_lines += 1
        if matched:
            self.matched_lines += 1
            if level:
                self.level_counts[level.upper()] += 1
            if timestamp:
                if self.first_timestamp is None:
                    self.first_timestamp = timestamp
                self.last_timestamp = timestamp
        else:
            self.skipped_lines += 1

    @property
    def match_rate(self) -> float:
        """Return the fraction of lines that matched filters."""
        if self.total_lines == 0:
            return 0.0
        return self.matched_lines / self.total_lines

    def format_report(self) -> str:
        """Return a human-readable summary string."""
        lines = [
            "--- logslice stats ---",
            f"Total lines read : {self.total_lines}",
            f"Matched lines    : {self.matched_lines}",
            f"Skipped lines    : {self.skipped_lines}",
            f"Match rate       : {self.match_rate:.1%}",
        ]
        if self.level_counts:
            level_str = ", ".join(
                f"{lvl}={cnt}" for lvl, cnt in sorted(self.level_counts.items())
            )
            lines.append(f"Levels matched   : {level_str}")
        if self.first_timestamp:
            lines.append(f"First timestamp  : {self.first_timestamp}")
        if self.last_timestamp:
            lines.append(f"Last timestamp   : {self.last_timestamp}")
        return "\n".join(lines)
