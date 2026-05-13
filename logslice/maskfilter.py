"""MaskFilter: replace sensitive field values with a fixed mask string."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

_DEFAULT_MASK = "***"

# Matches key=value or key="value" patterns
_KV_RE = re.compile(
    r'(?P<key>[\w.-]+)'
    r'(?P<sep>=|:\s*)'
    r'(?P<value>"[^"]*"|\S+)'
)


@dataclass
class MaskFilter:
    """Mask specific field values in log lines.

    Fields listed in *fields* will have their values replaced with *mask*.
    Matching is case-insensitive on field names.
    """

    fields: List[str]
    mask: str = _DEFAULT_MASK
    _masked_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.fields:
            raise ValueError("fields must not be empty")
        if not self.mask:
            raise ValueError("mask must not be empty")
        self._field_set = {f.lower() for f in self.fields}
        self._pattern = re.compile(
            r'(?P<key>' + '|'.join(re.escape(f) for f in self.fields) + r')'
            r'(?P<sep>=|:\s*)'
            r'(?P<value>"[^"]*"|\S+)',
            re.IGNORECASE,
        )

    def apply(self, line: str) -> str:
        """Return *line* with matching field values replaced by *mask*."""
        def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
            self._masked_count += 1
            return f"{m.group('key')}{m.group('sep')}{self.mask}"

        return self._pattern.sub(_replace, line)

    @property
    def masked_count(self) -> int:
        """Total number of field values masked so far."""
        return self._masked_count

    def feed(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield lines with sensitive fields masked."""
        for line in lines:
            yield self.apply(line)
