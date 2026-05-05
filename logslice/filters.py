"""Log filtering functions for logslice."""

import re
from datetime import datetime
from typing import Optional


LOG_LEVEL_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)

TIMESTAMP_PATTERNS = [
    re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"),
    re.compile(r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})"),
]

TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
]

# Canonical log level names; WARN and FATAL are aliases
LEVEL_ALIASES = {
    "WARN": "WARNING",
    "FATAL": "CRITICAL",
}


def extract_timestamp(line: str) -> Optional[datetime]:
    """Extract a datetime object from a log line, if present."""
    for pattern in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if match:
            raw = match.group(1)
            for fmt in TIMESTAMP_FORMATS:
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
    return None


def extract_level(line: str) -> Optional[str]:
    """Extract the log level from a log line, if present.

    Aliases such as WARN and FATAL are normalized to their canonical
    forms (WARNING and CRITICAL respectively).
    """
    match = LOG_LEVEL_PATTERN.search(line)
    if match:
        level = match.group(1).upper()
        return LEVEL_ALIASES.get(level, level)
    return None


def matches_time_range(
    line: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> bool:
    """Return True if the line's timestamp falls within [start, end]."""
    if start is None and end is None:
        return True
    ts = extract_timestamp(line)
    if ts is None:
        return False
    if start and ts < start:
        return False
    if end and ts > end:
        return False
    return True


def matches_level(line: str, levels: Optional[list] = None) -> bool:
    """Return True if the line's log level is in the provided list.

    Level comparisons are case-insensitive, and aliases (WARN, FATAL)
    are resolved before matching.
    """
    if not levels:
        return True
    level = extract_level(line)
    if level is None:
        return False
    normalized_levels = [
        LEVEL_ALIASES.get(lvl.upper(), lvl.upper()) for lvl in levels
    ]
    return level in normalized_levels


def matches_pattern(line: str, pattern: Optional[str] = None) -> bool:
    """Return True if the line matches the provided regex pattern."""
    if pattern is None:
        return True
    return bool(re.search(pattern, line))


def apply_filters(
    line: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    levels: Optional[list] = None,
    pattern: Optional[str] = None,
) -> bool:
    """Apply all active filters to a single log line."""
    return (
        matches_time_range(line, start, end)
        and matches_level(line, levels)
        and matches_pattern(line, pattern)
    )
