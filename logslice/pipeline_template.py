"""Pipeline integration for TemplateFormatter."""
from __future__ import annotations

from typing import Iterator, Optional

from logslice.templateformatter import TemplateFormatter


def apply_template(
    lines: Iterator[str],
    template: Optional[str],
) -> Iterator[str]:
    """Yield lines formatted with *template*.

    If *template* is ``None`` or empty the lines are passed through unchanged.
    """
    if not template:
        yield from lines
        return

    formatter = TemplateFormatter(template=template)
    yield from formatter.feed(lines)
