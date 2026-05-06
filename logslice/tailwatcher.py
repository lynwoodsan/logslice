"""Tail a log file and re-open it on rotation."""
from __future__ import annotations

import time
from typing import Generator, Optional

from logslice.rotationwatcher import RotationWatcher


def tail_with_rotation(
    path: str,
    poll_interval: float = 0.5,
    max_iterations: Optional[int] = None,
) -> Generator[str, None, None]:
    """Yield new lines from *path*, handling log rotation transparently.

    When rotation is detected the file is re-opened from the beginning.
    The generator runs indefinitely unless *max_iterations* is set (useful
    for testing).

    Args:
        path: Path to the log file to tail.
        poll_interval: Seconds to sleep between polls when no new data.
        max_iterations: Stop after this many poll loops (None = forever).

    Yields:
        Decoded text lines (newline stripped).
    """
    watcher = RotationWatcher(path)
    fh = _open_safe(path)
    iteration = 0

    try:
        while max_iterations is None or iteration < max_iterations:
            iteration += 1

            if watcher.check():
                # Rotation detected — close old handle and reopen.
                if fh is not None:
                    fh.close()
                fh = _open_safe(path)
                watcher.reset()

            if fh is not None:
                while True:
                    line = fh.readline()
                    if not line:
                        break
                    yield line.rstrip("\n")

            time.sleep(poll_interval)
    finally:
        if fh is not None:
            fh.close()


def _open_safe(path: str):
    """Open *path* for reading, returning None if it does not exist."""
    try:
        return open(path, "r", encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
