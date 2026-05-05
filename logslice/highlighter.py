"""Regex pattern highlighting for matched log lines."""

import re
from typing import Optional

# ANSI color codes for highlighting
HIGHLIGHT_COLOR = "\033[1;33m"  # Bold yellow
RESET_COLOR = "\033[0m"


def highlight_matches(line: str, pattern: Optional[str], use_color: bool = True) -> str:
    """Wrap regex matches in a line with ANSI highlight codes.

    Args:
        line: The log line to process.
        pattern: The regex pattern to highlight. If None, returns line unchanged.
        use_color: Whether to apply color codes.

    Returns:
        The line with matched segments highlighted, or original line if no pattern.
    """
    if not pattern or not use_color:
        return line

    try:
        compiled = re.compile(pattern)
    except re.error:
        return line

    def replacer(match: re.Match) -> str:
        return f"{HIGHLIGHT_COLOR}{match.group(0)}{RESET_COLOR}"

    return compiled.sub(replacer, line)


def count_matches(line: str, pattern: Optional[str]) -> int:
    """Count the number of times a pattern matches within a line.

    Args:
        line: The log line to search.
        pattern: The regex pattern to count.

    Returns:
        Number of matches found, or 0 if pattern is None or invalid.
    """
    if not pattern:
        return 0

    try:
        compiled = re.compile(pattern)
    except re.error:
        return 0

    return len(compiled.findall(line))


def strip_highlights(line: str) -> str:
    """Remove any ANSI highlight codes from a line.

    Args:
        line: The line potentially containing ANSI codes.

    Returns:
        The line with all ANSI escape sequences removed.
    """
    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", line)
