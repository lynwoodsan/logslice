"""Tail support: stream new lines appended to a log file, optionally from a bookmark."""

import time
from typing import Iterator, Optional

from logslice.bookmark import Bookmark


DEFAULT_POLL_INTERVAL = 0.25


def tail_file(
    path: str,
    bookmark: Optional[Bookmark] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_iterations: Optional[int] = None,
) -> Iterator[str]:
    """Yield new lines appended to *path* as they arrive.

    If a *bookmark* is provided the tail starts from the saved offset;
    the offset is updated after each batch of lines is emitted.

    *max_iterations* is used in tests to avoid an infinite loop.
    """
    offset = bookmark.load() if bookmark else 0
    iterations = 0

    with open(path, "r", errors="replace") as fh:
        fh.seek(offset)
        while True:
            line = fh.readline()
            if line:
                offset = fh.tell()
                if bookmark:
                    bookmark.save(offset)
                yield line.rstrip("\n")
            else:
                if max_iterations is not None:
                    iterations += 1
                    if iterations >= max_iterations:
                        return
                time.sleep(poll_interval)


def read_from_bookmark(
    path: str,
    bookmark: Bookmark,
) -> Iterator[str]:
    """Yield all lines written since the last bookmark, then stop."""
    offset = bookmark.load()
    with open(path, "r", errors="replace") as fh:
        fh.seek(offset)
        for line in fh:
            yield line.rstrip("\n")
        new_offset = fh.tell()
    bookmark.save(new_offset)
