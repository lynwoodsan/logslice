"""Log file reader with support for plain text and gzipped files."""

import gzip
import sys
from pathlib import Path
from typing import Generator, Optional


def open_log_file(path: Optional[str]):
    """Open a log file for reading, supporting .gz files and stdin."""
    if path is None or path == "-":
        return sys.stdin

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    if file_path.suffix == ".gz":
        return gzip.open(file_path, "rt", encoding="utf-8", errors="replace")

    return open(file_path, "r", encoding="utf-8", errors="replace")


def stream_lines(
    path: Optional[str],
    chunk_size: int = 8192,
) -> Generator[str, None, None]:
    """Stream lines from a log file one at a time.

    Args:
        path: Path to the log file, or None/"-" for stdin.
        chunk_size: Unused, reserved for future buffered reading.

    Yields:
        Individual lines from the file, with newlines stripped.
    """
    fh = open_log_file(path)
    try:
        for line in fh:
            yield line.rstrip("\n")
    finally:
        if fh is not sys.stdin:
            fh.close()


def count_lines(path: Optional[str]) -> int:
    """Count the total number of lines in a log file.

    Args:
        path: Path to the log file.

    Returns:
        Total line count.
    """
    total = 0
    for _ in stream_lines(path):
        total += 1
    return total
