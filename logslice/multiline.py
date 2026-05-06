"""Multiline log entry assembler.

Some log formats (e.g. Java stack traces, Python tracebacks) span
multiple lines.  This module groups continuation lines with the
preceding header line so that filters and formatters see a single
complete entry.

A line is treated as a *continuation* when it matches a user-supplied
regex pattern (default: leading whitespace, typical for stack traces).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

_DEFAULT_CONTINUATION = re.compile(r"^\s+")


@dataclass
class MultilineAssembler:
    """Accumulate continuation lines into a single joined entry."""

    continuation_pattern: re.Pattern = field(
        default_factory=lambda: _DEFAULT_CONTINUATION
    )
    separator: str = " "

    _pending: List[str] = field(default_factory=list, init=False, repr=False)

    # ------------------------------------------------------------------ #

    def _is_continuation(self, line: str) -> bool:
        return bool(self.continuation_pattern.search(line))

    def _flush(self) -> Optional[str]:
        if not self._pending:
            return None
        joined = self.separator.join(self._pending)
        self._pending.clear()
        return joined

    # ------------------------------------------------------------------ #

    def feed(self, line: str) -> Iterator[str]:
        """Feed one raw line; yield zero or one assembled entries."""
        if self._is_continuation(line):
            self._pending.append(line.rstrip("\n"))
        else:
            flushed = self._flush()
            if flushed is not None:
                yield flushed
            self._pending.append(line.rstrip("\n"))

    def finalize(self) -> Iterator[str]:
        """Flush any buffered lines at end-of-stream."""
        flushed = self._flush()
        if flushed is not None:
            yield flushed


def assemble_multiline(
    lines: Iterator[str],
    pattern: Optional[str] = None,
    separator: str = " ",
) -> Iterator[str]:
    """Convenience wrapper: assemble *lines* into multiline entries.

    Parameters
    ----------
    lines:
        Raw line iterator (e.g. from ``stream_lines``).
    pattern:
        Regex string identifying continuation lines.  ``None`` uses the
        default (leading whitespace).
    separator:
        String used to join continuation lines to their header.
    """
    compiled = re.compile(pattern) if pattern else _DEFAULT_CONTINUATION
    assembler = MultilineAssembler(
        continuation_pattern=compiled, separator=separator
    )
    for line in lines:
        yield from assembler.feed(line)
    yield from assembler.finalize()
