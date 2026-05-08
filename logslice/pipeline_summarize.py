"""Pipeline helper: attach a Summarizer to a line stream and emit the report."""
from __future__ import annotations

from typing import Iterable, Iterator, List, Optional

from logslice.summarizer import Summarizer


def apply_summarize(
    lines: Iterable[str],
    *,
    enabled: bool = False,
    top_n: int = 5,
    label: str = "=== Log Summary ===",
    levels: Optional[List[str]] = None,
    matched_flags: Optional[List[bool]] = None,
    emit_summary: bool = True,
) -> Iterator[str]:
    """Wrap *lines* with optional summarization.

    When *enabled* is False the lines are yielded unchanged and no summary
    is appended.  When *enabled* is True the lines are fed through a
    :class:`~logslice.summarizer.Summarizer` and, after the stream is
    exhausted, the formatted summary block is appended (one line per entry).

    Parameters
    ----------
    lines:
        Source iterable of log lines.
    enabled:
        Gate flag; pass ``True`` to activate summarisation.
    top_n:
        Maximum number of error sample lines in the summary.
    label:
        Header string for the summary block.
    levels:
        Optional parallel sequence of log-level strings (one per line).
    matched_flags:
        Optional parallel sequence of booleans indicating whether each line
        passed the active filters.
    emit_summary:
        When *True* (default) the summary block is appended to the stream.
        Set to *False* to collect statistics without emitting the report
        (useful for testing).
    """
    if not enabled:
        yield from lines
        return

    summarizer = Summarizer(top_n=top_n, label=label)
    yield from summarizer.feed(
        lines,
        levels=iter(levels) if levels is not None else None,
        matched_flags=iter(matched_flags) if matched_flags is not None else None,
    )

    if emit_summary:
        yield ""  # blank separator
        for summary_line in summarizer.format_summary():
            yield summary_line
