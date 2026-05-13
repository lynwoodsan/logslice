"""Pipeline integration for MaskFilter.

Provides *apply_mask* which wraps an iterable of log lines and applies
field-value masking when one or more field names are supplied.
"""

from __future__ import annotations

from typing import Iterator, List, Optional

from logslice.maskfilter import MaskFilter


def apply_mask(
    lines: Iterator[str],
    fields: Optional[List[str]] = None,
    mask: str = "***",
) -> Iterator[str]:
    """Yield log lines with sensitive field values replaced.

    Parameters
    ----------
    lines:
        Source iterator of raw log lines.
    fields:
        List of field names whose values should be masked.  When *None* or
        empty the source iterator is returned unchanged.
    mask:
        Replacement string used in place of the original value.
    """
    if not fields:
        yield from lines
        return

    mf = MaskFilter(fields=fields, mask=mask)
    yield from mf.feed(lines)
