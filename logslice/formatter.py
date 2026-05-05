"""Output formatting utilities for logslice."""

import sys
from typing import Optional, TextIO

# ANSI color codes
COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "WARN": "\033[33m",     # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "FATAL": "\033[35m",    # Magenta
    "RESET": "\033[0m",
}


def supports_color(stream: TextIO = sys.stdout) -> bool:
    """Return True if the stream supports ANSI color codes."""
    return hasattr(stream, "isatty") and stream.isatty()


def colorize_line(line: str, level: Optional[str], use_color: bool) -> str:
    """Apply ANSI color to a log line based on its level."""
    if not use_color or level is None:
        return line
    color = COLORS.get(level.upper())
    if color:
        return f"{color}{line}{COLORS['RESET']}"
    return line


def format_line(line: str, level: Optional[str], use_color: bool = False,
                prefix: Optional[str] = None) -> str:
    """Format a single log line with optional color and prefix."""
    output = line.rstrip("\n")
    if prefix:
        output = f"{prefix}{output}"
    output = colorize_line(output, level, use_color)
    return output


def write_output(lines: list[str], stream: TextIO = sys.stdout,
                 use_color: bool = False) -> int:
    """Write formatted lines to the given stream. Returns count of lines written."""
    count = 0
    for line in lines:
        print(line, file=stream)
        count += 1
    return count
