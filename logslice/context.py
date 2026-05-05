"""Context lines support: capture N lines before/after each match."""

from collections import deque
from typing import Generator, Iterable, Iterator, List, Tuple


class ContextBuffer:
    """Maintains a rolling buffer of pre-match lines and tracks post-match countdown."""

    def __init__(self, before: int = 0, after: int = 0):
        self.before = before
        self.after = after
        self._pre: deque = deque(maxlen=before)
        self._post_remaining: int = 0

    def feed(self, line: str, matched: bool) -> List[Tuple[str, bool]]:
        """
        Feed a line and whether it matched.
        Returns list of (line, is_context) tuples to emit.
        """
        results: List[Tuple[str, bool]] = []

        if matched:
            # Emit buffered pre-context lines
            for pre_line in self._pre:
                results.append((pre_line, True))
            self._pre.clear()
            # Emit the matched line itself
            results.append((line, False))
            # Reset post-context countdown
            self._post_remaining = self.after
        elif self._post_remaining > 0:
            results.append((line, True))
            self._post_remaining -= 1
        else:
            # Buffer as potential pre-context
            if self.before > 0:
                self._pre.append(line)

        return results

    def reset(self) -> None:
        self._pre.clear()
        self._post_remaining = 0


def apply_context(
    lines: Iterable[Tuple[str, bool]],
    before: int = 0,
    after: int = 0,
) -> Generator[Tuple[str, bool], None, None]:
    """
    Given an iterable of (line, matched) pairs, yield (line, is_context) pairs
    that include up to `before` lines before each match and `after` lines after.

    Yields:
        (line, is_context) where is_context=True means the line is context-only.
    """
    if before == 0 and after == 0:
        for line, matched in lines:
            if matched:
                yield line, False
        return

    buf = ContextBuffer(before=before, after=after)
    seen: set = set()
    pending: List[Tuple[str, bool]] = []

    for line, matched in lines:
        for out_line, is_ctx in buf.feed(line, matched):
            yield out_line, is_ctx
